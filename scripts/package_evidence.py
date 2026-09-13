"""Package completed study evidence and verify every archived file's checksum.

This exports existing results; it neither changes the registered analysis nor
claims that checksum verification proves the scientific conclusions.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_study.registration import source_hash, file_hash


def sha_stream(handle):
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    registration = json.loads(Path("configs/preregistration.json").read_text())
    if source_hash() != registration["code_sha256"]:
        raise SystemExit("Registered source differs; resolve provenance before packaging")
    for path, expected in registration["file_hashes"].items():
        if file_hash(path) != expected:
            raise SystemExit(f"Registered file changed: {path}")
    for model in registration["primary_models"]:
        marker = Path(f"results/confirmation-001/{model}-completed.json")
        if json.loads(marker.read_text()).get("status") != "registered_schedule_complete":
            raise SystemExit(f"Primary model schedule incomplete: {model}")
    if not Path("results/precision-comparison.json").exists() and not Path("results/q8-eligibility-failure.json").exists():
        raise SystemExit("Precision comparison or documented eligibility failure is missing")
    if not Path("docs/research-report.md").exists():
        raise SystemExit("Final research report is missing")
    if a.output.exists():
        raise SystemExit("Archive exists; choose a new path to preserve evidence")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    bundle = a.output.parent / (a.output.name + ".source.bundle")
    if bundle.exists():
        raise SystemExit("Source bundle exists; choose a new archive path")
    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], check=True)
    subprocess.run(["git", "bundle", "verify", str(bundle)], check=True, capture_output=True)
    files = {"source-history.bundle": bundle}
    for root in ("safety_study", "scripts", "tests", "configs", "docs", "results"):
        for path in Path(root).rglob("*"):
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts:
                files[str(path)] = path
    files["README.md"] = Path("README.md")
    for path in registration["file_hashes"]:
        files[path] = Path(path)
    for pattern in ("*-upstream.json", "*-weights.json", "server-*.json", "server-*.log", "gpu-*.jsonl"):
        for path in Path("artifacts/environment").glob(pattern):
            files[str(path)] = path
    for path in (Path("artifacts/environment/gpus.csv"), Path("artifacts/environment/cmake.log"),
                 Path("artifacts/environment/build.log"), Path("artifacts/task-bank-audit-before-fix.json")):
        if path.exists():
            files[str(path)] = path
    manifest = {"registration_sha256": file_hash("configs/preregistration.json"),
                "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "omissions": "Model weights, runtime build/vendor tree, virtual environment, full external research articles, and downloader/cache logs. Pinned source links and weight hashes are retained.",
                "files": {}}
    for name, path in sorted(files.items()):
        with path.open("rb") as handle:
            manifest["files"][name] = {"sha256": sha_stream(handle), "bytes": path.stat().st_size}
    payload = json.dumps(manifest, indent=2).encode()
    with tarfile.open(a.output, "w:gz") as archive:
        for name, path in sorted(files.items()):
            archive.add(path, arcname=name, recursive=False)
        info = tarfile.TarInfo("MANIFEST.json")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    with tarfile.open(a.output, "r:gz") as archive:
        for name, expected in manifest["files"].items():
            with archive.extractfile(name) as handle:
                if sha_stream(handle) != expected["sha256"]:
                    raise RuntimeError(f"Archive checksum mismatch: {name}")
    with a.output.open("rb") as handle:
        archive_hash = sha_stream(handle)
    receipt = {"archive": str(a.output), "archive_sha256": archive_hash,
               "archive_bytes": a.output.stat().st_size, "files_verified": len(files), "all_file_checksums_match": True}
    a.output.with_name(a.output.name + ".verification.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))
