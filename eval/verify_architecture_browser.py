"""Agent-authored regressions; distinct from reused and human-held-out benchmarks."""
import argparse
import csv
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from time import perf_counter
from playwright.sync_api import sync_playwright
from eval.provenance import source_hash
from eval.slot_metrics import measure

ROOT = Path(__file__).resolve().parents[1]


def oracle():
    with zipfile.ZipFile(ROOT/'data/olist_source.zip') as z:
        def read(name): return list(csv.DictReader(TextIOWrapper(z.open(name), encoding='utf-8-sig')))
        orders = read('olist_orders_dataset.csv')
        customers = {r['customer_id']:r for r in read('olist_customers_dataset.csv')}
        items = read('olist_order_items_dataset.csv')
        reviews = read('olist_order_reviews_dataset.csv')
    prices, scores = defaultdict(Decimal), defaultdict(list)
    for r in items: prices[r['order_id']] += Decimal(r['price'])
    for r in reviews: scores[r['order_id']].append(int(r['review_score']))
    rows = []
    for r in orders:
        if r['order_status'] != 'delivered': continue
        purchase = datetime.fromisoformat(r['order_purchase_timestamp'])
        row = {'year':str(purchase.year), 'month':purchase.strftime('%Y-%m'), 'state':customers[r['customer_id']]['customer_state'],
               'sales':float(prices[r['order_id']]), 'sales_eligible':r['order_id'] in prices}
        if r['order_delivered_customer_date'] and r['order_estimated_delivery_date']:
            delivered = datetime.fromisoformat(r['order_delivered_customer_date'])
            if delivered >= purchase:
                row['days'] = (delivered-purchase).total_seconds()/86400
                if scores[r['order_id']]: row['score'] = sum(scores[r['order_id']])/len(scores[r['order_id']])
        rows.append(row)
    return rows


def expected(case, rows):
    rows = [r for r in rows if r['year'] == case['year'] and (not case.get('state') or r['state'] == case['state'])]
    metric = case['metric']
    if metric in ('olist_orders','olist_aov','olist_revenue'): rows = [r for r in rows if r['sales_eligible']]
    elif metric == 'olist_delivery_days': rows = [r for r in rows if 'days' in r]
    else: rows = [r for r in rows if 'score' in r]
    if case.get('grain'):
        result = defaultdict(float)
        for r in rows: result[r['month']] += r['sales']
        return dict(result)
    if metric == 'olist_orders': return len(rows)
    if metric == 'olist_aov': return sum(r['sales'] for r in rows)/len(rows)
    key = 'days' if metric == 'olist_delivery_days' else 'score'
    return sum(r[key] for r in rows)/len(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--url', default='http://localhost:8012'); args = ap.parse_args()
    cases = [json.loads(line) for line in (ROOT/'eval/architecture_challenges.jsonl').read_text().splitlines()]
    original = oracle(); results = []; robustness = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
        def reset(pid='olist.sales.overview'):
            page.goto(args.url)
            page.wait_for_function('window.Lumen && Lumen.getRenderReceipt()')
            page.evaluate('(pid) => Lumen.setState(Lumen.defaultState(pid))', pid)
        def ask(text):
            count = page.evaluate('window.__lumenTurns || 0'); start = perf_counter()
            with page.expect_response(lambda r: r.url.endswith('/api/chat') and r.request.method == 'POST', timeout=120000) as observed:
                page.fill('#input', text); page.press('#input','Enter')
            response = observed.value.json()
            page.wait_for_function(f'(window.__lumenTurns || 0) > {count} || window.__lumenLast?.kind === "cancelled"', timeout=120000)
            return response, page.evaluate('window.__lumenLast'), (perf_counter()-start)*1000
        for case in cases:
            reset(case['start_page']); response, last, latency = ask(case['question'])
            state = page.evaluate('Lumen.getState()')
            destination = state['page_id'] == case.get('page',case['start_page'])
            controls = response['kind'] == case.get('kind','multi_step' if case.get('steps') else 'act')
            calculation = None
            slot_result = None
            if case.get('metric'):
                controls &= state['date_range']['start'] == case['year']+'-01-01' and state['date_range']['end'] == case['year']+'-12-31'
                if case.get('state'): controls &= state['filters'].get('br_state') == [case['state']]
                if case.get('grain'): controls &= state['grain'] == case['grain']
                wanted = expected(case, original)
                facts = [f for f in response['facts'] if f['metric'] == case['metric']]
                if isinstance(wanted,dict):
                    chart = next(c for c in response['cards'] if c['type']=='line')
                    actual = {datetime.strptime(label,'%b %Y').strftime('%Y-%m'):value
                              for label,value in zip(chart['labels'],chart['series'][0]['values'])}
                    calculation = actual.keys() == wanted.keys() and all(abs(actual[k]-v)<.005 for k,v in wanted.items())
                else:
                    actual = next(f['value'] for f in facts if f['kind']=='value')
                    calculation = abs(actual-wanted) < .005
                verification = last.get('render_verified') is True
                annotated = {'date_range':{'start':case['year']+'-01-01','end':case['year']+'-12-31'},
                             'filters':{'br_state':[case['state']]} if case.get('state') else {}}
                if case.get('grain'): annotated['grain'] = case['grain']
                slot_result = measure(annotated,state,annotated.keys())
            else:
                verification = not response['actions']
            assert destination and controls and verification and calculation is not False, {'id':case['id'], 'destination':destination, 'controls':controls, 'verification':verification, 'calculation':calculation, 'reply':response['reply']}
            results.append({'id':case['id'],'question':case['question'],'destination_ok':destination,'controls_ok':bool(controls),
                            'calculation_ok':calculation,'verification_ok':verification,'backend_latency_ms':response.get('latency_ms'),
                            'browser_latency_ms':round(latency,1),'execution':last.get('execution')})
            results[-1]['slots'] = slot_result
        # Delay delivery of a completed AI response and change the view in between.
        reset()
        def drift(route):
            response = route.fetch()
            page.evaluate('() => Lumen.setState({...Lumen.getState(), filters:{br_state:["RJ"]}})')
            route.fulfill(response=response)
        page.route('**/api/chat', drift, times=1)
        response,last,_ = ask('Show sales for SP in 2017')
        assert last['kind']=='cancelled' and page.evaluate('Lumen.getState().filters.br_state') == ['RJ']
        check = page.request.post(args.url+'/api/abort', data={'session_id':response['session_id'],'turn_id':response['turn_id']}).json()
        assert not check['ok'] # Already cancelled by the browser.
        robustness.append({'check':'manual change during AI request','ok':True})
        page.screenshot(path=str(ROOT/'eval/reports/state_drift.png'))
        # Failed render must not produce an answer or successful check.
        reset(); page.route('**/api/render', lambda route:route.fulfill(status=503,body='unavailable'), times=1)
        _,last,_ = ask('Show sales for SP in 2017')
        assert last['kind']=='cancelled' and not page.locator('.msg-bot').last.locator('.verify.ok').count()
        robustness.append({'check':'render failure suppresses answer and cancels pending context','ok':True})
        # Exact source anchors must be clickable on a successful view.
        reset(); _,last,_ = ask('Show monthly sales value for SP in 2017')
        assert last['evidence_anchors']
        page.locator('.source-details > summary').last.click()
        page.get_by_role('button',name='Show source in view').first.click()
        assert page.locator('.agent-focus').count()
        robustness.append({'check':'query-matched figure source highlight','ok':True})
        assert not errors, errors
        browser.close()
    scored = [r['slots'] for r in results if r['slots']]
    tp,fp,fn = (sum(r[key] for r in scored) for key in ('tp','fp','fn'))
    report = {'generated_at':datetime.now(timezone.utc).isoformat(), 'source_hash':source_hash(),
              'author':'Codex', 'independent_holdout':False, 'scope':'Agent-authored Windows Chromium regressions; original CSV/Decimal numerical expectations; rules mode',
              'cases':results,'robustness':robustness,'javascript_errors':errors,'passed':len(results)+len(robustness),
              'slot_metrics':{'scope':'Only explicitly annotated dates, filters and grain; destination measured separately.',
                              'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else 1,
                              'recall':tp/(tp+fn) if tp+fn else 1,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1}}
    (ROOT/'eval/reports/architecture_browser.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Architecture browser: {len(results)} challenges + {len(robustness)} recovery/evidence checks passed.")


if __name__=='__main__': main()
