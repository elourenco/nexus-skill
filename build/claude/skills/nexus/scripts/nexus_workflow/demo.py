"""Synthetic demonstration. The host is local Python, not a simulated LLM."""
import json
import subprocess
import sys
from pathlib import Path

from .orchestrator import Orchestrator, require
from .presentation import markdown, metrics
from .store import StateStore


def run_demo(directory):
    root = Path(directory).resolve()
    require(not root.exists(), 'Demo output directory must not exist; never overwrite user files')
    root.mkdir(parents=True, mode=0o700)
    (root / '.gitignore').write_text('.nexus/local/\n__pycache__/\n', encoding='utf-8')
    store = StateStore(root / '.nexus/local/workflow.json')
    engine = Orchestrator(store)
    engine.initialize(root, mode='BALANCED')
    sequence = 0

    def op(action, **data):
        nonlocal sequence
        sequence += 1
        return engine.apply(dict(operation_id=f'demo-{sequence}', expected_revision=store.read()['revision'],
                                 action=action, **data))

    artifacts = {
        'discovery': '# Discovery\nConsumer expects whitespace-trimmed case-insensitive labels.\n',
        'spec': '# Spec DEMO revision 1\nNormalize a string with strip and casefold; reject nonstrings with TypeError.\n'
                'Acceptance: normalize("  NEXUS  ") == "nexus"; normalize(None) raises TypeError.\n'
                'Scope: pure local function; no I/O, persistence or shared mutable state.\n',
        'plan': '# Plan DEMO revision 1\nSPEC: spec.md revision 1.\n'
                'DEMO-1: observe regression, implement normalize, run tests, review the small diff, deliver.\n'
                'One task owns labels.py; TDD selected for explicit input/output invariants.\n',
    }
    for kind, content in artifacts.items():
        (root / f'{kind}.md').write_text(content, encoding='utf-8')
        op('artifact', kind=kind, path=f'{kind}.md', revision='1', source='synthetic demo requirements',
           reason='Initial accepted demonstration contract')
    op('create', task_id='DEMO-1', title='Normalize labels', goal='Canonical label from a string',
       owner='local-demo', role='implementer', resources=['file:labels.py'], files=['labels.py', 'test_labels.py'],
       criteria=['Trim and casefold string labels', 'Reject nonstrings with TypeError'],
       authorization='Explicit demo invocation; synthetic files in new directory only',
       strategy={'kind':'tdd','reason':'Small deterministic domain invariants'}, review_required=True)
    (root / 'labels.py').write_text('def normalize(value):\n    return value\n', encoding='utf-8')
    (root / 'test_labels.py').write_text(
        'import unittest\nfrom labels import normalize\n\nclass LabelsTest(unittest.TestCase):\n'
        '    def test_normalizes(self):\n        self.assertEqual(normalize("  NEXUS  "), "nexus")\n'
        '    def test_rejects_nonstring(self):\n        with self.assertRaises(TypeError):\n            normalize(None)\n',
        encoding='utf-8')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', '.', '-v']
    red = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=30)
    (root / 'red.txt').write_text(red.stdout + red.stderr, encoding='utf-8')
    require(red.returncode != 0 and 'FAIL:' in red.stderr, 'Demo regression must fail for behavior before implementation')
    op('evidence', task_id='DEMO-1', kind='red', outcome='failed', source=f'red.txt; exit {red.returncode}',
       detail='Untrimmed string and missing type rejection observed')
    op('ready', task_id='DEMO-1')
    state = op('start', task_id='DEMO-1')
    (root / 'labels.py').write_text(
        'def normalize(value: str) -> str:\n'
        '    if not isinstance(value, str):\n        raise TypeError("label must be a string")\n'
        '    return value.strip().casefold()\n', encoding='utf-8')
    op('result', task_id='DEMO-1', run_id=state['tasks']['DEMO-1']['run']['id'], outcome='success',
       source='Local demo file write completed', summary='Implemented pure normalization function')
    green = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=30)
    (root / 'green.txt').write_text(green.stdout + green.stderr, encoding='utf-8')
    require(green.returncode == 0, 'Green tests failed; demonstration remains incomplete')
    op('evidence', task_id='DEMO-1', kind='test', outcome='passed',
       source='green.txt; python -B -m unittest discover -s . -v; exit 0', detail='Both acceptance regressions passed')
    op('evidence', task_id='DEMO-1', kind='acceptance', outcome='passed', criteria=[0,1],
       source='green.txt', detail='Normalized string and TypeError asserted against actual function')
    op('review', task_id='DEMO-1', reviewer='demo deterministic self-check (not independent review)',
       source='Synthetic recipe reviewed; test fixtures executed; no provider invoked', findings=[])
    op('complete', task_id='DEMO-1')
    state = op('deliver', source='labels.py and green.txt', memory='not-needed',
               reason='Synthetic demonstration; no project or global memory captured')
    todo = root / 'todo.md'
    todo.write_text(markdown(state), encoding='utf-8')
    report = {'state': str(store.path), 'todo': str(todo), 'revision': state['revision'],
              'red_exit_code': red.returncode, 'green_exit_code': green.returncode,
              'metrics': metrics(state), 'limitations': ['No provider dispatch', 'Demo review is not independent']}
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report
