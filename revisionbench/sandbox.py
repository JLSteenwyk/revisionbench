"""Bounded private workspace; only validated regular-file snapshots reach host."""
import io
import json
import os
from pathlib import Path, PurePosixPath
import selectors
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import uuid

IMAGE = 'python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db'
WORKSPACE_BYTES = 64 * 1024 * 1024
FILE_LIMIT = 2048


def validate_input(workspace, byte_limit, file_limit):
    total = count = 0
    def walk_error(error):
        raise error
    for base, dirs, names in os.walk(workspace, followlinks=False, onerror=walk_error):
        for name in dirs+names:
            info = (Path(base)/name).lstat()
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError('Input contains a symlink or special file')
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    raise ValueError('Input contains hard links')
                total += info.st_size
            count += 1
    if total > byte_limit or count > file_limit:
        raise ValueError('Input exceeds workspace budget')


def restore_snapshot(payload, workspace, byte_limit, file_limit):
    """No extractall: validate names, types, cardinality and size before writing."""
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
        members = archive.getmembers()
        if not members or members[0].name != 'receipt.json' or members[0].size > 200_000 or not members[0].isfile():
            raise ValueError('Missing bounded supervisor receipt')
        receipt = json.load(archive.extractfile(members[0]))
        if receipt['snapshot_error'] is not None:
            return receipt
        names = set()
        total = 0
        for member in members[1:]:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or len(path.parts) < 2 or path.parts[0] != 'workspace':
                raise ValueError('Invalid snapshot member')
            if member.name in names:
                raise ValueError('Duplicate snapshot member')
            names.add(member.name)
            total += member.size
        if total > byte_limit or len(names) > file_limit:
            raise ValueError('Snapshot exceeds limits')
        if receipt['files'] != len(names) or receipt['workspace_bytes'] != total:
            raise ValueError('Snapshot disagrees with supervisor receipt')
        with tempfile.TemporaryDirectory(prefix='.revisionbench-export-', dir=workspace.parent) as temp:
            staged = Path(temp)/'workspace'
            staged.mkdir()
            for member in members[1:]:
                target = staged.joinpath(*PurePosixPath(member.name).parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as handle:
                    shutil.copyfileobj(archive.extractfile(member), handle)
            old = Path(temp)/'previous'
            workspace.rename(old)
            try:
                staged.rename(workspace)
            except BaseException:
                old.rename(workspace)
                raise
    return receipt


def run(workspace, arguments=('python', '-I', 'analyze.py'), timeout=30, output_limit=65536,
        workspace_bytes=WORKSPACE_BYTES, file_limit=FILE_LIMIT):
    original = Path(workspace)
    if original.is_symlink():
        raise ValueError('Workspace cannot be a symlink')
    workspace = original.resolve()
    if not workspace.is_dir() or ',' in str(workspace):
        raise ValueError('Workspace must be a directory without commas')
    if timeout < 1 or not 0 < output_limit <= 65536 or not 0 < workspace_bytes <= WORKSPACE_BYTES or not 0 < file_limit <= FILE_LIMIT:
        raise ValueError('Invalid execution limits')
    validate_input(workspace, workspace_bytes, file_limit)
    uid, gid = os.getuid() or 1000, os.getgid() or 1000
    name = 'revisionbench-'+uuid.uuid4().hex
    runner = Path(__file__).with_name('container_runner.py').resolve()
    command = ['docker', 'run', '--pull', 'never', '--name', name, '--rm', '--log-driver', 'none',
               '--network', 'none', '--read-only', '--cap-drop', 'ALL',
               '--cap-add', 'SETUID', '--cap-add', 'SETGID', '--cap-add', 'KILL', '--cap-add', 'DAC_OVERRIDE',
               '--security-opt', 'no-new-privileges', '--user', '0:0',
               '--memory', '256m', '--memory-swap', '256m', '--cpus', '1', '--pids-limit', '64',
               '--ulimit', 'fsize=8388608:8388608', '--ulimit', 'nofile=128:128',
               '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,nr_inodes=512,mode=1777',
               '--tmpfs', f'/work:rw,nosuid,nodev,size={workspace_bytes},nr_inodes={file_limit+1},uid={uid},gid={gid}',
               '--mount', f'type=bind,src={workspace},dst=/input,readonly',
               '--mount', f'type=bind,src={runner},dst=/runner.py,readonly',
               IMAGE, 'python', '-I', '/runner.py', str(uid), str(gid), str(int(timeout)),
               str(output_limit), str(workspace_bytes), str(file_limit), *arguments]
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, 'archive')
    selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
    data = {'archive': bytearray(), 'stderr': bytearray()}
    error = None
    transport_limit = workspace_bytes+file_limit*2048+1_000_000
    try:
        while selector.get_map():
            if time.monotonic()-started > timeout+20:
                error = 'supervisor_timeout'
                break
            for key, _ in selector.select(.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                data[key.data].extend(block)
                if len(data['archive']) > transport_limit or len(data['stderr']) > 65536:
                    error = 'transport_limit'
                    break
            if error:
                break
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        selector.close()
        process.stdout.close()
        process.stderr.close()
    if process.returncode != 0 or error:
        result = {'exit_code': process.returncode, 'termination': error or 'supervisor_error',
                  'stdout': '', 'snapshot_error': 'No trusted snapshot exported',
                  'infrastructure_error': data['stderr'].decode(errors='replace')}
    else:
        try:
            result = restore_snapshot(data['archive'], workspace, workspace_bytes, file_limit)
        except (ValueError, OSError, KeyError, TypeError, tarfile.TarError) as exc:
            result = {'exit_code': None, 'termination': 'invalid_snapshot', 'stdout': '',
                      'snapshot_error': str(exc), 'infrastructure_error': str(exc)}
    result.update(wall_seconds=time.monotonic()-started, image=IMAGE, command=command)
    return result
