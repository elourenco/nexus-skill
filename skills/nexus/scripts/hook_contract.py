"""Bounded, dependency-free validation for local NEXUS hooks."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

EVENTS = (
    "session.start", "session.resume", "session.end", "task.created", "spec.validated",
    "plan.ready", "task.started", "code.pre_edit", "code.post_edit", "code.pre_commit",
    "test.completed", "review.requested", "review.completed", "task.blocked", "task.failed",
    "task.completed", "memory.retrieve", "memory.capture", "memory.refresh",
)
PROFILES = {"FAST", "BALANCED", "DEEP"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
MAX_JSON = 262144


class HookError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise HookError(code)


def identifier(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def utf8_string(value):
    if not isinstance(value, str):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def strings(value, limit=64):
    return (isinstance(value, list) and len(value) <= limit
            and all(utf8_string(v) and len(v) <= 2048 and "\x00" not in v for v in value))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def parse_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "INVALID_JSON")
            result[key] = value
        return result
    require(len(text.encode()) <= MAX_JSON, "INPUT_TOO_LARGE")
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(HookError("INVALID_JSON")))
    except (ValueError, RecursionError):
        raise HookError("INVALID_JSON") from None


def load_registry(path):
    with Path(path).open(encoding="utf-8") as stream:
        data = parse_json(stream.read(MAX_JSON + 1))
    code = "INVALID_REGISTRY"
    require(isinstance(data, dict) and set(data) == {"version", "hooks"}, code)
    require(type(data["version"]) is int and data["version"] == 1, code)
    require(isinstance(data["hooks"], list) and 0 < len(data["hooks"]) <= 64, code)
    ids = set()
    fields = {"id", "description", "event", "trigger_conditions", "execution_mode", "priority",
              "inputs", "outputs", "timeout", "retry_policy", "failure_policy", "permissions",
              "enabled", "supported_adapters", "handler", "config"}
    for h in data["hooks"]:
        require(isinstance(h, dict) and set(h) == fields, code)
        require(identifier(h["id"]) and h["id"] not in ids, code)
        ids.add(h["id"])
        require(isinstance(h["description"], str) and 0 < len(h["description"]) <= 512, code)
        require(strings(h["event"]) and h["event"] and set(h["event"]) <= set(EVENTS), code)
        require(h["execution_mode"] in ("OBSERVE", "ADVISE", "ENFORCE", "EXECUTE"), code)
        require(type(h["priority"]) is int and 0 <= h["priority"] <= 100, code)
        require(type(h["enabled"]) is bool, code)
        require(h["supported_adapters"] == ["local"], code)
        require(strings(h["inputs"]) and strings(h["outputs"]) and strings(h["permissions"]), code)
        require(type(h["timeout"]) in (int, float) and math.isfinite(h["timeout"])
                and 0 < h["timeout"] <= 60, code)
        trigger = h["trigger_conditions"]
        require(isinstance(trigger, dict) and set(trigger) == {"profiles", "any_flags"}, code)
        require(strings(trigger["profiles"]) and trigger["profiles"]
                and set(trigger["profiles"]) <= PROFILES and strings(trigger["any_flags"]), code)
        retry = h["retry_policy"]
        require(isinstance(retry, dict) and set(retry) == {"max_attempts"}, code)
        require(type(retry["max_attempts"]) is int and 1 <= retry["max_attempts"] <= 3, code)
        require(h["failure_policy"] in ("block", "warn"), code)
        require((h["execution_mode"] == "ENFORCE") == (h["failure_policy"] == "block"), code)
        config = h["config"]
        require(isinstance(config, dict), code)
        handler = h["handler"]
        if handler == "command":
            require(h["execution_mode"] in ("ENFORCE", "EXECUTE"), code)
            require(set(config) <= {"argv", "read_only", "cache_seconds"}
                    and {"argv", "read_only"} <= set(config), code)
            require(strings(config["argv"]) and config["argv"] and all(config["argv"]), code)
            require(type(config["read_only"]) is bool, code)
            require(h["permissions"] == ["command:" + h["id"]], code)
            require(config["read_only"] or (h["execution_mode"] == "EXECUTE" and retry["max_attempts"] == 1), code)
            cache = config.get("cache_seconds", 0)
            require(type(cache) is int and 0 <= cache <= 300 and (not cache or config["read_only"]), code)
        elif handler == "advice":
            require(h["execution_mode"] == "ADVISE" and not h["permissions"], code)
            require(set(config) == {"prompt"} and isinstance(config["prompt"], str)
                    and 0 < len(config["prompt"]) <= 2048, code)
        elif handler == "observe":
            require(h["execution_mode"] == "OBSERVE" and not h["permissions"] and not config, code)
        elif handler == "evidence":
            require(h["execution_mode"] == "ENFORCE" and not h["permissions"], code)
            require(set(config) == {"required_hooks"} and strings(config["required_hooks"])
                    and config["required_hooks"], code)
        elif handler in ("memory.read", "memory.write"):
            require(h["permissions"] == [handler] and not config, code)
            require(h["execution_mode"] == ("OBSERVE" if handler == "memory.read" else "EXECUTE"), code)
        else:
            raise HookError(code)
        require(handler == "command" or retry["max_attempts"] == 1, code)
    for h in data["hooks"]:
        if h["handler"] == "evidence":
            for needed in h["config"]["required_hooks"]:
                matches = [item for item in data["hooks"] if item["id"] == needed]
                require(matches and matches[0]["handler"] == "command" and matches[0]["config"]["read_only"], code)
    return data


def validate_event(event):
    code = "INVALID_EVENT"
    fields = {"event_id", "task_id", "event", "profile", "flags", "files", "inputs"}
    require(isinstance(event, dict) and set(event) == fields, code)
    require(identifier(event["event_id"]) and identifier(event["task_id"]), code)
    require(event["event"] in EVENTS and event["profile"] in ("FAST", "BALANCED", "DEEP"), code)
    require(strings(event["flags"]) and all(identifier(v) for v in event["flags"]), code)
    require(strings(event["files"], 128) and len(set(event["files"])) == len(event["files"]), code)
    inputs = event["inputs"]
    require(isinstance(inputs, dict) and set(inputs) <= {"evidence", "memory", "memory_ids"}, code)
    for field in ("evidence", "memory_ids"):
        require(strings(inputs.get(field, [])) and all(identifier(v) for v in inputs.get(field, [])), code)
    if "memory" in inputs:
        m = inputs["memory"]
        require(isinstance(m, dict) and set(m) == {"id", "content", "source", "expected_version"}, code)
        require(identifier(m["id"]) and utf8_string(m["content"]) and 0 < len(m["content"]) <= 4096, code)
        require(utf8_string(m["source"]) and 0 < len(m["source"]) <= 512, code)
        require(type(m["expected_version"]) is int and 0 <= m["expected_version"] < 1000000, code)


def snapshot(workspace, files):
    values = []
    total = 0
    for name in sorted(files):
        path = Path(name)
        require(not path.is_absolute() and ".." not in path.parts and name not in ("", "."), "INVALID_PATH")
        target = workspace / path
        require(target.resolve().is_relative_to(workspace), "INVALID_PATH")
        require(not target.is_symlink(), "INVALID_PATH")
        if not target.exists():
            values.append([name, "missing"])
            continue
        require(target.is_file(), "INVALID_PATH")
        with target.open("rb") as stream:
            content = stream.read(2 * 1024 * 1024 + 1)
            executable = stat.S_IMODE(os.fstat(stream.fileno()).st_mode) & 0o111
        total += len(content)
        require(len(content) <= 2 * 1024 * 1024 and total <= 16 * 1024 * 1024, "SCOPE_TOO_LARGE")
        values.append([name, hashlib.sha256(content).hexdigest(), executable])
    return digest(values) if values else None
