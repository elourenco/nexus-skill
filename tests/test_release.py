"""Release ordering and recovery with real Git history and an in-memory GitHub API."""
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from pathlib import Path

from scripts.release import GitHub, publish


class FakeGitHub:
    def __init__(self, root):
        self.root = root
        self.releases = {}
        self.calls = []
        self.fail_release = False

    def request(self, method, path, data=None):
        self.calls.append((method, path, data))
        if method == 'GET':
            return self.releases.get(path.removeprefix('releases/tags/'))
        if path == 'releases/generate-notes':
            return {'body': '## Changes\n* First merge #1\n* Second merge #2'}
        if path == 'git/refs':
            subprocess.run(['git', 'tag', data['ref'].removeprefix('refs/tags/'),
                            data['sha']], cwd=self.root, check=True, capture_output=True)
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
        path = self.root / '.claude-plugin/plugin.json'
        path.parent.mkdir()
        path.write_text(json.dumps({'version': '0.3.0'}))
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
        self.assertEqual(sum(path == 'git/refs' for _, path, _ in self.api.calls), 1)

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


class GitHubTransportTests(unittest.TestCase):
    def test_only_release_lookup_404_means_missing(self):
        api = GitHub('owner/repo', 'synthetic')
        for method, path, status in [('GET', 'releases/tags/v0.3.0', 404),
                                     ('GET', 'releases/tags/v0.3.0', 403),
                                     ('GET', 'releases/tags/v0.3.0', 500),
                                     ('POST', 'releases', 404)]:
            with self.subTest(method=method, status=status):
                error = HTTPError('https://example.invalid', status, 'failure', {}, None)
                with patch('scripts.release.urlopen', side_effect=error) as send:
                    if method == 'GET' and status == 404:
                        self.assertIsNone(api.request(method, path))
                    else:
                        with self.assertRaises(RuntimeError):
                            api.request(method, path)
                    self.assertEqual(send.call_count, 1)

    def test_uncertain_write_is_never_retried(self):
        with patch('scripts.release.urlopen', side_effect=URLError('timeout')) as send:
            with self.assertRaises(URLError):
                GitHub('owner/repo', 'synthetic').request('POST', 'releases', {})
            self.assertEqual(send.call_count, 1)


if __name__ == '__main__':
    unittest.main()
