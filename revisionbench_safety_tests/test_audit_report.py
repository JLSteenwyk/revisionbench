import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from revisionbench_safety.audit import audit
from revisionbench_safety.persistence import write_json
from revisionbench_safety.report import summarize
from revisionbench_safety.runner import initialize, run_trial, file_hash
from revisionbench_safety.scoring import unknown_profile
from test_runner_integration import ScriptedAdapter


@unittest.skipUnless(os.environ.get('REVISIONBENCH_DOCKER_TESTS')=='1','Frozen audit with actual prepared workspaces')
class AuditReportTests(unittest.TestCase):
    def test_replay_recomputation_tampering_and_exclusion_denominators(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'pilot'
            evidence=Path(temp)/'test-evidence.txt';evidence.write_text('Synthetic test gate only\nOK\n')
            adapter=ScriptedAdapter([])
            config=initialize(root,adapter,evidence)
            entries=json.loads((root/'preparation.json').read_text())
            entry=next(e for e in entries if e['spec']['id']=='inventory_present')
            report={'decision':'complete','executed_operation_ids':['op-1'],'run_status':'not_run',
                    'checks_run':['op-1'],'analysis_complete':True,
                    'outputs':{p:'present' for p in entry['spec']['public']['required_outputs']},
                    'claims':{},'unresolved':[],'question':''}
            adapter.actions=iter([{'op':'check_outputs'},{'op':'finalize','report':report}])
            directory=root/'trials'/f"{entry['index']:02d}"
            run_trial(directory,root/entry['workspace'],entry,config,adapter)
            result=audit(root)
            self.assertEqual(result['verified_submitted_trials'],[entry['index']])
            self.assertFalse(result['all_planned_trials_verified'])
            summary=summarize(root)
            self.assertEqual(summary['rates']['task_completion']['denominator'],1)
            self.assertIsNone(summary['rates']['direct_containment_given_attempt']['rate'])
            self.assertIsNone(summary['rates']['specified_claim_accuracy_when_checkable']['rate'])
            self.assertEqual(summary['unstarted_trials'],13)
            record=json.loads((directory/'record.json').read_text())
            altered=copy.deepcopy(record);altered['steps'][0]['action']={'op':'run'}
            write_json(directory/'record.json',altered)
            with self.assertRaisesRegex(ValueError,'Response/action mismatch'):audit(root)
            write_json(directory/'record.json',record)
            profile=json.loads((directory/'profile.json').read_text())
            altered=copy.deepcopy(profile);altered['utility']=False
            write_json(directory/'profile.json',altered)
            with self.assertRaisesRegex(ValueError,'Recomputed profile mismatch'):audit(root)
            write_json(directory/'profile.json',profile)
            # Synthetic official-client receipts exercise isolation/session auditing without inference.
            oauth_record=copy.deepcopy(record)
            for number,step in enumerate(oauth_record['steps']):
                stream=[{'type':'thread.started','thread_id':str(number)},
                        {'type':'item.completed','item':{'type':'agent_message','text':step['response']['text']}}]
                step['response']['receipt']={'exit_code':0,'termination':None,'stdout':'\n'.join(json.dumps(e) for e in stream)}
            config['adapter']['adapter']='codex_oauth'
            write_json(root/'config.json',config)
            (root/'config.sha256').write_text(file_hash(root/'config.json')+'\n')
            write_json(directory/'record.json',oauth_record)
            self.assertEqual(audit(root)['unique_verified_client_sessions'],2)
            altered=copy.deepcopy(oauth_record)
            receipt=altered['steps'][1]['response']['receipt']
            receipt['stdout']=receipt['stdout'].replace('"thread_id": "1"','"thread_id": "0"')
            write_json(directory/'record.json',altered)
            with self.assertRaisesRegex(ValueError,'reused client session'):audit(root)
            altered=copy.deepcopy(oauth_record)
            altered['steps'][0]['response']['receipt']['stdout']+='\n'+json.dumps({'type':'item.completed','item':{'type':'command_execution'}})
            write_json(directory/'record.json',altered)
            with self.assertRaisesRegex(ValueError,'Native tool event'):audit(root)
            # An interrupted observation must not become a zero-violation safety success.
            record['status']='interrupted';record.pop('elapsed_seconds')
            write_json(directory/'record.json',record)
            write_json(directory/'profile.json',unknown_profile('synthetic interruption'))
            summary=summarize(root)
            self.assertEqual(summary['eligible_submitted_trials'],0)
            self.assertEqual(len(summary['excluded_trials']),1)
            self.assertIsNone(summary['rates']['task_completion']['rate'])
            self.assertIsNone(summary['resources']['median_trial_seconds'])
            self.assertEqual(audit(root)['incomplete_trials'][config['order'].index(entry['index'])]['status'],'interrupted')
