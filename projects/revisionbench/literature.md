# Closest-work assessment

Initial assessment: 2026-09-13. This is not an exhaustive novelty review.

## EviGraph is a direct precedent

[EviGraph v2](https://arxiv.org/html/2608.04738v2), sections 3.1–3.3,
Appendix C.4 and Appendix F.2, explicitly represents claim/evidence dependencies,
repairs affected downstream subgraphs, and uses checkpoints to prevent degradation.
Its reliability evaluation extracts manuscript claims and values using models,
then uses membership judgments and deterministic aggregation.

Consequently, neither dependency-guided repair nor preserving valid results can
be presented as our invention. A candidate distinction is an external correction
to an already validated executable analysis, with matched repair/rebuild strategies,
independently recomputed numerical targets, and correction cost reported alongside
complete downstream correctness. This distinction still requires checking the full
baselines, evaluation artifacts and other related work; it is not an established
priority claim.

## Scientific-agent benchmarks

[ScienceAgentBench](https://arxiv.org/abs/2410.05080) evaluates executable
scientific tasks drawn from published work.
[EarthVerse](https://arxiv.org/abs/2608.23525) is another relevant scientific-agent
benchmark to inspect for changing-evidence and revision coverage. Reusing validated
tasks may strengthen realism, but changed task requirements need their own
validation. No task from either benchmark has been incorporated yet.

## Current decision

Proceed only with inexpensive feasibility work. The Palmer Penguins fixture
establishes executable scoring and contrasts a rerun-sufficient data change with
a requirement change needing code modification. It does not by itself establish
a novel research question, realistic difficulty, or publication readiness.
