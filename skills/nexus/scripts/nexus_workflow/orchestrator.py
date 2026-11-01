"""Rules and transitions, independent of CLI/Markdown presentation."""
import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .store import WorkflowError

MODES = {'FAST', 'BALANCED', 'DEEP'}
STRATEGIES = {'tdd', 'test-after', 'characterization', 'integration-contract', 'inspection'}
ARTIFACTS = {'discovery', 'spec', 'plan', 'alternatives', 'decision', 'delivery', 'memory'}
TERMINAL = {'done', 'cancelled'}


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise WorkflowError(message)


def text(data, key):
    value = data.get(key)
    require(isinstance(value, str) and bool(value.strip()), f'{key}: nonempty string required')
    return value.strip()


def strings(data, key, nonempty=False):
    value = data.get(key, [])
    require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value),
            f'{key}: list of nonempty strings required')
    require(not nonempty or bool(value), f'{key}: cannot be empty')
    require(len(set(value)) == len(value), f'{key}: duplicate values')
    return value


def number(value, name):
    require(type(value) in (float, int) and (type(value) is int or math.isfinite(value)) and value >= 0,
            f'{name}: finite nonnegative number required')
    return value


def positive_int(value, name):
    require(type(value) is int and value > 0, f'{name}: positive integer required')
    return value


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value),
            'Invalid stable ID')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


class Orchestrator:
    FIELDS = {
        'mode': 'mode reason', 'artifact': 'kind path revision source reason',
        'create': 'task_id title goal criteria owner role priority risk review_required resources files depends_on strategy authorization complexity',
        'amend': 'task_id title goal criteria owner role priority resources files strategy authorization reason',
        'depend': 'task_id dependency', 'reconcile': 'task_id reason', 'ready': 'task_id', 'start': 'task_id',
        'dispatch': 'task_id agent_id capabilities route_source', 'ack': 'task_id run_id handle source',
        'result': 'task_id run_id outcome source summary', 'evidence': 'task_id kind outcome source detail criteria',
        'request_review': 'task_id reviewer pillars source',
        'review': 'task_id reviewer source findings request_id', 'resolve': 'task_id finding_id source',
        'complete': 'task_id', 'rework': 'task_id reason', 'block': 'task_id reason next_action',
        'resume': 'task_id reason', 'recover': 'task_id diagnosis discarded source next_action',
        'interrupt': 'task_id reason', 'reconcile_run': 'task_id run_id outcome source next_action',
        'cancel': 'task_id reason', 'register': 'agent_id capabilities available source provider model effort',
        'budget': 'limit unit source', 'meter': 'kind value unit source', 'checkpoint': 'task_id next_action source',
        'deliver': 'source memory reason',
    }

    def __init__(self, store):
        self.store = store

    def initialize(self, workspace, mode='BALANCED', max_running=1, max_attempts=3):
        require(mode in MODES, 'Unknown mode')
        root = Path(workspace).resolve()
        require(root.is_dir(), 'Workspace must exist')
        return self.store.create({
            'schema_version': 1, 'id': str(uuid.uuid4()), 'revision': 0,
            'workspace': str(root), 'created_at': now(), 'mode': mode, 'status': 'active',
            'max_running': positive_int(max_running, 'max_running'),
            'max_attempts': positive_int(max_attempts, 'max_attempts'),
            'artifacts': {}, 'tasks': {}, 'registry': {}, 'budget': None,
            'meters': [], 'history': [], 'delivery': None,
        })

    def apply(self, request):
        require(isinstance(request, dict), 'Request must be an object')
        operation = identifier(request.get('operation_id'))
        revision = request.get('expected_revision')
        require(type(revision) is int and revision >= 0, 'expected_revision required')
        action = text(request, 'action')
        require(action in self.FIELDS, 'Unknown action')
        unknown = set(request) - set(self.FIELDS[action].split()) - {'operation_id', 'expected_revision', 'action'}
        require(not unknown, f'Unknown fields: {sorted(unknown)}')
        fingerprint = digest({k: v for k, v in request.items() if k != 'expected_revision'})

        def mutate(state):
            for event in state['history']:
                if event['operation_id'] == operation:
                    require(event['fingerprint'] == fingerprint, 'Operation ID reused with different payload')
                    return False
            require(state['revision'] == revision, 'Revision conflict; reload state and re-evaluate')
            require(state['status'] == 'active', 'Delivered workflow is immutable; initialize another workflow')
            self._validate_graph(state)
            getattr(self, '_op_' + action)(state, request)
            self._validate_graph(state)
            state['revision'] += 1
            state['history'].append({
                'revision': state['revision'], 'operation_id': operation, 'fingerprint': fingerprint,
                'at': now(), 'action': action, 'task_id': request.get('task_id'),
                'request': request,
            })
            return True
        return self.store.transact(mutate)

    def _task(self, state, request):
        task_id = text(request, 'task_id')
        require(task_id in state['tasks'], 'Unknown task')
        return state['tasks'][task_id]

    def _idle(self, task):
        require(not (task['run'] and task['run']['active']), 'Run active or uncertain; reconcile before mutation')

    def _editable(self, task):
        self._idle(task)
        require(task['status'] not in TERMINAL, 'Terminal task; use explicit rework for done tasks')

    def _validate_graph(self, state):
        # Kahn traversal avoids recursion limits for long dependency chains.
        tasks = state['tasks']
        indegree = {key: len(t['depends_on']) for key, t in tasks.items()}
        children = {key: [] for key in tasks}
        for key, task in tasks.items():
            for parent in task['depends_on']:
                require(parent in tasks, f'Missing dependency: {parent}')
                children[parent].append(key)
        ready = [key for key, count in indegree.items() if count == 0]
        count = 0
        while ready:
            parent = ready.pop()
            count += 1
            for child in children[parent]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        require(count == len(tasks), 'Dependency cycle')

    def _file(self, state, relative):
        root = Path(state['workspace'])
        path = (root / relative).resolve()
        require(path.is_relative_to(root) and path.is_file(), 'Artifact must be a file inside workspace')
        return path

    def _bindings(self, state):
        return {key: {'sha256': value['sha256'], 'revision': value['revision']} for key, value in state['artifacts'].items()
                if key in {'discovery', 'spec', 'plan', 'alternatives', 'decision'}}

    def _contracts(self, state, task):
        required = set() if state['mode'] == 'FAST' else {'discovery', 'spec', 'plan'}
        if state['mode'] == 'DEEP':
            required |= {'alternatives', 'decision'}
        require(required <= state['artifacts'].keys(), 'Mode requires discovery/spec/plan and DEEP alternatives/decision')
        require(task['bindings'] == self._bindings(state), 'Contracts changed; reconcile task explicitly')
        if 'plan' in state['artifacts']:
            require(state['artifacts']['plan'].get('spec_binding') == self._bindings(state).get('spec'),
                    'PLAN references an older SPEC; reconcile and register PLAN first')
        for kind in task['bindings']:
            artifact = state['artifacts'][kind]
            actual = hashlib.sha256(self._file(state, artifact['path']).read_bytes()).hexdigest()
            require(actual == artifact['sha256'], f'{kind} changed outside registered revision')

    def _proof(self, task, kind, outcome='passed'):
        matches = [e for e in task['evidence'] if e['generation'] == task['generation'] and e['kind'] == kind]
        return bool(matches) and matches[-1]['outcome'] == outcome

    def _eligibility(self, state, task):
        require(task['status'] in {'pending', 'ready'}, 'Task must be pending/ready')
        self._idle(task)
        self._contracts(state, task)
        require(all(state['tasks'][dep]['status'] == 'done' for dep in task['depends_on']),
                'Dependencies must be done; cancellation does not satisfy them')
        require(bool(task['authorization']), 'Authorization provenance required')
        require(task['failure_streak'] < 2, 'Two failures without verified progress; diagnose before retry')
        require(task['attempts'] < state['max_attempts'], 'Attempt budget exhausted')
        if task['risk'] == 'critical' or state['mode'] == 'DEEP':
            require(self._proof(task, 'architecture'), 'Architecture gate required')
        if task['strategy']['kind'] == 'tdd':
            require(self._proof(task, 'red', 'failed'), 'TDD requires observed failing regression before start')

    def _resources(self, state, values):
        normalized = []
        for resource in values:
            require(':' in resource, 'Resource needs namespace: file:, dir:, port:, db:, etc.')
            kind, name = resource.split(':', 1)
            require(kind and name, 'Empty resource')
            if kind in {'file', 'dir'}:
                path = PurePosixPath(name)
                require(not path.is_absolute() and '..' not in path.parts and str(path) == name,
                        'File/directory resource must be a normalized workspace-relative path')
                root = Path(state['workspace'])
                resolved = (root / name).resolve()
                require(resolved.is_relative_to(root), 'Owned resource resolves outside workspace')
                resource = kind + ':' + str(resolved.relative_to(root))
            normalized.append(resource)
        require(len(set(normalized)) == len(normalized), 'Aliased duplicate resource')
        return normalized

    @staticmethod
    def _conflict(left, right):
        if left == right:
            return True
        a, x = left.split(':', 1)
        b, y = right.split(':', 1)
        if a in {'file', 'dir'} and b in {'file', 'dir'}:
            # Conservative across case-sensitive/insensitive local volumes.
            x, y = x.casefold(), y.casefold()
            return (x == y or (a == 'dir' and (x == '.' or y.startswith(x + '/')))
                    or (b == 'dir' and (y == '.' or x.startswith(y + '/'))))
        return False

    def _launch(self, state, task, request, agent=None):
        self._eligibility(state, task)
        require(task['status'] == 'ready', 'Mark task ready before launch')
        task['resources'] = self._resources(state, task['resources'])
        active = [t for t in state['tasks'].values() if t['claimed']]
        require(len(active) < state['max_running'], 'Concurrency limit reached')
        require(not any(self._conflict(a, b) for t in active for a in t['resources'] for b in task['resources']),
                'Shared resource conflict')
        if state['budget']:
            budget = state['budget']
            measures = [m for m in state['meters'] if m['kind'] == 'actual' and m['unit'] == budget['unit']]
            require(bool(measures), 'Budget needs a measured total; estimate is not measurement')
            require(measures[-1]['value'] < budget['limit'], 'Budget exhausted; no new execution')
        task['attempts'] += 1
        task['claimed'] = True
        task['status'] = 'running'
        task['blocker'] = None
        task['started_at'] = task['started_at'] or now()
        task['run'] = {
            'id': str(uuid.uuid4()), 'active': True, 'acknowledged': agent is None,
            'handle': None, 'agent': agent, 'started_at': now(), 'stop_requested': False,
            'context': {key: task[key] for key in ('id', 'goal', 'criteria', 'resources', 'files',
                       'bindings', 'strategy', 'next_action', 'owner', 'role', 'authorization')},
        }
        task['run']['context']['artifacts'] = {
            key: value for key, value in state['artifacts'].items() if key in task['bindings']}
        task['run']['context']['constraints'] = [
            'Follow host instructions and existing authorization; no additional permissions are granted.',
            'Other agents may be working: preserve their edits and respect assigned resources.',
            'Report evidence and actual outcome; reconcile uncertain external effects before retry.',
        ]
        task['next_action'] = 'Execute with host tools' if agent is None else 'Dispatch context via host, then ack receipt'

    def _invalidate(self, task):
        task['generation'] += 1
        task['claimed'] = False
        task['status'] = 'pending'
        task['completed_at'] = None
        task['blocker'] = None
        task['next_action'] = 'Revalidate contracts, then mark ready'

    def _op_mode(self, state, r):
        mode = text(r, 'mode')
        require(mode in MODES, 'Unknown mode')
        text(r, 'reason')
        require(not any(t['run'] and t['run']['active'] for t in state['tasks'].values()),
                'Change mode at a reconciled checkpoint')
        state['mode'] = mode

    def _op_artifact(self, state, r):
        kind = text(r, 'kind')
        require(kind in ARTIFACTS, 'Unknown artifact kind')
        text(r, 'reason')
        path = self._file(state, text(r, 'path'))
        artifact = {'path': str(path.relative_to(state['workspace'])),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'revision': text(r, 'revision'), 'source': text(r, 'source'), 'at': now()}
        if kind == 'plan':
            require('spec' in state['artifacts'], 'PLAN requires a registered SPEC')
            artifact['spec_binding'] = self._bindings(state)['spec']
        if kind not in {'delivery', 'memory'}:
            for task in state['tasks'].values():
                self._idle(task)
            previous = state['artifacts'].get(kind)
            if previous is None or any(previous.get(key) != artifact.get(key)
                                       for key in ('sha256', 'revision', 'spec_binding')):
                for task in state['tasks'].values():
                    if task['status'] != 'cancelled':
                        self._invalidate(task)
        state['artifacts'][kind] = artifact

    def _strategy(self, data):
        require(isinstance(data, dict), 'strategy required')
        require(data.get('kind') in STRATEGIES, 'Unknown test strategy')
        text(data, 'reason')
        return data

    def _op_create(self, state, r):
        ident = identifier(r.get('task_id'))
        require(ident not in state['tasks'], 'Task ID already exists')
        risk = r.get('risk', 'normal')
        require(risk in {'low', 'normal', 'critical'}, 'Unknown risk')
        review = r.get('review_required', False)
        require(type(review) is bool, 'review_required must be boolean')
        priority = r.get('priority', 2)
        require(type(priority) is int and 0 <= priority <= 3, 'priority must be 0..3')
        state['tasks'][ident] = {
            'id': ident, 'title': text(r, 'title'), 'goal': text(r, 'goal'),
            'criteria': strings(r, 'criteria', True), 'owner': text(r, 'owner'), 'role': text(r, 'role'),
            'priority': priority, 'risk': risk, 'review_required': review,
            'resources': self._resources(state, strings(r, 'resources', True)), 'files': strings(r, 'files'),
            'depends_on': strings(r, 'depends_on'), 'strategy': self._strategy(r.get('strategy')),
            'authorization': text(r, 'authorization'), 'complexity': r.get('complexity'),
            'bindings': self._bindings(state), 'status': 'pending', 'attempts': 0, 'failure_streak': 0,
            'generation': 0, 'evidence': [], 'reviews': [], 'review_requests': [], 'findings': {}, 'failures': [],
            'run': None, 'claimed': False, 'blocker': None, 'next_action': 'Mark ready after checking dependencies',
            'created_at': now(), 'started_at': None, 'completed_at': None,
        }

    def _op_amend(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        text(r, 'reason')
        for key in ('title', 'goal', 'owner', 'role', 'authorization'):
            if key in r:
                task[key] = text(r, key)
        for key in ('criteria', 'resources', 'files'):
            if key in r:
                task[key] = strings(r, key, key != 'files')
                if key == 'resources':
                    task[key] = self._resources(state, task[key])
        if 'strategy' in r:
            task['strategy'] = self._strategy(r['strategy'])
        if 'priority' in r:
            require(type(r['priority']) is int and 0 <= r['priority'] <= 3, 'priority must be 0..3')
            task['priority'] = r['priority']
        self._invalidate(task)

    def _op_depend(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        dependency = text(r, 'dependency')
        require(dependency not in task['depends_on'], 'Dependency already present')
        task['depends_on'].append(dependency)
        self._invalidate(task)

    def _op_reconcile(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        text(r, 'reason')
        self._invalidate(task)
        task['bindings'] = self._bindings(state)

    def _op_ready(self, state, r):
        task = self._task(state, r)
        self._eligibility(state, task)
        task['status'] = 'ready'
        task['next_action'] = 'Start or prepare dispatch'

    def _op_start(self, state, r):
        self._launch(state, self._task(state, r), r)

    def _op_register(self, state, r):
        ident = identifier(r.get('agent_id'))
        require(type(r.get('available')) is bool, 'available must reflect verified host capability')
        state['registry'][ident] = {'id': ident, 'capabilities': strings(r, 'capabilities', True),
            'available': r['available'], 'source': text(r, 'source'), 'at': now(),
            'provider': r.get('provider'), 'model': r.get('model'), 'effort': r.get('effort')}

    def _op_dispatch(self, state, r):
        ident = text(r, 'agent_id')
        agent = state['registry'].get(ident)
        require(agent is not None and agent['available'], 'Provider/agent unavailable; verify fallback in host')
        require(set(strings(r, 'capabilities', True)) <= set(agent['capabilities']), 'Missing capability')
        route = text(r, 'route_source')
        task = self._task(state, r)
        self._launch(state, task, r, {**agent, 'route_source': route})

    def _run(self, state, r):
        task = self._task(state, r)
        require(task['run'] and task['run']['active'], 'No active run')
        require(task['run']['id'] == text(r, 'run_id'), 'Stale run receipt')
        return task

    def _op_ack(self, state, r):
        task = self._run(state, r)
        require(not task['run']['acknowledged'], 'Run already acknowledged')
        task['run'].update(acknowledged=True, handle=text(r, 'handle'), receipt=text(r, 'source'))
        task['next_action'] = 'Collect actual host result'

    def _op_result(self, state, r):
        task = self._run(state, r)
        require(task['run']['acknowledged'], 'Host dispatch has no receipt; reconcile instead of assuming execution')
        require(not task['run']['stop_requested'], 'Cancellation pending; reconcile stopped/completed outcome')
        outcome = text(r, 'outcome')
        require(outcome in {'success', 'failure'}, 'Unknown run outcome')
        source, summary = text(r, 'source'), text(r, 'summary')
        task['run'].update(active=False, finished_at=now(), source=source, summary=summary, outcome=outcome)
        if outcome == 'failure':
            task['claimed'] = False
            task['failure_streak'] += 1
            task['failures'].append({'at': now(), 'run_id': task['run']['id'], 'source': source, 'error': summary})
            task['status'], task['blocker'] = 'blocked', summary
            task['next_action'] = 'Diagnose failure before bounded retry'
        else:
            task['status'], task['blocker'] = 'validating', None
            task['next_action'] = 'Run adaptive testing, acceptance checks and applicable review'

    def _op_evidence(self, state, r):
        task = self._task(state, r)
        require(task['status'] not in TERMINAL, 'Terminal task evidence is frozen')
        kind, outcome = text(r, 'kind'), text(r, 'outcome')
        require(kind in {'architecture', 'red', 'test', 'acceptance'}, 'Unknown evidence kind')
        require(outcome in {'passed', 'failed'}, 'Unknown evidence outcome')
        if kind in {'test', 'acceptance'}:
            require(task['status'] == 'validating', 'Implementation result required before validation evidence')
        else:
            self._idle(task)
        criteria = r.get('criteria', [])
        require(isinstance(criteria, list) and all(type(i) is int and 0 <= i < len(task['criteria']) for i in criteria),
                'criteria must contain existing zero-based acceptance indexes')
        if kind == 'acceptance':
            require(bool(criteria), 'Acceptance evidence must identify criteria')
        task['evidence'].append({'id': r['operation_id'], 'generation': task['generation'],
            'at': now(), 'kind': kind, 'outcome': outcome, 'source': text(r, 'source'),
            'detail': text(r, 'detail'), 'criteria': criteria})
        if kind == 'test' and outcome == 'passed':
            task['failure_streak'] = 0

    def _op_request_review(self, state, r):
        task = self._task(state, r)
        require(task['status'] == 'validating', 'Review requires implementation result')
        task['review_requests'].append({'id': r['operation_id'], 'generation': task['generation'],
            'reviewer': text(r, 'reviewer'), 'pillars': strings(r, 'pillars', True),
            'source': text(r, 'source'), 'at': now(), 'answered': False})
        task['review_required'] = True
        task['next_action'] = 'Dispatch review in host; attach receipt with request_id'

    def _op_review(self, state, r):
        task = self._task(state, r)
        require(task['status'] == 'validating', 'Review requires implementation result')
        findings = r.get('findings')
        require(isinstance(findings, list), 'findings list required, including empty if no findings')
        if 'request_id' in r:
            request = next((item for item in task['review_requests'] if item['id'] == r['request_id']), None)
            require(request is not None and request['generation'] == task['generation']
                    and not request['answered'] and request['reviewer'] == r.get('reviewer'),
                    'Review receipt does not match an outstanding current request')
            request['answered'] = True
        for finding in findings:
            require(isinstance(finding, dict), 'Invalid finding')
            ident = identifier(finding.get('id'))
            require(ident not in task['findings'], 'Finding ID already exists; resolve explicitly or use a namespaced ID')
            severity = text(finding, 'severity')
            require(severity in {'critical', 'high', 'medium', 'low'}, 'Unknown severity')
            task['findings'][ident] = {'id': ident, 'severity': severity, 'detail': text(finding, 'detail'),
                                     'status': 'open', 'generation': task['generation']}
        task['reviews'].append({'at': now(), 'generation': task['generation'],
            'reviewer': text(r, 'reviewer'), 'source': text(r, 'source'), 'findings': findings,
            'request_id': r.get('request_id')})
        task['next_action'] = 'Resolve blocking findings, or complete with acceptance evidence'

    def _op_resolve(self, state, r):
        task = self._task(state, r)
        require(task['status'] == 'validating', 'Resolve against revised implementation')
        ident = text(r, 'finding_id')
        require(ident in task['findings'], 'Unknown finding')
        task['findings'][ident].update(status='resolved', resolution=text(r, 'source'), resolved_at=now())

    def _completion(self, state, task):
        self._contracts(state, task)
        require(all(state['tasks'][d]['status'] == 'done' for d in task['depends_on']), 'Dependency is not done')
        require(self._proof(task, 'test'), 'Latest test evidence must pass')
        accepted = {}
        for item in task['evidence']:
            if item['generation'] == task['generation'] and item['kind'] == 'acceptance':
                for criterion in item['criteria']:
                    accepted[criterion] = item['outcome']
        require(all(accepted.get(i) == 'passed' for i in range(len(task['criteria']))), 'Acceptance incomplete or failed')
        require(not any(f['status'] == 'open' and f['severity'] in {'critical', 'high'}
                        for f in task['findings'].values()), 'Blocking review findings')
        require(all(r['answered'] for r in task['review_requests'] if r['generation'] == task['generation']),
                'Outstanding review requests')
        if task['review_required'] or task['risk'] == 'critical' or state['mode'] == 'DEEP':
            require(any(r['generation'] == task['generation'] for r in task['reviews']), 'Review required')
        if task['risk'] == 'critical' or state['mode'] == 'DEEP':
            require(self._proof(task, 'architecture'), 'Architecture gate required')

    def _op_complete(self, state, r):
        task = self._task(state, r)
        require(task['status'] == 'validating', 'Completion requires a successful implementation result')
        self._idle(task)
        self._completion(state, task)
        task.update(status='done', claimed=False, completed_at=now(), blocker=None, next_action='Included in delivery gate')

    def _op_rework(self, state, r):
        task = self._task(state, r)
        self._idle(task)
        require(task['status'] in {'done', 'validating'}, 'Rework requires completed implementation')
        text(r, 'reason')
        affected = {task['id']}
        changed = True
        while changed:
            changed = False
            for child in state['tasks'].values():
                if child['id'] not in affected and affected.intersection(child['depends_on']):
                    affected.add(child['id'])
                    changed = True
        for ident in affected:
            self._idle(state['tasks'][ident])
        for ident in affected:
            child = state['tasks'][ident]
            if child['status'] != 'cancelled':
                self._invalidate(child)

    def _op_block(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        task.update(status='blocked', blocker=text(r, 'reason'), next_action=text(r, 'next_action'))

    def _op_resume(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        require(task['status'] == 'blocked', 'Resume requires blocked task')
        text(r, 'reason')
        require(task['failure_streak'] < 2, 'Two failures: recovery diagnosis required')
        self._invalidate(task)

    def _op_recover(self, state, r):
        task = self._task(state, r)
        self._editable(task)
        require(task['status'] == 'blocked', 'Recovery requires blocked task')
        text(r, 'diagnosis')
        text(r, 'source')
        strings(r, 'discarded', True)
        self._invalidate(task)
        task['failure_streak'] = 0
        task['next_action'] = text(r, 'next_action')

    def _op_interrupt(self, state, r):
        task = self._task(state, r)
        require(task['run'] and task['run']['active'], 'No active run to interrupt')
        task.update(status='blocked', blocker=text(r, 'reason'),
                    next_action='Inspect host run; resources remain reserved until reconciliation')

    def _op_reconcile_run(self, state, r):
        task = self._run(state, r)
        outcome = text(r, 'outcome')
        require(outcome in {'stopped', 'completed'}, 'Outcome must be verified stopped/completed')
        task['run'].update(active=False, finished_at=now(), reconciliation=text(r, 'source'), outcome=outcome)
        cancelled = task['run']['stop_requested']
        task['status'] = 'cancelled' if cancelled else ('validating' if outcome == 'completed' else 'blocked')
        task['claimed'] = task['status'] == 'validating'
        task['next_action'] = text(r, 'next_action')
        task['blocker'] = 'Run stopped; resume after inspecting effects' if task['status'] == 'blocked' else None

    def _op_cancel(self, state, r):
        task = self._task(state, r)
        require(task['status'] not in TERMINAL, 'Task already terminal')
        reason = text(r, 'reason')
        if task['run'] and task['run']['active']:
            task['run']['stop_requested'] = True
            task.update(status='blocked', blocker=reason, next_action='Stop in host, then reconcile actual effects')
        else:
            task.update(status='cancelled', claimed=False, blocker=reason, next_action='Reconcile delivery scope; cancellation is not rollback')

    def _op_budget(self, state, r):
        require(not any(t['run'] and t['run']['active'] for t in state['tasks'].values()),
                'Budget changes require idle checkpoint')
        state['budget'] = {'limit': number(r.get('limit'), 'limit'), 'unit': text(r, 'unit'), 'source': text(r, 'source')}

    def _op_meter(self, state, r):
        kind = text(r, 'kind')
        require(kind in {'actual', 'estimate'}, 'Meter kind must be actual/estimate')
        unit, value = text(r, 'unit'), number(r.get('value'), 'value')
        if kind == 'actual':
            previous = [m for m in state['meters'] if m['kind'] == kind and m['unit'] == unit]
            require(not previous or value >= previous[-1]['value'], 'Cumulative measured usage cannot decrease')
        state['meters'].append({'at': now(), 'kind': kind, 'unit': unit, 'value': value, 'source': text(r, 'source')})

    def _op_checkpoint(self, state, r):
        task = self._task(state, r)
        require(task['status'] not in TERMINAL, 'Terminal checkpoint is frozen')
        task['next_action'] = text(r, 'next_action')
        text(r, 'source')

    def _op_deliver(self, state, r):
        require(bool(state['tasks']), 'No tasks to deliver')
        for task in state['tasks'].values():
            require(task['status'] == 'done', 'Delivery requires all tasks done; cancelled scope must be reported separately')
            self._completion(state, task)
        memory = text(r, 'memory')
        require(memory in {'captured', 'not-needed', 'not-authorized'}, 'Explicit memory disposition required')
        if memory == 'captured':
            require('memory' in state['artifacts'], 'Captured memory requires artifact provenance')
            artifact = state['artifacts']['memory']
            actual = hashlib.sha256(self._file(state, artifact['path']).read_bytes()).hexdigest()
            require(actual == artifact['sha256'], 'Memory changed outside registered revision')
        state['delivery'] = {'at': now(), 'source': text(r, 'source'), 'memory': memory, 'reason': text(r, 'reason')}
        state['status'] = 'delivered'
