# Evidence and outstanding work

This is an active study, not a completed deliverable.

## Completed development work

- User objective copied verbatim into docs/objective.txt.
- Empty workspace inspected; one-GPU policy retained even though both GPUs were idle during inspection.
- Local GPU and dependency evidence saved in artifacts/environment.
- Pinned model repository revisions and licenses checked through public Hugging Face metadata.
- Existing vLLM installation diagnosed as unusable due to missing libcudart.so.13; existing environment left unchanged.
- Separate Python environment and CUDA llama.cpp build created. Runtime commit: acecd56032ddc34bada14a2d978f110d9c987095.
- Simulator, JSON-action controller, randomized peer experiment, seeded/natural recovery branches, trace export, and initial analysis implemented.
- 26 unit/integration tests passed as recorded in artifacts/environment/tests.txt, including registration integrity, forbidden-target scoring, within-seed pairing, trace diagnostics, multiplicity-adjusted interval widths, and JSON-type changes to protected records.
- Primary literature comparison updated after full-method checks revealed substantial overlap.
- Prospective sample-size simulation completed and saved in artifacts/sample-size-planning.json; this is planning evidence, not model data.
- Development-only pipeline created in scripts/development_pipeline.py. Its plan is in results/development-001/plan.json; it waits for verified weights and will not start confirmation.

## Required before completion

- Both model downloads and pinned SHA256 checks are complete. Qwen's initial runtime and 66-episode pilot passed replay audits; details and compatibility failures are in docs/pilot-results.md. Complete both models' amended-format runtime measurements.
- Complete results/development-002: nine tasks per experiment/model using the common alternating chat layout. Initial Qwen competence passed; Ministral's earlier consecutive-user template failure is preserved.
- Run and analyze development pilot and recovery experiments; fix issues without tuning on confirmation data.
- Complete sample-size justification and freeze preregistration before any confirmation run.
- Run held-out confirmatory experiments, retaining failed configurations and null results.
- Evaluate precision sensitivity where relevant and disclose limits.
- Complete analysis, report, reproducibility instructions, and requirement-by-requirement final audit.

Actual process liveness must be checked using tool handles or operating-system state; this document does not imply a job is running.
