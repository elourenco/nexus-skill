"""Failure and recovery invariants on real files, locks and processes."""

import copy
import importlib.util
import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


CLI = Path(__file__).resolve().parents[1] / "skills/nexus/scripts/memory.py"
SPEC = importlib.util.spec_from_file_location("nexus_memory_failures", CLI)
memory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory)
SCOPE = "project:alpha"


class MemoryFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "store"
        self.store = memory.Store(self.root, SCOPE)
        with self.store.locked(write=True, initialize=True):
            self.store.init()
        self.record = {
            "id": "queue-policy", "scope": SCOPE, "type": "decision",
            "summary": "Worker retry policy", "content": "Bound retries to three attempts.",
            "provenance": [{"reference": "src/queue.py", "observed_at": "2026-10-31T12:00:00Z"}],
            "confidence": {"level": "high", "reason": "Verified fixture"},
            "status": "active", "related_entities": ["src/queue.py"],
        }
        self.put(self.record, 0)

    def put(self, record, revision, author="agent-a"):
        with self.store.locked(write=True):
            return self.store.put(record, revision, author)

    def get(self, revision=None):
        with self.store.locked():
            return self.store.get("queue-policy", revision)

    def pack(self):
        with self.store.locked():
            return self.store.pack("Inspect queue", ids=["queue-policy"])

    def updated(self):
        return dict(self.record, summary="Worker retry policy revision two")

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def test_replace_failure_before_publication_preserves_current_and_cleans_temporary(self):
        before = self.snapshot()
        with patch.object(memory.os, "replace", side_effect=OSError("injected replace failure")):
            with self.assertRaises(OSError):
                self.put(self.updated(), 1)
        self.assertEqual(self.get()["revision"], 1)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.root.rglob(".pending-*")), [])

    def test_index_failure_after_publication_reports_persisted_and_pack_recovers(self):
        atomic_json = memory.atomic_json

        def fail_index(path, value):
            if Path(path).name == "index.json":
                raise OSError("injected index failure")
            return atomic_json(path, value)

        with patch.object(memory, "atomic_json", side_effect=fail_index):
            result = self.put(self.updated(), 1)
        self.assertTrue(result["persisted"])
        self.assertFalse(result["index_updated"])
        self.assertEqual(self.get()["revision"], 2)
        before = self.snapshot()
        pack = self.pack()
        self.assertEqual(pack["records"][0]["revision"], 2)
        self.assertFalse(pack["metrics"]["index_cache_hit"])
        self.assertEqual(self.snapshot(), before, "Read recovery must not persist the rebuilt index")

    def test_missing_or_corrupt_index_is_disposable_without_read_side_writes(self):
        index = self.root / "index.json"
        for damage in ("missing", "invalid_json", "wrong_schema"):
            with self.subTest(damage=damage):
                if damage == "missing":
                    index.unlink(missing_ok=True)
                elif damage == "invalid_json":
                    index.write_text("{broken", encoding="utf-8")
                else:
                    index.write_text('{"records":42}', encoding="utf-8")
                before = self.snapshot()
                with self.store.locked():
                    catalog, _, cached = self.store.catalog()
                self.assertFalse(cached)
                self.assertEqual([r["id"] for r in catalog["records"]], ["queue-policy"])
                self.assertEqual(self.pack()["records"][0]["revision"], 1)
                self.assertEqual(self.snapshot(), before)

    def test_fsync_failure_after_replace_reconciles_published_revision_without_retry(self):
        fsync_dir = memory.fsync_dir
        folder = self.root / "records" / "queue-policy"

        def fail_after_record_replace(path):
            if Path(path) == folder:
                raise OSError("injected directory fsync failure")
            return fsync_dir(path)

        with patch.object(memory, "fsync_dir", side_effect=fail_after_record_replace):
            with self.assertRaises(OSError):
                self.put(self.updated(), 1)
        current = self.get()
        self.assertEqual((current["revision"], current["summary"]),
                         (2, "Worker retry policy revision two"))
        self.assertEqual(self.get(1)["summary"], "Worker retry policy")
        before = self.snapshot()
        with self.assertRaises(memory.MemoryError):
            self.put(self.updated(), 1)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(list(folder.glob("*.json"))), 2)

    def test_killed_lock_holder_releases_lock_and_pending_file_is_ignored(self):
        # The child dies while holding the actual POSIX lock with unpublished bytes on disk.
        script = """
import importlib.util, os, pathlib, signal, sys, tempfile
spec = importlib.util.spec_from_file_location('child_memory', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
store = module.Store(sys.argv[2], 'project:alpha')
with store.locked(write=True):
    fd, pending = tempfile.mkstemp(prefix='.pending-', dir=pathlib.Path(sys.argv[2]) / 'records' / 'queue-policy')
    os.write(fd, b'{unpublished')
    os.fsync(fd)
    os.close(fd)
    print('ready', flush=True)
    signal.pause()
"""
        child = subprocess.Popen([sys.executable, "-c", script, str(CLI), str(self.root)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        self.addCleanup(child.stdout.close)
        self.addCleanup(child.stderr.close)
        ready, _, _ = select.select([child.stdout], [], [], 10)
        self.assertTrue(ready, "Child failed to reach its locked checkpoint")
        self.assertEqual(child.stdout.readline().strip(), "ready")
        with self.assertRaisesRegex(memory.MemoryError, "busy"):
            self.put(self.updated(), 1)
        child.kill()
        child.communicate(timeout=10)
        pending = list(self.root.rglob(".pending-*"))
        self.assertEqual(len(pending), 1)
        self.assertEqual(self.get()["revision"], 1)
        self.assertEqual(self.put(self.updated(), 1)["revision"], 2)
        self.assertEqual(self.pack()["records"][0]["revision"], 2)
        self.assertEqual(pending[0].read_bytes(), b"{unpublished")

    def test_symlink_record_fails_closed_and_external_target_is_untouched(self):
        record_path = self.root / "records/queue-policy/00000001.json"
        outside = Path(self.tmp.name) / "outside-record.json"
        original = record_path.read_bytes()
        outside.write_bytes(original)
        record_path.unlink()
        record_path.symlink_to(outside)
        with self.assertRaisesRegex(memory.MemoryError, "symlink"):
            self.get()
        with self.assertRaisesRegex(memory.MemoryError, "symlink"):
            self.pack()
        with self.assertRaisesRegex(memory.MemoryError, "symlink"):
            self.put(self.updated(), 1)
        self.assertEqual(outside.read_bytes(), original)

    def test_symlink_index_is_ignored_and_never_overwrites_external_target(self):
        index = self.root / "index.json"
        outside = Path(self.tmp.name) / "outside-index.json"
        original = b"external bytes must remain private and unchanged"
        outside.write_bytes(original)
        index.unlink()
        index.symlink_to(outside)
        open_file = Path.open

        def guard_external_read(path, *args, **kwargs):
            if Path(path) == index or Path(path) == outside:
                raise AssertionError("The symlink target must never be opened")
            return open_file(path, *args, **kwargs)

        with patch.object(Path, "open", guard_external_read):
            self.assertEqual(self.pack()["records"][0]["revision"], 1)
            result = self.put(self.updated(), 1)
        self.assertTrue(result["persisted"])
        self.assertFalse(result["index_updated"])
        self.assertEqual(outside.read_bytes(), original)
        self.assertTrue(index.is_symlink())

    def test_symlink_lock_fails_closed_and_does_not_modify_external_target(self):
        lock = self.root / ".lock"
        outside = Path(self.tmp.name) / "outside-lock"
        outside.write_bytes(b"external lock target")
        lock.unlink()
        lock.symlink_to(outside)
        with self.assertRaisesRegex(memory.MemoryError, "symlink"):
            self.get()
        with self.assertRaisesRegex(memory.MemoryError, "symlink"):
            self.put(self.updated(), 1)
        self.assertEqual(outside.read_bytes(), b"external lock target")

    def test_corrupt_highest_revision_never_silently_returns_older_state(self):
        self.put(self.updated(), 1)
        latest = self.root / "records/queue-policy/00000002.json"
        latest.write_text("{broken", encoding="utf-8")
        with self.assertRaises(memory.MemoryError):
            self.get()
        with self.assertRaises(memory.MemoryError):
            self.pack()
        self.assertEqual(self.get(1)["revision"], 1)
        before = self.snapshot()
        with self.assertRaises(memory.MemoryError):
            self.put(self.updated(), 2)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_types_and_unknown_fields_are_rejected_without_mutation(self):
        cases = [("id", []), ("summary", 123), ("type", {}),
                 ("content", []), ("related_entities", "src/queue.py"),
                 ("tags", [None]), ("provenance", {}),
                 ("confidence", "high"), ("status", []),
                 ("expires_at", 123), ("unexpected", "field")]
        for field, value in cases:
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                record[field] = value
                before = self.snapshot()
                with self.assertRaises(memory.MemoryError):
                    self.put(record, 1)
                self.assertEqual(self.snapshot(), before)
        for revision in (True, "1", -1):
            with self.subTest(revision=revision):
                before = self.snapshot()
                with self.assertRaises(memory.MemoryError):
                    self.put(self.updated(), revision)
                self.assertEqual(self.snapshot(), before)

    def test_date_without_time_is_rejected_before_persistence(self):
        for field in ("expires_at", "provenance"):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                if field == "provenance":
                    record[field][0]["observed_at"] = "2026-10-31Z"
                else:
                    record[field] = "2026-10-31Z"
                before = self.snapshot()
                with self.assertRaisesRegex(memory.MemoryError, "invalid_timestamp"):
                    self.put(record, 1)
                self.assertEqual(self.snapshot(), before)

    def test_secrets_in_summary_provenance_or_author_never_reach_store(self):
        secret = "Bearer " + "abcdefghijklmnopqrstuvwxyz123456789"
        for field in ("summary", "provenance", "author"):
            with self.subTest(field=field):
                record = self.updated()
                author = "agent-a"
                if field == "provenance":
                    record["provenance"] = [{"reference": secret, "observed_at": "2026-10-31T12:00:00Z"}]
                elif field == "author":
                    author = secret
                else:
                    record[field] = secret
                before = self.snapshot()
                with self.assertRaises(memory.MemoryError) as raised:
                    self.put(record, 1, author)
                self.assertNotIn(secret, str(raised.exception))
                self.assertEqual(self.snapshot(), before)

    def test_changed_cache_metadata_cannot_override_authoritative_record(self):
        index_path = self.root / "index.json"
        original = json.loads(index_path.read_text(encoding="utf-8"))
        for field, value in (("status", "expired"), ("type", 42)):
            with self.subTest(field=field):
                altered = copy.deepcopy(original)
                altered["records"][0][field] = value
                index_path.write_text(json.dumps(altered), encoding="utf-8")
                pack = self.pack()
                self.assertEqual([r["id"] for r in pack["records"]], ["queue-policy"])
                self.assertEqual(pack["records"][0]["status"], "active")
                self.assertEqual(pack["records"][0]["type"], "decision")
                self.assertFalse(pack["metrics"]["index_cache_hit"])

    def test_pack_budget_includes_metrics_growth_after_omitted_retrievals(self):
        for number in range(15):
            record = dict(self.record, id="candidate-" + str(number),
                          summary="Queue candidate " + str(number), content="x" * 1000)
            self.put(record, 0)
        for budget in (512, 728, 1000):
            with self.subTest(budget=budget):
                try:
                    with self.store.locked():
                        pack = self.store.pack("queue", max_chars=budget)
                except memory.MemoryError as error:
                    self.assertEqual(str(error), "budget_too_small_for_task")
                else:
                    self.assertLessEqual(len(memory.dumps(pack)), budget)

    def test_secret_scanner_finishes_on_maximum_plain_content_without_pathological_backtracking(self):
        script = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location('scanner_memory', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.scan_secrets('x' * 32768)
print('ok')
"""
        try:
            result = subprocess.run([sys.executable, "-c", script, str(CLI)],
                                    capture_output=True, text=True, timeout=3)
        except subprocess.TimeoutExpired:
            self.fail("Secret scanning stalled on valid maximum-length plain content")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_json_credentials_nested_in_content_are_rejected_without_persistence(self):
        record = self.updated()
        record["content"] = "JSON config " + json.dumps({"password": "fictitious_password_12345"})
        before = self.snapshot()
        with self.assertRaises(memory.MemoryError) as raised:
            self.put(record, 1)
        self.assertNotIn("fictitious_password_12345", str(raised.exception))
        self.assertEqual(self.snapshot(), before)

    def test_unchanged_write_is_noop_but_new_provenance_publishes_revision(self):
        before = self.snapshot()
        result = self.put(copy.deepcopy(self.record), 1)
        self.assertEqual(result["revision"], 1)
        self.assertTrue(result["unchanged"])
        self.assertEqual(self.snapshot(), before)
        changed = copy.deepcopy(self.record)
        changed["provenance"][0]["observed_at"] = "2026-10-31T13:00:00Z"
        result = self.put(changed, 1)
        self.assertEqual(result["revision"], 2)
        self.assertEqual(self.get()["provenance"], changed["provenance"])
        self.assertEqual(self.get(1)["provenance"], self.record["provenance"])

    def test_cli_duplicate_json_keys_are_rejected_without_mutation(self):
        source = Path(self.tmp.name) / "ambiguous.json"
        # A parser that silently takes the last value would publish revision two.
        serialized = json.dumps(self.updated())
        source.write_text('{"summary":"discarded input",' + serialized[1:], encoding="utf-8")
        before = self.snapshot()
        result = subprocess.run([
            sys.executable, str(CLI), "--root", str(self.root), "--scope", SCOPE,
            "put", "--file", str(source), "--expected-revision", "1",
            "--author", "agent-a", "--allow-write",
        ], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("error", json.loads(result.stderr))
        self.assertNotIn("discarded input", result.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
