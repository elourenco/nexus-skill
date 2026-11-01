"""Observable engine behavior using real SQLite, subprocesses and files."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "skills/nexus/scripts/hook_engine.py"


def hook(**updates):
    value = {
        "id": "check", "description": "Fixture validation", "event": ["code.post_edit"],
        "trigger_conditions": {"profiles": ["FAST", "BALANCED", "DEEP"], "any_flags": []},
        "execution_mode": "ENFORCE", "priority": 10, "inputs": [], "outputs": ["status"],
        "timeout": 1, "retry_policy": {"max_attempts": 1}, "failure_policy": "block",
        "permissions": ["command:check"], "enabled": True, "supported_adapters": ["local"],
        "handler": "command", "config": {"argv": [sys.executable, "check.py"], "read_only": True},
    }
    value.update(updates)
    return value


class HooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        (self.workspace / "source.txt").write_text("version one")
        (self.workspace / "check.py").write_text("print('synthetic-secret-not-for-logs')\n")
        self.state = self.root / "private/state.sqlite"
        self.registry = self.root / "registry.json"
        self.write_registry([hook()])

    def write_registry(self, hooks):
        self.registry.write_text(json.dumps({"version": 1, "hooks": hooks}))

    def event(self, **updates):
        value = {"event_id": "event-1", "task_id": "task-1", "event": "code.post_edit",
                 "profile": "BALANCED", "flags": [], "files": ["source.txt", "check.py"], "inputs": {}}
        value.update(updates)
        return value

    def argv(self, action="run", allow=("command:check",)):
        args = [sys.executable, str(ENGINE), action, "--workspace", str(self.workspace),
                "--state", str(self.state), "--registry", str(self.registry)]
        for permission in allow:
            args.extend(["--allow", permission])
        return args

    def run_event(self, event=None, allow=("command:check",)):
        run = subprocess.run(self.argv(allow=allow), input=json.dumps(event or self.event()),
                             text=True, capture_output=True, timeout=10)
        self.assertTrue(run.stdout.startswith("{"), run.stderr)
        return run.returncode, json.loads(run.stdout)

    def test_command_executes_and_redacts_output(self):
        code, result = self.run_event()
        self.assertEqual(code, 0)
        self.assertEqual(result["hooks"][0]["status"], "passed")
        self.assertNotIn("synthetic-secret", json.dumps(result))
        self.assertNotIn(b"synthetic-secret", self.state.read_bytes())

    def test_denied_command_never_runs(self):
        (self.workspace / "check.py").write_text("from pathlib import Path\nPath('effect').touch()")
        code, result = self.run_event(allow=())
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "PERMISSION_DENIED")
        self.assertFalse((self.workspace / "effect").exists())

    def test_duplicate_event_does_not_repeat_effect(self):
        (self.workspace / "check.py").write_text("with open('count', 'a') as f: f.write('x')\n")
        first = self.run_event()
        second = self.run_event()
        self.assertEqual(first[0], 0)
        self.assertTrue(second[1]["replayed"])
        self.assertEqual((self.workspace / "count").read_text(), "x")

    def test_event_identity_cannot_be_reused_with_new_input(self):
        self.run_event()
        code, result = self.run_event(self.event(task_id="other-task"))
        self.assertEqual(code, 3)
        self.assertEqual(result["error_code"], "EVENT_CONFLICT")

    def test_timeout_is_bounded_and_gate_closed(self):
        (self.workspace / "check.py").write_text("import time\ntime.sleep(30)")
        self.write_registry([hook(timeout=0.1, retry_policy={"max_attempts": 2})])
        start = time.monotonic()
        code, result = self.run_event()
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["attempts"], 2)
        self.assertEqual(result["hooks"][0]["error_code"], "TIMEOUT")

    def test_validation_failure_is_not_retried(self):
        (self.workspace / "check.py").write_text("with open('count','a') as f: f.write('x')\nraise SystemExit(1)")
        self.write_registry([hook(retry_policy={"max_attempts": 3})])
        code, result = self.run_event()
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["status"], "failed")
        self.assertEqual((self.workspace / "count").read_text(), "x")

    def test_observe_cannot_hide_command_execution(self):
        self.write_registry([hook(execution_mode="OBSERVE", failure_policy="warn")])
        code, result = self.run_event()
        self.assertEqual(code, 3)
        self.assertEqual(result["error_code"], "INVALID_REGISTRY")

    def test_mutating_commands_cannot_retry(self):
        self.write_registry([hook(execution_mode="EXECUTE", failure_policy="warn",
                                  config={"argv": [sys.executable, "check.py"], "read_only": False},
                                  retry_policy={"max_attempts": 2})])
        self.assertEqual(self.run_event()[0], 3)

    def test_advice_is_not_a_completed_cognitive_review(self):
        self.write_registry([hook(handler="advice", execution_mode="ADVISE", failure_policy="warn",
                                  permissions=[], config={"prompt": "Compare alternatives."})])
        code, result = self.run_event(allow=())
        self.assertEqual(code, 0)
        row = result["hooks"][0]
        self.assertEqual(row["status"], "advised")
        self.assertIsNone(row["model_usage"])
        self.assertEqual(row["gate_impact"], "none")

    def test_fast_omits_deep_advice(self):
        self.write_registry([hook(handler="advice", execution_mode="ADVISE", failure_policy="warn",
                                  permissions=[], config={"prompt": "Deep review"},
                                  trigger_conditions={"profiles": ["DEEP"], "any_flags": ["high_risk"]})])
        _, fast = self.run_event(self.event(profile="FAST", flags=["high_risk"]), allow=())
        _, deep = self.run_event(self.event(event_id="deep", profile="DEEP", flags=["high_risk"]), allow=())
        self.assertEqual(fast["hooks"], [])
        self.assertEqual(len(deep["hooks"]), 1)

    def test_duplicate_hook_ids_rejected(self):
        self.write_registry([hook(), hook()])
        self.assertEqual(self.run_event()[0], 3)

    def test_path_escape_and_unknown_event_rejected(self):
        for event in [self.event(files=["../registry.json"]), self.event(event="invented.event")]:
            with self.subTest(event=event):
                self.assertEqual(self.run_event(event)[0], 3)

    def test_recursive_command_is_stopped(self):
        (self.workspace / "check.py").write_text(
            "import os, subprocess, sys\n"
            f"r = subprocess.run({self.argv()!r}, input='{{}}', text=True, capture_output=True)\n"
            "assert 'RECURSION_LIMIT' in r.stdout, r.stdout\n")
        self.assertEqual(self.run_event()[0], 0)

    def wait_for_claim(self, process):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail(process.communicate())
            if (self.workspace / "started").exists():
                return
            time.sleep(0.02)
        self.fail("command did not start")

    def start_slow_command(self):
        (self.workspace / "check.py").write_text(
            "from pathlib import Path\nimport time\nPath('started').touch()\ntime.sleep(1)\n"
            "with open('count','a') as f: f.write('x')\n")
        self.write_registry([hook(timeout=3)])
        process = subprocess.Popen(self.argv(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        process.stdin.write(json.dumps(self.event()))
        process.stdin.close()
        process.stdin = None
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.wait_for_claim(process)
        return process

    def test_concurrent_processes_never_duplicate_work(self):
        process = self.start_slow_command()
        code, result = self.run_event()
        self.assertEqual(code, 3)
        self.assertEqual(result["error_code"], "IN_PROGRESS")
        other_code, other = self.run_event(self.event(event_id="event-2"))
        self.assertEqual(other_code, 3)
        self.assertEqual(other["error_code"], "WORKSPACE_BUSY")
        process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0)
        self.assertEqual((self.workspace / "count").read_text(), "x")

    def test_crash_requires_reconciliation_not_replay(self):
        process = self.start_slow_command()
        process.kill()
        process.communicate(timeout=5)
        code, result = self.run_event()
        self.assertEqual(code, 3)
        self.assertEqual(result["error_code"], "IN_PROGRESS")
        recovered = subprocess.run(self.argv("recover", allow=("state.reconcile",)) +
                                   ["--event-id", "event-1", "--confirmed-effects"],
                                   text=True, capture_output=True, timeout=5)
        self.assertEqual(recovered.returncode, 3)
        self.assertEqual(json.loads(recovered.stdout)["error_code"], "CHILD_STILL_RUNNING")
        # Reconcile the real child: wait for its known fixture effect and exit.
        with sqlite3.connect(self.state) as db:
            child = db.execute("SELECT child_pgid FROM events").fetchone()[0]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.killpg(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        recovered = subprocess.run(self.argv("recover", allow=("state.reconcile",)) +
                                   ["--event-id", "event-1", "--confirmed-effects"],
                                   text=True, capture_output=True, timeout=5)
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        self.assertEqual(self.run_event()[0], 2)  # abandoned event never re-executes

    def test_workspace_isolation_in_shared_state(self):
        self.run_event()
        second = self.root / "second"
        second.mkdir()
        (second / "source.txt").write_text("different")
        (second / "check.py").write_text("raise SystemExit(1)")
        self.workspace = second
        self.assertEqual(self.run_event()[0], 2)

    def test_completion_rejects_stale_receipt(self):
        completion = hook(id="completion", event=["task.completed"], handler="evidence",
                          permissions=[], config={"required_hooks": ["check"]})
        self.write_registry([hook(), completion])
        self.assertEqual(self.run_event()[0], 0)
        event = self.event(event_id="complete-1", event="task.completed", inputs={"evidence": ["event-1"]})
        self.assertEqual(self.run_event(event)[0], 0)
        (self.workspace / "source.txt").write_text("new version")
        event["event_id"] = "complete-2"
        code, result = self.run_event(event)
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "MISSING_EVIDENCE")

    def test_memory_versioning_and_scoped_retrieval(self):
        write = hook(id="memory", handler="memory.write", event=["memory.capture", "memory.refresh"],
                     execution_mode="EXECUTE", permissions=["memory.write"], failure_policy="warn", config={})
        read = hook(id="retrieve", handler="memory.read", event=["memory.retrieve"], execution_mode="OBSERVE",
                    permissions=["memory.read"], failure_policy="warn", config={})
        self.write_registry([write, read])
        memory = {"id": "decision-1", "content": "Synthetic decision", "source": "fixture", "expected_version": 0}
        event = self.event(event="memory.capture", inputs={"memory": memory})
        self.assertEqual(self.run_event(event, allow=("memory.write",))[0], 0)
        self.run_event(event, allow=("memory.write",))
        memory["content"] = "Replacement"
        code, conflict = self.run_event(self.event(event_id="write-2", event="memory.refresh", inputs={"memory": memory}), allow=("memory.write",))
        self.assertEqual(conflict["hooks"][0]["error_code"], "MEMORY_CONFLICT")
        memory["expected_version"] = 1
        self.run_event(self.event(event_id="write-3", event="memory.refresh", inputs={"memory": memory}), allow=("memory.write",))
        _, result = self.run_event(self.event(event_id="read", event="memory.retrieve", inputs={"memory_ids": ["decision-1"]}), allow=("memory.read",))
        record = result["hooks"][0]["output"]["records"][0]
        self.assertEqual(record["version"], 2)
        self.assertEqual(record["content"], "Replacement")
        read_event = self.event(event_id="read", event="memory.retrieve", inputs={"memory_ids": ["decision-1"]})
        _, replay = self.run_event(read_event, allow=("memory.read",))
        self.assertEqual(replay["hooks"][0]["output"], result["hooks"][0]["output"])

    def test_circuit_stops_repeated_operational_failures(self):
        (self.workspace / "check.py").write_text("import time\ntime.sleep(20)")
        self.write_registry([hook(timeout=0.05)])
        for i in range(3):
            self.run_event(self.event(event_id=f"fail-{i}"))
        _, result = self.run_event(self.event(event_id="circuit"))
        self.assertEqual(result["hooks"][0]["error_code"], "CIRCUIT_OPEN")
        self.assertEqual(result["hooks"][0]["attempts"], 0)
        self.run_event(self.event(event_id="denied"), allow=())
        _, protected = self.run_event(self.event(event_id="still-open"))
        self.assertEqual(protected["hooks"][0]["error_code"], "CIRCUIT_OPEN")

    def test_nul_in_path_is_structured_failure(self):
        code, result = self.run_event(self.event(files=["\x00"]))
        self.assertEqual(code, 3)
        self.assertIn(result["error_code"], ("INVALID_EVENT", "INVALID_PATH"))

    def test_cache_reuses_only_unchanged_explicit_scope(self):
        (self.workspace / "check.py").write_text("with open('count','a') as f: f.write('x')\n")
        self.write_registry([hook(config={"argv": [sys.executable, "check.py"], "read_only": True, "cache_seconds": 60})])
        self.run_event()
        _, reused = self.run_event(self.event(event_id="cache-2"))
        self.assertEqual(reused["hooks"][0]["attempts"], 0)
        self.assertEqual((self.workspace / "count").read_text(), "x")
        (self.workspace / "source.txt").write_text("changed")
        self.run_event(self.event(event_id="cache-3"))
        self.assertEqual((self.workspace / "count").read_text(), "xx")

    def test_cache_invalidated_when_executable_permission_removed(self):
        script = self.workspace / "check.py"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o700)
        self.write_registry([hook(config={"argv": ["./check.py"], "read_only": True, "cache_seconds": 60})])
        self.assertEqual(self.run_event()[0], 0)
        _, cached = self.run_event(self.event(event_id="cached"))
        self.assertEqual(cached["hooks"][0]["attempts"], 0)
        script.chmod(0o600)
        code, result = self.run_event(self.event(event_id="not-executable"))
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "COMMAND_UNAVAILABLE")
        self.assertEqual(result["hooks"][0]["attempts"], 1)

    def test_completion_rejects_receipt_after_executable_permission_removed(self):
        script = self.workspace / "check.py"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o700)
        completion = hook(id="completion", event=["task.completed"], handler="evidence",
                          permissions=[], config={"required_hooks": ["check"]})
        self.write_registry([hook(config={"argv": ["./check.py"], "read_only": True}), completion])
        self.assertEqual(self.run_event()[0], 0)
        complete = self.event(event_id="complete", event="task.completed", inputs={"evidence": ["event-1"]})
        self.assertEqual(self.run_event(complete)[0], 0)
        script.chmod(0o600)
        complete["event_id"] = "complete-after-chmod"
        code, result = self.run_event(complete)
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "MISSING_EVIDENCE")

    def test_memory_lone_surrogates_rejected_before_claim_and_next_event_succeeds(self):
        write = hook(id="memory", handler="memory.write", event=["memory.capture"],
                     execution_mode="EXECUTE", permissions=["memory.write"], failure_policy="warn", config={})
        self.write_registry([write])
        for field in ("content", "source"):
            for surrogate in ("\ud800", "\udfff"):
                with self.subTest(field=field, surrogate=repr(surrogate)):
                    self.state = self.root / f"{field}-{ord(surrogate)}.sqlite"
                    memory = {"id": "decision-1", "content": "Decisão válida 🌎", "source": "fixture", "expected_version": 0}
                    malformed = dict(memory, **{field: surrogate})
                    code, result = self.run_event(self.event(event="memory.capture", inputs={"memory": malformed}),
                                                  allow=("memory.write",))
                    self.assertEqual(code, 3)
                    self.assertEqual(result["error_code"], "INVALID_EVENT")
                    self.assertFalse(self.state.exists(), "invalid event must not open state or claim workspace")
                    code, result = self.run_event(self.event(event_id="valid-next", event="memory.capture", inputs={"memory": memory}),
                                                  allow=("memory.write",))
                    self.assertEqual(code, 0)
                    self.assertEqual(result["hooks"][0]["output"]["version"], 1)
                    with sqlite3.connect(self.state) as db:
                        self.assertEqual(db.execute("SELECT content FROM memory").fetchone()[0], memory["content"])
                        self.assertEqual(db.execute("SELECT count(*) FROM events WHERE status='running'").fetchone()[0], 0)

    def test_lone_surrogate_path_rejected_before_opening_state(self):
        code, result = self.run_event(self.event(files=["\ud800"]))
        self.assertEqual(code, 3)
        self.assertEqual(result["error_code"], "INVALID_EVENT")
        self.assertFalse(self.state.exists())

    def test_command_mutating_declared_scope_cannot_create_evidence(self):
        (self.workspace / "check.py").write_text("from pathlib import Path\nPath('source.txt').write_text('changed')")
        code, result = self.run_event()
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "STALE_INPUT")

    def test_uncertain_mutation_stops_next_event_until_reconciled(self):
        (self.workspace / "check.py").write_text("from pathlib import Path\nPath('effect').touch()\nraise SystemExit(1)")
        self.write_registry([hook(execution_mode="EXECUTE", failure_policy="warn",
                                  config={"argv": [sys.executable, "check.py"], "read_only": False})])
        code, result = self.run_event()
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][0]["error_code"], "UNCERTAIN_EFFECT")
        self.assertTrue((self.workspace / "effect").exists())
        self.assertEqual(self.run_event(self.event(event_id="new"))[1]["error_code"], "WORKSPACE_BUSY")

    def test_sigterm_kills_child_and_leaves_reconciliation_marker(self):
        process = self.start_slow_command()
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 3, stderr)
        self.assertEqual(json.loads(stdout)["status"], "interrupted")
        self.assertFalse((self.workspace / "count").exists())
        self.assertEqual(self.run_event()[1]["error_code"], "IN_PROGRESS")

    def test_fast_budget_refuses_long_command_before_spawn(self):
        self.write_registry([hook(timeout=60)])
        code, result = self.run_event(self.event(profile="FAST"))
        self.assertEqual(code, 2)
        self.assertEqual(result["error_code"], "EVENT_BUDGET_EXCEEDED")
        self.assertEqual(result["hooks"], [])

    def test_invalid_json_is_a_structured_failure(self):
        for value in ['{"event_id":"a","event_id":"b"}', '{"x":NaN}', '[' * 2000]:
            with self.subTest(value=value[:30]):
                run = subprocess.run(self.argv(), input=value, text=True, capture_output=True, timeout=5)
                self.assertEqual(run.returncode, 3)
                self.assertEqual(json.loads(run.stdout)["gate"], "block")
                self.assertNotIn("Traceback", run.stderr)

    def test_permissions_cannot_be_added_by_payload(self):
        event = self.event()
        event["permissions"] = ["command:check"]
        self.assertEqual(self.run_event(event, allow=())[0], 3)

    def test_builtin_timeout_is_enforced(self):
        self.write_registry([hook(handler="advice", execution_mode="ADVISE", failure_policy="warn",
                                  permissions=[], timeout=0.000001, config={"prompt": "Question"})])
        _, result = self.run_event(allow=())
        self.assertEqual(result["hooks"][0]["error_code"], "TIMEOUT")

    def test_disabled_required_check_does_not_allow_completion(self):
        completion = hook(id="completion", event=["task.completed"], handler="evidence",
                          permissions=[], config={"required_hooks": ["check"]})
        self.write_registry([hook(enabled=False), completion])
        self.run_event()
        event = self.event(event_id="complete", event="task.completed", inputs={"evidence": ["event-1"]})
        self.assertEqual(self.run_event(event)[0], 2)

    def test_successful_mutation_may_change_declared_files(self):
        (self.workspace / "check.py").write_text("from pathlib import Path\nPath('source.txt').write_text('changed')")
        self.write_registry([hook(execution_mode="EXECUTE", failure_policy="warn",
                                  config={"argv": [sys.executable, "check.py"], "read_only": False})])
        code, result = self.run_event()
        self.assertEqual(code, 0)
        self.assertEqual(result["hooks"][0]["status"], "passed")
        self.assertEqual((self.workspace / "source.txt").read_text(), "changed")

    def test_cache_cannot_approve_files_mutated_earlier_in_same_event(self):
        (self.workspace / "check.py").write_text("from pathlib import Path\nraise SystemExit(0 if Path('source.txt').read_text() == 'version one' else 1)")
        mutator = hook(id="mutator", execution_mode="EXECUTE", failure_policy="warn", priority=1,
                       permissions=["command:mutator"],
                       trigger_conditions={"profiles": ["BALANCED"], "any_flags": ["mutate"]},
                       config={"argv": [sys.executable, "-c", "from pathlib import Path; Path('source.txt').write_text('changed')"], "read_only": False})
        self.write_registry([mutator, hook(config={"argv": [sys.executable, "check.py"], "read_only": True, "cache_seconds": 60})])
        self.assertEqual(self.run_event()[0], 0)
        code, result = self.run_event(self.event(event_id="after-mutation", flags=["mutate"]),
                                      allow=("command:check", "command:mutator"))
        self.assertEqual(code, 2)
        self.assertEqual(result["hooks"][-1]["error_code"], "STALE_INPUT")

    def test_timed_out_memory_read_does_not_journal_content(self):
        write = hook(id="memory", handler="memory.write", event=["memory.capture"],
                     execution_mode="EXECUTE", permissions=["memory.write"], failure_policy="warn", config={})
        read = hook(id="retrieve", handler="memory.read", event=["memory.retrieve"], execution_mode="OBSERVE",
                    permissions=["memory.read"], failure_policy="warn", timeout=0.000001, config={})
        self.write_registry([write, read])
        memory = {"id": "private-1", "content": "private-synthetic-content", "source": "fixture", "expected_version": 0}
        self.run_event(self.event(event="memory.capture", inputs={"memory": memory}), allow=("memory.write",))
        _, result = self.run_event(self.event(event_id="read", event="memory.retrieve", inputs={"memory_ids": ["private-1"]}), allow=("memory.read",))
        self.assertEqual(result["hooks"][0]["error_code"], "TIMEOUT")
        with sqlite3.connect(self.state) as db:
            journal = db.execute("SELECT result FROM events WHERE event_id='read'").fetchone()[0]
        self.assertNotIn("private-synthetic-content", journal)

    def test_default_registry_runs_validation_and_completion(self):
        self.registry = ROOT / "skills/nexus/assets/hooks.json"
        (self.workspace / "scripts").mkdir()
        (self.workspace / "scripts/validate.py").write_text("from pathlib import Path\nPath('checked').touch()")
        files = ["source.txt", "scripts/validate.py"]
        code, result = self.run_event(self.event(profile="FAST", files=files), allow=("command:validation.run",))
        self.assertEqual(code, 0)
        self.assertTrue((self.workspace / "checked").exists())
        code, completed = self.run_event(self.event(event_id="done", event="task.completed", profile="FAST",
                                                  files=files, inputs={"evidence": ["event-1"]}), allow=())
        self.assertEqual(code, 0)
        self.assertEqual(completed["hooks"][-1]["output"]["verified_hooks"], ["validation.run"])


if __name__ == "__main__":
    unittest.main()
