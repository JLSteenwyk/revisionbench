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
    plan = doc["experiments"][args.experiment]
    for key in ("tasks", "repeats", "max_steps", "temperature", "max_tokens", "seed"):
        if getattr(args, key) != plan[key]:
            raise ValueError(f"Run {key} differs from registered plan")
    return doc
