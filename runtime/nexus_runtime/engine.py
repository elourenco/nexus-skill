"""Configuration, capability routing and a bounded, in-process execution owner."""

from __future__ import annotations

import copy
import json
import math
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable

from .adapters import AdapterError, HTTPAdapter
from .registry import COMMON, REGISTRY


def object_fields(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError("invalid or missing configuration fields")
    return value


def number(value, *, minimum=0, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("expected a finite number")
    if abs(value) > 2 ** 53 - 1 or not math.isfinite(value) or value < minimum or (integer and not isinstance(value, int)):
        raise ValueError("number outside allowed range")
    return value


def string(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected a nonempty string")
    return value


def strings(value):
    if not isinstance(value, (list, tuple)) or any(not isinstance(v, str) or not v for v in value):
        raise ValueError("expected a list of strings")
    if len(set(value)) != len(value):
        raise ValueError("duplicate values")
    return tuple(value)


@dataclass(frozen=True)
class Provider:
    id: str
    kind: str
    enabled: bool
    max_parallel: int
    data_classes: tuple[str, ...]
    endpoint: str
    api_key_env: str | None
    api_version: str | None


@dataclass(frozen=True)
class Model:
    id: str
    provider: str
    model: str
    capabilities: tuple[str, ...]
    level: int
    context_tokens: int
    max_output_tokens: int
    input_usd_per_million: Decimal | None = None
    output_usd_per_million: Decimal | None = None
    success_rate: float | None = None
    observed_latency_ms: float | None = None
    metrics_source: str | None = None

    def estimate_cost(self, input_tokens, output_tokens):
        if self.input_usd_per_million is None or self.output_usd_per_million is None:
            return None
        return (self.input_usd_per_million * input_tokens +
                self.output_usd_per_million * output_tokens) / Decimal(1000000)


@dataclass(frozen=True)
class Limits:
    max_calls: int
    max_parallel: int
    timeout_seconds: float
    deadline_seconds: float
    max_prompt_bytes: int
    max_output_tokens: int
    max_estimated_tokens: int | None = None
    max_estimated_cost_usd: Decimal | None = None


@dataclass(frozen=True)
class Config:
    providers: tuple[Provider, ...]
    models: tuple[Model, ...]
    limits: Limits
    policy: str
    order: tuple[str, ...]

    @classmethod
    def from_dict(cls, data):
        object_fields(data, ("providers", "models", "limits", "routing"),
                      ("providers", "models", "limits", "routing"))
        if not isinstance(data["providers"], list) or not isinstance(data["models"], list):
            raise ValueError("providers and models must be arrays")
        providers = []
        defaults = {
            "openai_responses": ("https://api.openai.com/v1/responses", "OPENAI_API_KEY", None),
            "anthropic_messages": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "2026-10-21"),
        }
        for p in data["providers"]:
            object_fields(p, ("id", "kind", "enabled", "max_parallel", "data_classes", "endpoint",
                              "api_key_env", "api_version"),
                          ("id", "kind", "enabled", "max_parallel", "data_classes"))
            if p["kind"] not in defaults or not isinstance(p["enabled"], bool):
                raise ValueError("unsupported adapter or invalid enabled flag")
            endpoint, key, version = defaults[p["kind"]]
            classes = strings(p["data_classes"])
            if not set(classes) <= {"public", "private", "restricted"}:
                raise ValueError("unknown data class")
            key = p.get("api_key_env", key)
            version = p.get("api_version", version)
            if key is not None:
                string(key)
            if version is not None:
                string(version)
            providers.append(Provider(string(p["id"]), p["kind"], p["enabled"],
                                      number(p["max_parallel"], minimum=1, integer=True), classes,
                                      string(p.get("endpoint", endpoint)), key, version))
        provider_ids = {p.id for p in providers}
        if len(provider_ids) != len(providers):
            raise ValueError("duplicate provider id")
        models = []
        for m in data["models"]:
            required = ("id", "provider", "model", "capabilities", "level", "context_tokens", "max_output_tokens")
            object_fields(m, (*required, "input_usd_per_million", "output_usd_per_million",
                              "success_rate", "observed_latency_ms", "metrics_source"), required)
            if m["provider"] not in provider_ids:
                raise ValueError("model references an undeclared provider")
            prices = [None if m.get(k) is None else Decimal(str(number(m[k])))
                      for k in ("input_usd_per_million", "output_usd_per_million")]
            success = None if m.get("success_rate") is None else number(m["success_rate"])
            latency = None if m.get("observed_latency_ms") is None else number(m["observed_latency_ms"])
            if success is not None and success > 1:
                raise ValueError("success_rate must be between zero and one")
            source = m.get("metrics_source")
            if success is not None or latency is not None:
                string(source)
            level = number(m["level"], minimum=1, integer=True)
            if level > 3:
                raise ValueError("level must be 1, 2 or 3")
            models.append(Model(string(m["id"]), m["provider"], string(m["model"]),
                                strings(m["capabilities"]), level,
                                number(m["context_tokens"], minimum=1, integer=True),
                                number(m["max_output_tokens"], minimum=1, integer=True),
                                *prices, success, latency, source))
        model_ids = {m.id for m in models}
        if len(model_ids) != len(models):
            raise ValueError("duplicate model id")
        required = ("max_calls", "max_parallel", "timeout_seconds", "deadline_seconds",
                    "max_prompt_bytes", "max_output_tokens")
        l = object_fields(data["limits"], (*required, "max_estimated_tokens", "max_estimated_cost_usd"), required)
        limits = Limits(**{
            k: (Decimal(str(number(v))) if k == "max_estimated_cost_usd" else
                number(v, minimum=1, integer=k not in ("timeout_seconds", "deadline_seconds")))
            for k, v in l.items()
        })
        if max(limits.timeout_seconds, limits.deadline_seconds) > threading.TIMEOUT_MAX:
            raise ValueError("timeout exceeds platform supported range")
        routing = object_fields(data["routing"], ("policy", "order"), ("policy", "order"))
        if routing["policy"] not in ("economy", "balanced", "quality"):
            raise ValueError("unknown routing policy")
        order = strings(routing["order"])
        if set(order) != model_ids:
            raise ValueError("routing order must contain every configured model exactly once")
        return cls(tuple(providers), tuple(models), limits, routing["policy"], order)


def load_config(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return Config.from_dict(json.loads(Path(path).read_text(), object_pairs_hook=unique))


@dataclass(frozen=True)
class Task:
    id: str
    agent: str
    prompt: str
    complexity: int = 1
    data_class: str = "private"
    required_capabilities: tuple[str, ...] = ()
    allowed_providers: tuple[str, ...] | None = None


@dataclass(frozen=True)
class RunResult:
    task_id: str
    status: str
    text: str | None = None
    error: str | None = None
    model: str | None = None
    provider: str | None = None
    host_handoff: bool = False


class Engine:
    """One instance owns one workflow budget, including every Council member."""

    def __init__(self, config: Config, adapters=None, clock=time.monotonic):
        self.config = config
        self.registry = REGISTRY
        self.providers = {p.id: p for p in config.providers}
        self.adapters = adapters if adapters is not None else {
            p.id: HTTPAdapter(p.kind, p.endpoint, p.api_key_env, p.api_version)
            for p in config.providers
        }
        self.clock = clock
        self.deadline = clock() + config.limits.deadline_seconds
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(config.limits.max_parallel)
        self.provider_slots = {p.id: threading.BoundedSemaphore(p.max_parallel) for p in config.providers}
        self.attempts = []
        self.reserved_tokens = 0
        self.reserved_cost = Decimal(0)
        self.unknown_cost = False
        self.escalations = 0

    def _instructions(self, task):
        return COMMON + "\n" + self.registry[task.agent].instructions

    def _input_estimate(self, task):
        # UTF-8 bytes are a conservative text heuristic, NOT a tokenizer/accounting guarantee.
        return len((self._instructions(task) + "\n" + task.prompt).encode("utf-8"))

    def _check_task(self, task):
        string(task.id)
        string(task.prompt)
        if task.agent not in self.registry or task.data_class not in ("public", "private", "restricted"):
            raise ValueError("unknown role or data class")
        if number(task.complexity, minimum=1, integer=True) > 3:
            raise ValueError("complexity must be 1, 2 or 3")
        strings(task.required_capabilities)
        if task.allowed_providers is not None:
            strings(task.allowed_providers)

    def route(self, task: Task, *, above_level=0):
        self._check_task(task)
        estimate = self._input_estimate(task)
        limits = self.config.limits
        if estimate > limits.max_prompt_bytes:
            return []
        required = set(self.registry[task.agent].capabilities) | set(task.required_capabilities)
        # This implementation has no tools, even if a catalog claims the model supports them.
        if not required <= {"text", "reasoning", "code_review"}:
            return []
        with self.lock:
            remaining_cost = (None if limits.max_estimated_cost_usd is None else
                              limits.max_estimated_cost_usd - self.reserved_cost)
            if (len(self.attempts) >= limits.max_calls or self.clock() >= self.deadline or
                    (limits.max_estimated_tokens is not None and
                     self.reserved_tokens + estimate + limits.max_output_tokens > limits.max_estimated_tokens)):
                return []
        candidates = []
        for model in self.config.models:
            provider = self.providers[model.provider]
            adapter = self.adapters.get(provider.id)
            if (not provider.enabled or adapter is None or not adapter.available() or
                    task.data_class not in provider.data_classes or
                    (task.allowed_providers is not None and provider.id not in task.allowed_providers) or
                    not required <= set(model.capabilities) or model.level < task.complexity or
                    model.level <= above_level or model.max_output_tokens < limits.max_output_tokens or
                    model.context_tokens < estimate + limits.max_output_tokens):
                continue
            cost = model.estimate_cost(estimate, limits.max_output_tokens)
            if remaining_cost is not None and (cost is None or cost > remaining_cost):
                continue
            candidates.append(model)

        def score(model):
            cost = model.estimate_cost(estimate, limits.max_output_tokens)
            cost = float("inf") if cost is None else float(cost)
            history = 1 if model.success_rate is None else 1 - model.success_rate
            latency = float("inf") if model.observed_latency_ms is None else model.observed_latency_ms
            with self.lock:
                previous = [a for a in self.attempts if a["model"] == model.id and a["status"] != "running"]
                if previous:
                    history = 1 - sum(a["status"] == "completed" for a in previous) / len(previous)
                    latency = sum(a["latency_ms"] for a in previous) / len(previous)
            order = self.config.order.index(model.id)
            if self.config.policy == "economy":
                return cost, latency, history, model.level, order
            if self.config.policy == "quality":
                return -model.level, history, latency, cost, order
            return model.level - task.complexity, history, latency, cost, order

        return sorted(candidates, key=score)

    def inspect(self):
        return {
            "providers": [{"id": p.id, "kind": p.kind, "enabled": p.enabled,
                           "locally_available": p.enabled and p.id in self.adapters and self.adapters[p.id].available(),
                           "authenticated_execution_verified": False} for p in self.config.providers],
            "models": [{"id": m.id, "provider": m.provider, "model": m.model,
                        "capabilities": m.capabilities, "capabilities_source": "operator_configuration"}
                       for m in self.config.models],
            "roles": [{"id": a.id, "tools": a.tools, "host_handoff": a.host_handoff}
                      for a in self.registry.values()],
            "execution": "text_only", "monetary_hard_cap_supported": False,
        }

    def _reserve(self, task, model, escalation):
        estimate = self._input_estimate(task) + self.config.limits.max_output_tokens
        cost = model.estimate_cost(self._input_estimate(task), self.config.limits.max_output_tokens)
        limits = self.config.limits
        with self.lock:
            if self.clock() >= self.deadline:
                return None, "deadline_exceeded"
            if len(self.attempts) >= limits.max_calls:
                return None, "call_budget_exhausted"
            if escalation and self.escalations:
                return None, "escalation_limit"
            if limits.max_estimated_tokens is not None and self.reserved_tokens + estimate > limits.max_estimated_tokens:
                return None, "estimated_token_budget_exhausted"
            if limits.max_estimated_cost_usd is not None and (cost is None or self.reserved_cost + cost > limits.max_estimated_cost_usd):
                return None, "estimated_cost_budget_exhausted"
            if escalation:
                self.escalations += 1
            self.reserved_tokens += estimate
            self.reserved_cost += cost or Decimal(0)
            self.unknown_cost |= cost is None
            attempt = {"task_id": task.id, "model": model.id, "provider": model.provider,
                       "requested_model": model.model, "effective_model": None,
                       "status": "running", "reason": "invalid_or_incomplete_output" if escalation else "initial",
                       "outcome_unknown": False, "input_tokens": None, "output_tokens": None,
                       "reserved_estimated_tokens": estimate, "usage_priced_cost_usd": None,
                       "estimated_cost_usd": None if cost is None else float(cost), "latency_ms": 0}
            self.attempts.append(attempt)
            return attempt, None

    def _record_usage(self, attempt, model, completion):
        with self.lock:
            attempt.update(input_tokens=completion.input_tokens, output_tokens=completion.output_tokens,
                           effective_model=completion.remote_model, request_id=completion.request_id)
            if completion.input_tokens is None or completion.output_tokens is None:
                return
            observed = completion.input_tokens + completion.output_tokens
            # Keep conservative reservations, but never ignore usage exceeding the heuristic.
            self.reserved_tokens += max(0, observed - attempt["reserved_estimated_tokens"])
            priced = model.estimate_cost(completion.input_tokens, completion.output_tokens)
            if priced is not None:
                reserved = model.estimate_cost(self._input_estimate_for_attempt(attempt), self.config.limits.max_output_tokens)
                self.reserved_cost += max(Decimal(0), priced - reserved)
                attempt["usage_priced_cost_usd"] = float(priced)

    def _input_estimate_for_attempt(self, attempt):
        return attempt["reserved_estimated_tokens"] - self.config.limits.max_output_tokens

    def _call(self, task, model, attempt, validator):
        started = self.clock()
        status, output, error, insufficient = "inconclusive", None, None, False
        try:
            completion = self.adapters[model.provider].complete(
                remote_model=model.model, instructions=self._instructions(task), prompt=task.prompt,
                max_output_tokens=self.config.limits.max_output_tokens,
                timeout_seconds=min(self.config.limits.timeout_seconds, max(0.001, self.deadline - self.clock())))
            self._record_usage(attempt, model, completion)
            if self.clock() >= self.deadline:
                error = "deadline_exceeded"
            elif completion.status == "refused":
                error = "refused"
            elif completion.status != "completed" or not completion.text.strip():
                error, insufficient = "incomplete_output", True
            else:
                try:
                    if validator:
                        validator(completion.text)
                except (ValueError, TypeError, RecursionError, OverflowError):
                    error, insufficient = "invalid_output", True
                else:
                    status, output = "completed", completion.text
        except AdapterError as exc:
            error = exc.code
            with self.lock:
                attempt["outcome_unknown"] = exc.outcome_unknown
            status = "inconclusive" if exc.outcome_unknown else "blocked"
        finally:
            with self.lock:
                attempt.update(status=status, error=error, latency_ms=(self.clock() - started) * 1000)
        return status, output, error, insufficient

    def run(self, task: Task, validator: Callable[[str], None] | None = None):
        candidates = self.route(task)
        if not candidates:
            return RunResult(task.id, "blocked", error="no_eligible_model")
        for index in range(2):
            error = "no_eligible_model"
            for model in candidates:
                if not self.slots.acquire(timeout=max(0, self.deadline - self.clock())):
                    return RunResult(task.id, "inconclusive" if index else "blocked", error="deadline_exceeded")
                provider_slot = self.provider_slots[model.provider]
                acquired_provider = False
                try:
                    acquired_provider = provider_slot.acquire(timeout=max(0, self.deadline - self.clock()))
                    if not acquired_provider:
                        return RunResult(task.id, "inconclusive" if index else "blocked", error="deadline_exceeded")
                    attempt, error = self._reserve(task, model, escalation=index == 1)
                    if attempt is None:
                        if error in ("estimated_cost_budget_exhausted", "estimated_token_budget_exhausted"):
                            continue  # No request was dispatched; another candidate may fit the new balance.
                        return RunResult(task.id, "inconclusive" if index else "blocked", error=error)
                    final_status, output, error, insufficient = self._call(task, model, attempt, validator)
                finally:
                    if acquired_provider:
                        provider_slot.release()
                    self.slots.release()
                break
            else:
                return RunResult(task.id, "inconclusive" if index else "blocked", error=error)
            if final_status == "completed":
                return RunResult(task.id, final_status, output, model=model.id, provider=model.provider,
                                 host_handoff=self.registry[task.agent].host_handoff)
            if insufficient and index == 0:
                higher = self.route(task, above_level=model.level)
                if higher:
                    candidates = higher
                    continue
            return RunResult(task.id, final_status, error=error, model=model.id, provider=model.provider)
        raise AssertionError("bounded attempt loop must return")

    def report(self):
        with self.lock:
            return {"attempts": copy.deepcopy(self.attempts), "escalations": self.escalations,
                    "reserved_estimated_tokens": self.reserved_tokens,
                    "reserved_estimated_cost_usd": None if self.unknown_cost else float(self.reserved_cost),
                    "budget_scope": "this_process_workflow", "monetary_hard_cap": False,
                    "reservation_policy": "retained_for_all_dispatched_calls"}
