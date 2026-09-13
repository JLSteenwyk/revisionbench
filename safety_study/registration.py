"""Fail-closed local preregistration validation (not a public registry)."""
import datetime
import hashlib
import json
from pathlib import Path


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hash():
    h = hashlib.sha256()
    for path in sorted(Path("safety_study").glob("*.py")):
        h.update(path.name.encode() + path.read_bytes())
    return h.hexdigest()


def validate_registration(path, args):
    doc = json.loads(Path(path).read_text())
    if doc.get("status") != "frozen":
        raise ValueError("Registration is not frozen")
    when = datetime.datetime.fromisoformat(doc["frozen_utc"])
    if when.tzinfo is None or when > datetime.datetime.now(datetime.timezone.utc):
        raise ValueError("Invalid registration timestamp")
    for key in ("hypotheses", "primary_comparisons", "sample_size_justification", "exclusions", "stopping_rules", "multiplicity"):
        if not doc.get(key):
            raise ValueError(f"Missing registration field: {key}")
    if doc.get("code_sha256") != source_hash():
        raise ValueError("Analysis/experiment code differs from frozen registration")
    for file, expected in doc.get("file_hashes", {}).items():
        if file_hash(file) != expected:
            raise ValueError(f"Registered file changed: {file}")
    for required in ("configs/models.json", "docs/protocol.md"):
        if required not in doc.get("file_hashes", {}):
            raise ValueError(f"Missing registered file: {required}")
    if args.model not in doc["models"]:
        raise ValueError("Model is not registered")
    plan = doc.get("model_experiments", {}).get(args.model, doc["experiments"])[args.experiment]
    for key in ("tasks", "repeats", "max_steps", "temperature", "max_tokens", "seed"):
        if getattr(args, key) != plan[key]:
            raise ValueError(f"Run {key} differs from registered plan")
    return doc


def validate_live_runtime(doc, model, server, weights):
    """Verify the recorded live launcher configuration against the frozen plan."""
    runtime = doc["runtime"]
    if server.get("model") != model or server.get("runtime_commit") != runtime["commit"]:
        raise ValueError("Live model/runtime differs from registration")
    expected = doc["model_weight_sha256"][model]
    if server.get("weight_sha256") != expected or weights.get("sha256") != expected:
        raise ValueError("Live weight hash differs from registration")
    command = server["command"]
    for flag, value in runtime["flags"].items():
        if command.count(flag) != 1:
            raise ValueError(f"Missing or repeated registered runtime flag: {flag}")
        if value is not True:
            index = command.index(flag)
            if index + 1 >= len(command) or command[index + 1] != str(value):
                raise ValueError(f"Live runtime flag differs: {flag}")
