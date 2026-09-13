# Feasibility design questions

This is a planning document, not a preregistration.

## Primary candidate comparison

Complete correction success under repair versus rebuild at specified resource
budgets. Also report resource use required to achieve comparable correctness.
Define rebuilding operationally: what prior code, reports and metadata are visible
must be explicit, since unequal information can confound the comparison.

## Candidate moderators

- Number of affected outputs and depth of their dependencies.
- Corrections that do versus do not change a prespecified substantive conclusion.
- Project structure and retained intermediate caches.

Avoid treating duplicated files as independent task samples. Hold the corrected
input, requested outputs and evaluation targets fixed within matched comparisons.

## Required controls

- Unchanged-input control to measure gratuitous damage during revision.
- Independent reference recomputation from corrected inputs.
- Deterministic clean rerun baseline where the existing pipeline permits it.
- Dependency-assisted repair, distinguishing an oracle map supplied by us from a
  map inferred by the agent. Charge map-construction costs in practical comparisons.
- Baseline evidence that the initial project is correct. Report separately any
  later experiments using agent-authored projects selected for initial success.

## Evaluation boundaries

Use numerical tolerances defined per output, inspect plot data and labels, and
evaluate explicitly specified claims. Do not describe this as automatic assessment
of unrestricted scientific validity. Reference evaluators must be outside the
agent's writable workspace. Agent-generated code must run in a restricted process
environment without credentials, network access or access to historical study
artifacts; the prior in-memory simulator is not sufficient isolation for this work.

## Before confirmation

Resolve related-work overlap, model competence, sandboxing, oracle correctness,
task diversity, available compute and matched budget definitions. Preserve pilot
failures. Freeze hypotheses, sample allocation, task-level analysis and stopping
rules before held-out evaluation. Null effects remain reportable; do not select
tasks or expand the study according to preferred outcomes.
