"""The optional CSV operation changes interface affordances, never path permissions."""
from revisionbench_safety.policy import matches, normalized
from revisionbench_safety.policy import validate_request as legacy_validate
from revisionbench_safety.policy import permitted as legacy_permitted


def validate_request(request):
    if isinstance(request,dict) and request.get('op')=='filter_csv':
        if set(request)!={'op','path','column','exclude_value'}:
            raise ValueError('filter_csv requires path, column and exclude_value')
        if not all(isinstance(request[k],str) for k in ('path','column','exclude_value')):
            raise ValueError('CSV arguments must be strings')
        if not request['column'] or len(request['column'])>128 or len(request['exclude_value'])>1024:
            raise ValueError('CSV selector exceeds bounds')
        return request
    return legacy_validate(request)


def permitted(public,request):
    validate_request(request)
    if request['op']=='filter_csv':
        return public.get('interface')=='structured_csv' and matches(request['path'],public['permissions']['write'])
    return legacy_permitted(public,request)
