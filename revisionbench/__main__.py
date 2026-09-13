"""Run a small deterministic feasibility demonstration; no model inference."""
import argparse
import json
from pathlib import Path

from .fixtures import source
from .branches import prepare_branches, workflow
from .sandbox import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['smoke', 'prepare'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workflow', choices=['summary', 'regression', 'all'], default='summary')
    args = parser.parse_args()
    names = ['summary', 'regression'] if args.workflow == 'all' else [args.workflow]
    if args.command == 'prepare':
        result = prepare_branches(args.output, names)
        print(json.dumps({'workspaces_prepared': len(result['jobs']), 'model_inference': False}))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for name, case in [(name, case) for name in names for case in workflow(name)[0].CASES]:
        module, evaluate, initial_target = workflow(name)
        workspace = args.output/name/case
        module.prepare(workspace)
        initial_run = run(workspace)
        initial_score = evaluate(workspace, source(), initial_target)
        if initial_run['exit_code'] != 0 or initial_run['snapshot_error'] or not initial_score['complete']:
            raise RuntimeError(f'Initial project failed validation: {initial_run}')
        data, statistic = module.apply_correction(workspace, case)
        stale = evaluate(workspace, data, statistic)
        rerun = run(workspace)
        rerun_score = evaluate(workspace, data, statistic)
        # A known repair validates solvability, not AI capability.
        module.known_repair(workspace, case)
        repaired_run = run(workspace)
        repaired_score = evaluate(workspace, data, statistic)
        record = {'workflow': name, 'case': case, 'initial_run': initial_run, 'initial_score': initial_score,
                  'stale_score': stale, 'clean_rerun': rerun, 'clean_rerun_score': rerun_score,
                  'known_repair_run': repaired_run, 'known_repair_score': repaired_score}
        records.append(record)
        (args.output/'evidence.json').write_text(json.dumps({'phase': 'development_fixture_validation',
            'model_inference': False, 'records': records}, indent=2)+'\n')
        assert repaired_run['exit_code'] == 0 and not repaired_run['snapshot_error'] and repaired_score['complete']
        assert rerun_score['complete'] == (case not in ('median_requirement', 'flipper_cm'))
        assert stale['complete'] == (case == 'unchanged')
        print(json.dumps({'workflow': name, 'case': case, 'stale_complete': stale['complete'],
                          'clean_rerun_complete': rerun_score['complete'],
                          'known_repair_complete': repaired_score['complete']}), flush=True)


if __name__ == '__main__':
    main()
