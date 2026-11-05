"""Explicit, bounded, read-only import of local hook check receipts.

No hook engine is instantiated here and no command or journal output is copied.
The local journal and declared identities remain operator-controlled provenance.
"""
from datetime import datetime
from contextlib import closing
import math
from pathlib import Path, PurePosixPath
import sqlite3
import time

from hook_contract import EVENTS, MAX_JSON, HookError, digest, identifier, load_registry, parse_json, snapshot
from .store import WorkflowError


def require(condition, message):
    if not condition:
        raise WorkflowError(message)


def local_path(workspace, name):
    require(isinstance(name, str) and 0 < len(name) <= 2048 and '\x00' not in name,
            'Receipt path must be workspace-relative')
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and '..' not in relative.parts
            and str(relative) == name and name != '.', 'Receipt path must be normalized and workspace-relative')
    path = Path(workspace) / name
    try:
        require(path.resolve().is_relative_to(workspace) and not path.is_symlink(), 'Unsafe receipt path')
    except (OSError, ValueError, RuntimeError) as error:
        raise WorkflowError('Unsafe receipt path') from error
    return path


def validate_policy(workspace, policy, files):
    require(isinstance(policy, dict) and set(policy) <= {'hook_receipts', 'independent_review'},
            'Invalid evidence_policy')
    if 'independent_review' in policy:
        require(type(policy['independent_review']) is bool, 'independent_review must be boolean')
    if 'hook_receipts' in policy:
        config = policy['hook_receipts']
        require(isinstance(config, dict) and set(config) == {'journal', 'registry', 'event', 'required_hooks'},
                'hook_receipts requires journal, registry, event, required_hooks')
        local_path(workspace, config['journal'])
        local_path(workspace, config['registry'])
        require(isinstance(config['event'], str) and config['event'] in EVENTS, 'Unknown receipt event')
        hooks = config['required_hooks']
        require(isinstance(hooks, list) and 0 < len(hooks) <= 64
                and all(identifier(h) for h in hooks)
                and len(set(hooks)) == len(hooks), 'required_hooks must be nonempty unique hook IDs')
        require(isinstance(files, list) and 0 < len(files) <= 128
                and all(isinstance(f, str) and len(f) <= 2048 and '\x00' not in f for f in files)
                and len(set(files)) == len(files), 'Receipt policy requires nonempty bounded task files')
        try:
            snapshot(Path(workspace), files)
        except (HookError, OSError, ValueError) as error:
            raise WorkflowError('Invalid receipt file scope') from error
    return policy


def _journal_result(path, workspace, event_id):
    require(path.is_file(), 'Hook journal must exist; import never creates it')
    deadline = time.monotonic() + 0.25
    try:
        # mode=ro prohibits accidental creation, query_only prohibits writes even
        # if this code is extended. URI quoting handles spaces, ? and # in paths.
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=0.2)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA trusted_schema=OFF')
            db.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            row = db.execute('SELECT status, CASE WHEN length(CAST(result AS BLOB)) <= ? '
                             'THEN result ELSE NULL END FROM events WHERE workspace=? AND event_id=? LIMIT 1',
                             (MAX_JSON, workspace, event_id)).fetchone()
        require(row is not None and row[0] == 'done' and isinstance(row[1], str),
                'Missing, unfinished or oversized hook receipt')
        return parse_json(row[1])
    except (sqlite3.Error, HookError, OSError, ValueError) as error:
        raise WorkflowError('Hook receipt unavailable or invalid') from error


def read_receipt(state, task, event_id):
    """Return only verified identity, scope and timestamps; repeat at final gates."""
    policy = task.get('evidence_policy', {})
    require('hook_receipts' in policy, 'Task has no hook receipt policy')
    validate_policy(state['workspace'], policy, task['files'])
    config = policy['hook_receipts']
    run = task['run']
    require(run is not None and not run['active'], 'Receipt requires a finished implementation run')
    try:
        registry_path = local_path(state['workspace'], config['registry'])
        require(registry_path.is_file(), 'Receipt registry must exist')
        registry = load_registry(registry_path)
        registry_digest = digest(registry)
        scope = snapshot(Path(state['workspace']), task['files'])
        result = _journal_result(local_path(state['workspace'], config['journal']), state['workspace'], event_id)
        require(isinstance(result, dict) and result.get('event_id') == event_id
                and result.get('task_id') == task['id'] and result.get('event') == config['event']
                and result.get('status') == 'completed' and result.get('gate') == 'pass',
                'Hook receipt task/event/outcome mismatch')
        require(scope is not None and result.get('scope') == scope, 'Stale hook receipt file scope')
        require(result.get('registry_digest') == registry_digest, 'Stale hook receipt registry')
        rows = result.get('hooks')
        require(isinstance(rows, list) and len(rows) <= 64
                and all(isinstance(row, dict) for row in rows), 'Invalid hook receipt rows')
        started = datetime.fromisoformat(run['started_at']).timestamp()
        verified = []
        for hook_id in config['required_hooks']:
            hook = next((h for h in registry['hooks'] if h['id'] == hook_id), None)
            require(hook is not None and hook['enabled'] and hook['handler'] == 'command'
                    and hook['config']['read_only'] and config['event'] in hook['event'],
                    'Receipt policy requires enabled read-only command hooks')
            matches = [row for row in rows if row.get('hook_id') == hook_id]
            require(len(matches) == 1, 'Required hook receipt missing or duplicated')
            row = matches[0]
            checked = row.get('checked_at')
            require(row.get('task_id') == task['id'] and row.get('event_id') == event_id
                    and row.get('handler') == 'command' and row.get('status') == 'passed'
                    and row.get('error_code') is None and row.get('execution_mode') == hook['execution_mode'],
                    'Required hook did not pass for task/event')
            require(type(checked) in (float, int) and math.isfinite(checked)
                    and started <= checked <= time.time(), 'Hook receipt predates current run or has invalid timestamp')
            execution = row.get('execution_id')
            require(isinstance(execution, str) and 0 < len(execution) <= 128, 'Hook execution identity required')
            verified.append({'hook_id': hook_id, 'execution_id': execution, 'checked_at': checked})
        # Detect edits during import as well as edits between import and gates.
        require(snapshot(Path(state['workspace']), task['files']) == scope
                and digest(load_registry(registry_path)) == registry_digest, 'Receipt inputs changed during validation')
        return {'event_id': event_id, 'event': config['event'], 'workspace': state['workspace'],
                'task_id': task['id'], 'generation': task['generation'], 'run_id': run['id'],
                'registry_digest': registry_digest, 'scope': scope, 'hooks': verified}
    except (HookError, OSError, ValueError, TypeError, OverflowError) as error:
        raise WorkflowError('Hook receipt invalid or unavailable') from error
