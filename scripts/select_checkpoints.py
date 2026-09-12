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
a = p.parse_args()
rows = []
for path in sorted((a.run / "episodes").glob("*.json")):
    d = json.loads(path.read_text())
    for i, t in enumerate(d["traces"]):
        if t["event"]["unauthorized_attempt"]:
            index = i + (a.timing == "after")
            if index < len(d["checkpoints"]):
                rows.append({**d["checkpoints"][index], "origin": "natural_" + a.timing + "_first_attempt",
                             "parent_episode": str(path), "parent_metadata": d["metadata"]})
            break
if a.output.exists():
    raise SystemExit("Refusing to overwrite checkpoint evidence")
a.output.write_text(json.dumps(rows, indent=2))
print(len(rows), "checkpoints")
