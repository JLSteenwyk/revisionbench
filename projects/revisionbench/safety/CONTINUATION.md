# Completed objective and continuation

The requested implementation, validation, one small OAuth pilot, audited evidence and findings report are complete. Final repository publication verification is recorded in the accompanying completion check. The approximate three-day horizon was not a requirement to wait or expand the experiment.

## Completed work

- Separate `revisionbench_safety` package: task preparation, trusted mediation and journals, independent scoring, bounded OAuth runner, reporting and audit. Original frozen packages remain unchanged.
- Fourteen development cases across seven matched pairs. Two author-visible reserved specifications remain unprepared and untested by models; no blind-holdout claim.
- Thirty manually labeled scorer fixtures and 14 author-scripted reference executions passed. All 29 safety tests, the additional receipt-audit check, and all 31 original tests passed. Failed development logs and the redaction fix are preserved.
- One frozen `gpt-5.6-luna` OAuth pilot completed all 14 attempts with no replacement, access or infrastructure failure. There were 39 inference calls with unique ephemeral sessions, four sandbox executions, and one repaired protocol error. A separate OAuth preflight is recorded.
- All 14 scores reproduce from sealed events and final workspaces. The 287-file archive was extracted and audited again. Completed-plan resumption made zero inference calls and changed no pilot file content.
- Results: strict utility 9/14; no observed unauthorized requests or state changes; reporting 108 correct, one incomplete issue-list field and 31 unknown fields; two factual claims correct; both required clarifications conform. See `pilot-report.md` for the distinction between truthful uncertainty, task failure and safety behavior.
- Historical correction-pilot audit passed; all 42 older registered file hashes and its aggregate source hash remain unchanged.

## Artifacts and exact commands

Implementation freeze commit: `e422577`. Pilot configuration SHA-256: `7b6bccc0f4a9add127cb9dbeda2d4b13fac6227d23cb51b122d1c1da6d6d53dd`.

Published evidence: `projects/revisionbench/safety/evidence/pilot-oauth-001/`. Software validation, preserved failure logs, full reference-execution archive and OAuth preflight: `projects/revisionbench/safety/evidence/implementation-validation-002/`. Working originals remain in ignored `revisionbench_runs/`.

Read-only audit and offline report regeneration:

```bash
python -m revisionbench_safety.audit revisionbench_runs/safety-pilot-oauth-001
python -m revisionbench_safety.report revisionbench_runs/safety-pilot-oauth-001
python projects/revisionbench/audit_pilot.py revisionbench_runs/pilot-oauth-001
```

Portable extraction/audit commands are in `pilot-report.md`. No new inference is needed. `package_evidence.py` packages only a terminal audited pilot into a new destination, under the runner lock, with per-file hashes and credential-pattern checking.

## Processes, limitations and future work

Pilot runner session `4331` returned exit code zero. OAuth preflight, initialization, test and push processes also finished. No process launched for this objective remains active. No GPU job or local model server was started or stopped. Revalidate live state before any future execution rather than relying on this note alone.

No required implementation or pilot work remains. Research questions remain open: whether the reporting requirements measure task-relevant utility; whether the literal CSV-edit interface adds avoidable difficulty; how to observe internal code attempts reliably; and whether substantively different tasks yield useful generalization. No novelty or publication-level behavioral finding is established. Those are future studies, not missing observations to impute as safe. Do not change frozen scores or launch more models without review of this pilot.

Do not stage unrelated `artifacts/` or `results/`. Credentials and model weights are excluded from published evidence.
