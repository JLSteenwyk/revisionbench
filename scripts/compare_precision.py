"""Paired secondary Q8-versus-Q4 comparisons on shared task/generation keys."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from safety_study.analyze import paired_contrast
from safety_study.world import CORE_CONDITIONS, CONTROLS


def compare(q4, q8):
    keys = {(r["task"], r["seed"]) for r in q8}
    shared = keys & {(r["task"], r["seed"]) for r in q4}
    q4 = [r for r in q4 if (r["task"], r["seed"]) in keys]
    report = {"q8_task_generation_keys": len(keys), "shared_task_generation_keys": len(shared), "comparisons": {}}
    for condition in CORE_CONDITIONS + CONTROLS:
        rows = [{**r, "condition": label} for label, source in (("q4", q4), ("q8", q8))
                for r in source if r["condition"] == condition]
        for outcome in ("unauthorized_attempt", "unauthorized_change", "task_complete"):
            report["comparisons"][condition + "_" + outcome] = paired_contrast(rows, {"q8": 1, "q4": -1}, outcome)
    interaction = {"peer_permission": 1, "peer_facts": -1, "reference_permission": -1, "reference_facts": 1}
    weights = {label + "_" + condition: sign * value
               for label, sign in (("q8", 1), ("q4", -1)) for condition, value in interaction.items()}
    rows = [{**r, "condition": label + "_" + r["condition"]}
            for label, source in (("q4", q4), ("q8", q8)) for r in source]
    report["comparisons"]["difference_in_source_by_permission_interactions"] = paired_contrast(rows, weights)
    report["interpretation"] = "Secondary configuration comparison: Q8 minus Q4, matched by task and seed. Extra Q4 generations excluded by design. Intervals are not adjusted across secondary comparisons. Conversion details and nondeterministic generation limit a quantization-only interpretation."
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("q4", type=Path)
    p.add_argument("q8", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    manifests = [json.loads((path / "manifest.json").read_text()) for path in (a.q4, a.q8)]
    if [m["arguments"]["model"] for m in manifests] != ["qwen", "qwen_q8"]:
        raise SystemExit("Expected Qwen Q4 then Qwen Q8 runs")
    for path in (a.q4, a.q8):
        if not json.loads((path / "audit.json").read_text())["all_state_and_score_checks_pass"]:
            raise SystemExit("Both runs must pass replay audit")
    if manifests[0]["code_sha256"] != manifests[1]["code_sha256"]:
        raise SystemExit("Controller/analysis source differs between configurations")
    for key in ("upstream", "upstream_revision", "repository", "revision"):
        if manifests[0]["model"][key] != manifests[1]["model"][key]:
            raise SystemExit(f"Model provenance differs: {key}")
    for key in ("max_steps", "temperature", "max_tokens", "seed", "split"):
        if manifests[0]["arguments"][key] != manifests[1]["arguments"][key]:
            raise SystemExit(f"Experimental setting differs: {key}")
    for flag in ("--ctx-size", "--reasoning", "--reasoning-budget", "--parallel", "--batch-size", "--ubatch-size", "--threads"):
        commands = [m["server"]["command"] for m in manifests]
        if commands[0][commands[0].index(flag)+1] != commands[1][commands[1].index(flag)+1]:
            raise SystemExit(f"Runtime setting differs: {flag}")
    data = [[json.loads(line) for line in (path / "summary.jsonl").read_text().splitlines()] for path in (a.q4, a.q8)]
    if a.output.exists():
        raise SystemExit("Output exists; preserve prior comparison")
    a.output.write_text(json.dumps(compare(*data), indent=2))
