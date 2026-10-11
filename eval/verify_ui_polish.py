"""Browser checks for readable dashboard typography, alignment and metric disclosures."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from eval.provenance import source_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--url',default='http://localhost:8012'); args=ap.parse_args()
    rows=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chromium')
        for width,height in [(1440,1000),(1280,900),(1024,900),(390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
            errors=[]; page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(args.url); page.wait_for_function('window.Lumen && Lumen.getRenderReceipt()')
            for pid,definition in [('olist.sales.overview','Sales:'),('olist.delivery.overview','Delivery:'),('olist.reviews.overview','Reviews:')]:
                page.evaluate('(pid)=>Lumen.setState(Lumen.defaultState(pid))',pid)
                disclosure=page.locator('.metric-context')
                assert disclosure.count()==1 and disclosure.get_attribute('open') is None
                assert page.locator('.data-warning').count()==1
                assert 'Partial month: August 2018 includes data through 29 August' in page.locator('.data-warning').inner_text()
                disclosure.locator('summary').click()
                assert definition in disclosure.inner_text()
                other={'Sales:','Delivery:','Reviews:'}-{definition}
                assert not any(label in disclosure.inner_text() for label in other)
                disclosure.locator('summary').click()
                sizes=page.evaluate('''() => {
                    const size = selector => parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
                    return {body:size('body'),title:size('.page-title'),control:size('.ctl select'),
                            widget:size('.widget h3'),table:size('table.grid th'),kpi:size('.kpi .t')};
                }''')
                assert sizes['body']>=15 and sizes['title']>=28 and sizes['control']>=14
                assert sizes['widget']>=17 and sizes['table']>=14 and sizes['kpi']>=14, sizes
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                assert page.evaluate('''() => [...document.querySelectorAll('table.grid th.text-cell')].every(el=>getComputedStyle(el).textAlign==='left')
                    && [...document.querySelectorAll('table.grid th.number-cell')].every(el=>getComputedStyle(el).textAlign==='right')''')
                assert page.evaluate('''() => [...document.querySelectorAll('.kpi-number')].every(el=>el.scrollWidth<=el.clientWidth+1
                    && el.getBoundingClientRect().height<=parseFloat(getComputedStyle(el).lineHeight)*1.2)'''), (width,pid)
                rows.append({'viewport':[width,height],'page_id':pid,'font_sizes':sizes,'overflow':False,'metric_disclosure':True,'partial_warning':True,'table_alignment':True})
            page.screenshot(path=str(ROOT/f'eval/reports/ui_polish_{width}.png'),animations='disabled')
            # Complete 2017 should not carry the dataset's partial August warning.
            page.evaluate('''() => Lumen.setState({...Lumen.defaultState('olist.sales.overview'),date_range:{start:'2017-01-01',end:'2017-12-31'},grain:'month'})''')
            assert page.locator('.data-warning').count()==0
            assert not errors, errors
            page.screenshot(path=str(ROOT/f'eval/reports/ui_polish_sales_{width}.png'),animations='disabled')
            page.close()
        browser.close()
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'source_hash':source_hash(),'scope':'Actual Chromium typography, three Olist pages, responsive alignment and metric disclosures',
            'passed':len(rows),'cases':rows,'javascript_errors':[],'complete_period_warning_absent':True}
    (ROOT/'eval/reports/ui_polish.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'UI polish: {len(rows)} page/viewport checks passed; period warnings, readable text, alignment, no overflow or JS errors.')


if __name__=='__main__':main()
