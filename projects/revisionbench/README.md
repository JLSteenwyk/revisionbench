# RevisionBench: repair versus rebuild after scientific corrections

Status: executable development fixture validated; literature and broader feasibility assessment ongoing. No model trials or confirmatory experiments registered or run.

Question: when an upstream fact or dataset changes, when is repairing an existing
analysis more reliable and less costly than rebuilding it from corrected inputs?

Compare ordinary repair, rebuilding, and repair with an explicit dependency map.
Evaluate complete downstream correctness, preservation of unaffected outputs,
runtime and inference cost. A running program or a confident completion message
does not establish a successful correction.

This project is separate from the completed authorization-boundary study at the
repository root. Its existing registration and evidence remain historical records.

## First decision: is the study worth scaling?

1. Inspect the methods and available artifacts of the closest research, especially
   EviGraph and scientific-agent benchmarks. Document exact overlap before claiming
   a contribution.
2. Build a small set of independently executable workflows with known outputs and
   controlled corrections. Prioritize distinct analysis structures over repeated
   cosmetic variants.
3. Establish baseline task competence of locally runnable models before comparing
   correction strategies. Measure feasibility rather than assume it from the prior
   study's simpler tasks.
4. Validate an independent evaluation oracle for affected and unaffected outputs.
5. Decide whether to proceed based on novelty, construct validity and feasibility,
   not whether the pilot produces a preferred direction or significance.

See [design questions](design.md). No paid inference, external publication or new
resource purchase is part of this initial local feasibility phase.

## Starting literature

- EviGraph: https://arxiv.org/abs/2608.04738
- ScienceAgentBench: https://arxiv.org/abs/2410.05080
- EarthVerse: https://arxiv.org/abs/2608.23525

These are relevant precedents, not evidence that our proposed comparison is novel.

## Implemented development slice

The root `revisionbench` package prepares a pinned public-data analysis, applies
corrections/controls across grouped summaries and OLS, executes known baselines in Docker, and grades five
output artifacts plus input integrity with an independent numerical oracle.
Eighteen unit/integration tests pass, including stale figures, wrong claims, damage
to unaffected counts, forbidden output file types, network/host isolation, timeouts
and output limits. Evidence and commands are linked in the root README.

Next: resolve the closest-work comparison, add different workflow structures,
connect the model controller to the bounded execution layer, and define matched
inference/tool budgets before a small model pilot. Simply rerunning the supplied analysis
already solves the data-only case; this baseline must remain in the study.

Storage and inode limits are now implemented and validated. Eighteen matched
strategy workspaces can be prepared reproducibly, with identical prior information
and explicit contracts. These are calibration fixtures on one dataset. Model
inference remains pending; the most recent GPU inspection found other workloads,
which were left alone.
