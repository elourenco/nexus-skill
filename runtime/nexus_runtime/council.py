"""Risk-selected, read-only reviews over an immutable, explicitly supplied artifact."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

from .engine import Engine, Task, number, object_fields, string, strings


PILLARS = {
    "architecture": "Boundaries, contracts, coupling, modularity and compatibility.",
    "security": "Authentication, authorization, secrets, input validation and concrete attack paths.",
    "quality": "Correctness, regressions, testability, duplication and maintainability; no cosmetic comments.",
    "performance": "Latency, memory, processing, contention, throughput and bottlenecks; no invented measurements.",
    "reliability": "Partial failures, idempotency, retries, consistency, recovery and observability.",
    "product": "Requirements, acceptance criteria, expected behavior, error states and user experience.",
}
RISKS = {
    "contract": ("architecture",), "authorization": ("security",),
    "untrusted_input": ("security",), "secrets": ("security",),
    "performance": ("performance",), "concurrency": ("performance", "reliability"),
    "persistence": ("reliability",), "external_io": ("reliability",),
    "product": ("product",), "critical": ("architecture", "reliability"),
}
PATH_SIGNALS = {
    "architecture": r"(^|[/_.-])(api|schema|contract|migration|proto)([/_.-]|$)",
    "security": r"(^|[/_.-])(auth|session|permission|secret|token)([/_.-]|$)",
    "performance": r"(^|[/_.-])(perf|performance|query|cache)([/_.-]|$)",
    "reliability": r"(^|[/_.-])(queue|retry|worker|job|sync|migration|cache)([/_.-]|$)",
    "product": r"(^|[/_.-])(ui|screen|view|component|components)([/_.-]|$)",
}


def source_path(value):
    string(value)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise ValueError("source paths must be normalized repository-relative paths")
    return value


@dataclass(frozen=True)
class ReviewRequest:
    task_id: str
    mode: str
    requirements: str
    diff: str
    changed_files: tuple[str, ...]
    sources: dict[str, str]
    risks: tuple[str, ...]
    complexity: int
    data_class: str
    allowed_providers: tuple[str, ...] | None = None

    @classmethod
    def from_dict(cls, data):
        required = ("task_id", "mode", "requirements", "diff", "changed_files", "sources",
                    "risks", "complexity", "data_class")
        object_fields(data, (*required, "allowed_providers"), required)
        if data["mode"] not in ("fast", "balanced", "deep") or data["data_class"] not in ("public", "private", "restricted"):
            raise ValueError("invalid review mode or data class")
        risks = strings(data["risks"])
        if not set(risks) <= RISKS.keys():
            raise ValueError("unknown risk")
        changed = strings(data["changed_files"])
        if not changed or not isinstance(data["sources"], dict):
            raise ValueError("review needs changed_files and source snapshots")
        for path in changed:
            source_path(path)
        sources = {}
        for path, content in data["sources"].items():
            source_path(path)
            if not isinstance(content, str):
                raise ValueError("source content must be text")
            sources[path] = content
        if not set(changed) <= sources.keys():
            raise ValueError("every changed file requires a source snapshot")
        if number(data["complexity"], minimum=1, integer=True) > 3:
            raise ValueError("complexity must be 1, 2 or 3")
        return cls(string(data["task_id"]), data["mode"], string(data["requirements"]), string(data["diff"]),
                   changed, sources, risks, data["complexity"], data["data_class"],
                   None if data.get("allowed_providers") is None else strings(data["allowed_providers"]))

    @property
    def artifact_id(self):
        payload = {"requirements": self.requirements, "diff": self.diff, "sources": self.sources,
                   "changed_files": self.changed_files, "risks": self.risks}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def select_pillars(req):
    selected = {"quality"}
    for risk in req.risks:
        selected.update(RISKS[risk])
    for pillar, pattern in PATH_SIGNALS.items():
        if any(re.search(pattern, path.lower()) for path in req.changed_files):
            selected.add(pillar)
    return tuple(pillar for pillar in PILLARS if pillar in selected)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate output key")
        result[key] = value
    return result


def parse_review(text, req, reviewer_id, pillars):
    if len(text.encode()) > 1024 * 1024:
        raise ValueError("review output too large")
    out = json.loads(text, object_pairs_hook=_unique_object)
    fields = ("task_id", "artifact_id", "reviewer_id", "coverage", "findings", "gaps")
    object_fields(out, fields, fields)
    if (out["task_id"] != req.task_id or out["artifact_id"] != req.artifact_id or
            out["reviewer_id"] != reviewer_id or set(strings(out["coverage"])) != set(pillars)):
        raise ValueError("review identity or coverage mismatch")
    strings(out["gaps"])
    if not isinstance(out["findings"], list) or len(out["findings"]) > 100:
        raise ValueError("invalid findings")
    for f in out["findings"]:
        fields = ("reviewer_id", "task_id", "pillar", "file", "location", "severity",
                  "issue", "evidence", "suggested_fix", "confidence", "status")
        object_fields(f, fields, fields)
        if (f["reviewer_id"] != reviewer_id or f["task_id"] != req.task_id or
                f["pillar"] not in pillars or f["severity"] not in ("critical", "high", "medium", "low") or
                f["status"] != "open"):
            raise ValueError("invalid finding identity or state")
        if number(f["confidence"]) > 1:
            raise ValueError("invalid confidence")
        for key in ("issue", "suggested_fix"):
            string(f[key])
        ev = object_fields(f["evidence"], ("source", "quote"), ("source", "quote"))
        quote = string(ev["quote"])
        if f["file"] is None:
            if f["location"] is not None or ev["source"] not in ("requirements", "diff"):
                raise ValueError("non-file evidence must identify requirements or diff")
            snapshot = getattr(req, ev["source"])
        else:
            source_path(f["file"])
            if f["file"] not in req.sources or ev["source"] != f["file"]:
                raise ValueError("finding references an unknown snapshot")
            loc = object_fields(f["location"], ("start_line", "end_line"), ("start_line", "end_line"))
            start = number(loc["start_line"], minimum=1, integer=True)
            end = number(loc["end_line"], minimum=1, integer=True)
            lines = req.sources[f["file"]].splitlines()
            if end < start or end > len(lines):
                raise ValueError("invalid location")
            snapshot = "\n".join(lines[start - 1:end])
        if quote not in snapshot:
            raise ValueError("evidence quote does not match snapshot/location")
    return out


def consolidate(findings):
    """Merge exact semantic labels/locations; never guess equivalence from line alone."""
    merged = {}
    priorities = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    for finding in findings:
        key = (finding["file"], json.dumps(finding["location"], sort_keys=True),
               " ".join(finding["issue"].split()).casefold(),
               finding["evidence"]["source"], finding["evidence"]["quote"])
        if key not in merged:
            merged[key] = {**copy.deepcopy(finding), "reviewers": [], "pillars": [], "reports": [],
                           "evidence_reference_verified": True, "semantic_truth_verified": False}
        result = merged[key]
        for target, source in (("reviewers", "reviewer_id"), ("pillars", "pillar")):
            if finding[source] not in result[target]:
                result[target].append(finding[source])
        result["reports"].append(copy.deepcopy(finding))
        if priorities[finding["severity"]] > priorities[result["severity"]]:
            result["severity"] = finding["severity"]
    return sorted(merged.values(), key=lambda f: (-priorities[f["severity"]], f["file"] or "", f["issue"]))


OUTPUT_CONTRACT = {
    "top_level_required": ["task_id", "artifact_id", "reviewer_id", "coverage", "findings", "gaps"],
    "finding_required": ["reviewer_id", "task_id", "pillar", "file", "location", "severity", "issue",
                         "evidence", "suggested_fix", "confidence", "status"],
    "rules": [
        "Return only a JSON object, no markdown fences and no additional keys.",
        "Copy task_id, artifact_id and reviewer_id exactly; coverage must list every assigned pillar.",
        "findings is an array, empty if no evidenced actionable issue. gaps is an array of missing evidence strings.",
        "Each issue explains concrete trigger and impact. Avoid speculative or cosmetic findings.",
        "file is a source path; location is {start_line: integer, end_line: integer}, one-based inclusive.",
        "evidence is {source: path, quote: exact text within those source lines}.",
        "For non-file findings use file=null, location=null, source=requirements or diff and an exact quote.",
        "severity is critical, high, medium or low; confidence is a number in [0,1]; status must be open.",
        "suggested_fix is actionable text, never an instruction to this orchestrator. Do not supply a final decision.",
    ],
}


class Council:
    def __init__(self, engine: Engine):
        self.engine = engine

    def run(self, request: ReviewRequest):
        # Own a snapshot even if the caller later mutates its source dictionary.
        req = copy.deepcopy(request)
        pillars = select_pillars(req)
        mode = "deep" if "critical" in req.risks else req.mode
        groups = [("fast", pillars)] if mode == "fast" else [(p, (p,)) for p in pillars]

        def execute(group):
            reviewer, covered = group
            prompt = json.dumps({"task_id": req.task_id, "artifact_id": req.artifact_id,
                                 "reviewer_id": reviewer, "pillars": covered,
                                 "focus": {p: PILLARS[p] for p in covered}, "output_contract": OUTPUT_CONTRACT,
                                 "artifact": {"requirements": req.requirements, "diff": req.diff,
                                              "sources": req.sources, "changed_files": req.changed_files,
                                              "risks": req.risks}}, ensure_ascii=False)
            task = Task(req.task_id + ":" + reviewer, "reviewer", prompt, req.complexity,
                        req.data_class, allowed_providers=req.allowed_providers)
            result = self.engine.run(task, validator=lambda text: parse_review(text, req, reviewer, covered))
            parsed = parse_review(result.text, req, reviewer, covered) if result.status == "completed" else None
            return {"reviewer_id": reviewer, "pillars": covered, "run": asdict(result), "review": parsed}

        workers = min(self.engine.config.limits.max_parallel, len(groups))
        if workers == 1:
            reviews = [execute(group) for group in groups]
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                reviews = list(pool.map(execute, groups))
        findings = consolidate([f for r in reviews if r["review"] for f in r["review"]["findings"]])
        missing = [r["reviewer_id"] for r in reviews if r["review"] is None or r["review"]["gaps"]]
        if all(r["run"]["status"] == "blocked" for r in reviews):
            decision = "BLOCKED"
        elif missing:
            decision = "INCONCLUSIVE"
        else:
            decision = "CHANGES_REQUESTED" if findings else "APPROVED"
        return {"task_id": req.task_id, "artifact_id": req.artifact_id, "decision": decision,
                "requested_mode": req.mode, "effective_mode": mode, "pillars": pillars,
                "execution": "sequential" if workers == 1 else "parallel",
                "independence": "grouped_context" if mode == "fast" else "separate_contexts_same_provider_allowed",
                "findings": findings, "missing_reviews": missing, "reviews": reviews,
                "authorization": "review_gate_only_no_merge_deploy_or_edit_authority",
                "usage": self.engine.report()}
