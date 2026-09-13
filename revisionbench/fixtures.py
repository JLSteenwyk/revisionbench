"""Prepare a development project and trusted correction specification."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CASES = ('unchanged', 'exclude_2007', 'median_requirement')


def source():
    provenance = json.loads((ROOT/'data/provenance.json').read_text())
    data = (ROOT/'data/penguins.csv').read_bytes()
    assert hashlib.sha256(data).hexdigest() == provenance['files']['penguins.csv']['sha256']
    return data.decode()


def correction(case):
    if case not in CASES:
        raise ValueError('Unknown development case')
    data = source()
    if case == 'exclude_2007':
        reader = csv.DictReader(io.StringIO(data))
        buffer = io.StringIO(newline='')
        writer = csv.DictWriter(buffer, fieldnames=reader.fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(r for r in reader if r['year'] != '2007')
        data = buffer.getvalue()
    return data, 'median' if case == 'median_requirement' else 'mean'


def prepare(workspace):
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace/'data').mkdir()
    (workspace/'data/penguins.csv').write_text(source())
    shutil.copyfile(ROOT/'templates/analyze.py', workspace/'analyze.py')


def apply_correction(workspace, case):
    data, statistic = correction(case)
    (workspace/'data/penguins.csv').write_text(data)
    requirements = f'''Update the completed analysis for correction case: {case}.
The current data/penguins.csv is authoritative and must not be edited.
Compute the {statistic} body mass in grams by species, excluding only missing
body masses. Use every remaining row for sample_counts.json.
Update all five outputs: summary.json, table.csv, figure.svg, conclusions.json,
and sample_counts.json under outputs/. Preserve the supplied output schemas.
The SVG title must be "{statistic} body mass (g); 1 pixel = 10 g"; each species
has one direct SVG rect whose id is the species and width is mass_g / 10.
The structured conclusion must name the statistic, species with largest value,
and its mass in grams. Values must agree to absolute tolerance 0.00001 grams.
This is a hypothetical benchmark correction, not an erratum to the source data.
'''
    (workspace/'CORRECTION.txt').write_text(requirements)
    return data, statistic
