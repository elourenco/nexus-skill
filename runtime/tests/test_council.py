import json
import unittest

from runtime.nexus_runtime.council import ReviewRequest, Council, select_pillars, parse_review, consolidate
from runtime.nexus_runtime.engine import Config, Engine
from runtime.tests.test_engine import FakeAdapter, configuration


def request(**overrides):
    data = {"task_id": "review-1", "mode": "balanced", "requirements": "Reject invalid input.",
            "diff": "--- a/src/parser.py\n+++ b/src/parser.py\n@@ -1 +1 @@\n-return None\n+return value",
            "changed_files": ["src/parser.py"], "sources": {"src/parser.py": "def parse(value):\n    return value\n"},
            "risks": [], "complexity": 1, "data_class": "private"}
    data.update(overrides)
    return ReviewRequest.from_dict(data)


def response(req, reviewer="quality", pillars=("quality",), findings=None, gaps=None):
    return {"task_id": req.task_id, "artifact_id": req.artifact_id, "reviewer_id": reviewer,
            "coverage": list(pillars), "findings": findings or [], "gaps": gaps or []}


def finding(pillar="quality", reviewer="quality"):
    return {"reviewer_id": reviewer, "task_id": "review-1", "pillar": pillar,
            "file": "src/parser.py", "location": {"start_line": 2, "end_line": 2},
            "severity": "high", "issue": "Invalid input is returned unchanged.",
            "evidence": {"source": "src/parser.py", "quote": "    return value"},
            "suggested_fix": "Reject invalid input before returning it.",
            "confidence": 0.9, "status": "open"}


class CouncilTests(unittest.TestCase):
    def test_pillars_are_selected_by_risk_and_files(self):
        self.assertEqual(select_pillars(request()), ("quality",))
        selected = select_pillars(request(changed_files=["src/auth/session.ts"],
                                         sources={"src/auth/session.ts": "export const session = null;"},
                                         risks=["concurrency", "performance"]))
        self.assertTrue({"security", "reliability", "performance", "quality"} <= set(selected))
        self.assertNotIn("product", selected)

    def test_hash_changes_with_evidence_or_requirements(self):
        self.assertNotEqual(request().artifact_id, request(requirements="Allow invalid input.").artifact_id)

    def test_missing_changed_file_snapshot_is_rejected_before_dispatch(self):
        with self.assertRaises(ValueError):
            request(sources={})

    def test_untrusted_oversized_numeric_value_is_rejected(self):
        req = request()
        bad = finding()
        bad["confidence"] = 10 ** 500
        with self.assertRaises(ValueError):
            parse_review(json.dumps(response(req, findings=[bad])), req, "quality", ("quality",))

    def test_false_evidence_and_wrong_revision_are_rejected(self):
        req = request()
        bad = finding()
        bad["evidence"]["quote"] = "imaginary code"
        with self.assertRaises(ValueError):
            parse_review(json.dumps(response(req, findings=[bad])), req, "quality", ("quality",))
        out = response(req)
        out["artifact_id"] = "previous revision"
        with self.assertRaises(ValueError):
            parse_review(json.dumps(out), req, "quality", ("quality",))

    def test_missing_coverage_and_self_resolved_findings_rejected(self):
        req = request()
        with self.assertRaises(ValueError):
            parse_review(json.dumps(response(req, pillars=())), req, "quality", ("quality",))
        bad = finding()
        bad["status"] = "resolved"
        with self.assertRaises(ValueError):
            parse_review(json.dumps(response(req, findings=[bad])), req, "quality", ("quality",))

    def test_duplicates_consolidate_without_losing_provenance(self):
        a, b = finding(), finding(pillar="security", reviewer="security")
        b["severity"] = "critical"
        merged = consolidate([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["severity"], "critical")
        self.assertEqual(set(merged[0]["reviewers"]), {"quality", "security"})
        self.assertEqual(set(merged[0]["pillars"]), {"quality", "security"})

    def test_independent_bugs_on_same_line_are_not_merged(self):
        a, b = finding(), finding()
        b["issue"] = "Returning shared state exposes mutations."
        self.assertEqual(len(consolidate([a, b])), 2)

    def run_council(self, req, answer, **limits):
        class Reviewer(FakeAdapter):
            def complete(self, **kwargs):
                from runtime.nexus_runtime.adapters import Completion
                data = json.loads(kwargs["prompt"])
                with self.lock:
                    self.calls.append(kwargs)
                return Completion(json.dumps(answer(data)), 12, 4, "completed", kwargs["remote_model"])
        adapter = Reviewer()
        adapter.outputs = []
        engine = Engine(Config.from_dict(configuration(**limits)), adapters={"one": adapter})
        return Council(engine).run(req), engine

    def test_single_provider_sequential_review_can_approve(self):
        req = request(mode="deep", risks=["contract"])
        def answer(data):
            return response(req, data["reviewer_id"], tuple(data["pillars"]))
        result, engine = self.run_council(req, answer, max_parallel=1)
        self.assertEqual(result["decision"], "APPROVED")
        self.assertEqual(result["execution"], "sequential")
        self.assertGreater(len(engine.adapters["one"].calls), 1)
        self.assertEqual(result["independence"], "separate_contexts_same_provider_allowed")

    def test_missing_pillar_never_approves(self):
        req = request(risks=["contract"])
        result, _ = self.run_council(req, lambda d: response(req, d["reviewer_id"], tuple(d["pillars"])),
                                     max_parallel=1, max_calls=1)
        self.assertIn(result["decision"], {"BLOCKED", "INCONCLUSIVE"})

    def test_fast_does_not_drop_high_risk_pillars(self):
        req = request(mode="fast", risks=["authorization"])
        result, engine = self.run_council(req, lambda d: response(req, d["reviewer_id"], tuple(d["pillars"])))
        self.assertEqual(result["decision"], "APPROVED")
        self.assertIn("security", result["pillars"])
        self.assertEqual(len(engine.adapters["one"].calls), 1)

    def test_explicit_critical_risk_requires_deep_review(self):
        req = request(mode="fast", risks=["critical", "authorization"])
        result, engine = self.run_council(req, lambda d: response(req, d["reviewer_id"], tuple(d["pillars"])))
        self.assertEqual(result["effective_mode"], "deep")
        self.assertGreater(len(engine.adapters["one"].calls), 1)

    def test_findings_request_changes_and_gaps_are_inconclusive(self):
        req = request()
        result, _ = self.run_council(req, lambda d: response(req, findings=[finding()]))
        self.assertEqual(result["decision"], "CHANGES_REQUESTED")
        self.assertFalse(result["findings"][0]["semantic_truth_verified"])
        result, _ = self.run_council(req, lambda d: response(req, gaps=["Missing caller contract"]))
        self.assertEqual(result["decision"], "INCONCLUSIVE")

    def test_model_cannot_supply_final_decision_or_execute_text(self):
        req = request()
        result, engine = self.run_council(req, lambda d: {"decision": "APPROVED", "command": "touch /tmp/unsafe"})
        self.assertEqual(result["decision"], "INCONCLUSIVE")
        self.assertLessEqual(len(engine.adapters["one"].calls), 2)


if __name__ == "__main__":
    unittest.main()
