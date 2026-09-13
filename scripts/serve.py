"""Launch the pinned local runtime on one idle-enough GPU; no global environment edits."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("model", choices=("qwen", "ministral", "qwen_q8"))
p.add_argument("--gpu", default="GPU-56e78ad3-b4d7-54f6-38fa-e95729009960")
p.add_argument("--port", type=int, default=8765)
p.add_argument("--context", type=int, default=8192)
p.add_argument("--reasoning", choices=("on", "off"), default="off")
a = p.parse_args()
specs = json.loads((root / "configs/models.json").read_text())
specs.update(json.loads((root / "configs/sensitivity-models.json").read_text()))
spec = specs[a.model]
weights = root / "models" / a.model / spec["filename"]
if not (root / f"artifacts/environment/{a.model}-weights.json").exists():
    raise SystemExit("Download and verify pinned weights first")
print("Checking complete weight file against pinned upstream SHA256", flush=True)
h = hashlib.sha256()
with weights.open("rb") as f:
    for block in iter(lambda: f.read(16 * 1024 * 1024), b""):
        h.update(block)
if h.hexdigest() != spec["sha256"]:
    raise SystemExit("Weight integrity mismatch; not starting inference")
free = int(subprocess.check_output(["nvidia-smi", "-i", a.gpu, "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True).strip())
if free < 42000:
    raise SystemExit(f"Selected GPU has only {free} MiB free; no workloads were interrupted")
with socket.socket() as sock:
    # Permit closed connections in TIME_WAIT, while an active listener still
    # prevents binding. Match the server's normal address-reuse behavior.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", a.port))
binary = root / "vendor/llama.cpp/build/bin/llama-server"
cmd = [str(binary), "--model", str(weights), "--alias", a.model, "--host", "127.0.0.1",
       "--port", str(a.port), "--ctx-size", str(a.context), "--parallel", "1", "--n-gpu-layers", "99",
       "--threads", "12", "--batch-size", "512", "--ubatch-size", "256", "--jinja",
       "--reasoning", a.reasoning, "--reasoning-budget", "0" if a.reasoning == "off" else "-1", "--no-context-shift"]
env = os.environ.copy()
env["CUDA_VISIBLE_DEVICES"] = a.gpu
# The model runtime requires no provider credentials.
for key in list(env):
    if any(s in key.upper() for s in ("API_KEY", "ACCESS_TOKEN", "AUTH_TOKEN", "OAUTH_TOKEN", "HF_TOKEN")):
        env.pop(key)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
logpath = root / f"artifacts/environment/server-{a.model}-{stamp}.log"
manifest = {"model": a.model, "command": cmd, "gpu_uuid": a.gpu, "free_mib_before": free,
            "launcher_pid": os.getpid(), "weight_sha256": h.hexdigest(),
            "timestamp": stamp, "reasoning": a.reasoning, "log": str(logpath.relative_to(root)),
            "runtime_commit": subprocess.check_output(["git", "-C", str(root / "vendor/llama.cpp"), "rev-parse", "HEAD"], text=True).strip()}
with logpath.open("w") as log:
    child = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    manifest["pid"] = child.pid
    (root / "artifacts/environment/server-current.json").write_text(json.dumps(manifest, indent=2))
    (root / f"artifacts/environment/server-{a.model}-{stamp}.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest), flush=True)
    def stop(signum, frame):
        child.terminate()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with (root / f"artifacts/environment/gpu-{a.model}-{stamp}.jsonl").open("w") as metrics:
        while child.poll() is None:
            usage = subprocess.check_output(["nvidia-smi", "-i", a.gpu, "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True).strip()
            metrics.write(json.dumps({"unix_time": time.time(), "used_mib_util_percent": usage}) + "\n")
            metrics.flush()
            time.sleep(5)
    raise SystemExit(child.returncode)
