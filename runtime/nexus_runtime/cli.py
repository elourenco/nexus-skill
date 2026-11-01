"""Explicit input/output CLI; no project discovery or persistent logs."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .adapters import AdapterError
from .council import Council, ReviewRequest, _unique_object
from .engine import Config, Engine, Task, object_fields


EXIT_CODES = {"completed": 0, "APPROVED": 0, "blocked": 3, "BLOCKED": 3,
              "inconclusive": 4, "INCONCLUSIVE": 4, "CHANGES_REQUESTED": 5}


def read_json(path, max_bytes=8 * 1024 * 1024):
    with Path(path).open("rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("input too large")
    return json.loads(raw, object_pairs_hook=_unique_object)


def task_from_dict(data):
    required = ("task_id", "agent", "prompt")
    object_fields(data, (*required, "complexity", "data_class", "required_capabilities", "allowed_providers"), required)
    values = dict(data)
    values["id"] = values.pop("task_id")
    return Task(**values)


def main(argv=None):
    parser = argparse.ArgumentParser(description="NEXUS: bounded text-only planning and risk-based review")
    parser.add_argument("--config", required=True, help="Explicit JSON provider/model/limits configuration")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="Inspect local configuration; makes no API call")
    for command in ("route", "run"):
        child = sub.add_parser(command, help="Rank models without dispatch" if command == "route" else "Execute a textual role")
        child.add_argument("--task", required=True, help="Task JSON file")
    review = sub.add_parser("review", help="Review supplied snapshots; never edits files")
    review.add_argument("--request", required=True, help="ReviewRequest JSON file")
    args = parser.parse_args(argv)
    try:
        engine = Engine(Config.from_dict(read_json(args.config, 1024 * 1024)))
        if args.command == "inspect":
            output, code = engine.inspect(), 0
        elif args.command == "review":
            output = Council(engine).run(ReviewRequest.from_dict(read_json(args.request)))
            code = EXIT_CODES[output["decision"]]
        else:
            task = task_from_dict(read_json(args.task))
            if args.command == "route":
                models = engine.route(task)
                output = {"task_id": task.id, "candidates": [m.id for m in models],
                          "policy": engine.config.policy, "dispatched": False,
                          "availability": "local_configuration_only"}
                code = 0 if models else 3
            else:
                result = engine.run(task)
                output = {"result": asdict(result), "usage": engine.report()}
                code = EXIT_CODES[result.status]
    except (ValueError, TypeError, KeyError, RecursionError, OSError, AdapterError):
        # Do not echo prompts, credentials, provider bodies or arbitrary paths in errors.
        output, code = {"error": "invalid_input_or_configuration"}, 2
    except KeyboardInterrupt:
        output, code = {"error": "interrupted", "remote_cancellation_confirmed": False}, 130
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return code
