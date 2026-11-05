#!/usr/bin/env python3
"""Create and validate a disposable consumer using an installed NEXUS package."""
import argparse
import json
from pathlib import Path
import sys

# Imports must work from the installed package without writing into its cache.
sys.dont_write_bytecode = True
from hook_contract import load_registry
from hook_engine import Engine
from nexus_workflow.orchestrator import Orchestrator, require
from nexus_workflow.store import StateStore, WorkflowError

DOMAIN_RED = 'def eligible(total: int) -> bool:\n    return total > 100\n'
DOMAIN_GREEN = 'def eligible(total: int) -> bool:\n    return total >= 100\n'
TESTS = '''import unittest
from shipping import eligible


class ShippingTests(unittest.TestCase):
    def test_below_threshold(self):
        self.assertFalse(eligible(99))

    def test_boundary(self):
        self.assertTrue(eligible(100))

    def test_above_threshold(self):
        self.assertTrue(eligible(101))
'''

# This is a fixture-specific consumer command, deliberately not a mutation or
# complexity framework. All subprocess output is structured synthetic metadata.
CHECKS = '''"""Checks owned by this synthetic consumer; Python standard library only."""
import argparse
import ast
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


def tests(minimum):
    suite = unittest.defaultTestLoader.discover('.', pattern='test_shipping.py')
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    report = {'tests': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped)}
    passed = (result.wasSuccessful() and result.testsRun >= minimum and not result.skipped)
    return report, passed


def mutation(minimum):
    # Run baseline and one known operator mutant in an isolated temporary copy.
    source = Path('shipping.py').read_text(encoding='utf-8')
    if source.count('>= 100') != 1:
        return {'error': 'Expected exactly one fixture mutation target'}, False
    with tempfile.TemporaryDirectory(prefix='nexus-consumer-mutant-') as temporary:
        root = Path(temporary)
        for name in ('shipping.py', 'test_shipping.py', 'checks.py'):
            shutil.copy2(name, root / name)
        command = [sys.executable, '-B', 'checks.py', 'tests', '--min-tests', '3']
        baseline = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=2)
        if baseline.returncode != 0:
            return {'error': 'Mutation baseline must pass'}, False
        (root / 'shipping.py').write_text(source.replace('>= 100', '> 100'), encoding='utf-8')
        mutant = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=2)
        observed = json.loads(mutant.stdout)
        killed = int(mutant.returncode == 1 and observed['tests'] >= 3
                     and observed['failures'] > 0 and observed['errors'] == 0)
        return {'mutants': 1, 'killed': killed, 'operator': '>= to >'}, killed >= minimum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=['tests', 'complexity', 'mutation'])
    parser.add_argument('--min-tests', type=int, default=3)
    parser.add_argument('--max-branches', type=int, default=0)
    parser.add_argument('--min-killed', type=int, choices=[1], default=1)
    args = parser.parse_args()
    if args.min_tests < 1 or args.max_branches < 0:
        parser.error('Thresholds must be nonnegative and min-tests positive')
    try:
        if args.check == 'tests':
            report, passed = tests(args.min_tests)
        elif args.check == 'complexity':
            tree = ast.parse(Path('shipping.py').read_text(encoding='utf-8'))
            branches = sum(isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.IfExp))
                           for node in ast.walk(tree))
            report, passed = {'fixture_branch_nodes': branches}, branches <= args.max_branches
        else:
            report, passed = mutation(args.min_killed)
        print(json.dumps(report, sort_keys=True))
        return 0 if passed else 1
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        print(json.dumps({'error': 'Consumer check failed or timed out'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
'''


def hook(ident, check, priority, timeout, flags, thresholds):
    return {
        'id': ident, 'description': f'Synthetic consumer {check} check', 'event': ['test.completed'],
        'trigger_conditions': {'profiles': ['FAST', 'BALANCED', 'DEEP'], 'any_flags': flags},
        'execution_mode': 'ENFORCE', 'priority': priority, 'inputs': ['Declared consumer files'],
        'outputs': ['Exit status'], 'timeout': timeout, 'retry_policy': {'max_attempts': 1},
        'failure_policy': 'block', 'permissions': ['command:' + ident], 'enabled': True,
        'supported_adapters': ['local'], 'handler': 'command',
        'config': {'argv': ['{python}', '-B', 'checks.py', check, *thresholds],
                   'read_only': True, 'cache_seconds': 0},
    }


def run_demo(directory):
    root = Path(directory).absolute()
    # lexists semantics: a dangling symlink is an existing caller-owned path too.
    require(not root.exists() and not root.is_symlink(), 'Output directory must not exist; never overwrite')
    root.mkdir(parents=True, mode=0o700)
    root = root.resolve()
    (root / '.nexus').mkdir(mode=0o700)
    (root / '.gitignore').write_text('.nexus/local/\n__pycache__/\n', encoding='utf-8')
    for name, content in [('shipping.py', DOMAIN_RED), ('test_shipping.py', TESTS), ('checks.py', CHECKS)]:
        (root / name).write_text(content, encoding='utf-8')
    registry = {'version': 1, 'hooks': [
        hook('tests', 'tests', 1, 2, [], ['--min-tests', '3']),
        hook('complexity', 'complexity', 2, 2, ['quality'], ['--max-branches', '0']),
        hook('mutation', 'mutation', 3, 6, ['mutation'], ['--min-killed', '1']),
    ]}
    registry_path = root / '.nexus/hooks.json'
    registry_path.write_text(json.dumps(registry, indent=2) + '\n', encoding='utf-8')
    store = StateStore(root / '.nexus/local/workflow.json')
    workflow = Orchestrator(store)
    workflow.initialize(root, mode='FAST')
    sequence = 0

    def op(action, **data):
        nonlocal sequence
        sequence += 1
        return workflow.apply(dict(operation_id=f'consumer-{sequence}',
            expected_revision=store.read()['revision'], action=action, **data))

    def rejected(action, **data):
        before = store.path.read_bytes()
        try:
            op(action, **data)
        except WorkflowError:
            require(store.path.read_bytes() == before, 'Rejected gate changed workflow')
            return True
        raise WorkflowError('Expected gate rejection was not observed')

    files = ['shipping.py', 'test_shipping.py', 'checks.py', '.nexus/hooks.json']
    op('create', task_id='DEMO-1', title='Free shipping threshold',
        goal='At total 100 or above shipping is free', criteria=['99 false, 100 true, 101 true'],
        owner='consumer-demo', role='implementer', resources=['file:shipping.py'], files=files,
        authorization='Explicit synthetic demo invocation; new output directory only',
        strategy={'kind': 'test-after', 'reason': 'Observe actual hook checks and gates'},
        evidence_policy={'hook_receipts': {'journal': '.nexus/local/hooks.sqlite',
            'registry': '.nexus/hooks.json', 'event': 'test.completed',
            'required_hooks': ['tests', 'complexity', 'mutation']}})

    def launch():
        op('ready', task_id='DEMO-1')
        state = op('start', task_id='DEMO-1')
        op('result', task_id='DEMO-1', run_id=state['tasks']['DEMO-1']['run']['id'],
            outcome='success', source='Synthetic local implementation write', summary='Ready for independent checks')

    def check(event_id):
        engine = Engine(root, root / '.nexus/local/hooks.sqlite', load_registry(registry_path),
                        ['command:tests', 'command:complexity', 'command:mutation'])
        try:
            return engine.run({'event_id': event_id, 'task_id': 'DEMO-1', 'event': 'test.completed',
                'profile': 'FAST', 'flags': ['quality', 'mutation'], 'files': files, 'inputs': {}})
        finally:
            engine.db.close()

    def accept(event_id):
        op('import_receipt', task_id='DEMO-1', event_id=event_id, source='Exact local consumer hook event')
        op('evidence', task_id='DEMO-1', kind='acceptance', outcome='passed', criteria=[0],
            source='Executed boundary assertions in test_shipping.py', detail='All three threshold cases passed')
        op('complete', task_id='DEMO-1')

    launch()
    red = check('consumer-red')
    require(red['gate'] == 'block' and red['hooks'][0]['status'] == 'failed', 'Expected real failing regression')
    failed_receipt = rejected('import_receipt', task_id='DEMO-1', event_id='consumer-red', source='Failed check')
    failed_complete = rejected('complete', task_id='DEMO-1')
    (root / 'shipping.py').write_text(DOMAIN_GREEN, encoding='utf-8')
    green = check('consumer-green')
    require(green['gate'] == 'pass' and len(green['hooks']) == 3, 'Expected all consumer checks to pass')
    accept('consumer-green')
    (root / 'shipping.py').write_text(DOMAIN_GREEN + '\n# Changed after verified receipt.\n', encoding='utf-8')
    stale = rejected('deliver', source='Synthetic consumer', memory='not-needed', reason='No durable knowledge')
    op('rework', task_id='DEMO-1', reason='Revalidate changed snapshot in a new generation')
    launch()
    recovered = check('consumer-recovered')
    require(recovered['gate'] == 'pass', 'Expected recovery checks to pass')
    accept('consumer-recovered')
    state = op('deliver', source='Synthetic consumer after fresh checks', memory='not-needed',
               reason='Synthetic fixture; no project memory captured')
    report = {
        'workspace': str(root), 'workflow': str(store.path), 'status': state['status'],
        'red': {'gate': red['gate'], 'tests': red['hooks'][0]['status']},
        'green': {row['hook_id']: row['status'] for row in green['hooks']},
        'failed_receipt_rejected': failed_receipt, 'failed_completion_rejected': failed_complete,
        'stale_delivery_rejected': stale, 'recovery_generation': state['tasks']['DEMO-1']['generation'],
        'limitations': ['Synthetic checks and one known mutation only', 'No native host integration or independent review',
                        'Branch-node count is fixture-specific, not a production complexity metric'],
    }
    (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run_demo(args.output_dir), indent=2))
        return 0
    except (WorkflowError, OSError, ValueError) as error:
        print(json.dumps({'error': str(error), 'outcome': 'Inspect partial output before retry'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
