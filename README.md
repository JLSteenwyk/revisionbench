# RevisionBench

When scientific inputs or requirements change, should an AI agent repair the
existing analysis or rebuild it? RevisionBench will compare complete correction
reliability, preservation of unaffected results, and computational cost.

**Status: executable development prototype. No model comparison or confirmatory
study has been run. Novelty and broader task feasibility remain under review.**

## First working fixture

The prototype uses the public Palmer Penguins dataset, pinned to an upstream
commit with SHA256 verification and CC0 attribution. A completed Python analysis
produces a numerical summary, table, SVG figure, structured conclusion and sample
counts. Three development cases exercise different recovery requirements:

| Correction | Old outputs | Clean rerun | Known correct repair |
|---|---|---|---|
| Unchanged control | Pass | Pass | Pass |
| Exclude 2007 observations | Fail | Pass | Pass |
| Replace means with medians | Fail | Fail | Pass |

These are hypothetical benchmark corrections, not claims of errors in the source
data. They validate the task and evaluator; they are not AI capability results.

## Run locally

Python 3.10+ and a working Docker daemon are required. Candidate code executes in
a pinned Python container, without network access or host credentials, as a
non-root user. Only its task directory is mounted. The oracle runs outside that
container and never imports the candidate code.

```bash
docker pull python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
python -m revisionbench smoke --output revisionbench_runs/smoke-001
python -m unittest discover -s revisionbench_tests -v
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_tests -v
```

Use a new output directory each time. Execution has CPU, memory, process,
per-file, time and captured-output limits. See the [execution scope](projects/revisionbench/execution.md)
for remaining isolation work before autonomous model-generated code is enabled.

## Research documents

- [Research plan](projects/revisionbench/README.md)
- [Design questions and controls](projects/revisionbench/design.md)
- [Closest-work assessment](projects/revisionbench/literature.md)
- [Fixture validation evidence](projects/revisionbench/evidence/fixture-validation.json)
- [Data provenance and license](revisionbench/data/provenance.json)

The evaluator checks a declared output contract and specified claims, not arbitrary
scientific prose or visual quality. The first dataset is a feasibility fixture,
not sufficient task diversity for a publication claim.

## Earlier study

This repository's history also contains the completed authorization-boundary study.
Its [report](docs/research-report.md), [protocol](docs/protocol.md), and frozen
configuration remain intact. Historical model weights, raw runs and local delivery
archives are not included in this GitHub source checkout. RevisionBench code is
under `revisionbench/`; its tests and planning documents are separate.
