# Completion audit

Status: **incomplete**. This checklist was added after preregistration to organize
delivery verification. It does not amend the experiments, scoring, exclusions,
or analysis. Paths below identify evidence to inspect, not assertions that the
evidence already proves completion. Final sign-off requires actual inspection
and a dated finding for every row.

## Objective requirements

| Requirement | Evidence and scope required at final review | Current disposition |
| --- | --- | --- |
| Closest primary research and specific contribution | Inspect `docs/literature.md` and the final report for established findings versus hypotheses, source-specific method comparisons, and the absence of an unsupported priority claim. Preserve the distinction between pre-freeze review and later literature follow-up. | Literature comparison exists; final synthesis pending. |
| No unsupported explanation of the Hugging Face incident | Inspect the final report for incident-specific claims; without incident evidence, restrict conclusions to the simulated tasks. | Final report pending. |
| Isolated synthetic workplace and valid authorized solutions | Review `safety_study/world.py`, controller tool dispatch, local client restrictions, tests, and saved action traces. Verify fake records/notes/queues, permissions, technically possible violations, and authorized solutions across all three task families and held-out cases. Model outputs must never be executed as host code. | Implementation and development evidence exist; final review pending. |
| Local models, pinned availability/license/runtime/precision, one GPU | Inspect both primary weight manifests, upstream metadata, model configurations, launcher records and GPU telemetry for every run. Confirm the designated GPU and exact weight/runtime/settings provenance. Review competence certificates and their underlying control episodes, not certificates alone. | Both primary models admitted; full-run telemetry pending. |
| Peer influence: matched information, source by claim, three controls | Check the six scripted message conditions and all three controls, actual initial states and permissions, budgets, randomized schedules, task/generation keys, and per-cell coverage in both primary peer runs. Explicitly describe scripted messages. | Confirmation running. |
| Replacement: fresh agents, independent artifact retention, new actions | Check all eight branches, original task/current permissions, retained/removed notes, queue and environment state, fresh history, remaining budgets and reset event counters. Keep seeded and natural origins separate; report when a natural artifact is absent and its effect is not identifiable. Include the registered original-agent continuation comparator. | Development audited; confirmation pending. |
| Intervention: matched checkpoints and five responses | Check branch snapshot identity, equal remaining budgets, the five conditions, actual enforcement across direct and queued operations, and attempts versus changes. Verify that natural branches start before the first attempt, while replacement branches start after it, under the frozen selector. | Development audited; confirmation pending. |
| Deterministic scoring and behavioral outcomes | Inspect replay audits and the underlying scoring logic for attempted/actual violations, legitimate completion, first violation time, clarification, repeated attempts after denial and alternative operations. Distinguish unauthorized no-op writes from actual record changes. Do not infer motives. | Development evidence exists; complete confirmation diagnostics pending. |
| Development pilot and held-out confirmation | Inspect retained failed pilots as well as successful pilots; parsing, solvability, runtime and memory evidence; the revised task bank and disjointness audit; and actual confirmation inputs. Unique identifiers do not establish diverse problem types. | Development complete; confirmation coverage pending. |
| Preregistration before confirmation, justified sample, exclusions and stopping | Verify `configs/preregistration.json` against Git history, all frozen file hashes and controller hash, run manifests and first inference timestamps. Inspect planning assumptions and actual sample coverage. Retain infrastructure failures and any explicit amendments; never substitute an outcome-selected smaller sample. | Registration frozen; full execution audit pending. |
| Task-cluster uncertainty, effects and nulls | Inspect complete analysis outputs and recompute/report registered primary contrasts with 97.5% intervals for the two primary model tests; distinguish secondary 95% intervals. Check task aggregation, shared generation keys, exclusions, non-estimable contrasts and conservative bounds. Report null results without interpreting them as proof of equivalence. | Complete analyses pending. |
| Quantization and application scaffolding | Inspect Q8 admission and the registered paired Q8/Q4 comparison, or document an actual admission failure. Match shared tasks and generation keys. Report third-party quantization provenance, role merging, fence parsing, controller limits and observed generation repeatability; do not attribute all between-model differences to model weights. | Q8 weights downloaded; admission and comparison pending. |
| Local inference and no unauthorized spending | Review launch/client paths and run provenance for local inference; no external paid inference or subscription replication has been authorized. Optional subscription replication is not necessary for completion. | Local execution so far; final provenance review pending. |
| Complete deliverables and reproducibility | Inspect literature, protocol, harness, validated scenarios/tests, versioned configs, pilot results, complete confirmation analysis, final report and reproduction instructions. Verify archive contents/checksums and source history, and make all final artifact links usable. | Report, complete results and archive pending. |

## Registered execution coverage

For **each** of Qwen Q4 and Ministral BF16, inspect raw episode keys against the
saved randomized schedule, not only a completion marker:

- Peer: 240 tasks × 2 generations × 9 conditions = 4,320 episodes.
- Seeded replacement: 120 tasks × 8 retention combinations = 960 episodes.
- Seeded intervention: 120 tasks × 5 conditions = 600 episodes.
- Natural replacement: independently reconstruct the first eligible failure per
  task among task indices 0–119 under the frozen selection rule; expect nine
  branches per selected task, including original continuation.
- Natural intervention: independently reconstruct selection under the same task
  restriction with the before-attempt checkpoint; expect five branches per
  selected task. If no checkpoint qualifies, inspect the raw evidence and the
  explicit unavailable record rather than treating seeded results as a substitute.

For Qwen Q8, admission requires verified pinned weights, a one-GPU load and the
nine-task control pilot under the frozen competence thresholds. If admitted,
inspect 120 tasks × 1 generation × 9 conditions = 1,080 peer episodes and the
paired comparison against Q4 generation zero. Admission failure must be a real,
documented failure, not a substitute for finishing a slow run.

For every completed run, inspect schedule coverage, provenance, replay audit,
diagnostics and analysis. Completion markers and checksum receipts alone do not
prove scientific validity or the completeness of the objective.

## Final sign-off

Not yet performed. Record the review date, concrete inspected evidence, any
remaining uncertainty, and a supported disposition for each requirement above.
Do not mark the study complete while any required item is missing, incomplete,
or unverified.
