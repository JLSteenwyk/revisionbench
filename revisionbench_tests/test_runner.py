import copy
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from revisionbench.adapters import AdapterError, CodexOAuth, LocalInference, bounded_process, clean_environment
from revisionbench.branches import hashes
from revisionbench import runner


class FakeModel:
    metadata = {'adapter': 'test', 'model': 'scripted'}

    def __init__(self, actions):
        self.actions = iter(actions)
        self.calls = []

    def generate(self, messages, timeout, limit):
        self.calls.append(copy.deepcopy(messages))
        action = next(self.actions)
        if isinstance(action, Exception):
            raise action
        return {'text': json.dumps(action), 'usage': None, 'receipt': {'test_only': True}}


def workspace(root):
    root.mkdir()
    for name in ('data', 'outputs', 'prior/outputs'):
        (root/name).mkdir(parents=True)
    (root/'data/penguins.csv').write_text('species,body_mass_g\nA,10\n')
    (root/'CORRECTION.txt').write_text('Test requirement')
    (root/'CONTRACT.json').write_text('{}')
    (root/'analyze.py').write_text('print("old")')
    (root/'outputs/stale.txt').write_text('not a successful result')
    (root/'prior/outputs/sample_counts.json').write_text('{"A":1}')
    return root


JOB = {'workflow': 'summary', 'case': 'median_requirement', 'strategy': 'repair', 'target': 'median'}


class AdapterTests(unittest.TestCase):
    def test_no_key_proxy_or_parent_session_inheritance(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'dummy', 'HTTP_PROXY': 'http://bad',
                                     'CODEX_THREAD_ID': 'parent'}):
            env = clean_environment()
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('HTTP_PROXY', env)
        self.assertNotIn('CODEX_THREAD_ID', env)

    def test_hosted_urls_and_redirects_rejected(self):
        for endpoint in ('https://api.openai.com/v1', 'http://localhost:8765/v1',
                         'http://127.0.0.1.evil/v1', 'http://user:pass@127.0.0.1/v1'):
            with self.assertRaises(ValueError):
                LocalInference('test', endpoint)
        seen = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append(self.path)
                self.send_response(302)
                self.send_header('Location', 'https://example.com/never-follow')
                self.end_headers()
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = LocalInference('test', f'http://127.0.0.1:{server.server_port}/v1')
            with self.assertRaises(AdapterError):
                adapter.generate([], 3, 4096)
            self.assertEqual(seen, ['/v1/chat/completions'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_local_request_roundtrip_no_credentials(self):
        received = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((dict(self.headers), json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                body = json.dumps({'choices':[{'message':{'content':'{"action":"finish"}'}}], 'usage': {'completion_tokens': 7}}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = LocalInference('test', f'http://127.0.0.1:{server.server_port}/v1')
            result = adapter.generate([{'role':'user','content':'test'}], 3, 4096)
            self.assertEqual(json.loads(result['text'])['action'], 'finish')
            self.assertEqual(result['usage']['completion_tokens'], 7)
            self.assertNotIn('Authorization', received[0][0])
            self.assertEqual(received[0][1]['temperature'], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_process_timeout_output_and_eof_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            start = time.monotonic()
            result = bounded_process([sys.executable, '-c', 'import os,time;os.close(1);os.close(2);time.sleep(5)'], '', temp, {}, .2, 2048)
            self.assertEqual(result['termination'], 'timeout')
            self.assertLess(time.monotonic()-start, 2)
            result = bounded_process([sys.executable, '-c', 'print("x"*10000)'], '', temp, {}, 3, 2048)
            self.assertEqual(result['termination'], 'output_limit')
            self.assertLessEqual(len(result['stdout'])+len(result['stderr']), 2048)

    def test_oauth_rejects_api_login_and_unexpected_tools(self):
        with patch('subprocess.check_output', return_value='codex-cli 0.154.0'), patch('subprocess.run') as status:
            status.return_value = subprocess.CompletedProcess([], 0, 'Logged in using an API key', '')
            with self.assertRaises(AdapterError):
                CodexOAuth('test')
        adapter = object.__new__(CodexOAuth)
        adapter.model, adapter.effort, adapter.features, adapter.env = 'test', 'low', ['shell_tool', 'apps'], {}
        stream = json.dumps({'type':'item.completed','item':{'type':'command_execution'}})
        with patch('revisionbench.adapters.bounded_process', return_value={'stdout':stream,'stderr':'','termination':None,'exit_code':0}):
            with self.assertRaisesRegex(AdapterError, 'native client tool'):
                adapter.generate([], 3, 4096)
        command = adapter.command(Path('/tmp/instructions'))
        self.assertIn('forced_login_method="chatgpt"', command)
        self.assertIn('permissions.revisionbench.filesystem={"/" = "deny"}', command)
        self.assertIn('--ignore-user-config', command)


class RunnerTests(unittest.TestCase):
    def test_persisted_credentials_are_redacted(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'record.json'
            runner.write_json(target, {'access_token':'do-not-store', 'log':'Authorization: Bearer abcdef',
                                      'nested':['sk-abcdefghijklmnopqrstuvwxyz', 'eyJheader.payload.signature']})
            text = target.read_text()
            for secret in ('do-not-store','abcdef','sk-abcdefghijklmnopqrstuvwxyz','eyJheader.payload.signature'):
                self.assertNotIn(secret, text)

    def test_execution_cannot_start_without_cleanup_time(self):
        with patch('revisionbench.runner.run') as executor:
            with self.assertRaisesRegex(AdapterError, 'Insufficient time'):
                runner.execute(Path('/unused'), runner.DEFAULT_BUDGET, 30, executor)
            executor.assert_not_called()

    def test_reads_reject_escape_symlinks_and_budgets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = workspace(Path(temp)/'work')
            (root/'link').symlink_to('/etc/passwd')
            for name in ('../outside', '/etc/passwd', 'link'):
                with self.assertRaises(ValueError):
                    runner.read_files(root, [name], 100)
            with self.assertRaises(ValueError):
                runner.read_files(root, ['data/penguins.csv'], 1)
            with self.assertRaises(ValueError):
                runner.parse_action('{"action":"write","code":"123"}', 2)

    def test_invalid_snapshot_never_graded_and_attempt_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = workspace(Path(temp)/'work')
            model = FakeModel([{'action':'finish'}])
            executor = lambda *a, **k: {'exit_code':0, 'snapshot_error':'special file', 'stdout':''}
            with patch('revisionbench.runner.workflow') as evaluate:
                result = runner.trial(Path(temp)/'trial', root, JOB, {'budget':runner.DEFAULT_BUDGET}, model, executor)
                evaluate.assert_not_called()
            self.assertEqual(result['status'], 'model_failure')
            self.assertIsNone(result['grade'])
            self.assertEqual(result['executions'], 1)
            self.assertTrue((Path(temp)/'trial/submitted_outputs/stale.txt').exists())

    def test_turn_budget_counts_bad_actions_and_never_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = workspace(Path(temp)/'work')
            model = FakeModel([{'action':'invalid'}]*2)
            budget = dict(runner.DEFAULT_BUDGET, model_turns=2)
            result = runner.trial(Path(temp)/'trial', root, JOB, {'budget':budget}, model)
            self.assertEqual(result['status'], 'budget_failure')
            self.assertEqual(len(model.calls), 2)
            self.assertEqual(result['executions'], 0)

    def test_feedback_excludes_hidden_grading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = workspace(Path(temp)/'work')
            model = FakeModel([{'action':'run'}, {'action':'finish'}])
            def executor(root, **kwargs):
                (root/'outputs').mkdir(exist_ok=True)
                (root/'outputs/sample_counts.json').write_text('{"A":1}')
                return {'exit_code':0,'snapshot_error':None,'stdout':'ordinary execution output','termination':None}
            with patch('revisionbench.runner.workflow', return_value=(None, lambda *a: {'complete':True,'checks':{'secret_check':True}}, None)):
                result = runner.trial(Path(temp)/'trial', root, JOB, {'budget':runner.DEFAULT_BUDGET}, model, executor)
            self.assertEqual(result['status'], 'success')
            self.assertNotIn('secret_check', json.dumps(model.calls))
            self.assertIn('ordinary execution output', json.dumps(model.calls))
            self.assertEqual(result['executions'], 2)

    def test_execution_budget_protected_inputs_and_access_failures(self):
        for mode in ('execution_budget', 'mutate_input', 'access'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = workspace(Path(temp)/'work')
                budget = dict(runner.DEFAULT_BUDGET, executions=1)
                actions = [AdapterError('access_failure','Subscription limit')] if mode=='access' else [{'action':'run'}, {'action':'run'}]
                model = FakeModel(actions)
                def executor(root, **kwargs):
                    if mode=='mutate_input':
                        (root/'data/penguins.csv').write_text('altered')
                    return {'exit_code':0,'snapshot_error':None,'stdout':'','termination':None}
                result = runner.trial(Path(temp)/'trial', root, JOB, {'budget':budget}, model, executor)
                self.assertEqual(result['status'], {'execution_budget':'budget_failure','mutate_input':'model_failure','access':'access_failure'}[mode])
                self.assertLessEqual(result['executions'], 1)

    def test_resume_preserves_interrupted_trial_and_rejects_configuration_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = workspace(root/'work')
            job = dict(JOB, workspace='work', initial_files=hashes(work))
            runner.write_json(root/'plan.json', {'jobs':[job]})
            config = {'source_hashes':runner.source_hashes(),'adapter':FakeModel.metadata,'order':[0],
                      'plan_sha256':hashlib.sha256((root/'plan.json').read_bytes()).hexdigest()}
            runner.write_json(root/'config.json', config)
            (root/'config.sha256').write_text(hashlib.sha256((root/'config.json').read_bytes()).hexdigest())
            (root/'trials/00').mkdir(parents=True)
            runner.write_json(root/'trials/00/record.json', {'status':'running','steps':[{'status':'in_flight'}]})
            model = FakeModel([])
            runner.resume(root, model)
            self.assertEqual(json.loads((root/'trials/00/record.json').read_text())['status'], 'interrupted')
            self.assertEqual(model.calls, [])
            config['order'] = []
            runner.write_json(root/'config.json', config)
            with self.assertRaisesRegex(ValueError, 'configuration changed'):
                runner.resume(root, model)


if __name__ == '__main__':
    unittest.main()
