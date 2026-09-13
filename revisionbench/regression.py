"""Regression fixture and independent Decimal-based reference calculations."""
import csv
from decimal import Decimal
import io
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from .fixtures import ROOT, source
from .oracle import numeric, safe_text

CASES = ('unchanged', 'exclude_2007', 'flipper_cm')


def correction(case):
    if case not in CASES:
        raise ValueError('Unknown regression case')
    data = source()
    if case == 'unchanged':
        return data, 'mm'
    reader = csv.DictReader(io.StringIO(data))
    fields = list(reader.fieldnames)
    rows = list(reader)
    if case == 'exclude_2007':
        rows = [r for r in rows if r['year'] != '2007']
    else:
        fields[fields.index('flipper_length_mm')] = 'flipper_length_cm'
        for row in rows:
            value = row.pop('flipper_length_mm')
            row['flipper_length_cm'] = value if value == 'NA' else str(Decimal(value)/10)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue(), 'cm' if case == 'flipper_cm' else 'mm'


def expected(data, unit):
    predictor = 'flipper_length_'+unit
    rows = list(csv.DictReader(io.StringIO(data)))
    pairs = [(Decimal(r[predictor]), Decimal(r['body_mass_g'])) for r in rows
             if r[predictor] != 'NA' and r['body_mass_g'] != 'NA']
    n = len(pairs)
    mx, my = (sum(p[i] for p in pairs)/n for i in (0, 1))
    covariance = sum((x-mx)*(y-my) for x, y in pairs)
    xx = sum((x-mx)**2 for x, _ in pairs)
    yy = sum((y-my)**2 for _, y in pairs)
    slope = covariance/xx
    intercept = my-slope*mx
    r_squared = covariance**2/(xx*yy)
    probes = [Decimal(x)/(10 if unit == 'cm' else 1) for x in (180, 200, 220)]
    return {'fit': {'n': n, 'slope': float(slope), 'intercept': float(intercept), 'r_squared': float(r_squared)},
            'predictions': [(float(x), float(intercept+slope*x)) for x in probes],
            'conclusions': {'predictor': predictor, 'unit': unit, 'association': 'positive' if slope > 0 else 'negative' if slope < 0 else 'zero', 'model_n': n},
            'counts': {s: sum(r['species']==s for r in rows) for s in {r['species'] for r in rows}}}


def evaluate(workspace, data, unit):
    target = expected(data, unit)
    checks, errors = {}, {}
    read = lambda name: safe_text(workspace, 'outputs/'+name)

    def check(name, function):
        try:
            checks[name] = bool(function())
        except (OSError, ValueError, TypeError, KeyError, ET.ParseError, AttributeError, IndexError) as error:
            checks[name] = False
            errors[name] = type(error).__name__

    def fit_ok():
        actual = json.loads(read('fit.json'))
        return type(actual['n']) is int and actual['n']==target['fit']['n'] and all(
            numeric(actual[k], target['fit'][k], 1e-8) for k in ('slope', 'intercept', 'r_squared'))

    def predictions_ok():
        actual = list(csv.DictReader(io.StringIO(read('predictions.csv'))))
        return len(actual)==3 and all(numeric(float(row['flipper_length']), x) and
            numeric(float(row['predicted_mass_g']), y, 1e-6) for row, (x, y) in zip(actual, target['predictions']))

    def figure_ok():
        xml = ET.fromstring(read('figure.svg'))
        ns = '{http://www.w3.org/2000/svg}'
        lines = xml.findall(ns+'line')
        if xml.findtext(ns+'title') != f'OLS body mass (g) versus flipper length ({unit})' or len(lines)!=1:
            return False
        a = lines[0].attrib
        return a['id']=='fit' and numeric(float(a['x1']), 50) and numeric(float(a['x2']), 590) and all(
            numeric(float(a[k]), 280-y/25, 1e-7) for k, (_, y) in zip(('y1','y2'), (target['predictions'][0], target['predictions'][-1])))

    check('input_preserved', lambda: safe_text(workspace, 'data/penguins.csv')==data)
    check('fit', fit_ok)
    check('predictions', predictions_ok)
    check('figure_data_and_title', figure_ok)
    check('conclusions', lambda: json.loads(read('conclusions.json'))==target['conclusions'])
    check('sample_counts', lambda: json.loads(read('sample_counts.json'))==target['counts'])
    return {'complete': all(checks.values()), 'checks': checks, 'errors': errors,
            'scope': 'OLS coefficients, r-squared, fixed predictions, SVG endpoints/title and specified claims; no causal or unrestricted scientific validity judgment.'}


def prepare(workspace):
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace/'data').mkdir()
    (workspace/'data/penguins.csv').write_text(source())
    shutil.copyfile(ROOT/'templates/regression.py', workspace/'analyze.py')


def apply_correction(workspace, case):
    data, unit = correction(case)
    (workspace/'data/penguins.csv').write_text(data)
    (workspace/'CORRECTION.txt').write_text(f'''Correct the completed OLS analysis for case {case}.
The authoritative predictor is flipper_length_{unit}, in {unit}; outcome is body_mass_g.
Use ordinary least squares with an intercept. Exclude only rows missing either
variable. Update fit.json, predictions.csv, figure.svg, conclusions.json and
sample_counts.json in outputs/. Sample counts include all input rows.
Prediction probes are { [18,20,22] if unit=='cm' else [180,200,220] } {unit}.
This is a hypothetical benchmark correction, not a source-data erratum.
''')
    return data, unit


def known_repair(workspace, case):
    if case == 'flipper_cm':
        path = workspace/'analyze.py'
        path.write_text(path.read_text().replace("predictor = 'flipper_length_mm'", "predictor = 'flipper_length_cm'")
                        .replace("unit = 'mm'", "unit = 'cm'").replace('[180.0, 200.0, 220.0]', '[18.0, 20.0, 22.0]'))
