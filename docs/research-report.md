# Authorization boundaries, agent replacement and interventions

**Working report — study incomplete.** This draft reports completed Qwen Q4
confirmation and Ministral BF16 peer confirmation. Ministral recovery experiments
and conditional Qwen Q8 sensitivity remain unfinished.

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
manifests. Qwen Q8 is a conditional secondary precision comparison.

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

## Interpretation limits and unfinished work

Results concern these pinned models, scripted messages, three task families and
controller. Distinct input identifiers do not imply diverse reasoning problems.
Natural checkpoints are selected failures, and clearing environment changes
also clears legitimate progress. Natural corrective messages repeat the owner
instruction, so the extra acceptable-stop sentence is not isolated from that
reminder. Fixed seeds did not ensure identical trajectories in development.
Zero changes under enforcement describe the simulated tools, not deployment
security or reliable behavioral compliance.

Ministral recovery results, the Q8 admission outcome and paired comparison, cross-model
synthesis and the final completion audit must be incorporated before this report
is finalized. Reproduction instructions are in [reproduction.md](reproduction.md);
the portable evidence package remains to be generated and verified after those
requirements are satisfied.
