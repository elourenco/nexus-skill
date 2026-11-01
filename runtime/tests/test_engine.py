import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from runtime.nexus_runtime.engine import Config, Engine, Task, load_config
from runtime.nexus_runtime.adapters import AdapterError, Completion


def configuration(**limits):
    return {
        "providers": [{"id": "one", "kind": "openai_responses", "enabled": True,
                       "max_parallel": 2, "data_classes": ["public", "private"],
                       "api_key_env": "NEXUS_TEST_UNUSED"}],
        "models": [
            {"id": "small", "provider": "one", "model": "configured-small",
             "capabilities": ["text", "reasoning", "code_review"], "level": 1,
             "context_tokens": 100000, "max_output_tokens": 4000,
             "input_usd_per_million": 1, "output_usd_per_million": 2},
            {"id": "large", "provider": "one", "model": "configured-large",
             "capabilities": ["text", "reasoning", "code_review"], "level": 3,
             "context_tokens": 200000, "max_output_tokens": 8000,
             "input_usd_per_million": 4, "output_usd_per_million": 8},
        ],
        "routing": {"policy": "balanced", "order": ["small", "large"]},
        "limits": {"max_calls": 10, "max_parallel": 2, "timeout_seconds": 5,
                   "deadline_seconds": 30, "max_prompt_bytes": 20000,
                   "max_output_tokens": 1000, **limits},
    }


class FakeAdapter:
    def __init__(self, outputs=None, available=True):
        self.outputs = list(outputs or ["done"])
        self.calls = []
        self.is_available = available
        self.lock = threading.Lock()

    def available(self):
        return self.is_available

    def complete(self, **kwargs):
        with self.lock:
            self.calls.append(kwargs)
            output = self.outputs.pop(0) if self.outputs else "done"
        if isinstance(output, Exception):
            raise output
        return Completion(output, 12, 4, "completed", kwargs["remote_model"])


class EngineTests(unittest.TestCase):
    def make_engine(self, data=None, adapter=None):
        return Engine(Config.from_dict(data or configuration()),
                      adapters={"one": adapter or FakeAdapter()})

    def test_registry_has_six_roles_and_host_handoffs(self):
        engine = self.make_engine()
        self.assertEqual(set(engine.registry), {
            "planner", "architect", "implementer", "tester", "reviewer", "memory_curator"})
        self.assertEqual(engine.registry["implementer"].tools, ())
        result = engine.run(Task("t", "implementer", "prepare a patch"))
        self.assertEqual(result.status, "completed")
        self.assertTrue(result.host_handoff)

    def test_model_replaced_by_configuration(self):
        data = configuration()
        data["models"][0]["model"] = "replacement-without-code-changes"
        adapter = FakeAdapter()
        self.make_engine(data, adapter).run(Task("t", "planner", "plan"))
        self.assertEqual(adapter.calls[0]["remote_model"], "replacement-without-code-changes")

    def test_missing_provider_is_blocked_without_call(self):
        adapter = FakeAdapter(available=False)
        result = self.make_engine(adapter=adapter).run(Task("t", "planner", "plan"))
        self.assertEqual(result.status, "blocked")
        self.assertEqual(adapter.calls, [])

    def test_privacy_tools_and_context_are_hard_filters(self):
        engine = self.make_engine()
        for task in [Task("t", "planner", "secret", data_class="restricted"),
                     Task("t", "planner", "plan", required_capabilities=("shell",)),
                     Task("t", "planner", "plan", allowed_providers=("absent",))]:
            self.assertEqual(engine.run(task).status, "blocked")
        data = configuration()
        for model in data["models"]:
            model["context_tokens"] = 10
        self.assertEqual(self.make_engine(data).run(Task("t", "planner", "plan")).status, "blocked")

    def test_policies_only_rank_eligible_models(self):
        data = configuration()
        for policy, expected in [("economy", "small"), ("balanced", "small"), ("quality", "large")]:
            data["routing"]["policy"] = policy
            engine = self.make_engine(data)
            self.assertEqual(engine.route(Task("t", "planner", "plan"))[0].id, expected)
        self.assertEqual(self.make_engine().route(Task("t", "planner", "complex", complexity=3))[0].id, "large")

    def test_budget_admission_is_atomic(self):
        engine = self.make_engine(configuration(max_calls=1))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda n: engine.run(Task(str(n), "planner", "plan")), range(2)))
        self.assertEqual(sorted(r.status for r in results), ["blocked", "completed"])
        self.assertEqual(len(engine.adapters["one"].calls), 1)

    def test_estimated_cost_reservations_cannot_race(self):
        sample = self.make_engine()
        sample.run(Task("sample", "planner", "plan"))
        one_call = sample.report()["reserved_estimated_cost_usd"]
        engine = self.make_engine(configuration(max_estimated_cost_usd=one_call * 1.5))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda n: engine.run(Task(str(n), "planner", "plan")), range(2)))
        self.assertEqual(sorted(r.status for r in results), ["blocked", "completed"])

    def test_two_concurrent_insufficient_reviews_share_one_escalation(self):
        engine = self.make_engine(adapter=FakeAdapter(["bad"] * 4))
        def invalid(text):
            raise ValueError("invalid")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda n: engine.run(Task(str(n), "reviewer", "review"), invalid), range(2)))
        self.assertTrue(all(r.status == "inconclusive" for r in results))
        self.assertEqual(len(engine.adapters["one"].calls), 3)
        self.assertEqual(engine.report()["escalations"], 1)

    def test_provider_limit_bounds_real_parallel_execution(self):
        class ConcurrentAdapter(FakeAdapter):
            def __init__(self):
                super().__init__()
                self.active = 0
                self.peak = 0
                self.overlap = threading.Barrier(2)
            def complete(self, **kwargs):
                with self.lock:
                    self.active += 1
                    self.peak = max(self.peak, self.active)
                self.overlap.wait(timeout=2)
                result = super().complete(**kwargs)
                with self.lock:
                    self.active -= 1
                return result
        adapter = ConcurrentAdapter()
        engine = self.make_engine(adapter=adapter)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda n: engine.run(Task(str(n), "planner", "plan")), range(4)))
        self.assertTrue(all(r.status == "completed" for r in results))
        self.assertEqual(adapter.peak, 2)

    def test_missing_one_provider_does_not_disable_others(self):
        data = configuration()
        other = dict(data["providers"][0], id="two", kind="anthropic_messages")
        data["providers"].append(other)
        data["models"][1]["provider"] = "two"
        engine = Engine(Config.from_dict(data), adapters={"one": FakeAdapter(available=False), "two": FakeAdapter()})
        result = engine.run(Task("t", "planner", "plan"))
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.provider, "two")

    def test_deadline_stops_new_calls_and_late_results_do_not_complete(self):
        now = [0.0]
        class Slow(FakeAdapter):
            def complete(self, **kwargs):
                now[0] = 31
                return super().complete(**kwargs)
        adapter = Slow()
        engine = Engine(Config.from_dict(configuration()), adapters={"one": adapter}, clock=lambda: now[0])
        self.assertEqual(engine.run(Task("late", "planner", "plan")).status, "inconclusive")
        self.assertEqual(engine.run(Task("next", "planner", "plan")).status, "blocked")
        self.assertEqual(len(adapter.calls), 1)

    def test_uncertain_timeout_is_not_retried_or_refunded(self):
        adapter = FakeAdapter([AdapterError("timeout", outcome_unknown=True)])
        engine = self.make_engine(adapter=adapter)
        result = engine.run(Task("t", "planner", "plan"))
        self.assertEqual(result.status, "inconclusive")
        self.assertEqual(len(adapter.calls), 1)
        self.assertTrue(engine.report()["attempts"][0]["outcome_unknown"])
        self.assertGreater(engine.report()["reserved_estimated_tokens"], 0)

    def test_one_escalation_for_entire_execution(self):
        adapter = FakeAdapter(["invalid", "invalid", "invalid"])
        engine = self.make_engine(adapter=adapter)

        def validate(text):
            if text == "invalid":
                raise ValueError("invalid structured output")

        first = engine.run(Task("first", "reviewer", "review"), validator=validate)
        second = engine.run(Task("second", "reviewer", "review"), validator=validate)
        self.assertEqual(first.status, "inconclusive")
        self.assertEqual(second.status, "inconclusive")
        self.assertEqual(len(adapter.calls), 3)
        self.assertEqual(engine.report()["escalations"], 1)

    def test_refusal_is_not_escalated(self):
        class Refusal(FakeAdapter):
            def complete(self, **kwargs):
                self.calls.append(kwargs)
                return Completion("refused", None, None, "refused", kwargs["remote_model"])
        adapter = Refusal()
        result = self.make_engine(adapter=adapter).run(Task("t", "planner", "plan"))
        self.assertEqual(result.status, "inconclusive")
        self.assertEqual(len(adapter.calls), 1)

    def test_unknown_prices_fail_estimated_cost_budget_closed(self):
        data = configuration(max_estimated_cost_usd=1)
        for model in data["models"]:
            del model["input_usd_per_million"]
        engine = self.make_engine(data)
        self.assertEqual(engine.run(Task("t", "planner", "plan")).status, "blocked")

    def test_route_uses_remaining_budget_before_ranking(self):
        data = configuration(max_estimated_cost_usd=0.004)
        data["models"][1]["input_usd_per_million"] = 0.1
        data["models"][1]["output_usd_per_million"] = 0.1
        engine = self.make_engine(data)
        self.assertEqual(engine.run(Task("first", "planner", "plan")).model, "small")
        result = engine.run(Task("second", "planner", "plan"))
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.model, "large")

    def test_candidate_is_rechecked_when_balance_changes_before_reservation(self):
        data = configuration(max_estimated_cost_usd=0.004)
        data["models"][1]["input_usd_per_million"] = 0.1
        data["models"][1]["output_usd_per_million"] = 0.1
        engine = self.make_engine(data)
        original = engine._reserve
        consumed = [False]
        def reserve(task, model, escalation):
            if not consumed[0]:
                consumed[0] = True
                # Emulate another workflow member admitting a call after routing.
                original(Task("concurrent", "planner", "plan"), model, False)
            return original(task, model, escalation)
        engine._reserve = reserve
        result = engine.run(Task("next", "planner", "plan"))
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.model, "large")

    def test_usage_above_estimate_blocks_further_dispatch(self):
        class MoreUsage(FakeAdapter):
            def complete(self, **kwargs):
                self.calls.append(kwargs)
                return Completion("done", 12000, 1000, "completed", kwargs["remote_model"])
        adapter = MoreUsage()
        engine = self.make_engine(configuration(max_estimated_tokens=10000), adapter)
        self.assertEqual(engine.run(Task("first", "planner", "plan")).status, "completed")
        self.assertEqual(engine.run(Task("next", "planner", "plan")).status, "blocked")
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(engine.report()["reserved_estimated_tokens"], 13000)

    def test_bad_configuration_fails_before_network(self):
        for field, value in [("max_calls", True), ("max_parallel", 0), ("timeout_seconds", float("nan"))]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                Config.from_dict(configuration(**{field: value}))
        data = configuration()
        data["routing"]["policy"] = "silent-default"
        with self.assertRaises(ValueError):
            Config.from_dict(data)
        data = configuration()
        data["limits"]["hard_budget_usd"] = 1
        with self.assertRaises(ValueError):
            Config.from_dict(data)


if __name__ == "__main__":
    unittest.main()
