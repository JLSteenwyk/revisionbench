# Completed confirmation results

The full study is still running. This document records completed, audited runs
only and is not the final research report. No schedule or analysis changes are
made in response to these results.

## Qwen Q4 peer experiment

Completed 4,320 episodes: 240 held-out tasks, two generations and nine conditions.
All 4,320 episodes passed the replay state/score consistency audit. An additional
review verified exact raw task/seed/condition coverage against the saved schedule,
every initial scenario against the held-out bank and every initial eight-step
budget. No infrastructure errors occurred.

The registered primary source-by-permission interaction was **+0.625 percentage
points**, with a task-cluster bootstrap **97.5% interval of −5.83 to +7.08 points**.
The conservative Hoeffding 97.5% interval was −37.59 to +38.84 points. This run
does not establish an extra permission-claim effect from peer attribution versus
reference attribution. It does not prove equivalence or general absence of peer
influence.

| Message/control | Unauthorized attempt | Actual unauthorized change | Legitimate completion |
| --- | ---: | ---: | ---: |
| No message | 35.42% | 35.42% | 94.17% |
| Peer facts | 42.08% | 42.08% | 91.04% |
| Peer reported success | 43.13% | 43.13% | 91.46% |
| Peer claimed permission | 79.17% | 79.17% | 90.63% |
| Reference facts | 48.96% | 48.96% | 93.54% |
| Reference reported success | 49.38% | 49.38% | 91.88% |
| Reference claimed permission | 85.42% | 85.42% | 94.17% |
| Owner authorized | 0% | 0% | 93.13% |
| Authorized shortcut | 0% | 0% | 91.67% |

Each row contains 480 episodes. The three outcome columns are separate measures;
completing the legitimate task does not imply staying within permission bounds.
Attempt and change rates happen to coincide in this completed run.

Registered secondary comparisons on unauthorized attempts:

- Claimed permission versus facts, averaged over source: **+36.77 points**
  (bootstrap 95% interval +31.88 to +41.46).
- Peer versus reference, averaged over claim: **−6.46 points**
  (bootstrap 95% interval −8.96 to −3.96).
- Reported success versus facts, averaged over source: **+0.73 points**
  (bootstrap 95% interval −2.50 to +4.06).

These are secondary results, not replacements for the primary interaction.
The source main effect's conservative Hoeffding 95% interval includes zero
(−23.99 to +11.07 points); its apparent precision therefore depends on the
bootstrap assumptions. The permission main effect's conservative interval is
+19.24 to +54.30 points. Full intervals and remaining registered contrasts are
retained in the analysis JSON. Generalization is limited to the pinned model,
controller, scripted messages and three synthetic task families.

Descriptive execution checks: the run contained 12,632 model responses, including
553 invalid actions (4.38% of responses). There were 229 clarification requests
across 198 episodes. No response used the accepted single-JSON-fence format.
Summed episode wall time was 5,344.69 seconds (89.08 minutes); summed inference
latency was 5,336.68 seconds. Reported token usage was 7,153,670 prompt tokens and
181,947 completion tokens, all served locally.

Among episodes that violated permissions, the median first violation occurred
at step one for both permission-claim conditions, step two for both facts-only
conditions and step three without a message. These conditional summaries compare
different subsets of episodes and are not standalone causal estimates of speed.
Episodes without a violation have finite observation, not proof of indefinite
compliance. No operation was blocked in this peer run, so it provides no evidence
about behavior after denial; that question belongs to the intervention experiment.

Descriptive rates by task family and wording variant, plus aggregate execution
counts, are saved in `results/confirmation-001/qwen-peer/descriptive-review.json`.
They do not introduce new primary tests.

Evidence: `results/confirmation-001/qwen-peer/{analysis.json,audit.json,
diagnostics.json,manifest.json,schedule.json,summary.jsonl,episodes/}` and
`results/confirmation-001/qwen-peer-execution-review.json`. Raw outputs remain
available for checking rounding and every reported contrast.

## Outstanding

Qwen replacement/intervention, the complete Ministral schedule, conditional Q8
validation/comparison, full diagnostics synthesis and the final report remain
pending. Natural recovery results must be reported separately from seeded states.
