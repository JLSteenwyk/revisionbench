# Execution scope and remaining work

Candidate projects execute with a pinned official Python Docker image, no network,
a read-only container root, a non-root user, dropped capabilities and
no-new-privileges. Only a dedicated task directory is mounted read/write. No host
credentials, Docker socket, historical results, oracle or reference targets are
mounted. Runs receive CPU/memory/process/per-file limits, a wall-time deadline and
a captured-output limit. Cleanup targets only a unique container created by that
invocation; no existing workloads are stopped.

The current integration probes pass: non-root execution, absence of the host home
and Docker socket, absence of credential variables, only loopback networking,
timeout termination and output truncation. Bubblewrap's initial network namespace
probe failed with an operation-not-permitted error; there is no fallback to
unrestricted host execution. Docker probes and the fixture run succeeded.

## Limits before autonomous execution

A per-file size limit does not bound total files or total workspace disk use.
An aggregate storage/inode quota must be implemented and tested before broad
autonomous model-generated execution. This prototype has run only the supplied
analysis, a known repair and bounded integration probes. Docker shares the host
kernel and these tests do not constitute a general sandbox escape audit.

The oracle rejects symlinks, special files and oversized output files, and never
executes candidate scripts. Candidate processes must be stopped before grading.
The SVG check validates declared bar data/title, not arbitrary rendering or visual
aesthetics. Future plot formats or unrestricted narrative need explicit scoring
design rather than relying on this fixed-contract evaluator.
