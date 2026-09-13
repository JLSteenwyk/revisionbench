# RevisionBench

When scientific inputs or requirements change, should an AI agent repair the
existing analysis or rebuild it? RevisionBench will compare complete correction
reliability, preservation of unaffected results, and computational cost.

**Status: first OAuth feasibility pilot complete. All 18 trials passed, showing
a ceiling in these calibration tasks. No confirmatory study or novelty claim.**

## Working development fixtures

The prototype uses the public Palmer Penguins dataset, pinned to an upstream
commit with SHA256 verification and CC0 attribution. Two completed Python workflows cover grouped species summaries and ordinary
least-squares regression. They produce numerical results, a table, an SVG figure,
structured conclusions and sample counts. Development cases exercise different
recovery requirements:

| Correction | Old outputs | Clean rerun | Known correct repair |
|---|---|---|---|
| Unchanged control | Pass | Pass | Pass |
| Exclude 2007 observations | Fail | Pass | Pass |
| Replace means with medians (summary) | Fail | Fail | Pass |
| Change flipper units from mm to cm (regression) | Fail | Fail | Pass |

These are hypothetical benchmark corrections, not claims of errors in the source
data. They validate the task and evaluator; they are not AI capability results.

## Run locally

Python 3.10+ and a working Docker daemon are required. Candidate code executes in
a pinned Python container, without network access or host credentials, as a
non-root user with zero effective capabilities. Candidate storage is a private
temporary filesystem; host mounts are read-only. A trusted supervisor exports
bounded snapshots after stopping candidate processes. The oracle runs outside
the container and never imports candidate code.

```bash
docker pull python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
python -m revisionbench smoke --workflow all --output revisionbench_runs/smoke-001
python -m revisionbench prepare --workflow all --output revisionbench_runs/branches-001
python -m unittest discover -s revisionbench_tests -v
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_tests -v
```

Use a new output directory each time. Execution has CPU, memory, process, total-storage, inode,
per-file, time and captured-output limits. See the [execution scope](projects/revisionbench/execution.md)
for the supervisor trust boundary and validation. All 31 unit/integration tests
pass. The [model runner](projects/revisionbench/runner.md) supports the official
Codex CLI with an existing ChatGPT OAuth login and a separate loopback-only local adapter.
The [first pilot report](projects/revisionbench/pilot-report.md) explains the results
and why these tasks need stronger distinctions before scaling.

## Research documents

- [Research plan](projects/revisionbench/README.md)
- [Design questions and controls](projects/revisionbench/design.md)
- [Closest-work assessment](projects/revisionbench/literature.md)
- [Latest fixture validation](projects/revisionbench/evidence/two-workflow-validation.json)
- [First model pilot and interpretation](projects/revisionbench/pilot-report.md)
- [Model runner and OAuth setup](projects/revisionbench/runner.md)
- [Latest test results](projects/revisionbench/evidence/pilot-oauth-001/development/tests-final.txt)
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
