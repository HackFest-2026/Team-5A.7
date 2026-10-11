"""Short-lived receipts for server-rendered views, not claims of browser inspection."""
import copy
import hashlib
import json
import math
import secrets
import threading
import time


def state_key(state):
    keys = ('page_id', 'filters', 'date_range', 'compare', 'compare_range', 'sort', 'top_n', 'grain')
    st = {k: state.get(k) for k in keys}
    st['filters'] = {k: sorted(v) for k, v in (st['filters'] or {}).items() if v}
    for k in ('date_range', 'compare_range'):
        r = st[k]
        st[k] = {f: r.get(f) for f in ('start', 'end')} if r else None
    return json.dumps(st, sort_keys=True, default=str)


class RenderReceipts:
    def __init__(self, ttl=600, capacity=200):
        self.ttl, self.capacity = ttl, capacity
        self.entries = {}
        self.lock = threading.RLock()

    def issue(self, payload):
        token = secrets.token_urlsafe(24)
        digest = hashlib.sha256(json.dumps(payload['widgets'], sort_keys=True, default=str).encode()).hexdigest()
        with self.lock:
            now = time.monotonic()
            self.entries = {k: v for k, v in self.entries.items() if now - v[0] < self.ttl}
            while len(self.entries) >= self.capacity:
                self.entries.pop(next(iter(self.entries)))
            self.entries[token] = (now, copy.deepcopy(payload))
        return {'id': token, 'payload_hash': digest, 'scope': 'server_rendered_payload'}

    def check(self, token, state, facts, metadata):
        with self.lock:
            entry = self.entries.get(token)
        if not entry or time.monotonic() - entry[0] >= self.ttl:
            return {'ok': False, 'reason': 'Render receipt expired or unavailable.'}
        payload = entry[1]
        if state_key(payload['state']) != state_key(state):
            return {'ok': False, 'reason': 'Rendered view differs from the applied state.'}
        if any(w.get('error') for w in payload['widgets']):
            return {'ok': False, 'reason': 'A view component failed to load.'}
        # Exact query + metric + raw value matching prevents coincidental-number citations.
        definitions = {w['id']: w for w in metadata['pages'][state['page_id']]['widgets']}
        anchors = []
        for i, fact in enumerate(facts):
            if not isinstance(fact.get('value'), (int, float)):
                continue
            for widget in payload['widgets']:
                definition = definitions[widget['id']]
                if definition['view'] != fact.get('view') or widget.get('sql') != fact.get('sql'):
                    continue
                cells = []
                if widget['type'] == 'kpi' and definition.get('metric') == fact['metric']:
                    cells = [(widget['value'], 'value', None, None)]
                elif widget['type'] == 'grid':
                    for col, field in enumerate(widget['columns']):
                        if field['field'] == fact['metric']:
                            cells += [(row[col], f'raw/{idx}/{col}', idx, col) for idx, row in enumerate(widget['raw'])]
                elif widget['type'] in ('bar', 'donut') and definition.get('metric') == fact['metric']:
                    cells = [(value, f'values/{idx}', idx, None) for idx, value in enumerate(widget['values'])]
                elif widget['type'] == 'line' and fact['metric'] in definition.get('metrics', []):
                    series = definition['metrics'].index(fact['metric'])
                    cells = [(value, f'series/{series}/values/{idx}', idx, None) for idx, value in enumerate(widget['series'][series]['values'])]
                matches = [(path, row, col) for value, path, row, col in cells
                           if isinstance(value, (int, float)) and math.isclose(value, fact['value'], rel_tol=1e-12, abs_tol=1e-8)]
                if len(matches) == 1:
                    path, row, col = matches[0]
                    anchors.append({'fact_index': i, 'widget_id': widget['id'], 'path': path, 'row': row, 'column': col})
                    break
        return {'ok': True, 'scope': 'server_payload_and_client_state', 'anchors': anchors,
                'anchored_figures': len(anchors), 'note': 'Other figures retain query evidence; this is not independent browser verification.'}
