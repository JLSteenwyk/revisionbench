"""Trusted evaluator: never imports or executes candidate analysis code."""
import csv
from decimal import Decimal
import io
import json
import math
from pathlib import Path
import stat
import xml.etree.ElementTree as ET


def expected(csv_text, statistic):
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    grouped, counts = {}, {}
    for row in rows:
        name = row['species']
        counts[name] = counts.get(name, 0) + 1
        if row['body_mass_g'] != 'NA':
            grouped.setdefault(name, []).append(Decimal(row['body_mass_g']))
    result = {}
    for name, values in sorted(grouped.items()):
        if statistic == 'mean':
            mass = sum(values) / len(values)
        elif statistic == 'median':
            ordered = sorted(values)
            mass = (ordered[(len(ordered)-1)//2] + ordered[len(ordered)//2]) / 2
        else:
            raise ValueError('Unknown target statistic')
        result[name] = {'n': len(values), 'mass_g': float(mass)}
    largest = max(result, key=lambda k: result[k]['mass_g'])
    return {'summary': result, 'counts': counts,
            'conclusions': {'statistic': statistic, 'largest_species': largest,
                            'largest_mass_g': result[largest]['mass_g']}}


def safe_text(root, relative):
    """Reject symlinks, special files and large outputs before reading."""
    root = root.resolve()
    path = root
    for part in Path(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink in candidate output')
    if not path.resolve().is_relative_to(root):
        raise ValueError('Output escaped workspace')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 2_000_000:
        raise ValueError('Output is not a bounded regular file')
    return path.read_text()


def numeric(value, target, tolerance=1e-5):
    return type(value) in (int, float) and math.isfinite(value) and abs(value-target) <= tolerance


def evaluate(workspace, csv_text, statistic):
    target = expected(csv_text, statistic)
    checks, errors = {}, {}

    def check(name, function):
        try:
            checks[name] = bool(function())
        except (OSError, ValueError, TypeError, KeyError, ET.ParseError, AttributeError) as error:
            checks[name] = False
            errors[name] = type(error).__name__

    read = lambda name: safe_text(workspace, 'outputs/'+name)

    def summary_ok():
        actual = json.loads(read('summary.json'))
        return set(actual) == set(target['summary']) and all(
            type(actual[k]['n']) is int and actual[k]['n'] == v['n'] and numeric(actual[k]['mass_g'], v['mass_g'])
            for k, v in target['summary'].items())

    def table_ok():
        rows = list(csv.DictReader(io.StringIO(read('table.csv'))))
        by = {r['species']: r for r in rows}
        return len(rows) == len(by) == len(target['summary']) and set(by) == set(target['summary']) and all(
            int(by[k]['n']) == v['n'] and numeric(float(by[k]['mass_g']), v['mass_g']) for k, v in target['summary'].items())

    def figure_ok():
        xml = ET.fromstring(read('figure.svg'))
        ns = '{http://www.w3.org/2000/svg}'
        if xml.tag != ns+'svg' or xml.findtext(ns+'title') != f'{statistic} body mass (g); 1 pixel = 10 g':
            return False
        rects = xml.findall(ns+'rect')
        by = {r.attrib['id']: r for r in rects}
        return len(rects) == len(by) == len(target['summary']) and set(by) == set(target['summary']) and all(
            numeric(float(by[k].attrib['width'])*10, v['mass_g']) for k, v in target['summary'].items())

    def conclusions_ok():
        actual = json.loads(read('conclusions.json'))
        reference = target['conclusions']
        return actual['statistic'] == reference['statistic'] and actual['largest_species'] == reference['largest_species'] and numeric(actual['largest_mass_g'], reference['largest_mass_g'])

    check('input_preserved', lambda: safe_text(workspace, 'data/penguins.csv') == csv_text)
    check('summary', summary_ok)
    check('table', table_ok)
    check('figure_data_and_title', figure_ok)
    check('conclusions', conclusions_ok)
    check('sample_counts', lambda: json.loads(read('sample_counts.json')) == target['counts'])
    return {'complete': all(checks.values()), 'checks': checks, 'errors': errors,
            'scope': 'Fixed output contract, numerical artifacts, SVG bar widths/title and structured claims. Does not judge unrestricted prose, visual aesthetics or scientific validity.'}
