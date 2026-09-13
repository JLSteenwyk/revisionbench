# Measurement refinement: active development

This is a new 0.3 measurement version. The earlier 14-trial pilot and its scoring remain frozen and auditable.

- [Measurement design and prospective confirmation gates](design.md)
- [24 development specifications](development-tasks-v03.json)
- [Author-visible reserved specifications](reserved-author-visible-v03.json)
- [Exposure history](exposure-record.json)
- [Development validation evidence](evidence/development-validation-001/manifest.json)
- [Active work and continuation](CONTINUATION.md)

Implemented: separate core task success, authorization, reporting accuracy and coverage, task-specific facts, evidence-availability labels, a bounded CSV interface, and four additional task families. Sixteen tests and 24 author-scripted reference cases pass. These are software-validation results; no revised-version model trial has run and nothing is frozen for confirmation inference yet.

Run validation from the repository root:

```bash
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_refinement_tests -v
python -m revisionbench_refinement.reference_validation --output revisionbench_runs/refinement-development/reference-NEW
python -m revisionbench_safety.audit revisionbench_runs/safety-pilot-oauth-001
```

Use a new reference output directory. Full calibration, the confirmation runner and audit, model pilot, findings and scale-up proposal remain required. Do not launch a larger study from this development milestone.
