#!/usr/bin/env python3
"""Local, explicit-call NEXUS hook executor. No native host hooks are installed."""
import argparse
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import signal
import sqlite3
import sys
import time
import uuid

from hook_contract import (EVENTS, MAX_JSON, HookError, canonical, digest, load_registry,
                           parse_json, require, snapshot, validate_event)
from hook_handlers import dispatch

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "assets/hooks.json"


class Engine:
    def __init__(self, workspace, state, registry, permissions):
        self.workspace = workspace.resolve(strict=True)
        require(self.workspace.is_dir() and os.name == "posix", "UNSUPPORTED_WORKSPACE")
        self.registry = registry
        self.registry_digest = digest(registry)
        self.permissions = set(permissions)
        self.scope = None
        state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(not state.is_symlink(), "UNSAFE_STATE_PATH")
        try:
            fd = os.open(state, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            require(state.is_file(), "UNSAFE_STATE_PATH")
        else:
            os.close(fd)
        self.db = sqlite3.connect(str(state), timeout=0.2, isolation_level=None)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS events(
                workspace TEXT NOT NULL, event_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT, owner_pid INTEGER NOT NULL, child_pgid INTEGER,
                PRIMARY KEY(workspace,event_id));
            CREATE UNIQUE INDEX IF NOT EXISTS active_workspace ON events(workspace)
                WHERE status IN ('running','uncertain');
            CREATE TABLE IF NOT EXISTS failures(
                workspace TEXT, registry_digest TEXT, hook_id TEXT, count INTEGER NOT NULL,
                PRIMARY KEY(workspace,registry_digest,hook_id));
            CREATE TABLE IF NOT EXISTS memory(
                workspace TEXT, record_id TEXT, version INTEGER, content TEXT, source TEXT,
                created REAL, active INTEGER, event_id TEXT,
                PRIMARY KEY(workspace,record_id,version));
        """)

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def claim(self, event, fingerprint):
        with self.transaction():
            previous = self.db.execute("SELECT fingerprint,status,result FROM events WHERE workspace=? AND event_id=?",
                                       (str(self.workspace), event["event_id"])).fetchone()
            if previous:
                require(previous[0] == fingerprint, "EVENT_CONFLICT")
                require(previous[1] not in ("running", "uncertain"), "IN_PROGRESS")
                result = json.loads(previous[2])
                for item in result.get("hooks", []):
                    if item["handler"] == "memory.read" and item["status"] == "observed":
                        records = []
                        for reference in item["output"]["records"]:
                            memory = self.db.execute(
                                "SELECT content,source,created FROM memory WHERE workspace=? AND record_id=? AND version=?",
                                (str(self.workspace), reference["id"], reference["version"])).fetchone()
                            require(memory is not None, "MEMORY_REPLAY_UNAVAILABLE")
                            records.append(dict(reference, content=memory[0], source=memory[1], created=memory[2]))
                        item["output"]["records"] = records
                result["replayed"] = True
                return result
            busy = self.db.execute("SELECT 1 FROM events WHERE workspace=? AND status IN ('running','uncertain')",
                                   (str(self.workspace),)).fetchone()
            require(not busy, "WORKSPACE_BUSY")
            self.db.execute("INSERT INTO events VALUES(?,?,?,'running',NULL,?,NULL)",
                            (str(self.workspace), event["event_id"], fingerprint, os.getpid()))
        return None

    def failure_count(self, hook_id):
        row = self.db.execute("SELECT count FROM failures WHERE workspace=? AND registry_digest=? AND hook_id=?",
                              (str(self.workspace), self.registry_digest, hook_id)).fetchone()
        return row[0] if row else 0

    def cached(self, hook, event):
        age = hook["config"].get("cache_seconds", 0)
        if not age or self.scope is None:
            return None
        rows = self.db.execute("SELECT event_id,result FROM events WHERE workspace=? AND status='done' ORDER BY rowid DESC LIMIT 64",
                               (str(self.workspace),)).fetchall()
        for event_id, raw in rows:
            result = json.loads(raw)
            if (result.get("scope") != self.scope or result.get("registry_digest") != self.registry_digest
                    or result.get("task_id") != event["task_id"]):
                continue
            for item in result.get("hooks", []):
                if (item["hook_id"] == hook["id"] and item["status"] == "passed"
                        and 0 <= time.time() - item["checked_at"] <= age):
                    return {"reused_from": event_id, "checked_at": item["checked_at"]}
        return None

    def execute_hook(self, hook, event):
        started = time.monotonic()
        row = {"hook_id": hook["id"], "event_id": event["event_id"], "task_id": event["task_id"],
               "execution_id": str(uuid.uuid4()), "status": "error", "duration_ms": None,
               "execution_mode": hook["execution_mode"], "error_code": None, "model_usage": None,
               "gate_impact": "none", "attempts": 0, "handler": hook["handler"], "output": {},
               "checked_at": time.time()}
        try:
            require(set(hook["permissions"]) <= self.permissions, "PERMISSION_DENIED")
            require(self.failure_count(hook["id"]) < 3, "CIRCUIT_OPEN")
            reused = self.cached(hook, event) if hook["handler"] == "command" else None
            if reused:
                row.update(status="passed", output={"reused_from": reused["reused_from"]}, checked_at=reused["checked_at"])
            else:
                for attempt in range(1, hook["retry_policy"]["max_attempts"] + 1):
                    row["attempts"] = attempt
                    try:
                        attempt_started = time.monotonic()
                        row["status"], row["output"] = dispatch(hook, self, event)
                        if hook["handler"] != "command" and time.monotonic() - attempt_started > hook["timeout"]:
                            raise HookError("UNCERTAIN_EFFECT" if hook["handler"] == "memory.write" else "TIMEOUT")
                        break
                    except HookError as error:
                        if error.code != "TIMEOUT" or attempt == hook["retry_policy"]["max_attempts"]:
                            raise
                        time.sleep(0.05 * attempt)
            # Cached checks and freshly executed checks have the same freshness contract.
            if hook["handler"] == "evidence" or (hook["handler"] == "command" and hook["config"]["read_only"]):
                require(snapshot(self.workspace, event["files"]) == self.scope, "STALE_INPUT")
        except HookError as error:
            row["error_code"] = error.code
            row["output"] = {}
            row["status"] = "failed" if error.code in ("CHECK_FAILED", "MISSING_EVIDENCE", "MEMORY_CONFLICT") else "error"
        except OSError:
            row["error_code"] = "COMMAND_UNAVAILABLE"
            row["output"] = {}
            row["status"] = "error"
        row["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
        failed = row["status"] in ("error", "failed")
        if hook["execution_mode"] == "ENFORCE":
            row["gate_impact"] = "block" if failed else "pass"
        elif failed:
            row["gate_impact"] = "warn"
        operational = row["error_code"] in ("TIMEOUT", "COMMAND_UNAVAILABLE", "UNCERTAIN_EFFECT")
        count = self.failure_count(hook["id"])
        if operational:
            count += 1
        elif row["status"] in ("passed", "observed", "advised"):
            count = 0
        if row["error_code"] != "CIRCUIT_OPEN":
            self.db.execute("INSERT INTO failures VALUES(?,?,?,?) ON CONFLICT(workspace,registry_digest,hook_id) DO UPDATE SET count=excluded.count",
                            (str(self.workspace), self.registry_digest, hook["id"], count))
        return row

    def run(self, event):
        validate_event(event)
        self.scope = snapshot(self.workspace, event["files"])
        fingerprint = digest([event, self.registry_digest, self.scope, sorted(self.permissions)])
        previous = self.claim(event, fingerprint)
        if previous is not None:
            return previous
        result = {"event_id": event["event_id"], "task_id": event["task_id"], "event": event["event"],
                  "status": "completed", "gate": "pass", "replayed": False, "hooks": [],
                  "scope": self.scope, "registry_digest": self.registry_digest}
        deadline = time.monotonic() + (10 if event["profile"] == "FAST" else 120)
        for hook in sorted(self.registry["hooks"], key=lambda h: (h["priority"], h["id"])):
            trigger = hook["trigger_conditions"]
            if (not hook["enabled"] or event["event"] not in hook["event"]
                    or event["profile"] not in trigger["profiles"]
                    or (trigger["any_flags"] and not set(trigger["any_flags"]) & set(event["flags"]))):
                continue
            # Reserve worst-case timeout and bounded backoff before starting the next hook.
            worst = hook["timeout"] * hook["retry_policy"]["max_attempts"] + 0.3
            if time.monotonic() + worst > deadline:
                result.update(status="blocked", gate="block", error_code="EVENT_BUDGET_EXCEEDED")
                break
            row = self.execute_hook(hook, event)
            result["hooks"].append(row)
            if row["gate_impact"] == "warn":
                result["status"] = "completed_with_warnings"
            if row["gate_impact"] == "block" or row["error_code"] == "UNCERTAIN_EFFECT":
                result.update(status="blocked", gate="block")
                break
        # Journal excludes retrieved memory text; explicit read output can contain it.
        journal = copy.deepcopy(result)
        for row in journal["hooks"]:
            if row["handler"] == "memory.read" and row["status"] == "observed":
                row["output"]["records"] = [{"id": r["id"], "version": r["version"]}
                                            for r in row["output"]["records"]]
        uncertain = any(r["error_code"] == "UNCERTAIN_EFFECT" for r in result["hooks"])
        self.db.execute("UPDATE events SET status=?,result=? WHERE workspace=? AND event_id=?",
                        ("uncertain" if uncertain else "done", canonical(journal), str(self.workspace), event["event_id"]))
        return result

    def recover(self, event_id, confirmed):
        require("state.reconcile" in self.permissions and confirmed, "RECONCILIATION_REQUIRED")
        with self.transaction():
            row = self.db.execute("SELECT status,owner_pid,child_pgid FROM events WHERE workspace=? AND event_id=?",
                                  (str(self.workspace), event_id)).fetchone()
            require(row is not None and row[0] in ("running", "uncertain"), "NOT_RECOVERABLE")
            try:
                os.kill(row[1], 0)
            except ProcessLookupError:
                pass
            else:
                raise HookError("OWNER_STILL_RUNNING")
            if row[2] is not None:
                try:
                    os.killpg(row[2], 0)
                except ProcessLookupError:
                    pass
                else:
                    raise HookError("CHILD_STILL_RUNNING")
            result = {"event_id": event_id, "status": "abandoned", "gate": "block", "hooks": [],
                      "error_code": "RECONCILED_NO_REPLAY", "replayed": False}
            self.db.execute("UPDATE events SET status='done',result=? WHERE workspace=? AND event_id=?",
                            (canonical(result), str(self.workspace), event_id))
        return {"status": "reconciled", "event_id": event_id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "list", "validate", "recover", "reset-circuit"))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--event-id")
    parser.add_argument("--hook-id")
    parser.add_argument("--confirmed-effects", action="store_true")
    args = parser.parse_args()
    engine = None
    try:
        require(not os.environ.get("NEXUS_HOOK_ACTIVE"), "RECURSION_LIMIT")
        registry = load_registry(args.registry)
        if args.action in ("list", "validate"):
            result = {"status": "valid", "events": EVENTS, "hooks": registry["hooks"] if args.action == "list" else len(registry["hooks"])}
        else:
            require(args.workspace is not None and args.state is not None, "WORKSPACE_AND_STATE_REQUIRED")
            event = None
            if args.action == "run":
                event = parse_json(sys.stdin.read(MAX_JSON + 1))
                validate_event(event)
            engine = Engine(args.workspace, args.state, registry, args.allow)
            if args.action == "run":
                result = engine.run(event)
            elif args.action == "recover":
                result = engine.recover(args.event_id, args.confirmed_effects)
            else:
                require("state.reconcile" in args.allow and args.confirmed_effects, "RECONCILIATION_REQUIRED")
                require(args.hook_id in {h["id"] for h in registry["hooks"]}, "UNKNOWN_HOOK")
                engine.db.execute("DELETE FROM failures WHERE workspace=? AND registry_digest=? AND hook_id=?",
                                  (str(engine.workspace), engine.registry_digest, args.hook_id))
                result = {"status": "circuit_reset", "hook_id": args.hook_id}
        print(canonical(result))
        return 2 if result.get("gate") == "block" else 0
    except HookError as error:
        print(canonical({"status": "error", "gate": "block", "error_code": error.code}))
        return 3
    except (OSError, sqlite3.Error, UnicodeError):
        print(canonical({"status": "error", "gate": "block", "error_code": "OPERATIONAL_FAILURE"}))
        return 3
    finally:
        if engine is not None:
            engine.db.close()


if __name__ == "__main__":
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt)
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(canonical({"status": "interrupted", "gate": "block", "error_code": "RECONCILIATION_REQUIRED"}))
        sys.exit(3)
