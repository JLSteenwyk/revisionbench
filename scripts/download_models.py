"""Download pinned public weights, with resumable HF downloads and SHA256 evidence."""
import hashlib
import argparse
import json
import os
from pathlib import Path

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
from huggingface_hub import hf_hub_download, HfApi

root = Path(__file__).resolve().parents[1]
models = json.loads((root / "configs/models.json").read_text())
p = argparse.ArgumentParser()
p.add_argument("--model", choices=list(models))
a = p.parse_args()
for name, spec in models.items():
    if a.model and name != a.model:
        continue
    target = root / "models" / name
    info = HfApi().model_info(spec["repository"], revision=spec["revision"], files_metadata=True, token=False)
    metadata = {"repository": spec["repository"], "revision": info.sha,
                "license": (info.card_data or {}).get("license"),
                "files": [{"name": f.rfilename, "size": f.size} for f in info.siblings if f.rfilename == spec["filename"]]}
    (root / f"artifacts/environment/{name}-upstream.json").write_text(json.dumps(metadata, indent=2))
    print("Downloading", name, metadata, flush=True)
    file = hf_hub_download(spec["repository"], spec["filename"], revision=spec["revision"], local_dir=target, token=False)
    h = hashlib.sha256()
    with open(file, "rb") as handle:
        for block in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            h.update(block)
    metadata["sha256"] = h.hexdigest()
    if spec.get("sha256") and h.hexdigest() != spec["sha256"]:
        raise RuntimeError("Downloaded bytes do not match the pinned upstream SHA256")
    metadata["local_path"] = str(Path(file).relative_to(root))
    (root / f"artifacts/environment/{name}-weights.json").write_text(json.dumps(metadata, indent=2))
    print("Verified", name, metadata["sha256"], flush=True)
