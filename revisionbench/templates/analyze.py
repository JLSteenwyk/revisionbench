"""Initial, correct analysis: species means of observed body mass."""
import csv
import json
from pathlib import Path
import statistics

rows = list(csv.DictReader(Path('data/penguins.csv').open()))
groups = {}
for row in rows:
    if row['body_mass_g'] != 'NA':
        groups.setdefault(row['species'], []).append(float(row['body_mass_g']))
summary = {name: {'n': len(values), 'mass_g': statistics.mean(values)}
           for name, values in sorted(groups.items())}
out = Path('outputs')
out.mkdir(exist_ok=True)
(out/'summary.json').write_text(json.dumps(summary, indent=2))
with (out/'table.csv').open('w') as handle:
    writer = csv.writer(handle)
    writer.writerow(['species', 'n', 'mass_g'])
    writer.writerows((name, values['n'], f"{values['mass_g']:.6f}") for name, values in summary.items())
statistic = 'mean'
bars = []
for i, (name, values) in enumerate(summary.items()):
    width = values['mass_g'] / 10
    bars.append(f'<rect id="{name}" x="100" y="{40+i*50}" width="{width:.6f}" height="20" fill="steelblue"/>')
    bars.append(f'<text x="0" y="{55+i*50}">{name}</text>')
(out/'figure.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="220">'
                            f'<title>{statistic} body mass (g); 1 pixel = 10 g</title>' + ''.join(bars) + '</svg>')
largest = max(summary, key=lambda name: summary[name]['mass_g'])
(out/'conclusions.json').write_text(json.dumps({'statistic': statistic, 'largest_species': largest,
                                               'largest_mass_g': summary[largest]['mass_g']}, indent=2))
# This output uses all rows, independently of mass missingness or estimator choice.
counts = {name: sum(row['species'] == name for row in rows) for name in sorted(groups)}
(out/'sample_counts.json').write_text(json.dumps(counts, indent=2))
