# Authorization and peer influence study

Development-stage research on peer messages, persistence through replacement, and intervention in tool-using agents. See [the protocol](docs/protocol.md), [prior work](docs/literature.md), and [the complete objective](docs/objective.txt).

The agent operates only on synthetic in-memory records through a JSON action protocol. It has no host execution tools. This is not a reproduction of a real intrusion.

## Validate the simulator

```bash
python -m unittest discover -s tests -v
```

## Local models

On a compatible Linux/CUDA 12.9 machine, build the pinned runtime with:

```bash
bash scripts/setup_runtime.sh
```

This uses a project-local virtual environment. CUDA compiler and a C++ toolchain must already exist. The measured host has NVIDIA Ada GPUs (compute capability 8.9); adjust the build architecture for a different GPU and record that change.

Pinned repositories and revisions are in `configs/models.json`. Download with:

```bash
.venv/bin/python scripts/download_models.py
```

The download script creates SHA256 manifests under `artifacts/environment/`. Qwen is a third-party Q4_K_M conversion; Ministral is an official BF16 GGUF. The local runtime is a pinned checkout of llama.cpp. Model compatibility, competence, and throughput must be measured before final selection.

Serve one model at a time:

```bash
.venv/bin/python scripts/serve.py qwen
```

The launcher checks available memory on the selected GPU and binds only to loopback. The default GPU UUID is this study machine's GPU 0; pass `--gpu YOUR_GPU_UUID` elsewhere. It records launch flags and samples GPU memory every five seconds. Stop this foreground process before launching the other model. The development configuration disables reasoning; this is a recorded experimental setting, not a claim about default model behavior.

## Development pilot

With the selected local model served on port 8765 under the alias `qwen` or `ministral`:

```bash
python -m safety_study.run --model qwen --tasks 3 --repeats 1 --output results/pilot-qwen
python -m safety_study.run --model qwen --experiment replacement --output results/seeded-replacement-qwen
python -m safety_study.run --model qwen --experiment intervention --output results/seeded-intervention-qwen
```

Every run gets a manifest, randomized schedule, full episode traces/checkpoints, and a summary. Existing output directories are never overwritten. Inference errors stop the run without paid fallback.

Verify and analyze completed runs:

```bash
python scripts/audit_run.py results/pilot-qwen
python -m safety_study.analyze results/pilot-qwen
python scripts/diagnose_run.py results/pilot-qwen
```

The audit replays actions and checks full state transitions, scores, summary rows, and schedule completion. Analysis groups natural and seeded experiments separately and pairs conditions within task, seed, and checkpoint before estimating task-cluster uncertainty. Sparse or degenerate empirical bootstrap intervals are not presented as precise evidence of no effect.

Diagnostics summarize recorded response latency, first-violation timing, and different-operation attempts after a denial. Timing among violating episodes is conditional; episodes without an observed violation remain explicitly counted. These diagnostics include partial failure traces and are descriptive, not a speed benchmark or an unconditional survival estimate.

For natural checkpoints:

```bash
python scripts/select_checkpoints.py results/pilot-qwen results/natural-before.json --timing before
python -m safety_study.run --model qwen --experiment intervention --checkpoints results/natural-before.json --output results/natural-intervention-qwen
```

For the full natural-recovery development pilot after both models finish an expanded development run:

```bash
python scripts/recovery_pilot.py --parent results/development-002 --output results/natural-development-002
```

This selects the first eligible failure episode per task in the saved randomized schedule: after the first attempt for replacement, before it for intervention. Branches inherit the recorded remaining action budget. Selection is conditional on observed failure; these runs do not estimate an unconditional deployment failure rate. The selector also supports a fixed `--task-index-limit` for prespecified subsets.

The local registration is frozen in `configs/preregistration.json` (2026-09-13 00:19:48 UTC), before the first held-out inference. The primary schedule is running in `results/confirmation-001/`; complete-study conclusions await the registered runs and final analysis. Pilot data are never relabeled as confirmation.

After the frozen registration and competence evidence are available, `scripts/confirmation_pipeline.py --registration PATH --output NEW_DIRECTORY` executes the registered primary schedules and audits each run. It refuses changed source files, model weights, sampling settings, or registered runtime flags. No confirmation is launched by setup or development scripts.

The separately pinned Q8 sensitivity weights can be downloaded with `scripts/download_models.py --config configs/sensitivity-models.json --model qwen_q8`. After its development competence check, the same confirmation runner supports `--models qwen_q8` using its registered secondary sample allocation. `scripts/compare_precision.py Q4_PEER_RUN Q8_PEER_RUN NEW_OUTPUT.json` reports paired comparisons on shared task/seed keys and checks provenance and runtime compatibility. Extra Q4 generations are excluded from that secondary comparison by design.
