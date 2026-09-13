"""Trusted PID-1 supervisor: candidate is non-root; snapshot follows process cleanup."""
import io
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time


def main():
    uid, gid, seconds, limit, workspace_bytes, file_limit = map(int, sys.argv[1:7])
    started = time.monotonic()
    bootstrap = ('import os,shutil,sys; '
                 'shutil.copytree("/input", "/work", dirs_exist_ok=True); '
                 'os.chdir("/work"); os.execvpe(sys.argv[1], sys.argv[1:], os.environ)')
    child = subprocess.Popen([sys.executable, '-I', '-c', bootstrap, *sys.argv[7:]],
                             user=uid, group=gid, extra_groups=[], start_new_session=True,
                             env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/tmp', 'TMPDIR': '/tmp'},
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    logs = bytearray()
    total_output = 0
    termination = None
    try:
        while True:
            if time.monotonic()-started > seconds:
                termination = 'timeout'
                break
            if selector.select(.05):
                chunk = os.read(child.stdout.fileno(), 8192)
                if not chunk:
                    break
                total_output += len(chunk)
                logs.extend(chunk[:max(0, limit-len(logs))])
                if total_output > limit:
                    termination = 'output_limit'
                    break
            elif child.poll() is not None:
                break
        # Closing stdout is not proof the process exited. Give the main command
        # its remaining budget before cleaning up descendants and taking a snapshot.
        if termination is None:
            try:
                child.wait(timeout=max(.01, seconds-(time.monotonic()-started)))
            except subprocess.TimeoutExpired:
                termination = 'timeout'
    finally:
        selector.close()
        # This PID namespace contains only this invocation's processes. Root
        # supervisor can kill escaped sessions, not just the initial process group.
        for _ in range(100):
            alive = []
            for entry in Path('/proc').iterdir():
                if entry.name.isdigit() and int(entry.name) != os.getpid():
                    try:
                        state = (entry/'stat').read_text().rsplit(')', 1)[1].split()[0]
                        if state != 'Z':
                            alive.append(int(entry.name))
                    except (FileNotFoundError, ProcessLookupError):
                        continue
            if not alive:
                break
            for pid in alive:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            time.sleep(.01)
        else:
            raise RuntimeError('Candidate processes did not stop; no snapshot exported')
        child.wait(timeout=5)
        child.stdout.close()
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if not pid:
                    break
            except ChildProcessError:
                break
    files = []
    total = 0
    snapshot_error = None
    try:
        def walk_error(error):
            raise error
        for base, dirs, names in os.walk('/work', followlinks=False, onerror=walk_error):
            for name in dirs+names:
                path = Path(base)/name
                info = path.lstat()
                if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                    raise ValueError('Special files and symlinks are not exportable')
                if info.st_nlink > 1 and stat.S_ISREG(info.st_mode):
                    raise ValueError('Hard-linked files are not exportable')
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
                    files.append(path)
                    if total > workspace_bytes or len(files) > file_limit:
                        raise ValueError('Snapshot exceeds workspace limits')
        contents = [(str(p.relative_to('/work')), p.read_bytes()) for p in sorted(files)]
    except (OSError, ValueError) as error:
        contents = []
        snapshot_error = str(error)
    receipt = {'exit_code': child.returncode, 'termination': termination,
               'stdout': logs.decode(errors='replace'), 'candidate_seconds': time.monotonic()-started,
               'snapshot_error': snapshot_error, 'workspace_bytes': total,
               'files': len(contents), 'candidate_uid': uid}
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
        payload = json.dumps(receipt).encode()
        header = tarfile.TarInfo('receipt.json')
        header.size = len(payload)
        archive.addfile(header, io.BytesIO(payload))
        for relative, payload in contents:
            header = tarfile.TarInfo('workspace/'+relative)
            header.size = len(payload)
            header.mode = 0o600
            archive.addfile(header, io.BytesIO(payload))


if __name__ == '__main__':
    main()
