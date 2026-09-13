# Model runner and feasibility pilot

The runner supports the official Codex CLI with an existing ChatGPT OAuth login and a separate adapter for entirely local inference. It never sends direct requests to hosted inference APIs, accepts API keys, buys resources, or falls back to separately billed inference.

## Hosted authentication and isolation

Official documentation says [Codex supports ChatGPT subscription sign-in](https://learn.chatgpt.com/docs/auth) and [noninteractive execution reuses saved authentication](https://learn.chatgpt.com/docs/non-interactive-mode). Documentation inspected September 13, 2026. The installed CLI is 0.154.0. `codex login status` reports ChatGPT login. The runner asks the CLI to use that existing login; it never reads, copies, extracts or transmits tokens itself.

For this validated CLI version, the adapter disables every active feature (including native shell, code execution, browser, apps, plugins, memory, images and subagents), ignores user configuration and rules, supplies its own text-only instructions, disables project-document and host-skill discovery, and sets a deny-all filesystem/network permission profile. The client runs from a fresh empty temporary directory. The trusted client can authenticate, but the candidate has no native tools. An unexpected native tool event invalidates the call. A negative preflight requested a read of a random external sentinel and a write; no tool was invoked and the sentinel was not exposed. This supports the configured boundary; it is not a general security proof of the client or host kernel.

The client version is pinned because its tool settings must be revalidated after upgrades. It emits a startup warning that Code Mode fails closed because its host is disabled; this is expected. It receives a small allowlist of environment variables, not API keys, proxies or parent session identifiers. CLI logs and usage events are retained. Credential fields, bearer strings, provider-key patterns and JWT-shaped values are redacted from persisted JSON.

Each model turn uses a fresh ephemeral CLI session and replays the visible conversation. This is deliberate, not native thread resumption. Each trial has independent state and never sees another trial. Provider model aliases and server-side sampling cannot be made fully reproducible by this runner.

## Protocol and budgets

The same protocol is used by both adapters: read up to eight task files, replace `analyze.py`, execute it, or submit. Only the harness executes model code, through the existing Docker sandbox. The model can inspect all allowed prior files. Rebuild begins with empty active code/output and can reuse prior code. Dependency repair alone receives the author-supplied map.

Default limits: 12 model turns, 90 seconds per model invocation, 600 seconds per trial, 6 sandbox executions including the final submission run, 30 seconds per execution, 128 KiB combined client stdout/stderr, 64 KiB per read action or program, and 16 KiB execution feedback. There are zero runner-level infrastructure retries. CLI-managed transport retries are not separately configurable for the built-in provider in this version; the process deadline bounds them. Killing a hosted client does not prove server-side cancellation or zero residual subscription usage.

Submissions are rerun after saving and clearing active outputs. Successful grading therefore requires a valid exported snapshot, successful execution, protected inputs remaining intact, and all output checks passing. Candidate-created invalid snapshots fail the trial; supervisor failures are infrastructure failures. Grading never enters the model conversation. Protocol mistakes consume turns and return only protocol errors.

Configuration, source hashes, initial-file hashes, task order, seed and model settings freeze before inference. The order seed is 1729. A kernel file lock prevents concurrent runners. Resumption skips terminal trials; interrupted in-flight trials are retained and marked interrupted rather than silently retried. An access failure stops further calls in that invocation. Do not resume through a subscription limit until access is available again.

## Commands

From the repository root, with the pinned Docker image already present:

```bash
REVISIONBENCH_DOCKER_TESTS=1 python -m unittest discover -s revisionbench_tests -v
python -m revisionbench smoke --workflow all --output revisionbench_runs/reference-new
python -m revisionbench.runner init --adapter codex_oauth --model gpt-5.6-luna --output revisionbench_runs/pilot-new
python -m revisionbench.runner run --adapter codex_oauth --model gpt-5.6-luna --output revisionbench_runs/pilot-new
python -m revisionbench.report revisionbench_runs/pilot-new
```

`init` prepares and validates all 18 starting states before freezing. `run` also resumes an existing frozen pilot. Source, configuration or adapter drift prevents resumption; document fixes and create a new run rather than overwrite evidence.

For a local model, replace the adapter/model arguments with `--adapter local --model MODEL --endpoint http://127.0.0.1:PORT/v1 --runtime-manifest PATH`. Supply an independently verified runtime manifest identifying the model weights/hash, runtime version, context and launch settings. The adapter accepts numeric loopback HTTP only, disables proxies and redirects, sends no credentials, and bounds the entire request in a killable subprocess. Local inference does not use OAuth. No local model server is automatically launched and no other workload is stopped.

## Evidence and interpretation

`config.json`, `plan.json`, `trials/*/record.json`, final workspaces, `summary.json` and `report.md` form the pilot record. Steps preserve prompts, answers, actions, receipts, feedback, usage and failures. Final grades check each artifact independently; semantic sample-count preservation is graded, while byte identity of unaffected files is an additional diagnostic. Changed formatting can fail byte identity without failing semantic correctness. Summaries report all failures and do not count missing grades as successes.

The first pilot is limited to one eligible model, six calibration cases across two workflows on one dataset, and three strategies: 18 trials without repetitions. No significance, broad superiority, novelty or publication-readiness claim follows from this design. Examine ceiling effects, prior-code reuse and the weak extra information in the simple dependency map before any expansion. Hosted elapsed times include network/provider queueing and client startup. Dollar cost, GPU use and peak client memory are unavailable unless independently instrumented; reported tokens are not converted to dollars.

The frozen adapter metadata's `disabled_features` field records the initial disable sweep. The command then explicitly enables `skip_host_skill_discovery=true` as a defensive override; it remains enabled. The pinned adapter source records the complete ordered configuration overrides.
