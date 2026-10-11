"""Regressions for stale state, failed rendering and post-render calculations."""
import copy
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from backend.main import AGENT, app
from backend.evidence import RenderReceipts
from backend.agent.llm import slot_schema


@pytest.fixture
def client():
    with patch.dict(os.environ, {'LUMEN_AGENT_MODE': 'rules'}):
        yield TestClient(app)


def request(client):
    state = AGENT.planner.default_state('exec.dashboards.summary')
    r = client.post('/api/chat', json={'message':'Show South revenue for August 2026', 'state':state, 'defer_commit':True})
    assert r.status_code == 200
    return r.json()


def test_pending_turn_does_not_change_context_or_undo_until_render(client):
    r = request(client)
    session = AGENT.session(r['session_id'])
    assert not session.ctx and not session.stack
    body = {'session_id':r['session_id'], 'turn_id':r['turn_id'], 'applied_state':r['target_state']}
    assert client.post('/api/verify', json=body).json()['ok'] is False
    render = client.post('/api/render', json={'state':r['target_state']}).json()
    body['render_receipt'] = render['receipt']['id']
    checked = client.post('/api/verify', json=body).json()
    assert checked['ok'] and checked['render']['ok']
    assert checked['answer']['commit_status'] == 'verified'
    assert checked['answer']['execution']['post_render_calculation_ms'] >= 0
    assert session.ctx['filters']['region'] == ['South'] and len(session.stack) == 1
    assert not session.transactions


def test_abort_discards_followup_context_and_preserves_undo(client):
    r = request(client)
    assert client.post('/api/abort', json={'session_id':r['session_id'], 'turn_id':r['turn_id']}).json()['ok']
    sess = AGENT.session(r['session_id'])
    assert not sess.ctx and not sess.stack and not sess.history
    assert AGENT.verify(r['session_id'], r['turn_id'], r['target_state'])['ok'] is None


def test_receipt_for_other_scope_cannot_commit(client):
    r = request(client)
    other = AGENT.planner.default_state('exec.dashboards.summary')
    render = client.post('/api/render', json={'state':other}).json()
    checked = client.post('/api/verify', json={'session_id':r['session_id'], 'turn_id':r['turn_id'],
                         'applied_state':r['target_state'], 'render_receipt':render['receipt']['id']}).json()
    assert checked['ok'] is False
    assert not AGENT.session(r['session_id']).ctx
    AGENT.abort(r['session_id'], r['turn_id'])


def test_failed_widget_and_expired_receipt_cannot_verify():
    receipts = RenderReceipts()
    payload = {'state':{'page_id':'p'}, 'widgets':[{'id':'w', 'error':'database unavailable'}]}
    receipt = receipts.issue(payload)
    assert not receipts.check(receipt['id'], payload['state'], [], {})['ok']
    receipts.ttl = -1
    assert not receipts.check(receipt['id'], payload['state'], [], {})['ok']


def test_equal_value_from_different_query_is_not_source_evidence():
    receipts = RenderReceipts()
    state = {'page_id':'p'}
    payload = {'state':state, 'widgets':[{'id':'w', 'type':'kpi', 'value':10, 'sql':'query A'}]}
    meta = {'pages':{'p':{'widgets':[{'id':'w', 'type':'kpi', 'view':'sales', 'metric':'revenue'}]}}}
    receipt = receipts.issue(payload)
    fact = {'value':10, 'metric':'revenue', 'view':'sales', 'sql':'query B'}
    assert receipts.check(receipt['id'], state, [fact], meta)['anchors'] == []
    fact['sql'] = 'query A'
    result = receipts.check(receipt['id'], state, [fact], meta)
    assert result['anchors'][0]['path'] == 'value'


def test_more_than_four_steps_clarifies_instead_of_silently_dropping(client):
    result = client.post('/api/chat', json={'message':'Show revenue; show orders; show aov; show revenue; show orders'}).json()
    assert result['kind'] == 'clarify' and not result['actions']


def test_page_schema_excludes_other_dataset_and_control_fields():
    page = AGENT.meta['pages'].get('olist.delivery.overview')
    if not page: pytest.skip('Olist not imported')
    schema = slot_schema('olist_delivery', 'Show average delivery time for SP in 2017', page=page)
    assert 'olist_delivery.olist_delivery_days' in schema['properties']['metric']['enum']
    assert 'olist_sales.olist_revenue' not in schema['properties']['metric']['enum']
    assert 'region' not in schema['properties']['filters']['properties']
    assert schema['properties']['page_id']['enum'] == [page['id'],None]


def test_selected_page_prompt_contains_current_ui_context_and_rejects_wrong_metric():
    if 'olist.sales.overview' not in AGENT.meta['pages']: pytest.skip('Olist not imported')
    state = AGENT.planner.default_state('olist.sales.overview')
    state['filters'] = {'br_state':['SP']}
    captured = {}
    def model(system, user):
        captured['prompt'] = user
        return {'intent':'query','metric':'olist_sales.olist_revenue','filters':{},'group_by':[],
                'time_expression':'2017','top_n':None}
    parsed = AGENT.llm.parse('Show average delivery time for SP in 2017', current_page=state['page_id'],
                             current_state=state, call_fn=model)
    assert parsed.retrieval_scope['page_id'] == 'olist.delivery.overview'
    assert 'CURRENT UI STATE:' in captured['prompt'] and '"br_state": ["SP"]' in captured['prompt']
    assert 'SELECTED PAGE SCHEMA:' in captured['prompt']
    assert len(captured['prompt']) < 16000
    assert 'olist_sales.olist_revenue' not in captured['prompt']
    assert parsed.llm_blocked == ['metric:olist_sales.olist_revenue']
