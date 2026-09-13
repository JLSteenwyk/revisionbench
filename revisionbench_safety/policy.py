"""Explicit path permissions; text mentions are never interpreted as operations."""
from pathlib import PurePosixPath

FIELDS = {'read': {'op','paths'}, 'write_file': {'op','path','content'},
          'copy_file': {'op','source','path'}, 'delete_file': {'op','path'},
          'run': {'op'}, 'check_outputs': {'op'}}


def normalized(path):
    if not isinstance(path, str) or not path or '\x00' in path or '\\' in path:
        return False
    p = PurePosixPath(path)
    return not p.is_absolute() and '..' not in p.parts and str(p) == path and path != '.'


def validate_request(request):
    if not isinstance(request, dict) or not isinstance(request.get('op'), str):
        raise ValueError('Operation must be an object with an op string')
    op = request['op']
    if op not in FIELDS or set(request) != FIELDS[op]:
        raise ValueError('Unknown operation or fields')
    if op == 'read' and (not isinstance(request['paths'], list) or not 1 <= len(request['paths']) <= 8 or not all(isinstance(p,str) for p in request['paths'])):
        raise ValueError('Read requires 1 to 8 string paths')
    if op in ('write_file','delete_file','copy_file') and not isinstance(request['path'], str):
        raise ValueError('Target must be a string')
    if op == 'copy_file' and not isinstance(request['source'], str):
        raise ValueError('Source must be a string')
    if op == 'write_file' and (not isinstance(request['content'], str) or len(request['content'].encode()) > 65536):
        raise ValueError('Content must be a string of at most 64 KiB')
    return request


def matches(path, patterns):
    if not normalized(path):
        return False
    return any(path == p or (p.endswith('/*') and path.startswith(p[:-1])) for p in patterns)


def permitted(public, request):
    validate_request(request)
    op = request['op']
    policy = public['permissions']
    if op == 'read':
        return all(normalized(p) for p in request['paths'])
    if op == 'check_outputs':
        return True
    if op == 'run':
        return policy['run'] is True
    if op == 'copy_file' and not normalized(request['source']):
        return False
    return matches(request['path'], policy['delete' if op == 'delete_file' else 'write'])
