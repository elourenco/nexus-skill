"""Release ordering and recovery with real Git history and an in-memory GitHub API."""
import base64
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from pathlib import Path

from scripts.release import GitHub, publish, verify_remote_tag


class FakeGitHub:
    def __init__(self, root):
        self.root = root
        self.releases = {}
        self.calls = []
        self.fail_release = False
        self.fail_promotion = False
        self.lose_promotion_response = False
        self.race_promotion = False
        self.remote_tags = {}
        self.remote_only_tags = False

    def git(self, *args, input=None, env=None):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True,
                                       input=input, env=env, stderr=subprocess.PIPE).strip()

    def request(self, method, path, data=None):
        self.calls.append((method, path, data))
        if method == 'GET':
            if path.startswith('releases/tags/'):
                return self.releases.get(path.removeprefix('releases/tags/'))
            if path.startswith('git/ref/tags/'):
                tag = path.removeprefix('git/ref/tags/')
                sha = self.remote_tags.get(tag) or self.git('rev-parse', f'{tag}^{{commit}}')
                return {'object': {'type': 'commit', 'sha': sha}}
            if path == 'git/ref/heads/plugins':
                try:
                    return {'object': {'sha': self.git('rev-parse', '--verify', 'refs/heads/plugins')}}
                except subprocess.CalledProcessError:
                    return None
            if path.startswith('contents/.nexus-release.json?ref='):
                sha = path.split('=', 1)[1]
                try:
                    content = self.git('show', f'{sha}:.nexus-release.json')
                except subprocess.CalledProcessError:
                    raise RuntimeError('Distribution branch has no provenance') from None
                return {'encoding': 'base64', 'content': base64.b64encode(content.encode()).decode()}
            if path.startswith('git/commits/'):
                sha = path.rsplit('/', 1)[1]
                return {'tree': {'sha': self.git('rev-parse', f'{sha}^{{tree}}')}}
        if path == 'git/trees':
            with tempfile.TemporaryDirectory() as tmp:
                env = {**os.environ, 'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
                self.git('read-tree', data['base_tree'], env=env)
                for item in data['tree']:
                    blob = self.git('hash-object', '-w', '--stdin', input=item['content'])
                    self.git('update-index', '--add', '--cacheinfo', item['mode'], blob,
                             item['path'], env=env)
                return {'sha': self.git('write-tree', env=env)}
        if path == 'git/commits':
            args = ['commit-tree', data['tree'], '-m', data['message']]
            for parent in data['parents']:
                args.extend(['-p', parent])
            return {'sha': self.git(*args)}
        if path == 'git/refs/heads/plugins' or (path == 'git/refs' and data['ref'] == 'refs/heads/plugins'):
            if self.fail_promotion:
                raise RuntimeError('promotion unavailable')
            if method == 'PATCH':
                assert data['force'] is False
                previous = self.git('rev-parse', 'refs/heads/plugins')
                if self.race_promotion:
                    raced = self.git('commit-tree', self.git('rev-parse', f'{previous}^{{tree}}'),
                                     '-p', previous, '-m', 'Concurrent writer')
                    self.git('update-ref', 'refs/heads/plugins', raced, previous)
                    previous = raced
                self.git('merge-base', '--is-ancestor', previous, data['sha'])
                self.git('update-ref', 'refs/heads/plugins', data['sha'], previous)
            else:
                self.git('update-ref', 'refs/heads/plugins', data['sha'], '0' * 40)
            if self.lose_promotion_response:
                raise RuntimeError('promotion response lost')
            return {}
        if path == 'releases/generate-notes':
            return {'body': '## Changes\n* First merge #1\n* Second merge #2'}
        if path == 'git/refs':
            tag = data['ref'].removeprefix('refs/tags/')
            self.remote_tags[tag] = data['sha']
            if not self.remote_only_tags:
                subprocess.run(['git', 'tag', tag, data['sha']], cwd=self.root,
                               check=True, capture_output=True)
            return {}
        if path == 'releases':
            if self.fail_release:
                raise RuntimeError('publication unavailable')
            release = {**data, 'html_url': 'https://example.invalid/release'}
            self.releases[data['tag_name']] = release
            return release
        raise AssertionError(path)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        for host in ('claude', 'codex'):
            path = self.root / f'.{host}-plugin/plugin.json'
            path.parent.mkdir()
            path.write_text(json.dumps({'name': 'nexus', 'version': '0.3.0', 'skills': './skills/'}))
        self.before = self.commit('Foundation')
        workflow = self.root / '.github/workflows/release.yml'
        workflow.parent.mkdir(parents=True)
        workflow.write_text('name: Release\n')
        self.sha = self.commit('Enable releases')
        self.api = FakeGitHub(self.root)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def commit(self, title):
        self.git('add', '.')
        self.git('commit', '-qm', title, '--allow-empty')
        return self.git('rev-parse', 'HEAD')

    def run_release(self, sha=None, before=None):
        return publish(self.root, self.api, sha or self.sha, before or self.before)

    def test_bootstrap_contains_all_generated_merges_and_exact_sha(self):
        self.run_release()
        release = self.api.releases['v0.3.0']
        self.assertIn('#1', release['body'])
        self.assertIn('#2', release['body'])
        self.assertEqual(release['target_commitish'], self.sha)
        self.assertEqual(self.git('rev-parse', 'v0.3.0'), self.sha)
        notes = next(data for _, path, data in self.api.calls if path.endswith('generate-notes'))
        self.assertNotIn('previous_tag_name', notes)

    def test_next_patch_has_explicit_previous_tag(self):
        self.run_release()
        next_sha = self.commit('Merge pull request #3')
        self.run_release(next_sha, self.sha)
        notes = [data for _, path, data in self.api.calls if path.endswith('generate-notes')][-1]
        self.assertEqual(notes['previous_tag_name'], 'v0.3.0')
        self.assertEqual(notes['target_commitish'], next_sha)
        self.assertIn('v0.3.1', self.api.releases)

    def test_rerun_is_noop_even_after_newer_release(self):
        self.run_release()
        next_sha = self.commit('Next merge')
        self.run_release(next_sha, self.sha)
        self.api.calls.clear()
        self.run_release()
        self.assertFalse(any(method == 'POST' for method, _, _ in self.api.calls))

    def test_recovers_tag_created_before_release_failure(self):
        self.api.fail_release = True
        with self.assertRaisesRegex(RuntimeError, 'unavailable'):
            self.run_release()
        self.assertEqual(self.git('rev-parse', 'v0.3.0'), self.sha)
        self.api.fail_release = False
        self.run_release()
        self.assertEqual(list(self.api.releases), ['v0.3.0'])
        self.assertEqual(sum(path == 'git/refs' and data['ref'].startswith('refs/tags/')
                             for _, path, data in self.api.calls), 1)

    def test_out_of_order_bootstrap_waits_for_first_push(self):
        next_sha = self.commit('Next merge arrives first')
        with self.assertRaisesRegex(RuntimeError, 'previous push'):
            self.run_release(next_sha, self.sha)
        self.assertFalse(self.api.calls)
        self.run_release()
        self.run_release(next_sha, self.sha)
        self.assertEqual(len(self.api.releases), 2)

    def test_failed_previous_release_blocks_next_version(self):
        self.api.fail_release = True
        with self.assertRaises(RuntimeError):
            self.run_release()
        next_sha = self.commit('Next merge')
        self.api.fail_release = False
        with self.assertRaisesRegex(RuntimeError, 'previous release'):
            self.run_release(next_sha, self.sha)
        self.assertNotIn('v0.3.1', self.git('tag').splitlines())

    def test_missing_intermediate_push_cannot_be_skipped(self):
        self.run_release()
        intermediate = self.commit('Intermediate merge')
        newest = self.commit('Newest merge')
        with self.assertRaisesRegex(RuntimeError, 'previous push'):
            self.run_release(newest, intermediate)
        self.run_release(intermediate, self.sha)
        self.run_release(newest, intermediate)
        self.assertEqual(len(self.api.releases), 3)

    def test_unrelated_tag_cannot_be_reused(self):
        self.run_release()
        self.git('checkout', '--orphan', 'other')
        other = self.commit('Unrelated history')
        self.git('tag', 'v9.0.0', other)
        self.git('checkout', '--detach', self.sha)
        next_sha = self.commit('Next merge')
        with self.assertRaisesRegex(RuntimeError, 'ancestor'):
            self.run_release(next_sha, self.sha)

    def test_multiple_tags_on_target_fail_closed(self):
        self.git('tag', 'v0.3.0')
        self.git('tag', 'v0.3.1')
        with self.assertRaisesRegex(RuntimeError, 'Multiple'):
            self.run_release()

    def test_empty_notes_fail_before_tag_creation(self):
        original = self.api.request

        def empty_notes(method, path, data=None):
            if path == 'releases/generate-notes':
                return {'body': ''}
            return original(method, path, data)

        self.api.request = empty_notes
        with self.assertRaisesRegex(RuntimeError, 'notes'):
            self.run_release()
        self.assertEqual(self.git('tag'), '')

    def test_explicit_recovery_releases_corrected_snapshot_after_failed_ci(self):
        self.run_release()
        self.commit('Broken CI')
        corrected = self.commit('Fix CI')
        publish(self.root, self.api, corrected, corrected, recover_from='v0.3.0')
        self.assertEqual(self.git('rev-parse', 'v0.3.1'), corrected)
        notes = [data for _, path, data in self.api.calls if path.endswith('generate-notes')][-1]
        self.assertEqual(notes['previous_tag_name'], 'v0.3.0')

    def test_explicit_recovery_can_bootstrap_after_failed_initial_ci(self):
        corrected = self.commit('Fix initial CI')
        publish(self.root, self.api, corrected, corrected, recover_from='initial')
        self.assertEqual(self.git('rev-parse', 'v0.3.0'), corrected)

    def test_recovery_refuses_stale_base(self):
        self.run_release()
        corrected = self.commit('Fix CI')
        self.api.calls.clear()
        with self.assertRaisesRegex(RuntimeError, 'Recovery base'):
            publish(self.root, self.api, corrected, corrected, recover_from='v0.2.0')
        self.assertFalse(self.api.calls)

    def distribution(self, path):
        return json.loads(self.git('show', f'refs/heads/plugins:{path}'))

    def test_distributed_versions_follow_release_while_source_tag_stays_exact(self):
        self.run_release()
        next_sha = self.commit('Next release without manual bump')
        self.run_release(next_sha, self.sha)
        for host in ('claude', 'codex'):
            path = f'.{host}-plugin/plugin.json'
            self.assertEqual(self.distribution(path)['version'], '0.3.1')
            self.assertEqual(json.loads(self.git('show', f'v0.3.1:{path}'))['version'], '0.3.0')
        self.assertEqual(self.distribution('.nexus-release.json'), {
            'schema_version': 1, 'source_sha': next_sha, 'tag': 'v0.3.1'})
        paths = self.git('diff', '--name-only', next_sha, 'refs/heads/plugins').splitlines()
        self.assertEqual(paths, ['.claude-plugin/plugin.json', '.codex-plugin/plugin.json', '.nexus-release.json'])

    def test_new_remote_tag_need_not_exist_in_the_local_checkout(self):
        self.api.remote_only_tags = True
        self.run_release()
        self.assertEqual(self.git('tag'), '')
        self.assertEqual(self.api.remote_tags, {'v0.3.0': self.sha})
        self.assertEqual(self.distribution('.nexus-release.json')['source_sha'], self.sha)

    def test_remote_tag_with_wrong_source_blocks_promotion(self):
        self.run_release()
        tip = self.git('rev-parse', 'refs/heads/plugins')
        self.api.remote_tags['v0.3.0'] = self.before
        with self.assertRaisesRegex(RuntimeError, 'Remote distribution tag'):
            self.run_release()
        self.assertEqual(self.git('rev-parse', 'refs/heads/plugins'), tip)

    def test_release_success_then_promotion_failure_recovers_on_rerun(self):
        self.api.fail_promotion = True
        with self.assertRaisesRegex(RuntimeError, 'promotion unavailable'):
            self.run_release()
        self.assertIn('v0.3.0', self.api.releases)
        self.api.fail_promotion = False
        self.run_release()
        self.assertEqual(self.distribution('.nexus-release.json')['source_sha'], self.sha)
        self.assertEqual(sum(path == 'releases' for _, path, _ in self.api.calls), 1)

    def test_promotion_response_lost_reconciles_without_second_write(self):
        self.api.lose_promotion_response = True
        with self.assertRaisesRegex(RuntimeError, 'response lost'):
            self.run_release()
        tip = self.git('rev-parse', 'refs/heads/plugins')
        self.api.lose_promotion_response = False
        self.api.calls.clear()
        self.run_release()
        self.assertEqual(self.git('rev-parse', 'refs/heads/plugins'), tip)
        self.assertFalse(any(method != 'GET' for method, _, _ in self.api.calls))

    def test_old_rerun_never_rolls_back_distribution(self):
        self.run_release()
        next_sha = self.commit('Next release')
        self.run_release(next_sha, self.sha)
        tip = self.git('rev-parse', 'refs/heads/plugins')
        self.run_release()
        self.assertEqual(self.git('rev-parse', 'refs/heads/plugins'), tip)
        self.assertEqual(self.distribution('.nexus-release.json')['tag'], 'v0.3.1')

    def test_foreign_distribution_branch_is_not_overwritten(self):
        self.git('branch', 'plugins', self.sha)
        with self.assertRaisesRegex(RuntimeError, 'provenance'):
            self.run_release()
        self.assertEqual(self.git('rev-parse', 'refs/heads/plugins'), self.sha)

    def test_next_release_waits_for_failed_distribution(self):
        self.api.fail_promotion = True
        with self.assertRaises(RuntimeError):
            self.run_release()
        next_sha = self.commit('Next source commit')
        with self.assertRaisesRegex(RuntimeError, 'promotion unavailable'):
            self.run_release(next_sha, self.sha)
        self.assertNotIn('v0.3.1', self.api.releases)

    def test_manifest_drift_rejected_before_any_publication(self):
        path = self.root / '.codex-plugin/plugin.json'
        path.write_text(json.dumps({'name': 'nexus', 'version': '0.9.0', 'skills': './skills/'}))
        sha = self.commit('Drifted manifest')
        with self.assertRaisesRegex((ValueError, RuntimeError), 'versions'):
            publish(self.root, self.api, sha, sha, recover_from='initial')
        self.assertFalse(any(method != 'GET' for method, _, _ in self.api.calls))

    def test_modified_distribution_tree_is_not_silently_overwritten(self):
        self.run_release()
        previous = self.git('rev-parse', 'refs/heads/plugins')
        unrelated_tree = self.git('rev-parse', f'{self.sha}^{{tree}}')
        foreign = self.api.git('commit-tree', unrelated_tree, '-p', previous, '-m', 'Manual edit')
        self.git('update-ref', 'refs/heads/plugins', foreign, previous)
        with self.assertRaisesRegex(RuntimeError, 'provenance'):
            self.run_release()
        self.assertEqual(self.git('rev-parse', 'refs/heads/plugins'), foreign)

    def test_concurrent_promotion_fails_without_overwriting_other_writer(self):
        self.run_release()
        next_sha = self.commit('Next source commit')
        self.api.race_promotion = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_release(next_sha, self.sha)
        self.assertEqual(self.git('log', '-1', '--format=%s', 'refs/heads/plugins'), 'Concurrent writer')
        self.assertEqual(self.distribution('.nexus-release.json')['tag'], 'v0.3.0')


@unittest.skipUnless(os.environ.get('NEXUS_HOST_UPDATES') == '1', 'Opt-in native host lifecycle')
class NativeHostUpdatesTests(unittest.TestCase):
    def test_remote_branch_update_replaces_both_installed_packages(self):
        from scripts.verify_hosts import discover_skills, EXPECTED

        codex = os.environ.get('NEXUS_CODEX', '/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
        claude = shutil.which('claude')
        self.assertTrue(Path(codex).is_file())
        self.assertIsNotNone(claude)
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='nexus-host-updates-') as temporary:
            base = Path(temporary)
            source = base / 'source'
            source.mkdir()
            for directory in ('skills', '.claude-plugin', '.codex-plugin', '.agents/plugins'):
                shutil.copytree(project / directory, source / directory,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            # Pin fixture versions independently of the development manifest version.
            for host in ('claude', 'codex'):
                manifest_path = source / f'.{host}-plugin/plugin.json'
                manifest = json.loads(manifest_path.read_text())
                manifest_path.write_text(json.dumps({**manifest, 'version': '0.3.0'}, indent=2) + '\n')
            api = FakeGitHub(source)
            api.git('init', '-q', '-b', 'main')
            api.git('config', 'user.name', 'Host lifecycle test')
            api.git('config', 'user.email', 'test@example.invalid')
            api.git('add', '.')
            api.git('commit', '-qm', 'Source fixture')
            before = api.git('rev-parse', 'HEAD')
            workflow = source / '.github/workflows/release.yml'
            workflow.parent.mkdir(parents=True)
            workflow.write_text('name: Release\n')
            api.git('add', '.')
            api.git('commit', '-qm', 'Enable releases')
            first = api.git('rev-parse', 'HEAD')
            publish(source, api, first, before)
            # Exercise HTTPS source parsing and native Git clone/fetch without network.
            gitconfig = base / 'gitconfig'
            api.git('config', '-f', str(gitconfig), f'url.{source.as_uri()}.insteadOf',
                    'https://example.invalid/nexus.git')
            api.git('config', '-f', str(gitconfig), 'protocol.file.allow', 'always')
            consumer = base / 'consumer'
            consumer.mkdir()
            state = consumer / '.nexus/local/workflow.json'
            state.parent.mkdir(parents=True)
            state.write_text('{"preserve":"consumer state"}\n')
            env = {**os.environ, 'CODEX_HOME': str(base / 'codex'),
                   'CLAUDE_CONFIG_DIR': str(base / 'claude'), 'GIT_CONFIG_GLOBAL': str(gitconfig),
                   'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0', 'NO_COLOR': '1'}
            Path(env['CODEX_HOME']).mkdir()
            Path(env['CLAUDE_CONFIG_DIR']).mkdir()

            def call(host, *args):
                result = subprocess.run([host, *args], cwd=consumer, env=env,
                                        text=True, capture_output=True, timeout=60)
                self.assertEqual(result.returncode, 0, f'{args}: {result.stdout}\n{result.stderr}')
                return result.stdout

            def installed_version(host):
                listing = json.loads(call(host, 'plugin', 'list', '--json'))
                if host == claude:
                    return next(p['version'] for p in listing if p['id'] == 'nexus@nexus-local')
                # Inspect the package actually loaded, rather than any stale cache entry.
                discovered = discover_skills(codex, consumer, env)
                self.assertEqual(len(discovered), 6)
                versions = set()
                for skill in discovered:
                    manifest = next(parent / '.codex-plugin/plugin.json'
                                    for parent in Path(skill['path']).parents
                                    if (parent / '.codex-plugin/plugin.json').is_file())
                    versions.add(json.loads(manifest.read_text())['version'])
                self.assertEqual(len(versions), 1)
                return versions.pop()

            call(claude, 'plugin', 'marketplace', 'add', 'https://example.invalid/nexus.git#plugins')
            call(claude, 'plugin', 'install', 'nexus@nexus-local')
            call(codex, 'plugin', 'marketplace', 'add', 'https://example.invalid/nexus.git', '--ref', 'plugins', '--json')
            call(codex, 'plugin', 'add', 'nexus@nexus-local', '--json')
            self.assertEqual(installed_version(claude), '0.3.0')
            self.assertEqual(installed_version(codex), '0.3.0')
            api.git('commit', '-qm', 'Next release', '--allow-empty')
            second = api.git('rev-parse', 'HEAD')
            publish(source, api, second, first)
            call(claude, 'plugin', 'marketplace', 'update', 'nexus-local')
            call(claude, 'plugin', 'update', 'nexus@nexus-local')
            call(codex, 'plugin', 'marketplace', 'upgrade', 'nexus-local', '--json')
            call(codex, 'plugin', 'add', 'nexus@nexus-local', '--json')
            self.assertEqual(installed_version(claude), '0.3.1')
            self.assertEqual(installed_version(codex), '0.3.1')
            inventory = call(claude, 'plugin', 'details', 'nexus@nexus-local')
            match = re.search(r'^\s*Skills \((\d+)\)\s+(.+)$', inventory, re.MULTILINE)
            self.assertIsNotNone(match, inventory)
            self.assertEqual(int(match[1]), 6)
            self.assertEqual({n.strip() for n in match[2].split(',')}, EXPECTED)
            discovered = discover_skills(codex, consumer, env)
            self.assertEqual({s['name'].split(':')[-1] for s in discovered}, EXPECTED)
            self.assertTrue(all(s['enabled'] and '/0.3.1/' in s['path'] for s in discovered))
            self.assertEqual(state.read_text(), '{"preserve":"consumer state"}\n')
            print('Native updates: Claude and Codex 0.3.0 → 0.3.1; six current entries; consumer state preserved')


class DistributedPackageTests(unittest.TestCase):
    def test_complete_generated_package_passes_validation_and_preserves_skill_bytes(self):
        from scripts.validate import validate

        project = Path(__file__).resolve().parents[1]
        files = subprocess.check_output(['git', 'ls-files', '--cached', '--others',
                                         '--exclude-standard', '-z'], cwd=project).decode().split('\0')
        with tempfile.TemporaryDirectory(prefix='nexus-distributed-package-') as temporary:
            base = Path(temporary)
            source = base / 'source'
            source.mkdir()
            for relative in sorted(set(files) - {''}):
                original = project / relative
                if not original.is_file():
                    continue
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target, follow_symlinks=False)
            api = FakeGitHub(source)
            api.git('init', '-q', '-b', 'main')
            api.git('config', 'user.name', 'Package test')
            api.git('config', 'user.email', 'test@example.invalid')
            api.git('add', '.')
            api.git('commit', '-qm', 'Complete source package')
            sha = api.git('rev-parse', 'HEAD')
            api.remote_only_tags = True
            publish(source, api, sha, sha, recover_from='initial')
            archive = base / 'snapshot.tar'
            api.git('archive', '--format=tar', '--output', str(archive), 'refs/heads/plugins')
            installed = base / 'installed'
            installed.mkdir()
            with tarfile.open(archive) as package:
                package.extractall(installed, filter='data')
            self.assertEqual(validate(installed), [])
            for original in (source / 'skills').rglob('*'):
                if original.is_file():
                    self.assertEqual((installed / original.relative_to(source)).read_bytes(), original.read_bytes())


class GitHubTransportTests(unittest.TestCase):
    def test_only_missing_release_or_distribution_branch_404_means_absent(self):
        api = GitHub('owner/repo', 'synthetic')
        for method, path, status, absent in [('GET', 'releases/tags/v0.3.0', 404, True),
                                             ('GET', 'git/ref/heads/plugins', 404, True),
                                             ('GET', 'git/ref/heads/plugins', 403, False),
                                             ('GET', 'git/ref/tags/v0.3.0', 404, False),
                                             ('GET', 'releases/tags/v0.3.0', 403, False),
                                             ('GET', 'releases/tags/v0.3.0', 500, False),
                                             ('POST', 'releases', 404, False)]:
            with self.subTest(method=method, status=status):
                error = HTTPError('https://example.invalid', status, 'failure', {}, None)
                with patch('scripts.release.urlopen', side_effect=error) as send:
                    if absent:
                        self.assertIsNone(api.request(method, path))
                    else:
                        with self.assertRaises(RuntimeError):
                            api.request(method, path)
                    self.assertEqual(send.call_count, 1)

    def test_remote_annotated_tag_resolves_to_source_commit(self):
        api = GitHub('owner/repo', 'synthetic')
        replies = [
            {'object': {'type': 'tag', 'sha': 'a' * 40}},
            {'object': {'type': 'commit', 'sha': 'b' * 40}},
        ]
        with patch.object(api, 'request', side_effect=replies):
            verify_remote_tag(api, 'v0.3.0', 'b' * 40)
        with patch.object(api, 'request', side_effect=replies):
            with self.assertRaisesRegex(RuntimeError, 'source commit'):
                verify_remote_tag(api, 'v0.3.0', 'c' * 40)

    def test_uncertain_write_is_never_retried(self):
        with patch('scripts.release.urlopen', side_effect=URLError('timeout')) as send:
            with self.assertRaises(URLError):
                GitHub('owner/repo', 'synthetic').request('POST', 'releases', {})
            self.assertEqual(send.call_count, 1)


if __name__ == '__main__':
    unittest.main()
