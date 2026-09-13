# Programmatic safety-profile extension

RevisionBench measures observable authorization behavior, protected-data integrity, reporting accuracy, support for specified claims, and handling of uncertainty. Task utility and containment are separate; there is no universal safety score.

- [Measurement design and scoring scope](design.md)
- [Related-work assessment](related-work.md)
- [Development specifications, version 0.2](development-tasks-v02.json)
- [Author-visible reserved specifications](reserved-author-visible-tasks-v02.json)
- [Initial scorer calibration](evidence/scorer-calibration-001/validation.json)
- [Current status and continuation](CONTINUATION.md)

The operation engine, independent observations, structured-report runner, aggregate report and audit are implemented. The pilot must be frozen only after validation. Calibration fixtures and scripted reference executions are software validation, not model results.

## Usage

From the repository root, with the existing sandbox prerequisites:

```bash
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_safety_tests -v
python -m revisionbench_safety.validation --output revisionbench_runs/safety-development/calibration-NEW
python -m revisionbench_safety.reference_validation --output revisionbench_runs/safety-development/reference-NEW
```

Save passing integration-test output to a file. After validating OAuth access and native-tool restrictions, initialize a new pilot directory (never overwrite an earlier attempt):

```bash
python -m revisionbench_safety.runner init --output revisionbench_runs/safety-pilot-oauth-001 --model gpt-5.6-luna --validation-evidence PATH_TO_PASSING_TEST_LOG
python -m revisionbench_safety.runner run --output revisionbench_runs/safety-pilot-oauth-001 --model gpt-5.6-luna
python -m revisionbench_safety.audit revisionbench_runs/safety-pilot-oauth-001
python -m revisionbench_safety.report revisionbench_runs/safety-pilot-oauth-001
```

Hosted inference uses the official CLI and existing ChatGPT OAuth login. No API keys or paid fallback are used. Run resumes the frozen plan and preserves interrupted attempts without repeating them; do not resume hosted calls while an access limit remains unresolved. Code changes after freezing are rejected. The original correction pilot remains separately auditable.
