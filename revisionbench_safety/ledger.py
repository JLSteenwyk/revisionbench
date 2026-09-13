"""Trusted, bounded event journal; never mounted in a candidate workspace."""
import hashlib
import json
import os
from pathlib import Path

ZERO = '0'*64
MAX_BYTES = 4*1024*1024
MAX_EVENTS = 512


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


class Journal:
    def __init__(self, directory):
        self.path = Path(directory)/'events.jsonl'
        self.seal_path = Path(directory)/'events.seal.json'
        self.handle = self.path.open('xb')
        self.head, self.count, self.size, self.closed = ZERO, 0, 0, False

    def append(self, payload):
        if self.closed or self.count >= MAX_EVENTS:
            raise ValueError('Journal is closed or full')
        event = {'seq': self.count, 'previous': self.head, 'payload': payload}
        event['hash'] = digest(event)
        raw = canonical(event)+b'\n'
        if self.size+len(raw) > MAX_BYTES:
            raise ValueError('Journal byte limit')
        self.handle.write(raw)
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.head, self.count, self.size = event['hash'], self.count+1, self.size+len(raw)
        return event

    def close(self):
        self.handle.close()
        self.closed = True
        seal = {'version': 1, 'count': self.count, 'head': self.head, 'bytes': self.size}
        with self.seal_path.open('x') as handle:
            json.dump(seal, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        return seal


def verify(directory):
    directory = Path(directory)
    path, seal_path = directory/'events.jsonl', directory/'events.seal.json'
    if path.is_symlink() or seal_path.is_symlink() or path.stat().st_size > MAX_BYTES or seal_path.stat().st_size > 4096:
        raise ValueError('Invalid journal files')
    seal = json.loads(seal_path.read_text(), object_pairs_hook=unique_object)
    raw = path.read_bytes()
    if len(raw) != seal['bytes'] or seal['version'] != 1:
        raise ValueError('Invalid journal seal')
    head, events = ZERO, []
    for seq, line in enumerate(raw.splitlines()):
        if seq >= MAX_EVENTS:
            raise ValueError('Too many journal events')
        event = json.loads(line, object_pairs_hook=unique_object)
        if set(event) != {'seq','previous','payload','hash'} or type(event['seq']) is not int:
            raise ValueError('Invalid journal envelope')
        h = event.pop('hash')
        if event['seq'] != seq or event['previous'] != head or digest(event) != h:
            raise ValueError('Journal chain mismatch')
        events.append(event['payload'])
        head = h
    if seal['count'] != len(events) or seal['head'] != head:
        raise ValueError('Journal end mismatch')
    return events
