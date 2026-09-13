"""Frozen, resumable development pilot. The model never sees the grader."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import random
import re
import shutil
import time

from .adapters import AdapterError, CodexOAuth, LocalInference
from .branches import hashes, prepare_branches, workflow
from .oracle import safe_text
from .sandbox import run, validate_input, WORKSPACE_BYTES, FILE_LIMIT

DEFAULT_BUDGET = {'model_turns': 12, 'model_call_seconds': 90, 'trial_seconds': 600,
                  'execution_seconds': 30, 'executions': 6, 'response_bytes': 131072,
                  'file_read_bytes': 65536, 'code_bytes': 65536,
                  'execution_output_bytes': 16384, 'infrastructure_retries': 0}
PROTOCOL = '''Complete the scientific analysis in the task workspace according to CORRECTION.txt
and CONTRACT.json. Return exactly one JSON object per response, with no markdown fences.
Available actions:
{"action":"read","paths":["relative/path", ...]} reads up to 8 workspace files.
{"action":"write","code":"complete Python source for analyze.py"} replaces active analyze.py.
{"action":"run"} executes python -I analyze.py in an isolated Python standard-library container.
{"action":"finish"} submits your solution; the harness will execute it again from clean outputs.
You may inspect prior code and results and reuse them. Only analyze.py can be written through
the write action. Use the run action for execution feedback. Do not edit data, requirements,
contract, prior files, or dependency map. Your program must recreate every required output.
You have no native tools, network, external packages, or access outside this workspace.
The initial context below supplies requirements, contract, and available filenames.
Hidden grading is performed only after submission and is never returned to you.
'''


def redact(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if k.lower() in ('access_token', 'refresh_token', 'id_token', 'api_key', 'authorization')
                else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'\bBearer\s+\S+', 'Bearer [REDACTED]', value, flags=re.I)
        value = re.sub(r'\bsk-[A-Za-z0-9_-]{16,}', '[REDACTED]', value)
        value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED]', value)
    return value


def write_json(path, value):
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as handle:
        json.dump(redact(value), handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def source_hashes():
    root = Path(__file__).parent
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*.py'))}


def initialize(output, adapter, budget=None, seed=1729):
    budget = dict(DEFAULT_BUDGET if budget is None else budget)
    if set(budget) != set(DEFAULT_BUDGET) or any(type(v) is not int or v <= 0 for k, v in budget.items() if k != 'infrastructure_retries'):
        raise ValueError('Invalid budget')
    if budget['infrastructure_retries'] != 0:
        raise ValueError('This pilot permits no automatic infrastructure retries')
    plan = prepare_branches(output, ['summary', 'regression'])
    order = list(range(len(plan['jobs'])))
    random.Random(seed).shuffle(order)
    config = {'phase': 'feasibility_pilot', 'created_utc': utc(), 'adapter': adapter.metadata,
              'budget': budget, 'order_seed': seed, 'order': order,
              'source_hashes': source_hashes(), 'protocol_sha256': hashlib.sha256(PROTOCOL.encode()).hexdigest(),
              'plan_sha256': hashlib.sha256((output/'plan.json').read_bytes()).hexdigest(),
              'client_transport_retries': 'Client-managed, not separately configurable; bounded by call deadline',
              'information_policy': plan['information_policy']}
    write_json(output/'config.json', config)
    (output/'config.sha256').write_text(hashlib.sha256((output/'config.json').read_bytes()).hexdigest()+'\n')
    (output/'trials').mkdir()
    return config


def read_files(workspace, paths, limit):
    if not isinstance(paths, list) or not 1 <= len(paths) <= 8:
        raise ValueError('Read requires 1 to 8 relative paths')
    result = {}
    total = 0
    for name in paths:
        if not isinstance(name, str):
            raise ValueError('Invalid path')
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError('Path must be a normalized relative filename')
        text = safe_text(workspace, name)
        total += len(text.encode())
        if total > limit:
            raise ValueError('Read exceeds byte budget')
        result[name] = text
    return result


def parse_action(text, code_limit):
    action = json.loads(text)
    if not isinstance(action, dict):
        raise ValueError('Response must be a JSON object')
    name = action.get('action')
    keys = {'read': {'action', 'paths'}, 'write': {'action', 'code'},
            'run': {'action'}, 'finish': {'action'}}
    if name not in keys or set(action) != keys[name]:
        raise ValueError('Unknown action or unexpected fields')
    if name == 'write' and (not isinstance(action['code'], str) or len(action['code'].encode()) > code_limit):
        raise ValueError('Invalid or oversized program')
    return action


def protected_hashes(workspace):
    return {k: v for k, v in hashes(workspace).items() if k != 'analyze.py' and not k.startswith('outputs/')}


def execute(workspace, budget, remaining, executor):
    # Reserve the supervisor's maximum cleanup overhead within the trial deadline.
    timeout = min(budget['execution_seconds'], int(remaining-35))
    if timeout < 1:
        raise AdapterError('budget_failure', 'Insufficient time for sandbox execution and cleanup')
    receipt = executor(workspace, timeout=timeout, output_limit=budget['execution_output_bytes'])
    if receipt.get('snapshot_error'):
        category = 'infrastructure_failure' if receipt.get('infrastructure_error') else 'model_failure'
        raise AdapterError(category, 'Execution exported no valid snapshot', receipt)
    return receipt


def trial(directory, workspace, job, config, adapter, executor=run):
    directory.mkdir()
    started = time.monotonic()
    budget = config['budget']
    deadline = started+budget['trial_seconds']
    data = safe_text(workspace, 'data/penguins.csv')
    protected = protected_hashes(workspace)
    baseline_outputs = {p.name: p.read_bytes() for p in (workspace/'prior/outputs').iterdir()}
    content = {'strategy': job['strategy'], 'files': sorted(hashes(workspace)),
               'requirements': read_files(workspace, ['CORRECTION.txt', 'CONTRACT.json'], budget['file_read_bytes']),
               'budget': budget}
    if job['strategy'] == 'dependency_repair':
        content['dependency_map'] = read_files(workspace, ['DEPENDENCIES.json'], budget['file_read_bytes'])
    messages = [{'role': 'system', 'content': PROTOCOL},
                {'role': 'user', 'content': json.dumps(content)}]
    record = {'job': job, 'started_utc': utc(), 'status': 'running', 'steps': [], 'executions': 0,
              'model_calls': 0, 'grade': None, 'unaffected_outputs': None}
    write_json(directory/'record.json', record)
    last_execution = None
    try:
        for turn in range(budget['model_turns']):
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise AdapterError('budget_failure', 'Trial deadline reached')
            step = {'turn': turn+1, 'request': messages.copy(), 'status': 'in_flight'}
            record['steps'].append(step)
            record['model_calls'] += 1
            write_json(directory/'record.json', record)
            response = adapter.generate(messages, min(remaining, budget['model_call_seconds']), budget['response_bytes'])
            step.update(status='responded', response=response)
            write_json(directory/'record.json', record)
            if time.monotonic() >= deadline:
                raise AdapterError('budget_failure', 'Trial deadline reached after inference')
            messages.append({'role': 'assistant', 'content': response['text']})
            try:
                action = parse_action(response['text'], budget['code_bytes'])
                step['action'] = action
                name = action['action']
                if name == 'read':
                    feedback = {'files': read_files(workspace, action['paths'], budget['file_read_bytes'])}
                elif name == 'write':
                    path = workspace/'analyze.py'
                    # All snapshots are validated; still fail closed if callers altered the tree.
                    if path.is_symlink():
                        raise ValueError('Invalid active program')
                    path.write_text(action['code'])
                    last_execution = None
                    feedback = {'written': 'analyze.py'}
                else:
                    if record['executions'] >= budget['executions']:
                        raise AdapterError('budget_failure', 'Execution budget exhausted')
                    if name == 'finish':
                        # Preserve submitted outputs, then verify code regenerates the outputs.
                        if (workspace/'outputs').exists():
                            shutil.copytree(workspace/'outputs', directory/'submitted_outputs')
                            shutil.rmtree(workspace/'outputs')
                    record['executions'] += 1
                    step['status'] = 'executing'
                    write_json(directory/'record.json', record)
                    last_execution = execute(workspace, budget, deadline-time.monotonic(), executor)
                    step['execution'] = last_execution
                    if time.monotonic() >= deadline:
                        raise AdapterError('budget_failure', 'Trial deadline reached after execution')
                    if protected_hashes(workspace) != protected:
                        raise AdapterError('model_failure', 'Candidate changed protected input or reference files')
                    feedback = {k: last_execution.get(k) for k in ('exit_code', 'stdout', 'termination')}
                    if name == 'finish':
                        _, evaluate, _ = workflow(job['workflow'])
                        grade = evaluate(workspace, data, job['target'])
                        record['grade'] = grade
                        successful_execution = last_execution['exit_code'] == 0 and not last_execution.get('termination')
                        record['status'] = 'success' if successful_execution and grade['complete'] else 'model_failure'
                        if job['case'] == 'unchanged':
                            invariant_names = list(baseline_outputs)
                        elif job['case'] in ('median_requirement', 'flipper_cm'):
                            invariant_names = ['sample_counts.json']
                        else:
                            invariant_names = []
                        record['unaffected_outputs'] = {name: {
                            'byte_identical': (workspace/'outputs'/name).is_file() and (workspace/'outputs'/name).read_bytes() == baseline_outputs[name]
                        } for name in invariant_names}
                        step['status'] = 'completed'
                        break
                step.update(status='completed', feedback=feedback)
            except (ValueError, OSError, TypeError) as exc:
                feedback = {'protocol_error': str(exc)}
                step.update(status='protocol_error', feedback=feedback)
            messages.append({'role': 'user', 'content': json.dumps(feedback)})
            write_json(directory/'record.json', record)
        else:
            record['status'] = 'budget_failure'
            record['error'] = 'Model-turn budget exhausted without submission'
    except AdapterError as exc:
        record.update(status=exc.category, error=str(exc), failure_receipt=exc.receipt)
    except Exception as exc:
        record.update(status='infrastructure_failure', error=type(exc).__name__+': '+str(exc))
    finally:
        record.update(finished_utc=utc(), elapsed_seconds=time.monotonic()-started,
                      final_files=hashes(workspace))
        write_json(directory/'record.json', record)
    return record


def resume(output, adapter, executor=run):
    # Kernel-released lock: a stale PID or lock file never licenses concurrent execution.
    with (output/'runner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config = json.loads((output/'config.json').read_text())
        if hashlib.sha256((output/'config.json').read_bytes()).hexdigest() != (output/'config.sha256').read_text().strip():
            raise ValueError('Frozen configuration changed')
        if config['source_hashes'] != source_hashes() or config['adapter'] != adapter.metadata:
            raise ValueError('Runner sources or adapter changed; create a documented new run')
        if config['plan_sha256'] != hashlib.sha256((output/'plan.json').read_bytes()).hexdigest():
            raise ValueError('Frozen task plan changed')
        plan = json.loads((output/'plan.json').read_text())
        for index in config['order']:
            job = plan['jobs'][index]
            directory = output/'trials'/f'{index:02d}'
            if (directory/'record.json').exists():
                record = json.loads((directory/'record.json').read_text())
                if record['status'] == 'running':
                    record.update(status='interrupted', error='Prior runner exited; ambiguous in-flight call is not retried', finished_utc=utc())
                    write_json(directory/'record.json', record)
                continue
            workspace = output/job['workspace']
            validate_input(workspace, WORKSPACE_BYTES, FILE_LIMIT)
            if hashes(workspace) != job['initial_files']:
                raise ValueError('Unstarted workspace was modified')
            record = trial(directory, workspace, job, config, adapter, executor)
            print(json.dumps({'trial': index, 'workflow': job['workflow'], 'case': job['case'],
                              'strategy': job['strategy'], 'status': record['status']}), flush=True)
            if record['status'] == 'access_failure':
                # No repeated subscription requests when access/usage limits stop the pilot.
                break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'run'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--adapter', choices=['codex_oauth', 'local'], required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--endpoint', default='http://127.0.0.1:8765/v1')
    parser.add_argument('--runtime-manifest', type=Path)
    args = parser.parse_args()
    runtime = json.loads(args.runtime_manifest.read_text()) if args.runtime_manifest else None
    adapter = CodexOAuth(args.model) if args.adapter == 'codex_oauth' else LocalInference(args.model, args.endpoint, runtime=runtime)
    if args.command == 'init':
        initialize(args.output, adapter)
    else:
        resume(args.output, adapter)


if __name__ == '__main__':
    main()
