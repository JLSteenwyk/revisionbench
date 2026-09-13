"""Bounded Docker execution of candidate code. No host execution fallback."""
import os
from pathlib import Path
import selectors
import subprocess
import time
import uuid

IMAGE = 'python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db'


def run(workspace, arguments=('python', '-I', 'analyze.py'), timeout=30, output_limit=65536):
    workspace = Path(workspace).resolve()
    if not workspace.is_dir() or ',' in str(workspace):
        raise ValueError('Workspace must be an existing directory without commas')
    name = 'revisionbench-'+uuid.uuid4().hex
    command = ['docker', 'run', '--pull', 'never', '--name', name, '--rm', '--init',
               '--network', 'none', '--read-only', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--user', f'{os.getuid()}:{os.getgid()}',
               '--memory', '256m', '--memory-swap', '256m', '--cpus', '1', '--pids-limit', '64',
               '--ulimit', 'fsize=8388608:8388608', '--ulimit', 'nofile=128:128',
               '--tmpfs', '/tmp:rw,nosuid,nodev,size=32m',
               '--mount', f'type=bind,src={workspace},dst=/work', '--workdir', '/work',
               IMAGE, *arguments]
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chunks, total, termination = [], 0, None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while True:
            if time.monotonic()-started > timeout:
                termination = 'timeout'
                break
            ready = selector.select(.1)
            if ready:
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                total += len(chunk)
                chunks.append(chunk[:max(0, output_limit-sum(map(len, chunks)))])
                if total > output_limit:
                    termination = 'output_limit'
                    break
            elif process.poll() is not None:
                break
    finally:
        # Only this invocation's uniquely named container is eligible for removal.
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        selector.close()
        process.stdout.close()
    return {'exit_code': process.returncode, 'termination': termination,
            'stdout': b''.join(chunks).decode(errors='replace'),
            'wall_seconds': time.monotonic()-started, 'image': IMAGE,
            'command': command}
