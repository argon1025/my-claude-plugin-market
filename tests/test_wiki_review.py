"""Exercise the same review collector and state transitions used by the update skill."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wiki_review_fixture import DOMAIN, GIT_ENV, create_fixture, git, json_file


SCRIPTS = Path(__file__).resolve().parents[1] / 'agent-wiki' / 'scripts'
REVIEW = SCRIPTS / 'collect_update_review.py'
MERGES = SCRIPTS / 'collect_update_merges.py'
PUBLICATION = SCRIPTS / 'check_update_publication.py'


class UpdateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='wiki-review-input-')
        cls.addClassCleanup(cls.shared.cleanup)
        cls.fixture = create_fixture(Path(cls.shared.name))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wiki-review-run-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wiki = self.root / 'wiki'
        git(self.root, 'clone', '-q', str(self.fixture / 'wiki'), str(self.wiki))
        self.out = self.root / 'work'
        self.config = self.root / 'config.json'
        self.config.write_bytes((self.fixture / 'config.json').read_bytes())
        self.feed = self.root / 'decisions.json'
        self.feed.write_bytes((self.fixture / 'decisions.json').read_bytes())
        self.state = self.wiki / 'state' / 'review' / f'{DOMAIN}.json'

    def run_cli(self, *args, expected=0):
        run = subprocess.run([sys.executable, *map(str, args)], env=GIT_ENV, text=True,
                             capture_output=True, timeout=30)
        self.assertEqual(run.returncode, expected, run.stderr + run.stdout)
        return run

    def collect(self, *args, expected=0):
        self.run_cli(REVIEW, '--wiki', self.wiki, '--workspace', self.root / 'workspace',
                     '--domain', DOMAIN, '--out', self.out, '--config', self.config,
                     '--decision-feed', self.feed, *args, expected=expected)
        return json.loads((self.out / 'review.json').read_text())

    def finalize(self, *keys, expected=0):
        return self.run_cli(REVIEW, '--wiki', self.wiki, '--domain', DOMAIN, '--out', self.out,
                            '--finalize', ','.join(keys), expected=expected)

    def test_legacy_merge_range(self):
        def run_merges(expected):
            self.run_cli(MERGES, '--wiki', self.wiki, '--workspace', self.root / 'workspace',
                         '--domain', DOMAIN, '--out', self.out, expected=expected)
            return json.loads((self.out / 'work.json').read_text())

        before = run_merges(0)
        self.assertEqual([row['slug'] for row in before['order']], ['batch-api'])
        row = before['repos']['batch-api']['commits'][0]
        self.assertEqual(row['parents'], 2)
        self.assertIn('lockerId', Path(row['parts'][0]['path']).read_text())
        json_file(self.wiki / 'state' / 'batch-api.json', {'cursor': row['sha']})
        self.assertEqual(run_merges(10)['order'], [])

    def test_legacy_unset_cursor_still_bootstraps(self):
        cursor = self.wiki / 'state' / 'batch-api.json'
        json_file(cursor, {'cursor': None})
        cmd = [MERGES, '--wiki', self.wiki, '--workspace', self.root / 'workspace',
               '--domain', DOMAIN, '--out', self.out]
        self.run_cli(*cmd, expected=20)
        work = json.loads((self.out / 'work.json').read_text())
        self.assertIn('batch-api', work['unset'])
        self.run_cli(*cmd, '--start', 'batch-api=HEAD')
        work = json.loads((self.out / 'work.json').read_text())
        self.assertTrue(work['repos']['batch-api']['bootstrapped'])
        cursor.write_text('{')
        self.run_cli(*cmd, expected=1)
        self.assertIn('batch-api', json.loads((self.out / 'work.json').read_text())['skipped'])

    def test_first_merge_zero_still_collects_decisions_and_review(self):
        tip = git(self.fixture / 'services' / 'batch-api', 'rev-parse', 'HEAD')
        json_file(self.wiki / 'state' / 'batch-api.json', {'cursor': tip})
        git(self.wiki, 'commit', '-qam', 'mark service merge as applied')
        result = self.collect('--paths', 'merges,decisions,wiki,code,docs', '--max-code', '1', '--max-docs', '1')
        self.assertFalse(result['sources']['merges']['items'])
        for src in ('code', 'docs', 'decisions', 'wiki'):
            self.assertTrue(result['sources'][src]['items'], src)
        self.assertIn('MARKET-17#42', json.dumps(result['sources']['decisions'], ensure_ascii=False))
        self.assertFalse(git(self.wiki, 'status', '--porcelain'))

    def test_independent_rotation_and_topic_only(self):
        args = ('--paths', 'code,docs', '--max-code', '1', '--max-docs', '1')
        first = self.collect(*args)
        first_code = first['proposed']['code']
        first_doc = first['proposed']['docs']
        self.assertIn('archive', first_code)
        self.assertEqual(first_doc, 'batch-api/export-batch.md')
        self.finalize('code', 'docs')
        cursors = {p.name: p.read_bytes() for p in (self.wiki / 'state').glob('*.json')}
        git(self.wiki, 'commit', '-qam', 'integrate reviewed rotation')
        state = self.state.read_bytes()
        topic = self.collect('--topic', '배송 증빙')
        self.assertFalse(topic['proposed'])
        self.assertEqual(state, self.state.read_bytes())
        path = 'knowledge/market/batch-api/export-batch.md'
        direct = self.collect('--topic', path)
        self.assertIn(path, [item['path'] for item in direct['sources']['topic']['items']])
        self.assertFalse(direct['proposed'])
        self.assertEqual(cursors, {p.name: p.read_bytes() for p in (self.wiki / 'state').glob('*.json')})
        second = self.collect(*args)
        self.assertEqual(second['proposed']['code'], 'batch-api/src/notice.py')
        self.assertEqual(second['proposed']['docs'], 'batch-api/export-replay.md')
        for path in ('code', 'docs'):
            self.assertNotEqual(first['proposed'][path], second['proposed'][path], path)
            self.assertEqual(len(second['sources'][path]['items']), 1)

    def test_incomplete_query_preserves_cursor_but_other_sources_continue(self):
        for response in ({'error': 'mock connection lost'},
                         {'scope': 'project = MARKET', 'from': None, 'through': 'r5', 'complete': False, 'records': []},
                         {'scope': 'project = MARKET', 'from': 'wrong checkpoint', 'through': 'r5', 'complete': True, 'records': []},
                         {'scope': 'project = OTHER', 'from': None, 'through': 'r5', 'complete': True, 'records': []}):
            with self.subTest(response=response):
                json_file(self.feed, {'refund-board': response})
                result = self.collect('--paths', 'decisions,wiki', expected=1)
                self.assertTrue(result['sources']['decisions']['errors'])
                self.assertNotIn('decisions:refund-board', result['proposed'])
                self.assertTrue(result['sources']['wiki']['items'])
                self.assertFalse(git(self.wiki, 'status', '--porcelain'))

    def test_empty_first_wiki_window_records_a_baseline_once(self):
        state = json.loads(self.state.read_text())
        del state['wiki']
        json_file(self.state, state)
        git(self.wiki, 'commit', '-qam', 'bootstrap wiki change collection')
        first = self.collect('--paths', 'wiki')
        self.assertFalse(first['sources']['wiki']['items'])
        self.assertEqual(first['proposed']['wiki'], git(self.wiki, 'rev-parse', 'HEAD'))
        self.finalize('wiki')
        git(self.wiki, 'commit', '-qam', 'record successfully checked range')
        second = self.collect('--paths', 'wiki')
        self.assertFalse(second['sources']['wiki']['items'])
        self.assertFalse(second['proposed'])

    def test_unavailable_service_is_an_error_even_when_other_sources_succeed(self):
        reg = self.wiki / 'registry.json'
        data = json.loads(reg.read_text())
        data['domains'][DOMAIN]['repos']['batch-api']['remote'] = str(self.root / 'unavailable')
        json_file(reg, data)
        git(self.wiki, 'commit', '-qam', 'service mirror unavailable')
        cursor_path = self.wiki / 'state' / 'batch-api.json'
        previous = cursor_path.read_bytes()
        result = self.collect('--paths', 'merges,docs', expected=1)
        self.assertTrue(result['sources']['merges']['errors'])
        self.assertNotIn('merges:batch-api', result['proposed'])
        self.assertTrue(result['sources']['docs']['items'])
        self.finalize('docs')
        self.assertEqual(previous, cursor_path.read_bytes())

    def test_publish_guard_with_open_pr_and_landed_topic(self):
        remote = self.root / 'remote.git'
        git(self.root, 'clone', '--bare', '-q', str(self.fixture / 'wiki'), str(remote))
        git(self.wiki, 'remote', 'set-url', 'origin', str(remote))
        base = git(self.wiki, 'rev-parse', 'HEAD')
        pulls = self.root / 'open-prs.json'

        def guard(base_sha, *flags, expected=0):
            return self.run_cli(PUBLICATION, '--wiki', self.wiki, '--base', base_sha, '--base-branch', 'main',
                                '--open-prs', pulls, *flags, expected=expected)

        json_file(pulls, {'complete': False, 'pulls': []})
        guard(base, expected=1)
        json_file(pulls, {'complete': True, 'pulls': []})
        guard(base)
        guard(base, '--ready', expected=10)
        branch = 'wiki-update/' + DOMAIN + '-' + base
        git(self.wiki, 'switch', '-qc', branch)
        doc = self.wiki / 'knowledge' / DOMAIN / 'refund-window.md'
        doc.write_text(doc.read_text().replace('3일', '8일').replace('규격 v1 §1', 'MARKET-17#42'))
        guard(base, '--ready', expected=1)
        git(self.wiki, 'commit', '-qam', '온라인 환불 결정 원문 반영')
        guard(base, '--ready')
        manual = {'head': 'wiki-add/decision', 'base': 'main', 'sha': 'example-head',
                  'url': 'https://host.example.invalid/market/pull/9'}
        json_file(pulls, {'complete': True, 'pulls': [manual]})
        guard(base, '--ready', expected=1)
        compared = self.root / 'compared.json'
        same = {'sha': manual['sha'], 'overlap': True, 'reason': '동일 대상의 환불 8일 결정을 반영'}
        json_file(compared, {manual['url']: same})
        self.assertIn(manual['url'], guard(base, '--ready', '--compared', compared, expected=10).stdout)
        json_file(compared, {manual['url']: {**same, 'sha': 'old'}})
        guard(base, '--ready', '--compared', compared, expected=1)
        json_file(compared, {manual['url']: {**same, 'overlap': False, 'reason': '다른 도메인의 배송 규격'}})
        guard(base, '--ready', '--compared', compared)
        git(self.wiki, 'push', '-q', 'origin', branch)
        url = 'https://host.example.invalid/market/pull/1'
        json_file(pulls, {'complete': True, 'pulls': [{'head': branch, 'base': 'main', 'url': url}]})
        self.assertIn(url, guard(base, expected=10).stdout)
        self.assertIn(url, guard(base, '--ready', expected=10).stdout)

        # In this local bare remote the mock host fast-forwards the accepted PR.
        git(self.wiki, 'push', '-q', 'origin', 'HEAD:main')
        git(self.wiki, 'fetch', '-q', 'origin', 'refs/heads/main:refs/remotes/origin/main')
        landed = git(self.wiki, 'rev-parse', 'origin/main')
        self.assertNotEqual(base, landed)
        json_file(pulls, {'complete': True, 'pulls': []})
        guard(base, '--ready', expected=1)
        git(self.wiki, 'switch', '-q', '--detach', landed)
        topic = self.collect('--topic', '환불')
        self.assertTrue(topic['sources']['topic']['items'])
        self.assertFalse(topic['proposed'])
        self.assertFalse(git(self.wiki, 'status', '--porcelain'))
        guard(landed, '--ready', expected=10)

    def test_confirmed_ranges_are_not_proposed_twice(self):
        args = ('--paths', 'merges,decisions,wiki')
        first = self.collect(*args)
        self.assertIn('merges:batch-api', first['proposed'])
        self.finalize(*first['proposed'])
        git(self.wiki, 'add', 'state')
        git(self.wiki, 'commit', '-qm', 'land proposal in base')
        json_file(self.feed, {'refund-board': {'scope': 'project = MARKET', 'from': 'r5', 'through': 'r5',
                                              'complete': True, 'records': []}})
        second = self.collect(*args)
        for source in ('merges', 'decisions', 'wiki'):
            self.assertFalse(second['sources'][source]['items'], source)
        self.assertFalse(second['proposed'])
        scope = 'project = REPLACEMENT'
        json_file(self.config, {'decisionSources': {DOMAIN: {'refund-board': scope}}})
        json_file(self.feed, {'refund-board': {'scope': scope, 'from': 'r5', 'through': 'r6',
                                              'complete': True, 'records': []}})
        renamed = self.collect('--paths', 'decisions', expected=1)
        self.assertIn('저장된 결정 조회 범위', renamed['sources']['decisions']['errors'][0])
        self.assertFalse(renamed['proposed'])
