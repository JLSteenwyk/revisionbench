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
- 31 unit/integration tests passed as recorded in artifacts/environment/tests.txt, including registration integrity, forbidden-target scoring, within-seed pairing, trace diagnostics, multiplicity-adjusted interval widths, and JSON-type changes to protected records.
- Primary literature comparison updated after full-method checks revealed substantial overlap.
- Prospective sample-size simulation completed and saved in artifacts/sample-size-planning.json; this is planning evidence, not model data.
- Development-only pipeline created in scripts/development_pipeline.py. Its plan is in results/development-001/plan.json; it waits for verified weights and will not start confirmation.

## Completed validation and registration

- Both primary weight files passed pinned SHA256 checks and loaded on one GPU.
- Both models completed 198 shared-format development episodes and passed all replay audits in results/development-003.
- Natural recovery completed and audited: Qwen 72 replacement + 40 intervention branches; Ministral 63 + 35.
- Revised-identifier controls passed: Qwen 25/27 tasks, no invalid actions; Ministral 21/27, 0.99% invalid actions.
- The materialized 240-input held-out bank is unique and disjoint from current and earlier saved development inputs. Earlier format failures and the failed task-bank audit are retained.
- Local preregistration frozen at 2026-09-13T00:19:48.976082+00:00, before held-out inference, and committed as b8efaaa. Registration SHA256: 9b9cb2ba760d2db2c60983c37a12b910622a462709e9ab857abc2eaa1fa1dc89.
- Registered primary execution started in results/confirmation-001. Its first run manifest confirms the held-out split, 240 tasks, two generations, and matching registration hash.
- Q8 controls and its registered secondary peer comparison are queued after successful completion of both primary schedules. Q8 admission remains conditional on weight/runtime and competence checks.

## Required before completion

- Finish and audit the registered primary peer, seeded recovery, and natural recovery schedules; retain nulls and any failures.
- Complete Q8 integrity/runtime/competence validation and its registered paired sensitivity check, or document an actual eligibility failure.
- Produce full uncertainty analyses, concise research report, portable evidence/reproduction package, and requirement-by-requirement completion audit.

Actual process liveness must be checked using tool handles or operating-system state; this document does not imply a job is running.

## Qwen confirmation completion — 2026-09-13 UTC

All five registered Qwen runs completed and passed replay: 4,320 peer, 960 seeded
replacement, 1,071 natural replacement, 600 seeded intervention and 595 natural
intervention episodes (7,546 total). Completed results, uncertainty and caveats
are recorded in `docs/confirmation-results.md`. The primary pipeline has advanced
to Ministral. Full-study completion, the Q8 comparison and final report remain
pending.

## Ministral peer confirmation completion — 2026-09-13 UTC

All 4,320 registered peer episodes completed and passed replay and schedule
checks, with zero infrastructure errors. Results and uncertainty are recorded in
`docs/confirmation-results.md` and the working research report. The primary
interaction interval includes zero. The two authorized-control violations were
reviewed directly: both targeted the still-protected prepared bundle, rather
than the action authorized by the control. The pipeline has advanced to seeded
replacement. The remaining recovery runs, independent reviews, Q8 comparison
and final package remain unfinished.

## Ministral seeded replacement completion — 2026-09-13 UTC

All 960 seeded replacement episodes completed and passed replay and schedule
checks, with zero infrastructure errors. Cell rates, secondary contrasts and
both bootstrap and conservative intervals are in the confirmation results and
working report. Independent reviews remain pending. The live primary pipeline
has advanced to natural replacement. Frozen registration and all registered
file/source hashes were reverified before this reporting update.

The independent seeded replacement review now passes all 960 initial states and
3,360 transitions, including target authorization, actual protected changes and
legitimate completion. Prompt and raw parsing review are not covered by this
check. Its post-registration reviewer and evidence are retained.

Natural replacement checkpoint selection independently verified: 86 eligible
Ministral tasks, no shared notes, and queues in 13 checkpoints. The registered
schedule has 774 branches. Note-retention effects cannot be identified from
these states; queue retention varies input in only 13/86 checkpoints. No seeded
substitution or schedule change was made.

## Ministral natural replacement completion — 2026-09-13 UTC

All 774 natural replacement branches passed replay and schedule checks, with
zero infrastructure errors. Cell outcomes and secondary uncertainty are reported
in the confirmation results. No new unauthorized changes occurred in fresh-agent
branches, while some forbidden attempts remained. The fresh-versus-original
attempt interval includes zero. Independent branch reviews remain pending.
The primary pipeline has advanced to seeded intervention.

Independent natural replacement branch review passes all 774 initial states and
2,432 transitions, including parent links, equal budgets and scored outcomes.
Prompt and raw parsing checks remain separate outstanding work.

Natural replacement prompt/parser review now passes: 688 fresh prompts, 86
original parent histories and all 2,432 raw-response/action mappings. Decoding
failures remain included. Intervention inference and later deliverables continue.
