"""Descriptive pilot reporting; no significance or generalization claims."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from .runner import write_json


def summarize(root):
    config = json.loads((root/'config.json').read_text())
    records = [json.loads(p.read_text()) for p in sorted((root/'trials').glob('*/record.json'))]
    groups = {}
    for strategy in ('repair', 'rebuild', 'dependency_repair'):
        rows = [r for r in records if r['job']['strategy'] == strategy]
        completed = [r for r in rows if r.get('grade') is not None]
        usages = [s.get('response', {}).get('usage') for r in rows for s in r['steps'] if 'response' in s]
        usage_totals = {}
        for key in sorted({k for u in usages if isinstance(u, dict) for k in u if isinstance(u[k], (int, float))}):
            usage_totals[key] = sum(u.get(key, 0) for u in usages if isinstance(u, dict))
        groups[strategy] = {
            'trials': len(rows), 'successful': sum(r['status']=='success' for r in rows),
            'statuses': dict(Counter(r['status'] for r in rows)),
            'artifact_checks': {k: {'passed': sum(r['grade']['checks'].get(k, False) for r in completed),
                                     'graded': sum(k in r['grade']['checks'] for r in completed)}
                                for k in sorted({k for r in completed for k in r['grade']['checks']})},
            'model_calls': sum(r.get('model_calls',0) for r in rows),
            'requested_actions': dict(Counter(s['action']['action'] for r in rows for s in r['steps'] if 'action' in s)),
            'sandbox_executions': sum(r.get('executions',0) for r in rows),
            'median_elapsed_seconds': statistics.median(r['elapsed_seconds'] for r in rows) if rows and all('elapsed_seconds' in r for r in rows) else None,
            'usage_totals': usage_totals or None,
            'usage_available_calls': sum(u is not None for u in usages),
            'unaffected_byte_comparisons': [{'case':r['job']['case'], 'workflow':r['job']['workflow'], 'outputs':r['unaffected_outputs']}
                                          for r in rows if r.get('unaffected_outputs')],
        }
    result = {'model':config['adapter'], 'recorded_trials':len(records), 'planned_trials':len(config['order']),
              'strategies':groups, 'statuses':dict(Counter(r['status'] for r in records)),
              'separately_billed_inference_used':False, 'dollar_cost':None,
              'gpu_usage':None, 'peak_client_memory':None,
              'limitations':['Six calibration cases across two workflows on one dataset; one model and one trial per cell.',
                  'No significance tests, broad superiority, novelty or publication-readiness claims.',
                  'Oracle dependency map is simple and author-supplied; rebuild can reuse prior code.',
                  'Fresh stateless CLI invocation per model turn; earlier visible conversation is replayed.',
                  'Provider-side sampling and snapshot version are not pinned; hosted replay is not guaranteed identical.',
                  'Byte identity is a stricter diagnostic than semantic correctness; sample_counts grading checks semantics.',
                  'Elapsed time includes client startup, authentication, provider queueing, inference and sandbox execution.',
                  'Token counts reflect reported usage, including repeated context; cached/reasoning tokens are subsets, not extra totals.']}
    write_json(root/'summary.json', result)
    lines = ['# RevisionBench feasibility pilot', '',
             f"Model: `{config['adapter']['model']}` via `{config['adapter']['adapter']}`. Recorded {len(records)} of {len(config['order'])} planned trials.", '',
             '| Strategy | Success | Model calls | Sandbox executions | Median elapsed seconds |',
             '| --- | ---: | ---: | ---: | ---: |']
    for name, group in groups.items():
        elapsed = group['median_elapsed_seconds']
        lines.append(f"| {name} | {group['successful']}/{group['trials']} | {group['model_calls']} | {group['sandbox_executions']} | {round(elapsed,2) if elapsed is not None else 'unavailable'} |")
    lines += ['', 'Statuses: '+json.dumps(result['statuses'])+'.', '',
              'Artifact-level checks, usage totals and unaffected-output comparisons are in `summary.json`. '
              'Every final grade requires a valid snapshot from execution with clean outputs. '
              'Missing grades are not counted as artifact passes. No grader feedback was supplied to the model.', '',
              'Limitations:', ''] + ['- '+x for x in result['limitations']]
    lines += ['', 'No separately billed inference was used. Dollar cost, GPU utilization and peak client memory are unavailable.', '']
    (root/'report.md').write_text('\n'.join(lines))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.root)['statuses']))
