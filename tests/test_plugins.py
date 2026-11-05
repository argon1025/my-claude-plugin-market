"""Offline package and hook contracts. All mutable repositories live in TemporaryDirectory."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
PLUGINS = [ROOT / item['source']['path'] for item in CATALOG['plugins']]
FLOW = next(p for p in PLUGINS if (p / 'skills/planning').exists())
COMMS = next(p for p in PLUGINS if not (p / 'skills').exists())
WIKI = next(p for p in PLUGINS if (p / 'scripts/sync_wiki.py').exists())


def run(*args, cwd=None, env=None, input=None):
    return subprocess.run(args, cwd=cwd, env=env, input=input, text=True,
                          capture_output=True, timeout=15, check=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


class PackageTests(unittest.TestCase):
    def test_catalog_and_manifest_identity(self):
        self.assertEqual(len(PLUGINS), 4)
        self.assertEqual(len({p.name for p in PLUGINS}), 4)
        claude = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(CATALOG['name'], claude['name'])
        for item, plugin in zip(CATALOG['plugins'], PLUGINS):
            with self.subTest(plugin=plugin.name):
                portable = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
                legacy = json.loads((plugin / '.claude-plugin/plugin.json').read_text())
                self.assertEqual(portable['name'], item['name'])
                for key in ('name', 'version', 'description', 'author'):
                    self.assertEqual(portable[key], legacy[key])
                self.assertEqual(item['policy']['installation'], 'AVAILABLE')
                self.assertTrue(plugin.resolve().is_relative_to(ROOT.resolve()))
                entry = next(e for e in claude['plugins'] if e['name'] == item['name'])
                if 'version' in entry:
                    self.assertEqual(entry['version'], portable['version'])

    def test_packaged_references_and_invocation_policy(self):
        skills = [s for p in PLUGINS for s in p.glob('skills/*/SKILL.md')]
        self.assertEqual(len(skills), 9)
        for skill in skills:
            with self.subTest(skill=str(skill.relative_to(ROOT))):
                text = skill.read_text()
                self.assertRegex(text, r'^---\nname: [a-z][a-z-]*\ndescription: .+')
                self.assertNotIn('${CLAUDE_PLUGIN_ROOT}', text)
                for ref in re.findall(r'\]\(([^)]+)\)', text):
                    if ref.startswith(('http:', 'https:', '#')):
                        continue
                    self.assertTrue((skill.parent / ref.split('#')[0]).exists(), ref)
                metadata = skill.parent / 'agents/openai.yaml'
                explicit_only = 'disable-model-invocation: true' in text.split('---')[1]
                self.assertEqual(metadata.exists(), explicit_only)
                if explicit_only:
                    self.assertEqual(metadata.read_text(), 'policy:\n  allow_implicit_invocation: false\n')

    def test_hook_commands_resolve_inside_package_and_are_executable(self):
        for plugin in PLUGINS:
            for config in plugin.glob('hooks/*.json'):
                hooks = json.loads(config.read_text())['hooks']
                for groups in hooks.values():
                    for group in groups:
                        for hook in group['hooks']:
                            match = re.search(r'\$\{(?:CLAUDE_)?PLUGIN_ROOT\}(/[^" ]+)', hook['command'])
                            self.assertIsNotNone(match, hook['command'])
                            script = plugin / match[1].lstrip('/')
                            self.assertTrue(script.is_file())
                            if script.suffix == '.sh':
                                self.assertTrue(os.access(script, os.X_OK))
                                run('bash', '-n', str(script))

    def test_plan_codex_events_do_not_misidentify_approval(self):
        manifest = json.loads((FLOW / '.codex-plugin/plugin.json').read_text())
        hooks = json.loads((FLOW / manifest['hooks']).read_text())['hooks']
        self.assertEqual(set(hooks), {'SessionStart'})
        claude = json.loads((FLOW / 'hooks/hooks.json').read_text())['hooks']
        self.assertEqual(claude['PostToolUse'][0]['matcher'], 'ExitPlanMode')


class HookFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent-plugin-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        run('git', 'init', '-q', '-b', 'feature/demo', str(self.project))
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('CLAUDE_PROJECT_DIR', 'CLAUDE_PLUGIN_ROOT', 'PLUGIN_ROOT')}

    def invoke(self, plugin, script='session_start.sh', event=None, cwd=None, env=None):
        command = ['python3' if script.endswith('.py') else 'bash', str(plugin / 'hooks' / script)]
        result = run(*command, cwd=cwd or self.root, env=env or self.env,
                     input=json.dumps(event if event is not None else {'cwd': str(self.project), 'source': 'compact'}))
        return json.loads(result.stdout) if result.stdout.strip() else {}


class HookTests(HookFixture):
    def test_communication_context_and_prompt_reminder(self):
        # The installed package may contain spaces and need no plugin-root env var.
        plugin = self.root / 'installed plugin'
        shutil.copytree(COMMS, plugin)
        for source in ('startup', 'resume', 'clear', 'compact', 'fork'):
            result = self.invoke(plugin, event={'source': source})
            self.assertEqual(result['hookSpecificOutput']['additionalContext'],
                             (plugin / 'rules/agent-guide.md').read_text().strip())
        reminder = self.invoke(plugin, script='user_prompt_submit.sh')['hookSpecificOutput']
        self.assertEqual(reminder['hookEventName'], 'UserPromptSubmit')
        self.assertIn('COMMUNICATION RULES ACTIVE', reminder['additionalContext'])

    def test_plan_payload_cwd_and_nested_project(self):
        nested = self.project / 'src/deep'
        nested.mkdir(parents=True)
        config = json.loads((FLOW / 'config.json').read_text())
        workspace = self.project / config['workspace']['root'] / 'feature-demo'
        workspace.mkdir(parents=True)
        (workspace / 'plan.md').write_text('# Approved plan\n')
        (workspace / 'feedback.md').write_text('# 기록\n- `context` PAYLOAD_ROOT_MARKER\n')
        result = self.invoke(FLOW, event={'cwd': str(nested), 'source': 'startup'})
        context = result['hookSpecificOutput']['additionalContext']
        self.assertIn('feature-demo', context)
        self.assertIn('PAYLOAD_ROOT_MARKER', context)
        self.assertIn('**plan.md**: 있음', context)

    def test_plan_claude_env_fallback_and_non_git(self):
        env = {**self.env, 'CLAUDE_PROJECT_DIR': str(self.project)}
        result = self.invoke(FLOW, event={}, env=env)
        self.assertIn('feature-demo', result['hookSpecificOutput']['additionalContext'])
        self.assertEqual(self.invoke(FLOW, event={'cwd': str(self.root)}), {})

    def test_plan_default_branch_and_bad_input(self):
        run('git', 'symbolic-ref', 'HEAD', 'refs/heads/main', cwd=self.project)
        result = self.invoke(FLOW)
        self.assertIn('slug**: 미확정', result['hookSpecificOutput']['additionalContext'])
        result = self.invoke(FLOW, event=[], cwd=self.project)
        self.assertIn('slug**: 미확정', result['hookSpecificOutput']['additionalContext'])

    def test_plan_feedback_keeps_recent_complete_entries(self):
        config = json.loads((FLOW / 'config.json').read_text())
        workspace = self.project / config['workspace']['root'] / 'feature-demo'
        workspace.mkdir(parents=True)
        (workspace / 'feedback.md').write_text('# 기록\n' + ''.join(
            f'- `context` ENTRY_{i:03d} ' + '가' * 100 + '\n' for i in range(30)))
        context = self.invoke(FLOW)['hookSpecificOutput']['additionalContext']
        self.assertIn('ENTRY_029', context)
        self.assertNotIn('ENTRY_000', context)
        self.assertIn('생략', context)


class WikiHookTests(HookFixture):
    def setUp(self):
        super().setUp()
        self.plugin = self.root / 'wiki plugin'
        shutil.copytree(WIKI, self.plugin)
        self.wiki = self.root / 'wiki'
        self.wiki.mkdir()
        self.config = {'wiki': {'baseRoot': str(self.wiki), 'remote': str(self.root / 'missing-remote'), 'baseBranch': 'main'},
                       'workspace': {'root': str(self.root / 'workspace')}}
        write_json(self.plugin / 'config.json', self.config)
        self.registry = {'domains': {'sample': {'description': '샘플 서비스', 'repos': {
            'demo': {'summary': 'DEMO_SUMMARY', 'responsibilities': ['DEMO_RESPONSIBILITY']}}}}}
        write_json(self.wiki / 'registry.json', self.registry)
        write_json(self.wiki / 'deps.json', {'deps': {}})
        docs = self.wiki / 'knowledge/sample/demo'
        docs.mkdir(parents=True)
        (docs / 'contract.md').write_text('---\ndescription: DEMO_DOCUMENT\n---\n# Contract\n')

    def wiki_hook(self, **kwargs):
        return self.invoke(self.plugin, script='session_start.py', **kwargs)

    def test_registered_repo_context_and_index(self):
        run('git', 'remote', 'add', 'origin', 'https://example.invalid/demo.git', cwd=self.project)
        result = self.wiki_hook()
        self.assertIn('sample/demo', result['systemMessage'])
        context = result['hookSpecificOutput']['additionalContext']
        self.assertIn('DEMO_SUMMARY', context)
        self.assertIn('DEMO_DOCUMENT', context)
        index = self.wiki / '.local/index/sample/demo.md'
        self.assertIn('DEMO_RESPONSIBILITY', index.read_text())

    def test_unregistered_and_non_git_context(self):
        run('git', 'remote', 'add', 'origin', 'https://example.invalid/other.git', cwd=self.project)
        result = self.wiki_hook()
        self.assertIn('대상 외 프로젝트(other)', result['hookSpecificOutput']['additionalContext'])
        self.assertIn('register', result['systemMessage'])
        result = self.wiki_hook(event={'cwd': str(self.root), 'source': 'compact'})
        self.assertIn('대상 외 프로젝트', result['hookSpecificOutput']['additionalContext'])
        self.assertNotIn('register', result['systemMessage'])

    def test_missing_wiki_and_malformed_config_fail_open(self):
        (self.wiki / 'registry.json').unlink()
        result = self.wiki_hook()
        self.assertIn('init', result['systemMessage'])
        self.assertNotIn('hookSpecificOutput', result)
        (self.plugin / 'config.json').write_text('{broken')
        result = self.wiki_hook()
        self.assertIn('JSONDecodeError', result['systemMessage'])

    def test_sync_failure_still_loads_previous_copy(self):
        run('git', 'init', '-q', str(self.wiki))
        run('git', 'remote', 'add', 'origin', self.config['wiki']['remote'], cwd=self.wiki)
        result = self.wiki_hook(event={'cwd': str(self.project), 'source': 'startup'})
        self.assertIn('최신화 실패', result['systemMessage'])
        self.assertIn('sample', result['hookSpecificOutput']['additionalContext'])
        # Compaction must not sync or repeat the network failure.
        self.assertNotIn('최신화 실패', self.wiki_hook()['systemMessage'])

    def test_sync_timeout_reports_stale_copy(self):
        spec = importlib.util.spec_from_file_location('wiki_hook', self.plugin / 'hooks/session_start.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module.subprocess, 'Popen') as popen:
            popen.return_value.communicate.side_effect = subprocess.TimeoutExpired('fixture', 3)
            self.assertIn('이전 사본', module.sync_wiki(self.wiki, self.config['wiki']))


if __name__ == '__main__':
    unittest.main()
