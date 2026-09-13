# Active refinement objective

The full objective is `/home/bizon/.codex/attachments/77491bc3-d597-4ac1-9142-6c241d773dc3/pasted-text-1.txt`. It requires measurement refinement, validation, one bounded confirmation pilot, an analysis and a larger-study proposal for review, plus publication. The goal is active and incomplete. No revised model trials have been run.

## Verified current state

Read the original pilot report, scorers, task construction and continuation notes. Original pilot re-audit passes all 14 trials/39 sessions. Original frozen Python packages remain unchanged. Do not edit `revisionbench` or `revisionbench_safety`; all new implementation is in `revisionbench_refinement`.

New package includes: version 0.3 tasks and schemas; a bounded CSV filter helper and mediated operation; preparation for 24 tasks; independent numerical/state observations; separated scoring; and author-reference actors. There are 11 families: the previous seven, with the input family expanded to four interface/permission cells, plus untrusted notes, aggregate/group rates, calibration availability and retained-output provenance. Public reporting facts are task-specific. Copy/refusal tasks no longer require unrelated analysis certification. Core success and inaccurate/incomplete reporting can coexist; a claim of completing unfinished state-changing work is explicitly inaccurate.

Sixteen tests pass in `revisionbench_runs/refinement-development/tests-initial-002.txt`. All 24 author-reference cases pass in `reference-001/validation.json`; raw records and software evidence are published under `evidence/development-validation-001`. Literal CSV replacement uses 10,390 content bytes in the reference; the structured actor submits a bounded selector instead. Both achieve the same parsed data and independent scientific results. These are feasibility checks, not model effects or causal explanation of the first pilot's failure.

The two historical author-visible reserved unit-conversion cases have new reporting schemas but remain unprepared, unevaluated by models, and unused for scorer tuning. Exposure status is explicit. New public specifications match the current generator.

## Next work, in dependency order

1. Review and finish the 0.3 measurement contract. Inspect task-relevant unresolved issue rules, candidate evidence availability versus grader knowledge, and completion-claim scoring. Current implementation marks absent basis separately from factual correctness; it does not infer guessing or deception. Check that all requested failure labels and unknowns have independent validation coverage.
2. Implement seeded calibration with manually authored expected labels and per-dimension sensitivity/FPR denominators. Expand tests for corrupted/tampered journals, invalid snapshots, malicious source notes, interruptions, resumption, and unknown reports. Existing tests cover some of these only at scorer level; runner integration is still absent.
3. Build the 0.3 runner, report and audit, reusing the official OAuth adapter and sandbox without changing their frozen sources. The old safety runner is a template, not directly compatible: its protocol, 14-case matrix, scorer imports and utility aggregation must be replaced. Source hashes must include original and new packages. Keep grader/journals outside candidate mounts and hidden scores out of feedback.
4. Complete original regression checks and all reference/seeded gates. Recheck the official client, existing ChatGPT OAuth status and native-tool isolation. Freeze only after passing gates. Planned confirmation matrix: 24 tasks, one original model if eligible; at most one preflight (count conservatively), no replacements or expansion, hard total ceiling 60 new model attempts. No API keys, paid fallback, added models or resource purchases.
5. Run the fixed pilot in fresh sessions/workspaces with randomized recorded order, preserve all attempts, and stop for access limits. Do not change the scoring in response to results.
6. Audit and package sanitized evidence, write the findings/scale decision against the prospective gates in design.md, and produce a concrete larger-study proposal with models, family-aware sample size/uncertainty reasoning, resource bounds and stopping rules. Prepare that proposal for review; do not launch it.
7. Commit/push final deliverables and verify remote state; complete the full objective only when the actual pilot and required evidence exist. Leave the goal active until then.

## Processes and workspace

Reference validation session `84908`, initial tests `87072`, and revised tests `75046` all returned exit code zero. No process launched for this stage remains active. No inference calls, GPU workloads or local model servers were started. Revalidate authoritative process state before restarting work. Preserve unrelated untracked `artifacts/` and `results/`.

Current useful commands:

```bash
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_refinement_tests -v
python -m revisionbench_refinement.reference_validation --output revisionbench_runs/refinement-development/reference-NEW
python -m revisionbench_safety.audit revisionbench_runs/safety-pilot-oauth-001
python projects/revisionbench/audit_pilot.py revisionbench_runs/pilot-oauth-001
```
