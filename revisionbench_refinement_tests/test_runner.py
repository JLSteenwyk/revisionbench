import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from revisionbench.adapters import AdapterError
from revisionbench.branches import hashes
from revisionbench_safety.ledger import verify
from revisionbench_safety.persistence import write_json
from revisionbench_refinement.preparation import prepare
from revisionbench_refinement.runner import BUDGET,PREFLIGHT_PROMPT,initialize,preflight,resume,run_trial
from revisionbench_refinement.validation import validate
from test_refinement import case


class ScriptedAdapter:
    metadata={'adapter':'scripted_validation','model':'none'}
    def __init__(self,actions):self.actions=iter(actions);self.calls=[]
    def generate(self,messages,timeout,limit):
        self.calls.append(copy.deepcopy(messages));action=next(self.actions)
        if isinstance(action,Exception):raise action
        return {'text':action if isinstance(action,str) else json.dumps(action),'usage':None,'receipt':{'validation_only':True}}


class NonDockerRunnerTests(unittest.TestCase):
    def execute(self,root,actions):
        spec=case('calibration_available');prep=prepare(spec,root/'workspace');adapter=ScriptedAdapter(actions)
        record=run_trial(root/'trusted',root/'workspace',{'index':0,'spec':spec,**prep},{'budget':BUDGET},adapter)
        return record,json.loads((root/'trusted/profile.json').read_text()),adapter

    def test_calibration_all_manual_expected_labels_pass(self):
        result=validate();self.assertTrue(result['all_passed']);self.assertEqual(result['fixtures'],34)
        for metrics in result['dimensions'].values():
            self.assertEqual(metrics['sensitivity'],1.0)
            self.assertEqual(metrics['false_positive_rate'],0.0)

    def test_fact_answer_scored_after_finalization_with_public_only_feedback(self):
        with tempfile.TemporaryDirectory() as temp:
            report={'decision':'complete','executed_operation_ids':['op-1'],'checks_run':[],'run_status':'not_run',
                    'facts':{'calibrated_value':8},'unresolved':[],'question':''}
            root=Path(temp)
            record,profile,adapter=self.execute(root,[{'op':'read','paths':['data/measurement.json','data/calibration.json']},
                                                       {'op':'finalize','report':report}])
            self.assertEqual(record['status'],'submitted');self.assertTrue(profile['core_task_success'])
            self.assertTrue(profile['evidence']['calibrated_value']['basis_observed'])
            self.assertNotIn('expected_decision',json.dumps(adapter.calls));self.assertNotIn('core_task_success',json.dumps(adapter.calls))
            self.assertEqual(len(verify(root/'trusted')),3)

    def test_inaccurate_answer_preserved_without_grader_coaching(self):
        with tempfile.TemporaryDirectory() as temp:
            record,profile,adapter=self.execute(Path(temp),[{'op':'finalize','report':{'decision':'complete','facts':{'calibrated_value':9}}}])
            self.assertEqual(record['status'],'submitted');self.assertFalse(profile['core_task_success'])
            self.assertEqual(profile['evidence']['calibrated_value']['accuracy'],'incorrect');self.assertEqual(len(adapter.calls),1)

    def test_access_failure_preserved_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            record,profile,adapter=self.execute(Path(temp),[AdapterError('access_failure','mock usage limit')])
            self.assertEqual(record['status'],'access_failure');self.assertEqual(len(adapter.calls),1)

    def test_invalid_json_does_not_become_an_action(self):
        with tempfile.TemporaryDirectory() as temp:
            record,profile,adapter=self.execute(Path(temp),['{"op":"run","op":"read"}',{'op':'finalize','report':{}}])
            self.assertEqual(record['steps'][0]['status'],'protocol_error')
            self.assertEqual(record['execution_calls'],0);self.assertEqual(profile['authorization']['operation_opportunities'],0)

    def test_preflight_is_one_attempt_even_if_interrupted_or_access_blocked(self):
        config={'preflight_trials':1,'preflight_prompt':PREFLIGHT_PROMPT,'budget':BUDGET}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);adapter=ScriptedAdapter([{'native_tools_available':False,'explanation':'scripted fixture'}])
            self.assertTrue(preflight(root,config,adapter));self.assertTrue(preflight(root,config,adapter))
            self.assertEqual(len(adapter.calls),1)
            write_json(root/'preflight.json',{'status':'running','model_calls':1})
            self.assertFalse(preflight(root,config,adapter));self.assertEqual(len(adapter.calls),1)
            self.assertEqual(json.loads((root/'preflight.json').read_text())['status'],'interrupted')
        with tempfile.TemporaryDirectory() as temp:
            adapter=ScriptedAdapter([AdapterError('access_failure','mock quota')]);root=Path(temp)
            self.assertFalse(preflight(root,config,adapter));self.assertFalse(preflight(root,config,adapter));self.assertEqual(len(adapter.calls),1)


@unittest.skipUnless(os.environ.get('REVISIONBENCH_DOCKER_TESTS')=='1','Real frozen task preparation')
class FrozenRunnerTests(unittest.TestCase):
    def test_interruption_resumption_access_stop_and_config_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'pilot';test_evidence=Path(temp)/'fixture-gate.txt';test_evidence.write_text('Synthetic gate for test initialization only\nOK\n')
            reference=Path('projects/revisionbench/refinement/evidence/development-validation-001/reference-validation.json')
            adapter=ScriptedAdapter([]);config=initialize(root,adapter,test_evidence,reference)
            first=config['order'][0];directory=root/'trials'/f'{first:02d}';directory.mkdir()
            write_json(directory/'record.json',{'status':'running','steps':[{'status':'in_flight'}]})
            dispatched=[]
            def fake_trial(directory,workspace,entry,config,adapter):
                dispatched.append(entry['index']);directory.mkdir();record={'status':'submitted'}
                write_json(directory/'record.json',record);return record
            with patch('builtins.print'):resume(root,adapter,trial_function=fake_trial)
            self.assertEqual(dispatched,config['order'][1:])
            record=json.loads((directory/'record.json').read_text());self.assertEqual(record['status'],'interrupted')
            self.assertIsNone(json.loads((directory/'profile.json').read_text())['core_task_success'])
            before=hashes(root);resume(root,adapter,trial_function=fake_trial);self.assertEqual(before,hashes(root))
            self.assertEqual(adapter.calls,[])
            with patch('revisionbench_refinement.runner.sources',return_value={}):
                with self.assertRaisesRegex(ValueError,'Sources or adapter changed'):resume(root,adapter)
            write_json(directory/'record.json',{'status':'access_failure'})
            with patch('builtins.print'):resume(root,adapter,trial_function=lambda *a: self.fail('Access blocker ignored'))
            changed=copy.deepcopy(config);changed['seed']+=1;write_json(root/'config.json',changed)
            with self.assertRaisesRegex(ValueError,'Configuration changed'):resume(root,adapter)
