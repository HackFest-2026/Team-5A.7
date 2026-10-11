"""Micro precision/recall/F1 for explicitly annotated state fields only."""
import json


def slots(state, fields):
    result = set()
    for field in fields:
        value = state.get(field)
        if field == 'filters':
            for key, values in (value or {}).items():
                result.update((f'filters.{key}', str(v)) for v in values)
        elif field in ('date_range', 'compare_range'):
            if value:
                result.update((f'{field}.{key}', str(value.get(key))) for key in ('start','end'))
        elif value is not None:
            result.add((field, json.dumps(value,sort_keys=True)))
    return result


def measure(expected, actual, fields):
    wanted, got = slots(expected, fields), slots(actual, fields)
    tp, fp, fn = len(wanted & got), len(got-wanted), len(wanted-got)
    precision = tp/(tp+fp) if tp+fp else 1.0
    recall = tp/(tp+fn) if tp+fn else 1.0
    return {'tp':tp,'fp':fp,'fn':fn,'precision':precision,'recall':recall,
            'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.0,
            'annotated_fields':list(fields)}
