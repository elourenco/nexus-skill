"""Review packages must represent the actual target, including local work."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/nexus/scripts/review_package.py'


class ReviewPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Synthetic fixture')
        (self.repo / 'app.py').write_text('value = 1\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def run_package(self, *args, ok=True):
        import sys
        result = subprocess.run([sys.executable, str(SCRIPT), '--workspace', str(self.repo),
                                 '--base', self.base, '--output', str(self.root / 'package'), *args],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        return result

    def manifest(self):
        return json.loads((self.root / 'package/manifest.json').read_text())

    def test_worktree_captures_staged_unstaged_and_explicit_untracked(self):
        (self.repo / 'app.py').write_text('value = 2\n')
        self.git('add', 'app.py')
        (self.repo / 'app.py').write_text('value = 3\n')
        (self.repo / 'new.py').write_text('new = True\n')
        (self.repo / 'ignored.env').write_text('synthetic private data')
        (self.repo / '.gitignore').write_text('*.env\n')
        self.run_package('--include-untracked', '--gap', 'No live service exercised')
        manifest = self.manifest()
        diff = (self.root / 'package/changes.diff').read_text()
        self.assertIn('+value = 3', diff)
        self.assertIn('+new = True', diff)
        self.assertNotIn('synthetic private data', diff)
        self.assertEqual(manifest['base'], self.base)
        self.assertEqual(manifest['mode'], 'worktree')
        self.assertEqual(manifest['gaps'], ['No live service exercised'])
        self.assertEqual(len(manifest['artifact_id']), 64)

    def test_commit_target_ignores_later_dirty_changes(self):
        (self.repo / 'app.py').write_text('value = 2\n')
        self.git('commit', '-qam', 'change')
        head = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'app.py').write_text('value = 999\n')
        self.run_package('--head', head)
        diff = (self.root / 'package/changes.diff').read_text()
        self.assertIn('+value = 2', diff)
        self.assertNotIn('999', diff)
        self.assertEqual(self.manifest()['head'], head)

    def test_untracked_omission_is_explicit_and_attachments_are_hashed(self):
        (self.repo / 'new.py').write_text('new = True\n')
        brief = self.root / 'brief.md'
        brief.write_text('Synthetic requirement')
        self.run_package('--brief', str(brief))
        manifest = self.manifest()
        self.assertEqual(manifest['omitted_untracked'], ['new.py'])
        self.assertEqual(manifest['attachments'][0]['kind'], 'brief')
        saved = self.root / 'package' / manifest['attachments'][0]['file']
        self.assertEqual(saved.read_text(), 'Synthetic requirement')

    def test_output_is_exclusive(self):
        self.run_package()
        before = (self.root / 'package/manifest.json').read_bytes()
        self.run_package(ok=False)
        self.assertEqual((self.root / 'package/manifest.json').read_bytes(), before)

    def test_rejects_invalid_base_and_external_untracked_symlink(self):
        self.run_package('--base', '--bad-ref', ok=False)
        outside = self.root / 'outside'
        outside.write_text('private')
        (self.repo / 'link').symlink_to(outside)
        self.run_package('--include-untracked', ok=False)
        self.assertFalse((self.root / 'package').exists())

    def test_changes_during_capture_are_rejected(self):
        self.assertTrue(SCRIPT.exists(), 'review collector missing')
        spec = importlib.util.spec_from_file_location('review_package', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.capture
        calls = 0

        def changing(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 1:
                (self.repo / 'app.py').write_text('value = 99\n')
            return result

        with patch.object(module, 'capture', side_effect=changing):
            with self.assertRaisesRegex(module.PackageError, 'changed'):
                module.collect(self.repo, self.base, self.root / 'package')
        self.assertFalse((self.root / 'package').exists())

    def test_large_attachment_is_rejected_before_publication(self):
        large = self.root / 'large'
        large.write_bytes(b'x' * (2 * 1024 * 1024 + 1))
        self.run_package('--evidence', str(large), ok=False)
        self.assertFalse((self.root / 'package').exists())

    def test_repo_fsmonitor_is_not_executed(self):
        monitor = self.root / 'monitor.sh'
        marker = self.root / 'monitor-ran'
        monitor.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
        monitor.chmod(0o700)
        self.git('config', 'core.fsmonitor', str(monitor))
        self.run_package()
        self.assertFalse(marker.exists(), 'collector executed repository fsmonitor')

    def test_untracked_missing_newline_does_not_join_patch_headers(self):
        (self.repo / 'a.txt').write_text('one')
        (self.repo / 'b.txt').write_text('two')
        self.run_package('--include-untracked')
        diff = (self.root / 'package/changes.diff').read_text()
        self.assertIn('+one\n\\ No newline at end of file\n', diff)
        self.assertNotIn('+one---', diff)

    def test_worktree_filter_cannot_execute_or_hide_changes(self):
        cleaner = self.root / 'clean.sh'
        marker = self.root / 'filter-ran'
        cleaner.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\ncat >/dev/null\nprintf "value = 1\\n"\n')
        cleaner.chmod(0o700)
        (self.repo / '.gitattributes').write_text('app.py filter=hide\n')
        self.git('config', 'filter.hide.clean', str(cleaner))
        (self.repo / 'app.py').write_text('value = 999\n')
        self.run_package(ok=False)
        self.assertFalse(marker.exists(), 'collector executed a clean filter')
        self.assertFalse((self.root / 'package').exists())


if __name__ == '__main__':
    unittest.main()
