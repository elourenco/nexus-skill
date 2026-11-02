"""A copied skill runs against a separate disposable consumer, without cache writes."""
import hashlib
import json
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1] / 'skills/nexus'


class ConsumerDemoTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def execute(self, package=PACKAGE, output=None):
        return subprocess.run([sys.executable, str(package / 'scripts/consumer_demo.py'),
            '--output-dir', str(output or self.root / 'consumer')], cwd=self.root,
            capture_output=True, text=True, timeout=30)

    @staticmethod
    def tree(path):
        return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in path.rglob('*') if p.is_file()}

    def test_consumer_observes_failed_stale_and_recovered_gates_and_mutation(self):
        run = self.execute()
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['red']['gate'], 'block')
        self.assertEqual(report['red']['tests'], 'failed')
        self.assertTrue(report['failed_receipt_rejected'])
        self.assertTrue(report['failed_completion_rejected'])
        self.assertTrue(report['stale_delivery_rejected'])
        self.assertEqual(report['green']['mutation'], 'passed')
        self.assertEqual(report['status'], 'delivered')
        consumer = self.root / 'consumer'
        state = json.loads((consumer / '.nexus/local/workflow.json').read_text())
        self.assertEqual(state['tasks']['DEMO-1']['generation'], 1)
        self.assertEqual(state['tasks']['DEMO-1']['attempts'], 2)
        self.assertEqual(state['status'], 'delivered')
        with closing(sqlite3.connect(consumer / '.nexus/local/hooks.sqlite')) as db:
            results = [json.loads(row[0]) for row in db.execute('SELECT result FROM events ORDER BY rowid')]
        self.assertEqual([r['gate'] for r in results], ['block', 'pass', 'pass'])
        self.assertFalse(list(consumer.rglob('__pycache__')))

    def test_existing_output_is_never_modified(self):
        output = self.root / 'existing'
        output.mkdir()
        (output / 'user.txt').write_text('keep')
        before = self.tree(output)
        run = self.execute(output=output)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(self.tree(output), before)

    def test_relocated_package_is_read_only_and_cwd_remains_consumer(self):
        package = self.root / 'installed/nexus'
        shutil.copytree(PACKAGE, package, ignore=shutil.ignore_patterns('__pycache__'))
        before = self.tree(package)
        for path in package.rglob('*'):
            path.chmod(0o555 if path.is_dir() else 0o444)
        package.chmod(0o555)
        self.addCleanup(self.restore_modes, package)
        run = self.execute(package=package)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(before, self.tree(package))
        self.assertFalse(list(package.rglob('__pycache__')))
        self.assertFalse((self.root / '.nexus').exists())

    @staticmethod
    def restore_modes(root):
        root.chmod(0o755)
        for path in root.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)

    def test_mutation_runner_kills_real_operator_change_and_detects_survivor(self):
        run = self.execute()
        self.assertEqual(run.returncode, 0, run.stderr)
        consumer = self.root / 'consumer'
        source = consumer / 'shipping.py'
        before = source.read_bytes()
        command = [sys.executable, '-B', 'checks.py', 'mutation', '--min-killed', '1']
        killed = subprocess.run(command, cwd=consumer, capture_output=True, text=True, timeout=10)
        self.assertEqual(killed.returncode, 0, killed.stderr)
        self.assertEqual(json.loads(killed.stdout)['killed'], 1)
        self.assertEqual(source.read_bytes(), before)
        tests = consumer / 'test_shipping.py'
        tests.write_text(tests.read_text().replace('eligible(100)', 'eligible(101)'))
        survived = subprocess.run(command, cwd=consumer, capture_output=True, text=True, timeout=10)
        self.assertEqual(survived.returncode, 1, survived.stderr)
        self.assertEqual(json.loads(survived.stdout)['killed'], 0)
        self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
