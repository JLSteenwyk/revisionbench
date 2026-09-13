"""Text-only inference transports. No hosted HTTP requests or API-key support."""
import ipaddress
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


class AdapterError(RuntimeError):
    def __init__(self, category, message, receipt=None):
        super().__init__(message)
        self.category = category
        self.receipt = receipt or {}


def bounded_process(command, prompt, cwd, env, timeout, limit):
    """Bound both streams and kill only this invocation's process group."""
    started = time.monotonic()
    # A file avoids blocking on a large stdin before starting output supervision.
    with tempfile.TemporaryFile() as stdin:
        stdin.write(prompt.encode())
        stdin.seek(0)
        child = subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, cwd=cwd, env=env, start_new_session=True)
        streams = {'stdout': bytearray(), 'stderr': bytearray()}
        termination = None
        with selectors.DefaultSelector() as selector:
            for name in streams:
                selector.register(getattr(child, name), selectors.EVENT_READ, name)
            try:
                while selector.get_map() or child.poll() is None:
                    if time.monotonic()-started >= timeout:
                        termination = 'timeout'
                        break
                    for key, _ in selector.select(.05):
                        block = os.read(key.fd, 65536)
                        if not block:
                            selector.unregister(key.fileobj)
                            continue
                        remaining = limit-sum(map(len, streams.values()))
                        streams[key.data].extend(block[:max(0, remaining)])
                        if len(block) > remaining:
                            termination = 'output_limit'
                            break
                    if termination:
                        break
            finally:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=5)
                child.stdout.close()
                child.stderr.close()
    return {**{k: v.decode(errors='replace') for k, v in streams.items()},
            'exit_code': child.returncode, 'termination': termination,
            'wall_seconds': time.monotonic()-started}


def clean_environment():
    # Explicit allowlist: no provider keys, inherited proxies, session IDs or hooks.
    return {k: os.environ[k] for k in ('PATH', 'HOME', 'CODEX_HOME', 'LANG', 'SSL_CERT_FILE')
            if k in os.environ}


class CodexOAuth:
    """Official CLI, existing ChatGPT login, no model-native tool access."""
    def __init__(self, model, effort='low'):
        self.model, self.effort = model, effort
        self.env = clean_environment()
        version = subprocess.check_output(['codex', '--version'], env=self.env, text=True).strip()
        # Pin security configuration to the client version validated by this runner.
        if version != 'codex-cli 0.154.0':
            raise AdapterError('access_failure', 'Codex version requires isolation revalidation')
        status = subprocess.run(['codex', 'login', 'status'], env=self.env,
                                capture_output=True, text=True, timeout=15)
        if status.returncode or 'Logged in using ChatGPT' not in status.stdout+status.stderr:
            raise AdapterError('access_failure', 'Existing ChatGPT subscription login required')
        feature_lines = subprocess.check_output(['codex', 'features', 'list'], env=self.env,
                                                text=True, timeout=15).splitlines()
        self.features = sorted(line.split()[0] for line in feature_lines
                               if line.strip() and not any(s in line.split() for s in ('removed', 'deprecated')))
        self.metadata = {'adapter': 'codex_oauth', 'model': model, 'effort': effort,
                         'client_version': version, 'authentication': 'existing ChatGPT login',
                         'disabled_features': self.features,
                         'native_tools': 'disabled; deny-all filesystem and network backstop',
                         'temperature': None, 'seed': None, 'max_output_tokens': None}

    def command(self, instructions):
        values = {
            'forced_login_method': 'chatgpt', 'model_provider': 'openai',
            'web_search': 'disabled', 'approval_policy': 'never',
            'default_permissions': 'revisionbench',
            'permissions.revisionbench.filesystem': {'/': 'deny'},
            'permissions.revisionbench.network.enabled': False,
            'project_doc_max_bytes': 0, 'model_reasoning_effort': self.effort,
            'model_instructions_file': str(instructions),
            'features.skip_host_skill_discovery': True,
        }
        command = ['codex', 'exec', '--ignore-user-config', '--ignore-rules',
                   '--ephemeral', '--skip-git-repo-check', '--json', '--color', 'never',
                   '--model', self.model]
        for feature in self.features:
            command += ['--disable', feature]
        # TOML inline tables differ from JSON objects.
        for key, value in values.items():
            encoded = '{"/" = "deny"}' if isinstance(value, dict) else json.dumps(value)
            command += ['-c', key+'='+encoded]
        return command+['-']

    def generate(self, messages, timeout, limit):
        with tempfile.TemporaryDirectory(prefix='revisionbench-client-') as temp:
            instructions = Path(temp)/'instructions.txt'
            instructions.write_text('You are a text-only scientific coding model. Follow the supplied protocol. '
                                    'You have no native tools. Return only the requested JSON action.')
            command = self.command(instructions)
            receipt = bounded_process(command, json.dumps(messages), temp, self.env, timeout, limit)
        # Logs contain no credentials by design; never expose stderr to the candidate.
        if receipt['termination']:
            raise AdapterError('budget_failure', receipt['termination'], receipt)
        events = []
        for line in receipt['stdout'].splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                raise AdapterError('infrastructure_failure', 'Invalid CLI event stream', receipt)
        items = [e['item'] for e in events if e.get('type') == 'item.completed']
        forbidden = [i for i in items if i.get('type') not in ('agent_message', 'reasoning', 'error')]
        if forbidden:
            raise AdapterError('infrastructure_failure', 'Unexpected native client tool event', receipt)
        if receipt['exit_code'] or any(e.get('type') in ('error', 'turn.failed') for e in events):
            text = (receipt['stdout']+receipt['stderr']).lower()
            category = 'access_failure' if any(x in text for x in
                ('usage limit', 'rate limit', 'unauthorized', 'authentication', 'not supported', 'quota', '401', '429')) else 'infrastructure_failure'
            raise AdapterError(category, 'Codex invocation failed; see trusted receipt', receipt)
        answers = [i['text'] for i in items if i.get('type') == 'agent_message']
        if not answers:
            raise AdapterError('infrastructure_failure', 'No final model response', receipt)
        usage = next((e.get('usage') for e in reversed(events) if e.get('type') == 'turn.completed'), None)
        return {'text': answers[-1], 'usage': usage, 'receipt': receipt}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise AdapterError('infrastructure_failure', 'Local inference redirects are forbidden')


class LocalInference:
    """OpenAI-compatible protocol ONLY to an explicitly numeric loopback address."""
    def __init__(self, model, endpoint, max_tokens=4096, seed=1729, runtime=None):
        parsed = urllib.parse.urlsplit(endpoint)
        try:
            local = ipaddress.ip_address(parsed.hostname).is_loopback
        except (ValueError, TypeError):
            local = False
        if not local or parsed.scheme != 'http' or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Local inference requires a numeric loopback HTTP URL without credentials')
        self.endpoint, self.model, self.max_tokens, self.seed = endpoint.rstrip('/'), model, max_tokens, seed
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.metadata = {'adapter': 'local', 'model': model, 'endpoint': self.endpoint,
                         'max_output_tokens': max_tokens, 'temperature': 0, 'seed': seed,
                         'runtime': runtime, 'authentication': 'none', 'client_version': 'stdlib urllib'}

    def generate(self, messages, timeout, limit):
        # Isolate the HTTP wait in a killable child: a slowly streaming local server
        # must not extend the deadline by repeatedly resetting a socket timeout.
        body = {'model': self.model, 'messages': messages, 'temperature': 0,
                'seed': self.seed, 'max_tokens': self.max_tokens, 'stream': False}
        with tempfile.TemporaryDirectory(prefix='revisionbench-local-') as temp:
            receipt = bounded_process([sys.executable, '-I', str(Path(__file__).resolve()),
                                       self.endpoint, str(timeout), str(limit)],
                                      json.dumps(body), temp, {}, timeout, limit)
        if receipt['termination']:
            raise AdapterError('budget_failure', receipt['termination'], receipt)
        if receipt['exit_code']:
            raise AdapterError('infrastructure_failure', 'Local transport failed', receipt)
        try:
            data = json.loads(receipt['stdout'])
            if data['choices'][0].get('message', {}).get('tool_calls'):
                raise AdapterError('infrastructure_failure', 'Unexpected provider tool call', receipt)
            return {'text': data['choices'][0]['message']['content'], 'usage': data.get('usage'), 'receipt': receipt}
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AdapterError('infrastructure_failure', 'Invalid local response', receipt) from exc

    def request(self, body, timeout, limit):
        started = time.monotonic()
        request = urllib.request.Request(self.endpoint+'/chat/completions', data=json.dumps(body).encode(),
                                          headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read(limit+1)
            if len(raw) > limit:
                raise AdapterError('budget_failure', 'Local response exceeds output limit')
            return raw.decode()
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            raise AdapterError('infrastructure_failure', type(exc).__name__) from exc


if __name__ == '__main__':
    try:
        endpoint, timeout, limit = sys.argv[1:]
        print(LocalInference('transport', endpoint).request(json.load(sys.stdin), float(timeout), int(limit)))
    except Exception as exc:
        print(type(exc).__name__, file=sys.stderr)
        sys.exit(1)
