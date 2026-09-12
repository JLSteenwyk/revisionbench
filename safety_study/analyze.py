"""Descriptive summaries and paired task-cluster uncertainty; no episode pseudoreplication."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import statistics


def mean(xs):
    return sum(xs) / len(xs)


def percentile(xs, p):
    s = sorted(xs)
    x = (len(s) - 1) * p
    lo = int(x)
    return s[lo] + (s[min(lo + 1, len(s)-1)] - s[lo]) * (x-lo)


def paired_contrast(rows, weights, metric="unauthorized_attempt", draws=5000, seed=739):
    tasks = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["status"] != "infrastructure_error" and r["condition"] in weights:
            tasks[r["task"]][r["condition"]].append(float(r[metric]))
    values = [sum(weights[c] * mean(cells[c]) for c in weights)
              for cells in tasks.values() if all(c in cells for c in weights)]
    if not values:
        return {"estimable": False, "task_clusters": 0}
    result = {"estimable": True, "task_clusters": len(values), "risk_difference": mean(values)}
    if len(values) < 10:
        result["ci95"] = None
        result["warning"] = "Fewer than 10 task clusters; descriptive estimate only"
    else:
        rng = random.Random(seed)
        samples = [mean(rng.choices(values, k=len(values))) for _ in range(draws)]
        result["ci95"] = [percentile(samples, .025), percentile(samples, .975)]
        if len(set(values)) == 1:
            result["warning"] = "Degenerate empirical bootstrap: these intervals do not exclude rare unseen events"
    return result


def summarize(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    cells = {}
    for c, rr in sorted(by.items()):
        valid = [r for r in rr if r["status"] != "infrastructure_error"]
        cells[c] = {"episodes": len(rr), "infrastructure_errors": len(rr)-len(valid),
                    "task_clusters": len({r["task"] for r in valid})}
        for metric in ("unauthorized_attempt", "unauthorized_change", "task_complete", "invalid_actions", "clarifications", "attempts_after_denial", "steps"):
            cells[c][metric] = mean([float(r[metric]) for r in valid]) if valid else None
    contrasts = {}
    if rows and rows[0]["experiment"] == "peer":
        contrasts["source_by_permission"] = paired_contrast(rows, {"peer_permission": 1, "peer_facts": -1, "reference_permission": -1, "reference_facts": 1})
        contrasts["source_by_success"] = paired_contrast(rows, {"peer_success": 1, "peer_facts": -1, "reference_success": -1, "reference_facts": 1})
        contrasts["peer_permission_vs_facts"] = paired_contrast(rows, {"peer_permission": 1, "peer_facts": -1})
    return {"cells": cells, "contrasts": contrasts}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    a = p.parse_args()
    rows = [json.loads(line) for line in (a.run / "summary.jsonl").read_text().splitlines()]
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["experiment"], r.get("origin", "not_applicable"))].append(r)
    results = {"|".join(k): summarize(v) for k, v in groups.items()}
    (a.run / "analysis.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
