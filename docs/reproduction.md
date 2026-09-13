# Reproducing and checking the study

The frozen plan is `configs/preregistration.json`. It was committed before held-out inference. This is a local, timestamped registration, not a public registry. The final report must be read alongside the scope limits in that registration and `docs/protocol.md`.

## Two different kinds of reproduction

**Replay the saved actions:** no GPU or model download is needed. Python replays each recorded virtual action and checks state transitions and scores. This can deterministically verify what the recorded agents did.

```bash
python -m unittest discover -s tests -v
python scripts/audit_run.py results/confirmation-001/qwen-peer
python -m safety_study.analyze results/confirmation-001/qwen-peer
python scripts/diagnose_run.py results/confirmation-001/qwen-peer
```

The last three commands write `audit.json`, `analysis.json`, and `diagnostics.json` in the supplied run directory. Run them on a separate extracted copy of the evidence archive, or copy the run directory first, to preserve the original evidence. Repeat them for each completed run directory listed in the final evidence manifest. The full historical development record includes intentional stops and failed configurations; an incomplete run is not expected to pass the complete-schedule audit. Its failure record must remain intact.

**Generate new model outputs:** this needs compatible hardware, weights, and the pinned inference software. Identical seeds did not guarantee identical model action sequences in development. A rerun is a replication sample, not a promise to regenerate identical observations. Use a new output directory, retain original evidence, and disclose changes in hardware or software.

Do not overwrite `artifacts/environment/tests.txt` when rerunning tests: it is historical evidence hashed by the registration. Keep new test output in a separate file or on the terminal. Likewise, do not edit registered configuration, protocol, or source files while a registered schedule is running.

## Runtime and weights

The study uses a single RTX 6000 Ada GPU at a time. The local build targets CUDA 12.9 and compute capability 8.9; exact launch commands, runtime commit, weight hashes, model revisions, and memory samples are saved with the runs. The initial global vLLM installation was unusable and was left unchanged; the study uses its project-local environment and llama.cpp build.

```bash
bash scripts/setup_runtime.sh
.venv/bin/python scripts/download_models.py
.venv/bin/python scripts/download_models.py --config configs/sensitivity-models.json --model qwen_q8
```

Weights are intentionally omitted from the portable evidence archive because they are large and can be downloaded from their pinned public repositories. Qwen Q4_K_M and Q8_0 are third-party conversions from the same pinned repository revision; Ministral BF16 is an official GGUF conversion. Repository metadata and expected SHA256 values are retained. The launcher rehashes the complete file before loading it.

The automatic pipeline defaults to this machine's recorded GPU UUID. On another machine, inspect the recorded requirements and use `scripts/serve.py MODEL --gpu YOUR_GPU_UUID` with the individual runner commands below, documenting the hardware change. Rebuilding for another architecture changes the reproduction environment and must be disclosed. No model-generated text is executed on the host, and no provider billing credential is used by the inference controller.

## Registered schedules

On the original environment, with the archived eligibility evidence and all registered file hashes intact:

```bash
.venv/bin/python scripts/confirmation_pipeline.py --registration configs/preregistration.json --output results/replication-primary
```

The pipeline runs the two primary models serially. For each model it executes the peer factorial and controls, seeded replacement and intervention, and the prespecified natural-checkpoint branches. Every complete run is audited before analysis. Natural checkpoints come from the new peer run under the frozen selection rule, not from manually chosen dramatic examples.

For a manual peer run with a separately launched local server:

```bash
.venv/bin/python -m safety_study.run --model qwen --split confirmation --registration configs/preregistration.json --tasks 240 --repeats 2 --max-steps 8 --temperature 0.7 --max-tokens 512 --seed 20260912 --output results/replication-qwen-peer
```

Use the exact model-specific plans in the registration for recovery and Q8; do not reuse the peer sample size by accident. Recovery uses 120 tasks and one generation per branch, while natural branches use their saved remaining action budgets. The Q8 peer comparison uses 120 tasks and one generation per condition. Its admission requires a passing nine-task development control run under the same frozen controller.

```bash
.venv/bin/python scripts/download_models.py --config configs/sensitivity-models.json --model qwen_q8 > q8-download.log 2>&1 &
q8_download_pid=$!
.venv/bin/python scripts/development_pipeline.py --download-pids "$q8_download_pid" --models qwen_q8 --tasks 9 --controls-only --output results/q8-controls
.venv/bin/python scripts/confirmation_pipeline.py --registration configs/preregistration.json --models qwen_q8 --output results/replication-q8
.venv/bin/python scripts/compare_precision.py results/replication-primary/qwen-peer results/replication-q8/qwen_q8-peer results/replication-precision.json
```

The development pipeline only consults download PIDs while a required verified-weight manifest is absent. When weights are already verified, `--download-pids` is retained as a launcher interface parameter and no download wait occurs. Never supply a random PID to justify waiting on an unverified transfer. If the historical `results/q8-controls` directory already exists, preserve it and use the archived eligibility evidence or make a separately documented replication registration with new evidence paths.

## Interpreting the evidence

All task data are fake. The 240 held-out inputs are distinct and disjoint from the development inputs, but they come from only three authored micro-workflow families. Varied ticket identifiers do not create new problem types. Natural-recovery estimates are conditional on observed failure checkpoints, and removing predecessor changes can also remove legitimate progress.

The primary source-by-permission comparisons use 97.5% intervals for the two-model family. Secondary comparisons use descriptive 95% intervals. Small or degenerate bootstraps are not treated as precise safety evidence. Unauthorized attempts, actual changes, and legitimate completion are separate outcomes; an attempted forbidden no-op does not count as a new change.

A changed frozen file should cause a registration check to fail. Do not disable that check to obtain a run. Preserve the original commitment and create a documented replication or amendment that identifies the changed environment, source, or analysis. The source-history bundle in the final package supports inspection of earlier development versions and the registration commit.

## Independent post-registration reviews

The replay auditor uses the same simulator as the experiment. Additional reviewers
check selected requirements directly from saved JSON without calling simulator
or scoring functions. For example, on a separate extracted evidence copy:

```bash
python scripts/review_analysis.py results/confirmation-001/ministral-peer review-analysis-new.json
python scripts/review_seeded_replacement.py results/confirmation-001/ministral-replacement review-seeded-new.json
python scripts/review_natural_intervention.py results/confirmation-001/ministral-intervention-natural results/confirmation-001/ministral-intervention-checkpoints.json review-natural-new.json
```

These scripts refuse existing output files. Each result describes its verification
scope and limits. The natural-intervention reviewer checks matched states, budgets,
initial histories, parsing and outcomes, but does not reconstruct parent selection
or independently calculate confidence intervals. The analysis reviewer independently recalculates the three main cell rates and
all contrasts and intervals, relying on the separately checked event labels.
Existing selection review evidence is retained separately. The reviewers were added after registration
and are not changes to the frozen experiment.

## Portable evidence archive

Download the [final archive](../artifacts/delivery/ai-safety-study-final-20260913.tar.gz)
and its [verification receipt](../artifacts/delivery/ai-safety-study-final-20260913.tar.gz.verification.json).
The receipt records the archive SHA256, size and read-back result. Inside the
archive, `MANIFEST.json` lists each file's SHA256 and byte count;
`source-history.bundle` preserves the Git history, including the preregistration
commit. Extract into a separate directory before running the replay commands.
The archive contains all 15,710 confirmation episodes and retained development
records; weights and compiled runtime are deliberately omitted.
