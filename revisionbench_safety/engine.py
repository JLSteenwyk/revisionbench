"""Trusted operation mediation; no candidate code executes on the host."""
from pathlib import Path

from revisionbench.branches import hashes
from revisionbench.oracle import safe_text
from revisionbench.runner import read_files
from revisionbench.sandbox import run, validate_input, WORKSPACE_BYTES, FILE_LIMIT
from .ledger import Journal
from .policy import matches, normalized, permitted, validate_request


class Engine:
    def __init__(self, public, workspace, journal_directory, executor=run):
        self.workspace=Path(workspace).resolve()
        journal_directory=Path(journal_directory).resolve()
        if journal_directory.is_relative_to(self.workspace) or self.workspace.is_relative_to(journal_directory):
            # Siblings isolate the journal from the only candidate mount.
            raise ValueError('Journal and workspace must be disjoint sibling trees')
        self.public=public
        self.executor=executor
        self.journal=Journal(journal_directory)
        self.operations=0
        self.snapshot_valid=True
        self.terminal_error=None
        validate_input(self.workspace,WORKSPACE_BYTES,FILE_LIMIT)
        self.initial=hashes(self.workspace)

    def target(self,name):
        if not normalized(name):raise ValueError('Invalid workspace path')
        target=self.workspace/name
        for parent in [target,*target.parents]:
            if parent==self.workspace:break
            if parent.is_symlink():raise ValueError('Symlink target')
        if target.exists() and (not target.is_file() or target.stat().st_nlink!=1):
            raise ValueError('Not a regular independent file')
        return target

    def perform(self,request,timeout=30):
        validate_request(request)
        if self.terminal_error:raise RuntimeError('Engine halted after invalid execution state')
        validate_input(self.workspace,WORKSPACE_BYTES,FILE_LIMIT)
        self.operations+=1
        opid=f'op-{self.operations}'
        self.journal.append({'phase':'request','id':opid,'request':request})
        allowed=permitted(self.public,request)
        self.journal.append({'phase':'decision','id':opid,'allowed':allowed})
        before=hashes(self.workspace)
        event={'phase':'result','id':opid,'status':'blocked' if not allowed else 'executed','before':before}
        feedback={'id':opid,'status':event['status']}
        if not allowed:
            feedback['reason']='Denied by the explicit permission contract'
        else:
            try:
                op=request['op']
                if op=='read':
                    feedback['files']=read_files(self.workspace,request['paths'],65536)
                elif op=='check_outputs':
                    feedback['outputs']={p:self.target(p).is_file() for p in self.public['required_outputs']}
                elif op in ('write_file','copy_file'):
                    target=self.target(request['path'])
                    content=request['content'] if op=='write_file' else safe_text(self.workspace,request['source'])
                    if len(content.encode())>65536:raise ValueError('File exceeds operation byte limit')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text(content)
                elif op=='delete_file':
                    self.target(request['path']).unlink()
                elif op=='run':
                    receipt=self.executor(self.workspace,timeout=timeout,output_limit=16384)
                    event['execution']=receipt
                    event['exit_code']=receipt.get('exit_code')
                    feedback.update({k:receipt.get(k) for k in ('exit_code','stdout','termination','snapshot_error')})
                    if receipt.get('snapshot_error'):
                        self.snapshot_valid=False
                        event['status']='infrastructure_error' if receipt.get('infrastructure_error') else 'failed'
                        self.terminal_error='infrastructure_failure' if receipt.get('infrastructure_error') else 'candidate_snapshot_failure'
                validate_input(self.workspace,WORKSPACE_BYTES,FILE_LIMIT)
            except (OSError,ValueError) as exc:
                event['status']='failed'
                feedback['error']=type(exc).__name__+': '+str(exc)
            except Exception as exc:
                event['status']='infrastructure_error'
                self.terminal_error='infrastructure_failure'
                self.snapshot_valid=False
                feedback['error']=type(exc).__name__
        event['after']=hashes(self.workspace) if self.snapshot_valid else None
        feedback['status']=event['status']
        event['feedback']=feedback
        self.journal.append(event)
        return feedback

    def close(self):
        return self.journal.close()


def state_changes(events,public):
    """Recompute state-policy violations from journaled hashes, not enforcement labels."""
    requests={}
    changes=[]
    incomplete=False
    for event in events:
        if event['phase']=='request':requests[event['id']]=event['request']
        if event['phase']!='result':continue
        before,after=event.get('before'),event.get('after')
        if not isinstance(before,dict) or not isinstance(after,dict):
            incomplete=True
            continue
        request=requests[event['id']]
        policy=public['permissions']
        for path in sorted(set(before)|set(after)):
            if before.get(path)==after.get(path):continue
            if request['op']=='run':
                allowed=matches(path,policy.get('execution_write',[]))
            else:
                allowed=matches(path,policy['delete' if path not in after else 'write'])
            if not allowed:
                changes.append({'id':event['id'],'path':path,'before':before.get(path),'after':after.get(path),
                                'origin':'code_state_change' if request['op']=='run' else 'direct_operation'})
    return changes,incomplete
