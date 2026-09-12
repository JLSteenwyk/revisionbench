# Authorization and peer influence study

Development-stage research on peer messages, persistence through replacement, and intervention in tool-using agents. See [the protocol](docs/protocol.md), [prior work](docs/literature.md), and [the complete objective](docs/objective.txt).

The agent operates only on synthetic in-memory records through a JSON action protocol. It has no host execution tools. This is not a reproduction of a real intrusion.

## Validate the simulator

```bash
python -m unittest discover -s tests -v
```

## Local models

Pinned repositories and revisions are in `configs/models.json`. Download with:

```bash
.venv/bin/python scripts/download_models.py
```

The download script creates SHA256 manifests under `artifacts/environment/`. Qwen is a third-party Q4_K_M conversion; Ministral is an official BF16 GGUF. The local runtime is a pinned checkout of llama.cpp. Model compatibility, competence, and throughput must be measured before final selection.

## Development pilot

With the selected local model served on port 8765 under the alias `qwen` or `ministral`:

```bash
python -m safety_study.run --model qwen --tasks 3 --repeats 1 --output results/pilot-qwen
python -m safety_study.run --model qwen --experiment replacement --output results/seeded-replacement-qwen
python -m safety_study.run --model qwen --experiment intervention --output results/seeded-intervention-qwen
```

Every run gets a manifest, randomized schedule, full episode traces/checkpoints, and a summary. Existing output directories are never overwritten. Inference errors stop the run without paid fallback.

For natural checkpoints:

```bash
python scripts/select_checkpoints.py results/pilot-qwen results/natural-before.json --timing before
python -m safety_study.run --model qwen --experiment intervention --checkpoints results/natural-before.json --output results/natural-intervention-qwen
```

No confirmatory results are available yet. Confirmation requires a separate held-out split and frozen registration; pilot data must never be relabeled as confirmation.
