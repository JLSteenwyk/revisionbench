"""Run natural-state development branches after a completed competence pilot."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_study.agent import LocalClient

p = argparse.ArgumentParser()
p.add_argument("--parent", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--wait-pid", type=int)
a = p.parse_args()
if a.output.exists():
    raise SystemExit("Output exists; preserve prior evidence")
a.output.mkdir(parents=True)
(a.output / "plan.json").write_text(json.dumps({"phase": "development_only", "parent": str(a.parent),
    "selection": "first eligible episode in saved randomized schedule per task",
    "replacement_timing": "after_first_attempt", "intervention_timing": "before_first_attempt",
    "repeats": 1, "budget": "remaining steps in the selected parent checkpoint"}, indent=2))


def command(arguments, log):
    with log.open("w") as handle:
        subprocess.run([sys.executable, *arguments], cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=True)


if a.wait_pid:
    while True:
        proc = Path("/proc") / str(a.wait_pid) / "cmdline"
        try:
            cmdline = proc.read_bytes()
        except FileNotFoundError:
            break
        if b"scripts/development_pipeline.py" not in cmdline:
            raise SystemExit("Wait PID no longer identifies the expected development pipeline")
        time.sleep(5)

for model in ("qwen", "ministral"):
    if not (a.parent / f"{model}-completed.json").exists():
        raise SystemExit(f"Parent pilot is incomplete for {model}")
    if not json.loads((a.parent / f"{model}-competence.json").read_text())["passed"]:
        raise SystemExit(f"Parent competence failed for {model}")

for model in ("qwen", "ministral"):
    peer = a.parent / f"{model}-peer"
    if not json.loads((peer / "audit.json").read_text())["all_state_and_score_checks_pass"]:
        raise SystemExit("Parent audit failed")
    selected = {}
    for experiment, timing in (("replacement", "after"), ("intervention", "before")):
        cp = a.output / f"{model}-{timing}.json"
        command(["scripts/select_checkpoints.py", str(peer), str(cp), "--timing", timing, "--one-per-task"],
                a.output / f"{model}-{timing}-selection.log")
        selected[experiment] = cp
    if not any(json.loads(path.read_text()) for path in selected.values()):
        (a.output / f"{model}-no-natural-checkpoints.json").write_text(json.dumps({"reason": "No eligible natural failure checkpoint"}))
        continue
    with (a.output / f"launch-{model}.log").open("w") as log:
        server = subprocess.Popen([sys.executable, "scripts/serve.py", model], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 600
            while True:
                if server.poll() is not None:
                    raise RuntimeError("Owned server exited; inspect launch log")
                try:
                    identity = json.loads((ROOT / "artifacts/environment/server-current.json").read_text())
                    if identity.get("launcher_pid") != server.pid:
                        raise RuntimeError("Waiting for owned server")
                    LocalClient("http://127.0.0.1:8765/v1", model).server_info()
                    break
                except Exception:
                    if time.monotonic() > deadline:
                        raise RuntimeError("Owned server readiness deadline exceeded")
                    time.sleep(5)
            for experiment, cp in selected.items():
                if not json.loads(cp.read_text()):
                    continue
                run = a.output / f"{model}-{experiment}"
                command(["-m", "safety_study.run", "--model", model, "--experiment", experiment,
                         "--checkpoints", str(cp), "--output", str(run)], a.output / f"{model}-{experiment}.log")
                for script in ("scripts/audit_run.py", "scripts/diagnose_run.py"):
                    command([script, str(run)], a.output / f"{model}-{experiment}-{Path(script).stem}.log")
                command(["-m", "safety_study.analyze", str(run)], a.output / f"{model}-{experiment}-analysis.log")
                print("Completed and audited:", model, experiment, flush=True)
        finally:
            server.terminate()
            server.wait(timeout=30)
print("Natural recovery pilot complete; no confirmation launched", flush=True)
