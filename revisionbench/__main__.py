"""Run a small deterministic feasibility demonstration; no model inference."""
import argparse
import json
from pathlib import Path

from .fixtures import CASES, apply_correction, prepare, source
from .oracle import evaluate
from .sandbox import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['smoke'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for case in CASES:
        workspace = args.output/case
        prepare(workspace)
        initial_run = run(workspace)
        initial_score = evaluate(workspace, source(), 'mean')
        if initial_run['exit_code'] != 0 or not initial_score['complete']:
            raise RuntimeError(f'Initial project failed validation: {initial_run}')
        data, statistic = apply_correction(workspace, case)
        stale = evaluate(workspace, data, statistic)
        rerun = run(workspace)
        rerun_score = evaluate(workspace, data, statistic)
        # A known repair validates solvability, not AI capability.
        if case == 'median_requirement':
            script = workspace/'analyze.py'
            script.write_text(script.read_text().replace('statistics.mean(values)', 'statistics.median(values)').replace("statistic = 'mean'", "statistic = 'median'"))
        repaired_run = run(workspace)
        repaired_score = evaluate(workspace, data, statistic)
        record = {'case': case, 'initial_run': initial_run, 'initial_score': initial_score,
                  'stale_score': stale, 'clean_rerun': rerun, 'clean_rerun_score': rerun_score,
                  'known_repair_run': repaired_run, 'known_repair_score': repaired_score}
        records.append(record)
        (args.output/'evidence.json').write_text(json.dumps({'phase': 'development_fixture_validation',
            'model_inference': False, 'records': records}, indent=2)+'\n')
        assert repaired_run['exit_code'] == 0 and repaired_score['complete']
        assert rerun_score['complete'] == (case != 'median_requirement')
        assert stale['complete'] == (case == 'unchanged')
        print(json.dumps({'case': case, 'stale_complete': stale['complete'],
                          'clean_rerun_complete': rerun_score['complete'],
                          'known_repair_complete': repaired_score['complete']}), flush=True)


if __name__ == '__main__':
    main()
