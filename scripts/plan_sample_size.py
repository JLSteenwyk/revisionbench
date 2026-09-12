"""Prospective simulation for a paired source-by-permission contrast.

This is a planning DGP, not model evidence. Shared task propensities are drawn
from a scaled beta distribution. The true interaction is exactly delta, with
independent Bernoulli generations conditional on the task. Report assumptions.
"""
import argparse
import json
import math
from pathlib import Path
import random
from statistics import NormalDist, mean, variance

p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, default=Path("artifacts/sample-size-planning.json"))
p.add_argument("--simulations", type=int, default=1000)
p.add_argument("--delta", type=float, default=.15)
p.add_argument("--seed", type=int, default=20260913)
a = p.parse_args()
if a.output.exists():
    raise SystemExit("Use a fresh output path; planning evidence is versioned")
rows = []
critical = NormalDist().inv_cdf(1 - .025/2)  # two-sided alpha=.025 for each of two models
for n in (60, 120, 240):
    for baseline in (.05, .2, .5):
        rng = random.Random(a.seed + n + round(baseline*100))
        detected = 0
        estimates = []
        repeats = 2
        for trial in range(a.simulations):
            contrasts = []
            for task in range(n):
                b = .75 * rng.betavariate(baseline/.75 * 8, (1-baseline/.75)*8)
                probabilities = (b+.05+a.delta, b, b+.05, b)
                values = [sum(rng.random() < p for _ in range(repeats))/repeats for p in probabilities]
                contrasts.append(values[0]-values[1]-values[2]+values[3])
            estimate = mean(contrasts)
            se = math.sqrt(variance(contrasts)/n)
            detected += se > 0 and abs(estimate)/se > critical
            estimates.append(estimate)
        power = detected/a.simulations
        rows.append({"tasks": n, "repeats_per_cell": repeats, "baseline_mean": baseline,
                     "true_interaction": a.delta, "estimated_power_normal_test": power,
                     "monte_carlo_se": math.sqrt(power*(1-power)/a.simulations),
                     "mean_estimate": mean(estimates), "core_episodes_per_model": n*repeats*6})
result = {"purpose": "prospective planning; not experimental results", "seed": a.seed,
          "simulations_per_design": a.simulations, "alpha_per_model": .025,
          "assumptions": ["Independent task draws within the authored task distribution",
                          "Shared beta-distributed baseline propensity with concentration 8",
                          "Independent within-task outcomes conditional on propensity",
                          "Successive model generations may violate this simplifying independence assumption",
                          "Normal-approximation test used for planning; empirical task bootstrap used for reporting",
                          "No guarantee of power under unmodeled task-by-treatment heterogeneity"],
          "designs": rows}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(result, indent=2))
for r in rows:
    print(r)
