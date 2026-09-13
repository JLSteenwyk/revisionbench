"""Execute a frozen local study schedule; never creates or edits registration."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_study.agent import LocalClient
from safety_study.registration import validate_registration

p = argparse.ArgumentParser()
p.add_argument("--registration", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--models", nargs="+")
a = p.parse_args()
registration = json.loads(a.registration.read_text())
models = a.models or registration["primary_models"]
if a.output.exists():
    raise SystemExit("Output exists; preserve original confirmation records")


def plan_for(model):
    return registration.get("model_experiments", {}).get(model, registration["experiments"])


for model in models:
    for experiment, plan in plan_for(model).items():
        validate_registration(a.registration, SimpleNamespace(model=model, experiment=experiment, **plan))
    evidence = Path(registration["eligibility_evidence"][model])
    competence = json.loads(evidence.read_text())
    if competence.get("model") != model or not competence.get("passed"):
        raise SystemExit(f"Required competence evidence missing or failed: {model}")

a.output.mkdir(parents=True)
(a.output / "plan.json").write_text(json.dumps({"phase": "confirmation", "models": models,
    "registration": str(a.registration),
    "registration_sha256": hashlib.sha256(a.registration.read_bytes()).hexdigest()}, indent=2))


def command(arguments, logfile):
    with logfile.open("w") as handle:
        subprocess.run([sys.executable, *arguments], cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=True)


def run(model, experiment, checkpoints=None):
    plan = plan_for(model)[experiment]
    label = f"{model}-{experiment}" + ("-natural" if checkpoints else "")
    output = a.output / label
    args = ["-m", "safety_study.run", "--model", model, "--experiment", experiment,
            "--split", "confirmation", "--registration", str(a.registration), "--output", str(output)]
    for key in ("tasks", "repeats", "max_steps", "temperature", "max_tokens", "seed"):
        args.extend(["--" + key.replace("_", "-"), str(plan[key])])
    if checkpoints:
        args.extend(["--checkpoints", str(checkpoints)])
    command(args, a.output / f"{label}.log")
    for script in ("scripts/audit_run.py", "scripts/diagnose_run.py"):
        command([script, str(output)], a.output / f"{label}-{Path(script).stem}.log")
    command(["-m", "safety_study.analyze", str(output)], a.output / f"{label}-analysis.log")
    print("Completed and audited:", label, flush=True)
    return output


for model in models:
    print("Starting registered model:", model, flush=True)
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
            peer = run(model, "peer")
            for experiment in ("replacement", "intervention"):
                if experiment not in plan_for(model):
                    continue
                run(model, experiment)
                timing = registration["natural_recovery"][experiment + "_timing"]
                cp = a.output / f"{model}-{experiment}-checkpoints.json"
                command(["scripts/select_checkpoints.py", str(peer), str(cp), "--timing", timing,
                         "--one-per-task", "--task-index-limit", str(registration["natural_recovery"]["task_index_limit"])],
                        a.output / f"{model}-{experiment}-selection.log")
                if json.loads(cp.read_text()):
                    run(model, experiment, checkpoints=cp)
                else:
                    (a.output / f"{model}-{experiment}-natural-unavailable.json").write_text(json.dumps({
                        "reason": "No eligible natural checkpoint under the frozen selection rule",
                        "interpretation": "Natural recovery contrast not estimable; seeded data remain separate"}))
            (a.output / f"{model}-completed.json").write_text(json.dumps({"model": model, "status": "registered_schedule_complete"}))
        finally:
            server.terminate()
            server.wait(timeout=30)
print("Registered schedules completed and audited; final synthesis still required", flush=True)
