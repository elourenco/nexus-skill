"""Single-machine POSIX JSON store with bounded locking and atomic snapshots."""
import errno
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Explicit platform boundary, not an unsafe unlocked fallback.
    fcntl = None


class WorkflowError(Exception):
    """An operation was rejected or its durable outcome needs reconciliation."""


class StateStore:
    def __init__(self, path: Path, timeout: float = 2.0):
        self.path = path.expanduser().resolve()
        self.timeout = timeout

    @contextmanager
    def _lock(self, exclusive: bool, create: bool = False):
        if fcntl is None:
            raise WorkflowError('This store requires POSIX flock; Windows is unsupported')
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(str(self.path) + '.lock', os.O_CREAT | os.O_RDWR, 0o600)
        except OSError as exc:
            raise WorkflowError(f'Cannot open store lock: {exc}') from exc
        try:
            deadline = time.monotonic() + self.timeout
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            while True:
                try:
                    fcntl.flock(fd, mode | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if exc.errno not in (errno.EAGAIN, errno.EACCES):
                        raise
                    if time.monotonic() >= deadline:
                        raise WorkflowError('Store busy; bounded lock timeout') from exc
                    time.sleep(0.02)
            yield
        finally:
            os.close(fd)

    def _read(self):
        try:
            state = json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(state, dict) or state.get('schema_version') != 1
                    or type(state.get('revision')) is not int
                    or not isinstance(state.get('tasks'), dict)
                    or not isinstance(state.get('history'), list)
                    or state['revision'] != len(state['history'])):
                raise ValueError('Invalid schema/version/revision')
            return state
        except (OSError, ValueError) as exc:
            raise WorkflowError(f'Cannot read state; do not reset it blindly: {exc}') from exc

    def read(self):
        with self._lock(False):
            return self._read()

    def create(self, state):
        with self._lock(True, create=True):
            if self.path.exists():
                raise WorkflowError('State already exists; use show/resume')
            self._write(state)
        return state

    def transact(self, mutate):
        with self._lock(True):
            state = self._read()
            changed = mutate(state)
            if changed:
                self._write(state)
            return state

    def _write(self, state):
        temporary = None
        replaced = False
        try:
            payload = json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
            fd, temporary = tempfile.mkstemp(prefix=f'.{self.path.name}.', dir=self.path.parent)
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            replaced = True
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except (OSError, ValueError) as exc:
            detail = 'outcome uncertain: inspect operation_id before retry' if replaced else 'not committed'
            raise WorkflowError(f'Persistence failed ({detail}): {exc}') from exc
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
