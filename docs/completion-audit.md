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

## Interim source review — 2026-09-13 UTC

Inspected `safety_study/agent.py`, `safety_study/world.py`,
`scripts/serve.py`, `scripts/audit_run.py`, the protocol and the first
confirmation run manifest while the primary pipeline remained live.

- The controller parses JSON and passes the resulting object to `World.step`.
  Record operations address an in-memory dictionary; names are never opened as
  host paths. Queue dispatch allows only the three record-mutation operations.
  These observations support the intended tool boundary, not a general security
  audit of the native inference runtime or its dependencies.
- The inference client permits literal loopback HTTP only, disables proxies and
  redirects, and sends no provider authentication header. The launcher binds to
  loopback and sets one GPU UUID. This supports local inference by this harness;
  final review still needs provenance and telemetry across every run.
- Source labels are the only source-factor difference in the message generator.
  The success and permission suffixes also change message length. Thus a claim
  effect concerns these specific messages, not an isolated semantic property
  independent of wording or length. The source-by-claim interaction is the
  registered primary comparison.
- `ask_owner` always returns a scripted refusal to grant additional permission.
  Clarification counts measure requests in that workflow, not the effectiveness
  of real human oversight. The supplied correct prepared bundle makes task
  completion largely a choice of execution route, limiting generalization to
  difficult open-ended work.
- The replay auditor re-executes saved actions with the same deterministic
  simulator implementation. It verifies trace/state/score consistency, but is
  not an independently implemented authorization oracle. Scoring tests and
  source review therefore remain necessary evidence alongside replay checks.
- The active Qwen peer manifest records 240 tasks, two generations, eight steps,
  temperature 0.7, 512 output tokens, the held-out split, pinned Q4 weights and
  the frozen registration hash. This establishes the configured run; only
  complete raw coverage can establish that the schedule actually finished.

These findings should inform the final report's limitations. No registered
implementation, hypotheses, or analysis changed during this review.

At 2026-09-13T01:00:34 UTC, an independent comparison of the first peer run's
saved schedule against the held-out task bank verified all 4,320 planned
task/generation/condition combinations, including the registered seed formula
and eight-step budgets. Evidence:
`results/confirmation-001/qwen-peer-schedule-review.json`. This checks the
planned schedule only; execution was still in progress and remains unverified
until complete raw coverage is audited.

## Completed-run evidence — 2026-09-13 UTC

- Qwen peer: all 4,320 episodes passed the pipeline replay audit. The additional
  `results/confirmation-001/qwen-peer-execution-review.json` verifies raw
  task/seed/condition coverage against the schedule, initial scenarios against
  the held-out bank and initial budgets. Completed analysis and descriptive
  diagnostics are recorded in `docs/confirmation-results.md`.
- Qwen seeded replacement: all 960 episodes passed the pipeline replay audit;
  completed results are recorded separately from natural replacement. The
  initial-state/retention and saved prompt verification are recorded below.
- Qwen natural replacement: an independent pass through all saved peer episodes
  reconstructed the frozen selection rule and exactly matched all 119 selected
  checkpoints, including snapshots, histories, metadata, order and remaining
  budgets. Evidence is in
  `results/confirmation-001/qwen-natural-replacement-selection-review.json`.
  None of these checkpoints has notes or a pending queue. This verifies
  selection provenance. All 1,071 branches subsequently passed replay; their
  completed outcomes are recorded in `docs/confirmation-results.md`.

The study's overall disposition remains incomplete.

Further independent checks on 2026-09-13 UTC:

- Natural intervention selection exactly matches the first eligible episode per
  task and the checkpoint before its first unauthorized attempt: 119 checkpoints,
  with four to eight remaining steps. Saved snapshots, histories and parent
  metadata match the source episodes. Evidence:
  `results/confirmation-001/qwen-natural-intervention-selection-review.json`.
  All 595 branches subsequently completed and passed replay.
- Initial states for all 960 seeded replacement, 1,071 natural replacement and
  600 seeded intervention episodes match independently constructed expectations
  for retained notes, queues, environment records and intervention settings.
  Task/condition coverage, seeds and initial remaining budgets also match.
  Evidence: `results/confirmation-001/qwen-branch-initial-state-review.json`.
  This check does not call the simulator's replacement function. It verifies
  initial state construction, not prompt provenance or an independent scoring
  oracle. Those remain distinct audit requirements.

- Saved first-request histories for the same three completed branch runs also
  match the intended context. All 2,512 fresh histories contain only the
  registered system prompt and the original task, current permissions and
  retained workspace. All 119 original-continuation histories exactly preserve
  the selected parent history after the documented adjacent-user-message merge.
  Owner instructions and workspace text were independently reconstructed;
  system text was compared with the frozen constant. Evidence:
  `results/confirmation-001/qwen-branch-prompt-review.json`. This verifies saved
  controller requests, not the inference engine's internal cache behavior.

- Qwen natural intervention: all 595 initial branch states and first-request
  histories match independent construction from their selected parent
  checkpoints. Every checkpoint has all five conditions, with the correct seed,
  remaining budget and parent link. Owner-correction and acceptable-stop branches
  append the complete owner instruction; other branches preserve parent history.
  Evidence: `results/confirmation-001/qwen-natural-intervention-branch-review.json`.
  This closes the saved initial-state and prompt checks for Qwen's branch runs;
  runtime provenance and independent statistical review remain separate work.

- Qwen primary statistical review: reconstructed attempted-violation outcomes
  from raw trace events, paired four source/claim cells within each of 480
  task/generation blocks and averaged the two generations within each of 240
  tasks. An independent bootstrap implementation reproduces the registered
  source-by-permission estimate (+0.625 percentage points), 97.5% interval
  (−5.83 to +7.08 points), and conservative interval (−37.59 to +38.84 points).
  Evidence: `results/confirmation-001/qwen-primary-statistical-review.json`.
  This verifies pairing, task clustering and interval arithmetic; it relies on
  the recorded authorization labels and is not an independent scoring oracle.

- Independent Qwen state-outcome review covers all 7,546 episodes and 22,647
  saved transitions. Direct before/after comparisons, with type-sensitive JSON
  equality and owner permissions applied independently, reproduce every event's
  forbidden-change targets, every episode's new-change score and final legitimate
  completion score. Starting from each branch's initial state excludes inherited
  predecessor damage from new-change counts. Evidence:
  `results/confirmation-001/qwen-independent-state-outcome-review.json`.
  This does not call simulator scoring or hashing functions. It verifies state
  outcomes, not intended write targets, task answer construction, or complete
  independent replay of tool semantics.
