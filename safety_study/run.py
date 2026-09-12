"""python -m safety_study.run --model qwen --output results/pilot-qwen"""
import argparse
import hashlib
import itertools
import json
import platform
import random
import subprocess
from pathlib import Path

from .agent import LocalClient, run_episode
from .world import CORE_CONDITIONS, CONTROLS, INTERVENTIONS, World, scenario, seeded_snapshot, replacement, digest
from .registration import source_hash, validate_registration


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=("qwen", "ministral"), required=True)
    p.add_argument("--endpoint", default="http://127.0.0.1:8765/v1")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--experiment", choices=("peer", "replacement", "intervention"), default="peer")
    p.add_argument("--tasks", type=int, default=3)
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--max-steps", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260912)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--split", choices=("development", "confirmation"), default="development")
    p.add_argument("--registration", type=Path)
    p.add_argument("--checkpoints", type=Path, help="Natural checkpoints exported with select_checkpoints.py")
    a = p.parse_args()
    if a.split == "confirmation" and (not a.registration or not a.registration.is_file()):
        p.error("Confirmation requires a frozen registration file")
    if a.split == "confirmation":
        try:
            validate_registration(a.registration, a)
        except (ValueError, KeyError) as e:
            p.error(str(e))
    natural = json.loads(a.checkpoints.read_text()) if a.checkpoints else None
    if natural is not None:
        if not natural:
            p.error("No natural checkpoints available; do not substitute seeded results")
        if a.experiment == "peer":
            p.error("Peer experiment starts from independent task states")
        if any(cp["snapshot"]["task"]["split"] != a.split for cp in natural):
            p.error("Checkpoint split differs from requested split")
    if a.output.exists():
        p.error("Output directory exists; use a new run directory to preserve provenance")
    if a.tasks < 1 or a.repeats < 1 or a.max_steps < 1:
        p.error("Task, repeat, and step counts must be positive")
    client = LocalClient(a.endpoint, a.model, a.temperature, a.max_tokens)
    served_models = client.server_info()
    model_specs = json.loads(Path("configs/models.json").read_text())
    weight_manifest = Path(f"artifacts/environment/{a.model}-weights.json")
    if not weight_manifest.exists():
        p.error("Verified pinned weight manifest missing")
    a.output.mkdir(parents=True)
    (a.output / "episodes").mkdir()
    manifest = {"arguments": {k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
                "model": model_specs[a.model], "weights": json.loads(weight_manifest.read_text()),
                "code_sha256": source_hash(), "python": platform.python_version(), "served_models": served_models,
                "runtime_commit": subprocess.check_output(["git", "-C", "vendor/llama.cpp", "rev-parse", "HEAD"], text=True).strip(),
                "registration_sha256": hashlib.sha256(a.registration.read_bytes()).hexdigest() if a.registration else None,
                "checkpoint_file_sha256": hashlib.sha256(a.checkpoints.read_bytes()).hexdigest() if a.checkpoints else None}
    server_record = Path("artifacts/environment/server-current.json")
    if server_record.exists():
        manifest["server"] = json.loads(server_record.read_text())
    (a.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    jobs = []
    for i in range(a.tasks if natural is None else len(natural)):
        task = scenario(i, a.split) if natural is None else World.restore(natural[i]["snapshot"]).task
        for repeat in range(a.repeats):
            seed = a.seed + i * 1000 + repeat * 100
            if a.experiment == "peer":
                for condition in CORE_CONDITIONS + CONTROLS:
                    jobs.append((World(task, condition), {"condition": condition}, seed, None, a.max_steps))
            else:
                snap = natural[i]["snapshot"] if natural else seeded_snapshot(task)
                origin = natural[i]["origin"] if natural else "deliberately_seeded"
                metadata = {"origin": origin, "checkpoint_id": digest(snap), "repeat": repeat}
                metadata["task_complete_at_checkpoint"] = World.restore(snap).scores()["task_complete"]
                if natural:
                    metadata["parent_episode"] = natural[i]["parent_episode"]
                    metadata["parent_metadata"] = natural[i]["parent_metadata"]
                remaining = natural[i]["remaining_steps"] if natural else a.max_steps
                old_history = natural[i]["history"] if natural else None
                if a.experiment == "replacement":
                    for n, q, c in itertools.product((False, True), repeat=3):
                        w = replacement(snap, n, q, c)
                        jobs.append((w, {**metadata, "condition": f"notes{int(n)}_queue{int(q)}_changes{int(c)}", "replacement": True}, seed, None, remaining))
                    if natural:
                        jobs.append((replacement(snap, True, True, True), {**metadata, "condition": "original_continues", "replacement": False}, seed, old_history, remaining))
                else:
                    for intervention in INTERVENTIONS:
                        w = replacement(snap, True, True, True)
                        w.intervention = intervention
                        history = list(old_history) if old_history else None
                        if history is not None and intervention in ("owner_stop", "acceptable_stop"):
                            history.append({"role": "user", "content": w.owner_text()})
                        jobs.append((w, {**metadata, "condition": intervention}, seed, history, remaining))
    random.Random(a.seed).shuffle(jobs)
    (a.output / "schedule.json").write_text(json.dumps([
        {"task": w.task.id, "seed": seed, "metadata": meta, "max_steps": steps}
        for w, meta, seed, hist, steps in jobs], indent=2))
    for j, (world, meta, seed, history, steps) in enumerate(jobs):
        result = run_episode(world, client, seed, steps, history, include_external=a.experiment == "peer")
        result["metadata"] = {**meta, "task": world.task.id, "family": world.task.family, "split": world.task.split,
                              "seed": seed, "model": a.model, "experiment": a.experiment}
        path = a.output / "episodes" / f"{j:05d}.json"
        path.write_text(json.dumps(result, indent=2))
        with (a.output / "summary.jsonl").open("a") as handle:
            handle.write(json.dumps({"episode": path.name, **result["metadata"], "status": result["status"], **result["scores"]}) + "\n")
        print(f"{j+1}/{len(jobs)} {world.task.id} {meta['condition']} {result['status']} {result['scores']}", flush=True)
        if result["status"] == "infrastructure_error":
            raise RuntimeError("Inference failed; stopped without automatic retry or paid fallback")


if __name__ == "__main__":
    main()
