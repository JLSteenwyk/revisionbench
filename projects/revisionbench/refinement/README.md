# Measurement refinement and confirmation pilot

Version 0.3 separates core task success, authorization, reporting accuracy, reporting coverage, evidence support and uncertainty. The earlier 14-trial pilot and its original scoring remain unchanged.

The new **24-trial OAuth confirmation pilot is complete and audited**: 23/24 core-task successes, 102/102 checkable action/outcome fields correct, 22/22 available facts answered correctly, and one appropriately unknown calibration fact. No unauthorized direct request or state change was observed. These are narrow task results, not a general safety certification.

- [Confirmation findings and scale decision](confirmation-report.md)
- [Larger-study proposal — review required, not launched](scale-up-proposal.md)
- [Machine-readable proposed scope](scale-up-plan.json)
- [Measurement design](design.md)
- [24 versioned development specifications](development-tasks-v03.json)
- [Report protocol](report-protocol-v03.txt) and [prospective scale gates](scale-gates-v03.json)
- [Reserved author-visible specifications](reserved-author-visible-v03.json) and [exposure history](exposure-record.json)
- [Pre-inference validation](evidence/preflight-validation-002/manifest.json)
- [Audited model evidence](evidence/confirmation-oauth-001/manifest.json)
- [Continuation and exact commands](CONTINUATION.md)

Validation includes 28 refinement tests, 60 historical regression tests, 34 manually labeled calibration fixtures and 24 author-scripted reference executions. Software-validation records are separate from model results. Literal and structured CSV interfaces both pass reference solutions, but the model succeeded only with the structured interface in this one-per-condition comparison. This does not establish a causal effect.

Offline verification from the repository root:

```bash
python -m revisionbench_refinement.audit revisionbench_runs/refinement-pilot-oauth-001
python -m revisionbench_refinement.report revisionbench_runs/refinement-pilot-oauth-001
python -m revisionbench_safety.audit revisionbench_runs/safety-pilot-oauth-001
```

Portable archive extraction commands are in the confirmation report. No inference is needed to reproduce the scores. The proposed 384-trial larger study requires review and is not implemented as an automatic continuation of this pilot.
