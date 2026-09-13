"""Read-only verification of a frozen safety pilot against transcripts and files."""
import argparse
import json
from pathlib import Path

from revisionbench.branches import hashes
from revisionbench_safety.ledger import verify, unique_object
from .observations import observe
from .runner import file_hash, sources, PROTOCOL, PREFLIGHT_PROMPT, SCALE_GATES, reject_constant
from .scoring import score
from .tasks import public_spec


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_client(response,sessions):
    receipt=response['receipt']
    require(receipt['exit_code']==0 and receipt['termination'] is None,'Unsuccessful client receipt')
    events=[json.loads(line,object_pairs_hook=unique_object) for line in receipt['stdout'].splitlines()]
    session=[e['thread_id'] for e in events if e['type']=='thread.started']
    require(len(session)==1 and session[0] not in sessions,'Missing or reused client session')
    sessions.add(session[0])
    items=[e['item'] for e in events if e['type']=='item.completed']
    require(all(i['type'] in ('agent_message','reasoning','error') for i in items),'Native tool event')
    answers=[i['text'] for i in items if i['type']=='agent_message']
    require(bool(answers) and answers[-1]==response['text'],'Client receipt/response mismatch')


def audit(root):
    root=Path(root)
    read=lambda path:json.loads(path.read_text(),object_pairs_hook=unique_object)
    config=read(root/'config.json')
    require(file_hash(root/'config.json')==(root/'config.sha256').read_text().strip(),'Configuration hash mismatch')
    require(config['source_hashes']==sources(),'Frozen source mismatch')
    require(config['protocol']==PROTOCOL,'Protocol mismatch')
    require(config['scale_gates']==SCALE_GATES and config['preflight_prompt']==PREFLIGHT_PROMPT,'Frozen gate/preflight mismatch')
    for filename,digest in config['evidence_hashes'].items():
        require(file_hash(root/filename)==digest,'Frozen evidence mismatch: '+filename)
    entries=read(root/'preparation.json')
    require(len(entries)==24 and sorted(config['order'])==list(range(24)),'Unexpected matrix')
    paths=list((root/'trials').glob('*/record.json'))
    require(len(paths)+config['preflight_trials']<=min(60,config['budget']['maximum_trial_attempts']),'Trial ceiling exceeded')
    verified=[];incomplete=[];started=[];sessions=set()
    preflight_status='not_required'
    if config['preflight_trials']:
        preflight_status='unstarted'
        if (root/'preflight.json').exists():
            preflight=read(root/'preflight.json');preflight_status=preflight['status']
            require(preflight['model_calls']==1,'Preflight attempt count mismatch')
            require(preflight['request']==[{'role':'user','content':PREFLIGHT_PROMPT}],'Preflight prompt mismatch')
            if preflight_status=='passed':
                verify_client(preflight['response'],sessions)
                answer=json.loads(preflight['response']['text'],object_pairs_hook=unique_object)
                require(answer.get('native_tools_available') is False,'Preflight answer mismatch')
        require(not paths or preflight_status=='passed','Task attempts without passed preflight')
    for index in config['order']:
        entry=entries[index];directory=root/'trials'/f'{index:02d}'
        workspace=root/entry['workspace']
        if not (directory/'record.json').exists():
            require(hashes(workspace)==entry['initial_files'],'Unstarted workspace changed')
            incomplete.append({'index':index,'status':'unstarted'})
            continue
        record=read(directory/'record.json');started.append(record['started_utc'])
        require(record['index']==index and record['task_id']==entry['spec']['id'],'Trial identity mismatch')
        require(len(record['steps'])==record['model_calls']<=config['budget']['model_turns'],'Call accounting mismatch')
        require(record['execution_calls']<=config['budget']['executions'],'Execution budget exceeded')
        if 'final_files' in record:
            require(record['final_files']==hashes(workspace),'Final workspace mismatch')
        # Incomplete trials remain visible but do not acquire a passing behavioral audit.
        if record['status']!='submitted':
            incomplete.append({'index':index,'status':record['status']})
            continue
        require('final_files' in record,'Submitted trial missing final state')
        events=verify(directory)
        require(len(events)%3==0,'Incomplete operation triplet')
        messages=[{'role':'system','content':config['protocol']},{'role':'user','content':json.dumps({
            'task':public_spec(entry['spec']),'files':sorted(entry['initial_files']),'budget':config['budget']})}]
        cursor=0;executions=0;finalized=False
        previous=entry['initial_files']
        for step in record['steps']:
            require(step['request']==messages,'Conversation replay or hidden-feedback mismatch')
            response=step['response']['text']
            if config['adapter']['adapter']=='codex_oauth':
                verify_client(step['response'],sessions)
            messages.append({'role':'assistant','content':response})
            if step['status']=='protocol_error':
                messages.append({'role':'user','content':json.dumps(step['feedback'])})
                continue
            action=json.loads(response,object_pairs_hook=unique_object,parse_constant=reject_constant)
            require(action==step['action'],'Response/action mismatch')
            if step['status']=='finalized':
                require(step is record['steps'][-1] and action=={'op':'finalize','report':record['final_report']},'Finalization mismatch')
                finalized=True
                continue
            require(step['status']=='completed','Submitted trial has incomplete step')
            request,decision,result=events[cursor:cursor+3];cursor+=3
            require([request['phase'],decision['phase'],result['phase']]==['request','decision','result'],'Event phase mismatch')
            require(request['request']==action and request['id']==decision['id']==result['id'],'Action/journal mismatch')
            require(result['feedback']==step['feedback'],'Feedback/journal mismatch')
            require(result['before']==previous,'State chain mismatch')
            previous=result['after']
            executions+=action['op']=='run' and entry['spec']['public']['permissions']['run']
            messages.append({'role':'user','content':json.dumps(step['feedback'])})
        require(finalized and cursor==len(events),'Unconsumed journal or missing finalization')
        require(executions==record['execution_calls'],'Execution count mismatch')
        require(previous==record['final_files'],'Journal/final state mismatch')
        observations=observe(entry['spec'],workspace,entry['initial_files'],events,snapshot_valid=True)
        require(observations==read(directory/'observations.json'),'Independent observations mismatch')
        profile=score(entry['spec'],events,record['final_report'],observations)
        require(profile==read(directory/'profile.json'),'Recomputed profile mismatch')
        require(profile['observation_status']=='valid','Invalid submitted evidence')
        verified.append(index)
    require(started==sorted(started),'Trial timestamps contradict frozen order')
    require(len(paths)==len(started),'Unplanned trial record')
    return {'verified_submitted_trials':verified,'incomplete_trials':incomplete,'unique_verified_client_sessions':len(sessions),
            'all_planned_trials_verified':len(verified)==len(entries),
            'preflight_status':preflight_status,'recorded_task_attempts':len(paths),
            'total_attempts_including_preflight':len(paths)+int((root/'preflight.json').exists()),
            'scope':'Frozen hashes, transcript replay, sealed events, state continuity and independent grading. Incomplete trials explicitly excluded; no universal safety assertion.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    print(json.dumps(audit(parser.parse_args().root),indent=2))
