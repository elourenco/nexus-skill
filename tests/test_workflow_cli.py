"""Subprocess acceptance tests for the replaceable presentation adapter."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/nexus/scripts/workflow.py'


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state.json'

    def call(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(CLI), '--state', str(self.state), *args],
            input=stdin, text=True, capture_output=True, cwd=self.root, timeout=15)

    def init(self):
        result = self.call('init', '--workspace', str(self.root), '--mode', 'FAST')
        self.assertEqual(result.returncode, 0, result.stderr)

    def apply(self, action, **data):
        state = json.loads(self.state.read_text())
        return self.call('apply', '--request', '-', stdin=json.dumps(dict(
            operation_id=f'cli-{state["revision"]}', expected_revision=state['revision'], action=action, **data)))

    def test_cli_mutations_are_reflected_in_markdown_json_and_history(self):
        self.init()
        created = self.apply('create', task_id='CLI-1', title='Fix | title\nline', goal='Observed behavior',
            criteria=['One result'], owner='main', role='implementer', resources=['file:a.py'],
            authorization='user request', strategy={'kind':'test-after','reason':'Low risk'})
        self.assertEqual(created.returncode, 0, created.stderr)
        blocked = self.apply('block', task_id='CLI-1', reason='Missing input', next_action='Collect source')
        self.assertEqual(blocked.returncode, 0, blocked.stderr)
        projection = self.call('show')
        self.assertEqual(projection.returncode, 0, projection.stderr)
        self.assertIn('blocked', projection.stdout)
        self.assertIn('Missing input', projection.stdout)
        self.assertIn('Collect source', projection.stdout)
        state = json.loads(self.call('show', '--format', 'json').stdout)
        self.assertEqual(state['tasks']['CLI-1']['status'], 'blocked')
        history = json.loads(self.call('history', '--task', 'CLI-1').stdout)
        self.assertEqual([event['action'] for event in history], ['create', 'block'])
        self.assertIsNone(json.loads(self.call('metrics').stdout)['actual_usage'])

    def test_invalid_input_returns_nonzero_without_mutation(self):
        self.init()
        before = self.state.read_bytes()
        invalid = self.call('apply', '--request', '-', stdin='{"broken":')
        self.assertNotEqual(invalid.returncode, 0)
        self.assertEqual(before, self.state.read_bytes())

    def test_large_integer_budget_does_not_overflow_float_conversion(self):
        self.init()
        result = self.apply('budget', limit=10 ** 400, unit='tokens', source='Synthetic boundary case')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_template_export_does_not_require_store_or_modify_source(self):
        result = self.call('template', 'task')
        self.assertEqual(result.returncode, 0, result.stderr)
        original = (ROOT / 'skills/nexus/assets/templates/task.md').read_text()
        self.assertEqual(result.stdout, original)
        self.assertFalse(self.state.exists())

    def test_demo_executes_real_red_green_and_delivery(self):
        demo = self.call('demo', '--output-dir', str(self.root / 'demo'))
        self.assertEqual(demo.returncode, 0, demo.stderr)
        report = json.loads(demo.stdout)
        self.assertNotEqual(report['red_exit_code'], 0)
        self.assertEqual(report['green_exit_code'], 0)
        saved = json.loads(Path(report['state']).read_text())
        self.assertEqual(saved['status'], 'delivered')
        self.assertEqual(saved['tasks']['DEMO-1']['status'], 'done')
        self.assertTrue(Path(report['todo']).is_file())
        self.assertEqual(len(saved['history']), report['revision'])


if __name__ == '__main__':
    unittest.main()
