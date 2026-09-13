# Repair versus rebuild after scientific corrections

Status: feasibility and literature assessment; no experiments registered or run.

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
