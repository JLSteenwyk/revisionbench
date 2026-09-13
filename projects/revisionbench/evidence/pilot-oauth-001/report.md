# RevisionBench feasibility pilot

Model: `gpt-5.6-luna` via `codex_oauth`. Recorded 18 of 18 planned trials.

| Strategy | Success | Model calls | Sandbox executions | Median elapsed seconds |
| --- | ---: | ---: | ---: | ---: |
| repair | 6/6 | 24 | 11 | 31.52 |
| rebuild | 6/6 | 29 | 12 | 32.74 |
| dependency_repair | 6/6 | 24 | 12 | 27.99 |

Statuses: {"success": 18}.

Artifact-level checks, usage totals and unaffected-output comparisons are in `summary.json`. Every final grade requires a valid snapshot from execution with clean outputs. Missing grades are not counted as artifact passes. No grader feedback was supplied to the model.

Limitations:

- Six calibration cases across two workflows on one dataset; one model and one trial per cell.
- No significance tests, broad superiority, novelty or publication-readiness claims.
- Oracle dependency map is simple and author-supplied; rebuild can reuse prior code.
- Fresh stateless CLI invocation per model turn; earlier visible conversation is replayed.
- Provider-side sampling and snapshot version are not pinned; hosted replay is not guaranteed identical.
- Byte identity is a stricter diagnostic than semantic correctness; sample_counts grading checks semantics.
- Elapsed time includes client startup, authentication, provider queueing, inference and sandbox execution.
- Token counts reflect reported usage, including repeated context; cached/reasoning tokens are subsets, not extra totals.

No separately billed inference was used. Dollar cost, GPU utilization and peak client memory are unavailable.
