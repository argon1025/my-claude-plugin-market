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
        self.assertEqual(len(PLUGINS), 5)
        self.assertEqual(len({p.name for p in PLUGINS}), 5)
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
        self.assertEqual(len(skills), 13)
        self.assertEqual({s.parent.name for s in skills if s.parents[2].name == 'auto-flow'},
                         {'run-issue', 'plan-issue', 'resolve-issue', 'review-issue'})
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

    def test_auto_flow_issue_template_sections_and_tables(self):
        record = (ROOT / 'auto-flow/references/issue-template.md').read_text()
        template = record.split('```markdown\n', 1)[1].split('\n```', 1)[0]
        lines = template.splitlines()
        # The status line is the first line under the first section; skills read it to pick the stage.
        self.assertEqual(lines[:2], ['## 진행', '상태: 검토'])
        self.assertEqual([line[3:] for line in lines if line.startswith('## ')],
                         ['진행', '요청', '스펙', '정책 변경', '결정', '미결 사항', '레포별 계획',
                          '리뷰 기록', '교정 기록'])
        headers = [lines[index - 1] for index, line in enumerate(lines) if line.startswith('| --- |')]
        self.assertEqual(headers, [
            '| 레포 | 맡은 쪽 | 브랜치 | PR | 단계 |',
            '| 번호 | 인수 조건 | 근거 | 확인 방법 | 맡는 레포 | 확인 결과 |',
            '| 기존 | 새 정책 | 근거 | 위키 반영 |',
            '| 번호 | 질문 | 답할 사람 | 걸린 인수 조건 |',
            '| 번호 | 회차 | 레포 | 지적과 위치 | 등급 | 판정과 처리 | 상태 |',
            '| 유형 | 처음 판단 | 바로잡은 내용 | 드러난 지점 |',
        ])
        for header, rule in zip(headers, (line for line in lines if line.startswith('| --- |'))):
            self.assertEqual(header.count('|'), rule.count('|'))

    def test_auto_flow_stage_documents_resolve_and_are_entered_by_skills(self):
        references = ROOT / 'auto-flow/references'
        for document in references.rglob('*.md'):
            for ref in re.findall(r'\]\(([^)]+)\)', document.read_text()):
                if ref.startswith(('http:', 'https:', '#')):
                    continue
                with self.subTest(document=str(document.relative_to(ROOT)), ref=ref):
                    self.assertTrue((document.parent / ref.split('#')[0]).exists())
        stages = {'run-issue': {'stage-plan.md', 'stage-resolve.md', 'stage-review.md'},
                  'plan-issue': {'stage-plan.md'}, 'resolve-issue': {'stage-resolve.md'},
                  'review-issue': {'stage-review.md'}}
        for name, expected in stages.items():
            with self.subTest(skill=name):
                text = (ROOT / 'auto-flow/skills' / name / 'SKILL.md').read_text()
                linked = {Path(ref).name for ref in re.findall(r'\]\(([^)]+)\)', text)}
                # Every entry point runs the shared start procedure, then only its own stage documents.
                self.assertEqual(linked, expected | {'common.md'})

    def test_plan_codex_events_do_not_misidentify_approval(self):
        manifest = json.loads((FLOW / '.codex-plugin/plugin.json').read_text())
        hooks = json.loads((FLOW / manifest['hooks']).read_text())['hooks']
        self.assertEqual(set(hooks), {'SessionStart'})
        # Approval is the planning skill's question, so neither client registers a plan-mode hook.
        claude = json.loads((FLOW / 'hooks/hooks.json').read_text())['hooks']
        self.assertEqual(set(claude), {'SessionStart'})


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

    def checkout(self, branch):
        run('git', 'symbolic-ref', 'HEAD', f'refs/heads/{branch}', cwd=self.project)

    def workspace(self, folder):
        config = json.loads((FLOW / 'config.json').read_text())
        path = self.project / config['workspace']['root'] / folder
        path.mkdir(parents=True)
        return path

    def test_plan_payload_cwd_and_nested_project(self):
        self.checkout('feature/PROJ-12-demo')
        nested = self.project / 'src/deep'
        nested.mkdir(parents=True)
        workspace = self.workspace('PROJ-12')
        (workspace / 'plan.md').write_text('# Approved plan\n')
        (workspace / 'feedback.md').write_text('# 기록\n- `constraint` PAYLOAD_ROOT_MARKER\n')
        result = self.invoke(FLOW, event={'cwd': str(nested), 'source': 'startup'})
        context = result['hookSpecificOutput']['additionalContext']
        self.assertIn('이슈 키**: `PROJ-12`', context)
        self.assertIn('/PROJ-12/` — `plan.md`·`feedback.md` 있음', context)
        self.assertIn('**읽기**', context)
        # Record bodies are read on demand, never injected.
        self.assertNotIn('PAYLOAD_ROOT_MARKER', context)

    def test_plan_claude_env_fallback_and_non_git(self):
        self.checkout('feature/PROJ-12-demo')
        env = {**self.env, 'CLAUDE_PROJECT_DIR': str(self.project)}
        result = self.invoke(FLOW, event={}, env=env)
        context = result['hookSpecificOutput']['additionalContext']
        self.assertIn('/PROJ-12/` — 아직 없으며', context)
        self.assertNotIn('**읽기**', context)
        self.assertEqual(self.invoke(FLOW, event={'cwd': str(self.root)}), {})

    def test_plan_branch_without_key_and_bad_input(self):
        # Lowercase tokens such as utf-8 are not issue keys.
        for branch in ('main', 'feature/demo', 'fix/utf-8-encoding'):
            with self.subTest(branch=branch):
                self.checkout(branch)
                context = self.invoke(FLOW)['hookSpecificOutput']['additionalContext']
                self.assertIn('이슈 키**: 브랜치명에 없음', context)
        result = self.invoke(FLOW, event=[], cwd=self.project)
        self.assertIn('이슈 키**: 브랜치명에 없음', result['hookSpecificOutput']['additionalContext'])

    def test_plan_key_matches_existing_folders_only_as_whole_key(self):
        self.checkout('feature/PROJ-12-demo')
        (self.workspace('feature-proj-12-demo') / 'feedback.md').write_text('# 기록\n')
        self.workspace('PROJ-12-split')
        (self.workspace('PROJ-123') / 'plan.md').write_text('# Other issue\n')
        context = self.invoke(FLOW)['hookSpecificOutput']['additionalContext']
        self.assertIn('/feature-proj-12-demo/` — `feedback.md` 있음', context)
        self.assertIn('/PROJ-12-split/` — 기록 파일 없음', context)
        self.assertNotIn('PROJ-123', context)


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
        # Document names and descriptions live in the index file; the context carries only its path and counts.
        docs_index = self.wiki / '.local/index/sample/demo.md'
        repos_index = self.wiki / '.local/index/sample/demo.repos.md'
        self.assertNotIn('DEMO_DOCUMENT', context)
        self.assertNotIn('contract', context)
        self.assertIn(str(docs_index), context)
        self.assertIn(str(repos_index), context)
        self.assertIn('demo 전용 문서 1건', context)
        self.assertIn('contract — DEMO_DOCUMENT', docs_index.read_text())
        self.assertNotIn('DEMO_RESPONSIBILITY', docs_index.read_text())
        self.assertIn('DEMO_RESPONSIBILITY', repos_index.read_text())

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
