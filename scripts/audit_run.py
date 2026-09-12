"""Independently replay every recorded action and verify scores and state transitions."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from safety_study.world import World, digest

p = argparse.ArgumentParser()
p.add_argument("run", type=Path)
a = p.parse_args()
schedule = json.loads((a.run / "schedule.json").read_text())
paths = sorted((a.run / "episodes").glob("*.json"))
summaries = [json.loads(s) for s in (a.run / "summary.jsonl").read_text().splitlines()]
assert len(paths) == len(schedule) == len(summaries), "Run incomplete or duplicate summaries"
assert len({r['episode'] for r in summaries}) == len(summaries)
summary_by = {r['episode']: r for r in summaries}
for path, plan in zip(paths, schedule):
    result = json.loads(path.read_text())
    assert result["status"] != "infrastructure_error", "Infrastructure error retained; not a complete run"
    assert result["metadata"]["task"] == plan["task"]
    assert result["metadata"]["condition"] == plan["metadata"]["condition"]
    w = World.restore(result["checkpoints"][0]["snapshot"])
    for checkpoint, trace in zip(result["checkpoints"], result["traces"]):
        assert digest(w.snapshot()) == digest(checkpoint["snapshot"]), f"Checkpoint mismatch: {path}"
        w.step(trace["event"]["action"])
        assert w.events[-1] == trace["event"], f"Event mismatch: {path}"
    assert w.scores() == result["scores"], f"Score mismatch: {path}"
    assert digest(w.snapshot()) == digest(result["final"]), f"Final state mismatch: {path}"
    for key, value in w.scores().items():
        assert summary_by[path.name][key] == value
report = {"episodes_replayed": len(paths), "schedule_complete": True, "all_state_and_score_checks_pass": True}
(a.run / "audit.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report))
