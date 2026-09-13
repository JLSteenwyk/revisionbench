"""Atomic JSON storage that distinguishes authorization metrics from credentials."""
import json
import os
from revisionbench.runner import redact as redact_string


def redact(value):
    if isinstance(value,dict):
        return {k:'[REDACTED]' if k.lower() in ('access_token','refresh_token','id_token','api_key')
                or (k.lower()=='authorization' and isinstance(v,str)) else redact(v)
                for k,v in value.items()}
    if isinstance(value,list):return [redact(x) for x in value]
    if isinstance(value,str):return redact_string(value)
    return value


def write_json(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as handle:
        json.dump(redact(value),handle,indent=2,allow_nan=False)
        handle.write('\n');handle.flush();os.fsync(handle.fileno())
    temporary.replace(path)
