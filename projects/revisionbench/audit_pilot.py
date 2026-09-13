"""Audit a finished pilot against its frozen plan and current on-disk artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from revisionbench.branches import hashes, workflow
from revisionbench.runner import source_hashes, write_json


def audit(root):
    config = json.loads((root/'config.json').read_text())
    plan = json.loads((root/'plan.json').read_text())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(root/'config.json') == (root/'config.sha256').read_text().strip()
    assert digest(root/'plan.json') == config['plan_sha256']
    assert source_hashes() == config['source_hashes']
    assert sorted(config['order']) == list(range(18))
    assert len(plan['jobs']) == 18
    record_paths = sorted((root/'trials').glob('*/record.json'))
    assert len(record_paths) == 18
    actual_order = sorted((json.loads(p.read_text())['started_utc'], int(p.parent.name)) for p in record_paths)
    assert [i for _, i in actual_order] == config['order'], 'Execution order differs from frozen randomization'
    sessions = []
    counts = {'trials': 0, 'model_calls': 0, 'sandbox_executions': 0, 'artifact_checks': 0,
              'protocol_errors': 0, 'successes': 0, 'failures': {}}
    for i, job in enumerate(plan['jobs']):
        record = json.loads((root/'trials'/f'{i:02d}'/'record.json').read_text())
        assert record['job'] == job
        assert record['status'] != 'running'
        assert record['started_utc'] >= config['created_utc']
        workspace = root/job['workspace']
        assert hashes(workspace) == record['final_files']
        assert record['model_calls'] == len(record['steps']) <= config['budget']['model_turns']
        assert record['executions'] <= config['budget']['executions']
        counts['model_calls'] += record['model_calls']
        counts['sandbox_executions'] += record['executions']
        counts['trials'] += 1
        history = None
        for step in record['steps']:
            if history is not None:
                assert history == step['request'], 'Conversation contains undeclared feedback'
            history = step['request'].copy()
            if 'response' in step:
                response = step['response']
                receipt = response['receipt']
                assert receipt['exit_code'] == 0 and receipt['termination'] is None
                assert receipt['wall_seconds'] <= config['budget']['model_call_seconds']+5
                assert len((receipt['stdout']+receipt['stderr']).encode()) <= config['budget']['response_bytes']
                events = [json.loads(line) for line in receipt['stdout'].splitlines()]
                ids = [e['thread_id'] for e in events if e['type']=='thread.started']
                assert len(ids)==1
                sessions.extend(ids)
                assert all(e['item']['type'] in ('agent_message','reasoning','error')
                           for e in events if e['type']=='item.completed')
                history.append({'role':'assistant','content':response['text']})
            if 'feedback' in step:
                history.append({'role':'user','content':json.dumps(step['feedback'])})
            counts['protocol_errors'] += step['status']=='protocol_error'
        if record['status']=='success':
            last = record['steps'][-1]
            assert last['action']['action']=='finish'
            execution = last['execution']
            assert execution['exit_code']==0 and execution['snapshot_error'] is None and execution['termination'] is None
            module, evaluate, _ = workflow(job['workflow'])
            data, target = module.correction(job['case'])
            assert hashlib.sha256(data.encode()).hexdigest()==job['corrected_input_sha256']
            assert evaluate(workspace, data, target)==record['grade']
            assert record['grade']['complete']
            assert all(record['grade']['checks'].values())
            protected = {k:v for k,v in record['final_files'].items() if k!='analyze.py' and not k.startswith('outputs/')}
            initial = {k:v for k,v in job['initial_files'].items() if k!='analyze.py' and not k.startswith('outputs/')}
            assert protected == initial
            assert record['elapsed_seconds'] <= config['budget']['trial_seconds']+5
            counts['artifact_checks'] += len(record['grade']['checks'])
            counts['successes'] += 1
        else:
            counts['failures'][record['status']] = counts['failures'].get(record['status'], 0)+1
    assert len(sessions) == len(set(sessions)), 'CLI session reused across calls'
    result = {'audit_passed': True, 'config_sha256': digest(root/'config.json'),
              'checks': counts, 'unique_ephemeral_sessions':len(sessions),
              'scope':'Frozen source/config/plan, complete trial accounting, fresh sessions, declared feedback chain, budgets, protected inputs, final artifact hashes and independent regrading of all recorded successes.'}
    write_json(root/'audit.json', result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args=parser.parse_args()
    print(json.dumps(audit(args.root),indent=2))
