"""Read-only projections; replacing this adapter does not change orchestration."""
from datetime import datetime
from html import escape


def elapsed(start, finish):
    if start is None or finish is None:
        return None
    return max(0, (datetime.fromisoformat(finish) - datetime.fromisoformat(start)).total_seconds())


def metrics(state):
    tasks = list(state['tasks'].values())
    actual, estimated = {}, {}
    for meter in state['meters']:
        (actual if meter['kind'] == 'actual' else estimated)[meter['unit']] = {
            'value': meter['value'], 'source': meter['source'], 'at': meter['at']}
    return {
        'tasks': len(tasks), 'done': sum(t['status'] == 'done' for t in tasks),
        'cancelled': sum(t['status'] == 'cancelled' for t in tasks),
        'completion_rate': sum(t['status'] == 'done' for t in tasks) / len(tasks) if tasks else None,
        'failures': sum(len(t['failures']) for t in tasks),
        'retries': sum(max(0, t['attempts'] - 1) for t in tasks),
        'rework_events': sum(e['action'] == 'rework' for e in state['history']),
        'test_receipts': sum(e['kind'] in {'test', 'red'} for t in tasks for e in t['evidence']),
        'review_receipts': sum(len(t['reviews']) for t in tasks),
        'actual_usage': actual or None, 'estimated_usage': estimated or None,
        'durations_seconds': {t['id']: {
            'lead': elapsed(t['created_at'], t['completed_at']),
            'cycle': elapsed(t['started_at'], t['completed_at']),
        } for t in tasks},
        'duration_basis': 'UTC wall clock; cycle includes waiting/rework; null until done',
    }


def stage(state):
    if state['status'] == 'delivered':
        return 'MEMORY / DELIVERY completed'
    artifacts = state['artifacts']
    if state['mode'] != 'FAST':
        for kind in ('discovery', 'spec', 'plan'):
            if kind not in artifacts:
                return kind.upper()
    tasks = list(state['tasks'].values())
    if not tasks:
        return 'TASKS'
    if all(t['status'] == 'done' for t in tasks):
        return 'DELIVERY'
    if any(t['status'] == 'validating' for t in tasks):
        return 'TESTING / REVIEW'
    return 'EXECUTION'


def cell(value):
    value = '—' if value is None or value == '' else str(value)
    return escape(value, quote=False).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')


def markdown(state):
    stats = metrics(state)
    lines = [f'# NEXUS Todo — {cell(state["mode"])}', '',
        f'Revision: {state["revision"]} · Stage: {stage(state)} · Status: {state["status"]}',
        f'Progress: {stats["done"]}/{stats["tasks"]} tasks done (unweighted; not percentage of effort).', '',
        '| ID / task | Status | Priority | Depends on | Owner / agent | Provider / model | Blocker | Evidence | Next action |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for task in sorted(state['tasks'].values(), key=lambda t: (t['priority'], t['id'])):
        agent = (task['run'] or {}).get('agent') or {}
        evidence = [e for e in task['evidence'] if e['generation'] == task['generation']]
        rows = [task['id'] + ': ' + task['title'], task['status'], task['priority'],
            ', '.join(task['depends_on']), task['owner'] + (' / ' + agent['id'] if agent else ''),
            f'{agent.get("provider") or "unknown"} / {agent.get("model") or "unknown"}',
            task['blocker'], ', '.join(e['id'] + ':' + e['outcome'] for e in evidence), task['next_action']]
        lines.append('| ' + ' | '.join(cell(v) for v in rows) + ' |')
    lines += ['', '## Usage', '', f'Measured: {cell(stats["actual_usage"])}',
              f'Estimated (separate): {cell(stats["estimated_usage"])}', '',
              'Projection only. Mutate via CLI apply or a host adapter using the same revision/operation contract.',
              'Evidence and provider metadata are attributed receipts; this view does not independently verify them.', '']
    return '\n'.join(lines)
