"""Baseline OLS fit of body mass on flipper length, with an intercept."""
import csv
import json
from pathlib import Path
import statistics

predictor = 'flipper_length_mm'
unit = 'mm'
probes = [180.0, 200.0, 220.0]
rows = list(csv.DictReader(Path('data/penguins.csv').open()))
pairs = [(float(r[predictor]), float(r['body_mass_g'])) for r in rows
         if r[predictor] != 'NA' and r['body_mass_g'] != 'NA']
x, y = zip(*pairs)
slope, intercept = statistics.linear_regression(x, y)
residual = sum((mass-(intercept+slope*length))**2 for length, mass in pairs)
total = sum((mass-statistics.mean(y))**2 for mass in y)
fit = {'n': len(pairs), 'slope': slope, 'intercept': intercept, 'r_squared': 1-residual/total}
out = Path('outputs')
out.mkdir(exist_ok=True)
(out/'fit.json').write_text(json.dumps(fit, indent=2))
with (out/'predictions.csv').open('w') as handle:
    writer = csv.writer(handle)
    writer.writerow(['flipper_length', 'predicted_mass_g'])
    writer.writerows((v, f'{intercept+slope*v:.9f}') for v in probes)
(out/'figure.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="300">'
    f'<title>OLS body mass (g) versus flipper length ({unit})</title>'
    f'<line id="fit" x1="50" y1="{280-(intercept+slope*probes[0])/25:.9f}" '
    f'x2="590" y2="{280-(intercept+slope*probes[-1])/25:.9f}" stroke="steelblue"/>'
    f'<text x="30" y="295">{probes[0]} {unit}</text><text x="530" y="295">{probes[-1]} {unit}</text></svg>')
(out/'conclusions.json').write_text(json.dumps({'predictor': predictor, 'unit': unit,
    'association': 'positive' if slope > 0 else 'negative' if slope < 0 else 'zero', 'model_n': len(pairs)}))
(out/'sample_counts.json').write_text(json.dumps({s: sum(r['species']==s for r in rows)
                                               for s in sorted({r['species'] for r in rows})}))
