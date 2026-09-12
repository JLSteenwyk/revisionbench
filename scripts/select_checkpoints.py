"""Export first pre-violation and first post-violation natural checkpoints per episode.
These are selected failure states, not an unbiased sample of all deployments.
"""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("run", type=Path)
p.add_argument("output", type=Path)
p.add_argument("--timing", choices=("before", "after"), default="before")
p.add_argument("--one-per-task", action="store_true", help="First eligible episode in the saved randomized schedule for each task")
p.add_argument("--task-index-limit", type=int, help="Only authored task indices below this fixed limit")
a = p.parse_args()
rows = []
seen = set()
for path in sorted((a.run / "episodes").glob("*.json")):
    d = json.loads(path.read_text())
    task = d["metadata"]["task"]
    if a.one_per_task and task in seen:
        continue
    if a.task_index_limit is not None and int(task.rsplit("-", 1)[1]) >= a.task_index_limit:
        continue
    if d["status"] == "infrastructure_error":
        continue
    for i, t in enumerate(d["traces"]):
        if t["event"]["unauthorized_attempt"]:
            index = i + (a.timing == "after")
            if index < len(d["checkpoints"]):
                rows.append({**d["checkpoints"][index], "origin": "natural_" + a.timing + "_first_attempt",
                             "parent_episode": str(path), "parent_metadata": d["metadata"]})
                seen.add(task)
            break
if a.output.exists():
    raise SystemExit("Refusing to overwrite checkpoint evidence")
a.output.write_text(json.dumps(rows, indent=2))
print(len(rows), "checkpoints")
