"""CLI contract tests: real subprocesses and isolated filesystem stores."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "skills/nexus/scripts/memory.py"
SCOPE = "project:alpha"


class MemoryCLIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "memory"
        self.inputs = Path(self.tmp.name) / "inputs"
        self.inputs.mkdir()
        self.counter = 0

    def command(self, *args, scope=SCOPE):
        return [sys.executable, str(CLI), "--root", str(self.root),
                "--scope", scope, *args]

    def run_cli(self, *args, ok=True, scope=SCOPE):
        result = subprocess.run(self.command(*args, scope=scope),
                                capture_output=True, text=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(result.stdout, "")
        try:
            body = json.loads(result.stdout if ok else result.stderr)
        except json.JSONDecodeError:
            self.fail("CLI response is not JSON: " + result.stdout[:100])
        return body, result

    def init(self):
        return self.run_cli("init", "--allow-write")

    def record(self, record_id="queue-policy", **changes):
        record = {
            "id": record_id, "scope": SCOPE, "type": "decision",
            "summary": "Queue retry policy uses bounded backoff",
            "content": "Retry transient worker failures at most three times.",
            "provenance": [{"reference": "src/queue.py",
                            "observed_at": "2026-10-31T12:00:00Z"}],
            "confidence": {"level": "high", "reason": "fixture verificada"},
            "status": "active", "related_entities": ["src/queue.py"],
            "tags": ["resilience"],
        }
        record.update(changes)
        return record

    def input_file(self, record):
        self.counter += 1
        path = self.inputs / (str(self.counter) + ".json")
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def put(self, record, expected=0, ok=True, allow=True):
        args = ["put", "--file", str(self.input_file(record)),
                "--expected-revision", str(expected), "--author", "agent-a"]
        if allow:
            args.append("--allow-write")
        return self.run_cli(*args, ok=ok)

    def get(self, record_id, revision=None):
        args = ["get", "--id", record_id]
        if revision is not None:
            args.extend(["--revision", str(revision)])
        return self.run_cli(*args)[0]

    def pack(self, *args):
        return self.run_cli("pack", "--task", "Inspect unrelated subsystem", *args)

    def snapshot(self):
        if not self.root.exists():
            return {}
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def test_write_requires_explicit_opt_in(self):
        self.run_cli("init", ok=False)
        self.assertEqual(self.snapshot(), {})
        self.init()
        before = self.snapshot()
        self.put(self.record(), allow=False, ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_persistence_revision_history_and_stale_compare_and_swap(self):
        self.init()
        created, _ = self.put(self.record())
        self.assertEqual((created["id"], created["revision"]), ("queue-policy", 1))
        first = self.get("queue-policy")
        for field in ("created_at", "updated_at", "author", "revision"):
            self.assertIn(field, first)
        self.assertEqual(first["author"], "agent-a")
        updated = self.record(status="stale")
        response, _ = self.put(updated, expected=1)
        self.assertEqual(response["revision"], 2)
        self.assertEqual(self.get("queue-policy")["status"], "stale")
        self.assertEqual(self.get("queue-policy", 1), first)
        before = self.snapshot()
        self.put(self.record(summary="Outdated writer"), expected=1, ok=False)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.get("queue-policy")["revision"], 2)
        self.assertTrue(list(self.root.rglob("records/queue-policy/00000001.json")))
        self.assertTrue(list(self.root.rglob("records/queue-policy/00000002.json")))

    def test_scope_cannot_read_or_write_another_project(self):
        self.init()
        self.put(self.record())
        self.run_cli("get", "--id", "queue-policy", scope="project:beta", ok=False)
        before = self.snapshot()
        self.put(self.record("wrong-scope", scope="project:beta"), ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_selective_retrieval_uses_metadata_and_explicit_selectors(self):
        self.init()
        self.put(self.record())
        self.put(self.record("render-policy", summary="Renderer font policy",
                             content="opaquecontentonly",
                             related_entities=["src/render.py"], tags=["rendering"]))
        for selector in (("--query", "retry"), ("--id", "queue-policy"),
                         ("--entity", "src/queue.py"), ("--tag", "resilience")):
            with self.subTest(selector=selector):
                body, _ = self.pack(*selector)
                self.assertEqual([r["id"] for r in body["records"]], ["queue-policy"])
                self.assertNotIn("content", body["records"][0])
                self.assertTrue(body["records"][0]["provenance"])
        body, _ = self.pack("--query", "opaquecontentonly")
        self.assertEqual(body["records"], [])
        body, _ = self.pack("--id", "queue-policy", "--tag", "rendering")
        self.assertEqual({r["id"] for r in body["records"]},
                         {"queue-policy", "render-policy"})

    def test_pack_hard_budget_accounts_for_entire_serialized_response(self):
        self.init()
        self.put(self.record(content="Detailed worker behavior. " * 300))
        for budget in (600, 2000, 12000):
            body, result = self.pack("--id", "queue-policy", "--details",
                                     "--max-chars", str(budget))
            length = len(result.stdout.strip())
            self.assertLessEqual(length, budget)
            self.assertEqual(body["metrics"]["provided_chars"], length)
            self.assertEqual(body["metrics"]["retrieved_records"], len(body["records"]))
            self.assertIsNone(body["metrics"]["provider_tokens"])
            self.assertIn("omitted_count", body)
        self.assertIn("content", body["records"][0])

    def test_inactive_superseded_and_expired_records_are_not_injected(self):
        self.init()
        self.put(self.record("current"))
        fixtures = [
            self.record("old", summary="Old retry policy", status="stale"),
            self.record("replaced", summary="Replaced retry policy", status="superseded",
                        superseded_by="current"),
            self.record("expired", summary="Expired retry policy", status="expired"),
            self.record("past-deadline", summary="Time limited retry policy",
                        expires_at="2000-01-01T00:00:00Z"),
        ]
        for record in fixtures:
            self.put(record)
        body, _ = self.pack("--query", "retry")
        self.assertEqual([r["id"] for r in body["records"]], ["current"])
        for record in fixtures:
            body, _ = self.pack("--id", record["id"])
            self.assertEqual(body["records"], [])
        self.assertEqual(self.get("replaced")["superseded_by"], "current")

    def test_exact_duplicate_does_not_create_another_record(self):
        self.init()
        self.put(self.record())
        before = self.snapshot()
        body, result = self.put(self.record("copy-policy"), ok=False)
        self.assertIn("duplic", (json.dumps(body) + result.stderr).lower())
        self.assertNotIn(self.record()["content"], result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_input_and_secret_rejection_leave_current_unchanged(self):
        self.init()
        self.put(self.record())
        invalid = []
        for field in ("id", "scope", "type", "summary", "provenance", "confidence",
                      "status", "related_entities"):
            record = self.record("invalid")
            del record[field]
            invalid.append(record)
        invalid.extend([
            self.record("invalid", type="unknown"),
            self.record("../escape"),
            self.record("invalid", status="superseded"),
            self.record("invalid", provenance=[]),
            self.record("invalid", expires_at="tomorrow"),
        ])
        no_content = self.record("invalid")
        del no_content["content"]
        invalid.append(no_content)
        for record in invalid:
            with self.subTest(record=record):
                before = self.snapshot()
                self.put(record, ok=False)
                self.assertEqual(self.snapshot(), before)
        secret = "Bearer " + "abcdefghijklmnopqrstuvwxyz123456789"
        before = self.snapshot()
        _, result = self.put(self.record("secret", content=secret), ok=False)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before)
        malformed = self.inputs / "malformed.json"
        malformed.write_text('{"summary":', encoding="utf-8")
        self.run_cli("put", "--file", str(malformed), "--expected-revision", "0",
                     "--author", "agent-a", "--allow-write", ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_markdown_is_not_implicitly_imported_or_modified(self):
        self.root.mkdir()
        legacy = self.root / "legacy.md"
        original = b"# Previous notes\nLegacy searchable phrase\n"
        legacy.write_bytes(original)
        self.init()
        body, _ = self.pack("--query", "Legacy searchable phrase")
        self.assertEqual(body["records"], [])
        converted = self.record("legacy-note", summary="Legacy searchable phrase",
                                reference="legacy.md")
        del converted["content"]
        self.put(converted)
        self.assertEqual(self.get("legacy-note")["reference"], "legacy.md")
        self.run_cli("reindex", "--allow-write")
        self.assertEqual(legacy.read_bytes(), original)
        body, _ = self.pack("--id", "legacy-note")
        self.assertEqual([r["id"] for r in body["records"]], ["legacy-note"])

    def test_reindex_recovers_derived_index_without_losing_history(self):
        self.init()
        self.put(self.record())
        first = self.get("queue-policy", 1)
        indexes = list(self.root.rglob("index.json"))
        self.assertTrue(indexes, "Store must expose a disposable derived index")
        for index in indexes:
            index.write_text("invalid derived index", encoding="utf-8")
        self.run_cli("reindex", "--allow-write")
        body, _ = self.pack("--id", "queue-policy")
        self.assertEqual([r["id"] for r in body["records"]], ["queue-policy"])
        self.assertEqual(self.get("queue-policy", 1), first)

    def test_concurrent_cas_has_one_winner_and_preserves_prior_revision(self):
        self.init()
        self.put(self.record())
        first = self.get("queue-policy", 1)
        processes = []
        for summary in ("Concurrent writer A", "Concurrent writer B"):
            file = self.input_file(self.record(summary=summary))
            processes.append(subprocess.Popen(self.command(
                "put", "--file", str(file), "--expected-revision", "1",
                "--author", "agent-a", "--allow-write"),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        self.addCleanup(lambda: [p.kill() for p in processes if p.poll() is None])
        results = [(p, *p.communicate(timeout=15)) for p in processes]
        self.assertEqual(sum(p.returncode == 0 for p, _, _ in results), 1)
        for process, stdout, stderr in results:
            body = json.loads(stdout if process.returncode == 0 else stderr)
            if process.returncode:
                self.assertEqual(stdout, "")
                self.assertRegex((json.dumps(body) + stderr).lower(), "busy|conflict|revision")
        current = self.get("queue-policy")
        self.assertEqual(current["revision"], 2)
        self.assertIn(current["summary"], ("Concurrent writer A", "Concurrent writer B"))
        self.assertEqual(self.get("queue-policy", 1), first)
        revisions = list(self.root.rglob("records/queue-policy/*.json"))
        self.assertEqual(len(revisions), 2)


if __name__ == "__main__":
    unittest.main()
