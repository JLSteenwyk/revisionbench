# Active objective and continuation

Objective: implement and validate a programmatic safety profile, then complete one small OAuth development pilot and publish sanitized evidence. Approximately three days is a work horizon, not a waiting requirement. The full user objective is in `/home/bizon/.codex/attachments/9f3457c2-3eca-4179-ab82-95a388d40289/pasted-text-1.txt`.

## Completed in the first implementation stage

- Inspected existing runner/scorers/pilot and four primary benchmark implementations. Pinned source links and hashes are recorded.
- Wrote the measurement design, observation limits and focused related-work assessment.
- Added a separate `revisionbench_safety` package, preserving the original frozen `revisionbench` source hashes.
- Implemented typed permission checks, a sealed event journal, and deterministic safety-profile comparisons with explicit unknown/missing observations.
- Defined 14 development task specifications across seven matched pairs. They are planned tasks, not model results.
- Fourteen unit tests pass; 30 manually labeled calibration fixtures match their expected labels. Small fixture sensitivities/FPRs are not general detector performance estimates.
- The original 18-trial correction pilot still passes its audit against the unchanged implementation.

No new safety-model inference has run. No reserved evaluation instances have been generated yet. No task/scorer/pilot configuration has been frozen. The model-facing operation engine, observations from real executions, safety trial controller, aggregate pilot report and final audit remain incomplete.

## Next work, in dependency order

1. Implement real task preparation, independently verified baselines and interventions. Generate a separate author-visible reserved set; document its exposure and relatedness without claiming blind holdout status.
2. Build a trusted operation engine connecting `policy.py`, `ledger.py`, the existing sandbox and bounded file operations. Journal requests before enforcement and results afterward. Keep the journal/seal, private task oracle and other trials outside candidate mounts. Derive protected changes and factual truth from trusted observations, not submitted reports.
3. Implement the structured final-report protocol and safety runner using the existing OAuth adapter. Add per-trial source/config hashes, randomization, hard budgets, resumption accounting, and a global attempt ceiling of 60 (planned pilot 14). Log all calls and protocol errors. Never feed hidden scores back.
4. Validate actual operation-engine behavior, denied attempts, successful forbidden state changes in disposable sandbox copies, inability to tamper with trusted logs, missing snapshots, interruptions and infrastructure/access failures. Rerun scorer fixtures and existing relevant tests after changes. Preserve failures/fixes.
5. Recheck supported OAuth login/client version and native-tool isolation without extracting tokens. Freeze only after the above gates pass, then run one 14-trial development pilot. No extra model or expansion based on results.
6. Compute per-dimension rates with denominators/opportunities/unknowns, audit and package all trials, write limitations/recommendations, update continuation state, commit and push. Do not mark the goal complete before actual required evidence exists.

## Commands available now

```bash
python -m unittest discover -s revisionbench_safety_tests -v
python -m revisionbench_safety.validation --output revisionbench_runs/safety-development/calibration-NEW
python -m revisionbench_safety.tasks
python projects/revisionbench/audit_pilot.py revisionbench_runs/pilot-oauth-001
```

Use a new calibration output directory. Sources under `revisionbench_safety` may change until the new pilot freezes; keep the original `revisionbench` package unchanged so the historical pilot remains auditable. Do not add the unrelated untracked `artifacts/` or `results/` directories to Git.

## Processes and access

No live process was launched for this safety stage. No GPU job or local model server was started or stopped. The earlier OAuth pilot completed; its process is terminal. Revalidate actual process handles and OAuth status before relying on earlier observations. Credentials must remain accessible only to the trusted official client, with native model tools disabled.
