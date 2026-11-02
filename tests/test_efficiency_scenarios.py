"""Executable fixtures and unchanged workflow gates, not an LLM quality grader."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.evaluate import prepare

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/nexus/scripts'))
from nexus_workflow.orchestrator import Orchestrator
from nexus_workflow.store import StateStore, WorkflowError


class EfficiencyScenariosTests(unittest.TestCase):
    def test_suite_prepares_independent_workspaces_and_valid_expectations(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / 'run'
            manifest = prepare(run, 'efficiency-fixtures', 1, ROOT / 'evals/efficiency-suite.json')
            for scenario in manifest['suite']['scenarios']:
                first = run / 'contexts' / scenario['id'] / 'baseline/1/workspace'
                second = run / 'contexts' / scenario['id'] / 'nexus/1/workspace'
                self.assertTrue(first.is_dir())
                self.assertTrue(second.is_dir())
                (first / 'isolation-probe.txt').write_text('one sample only')
                self.assertFalse((second / 'isolation-probe.txt').exists())

    def test_fast_fixtures_fail_before_fix_and_pass_without_artifacts(self):
        for fixture in ('python-name', 'python-name-tracked'):
            with self.subTest(fixture=fixture), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory) / 'workspace'
                shutil.copytree(ROOT / 'evals/fixtures' / fixture, workspace)
                before = {p.name: p.read_bytes() for p in workspace.iterdir()}
                command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', '.', '-v']
                red = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(red.returncode, 0)
                self.assertIn('FAIL:', red.stderr)
                (workspace / 'names.py').write_text('def normalize_name(value):\n    return value.strip()\n')
                green = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=10)
                self.assertEqual(green.returncode, 0, green.stderr)
                self.assertEqual({p.name for p in workspace.iterdir()}, set(before))
                for name, data in before.items():
                    if name != 'names.py':
                        self.assertEqual((workspace / name).read_bytes(), data)

    def test_balanced_executor_resumes_without_rewriting_accepted_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = StateStore(root / '.nexus/local/workflow.json')
            engine = Orchestrator(store)
            engine.initialize(root, mode='BALANCED')
            sequence = 0

            def op(action, **fields):
                nonlocal sequence
                sequence += 1
                return engine.apply(dict(operation_id=f'resume-{sequence}',
                                         expected_revision=store.read()['revision'],
                                         action=action, **fields))

            for kind in ('discovery', 'spec', 'plan'):
                shutil.copyfile(ROOT / 'evals/fixtures/python-name-plan' / f'{kind}.md', root / f'{kind}.md')
                op('artifact', kind=kind, path=f'{kind}.md', revision='1',
                   source='Synthetic accepted fixture', reason='Initial approved contract')
            op('create', task_id='T1', title='Resume accepted increment', goal='Fixture verification',
               criteria=['Observed result'], owner='main', role='implementer', resources=['file:names.py'],
               authorization='Synthetic test only',
               strategy={'kind': 'test-after', 'reason': 'Known local fixture'})
            artifacts = json.loads(json.dumps(store.read()['artifacts']))
            fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.md')}
            # A new coordinator reads the existing state; no re-registration or new store.
            engine = Orchestrator(StateStore(store.path))
            op('ready', task_id='T1')
            state = op('start', task_id='T1')
            op('result', task_id='T1', run_id=state['tasks']['T1']['run']['id'],
               outcome='success', source='Synthetic host receipt', summary='State-contract test')
            with self.assertRaises(WorkflowError):
                op('complete', task_id='T1')
            op('evidence', task_id='T1', kind='test', outcome='passed',
               source='Synthetic state-machine test', detail='Declared evidence, not consumer execution')
            op('evidence', task_id='T1', kind='acceptance', outcome='passed', criteria=[0],
               source='Synthetic state-machine test', detail='Declared evidence, not consumer execution')
            op('complete', task_id='T1')
            op('deliver', source='Synthetic state-machine test', memory='not-needed', reason='No durable learning')
            self.assertEqual(store.read()['status'], 'delivered')
            self.assertEqual(store.read()['artifacts'], artifacts)
            self.assertEqual({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.md')},
                             fingerprints)


if __name__ == '__main__':
    unittest.main()
