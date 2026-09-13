"""Matched starting states for development; no model inference."""
import hashlib
import datetime
import json
from pathlib import Path
import shutil

from . import fixtures, oracle, regression
from .sandbox import run

STRATEGIES = ('repair', 'rebuild', 'dependency_repair')


def workflow(name):
    if name == 'summary':
        return fixtures, oracle.evaluate, 'mean'
    if name == 'regression':
        return regression, regression.evaluate, 'mm'
    raise ValueError('Unknown workflow')


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def contract(name, target):
    common = {'input': 'data/penguins.csv', 'output_directory': 'outputs',
              'sample_counts.json': 'JSON object mapping species to counts over all input rows',
              'missing_value': 'NA'}
    if name == 'summary':
        common.update({
            'summary.json': 'JSON object mapping species to {"n": integer, "mass_g": number}; exclude missing body mass',
            'table.csv': 'Header species,n,mass_g; exactly one row per species',
            'figure.svg': f'SVG namespace http://www.w3.org/2000/svg, title "{target} body mass (g); 1 pixel = 10 g"; one direct rect per species, id=species and width=mass_g/10',
            'conclusions.json': f'Object with statistic="{target}", largest_species, largest_mass_g',
            'absolute_tolerance_g': .00001})
    else:
        common.update({
            'fit.json': 'Object with n (integer), slope, intercept, r_squared; OLS with intercept, using rows nonmissing in predictor and outcome',
            'predictions.csv': f'Header flipper_length,predicted_mass_g, ordered probes { [18,20,22] if target=="cm" else [180,200,220] }',
            'figure.svg': f'SVG namespace http://www.w3.org/2000/svg, title "OLS body mass (g) versus flipper length ({target})"; one direct line id=fit, x1=50,x2=590, y1=280-first_prediction/25, y2=280-last_prediction/25',
            'conclusions.json': f'Object with predictor="flipper_length_{target}", unit="{target}", association=positive/negative/zero according to slope, model_n=number of fitted observations',
            'fit_absolute_tolerance': 1e-8, 'prediction_absolute_tolerance_g': 1e-6,
            'figure_coordinate_absolute_tolerance': 1e-7})
    return common


def prepare_branches(output, names):
    output.mkdir(parents=True, exist_ok=False)
    jobs = []
    baselines = []
    for name in names:
        module, evaluate, initial_target = workflow(name)
        base = output/'baselines'/name
        module.prepare(base)
        execution = run(base)
        score = evaluate(base, fixtures.source(), initial_target)
        if execution['exit_code'] != 0 or execution['snapshot_error'] or not score['complete']:
            raise RuntimeError(f'Invalid baseline {name}: {execution}')
        baselines.append({'workflow': name, 'execution': execution, 'score': score})
        for case in module.CASES:
            for strategy in STRATEGIES:
                path = output/'workspaces'/name/case/strategy
                shutil.copytree(base, path)
                prior = path/'prior'
                prior.mkdir()
                shutil.copyfile(base/'analyze.py', prior/'analyze.py')
                shutil.copytree(base/'outputs', prior/'outputs')
                data, target = module.apply_correction(path, case)
                (path/'CONTRACT.json').write_text(json.dumps(contract(name, target), indent=2)+'\n')
                if strategy == 'rebuild':
                    (path/'analyze.py').unlink()
                    shutil.rmtree(path/'outputs')
                if strategy == 'dependency_repair':
                    (path/'DEPENDENCIES.json').write_text(json.dumps({
                        'provenance': 'Benchmark-author supplied; oracle map, not agent-discovered',
                        'edges': [['data/penguins.csv', 'analyze.py'], ['CORRECTION.txt', 'analyze.py']]
                                 + [['analyze.py', 'outputs/'+p.name] for p in sorted((base/'outputs').iterdir())]
                    }, indent=2)+'\n')
                jobs.append({'workflow': name, 'case': case, 'strategy': strategy,
                             'workspace': str(path.relative_to(output)), 'target': target,
                             'corrected_input_sha256': hashlib.sha256(data.encode()).hexdigest(),
                             'initial_files': hashes(path)})
    source_files = {str(p.relative_to(fixtures.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(fixtures.ROOT.rglob('*.py'))}
    manifest = {'phase': 'development', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_files_sha256': source_files,
                'model_inference': False, 'jobs': jobs, 'baselines': baselines,
                'information_policy': 'All strategies see identical corrected input, requirements, output contract, and prior code/outputs. Rebuild starts with no active code/outputs but may reuse prior code. Dependency repair additionally receives an author-supplied oracle map. No hidden expected numbers are supplied.'}
    (output/'plan.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
