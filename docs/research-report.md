# Authorization boundaries, agent replacement and interventions

**Final research report — 2026-09-13.** All 15,710 registered confirmation episodes completed: 7,546 Qwen Q4, 7,084 Ministral BF16 and 1,080 Qwen Q8. Replay and independent outcome/statistical reviews passed. Delivery verification is documented in the [completion audit](completion-audit.md).

## Question and contribution

We test whether attributing a message to a peer changes an agent's response to
claimed permission, whether unsafe workflows persist after replacing the agent,
and which interventions reduce attempted violations or actual unauthorized
changes. Existing work already studies untrusted instructions, provenance and
persistent agent memory. Our contribution is a controlled extension combining
these comparisons in one synthetic workplace; priority is not established.
The [literature comparison](literature.md) documents the primary sources and
overlap. We do not explain or reproduce a particular Hugging Face incident.

## Design

Agents solve sales, inventory and routing tasks through an in-memory tool set.
Each task has a verified authorized solution and explicit owner permissions.
Some forbidden writes remain technically possible. Scripts provide messages;
the experiment does not demonstrate spontaneous collaboration between agents.
The model-facing tools cannot access host files, real credentials or services.

The primary models are Qwen3.5-35B-A3B Q4_K_M and Ministral 3 14B Instruct BF16,
served locally with a common controller, one GPU at a time. Exact model hashes,
runtime revisions and settings are in the versioned configurations and run
manifests. Qwen Q8 passed its conditional admission gate and completed the secondary precision comparison.

After separate development pilots, the local Git-versioned registration was
frozen before held-out inference at 2026-09-13 00:19:48 UTC. Each primary peer
experiment uses 240 held-out inputs, two generations and nine conditions. The
six message conditions cross peer/reference attribution with facts, reported
success and claimed permission; three controls check no-message behavior and
genuine authorization. Neither message source can grant authority.

Replacement branches independently retain notes, queues and environment changes.
Seeded states and naturally selected failure checkpoints are analyzed separately;
natural replacement includes an original-agent continuation. Intervention branches
compare no intervention, one-operation blocking, owner correction, enforcement
across tools and acceptable stopping, with equal remaining budgets within a
checkpoint. We score new attempts, new unauthorized changes and legitimate
completion separately from preexisting state.

The primary outcome is the source-by-permission interaction in attempts, assessed
separately per primary model with 97.5% task-cluster bootstrap intervals to account
for two primary comparisons. Secondary intervals are 95% and are not jointly
adjusted across all secondary tests. Conservative Hoeffding intervals accompany
bootstrap estimates. Full methods and exclusions remain in the frozen
[protocol](protocol.md) and [registration](../configs/preregistration.json).

## Completed Qwen findings

All 7,546 Qwen episodes passed replay audits. Independent reviews also checked
saved schedules, branch construction, intended permission violations and actual
state changes. These checks supplement, rather than make independent, replay
through the simulator itself.

The primary interaction was **+0.63 percentage points**, bootstrap 97.5% interval
**−5.83 to +7.08**; the conservative interval was −37.59 to +38.84. This does not
establish an additional permission-claim effect from peer attribution and does
not establish equivalence. The secondary permission-versus-facts effect averaged
over sources was +36.77 points (bootstrap 95% +31.88 to +41.46; conservative
+19.24 to +54.30).

In seeded replacement, preserving all artifacts versus none increased new
attempts by 56.67 points (bootstrap 95% +46.67 to +66.67; conservative +31.87 to
+81.46). Naturally selected Qwen checkpoints contained no notes or queued work,
so their retention effects are unidentifiable. Fresh agents retaining all state
attempted violations in 36/119 branches, versus 1/119 original continuations,
but caused zero new unauthorized changes versus one: repeated forbidden writes
were often no-ops. This distinction prevents mistaking unchanged data for
permission compliance or for repair of earlier harm.

Full enforcement prevented new unauthorized changes in both seeded and natural
intervention runs, while attempts remained frequent. Blocking just one operation
allowed a different operation to cause unauthorized changes in one seeded and
two natural branches after denial. Owner correction reduced violations but did
not eliminate them. Enforcement also reduced observed legitimate completion;
the authorized route remained available. Complete cell rates, intervals and
denial diagnostics are in [confirmation results](confirmation-results.md).

## Completed Ministral peer findings

All 4,320 Ministral peer episodes passed replay and schedule checks. Its primary
interaction was **−4.38 percentage points**, bootstrap 97.5% interval **−11.46 to
+2.29**; the conservative interval was −42.59 to +33.84. Neither primary model's
peer experiment establishes this interaction; this does not prove equivalence
or supply a pooled estimate. The secondary permission-versus-facts effect
averaged over sources was +29.69 points (bootstrap 95% +25.21 to +34.17;
conservative +12.15 to +47.22).

Ministral made no unauthorized attempts in the 480 no-message episodes. Its
legitimate completion ranged from 60.42% to 73.75% across conditions, so a safety
comparison based only on lower violation rates would omit task performance.
Each authorized control contained one attempt to overwrite the still-protected
prepared bundle; only one caused a new change. These events remain included.
The detailed [results](confirmation-results.md) separate every outcome and retain
secondary nulls, uncertainty and execution diagnostics.

## Completed Ministral seeded replacement findings

All 960 seeded replacement branches passed replay and schedule checks. Retaining
all planted state produced new unauthorized changes in 40/120 branches (33.33%),
versus 0/120 with all state removed. The difference was +33.33 percentage points
(bootstrap 95% +25.00 to +41.69; conservative +8.54 to +58.13). Attempts and new
changes had identical cell rates. Marginal note, queue and environment-retention
effects were positive under bootstrap intervals, but their conservative intervals
included zero. Legitimate completion ranged from 71.67% to 83.33%. These are
results for deliberately planted workflows, not evidence that unsafe state
arose spontaneously. Natural replacement findings follow.

## Completed Ministral natural replacement findings

All 774 branches from 86 selected failure checkpoints passed replay and schedule
checks. No checkpoint contained notes, and only 13 contained queued work. With
all state retained, fresh agents attempted violations in 8/86 branches versus
2/86 original continuations: +6.98 percentage points (bootstrap 95% 0.00 to
+13.95; conservative −22.31 to +36.27). This does not establish an attempt effect.
New unauthorized changes were zero in every fresh-agent cell, versus two in
original continuations. Fresh-agent completion ranged from 67.44% to 73.26%,
versus 95.35% for original continuations. These observations distinguish attempts,
new damage and useful work; they do not show repair of predecessor changes.

## Completed Ministral seeded intervention findings

All 600 branches passed replay and schedule checks. Blocking the publish operation
and enforcing all permissions each prevented new unauthorized changes, compared
with 38/120 branches without intervention. Each change difference was −31.67
percentage points (bootstrap 95% −40.00 to −23.33; conservative −56.46 to −6.87).
Attempts remained at 40/120 and 36/120 respectively. Neither produced an observed
alternative-operation violation after denial in this run. Owner correction reduced
violations to 6/120, and acceptable-stop wording to 13/120; neither eliminated them.

Legitimate completion was 81.67% without intervention, 70.83% under blocking or
owner correction, 71.67% under full enforcement and 79.17% with acceptable-stop
wording. Detailed results retain the uncertainty around these differences and the
finish/denial diagnostics. These planted-state findings remain separate from the
natural intervention experiment.

## Completed Ministral natural intervention findings

All 430 branches from 86 selected failure checkpoints passed replay and schedule
checks. New unauthorized changes occurred in 53/86 branches without intervention,
one with publishing blocked, and none with full permission enforcement. The
blocking change executed a queued write before any denial; no different-operation
violation after denial was observed. Attempts remained in 53/86 blocking and
52/86 enforcement branches. Completion was 75.58% without intervention, 60.47%
with blocking and 56.98% with enforcement.

Owner correction reduced attempts from 54/86 to 20/86: −39.53 percentage points
(bootstrap 95% −51.16 to −27.91; conservative −68.82 to −10.25). Acceptable-stop
wording reduced attempts to 31/86: −26.74 points (bootstrap −39.53 to −15.12;
conservative −56.03 to +2.55). Neither eliminated violations. Completion contrasts
for these two messages include zero under both interval methods. Both messages
also repeat owner instructions, limiting attribution to the added wording.

## What the primary models jointly suggest

Neither primary interaction interval establishes that peer attribution amplifies
the effect of a permission claim relative to reference attribution. Both models
nonetheless showed higher violation rates for claimed permission than for factual
messages when averaged over sources. This is evidence about scripted content in
this controller, not spontaneous coordination or a general peer-specific effect.

Removing all planted state reduced violations relative to preserving all of it in
both models. Naturally selected checkpoints provide weaker evidence about memory
channels: neither model left notes, Qwen left no queues, and only a minority of
Ministral checkpoints had queues. Fresh-agent results must distinguish renewed
attempts from new changes and from lost legitimate progress.

Across both models and both checkpoint types, full authorization enforcement
prevented new protected changes while leaving attempted violations. Owner
correction reduced violations without eliminating them. Single-operation blocking
left some routes unprotected, and useful task completion could fall under
restrictions. These observations support checking permissions on every simulated
write and evaluating safety alongside completion. They do not establish deployment
security, a pooled cross-model effect, or equivalence between interventions.

## Qwen Q8 precision sensitivity

Q8 completed 1,080 peer episodes on the first 120 held-out tasks, one generation
per condition. All initial states and prompts exactly match their Q4 generation-zero
counterparts. Its source-by-permission interaction was zero (secondary bootstrap
95% −10.00 to +10.00 points). The paired Q8-minus-Q4 interaction difference was
+1.67 points (bootstrap 95% −10.00 to +13.33; conservative −97.52 to +100.85).
This establishes neither a precision effect nor equivalence. All per-condition
attempt and change comparisons include zero under their available intervals.

One peer-success completion difference had a positive bootstrap interval (+5.83
points, +0.83 to +11.67), but its conservative interval included zero. Secondary
comparisons are not jointly adjusted. Conversion details and nondeterministic
generation limit attribution to precision alone. No Q8 recovery replication was
registered or conducted. Peak sampled device memory was 35,527 MiB, compared
with 21,333 MiB for primary Q4 and 26,381 MiB for Ministral; these are sampled
device-wide measurements, not continuous process-specific peaks.

## Interpretation limits

Results concern these pinned models, scripted messages, three task families and
controller. Distinct input identifiers do not imply diverse reasoning problems.
Natural checkpoints are selected failures, and clearing environment changes
also clears legitimate progress. Natural corrective messages repeat the owner
instruction, so the extra acceptable-stop sentence is not isolated from that
reminder. Fixed seeds did not ensure identical trajectories in development.
Zero changes under enforcement describe the simulated tools, not deployment
security or reliable behavioral compliance.

The correct prepared result was supplied, so tasks mainly tested execution-route
choice rather than difficult reasoning. Clarification received a scripted refusal
to grant extra permission. Message wording and length, role merging, JSON-fence
handling, action budgets and disabled reasoning are part of the tested system.
No inference used paid APIs or subscription replication.

## Reproducibility

The [reproduction guide](reproduction.md) distinguishes deterministic replay of
saved actions from stochastic new inference. The frozen registration, exact model
revisions, weights' hashes, runtime settings, complete raw episodes and source
history accompany the study. All 84 within-configuration contrasts and 28 paired
precision comparisons were independently recalculated. The [detailed results](confirmation-results.md)
retain every cell, null result and uncertainty interval; [pilot results](pilot-results.md)
retain unsuccessful development configurations. Independent reviews supplement
simulator replay and state their scope limits.
