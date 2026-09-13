# First OAuth pilot: feasible execution, a ceiling in the current tasks

RevisionBench completed all 18 planned trials using `gpt-5.6-luna` through the official Codex CLI's existing ChatGPT OAuth login. Every trial passed all five artifact checks and input integrity after the submitted program regenerated its outputs. This establishes basic runner and task feasibility. It does **not** distinguish the strategies on correction success or justify scaling this task set unchanged.

The pilot ran September 13, 2026, from 14:35:29 to 14:44:26 UTC. Candidate programs ran locally in the bounded Docker sandbox; model inference was hosted through the subscription. No API keys, separately billed inference endpoints, local model server, or additional purchased resources were used. Existing GPU workloads were left alone. The local inference adapter was tested against a loopback mock server; an open-weight model pilot has not been run.

| Strategy | Complete success | Model calls | Sandbox executions | Median trial seconds | Reported input tokens | Reported output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Repair | 6/6 | 24 | 11 | 31.52 | 234,384 | 4,791 |
| Rebuild | 6/6 | 29 | 12 | 32.74 | 273,726 | 5,162 |
| Dependency-guided repair | 6/6 | 24 | 12 | 27.99 | 253,407 | 4,343 |

These are descriptive totals from one trial per cell. They do not establish that one strategy is faster or more efficient. Reported input tokens include repeated conversation context; the client also reported 114,688 cached input tokens across the pilot. Do not add cached tokens to the input counter. Token usage was available for all 77 calls. Dollar cost, peak client memory, and GPU utilization attributable to this pilot were not measured.

There were no terminal model, budget, infrastructure, subscription, or interruption failures. Eight read requests exceeded the eight-file action limit; the model received a protocol error, spent a turn, and recovered. These attempts remain in the transcripts and usage totals. The 35 executions include 18 final runs with clean outputs. All 108 final checks passed: 90 artifact checks and 18 input-integrity checks. Sample counts were correct in all 18 trials. Among the 36 selected unaffected-output byte comparisons, 28 were identical; the others still passed the declared numerical and label checks. Byte differences alone are not evidence of scientific damage or visual equivalence.

## What this tells us

The model can read the protocol, inspect prior work, modify scientific code, recover from a bounded tool error, and produce consistent numerical artifacts without grader feedback. The sandbox, snapshot handling, transcript recording and final evaluation worked for these runs.

The scientific comparison is weak at this scale. All six rebuild trials read `prior/analyze.py`; both repair strategies also read the existing analysis. This follows the frozen information policy, but means rebuilding is a change in active workspace state, not independent problem solving without prior code. The dependency map is a small author-supplied list, and both workflows use one dataset. The only write operation replaces the entire single-file program, so the pilot does not assess the cost advantage of small patch operations in large projects. Fresh CLI sessions replay context each turn, making measured usage partly a property of this harness. Hosted aliases, sampling, caching and queueing also limit exact replay and cost comparisons.

Keep these cases as calibration checks. Before expanding to more models or repetitions, review a design with genuinely different workflow structures, multiple stages and selective downstream invalidation, while keeping input information and tool capabilities matched. Add patch operations if incremental editing cost is an intended outcome. Establish task diversity and related-work overlap before making a novelty or publication claim. No additional model or expanded experiment was launched after this pilot.

## Validation and reproducibility

The [runner documentation](runner.md) specifies the authentication boundary, protocol, budgets and commands. Configuration and source hashes froze before the first trial; order used seed 1729. The implementation is pinned by commit `6ebd3a6`. All 31 unit/integration tests passed, and all six deterministic reference validations passed.

The [post-run audit](evidence/pilot-oauth-001/audit.json) verified the frozen order, all final file hashes, unchanged protected files, budgets, 77 distinct ephemeral CLI sessions, and the exact model-visible feedback chain. It independently regraded all 18 successes. A completed-run resumption returned without new trial output or changes to 294 record/artifact files. The earlier study's frozen registration and source hashes also match their original values.

[Summary and per-artifact results](evidence/pilot-oauth-001/summary.json), [frozen configuration](evidence/pilot-oauth-001/config.json), [complete records](evidence/pilot-oauth-001/records.tar.gz), and [archive hashes](evidence/pilot-oauth-001/archive-manifest.json) are included. Extract the archive into `revisionbench_runs/` and run:

```bash
python projects/revisionbench/audit_pilot.py revisionbench_runs/pilot-oauth-001
python -m revisionbench.report revisionbench_runs/pilot-oauth-001
```

Three development preflights are preserved separately: an unsupported provider-configuration override failed before inference; a no-tools response was incorrectly rejected because the parser treated a startup warning as a tool action; the corrected negative isolation preflight succeeded without exposing its sentinel. These fixes occurred before configuration freeze. Two preflights reached the model; they are excluded from pilot totals. No pilot trial was silently rerun or replaced.
