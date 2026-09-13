import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from revisionbench.sandbox import restore_snapshot


def payload(name, size=1, kind=tarfile.REGTYPE, count=1):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        data = json.dumps({'snapshot_error': None, 'files': count, 'workspace_bytes': size}).encode()
        receipt = tarfile.TarInfo('receipt.json')
        receipt.size = len(data)
        archive.addfile(receipt, io.BytesIO(data))
        member = tarfile.TarInfo(name)
        member.type = kind
        member.size = size if kind == tarfile.REGTYPE else 0
        archive.addfile(member, io.BytesIO(b'x'*size))
    return buffer.getvalue()


class SnapshotValidationTests(unittest.TestCase):
    def test_invalid_members_do_not_modify_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'task'
            root.mkdir()
            (root/'original').write_text('safe')
            for name, kind in [('workspace/../outside', tarfile.REGTYPE),
                               ('/workspace/absolute', tarfile.REGTYPE),
                               ('workspace/link', tarfile.SYMTYPE)]:
                with self.assertRaises(ValueError):
                    restore_snapshot(payload(name, kind=kind), root, 100, 10)
                self.assertEqual((root/'original').read_text(), 'safe')

    def test_budget_and_receipt_disagreement_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'task'
            root.mkdir()
            with self.assertRaises(ValueError):
                restore_snapshot(payload('workspace/file', size=100), root, 10, 10)
            with self.assertRaises(ValueError):
                restore_snapshot(payload('workspace/file', count=2), root, 100, 10)

    def test_valid_snapshot_preserves_deletions_and_new_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'task'
            root.mkdir()
            (root/'old').write_text('old')
            restore_snapshot(payload('workspace/new'), root, 100, 10)
            self.assertFalse((root/'old').exists())
            self.assertEqual((root/'new').read_bytes(), b'x')
