#!/usr/bin/env python3
"""Opt-in, scoped local memory. Standard library; cooperative POSIX locking."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

try:
    import fcntl
except ImportError:
    fcntl = None

MAX_FILE_BYTES = 1_048_576
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}\Z")
SCOPE = re.compile(r"(working|project|shared):[a-zA-Z0-9][a-zA-Z0-9_./-]{0,159}\Z")
REVISION = re.compile(r"[0-9]{8}\.json\Z")
REQUIRED = {"id", "scope", "type", "summary", "provenance", "confidence", "status", "related_entities"}
OPTIONAL = {"content", "reference", "tags", "expires_at", "superseded_by"}
GENERATED = {"created_at", "updated_at", "author", "revision"}
META = ("id", "scope", "type", "summary", "status", "updated_at", "revision", "related_entities", "tags", "expires_at")
SECRET = re.compile(
    r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}|"
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|"
    r"\b(?:gh[pousr]_|sk-(?:proj-)?)[A-Za-z0-9_-]{16,}|"
    r"\b[a-z][a-z0-9+.-]{0,31}://[^\s/:]+:[^\s/@]+@|"
    r"""\b(?:password|passwd|api[_-]?key|access[_-]?token|secret|client[_-]?secret)["']?\s*[:=]\s*["']?[^\s,;"']{6,}""",
    re.IGNORECASE,
)


class MemoryError(Exception):
    """Only stable, non-sensitive error codes cross the CLI boundary."""


def require(condition, code="invalid_record"):
    if not condition:
        raise MemoryError(code)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def date(value):
    require(isinstance(value, str) and value.endswith("Z"), "invalid_timestamp")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise MemoryError("invalid_timestamp") from None
    require(result.utcoffset() is not None and result.utcoffset().total_seconds() == 0, "invalid_timestamp")
    return result


def string(value, limit=32768):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def scan_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(not (re.fullmatch(r"password|passwd|api[_-]?key|access[_-]?token|secret|client[_-]?secret", key, re.I)
                         and item), "secret_detected")
            scan_secrets(key)
            scan_secrets(item)
    elif isinstance(value, list):
        for item in value:
            scan_secrets(item)
    elif isinstance(value, str):
        require(not SECRET.search(value), "secret_detected")


def validate_record(record, scope, stored=False):
    require(isinstance(record, dict))
    scan_secrets(record)
    fields = REQUIRED | OPTIONAL | (GENERATED if stored else set())
    require(REQUIRED <= record.keys() and record.keys() <= fields)
    require(isinstance(record["id"], str) and ID.fullmatch(record["id"]))
    require(record["scope"] == scope, "scope_mismatch")
    require(record["type"] in ("decision", "observation", "hypothesis", "checkpoint", "pattern"))
    require(string(record["summary"], 400))
    require("content" in record or "reference" in record)
    for field in ("content", "reference"):
        if field in record:
            require(string(record[field]))
    require(record["status"] in ("active", "stale", "superseded", "expired"))
    for field in ("related_entities", "tags"):
        values = record.get(field, [])
        require(isinstance(values, list) and len(values) <= 64)
        require(all(string(v, 256) for v in values))
        require(len(set(values)) == len(values))
    sources = record["provenance"]
    require(isinstance(sources, list) and 1 <= len(sources) <= 32)
    for source in sources:
        require(isinstance(source, dict) and {"reference", "observed_at"} <= source.keys()
                and source.keys() <= {"reference", "observed_at", "revision"})
        require(string(source["reference"], 2048))
        date(source["observed_at"])
        if "revision" in source:
            require(string(source["revision"], 256))
    confidence = record["confidence"]
    require(isinstance(confidence, dict) and confidence.keys() == {"level", "reason"})
    require(confidence["level"] in ("low", "medium", "high") and string(confidence["reason"], 1000))
    if "expires_at" in record:
        date(record["expires_at"])
    if record["status"] == "superseded":
        require(isinstance(record.get("superseded_by"), str) and ID.fullmatch(record["superseded_by"])
                and record["superseded_by"] != record["id"])
    else:
        require("superseded_by" not in record)
    if stored:
        require(GENERATED <= record.keys())
        date(record["created_at"])
        date(record["updated_at"])
        require(date(record["updated_at"]) >= date(record["created_at"]))
        require(type(record["revision"]) is int and 1 <= record["revision"] <= 99999999)
        require(string(record["author"], 128))
    return record


def safe_path(path):
    require(not path.is_symlink(), "symlink_not_supported")
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def read_json(path):
    safe_path(path)
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    require(len(data) <= MAX_FILE_BYTES, "file_too_large")
    try:
        return json.loads(data, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError):
        raise MemoryError("invalid_json") from None


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    """A failure after replace is an uncertain outcome: caller must inspect state."""
    safe_path(path)
    data = (dumps(value) + "\n").encode("utf-8")
    require(len(data) <= MAX_FILE_BYTES, "file_too_large")
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def metadata_digest(records):
    return hashlib.sha256(dumps(records).encode("utf-8")).hexdigest()


def alive(record):
    return record["status"] == "active" and (
        "expires_at" not in record or date(record["expires_at"]) > datetime.now(timezone.utc))


def fingerprint(record):
    def normal(value):
        if isinstance(value, str):
            return " ".join(unicodedata.normalize("NFC", value).split())
        if isinstance(value, list):
            return sorted(normal(v) for v in value)
        return value
    # Sources/confidence/status are evidence about a fact, not a different fact.
    fact = {k: normal(record.get(k)) for k in ("type", "summary", "content", "reference", "related_entities")}
    return hashlib.sha256(dumps(fact).encode()).hexdigest()


class Store:
    def __init__(self, root, scope):
        require(fcntl is not None, "posix_required")
        require(isinstance(scope, str) and SCOPE.fullmatch(scope), "invalid_scope")
        self.root = Path(root).absolute()
        safe_path(self.root)
        self.scope = scope

    @contextmanager
    def locked(self, write=False, initialize=False):
        if initialize:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(self.root.is_dir(), "store_not_initialized")
        safe_path(self.root / ".lock")
        flags = os.O_RDWR | os.O_NOFOLLOW
        if initialize:
            flags |= os.O_CREAT
        try:
            fd = os.open(self.root / ".lock", flags, 0o600)
        except FileNotFoundError:
            raise MemoryError("store_not_initialized") from None
        try:
            try:
                fcntl.flock(fd, (fcntl.LOCK_EX if write else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except BlockingIOError:
                raise MemoryError("busy") from None
            if not initialize:
                self.manifest()
            yield
        finally:
            os.close(fd)

    def manifest(self):
        manifest = read_json(self.root / "manifest.json")
        require(isinstance(manifest, dict) and manifest.get("format") == 1, "unsupported_format")
        require(manifest.get("scope") == self.scope, "scope_mismatch")
        require(safe_path(self.root / "records").is_dir(), "invalid_store")
        return manifest

    def init(self):
        if (self.root / "manifest.json").exists():
            self.manifest()
            return {"scope": self.scope, "initialized": True}
        records = safe_path(self.root / "records")
        require(not records.exists() or not list(records.iterdir()), "existing_records_without_manifest")
        records.mkdir(exist_ok=True, mode=0o700)
        atomic_json(self.root / "manifest.json", {"format": 1, "scope": self.scope})
        atomic_json(self.root / "index.json", {"format": 1, "scope": self.scope, "signature": {}, "records": [], "metadata_digest": metadata_digest([])})
        return {"scope": self.scope, "initialized": True}

    def inventory(self):
        latest = {}
        signature = {}
        for folder in sorted((self.root / "records").iterdir()):
            safe_path(folder)
            require(folder.is_dir() and ID.fullmatch(folder.name), "invalid_store")
            revisions = []
            for path in sorted(folder.iterdir()):
                safe_path(path)
                if path.name.startswith(".pending-"):
                    continue
                require(path.is_file() and REVISION.fullmatch(path.name), "invalid_store")
                revision = int(path.stem)
                require(revision > 0, "invalid_revision")
                revisions.append((revision, path))
            if revisions:
                revision, path = max(revisions)
                stat = path.stat()
                latest[folder.name] = path
                signature[folder.name] = [revision, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]
        return latest, signature

    def read_record(self, path):
        record = validate_record(read_json(path), self.scope, stored=True)
        require(record["id"] == path.parent.name and record["revision"] == int(path.stem), "record_identity_mismatch")
        return record

    def catalog(self, rebuild=False):
        latest, signature = self.inventory()
        if not rebuild:
            try:
                index = read_json(self.root / "index.json")
                if (isinstance(index, dict) and index.get("format") == 1 and index.get("scope") == self.scope
                        and index.get("signature") == signature and isinstance(index.get("records"), list)
                        and index.get("metadata_digest") == metadata_digest(index["records"])
                        and {r["id"] for r in index["records"]} == set(latest)
                        and len(index["records"]) == len(latest)
                        and all(set(r) <= set(META) and {"id", "summary", "type", "status", "related_entities", "revision"} <= r.keys()
                                for r in index["records"])):
                    # Validate cached metadata before selection; corrupt cache is disposable.
                    for r in index["records"]:
                        require(r.get("scope") == self.scope and string(r["summary"], 400))
                        require(r["type"] in ("decision", "observation", "hypothesis", "checkpoint", "pattern"))
                        require(r["status"] in ("active", "stale", "superseded", "expired"))
                        require(isinstance(r["related_entities"], list) and isinstance(r.get("tags", []), list))
                        require(all(isinstance(x, str) for x in r["related_entities"] + r.get("tags", [])))
                        require(r["revision"] == signature[r["id"]][0])
                        if "expires_at" in r:
                            date(r["expires_at"])
                    return index, latest, True
            except (MemoryError, OSError, TypeError, KeyError):
                pass
        metadata = []
        for path in latest.values():
            record = self.read_record(path)
            metadata.append({k: record[k] for k in META if k in record})
        return {"format": 1, "scope": self.scope, "signature": signature, "records": metadata,
                "metadata_digest": metadata_digest(metadata)}, latest, False

    def reindex(self):
        index, _, _ = self.catalog(rebuild=True)
        atomic_json(self.root / "index.json", index)
        return {"indexed_records": len(index["records"])}

    def get(self, record_id, revision=None):
        require(isinstance(record_id, str) and ID.fullmatch(record_id), "invalid_id")
        folder = safe_path(self.root / "records" / record_id)
        if revision is None:
            latest, _ = self.inventory()
            require(record_id in latest, "not_found")
            path = latest[record_id]
        else:
            require(1 <= revision <= 99999999, "invalid_revision")
            path = folder / f"{revision:08d}.json"
        require(path.is_file(), "not_found")
        return self.read_record(path)

    def put(self, record, expected_revision, author):
        validate_record(record, self.scope)
        require(type(expected_revision) is int and 0 <= expected_revision < 99999999, "invalid_revision")
        require(string(author, 128), "invalid_author")
        scan_secrets(author)
        latest, _ = self.inventory()
        previous = self.read_record(latest[record["id"]]) if record["id"] in latest else None
        require((previous["revision"] if previous else 0) == expected_revision, "revision_conflict")
        if previous and {k: v for k, v in previous.items() if k not in GENERATED} == record:
            return {"id": record["id"], "revision": previous["revision"], "persisted": True, "unchanged": True}
        if record["status"] == "superseded":
            require(record["superseded_by"] in latest and alive(self.read_record(latest[record["superseded_by"]])), "invalid_replacement")
        fact = fingerprint(record)
        for record_id, path in latest.items():
            if record_id != record["id"]:
                require(fingerprint(self.read_record(path)) != fact, "duplicate_record")
        now = timestamp()
        saved = dict(record, author=author, revision=expected_revision + 1,
                     created_at=previous["created_at"] if previous else now, updated_at=now)
        validate_record(saved, self.scope, stored=True)
        folder = safe_path(self.root / "records" / record["id"])
        folder.mkdir(exist_ok=True, mode=0o700)
        fsync_dir(folder.parent)
        path = folder / f"{saved['revision']:08d}.json"
        require(not path.exists(), "revision_conflict")
        atomic_json(path, saved)
        indexed = True
        try:
            self.reindex()
        except (MemoryError, OSError):
            indexed = False
        return {"id": saved["id"], "revision": saved["revision"], "persisted": True, "index_updated": indexed}

    def pack(self, task, query="", ids=(), entities=(), tags=(), max_chars=6000, details=False):
        require(string(task, 2000) and isinstance(query, str) and len(query) <= 2000, "invalid_query")
        require(512 <= max_chars <= 100000, "invalid_budget")
        scan_secrets([task, query, list(ids), list(entities), list(tags)])
        index, latest, cached = self.catalog()
        words = set(re.findall(r"\w+", (task + " " + query).casefold()))
        candidates = []
        for meta in index["records"]:
            if not alive(meta):
                continue
            terms = " ".join([meta["summary"], meta["type"], *meta["related_entities"], *meta.get("tags", [])])
            matches = len(words & set(re.findall(r"\w+", terms.casefold())))
            score = (int(meta["id"] in ids), len(set(entities) & set(meta["related_entities"])),
                     len(set(tags) & set(meta.get("tags", []))), matches)
            if any(score):
                candidates.append((score, meta["id"]))
        candidates.sort(key=lambda item: (tuple(-n for n in item[0]), item[1]))
        pack = {"task": task, "scope": self.scope, "records": [], "omitted_count": len(candidates),
                "needs_revalidation": True,
                "metrics": {"metadata_records": len(index["records"]), "retrieved_records": 0, "loaded_records": 0,
                            "retrieved_chars": 0, "provided_chars": 0, "provider_tokens": None,
                            "index_cache_hit": cached}}
        require(len(pack_text(pack)) <= max_chars, "budget_too_small_for_task")
        for _, record_id in candidates:
            record = self.read_record(latest[record_id])
            require(alive(record), "catalog_changed")
            selected = {k: v for k, v in record.items() if details or k != "content"}
            selected["needs_revalidation"] = True
            selected["record_reference"] = f"records/{record_id}/{record['revision']:08d}.json"
            pack["records"].append(selected)
            pack["omitted_count"] -= 1
            pack["metrics"]["retrieved_records"] += 1
            size = len(dumps(record))
            pack["metrics"]["retrieved_chars"] += size
            pack["metrics"]["loaded_records"] += 1
            if len(pack_text(pack)) > max_chars:
                pack["records"].pop()
                pack["omitted_count"] += 1
                pack["metrics"]["retrieved_records"] -= 1
                # Retrieval happened even if the budget prevented providing the record.
        # Counters can grow after an oversized candidate was omitted. Enforce
        # the limit on the final envelope, including every measured counter.
        while len(pack_text(pack)) > max_chars and pack["records"]:
            pack["records"].pop()
            pack["omitted_count"] += 1
            pack["metrics"]["retrieved_records"] -= 1
        require(len(pack_text(pack)) <= max_chars, "budget_too_small_for_task")
        return pack


def pack_text(pack):
    while True:
        text = dumps(pack)
        if pack["metrics"]["provided_chars"] == len(text):
            return text
        pack["metrics"]["provided_chars"] = len(text)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MemoryError("invalid_arguments")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--root", required=True, help="Explicit store directory; never a global default")
    parser.add_argument("--scope", required=True, help="working:project/task, project:id or shared:collection")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    for command in ("init", "put", "reindex"):
        sub = commands.add_parser(command)
        sub.add_argument("--allow-write", action="store_true", help="Explicit opt-in; host authorization still applies")
        if command == "put":
            sub.add_argument("--file", required=True)
            sub.add_argument("--expected-revision", type=int, required=True)
            sub.add_argument("--author", required=True)
    sub = commands.add_parser("get")
    sub.add_argument("--id", required=True)
    sub.add_argument("--revision", type=int)
    sub = commands.add_parser("pack")
    sub.add_argument("--task", required=True)
    sub.add_argument("--query", default="")
    for selector in ("id", "entity", "tag"):
        sub.add_argument("--" + selector, action="append", default=[])
    sub.add_argument("--max-chars", type=int, default=6000)
    sub.add_argument("--details", action="store_true")
    args = parser.parse_args(argv)
    write = args.command in ("init", "put", "reindex")
    require(not write or args.allow_write, "write_not_authorized")
    store = Store(args.root, args.scope)
    record = None
    if args.command == "put":
        record = validate_record(read_json(Path(args.file)), args.scope)
    with store.locked(write=write, initialize=args.command == "init"):
        if args.command == "init":
            result = store.init()
        elif args.command == "put":
            result = store.put(record, args.expected_revision, args.author)
        elif args.command == "get":
            result = store.get(args.id, args.revision)
        elif args.command == "reindex":
            result = store.reindex()
        else:
            result = store.pack(args.task, args.query, args.id, args.entity, args.tag, args.max_chars, args.details)
    print(dumps(result))


if __name__ == "__main__":
    try:
        main()
    except MemoryError as error:
        print(dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)
    except (OSError, UnicodeError, ValueError, TypeError):
        # Filesystem/parser errors may contain paths, credentials or private source text.
        print(dumps({"error": "io_or_input_error_inspect_before_retry"}), file=sys.stderr)
        sys.exit(1)
