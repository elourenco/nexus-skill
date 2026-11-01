"""Behavioral contracts: durable state, gates, recovery and safe scheduling."""
import json
import multiprocessing
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/nexus/scripts'
sys.path.insert(0, str(SCRIPTS))

try:
    from nexus_workflow.store import StateStore, WorkflowError
    from nexus_workflow.orchestrator import Orchestrator
except ImportError:
    StateStore = Orchestrator = None


def competing_update(path, revision, ident, queue):
    try:
        Orchestrator(StateStore(Path(path))).apply({
            'operation_id': ident, 'expected_revision': revision,
            'action': 'mode', 'mode': 'FAST', 'reason': 'concurrent editor',
        })
        queue.put('ok')
    except WorkflowError:
        queue.put('conflict')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Orchestrator, 'Workflow executor is not implemented')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'local/state.json'
        self.store = StateStore(self.path)
        self.engine = Orchestrator(self.store)
        self.engine.initialize(self.root, mode='FAST', max_running=2, max_attempts=3)
        self.seq = 0

    def op(self, action, **data):
        self.seq += 1
        return self.engine.apply(dict(operation_id=f'op-{self.seq}',
            expected_revision=self.store.read()['revision'], action=action, **data))

    def task(self, ident='T1', **data):
        return self.op('create', task_id=ident, title=f'Task {ident}',
            goal='An observable change', criteria=['Behavior verified'],
            owner='main', role='implementer', resources=[f'file:{ident}.py'],
            authorization='user request in this chat',
            strategy={'kind': 'test-after', 'reason': 'Low risk change'}, **data)

    def start(self, ident='T1'):
        self.op('ready', task_id=ident)
        self.op('start', task_id=ident)
        return self.store.read()['tasks'][ident]['run']['id']

    def result(self, ident='T1', **data):
        run = self.store.read()['tasks'][ident]['run']['id']
        return self.op('result', task_id=ident, run_id=run,
            outcome='success', source='host execution receipt', summary='Implementation finished', **data)

    def checks(self, ident='T1'):
        self.op('evidence', task_id=ident, kind='test', outcome='passed',
            source='python3 -m unittest (exit 0)', detail='Behavior verified')
        self.op('evidence', task_id=ident, kind='acceptance', outcome='passed',
            source='observed output', detail='Behavior verified', criteria=[0])

    def complete(self, ident='T1'):
        self.result(ident)
        self.checks(ident)
        self.op('complete', task_id=ident)

    def artifact(self, kind, text='accepted', revision='1'):
        file = self.root / f'{kind}.md'
        file.write_text(text)
        self.op('artifact', kind=kind, path=file.name, revision=revision,
            source='user requirements', reason='Initial or reconciled contract')

    def test_fast_flow_requires_real_acceptance_before_delivery(self):
        self.task()
        self.start()
        self.result()
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.checks()
        self.op('complete', task_id='T1')
        self.op('deliver', source='local validated changes', memory='not-needed',
            reason='No durable learning to persist')
        state = self.store.read()
        self.assertEqual(state['status'], 'delivered')
        self.assertEqual(state['tasks']['T1']['status'], 'done')
        self.assertEqual(state['tasks']['T1']['attempts'], 1)

    def test_balanced_requires_spec_plan_and_detects_changed_contract(self):
        self.op('mode', mode='BALANCED', reason='Feature scope')
        self.task()
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='T1')
        self.artifact('discovery')
        self.artifact('spec')
        self.artifact('plan')
        self.op('reconcile', task_id='T1', reason='Bind accepted contracts')
        (self.root / 'spec.md').write_text('silently changed')
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='T1')
        self.artifact('spec', text='new accepted criteria', revision='2')
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='T1')
        self.op('reconcile', task_id='T1', reason='Reviewed changed criteria')
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='T1')
        self.artifact('plan', text='Plan for spec revision 2', revision='2')
        self.op('reconcile', task_id='T1', reason='Plan updated for spec revision 2')
        self.start()
        self.complete()

    def test_dependency_blocks_start_until_predecessor_done(self):
        self.task('A')
        self.task('B', depends_on=['A'])
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='B')
        self.start('A')
        self.complete('A')
        self.start('B')
        self.assertEqual(self.store.read()['tasks']['B']['status'], 'running')

    def test_cycles_and_missing_dependencies_are_transactional(self):
        self.task('A')
        self.task('B', depends_on=['A'])
        before = self.path.read_bytes()
        for dep in ['B', 'missing']:
            with self.assertRaises(WorkflowError):
                self.op('depend', task_id='A', dependency=dep)
            self.assertEqual(self.path.read_bytes(), before)

    def test_critical_tdd_requires_architecture_red_green_and_review(self):
        self.task(risk='critical', review_required=True)
        self.op('amend', task_id='T1', strategy={'kind':'tdd', 'reason':'Domain invariant'},
            reason='Critical invariant')
        with self.assertRaises(WorkflowError):
            self.start()
        self.op('evidence', task_id='T1', kind='architecture', outcome='passed',
            source='ADR-1', detail='Boundaries, alternatives, contracts and rollback inspected')
        self.op('evidence', task_id='T1', kind='red', outcome='failed',
            source='regression command exit 1', detail='Fails on missing invariant')
        self.start()
        self.result()
        self.checks()
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.op('review', task_id='T1', reviewer='independent-reviewer',
            source='review receipt', findings=[])
        self.op('complete', task_id='T1')

    def test_failure_budget_stops_retries_and_preserves_diagnostics(self):
        self.task()
        for _ in range(2):
            run = self.start()
            self.op('result', task_id='T1', run_id=run, outcome='failure',
                source='host exit 1', summary='Reproducible error')
            if _ == 0:
                self.op('resume', task_id='T1', reason='Fixed environment')
        with self.assertRaises(WorkflowError):
            self.op('resume', task_id='T1', reason='Try again')
        self.op('recover', task_id='T1', diagnosis='Incorrect fixture',
            discarded=['Provider failure'], source='reproduction log',
            next_action='Repair fixture and run once')
        self.start()
        self.complete()
        self.assertEqual(len(self.store.read()['tasks']['T1']['failures']), 2)

    def test_review_finding_blocks_done_and_rework_invalidates_evidence(self):
        self.task(review_required=True)
        self.start()
        self.result()
        self.checks()
        self.op('review', task_id='T1', reviewer='reviewer', source='independent diff review',
            findings=[{'id':'F1','severity':'critical','detail':'Broken invariant'}])
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.op('rework', task_id='T1', reason='Fix F1')
        self.start()
        self.result()
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.checks()
        self.op('resolve', task_id='T1', finding_id='F1', source='regression proof')
        self.op('review', task_id='T1', reviewer='reviewer', source='new diff review', findings=[])
        self.op('complete', task_id='T1')

    def test_interrupted_run_holds_resources_until_reconciled(self):
        self.task('A')
        self.task('B')
        self.op('amend', task_id='B', resources=['file:A.py'], reason='Shared file')
        run = self.start('A')
        self.op('interrupt', task_id='A', reason='Host disconnected')
        restored = Orchestrator(StateStore(self.path))
        self.assertEqual(restored.store.read()['tasks']['A']['run']['id'], run)
        with self.assertRaises(WorkflowError):
            self.start('B')
        with self.assertRaises(WorkflowError):
            self.op('resume', task_id='A', reason='Unknown outcome')
        self.op('reconcile_run', task_id='A', run_id=run, outcome='stopped',
            source='Host confirmed process stopped', next_action='Resume pending step')
        self.op('resume', task_id='A', reason='Confirmed no active worker')
        self.start('B')

    def test_provider_unavailable_does_not_simulate_dispatch(self):
        self.task()
        self.op('register', agent_id='worker', capabilities=['implementation'],
            available=False, source='host discovery', provider='example', model=None)
        self.op('ready', task_id='T1')
        with self.assertRaises(WorkflowError):
            self.op('dispatch', task_id='T1', agent_id='worker',
                capabilities=['implementation'], route_source='user policy')
        self.assertEqual(self.store.read()['tasks']['T1']['attempts'], 0)
        self.op('block', task_id='T1', reason='Provider unavailable', next_action='Wait or select verified host')

    def test_dispatch_requires_host_receipt_before_result(self):
        self.artifact('spec')
        self.task()
        self.op('register', agent_id='worker', capabilities=['implementation'],
            available=True, source='host discovery', provider='host', model='verified-model')
        self.op('ready', task_id='T1')
        self.op('dispatch', task_id='T1', agent_id='worker',
            capabilities=['implementation'], route_source='user policy')
        with self.assertRaises(WorkflowError):
            self.result()
        run = self.store.read()['tasks']['T1']['run']['id']
        context = self.store.read()['tasks']['T1']['run']['context']
        self.assertEqual(context['artifacts']['spec']['path'], 'spec.md')
        self.assertEqual(context['authorization'], 'user request in this chat')
        self.op('ack', task_id='T1', run_id=run, handle='host-run-123', source='host spawn response')
        self.complete()

    def test_budget_uses_measured_data_and_stops_new_execution(self):
        self.task()
        self.op('budget', limit=10, unit='tokens', source='test authorized budget')
        self.op('meter', kind='estimate', value=1, unit='tokens', source='estimate')
        with self.assertRaises(WorkflowError):
            self.start()
        self.op('meter', kind='actual', value=10, unit='tokens', source='host measurement')
        with self.assertRaises(WorkflowError):
            self.start()
        self.assertEqual(self.store.read()['tasks']['T1']['attempts'], 0)

    def test_independent_parallel_tasks_allowed_conflicts_rejected(self):
        for ident in ['A','B','C']:
            self.task(ident)
        self.start('A')
        self.start('B')
        with self.assertRaises(WorkflowError):
            self.start('C')
        self.complete('A')
        self.start('C')

    def test_idempotency_cas_and_history_survive_reopen(self):
        self.task()
        request = dict(operation_id='stable-id', expected_revision=self.store.read()['revision'],
            action='block', task_id='T1', reason='Waiting for data', next_action='Fetch data')
        self.engine.apply(request)
        after = self.path.read_bytes()
        Orchestrator(StateStore(self.path)).apply(request)
        self.assertEqual(self.path.read_bytes(), after)
        changed = dict(request, reason='Different request')
        with self.assertRaises(WorkflowError):
            self.engine.apply(changed)
        stale = dict(request, operation_id='stale')
        with self.assertRaises(WorkflowError):
            self.engine.apply(stale)
        self.assertEqual(self.store.read()['history'][-1]['operation_id'], 'stable-id')

    def test_concurrent_processes_cannot_lose_updates(self):
        ctx = multiprocessing.get_context('spawn')
        queue = ctx.Queue()
        revision = self.store.read()['revision']
        processes = [ctx.Process(target=competing_update,
            args=(str(self.path), revision, f'writer-{i}', queue)) for i in range(2)]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(sorted(queue.get(timeout=2) for _ in processes), ['conflict', 'ok'])
        self.assertEqual(self.store.read()['revision'], revision + 1)
        queue.close()

    def test_cancel_running_is_request_until_stop_receipt(self):
        self.task()
        run = self.start()
        self.op('cancel', task_id='T1', reason='User cancelled')
        task = self.store.read()['tasks']['T1']
        self.assertTrue(task['run']['active'])
        self.assertNotEqual(task['status'], 'cancelled')
        self.op('reconcile_run', task_id='T1', run_id=run, outcome='stopped',
            source='host stop confirmation', next_action='No further work')
        self.assertEqual(self.store.read()['tasks']['T1']['status'], 'cancelled')

    def test_corrupt_state_never_reports_success(self):
        self.path.write_text('{broken')
        with self.assertRaises(WorkflowError):
            self.store.read()

    def test_artifacts_cannot_read_outside_workspace(self):
        with self.assertRaises(WorkflowError):
            self.op('artifact', kind='spec', path='../secret.md', revision='1',
                source='test', reason='Invalid path')

    def test_unknown_fields_are_rejected_instead_of_silently_ignored(self):
        self.task()
        before = self.path.read_bytes()
        with self.assertRaises(WorkflowError):
            self.op('amend', task_id='T1', criterai=['Changed'], reason='Typo must not appear successful')
        self.assertEqual(self.path.read_bytes(), before)

    def test_directory_claim_and_symlink_aliases_conflict(self):
        (self.root / 'src').mkdir()
        (self.root / 'alias').symlink_to(self.root / 'src', target_is_directory=True)
        self.task('A')
        self.task('B')
        self.op('amend', task_id='A', resources=['dir:src'], reason='Directory ownership')
        self.op('amend', task_id='B', resources=['file:alias/a.py'], reason='Aliased shared file')
        self.start('A')
        with self.assertRaises(WorkflowError):
            self.start('B')

    def test_workspace_directory_claim_conflicts_with_every_file(self):
        self.task('A')
        self.task('B')
        self.op('amend', task_id='A', resources=['dir:.'], reason='Workspace ownership')
        self.start('A')
        with self.assertRaises(WorkflowError):
            self.start('B')

    def test_spec_revision_change_requires_task_reconciliation_even_same_bytes(self):
        self.artifact('spec')
        self.task()
        self.artifact('spec', revision='2')
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='T1')

    def test_same_artifact_refresh_preserves_task_proofs_and_state(self):
        self.artifact('spec')
        self.task()
        self.start()
        self.complete()
        self.artifact('spec')
        self.assertEqual(self.store.read()['tasks']['T1']['status'], 'done')

    def test_snapshot_write_failure_preserves_previous_revision(self):
        self.task()
        before = self.path.read_bytes()
        with patch('nexus_workflow.store.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(WorkflowError):
                self.op('block', task_id='T1', reason='Wait', next_action='Inspect')
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob('.state.json.*')), [])

    def test_attempt_limit_cannot_be_reset_by_recovery(self):
        self.task()
        for attempt in range(3):
            run = self.start()
            self.op('result', task_id='T1', run_id=run, outcome='failure', source='host result', summary='Failure')
            self.op('recover', task_id='T1', diagnosis='Known defect', discarded=['Network'],
                source='reproduction', next_action='Repair')
        with self.assertRaises(WorkflowError):
            self.start()
        self.assertEqual(self.store.read()['tasks']['T1']['attempts'], 3)

    def test_stale_worker_result_cannot_finish_a_new_attempt(self):
        self.task()
        first_run = self.start()
        self.op('result', task_id='T1', run_id=first_run, outcome='failure', source='host', summary='Failed')
        self.op('resume', task_id='T1', reason='Fixed input')
        second_run = self.start()
        with self.assertRaises(WorkflowError):
            self.op('result', task_id='T1', run_id=first_run, outcome='success', source='stale host', summary='Late result')
        self.assertEqual(self.store.read()['tasks']['T1']['run']['id'], second_run)

    def test_rework_invalidates_completed_dependents(self):
        self.task('A')
        self.task('B', depends_on=['A'])
        self.start('A')
        self.complete('A')
        self.start('B')
        self.complete('B')
        self.op('rework', task_id='A', reason='Discovered contract defect')
        self.assertEqual(self.store.read()['tasks']['B']['status'], 'pending')
        with self.assertRaises(WorkflowError):
            self.op('ready', task_id='B')

    def test_deep_mode_enforces_architecture_and_review(self):
        self.op('mode', mode='DEEP', reason='Architectural change')
        for kind in ('discovery', 'spec', 'plan', 'alternatives', 'decision'):
            self.artifact(kind)
        self.task()
        with self.assertRaises(WorkflowError):
            self.start()
        self.op('evidence', task_id='T1', kind='architecture', outcome='passed',
            source='ADR and contract review', detail='Alternatives, boundaries and recovery verified')
        self.start()
        self.result()
        self.checks()
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.op('review', task_id='T1', reviewer='council', source='Architecture and resilience review', findings=[])
        self.op('complete', task_id='T1')

    def test_validation_reserves_files_until_completion(self):
        self.task('A')
        self.task('B')
        self.op('amend', task_id='B', resources=['file:A.py'], reason='Shared ownership in sequence')
        self.start('A')
        self.result('A')
        with self.assertRaises(WorkflowError):
            self.start('B')
        self.checks('A')
        self.op('complete', task_id='A')
        self.start('B')

    def test_blocking_validation_does_not_release_unvalidated_work(self):
        self.task('A')
        self.task('B')
        self.op('amend', task_id='B', resources=['file:A.py'], reason='Same file')
        self.start('A')
        self.result('A')
        self.op('block', task_id='A', reason='Test service down', next_action='Restore service')
        with self.assertRaises(WorkflowError):
            self.start('B')
        self.op('cancel', task_id='A', reason='Explicitly abandon this validation')
        self.start('B')

    def test_review_cannot_overwrite_a_blocking_finding_with_same_id(self):
        self.task(review_required=True)
        self.start()
        self.result()
        self.checks()
        self.op('review', task_id='T1', reviewer='security', source='review one',
            findings=[{'id':'F1', 'severity':'high', 'detail':'Security defect'}])
        with self.assertRaises(WorkflowError):
            self.op('review', task_id='T1', reviewer='performance', source='review two',
                findings=[{'id':'F1', 'severity':'low', 'detail':'Unrelated naming issue'}])
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.assertEqual(self.store.read()['tasks']['T1']['findings']['F1']['severity'], 'high')

    def test_requested_reviews_must_all_return_before_completion(self):
        self.task()
        self.start()
        self.result()
        self.checks()
        for reviewer in ['architecture', 'quality']:
            self.op('request_review', task_id='T1', reviewer=reviewer,
                pillars=[reviewer], source='Host routing policy')
        requests = self.store.read()['tasks']['T1']['review_requests']
        first, second = requests[0]['id'], requests[1]['id']
        self.op('review', task_id='T1', reviewer='architecture', request_id=first,
            source='Architecture receipt', findings=[])
        with self.assertRaises(WorkflowError):
            self.op('complete', task_id='T1')
        self.op('review', task_id='T1', reviewer='quality', request_id=second,
            source='Quality receipt', findings=[])
        self.op('complete', task_id='T1')

    def test_post_replace_failure_can_be_reconciled_by_operation_id(self):
        self.task()
        request = dict(operation_id='durable-op', expected_revision=self.store.read()['revision'],
            action='block', task_id='T1', reason='Wait', next_action='Inspect')
        real_fsync = os.fsync
        calls = 0

        def fail_directory(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('directory fsync failure')
            return real_fsync(fd)

        with patch('nexus_workflow.store.os.fsync', side_effect=fail_directory):
            with self.assertRaisesRegex(WorkflowError, 'uncertain'):
                self.engine.apply(request)
        committed = self.store.read()['revision']
        self.engine.apply(request)
        self.assertEqual(self.store.read()['revision'], committed)
        self.assertEqual(self.store.read()['tasks']['T1']['status'], 'blocked')

    def test_busy_store_returns_bounded_error(self):
        with self.store._lock(True):
            with self.assertRaisesRegex(WorkflowError, 'timeout'):
                StateStore(self.path, timeout=0.01).read()

    def test_captured_memory_must_still_match_registered_artifact(self):
        self.task()
        self.start()
        self.complete()
        self.artifact('memory')
        (self.root / 'memory.md').write_text('unregistered replacement')
        with self.assertRaises(WorkflowError):
            self.op('deliver', source='local diff', memory='captured', reason='Learning recorded')


if __name__ == '__main__':
    unittest.main()
