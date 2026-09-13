"""Package a terminal pilot after auditing, without invoking any model."""
import argparse
import fcntl
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from revisionbench_safety.audit import audit
from revisionbench_safety.report import summarize


def package(root,output):
    with (root/'runner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=audit(root)
        if any(t['status'] in ('running','unstarted') for t in result['incomplete_trials']):
            raise ValueError('Pilot has live or unstarted trials')
        summary=summarize(root)
        (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
        files=[p for p in sorted(root.rglob('*')) if p.is_file() and p.name!='runner.lock']
        suspect=re.compile(rb'(?i)(?:Bearer\s+[A-Za-z0-9._~-]{20,}|sk-[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,})')
        manifest={}
        for path in files:
            if path.is_symlink():raise ValueError('Symlink in evidence')
            data=path.read_bytes()
            if suspect.search(data):raise ValueError('Potential credential pattern in '+str(path.relative_to(root)))
            manifest[str(path.relative_to(root))]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
        output.mkdir(parents=True,exist_ok=False)
        archive=output/'pilot-records.tar.gz'
        with archive.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w') as tar:
            for path in files:
                data=path.read_bytes();info=tarfile.TarInfo(str(Path(root.name)/path.relative_to(root)))
                info.size=len(data);info.mode=0o644;info.mtime=0
                tar.addfile(info,io.BytesIO(data))
        for name in ('config.json','config.sha256','audit.json','summary.json','report.md','scorer-validation.json','validation-tests.txt'):
            (output/name).write_bytes((root/name).read_bytes())
        metadata={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'archive_bytes':archive.stat().st_size,'files':manifest,
                  'credential_scan':'No bearer, common API-key, or JWT patterns detected. Candidate workspaces exclude credentials by construction; this scan is not a universal secret detector.',
                  'all_planned_trials_verified':result['all_planned_trials_verified']}
        (output/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
        return {'archive_bytes':metadata['archive_bytes'],'files':len(files),'statuses':summary['statuses']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();print(json.dumps(package(args.root,args.output),indent=2))
