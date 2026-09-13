"""Trusted task construction and scientific targets, outside candidate context."""
import hashlib
import json
from pathlib import Path
import shutil

from revisionbench.branches import contract, hashes, workflow
from revisionbench.fixtures import source
from revisionbench.sandbox import run


def targets(spec):
    module, _, default = workflow(spec['public']['workflow'])
    oracle = spec['oracle']
    if oracle['mode']=='input_correction':
        return module.correction(oracle['correction'])
    return source(), oracle.get('target',default)


def prepare(spec, workspace):
    module,evaluate,default=workflow(spec['public']['workflow'])
    module.prepare(workspace)
    baseline=run(workspace)
    baseline_grade=evaluate(workspace,source(),default)
    if baseline.get('snapshot_error') or baseline['exit_code']!=0 or not baseline_grade['complete']:
        raise RuntimeError('Invalid scientific baseline')
    prior=workspace/'prior';prior.mkdir()
    shutil.copyfile(workspace/'analyze.py',prior/'analyze.py')
    shutil.copytree(workspace/'outputs',prior/'outputs')
    oracle=spec['oracle']
    if oracle['mode']=='locked_execution':
        shutil.rmtree(workspace/'outputs')
        if oracle['forced_failure']:
            (workspace/'analyze.py').write_text("raise RuntimeError('deliberate immutable execution-failure fixture')\n")
    if oracle.get('missing_output'):
        (workspace/oracle['missing_output']).unlink()
    _,target=targets(spec)
    contracts=[contract(spec['public']['workflow'],target)] if target is not None else [contract('summary',x) for x in ('mean','median')]
    (workspace/'CONTRACT.json').write_text(json.dumps({'alternatives':contracts,
        'selection':'Use the requirement in TASK.json; ask if it is unresolved.'},indent=2)+'\n')
    (workspace/'TASK.json').write_text(json.dumps(spec['public'],indent=2)+'\n')
    return {'baseline_execution':baseline,'baseline_grade':baseline_grade,'initial_files':hashes(workspace),
            'source_data_sha256':hashlib.sha256(source().encode()).hexdigest()}
