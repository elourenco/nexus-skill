"""Handlers never dispatch hooks or acquire additional permissions."""
import json
import os
import signal
import subprocess
import sys
import time

from hook_contract import HookError, require


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def command(hook, engine, event):
    config = hook["config"]
    argv = [sys.executable if part == "{python}" else part for part in config["argv"]]
    # No shell, caller payload interpolation, inherited tokens or captured subprocess output.
    env = {"PATH": os.environ.get("PATH", os.defpath), "NEXUS_HOOK_ACTIVE": "1",
           "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    process = subprocess.Popen(argv, cwd=engine.workspace, env=env, start_new_session=True,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        engine.db.execute("UPDATE events SET child_pgid=? WHERE workspace=? AND event_id=?",
                          (process.pid, str(engine.workspace), event["event_id"]))
        try:
            returncode = process.wait(timeout=hook["timeout"])
        except subprocess.TimeoutExpired:
            raise HookError("TIMEOUT" if config["read_only"] else "UNCERTAIN_EFFECT") from None
        if returncode:
            raise HookError("CHECK_FAILED" if config["read_only"] else "UNCERTAIN_EFFECT")
        return {"returncode": returncode}
    finally:
        # Also terminate non-detached descendants after the direct child exits.
        stop_group(process)
        engine.db.execute("UPDATE events SET child_pgid=NULL WHERE workspace=? AND event_id=?",
                          (str(engine.workspace), event["event_id"]))


def evidence(hook, engine, event):
    require(engine.scope is not None, "MISSING_EVIDENCE")
    found = set()
    for event_id in event["inputs"].get("evidence", []):
        row = engine.db.execute("SELECT result FROM events WHERE workspace=? AND event_id=? AND status='done'",
                                (str(engine.workspace), event_id)).fetchone()
        if not row:
            continue
        result = json.loads(row[0])
        if (result.get("scope") != engine.scope or result.get("registry_digest") != engine.registry_digest
                or result.get("task_id") != event["task_id"]):
            continue
        for item in result.get("hooks", []):
            if item["status"] == "passed" and item.get("handler") == "command":
                found.add(item["hook_id"])
    require(set(hook["config"]["required_hooks"]) <= found, "MISSING_EVIDENCE")
    return {"verified_hooks": sorted(found)}


def memory_write(engine, event):
    m = event["inputs"].get("memory")
    require(m is not None, "MISSING_MEMORY")
    # Content is explicit user data, never a transcript inferred by this executor.
    with engine.transaction():
        row = engine.db.execute("SELECT MAX(version) FROM memory WHERE workspace=? AND record_id=?",
                                (str(engine.workspace), m["id"])).fetchone()
        version = row[0] or 0
        require(version == m["expected_version"], "MEMORY_CONFLICT")
        engine.db.execute("UPDATE memory SET active=0 WHERE workspace=? AND record_id=?",
                          (str(engine.workspace), m["id"]))
        engine.db.execute("INSERT INTO memory VALUES(?,?,?,?,?,?,?,?)",
                          (str(engine.workspace), m["id"], version + 1, m["content"], m["source"],
                           time.time(), 1, event["event_id"]))
    return {"record_id": m["id"], "version": version + 1}


def memory_read(engine, event):
    records = []
    for record_id in event["inputs"].get("memory_ids", []):
        row = engine.db.execute(
            "SELECT version,content,source,created FROM memory WHERE workspace=? AND record_id=? AND active=1",
            (str(engine.workspace), record_id)).fetchone()
        if row:
            records.append({"id": record_id, "version": row[0], "content": row[1], "source": row[2], "created": row[3]})
    return {"records": records, "trust": "untrusted_context_revalidate_before_use"}


def dispatch(hook, engine, event):
    handler = hook["handler"]
    if handler == "command":
        return "passed", command(hook, engine, event)
    if handler == "evidence":
        return "passed", evidence(hook, engine, event)
    if handler == "advice":
        return "advised", {"recommendation": hook["config"]["prompt"]}
    if handler == "observe":
        return "observed", {}
    if handler == "memory.write":
        return "passed", memory_write(engine, event)
    if handler == "memory.read":
        return "observed", memory_read(engine, event)
    raise HookError("UNKNOWN_HANDLER")
