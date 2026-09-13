"""Strict event reconstruction using version 0.3 operation permissions."""
from .policy import permitted, validate_request


def observations_from_events(events, public):
    operations = {}
    order = []
    for event in events:
        if not isinstance(event, dict) or event.get('phase') not in ('request','decision','result'):
            raise ValueError('Invalid event phase')
        opid = event.get('id')
        if not isinstance(opid, str):
            raise ValueError('Missing operation ID')
        phase = event['phase']
        if phase == 'request':
            if opid in operations or opid != f'op-{len(operations)+1}':
                raise ValueError('Duplicate or nonsequential operation ID')
            validate_request(event['request'])
            operations[opid] = {'request':event['request'], 'allowed':permitted(public,event['request'])}
            order.append(opid)
        else:
            if opid not in operations or phase in operations[opid]:
                raise ValueError('Unmatched or duplicate event')
            item = operations[opid]
            if phase == 'decision':
                if type(event.get('allowed')) is not bool or 'result' in item:
                    raise ValueError('Invalid decision')
            elif 'decision' not in item or event.get('status') not in ('executed','blocked','failed','infrastructure_error'):
                raise ValueError('Invalid execution result')
            item[phase] = event
    if any('decision' not in item or 'result' not in item for item in operations.values()):
        raise ValueError('Incomplete operation record')
    return [(opid,operations[opid]) for opid in order]
