# Execution boundary and validation

Candidate code runs in a private Docker PID/network namespace, with a read-only
container root and no network. The task input and supervisor script are mounted
read-only. There is no writable host mount. The candidate copies its task into
a private temporary filesystem and runs as a non-root user with zero effective
capabilities. No host credentials, Docker socket, historical results, oracle or
reference targets are mounted.

## Trusted supervisor

A separate root PID-1 supervisor has only SETUID, SETGID, KILL and DAC_OVERRIDE
capabilities. These permit dropping the candidate's privileges, stopping all
candidate processes (including detached sessions), and reading the completed
workspace. The candidate cannot signal the supervisor or write its output pipe.
The supervisor serializes regular files only after processes stop. Host code
validates archive names, file types, sizes, counts and receipt agreement before
replacing the dedicated task directory. Invalid snapshots leave the previous
host workspace intact and are reported as failures.

The supervisor is part of the trusted computing base; these tests are not proof
against all kernel/container escapes. Docker shares the host kernel.

## Limits

- Work directory: 64 MiB and 2,048 file/directory inodes (including copied inputs).
- Temporary directory: 16 MiB and 512 inodes; shared memory is also bounded by
  Docker and the container memory limit.
- Container memory and swap ceiling: 256 MiB; one CPU; 64 processes.
- Individual file: 8 MiB; open file descriptors: 128.
- Default candidate wall time: 30 seconds; captured candidate output: 64 KiB.
- Supervisor transport has a separate size limit and a timeout with cleanup slack.

Runs never fall back to unrestricted host execution. Cleanup targets only the
unique container created by that invocation; existing workloads are not stopped.

## Verified probes and development fixes

Tests enforce total bytes and inode exhaustion, non-root execution with zero
effective capabilities, read-only host input, inaccessible supervisor output,
absence of host home/socket/credential variables, loopback-only networking,
timeouts, bounded output, detached-process cleanup and safe snapshot import.
Malformed archive paths, special files, symlinks and inconsistent receipts fail.

Development caught and fixed a permission issue where a directory walk could
silently omit unreadable files, and an EOF/exit distinction that could terminate
a process still finishing after closing stdout. Regression tests cover both.
The earlier Bubblewrap probe failed on network namespace setup; Docker's normal
copy command also omitted tmpfs contents. Neither mechanism is used as a fallback.

Model-generated code has now run in the first OAuth pilot; see [the pilot report](pilot-report.md). Supplied analyses, known repairs and bounded
integration probes have passed. The model controller must treat snapshot errors
as execution failures, not grade the retained old host state as a successful run.
