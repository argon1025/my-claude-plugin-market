#!/usr/bin/env python3
"""Install packages in a temporary Codex home and check the real loader (no model calls)."""
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]


def inspect(env, cwd, overrides=()):
    server = subprocess.Popen(['codex', 'app-server', '--stdio', *overrides],
                              cwd=cwd, env=env, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    messages = queue.Queue()

    def read():
        for line in server.stdout:
            messages.put(json.loads(line))
        messages.put({'error': 'server closed stdout'})

    threading.Thread(target=read, daemon=True).start()

    def request(i, method, params):
        server.stdin.write(json.dumps({'id': i, 'method': method, 'params': params}) + '\n')
        server.stdin.flush()
        while True:
            response = messages.get(timeout=30)
            if response.get('id') == i:
                if 'error' in response:
                    raise RuntimeError(response['error'])
                return response['result']
            if response.get('error'):
                raise RuntimeError(response['error'])

    try:
        request(1, 'initialize', {'clientInfo': {'name': 'plugin-loader-test', 'version': '1'}})
        server.stdin.write('{"method":"initialized"}\n')
        server.stdin.flush()
        skills = request(2, 'skills/list', {'cwds': [str(cwd)]})
        hooks = request(3, 'hooks/list', {'cwds': [str(cwd)]})
        return skills, hooks
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        server.stdin.close()
        server.stdout.close()


def main():
    catalog = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
    ids = {item['name'] + '@' + catalog['name'] for item in catalog['plugins']}
    with tempfile.TemporaryDirectory(prefix='codex-loader-') as directory:
        cwd = Path(directory)
        home = cwd / 'codex'
        home.mkdir()
        (home / 'config.toml').write_text('[features]\napps = false\nremote_plugin = false\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('ORCA_', 'CODEX_', 'CLAUDE_CODE_'))}
        env['CODEX_HOME'] = str(home)

        def codex(*args):
            return subprocess.run(['codex', *args], cwd=cwd, env=env, text=True,
                                  capture_output=True, timeout=30, check=True)

        version = codex('--version').stdout.strip()
        codex('plugin', 'marketplace', 'add', str(ROOT), '--json')
        for ident in sorted(ids):
            codex('plugin', 'add', ident, '--json')
        skills, hooks = inspect(env, cwd)
        loaded = [s for row in skills['data'] for s in row['skills'] if s.get('pluginId') in ids]
        expected = {item['name'] + ':' + path.parent.name
                    for item in catalog['plugins']
                    for path in (ROOT / item['source']['path']).glob('skills/*/SKILL.md')}
        assert {s['name'] for s in loaded} == expected, loaded
        configured = [h for row in hooks['data'] for h in row['hooks'] if h.get('pluginId') in ids]
        assert len(configured) == 4, configured
        assert sorted(h['eventName'] for h in configured) == ['sessionStart'] * 3 + ['userPromptSubmit']
        assert all(h['trustStatus'] == 'untrusted' for h in configured), configured
        assert not any(row.get('errors') for row in hooks['data']), hooks
        comms = next(item['name'] for item in catalog['plugins']
                     if not (ROOT / item['source']['path'] / 'skills').exists())
        config_path = home / 'config.toml'
        config = config_path.read_text()
        section = f'[plugins."{comms}@{catalog["name"]}"]\nenabled = true'
        assert section in config, 'Expected installed plugin configuration'
        config_path.write_text(config.replace(section, section.replace('true', 'false')))
        _, disabled = inspect(env, cwd)
        active = [h for row in disabled['data'] for h in row['hooks'] if h.get('pluginId') in ids]
        assert len(active) == 2, active
        print(f'{version}: {len(loaded)} skills, {len(configured)} untrusted hooks; disable removes both communication hooks')


if __name__ == '__main__':
    main()
