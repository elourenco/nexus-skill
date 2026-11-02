"""Opt-in bridge uses actual hook journals, without executing hooks in workflow."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/nexus/scripts'
sys.path.insert(0, str(SCRIPTS))
from hook_engine import Engine
from hook_contract import load_registry
from nexus_workflow.orchestrator import Orchestrator
from nexus_workflow.store import StateStore, WorkflowError


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.store = StateStore(self.root / 'workflow.json')
        self.engine = Orchestrator(self.store)
        self.engine.initialize(self.root, mode='FAST')
        self.seq = 0
        (self.root / 'source.py').write_text('value = 1\n')
        self.registry = {'version': 1, 'hooks': [{
            'id': 'tests', 'description': 'Synthetic check', 'event': ['test.completed'],
            'trigger_conditions': {'profiles': ['FAST'], 'any_flags': []},
            'execution_mode': 'ENFORCE', 'priority': 1, 'inputs': [], 'outputs': [],
            'timeout': 1, 'retry_policy': {'max_attempts': 1}, 'failure_policy': 'block',
            'permissions': ['command:tests'], 'enabled': True, 'supported_adapters': ['local'],
            'handler': 'command', 'config': {'argv': [sys.executable, '-c', 'print("private fixture")'],
                                            'read_only': True},
        }]}
        self.write_registry()
        self.policy = {'hook_receipts': {'journal': 'hooks.sqlite', 'registry': 'hooks.json',
            'event': 'test.completed', 'required_hooks': ['tests']}}

    def write_registry(self):
        (self.root / 'hooks.json').write_text(json.dumps(self.registry))

    def op(self, action, **data):
        self.seq += 1
        return self.engine.apply(dict(operation_id=f'op-{self.seq}',
            expected_revision=self.store.read()['revision'], action=action, **data))

    def create(self, policy=True, **extra):
        return self.op('create', task_id='T1', title='Fixture', goal='Observe result',
            criteria=['Accepted'], owner='main', role='implementer', resources=['file:source.py'],
            files=['source.py'], authorization='Synthetic user request',
            strategy={'kind': 'test-after', 'reason': 'Fixture'},
            **({'evidence_policy': self.policy} if policy else {}), **extra)

    def launch(self):
        self.op('ready', task_id='T1')
        self.op('start', task_id='T1')
        self.op('result', task_id='T1', run_id=self.store.read()['tasks']['T1']['run']['id'],
            outcome='success', source='fixture host', summary='Finished')
        self.op('evidence', task_id='T1', kind='acceptance', outcome='passed', source='fixture observation',
            detail='Accepted behavior', criteria=[0])

    def journal(self, event_id='check-1', **changes):
        engine = Engine(self.root, self.root / 'hooks.sqlite', load_registry(self.root / 'hooks.json'),
                        ['command:tests'])
        self.addCleanup(engine.db.close)
        event = {'event_id': event_id, 'task_id': 'T1', 'event': 'test.completed',
            'profile': 'FAST', 'files': ['source.py'], 'flags': [], 'inputs': {}}
        event.update(changes)
        return engine.run(event)

    def receipt(self, event_id='check-1'):
        return self.op('import_receipt', task_id='T1', event_id=event_id, source='local hook journal')

    def edit_journal(self, mutate):
        with self.database() as db:
            raw = json.loads(db.execute('SELECT result FROM events').fetchone()[0])
            mutate(raw)
            db.execute('UPDATE events SET result=?', (json.dumps(raw),))

    def database(self):
        db = sqlite3.connect(self.root / 'hooks.sqlite')
        self.addCleanup(db.close)
        return db

    def test_valid_receipt_completes_delivers_without_private_outputs(self):
        self.create(); self.launch(); self.journal(); self.receipt()
        self.op('complete', task_id='T1')
        self.op('deliver', source='local fixture', memory='not-needed', reason='No learning')
        self.assertEqual(self.store.read()['status'], 'delivered')
        self.assertNotIn('private fixture', self.store.path.read_text())

    def test_legacy_tasks_keep_declared_evidence_and_no_policy_field(self):
        self.create(policy=False); self.launch()
        self.op('evidence', task_id='T1', kind='test', outcome='passed', source='declared', detail='Passed')
        self.op('complete', task_id='T1')
        self.assertEqual(self.store.read()['schema_version'], 1)

    def test_declared_test_cannot_bypass_opt_in_receipt_gate(self):
        self.create(); self.launch()
        self.op('evidence', task_id='T1', kind='test', outcome='passed', source='declared', detail='Passed')
        with self.assertRaises(WorkflowError): self.op('complete', task_id='T1')

    def test_wrong_task_workspace_event_snapshot_registry_and_missing_hook_rejected(self):
        self.create(); self.launch(); self.journal()
        original = (self.root / 'hooks.sqlite').read_bytes()
        mutations = [lambda r: r.update(task_id='other'), lambda r: r.update(event='code.post_edit'),
            lambda r: r.update(scope='wrong'), lambda r: r.update(registry_digest='wrong'),
            lambda r: r.update(hooks=[]), lambda r: r['hooks'][0].update(status='failed'),
            lambda r: r['hooks'][0].update(checked_at=0),
            lambda r: r['hooks'][0].update(task_id='other')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                (self.root / 'hooks.sqlite').write_bytes(original)
                self.edit_journal(mutation)
                before = self.store.path.read_bytes()
                with self.assertRaises(WorkflowError): self.receipt()
                self.assertEqual(before, self.store.path.read_bytes())
        (self.root / 'hooks.sqlite').write_bytes(original)
        with self.database() as db:
            db.execute('UPDATE events SET workspace=?', ('/wrong/workspace',))
        with self.assertRaises(WorkflowError): self.receipt()

    def test_files_and_registry_revalidated_at_completion_and_delivery(self):
        self.create(); self.launch(); self.journal(); self.receipt()
        (self.root / 'source.py').write_text('value = 2\n')
        with self.assertRaises(WorkflowError): self.op('complete', task_id='T1')
        (self.root / 'source.py').write_text('value = 1\n')
        self.op('complete', task_id='T1')
        self.registry['hooks'][0]['description'] = 'Changed contract'
        self.write_registry()
        with self.assertRaises(WorkflowError):
            self.op('deliver', source='fixture', memory='not-needed', reason='No learning')

    def test_rework_cannot_reimport_old_generation_even_same_bytes(self):
        self.create(); self.launch(); self.journal(); self.receipt()
        self.op('rework', task_id='T1', reason='Revisit implementation')
        self.launch()
        with self.assertRaises(WorkflowError): self.receipt()
        self.journal(event_id='check-2'); self.receipt('check-2')
        self.op('complete', task_id='T1')

    def test_receipt_replay_is_idempotent_and_failed_reads_do_not_create_database(self):
        self.create(); self.launch()
        with self.assertRaises(WorkflowError): self.receipt()
        self.assertFalse((self.root / 'hooks.sqlite').exists())
        self.journal()
        request = dict(operation_id='stable', expected_revision=self.store.read()['revision'],
            action='import_receipt', task_id='T1', event_id='check-1', source='journal')
        self.engine.apply(request)
        before = self.store.path.read_bytes()
        (self.root / 'hooks.sqlite').unlink()
        self.engine.apply(request)
        self.assertEqual(before, self.store.path.read_bytes())

    def test_invalid_policy_and_empty_file_scope_rejected_atomically(self):
        for policy in [None, {'unknown': True}, {'independent_review': 'yes'},
                       {'hook_receipts': {}}, {'hook_receipts': dict(self.policy['hook_receipts'], journal='../escape')}]:
            self.policy = policy
            with self.subTest(policy=policy), self.assertRaises(WorkflowError): self.create()
        self.policy = {'hook_receipts': {'journal': 'hooks.sqlite', 'registry': 'hooks.json',
            'event': 'test.completed', 'required_hooks': ['tests']}}
        self.create()
        with self.assertRaises(WorkflowError): self.op('amend', task_id='T1', files=[], reason='Empty scope')

    def test_missing_or_failed_journal_and_unsafe_command_cannot_supply_receipt(self):
        self.create(); self.launch(); self.journal()
        with self.assertRaises(WorkflowError): self.receipt('missing')
        self.edit_journal(lambda r: r.update(gate='block'))
        with self.assertRaises(WorkflowError): self.receipt()
        self.registry['hooks'][0].update(execution_mode='EXECUTE', failure_policy='warn')
        self.registry['hooks'][0]['config']['read_only'] = False
        self.write_registry()
        with self.assertRaises(WorkflowError): self.receipt()

    def test_independent_review_policy_requires_provenance_and_rejects_owner(self):
        self.policy = {'independent_review': True}
        self.create(); self.launch()
        self.op('evidence', task_id='T1', kind='test', outcome='passed', source='declared', detail='Passed')
        for fields in [{'reviewer': 'main', 'reviewer_handle': 'other'},
                       {'reviewer': 'other', 'reviewer_handle': 'main'}, {'reviewer': 'other'}]:
            with self.assertRaises(WorkflowError):
                self.op('review', task_id='T1', source='host reviewer receipt', findings=[], **fields)
        with self.assertRaises(WorkflowError): self.op('complete', task_id='T1')
        self.op('review', task_id='T1', reviewer='quality', reviewer_handle='host-review-123',
            source='host reviewer receipt', findings=[])
        self.op('complete', task_id='T1')

    def test_policy_amend_invalidates_receipts_and_legacy_state_has_no_migration(self):
        self.create(policy=False)
        self.assertNotIn('evidence_policy', self.store.read()['tasks']['T1'])
        self.op('amend', task_id='T1', evidence_policy=self.policy, reason='Require checked evidence')
        self.assertEqual(self.store.read()['tasks']['T1']['generation'], 1)
        self.launch(); self.journal(); self.receipt()
        self.op('rework', task_id='T1', reason='Policy revision')
        self.op('amend', task_id='T1', evidence_policy={}, reason='Explicitly return to declared evidence')
        self.launch()
        self.op('evidence', task_id='T1', kind='test', outcome='passed', source='declared', detail='Passed')
        self.op('complete', task_id='T1')

    def test_journal_is_read_only_bounded_and_revalidated_if_deleted(self):
        self.create(); self.launch(); self.journal()
        with self.database() as db:
            before = db.execute('SELECT * FROM events').fetchall()
        self.receipt()
        with self.database() as db:
            self.assertEqual(db.execute('SELECT * FROM events').fetchall(), before)
        self.op('complete', task_id='T1')
        (self.root / 'hooks.sqlite').unlink()
        with self.assertRaises(WorkflowError):
            self.op('deliver', source='fixture', memory='not-needed', reason='No learning')

    def test_invalid_oversized_and_busy_journal_fail_without_workflow_mutation(self):
        self.create(); self.launch(); self.journal()
        with self.database() as db:
            original = db.execute('SELECT result FROM events').fetchone()[0]
            db.execute('UPDATE events SET result=?', ('x' * 262145,))
        before = self.store.path.read_bytes()
        with self.assertRaises(WorkflowError): self.receipt()
        self.assertEqual(before, self.store.path.read_bytes())
        with self.database() as db:
            db.execute('UPDATE events SET result=?', ('{"broken":',))
        with self.assertRaises(WorkflowError): self.receipt()
        with self.database() as db:
            db.execute('UPDATE events SET result=?', (original,))
        with self.database() as db:
            db.execute('BEGIN EXCLUSIVE')
            with self.assertRaises(WorkflowError): self.receipt()
            db.rollback()
        self.assertEqual(before, self.store.path.read_bytes())

    def test_import_payload_does_not_accept_asserted_status_or_output(self):
        self.create(); self.launch(); self.journal()
        for extras in [{'outcome': 'passed'}, {'receipt': {'status': 'passed'}}, {'event_id': []}]:
            request = dict(operation_id='invalid', expected_revision=self.store.read()['revision'],
                action='import_receipt', task_id='T1', event_id='check-1', source='fixture')
            request.update(extras)
            with self.assertRaises(WorkflowError): self.engine.apply(request)

    def test_executable_bit_changes_and_newer_declared_evidence_invalidate_gate(self):
        self.create(); self.launch(); self.journal(); self.receipt()
        source = self.root / 'source.py'
        source.chmod(0o700)
        with self.assertRaises(WorkflowError): self.op('complete', task_id='T1')
        source.chmod(0o600)
        self.op('evidence', task_id='T1', kind='test', outcome='passed', source='declared', detail='Passed')
        with self.assertRaises(WorkflowError): self.op('complete', task_id='T1')

    def test_old_cached_hook_check_cannot_be_replayed_in_new_run(self):
        self.registry['hooks'][0]['config']['cache_seconds'] = 60
        self.write_registry()
        self.create(); self.launch(); self.journal(); self.receipt()
        self.op('rework', task_id='T1', reason='New generation')
        self.launch()
        result = self.journal(event_id='cached-in-new-run')
        self.assertIn('reused_from', result['hooks'][0]['output'])
        with self.assertRaises(WorkflowError): self.receipt('cached-in-new-run')

    def test_workflow_import_does_not_execute_hook_commands(self):
        self.create(); self.launch(); self.journal()
        with patch('subprocess.run', side_effect=AssertionError('Workflow must never execute commands')):
            self.receipt()
            self.op('complete', task_id='T1')

    def test_delegated_implementer_id_and_host_handle_cannot_self_review(self):
        self.policy = {'independent_review': True}
        self.create()
        self.op('register', agent_id='worker', capabilities=['implementation'], available=True,
            source='fixture host', provider='same-provider', model='same-model')
        self.op('ready', task_id='T1')
        self.op('dispatch', task_id='T1', agent_id='worker', capabilities=['implementation'], route_source='fixture')
        run = self.store.read()['tasks']['T1']['run']
        self.assertEqual(run['context']['evidence_policy'], self.policy)
        self.op('ack', task_id='T1', run_id=run['id'], handle='host-implementation-123', source='fixture host')
        self.op('result', task_id='T1', run_id=run['id'], outcome='success', source='fixture', summary='Finished')
        for fields in [{'reviewer': ' WORKER ', 'reviewer_handle': 'other'},
                       {'reviewer': 'quality', 'reviewer_handle': ' HOST-IMPLEMENTATION-123 '}]:
            with self.assertRaises(WorkflowError):
                self.op('review', task_id='T1', source='fixture review', findings=[], **fields)
        self.op('review', task_id='T1', reviewer='quality', reviewer_handle='host-review-123',
            source='Independent declared review using same provider and model', findings=[])

    def test_symlinked_registry_and_journal_are_rejected(self):
        for field in ('registry', 'journal'):
            target = self.root / 'actual'
            target.write_text('{}')
            alias = self.root / ('alias-' + field)
            alias.symlink_to(target)
            self.policy['hook_receipts'][field] = alias.name
            with self.assertRaises(WorkflowError): self.create()
            self.policy['hook_receipts'][field] = 'hooks.json' if field == 'registry' else 'hooks.sqlite'


if __name__ == '__main__':
    unittest.main()
