"""Bounded, non-retrying text completions through configured HTTP endpoints."""

from dataclasses import dataclass
import ipaddress
import json
import math
import os
import socket
import time
from typing import Callable
from urllib import error, parse, request


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    status: str
    remote_model: str
    request_id: str | None = None


class AdapterError(Exception):
    """Safe public error; provider payloads and connection details stay private."""

    def __init__(self, code: str, outcome_unknown: bool = False):
        self.code = code if code in {
            "auth", "unavailable", "rate_limit", "invalid_request", "timeout",
            "transport", "invalid_response",
        } else "transport"
        self.outcome_unknown = outcome_unknown
        super().__init__(self.code)


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_transport(url: str, headers: dict, payload: dict, timeout_seconds: float) -> dict:
    """Bound response size and check elapsed time between blocking operations.

    The socket timeout protects against inactivity. The monotonic deadline also
    stops continuously arriving bodies between read1 calls. This is not a hard
    wall deadline: DNS, connection establishment, or one read1 call may overrun
    it. Closing the connection does not imply cancellation at the provider.
    """
    req = request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    # No proxy discovery: credentials must travel only to the configured endpoint.
    opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
    deadline = time.monotonic() + timeout_seconds
    try:
        with opener.open(req, timeout=timeout_seconds) as result:
            raw = bytearray()
            limit = 2 * 1024 * 1024
            while True:
                if time.monotonic() >= deadline:
                    raise AdapterError("timeout", True)
                block = result.read1(min(64 * 1024, limit + 1 - len(raw)))
                if time.monotonic() >= deadline:
                    raise AdapterError("timeout", True)
                if not block:
                    break
                raw.extend(block)
                if len(raw) > limit:
                    raise AdapterError("invalid_response", True)
            try:
                body = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeError):
                raise AdapterError("invalid_response", True) from None
            if not isinstance(body, dict):
                raise AdapterError("invalid_response", True)
            request_id = result.headers.get("x-request-id") or result.headers.get("request-id")
            if request_id:
                body = {**body, "_http_request_id": request_id}
            return body
    except error.HTTPError as exc:
        status = exc.code
        exc.close()
        code = {400: "invalid_request", 401: "auth", 403: "auth", 429: "rate_limit"}.get(status, "transport")
        raise AdapterError(code, status >= 500) from None
    except (TimeoutError, socket.timeout):
        raise AdapterError("timeout", True) from None
    except error.URLError as exc:
        code = "timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "transport"
        raise AdapterError(code, True) from None
    except (OSError, ValueError):
        raise AdapterError("transport", True) from None


def _token(usage: dict, key: str) -> int | None:
    value = usage.get(key)
    if value is not None and (type(value) is not int or value < 0 or value > 2 ** 53 - 1):
        raise AdapterError("invalid_response", True)
    return value


def _check_provider_error(body: dict) -> None:
    """Classify only known error identifiers; never retain provider messages."""
    failure = body.get("error")
    if failure is None and body.get("type") != "error":
        return
    identifier = None
    if isinstance(failure, dict):
        identifier = failure.get("code") or failure.get("type")
    codes = {
        "invalid_api_key": "auth", "authentication_error": "auth",
        "permission_error": "auth", "rate_limit_exceeded": "rate_limit",
        "rate_limit_error": "rate_limit", "invalid_request_error": "invalid_request",
        "server_error": "transport", "api_error": "transport",
        "overloaded_error": "transport",
    }
    code = codes.get(identifier, "invalid_response") if isinstance(identifier, str) else "invalid_response"
    raise AdapterError(code, code in {"transport", "invalid_response"})


class HTTPAdapter:
    def __init__(self, kind: str, endpoint: str, api_key_env: str | None = None,
                 api_version: str | None = None, transport: Callable | None = None):
        if kind not in {"openai_responses", "anthropic_messages"} or not isinstance(endpoint, str):
            raise AdapterError("invalid_request")
        try:
            parts = parse.urlsplit(endpoint)
            host = parts.hostname
            _ = parts.port
            loopback = host == "localhost"
            if host and not loopback:
                try:
                    loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    pass
            valid = (parts.scheme == "https" or parts.scheme == "http" and loopback)
            if (not valid or not host or parts.username is not None or parts.password is not None
                    or "?" in endpoint or "#" in endpoint or any(c.isspace() or ord(c) < 32 for c in endpoint)):
                raise ValueError
        except (ValueError, TypeError):
            raise AdapterError("invalid_request") from None
        self.kind = kind
        self.endpoint = endpoint
        self.api_key_env = api_key_env
        self.api_version = api_version
        self._transport = transport or _http_transport

    def available(self) -> bool:
        return self.api_key_env is None or bool(os.environ.get(self.api_key_env))

    def complete(self, remote_model: str, instructions: str, prompt: str,
                 max_output_tokens: int, timeout_seconds: float) -> Completion:
        if (not isinstance(remote_model, str) or not remote_model.strip()
                or not isinstance(instructions, str) or not isinstance(prompt, str)
                or type(max_output_tokens) is not int or max_output_tokens <= 0
                or isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
                or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
            raise AdapterError("invalid_request")
        key = os.environ.get(self.api_key_env) if self.api_key_env else None
        if self.api_key_env and not key:
            raise AdapterError("unavailable")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.kind == "openai_responses":
            if key:
                headers["Authorization"] = "Bearer " + key
            payload = {"model": remote_model, "instructions": instructions, "input": prompt,
                       "max_output_tokens": max_output_tokens, "store": False}
        else:
            if key:
                headers["x-api-key"] = key
            if self.api_version:
                headers["anthropic-version"] = self.api_version
            payload = {"model": remote_model, "system": instructions,
                       "messages": [{"role": "user", "content": prompt}], "max_tokens": max_output_tokens}
        try:
            body = self._transport(self.endpoint, headers, payload, timeout_seconds)
        except AdapterError:
            raise
        except (TimeoutError, socket.timeout):
            raise AdapterError("timeout", True) from None
        except Exception:
            raise AdapterError("transport", True) from None
        return self._parse(body, remote_model)

    def _parse(self, body: dict, requested_model: str) -> Completion:
        if not isinstance(body, dict):
            raise AdapterError("invalid_response", True)
        _check_provider_error(body)
        usage = body.get("usage", {})
        if not isinstance(usage, dict):
            raise AdapterError("invalid_response", True)
        input_tokens = _token(usage, "input_tokens")
        output_tokens = _token(usage, "output_tokens")
        texts = []
        refused = False
        truncated = False
        if self.kind == "openai_responses":
            provider_status = body.get("status")
            if provider_status == "incomplete":
                details = body.get("incomplete_details")
                reason = details.get("reason") if isinstance(details, dict) else None
                truncated = reason == "max_output_tokens"
                refused = reason == "content_filter"
                if not truncated and not refused:
                    raise AdapterError("invalid_response", True)
            elif provider_status != "completed":
                raise AdapterError("invalid_response", True)
            output = body.get("output")
            if not isinstance(output, list):
                raise AdapterError("invalid_response", True)
            content = []
            for item in output:
                if not isinstance(item, dict):
                    raise AdapterError("invalid_response", True)
                if item.get("type") == "reasoning":
                    continue
                if item.get("type") != "message" or item.get("role") != "assistant":
                    raise AdapterError("invalid_response", True)
                if item.get("status") != "completed" and not (
                        (truncated or refused) and item.get("status") == "incomplete"):
                    raise AdapterError("invalid_response", True)
                pieces = item.get("content")
                if not isinstance(pieces, list):
                    raise AdapterError("invalid_response", True)
                content.extend(pieces)
            text_type = "output_text"
        else:
            stop_reason = body.get("stop_reason")
            if not isinstance(stop_reason, str) or stop_reason not in {"end_turn", "max_tokens", "refusal"}:
                raise AdapterError("invalid_response", True)
            truncated = stop_reason == "max_tokens"
            refused = stop_reason == "refusal"
            content = body.get("content")
            text_type = "text"
            cache = [_token(usage, key) for key in ("cache_creation_input_tokens", "cache_read_input_tokens")]
            if input_tokens is not None:
                input_tokens += sum(value for value in cache if value is not None)
        if not isinstance(content, list):
            raise AdapterError("invalid_response", True)
        for piece in content:
            if not isinstance(piece, dict):
                raise AdapterError("invalid_response", True)
            if piece.get("type") == text_type:
                if not isinstance(piece.get("text"), str):
                    raise AdapterError("invalid_response", True)
                texts.append(piece["text"])
            elif piece.get("type") == "refusal":
                refused = True
            else:
                raise AdapterError("invalid_response", True)
        text = "\n".join(texts)
        if refused:
            status = "refused"
        elif truncated:
            status = "incomplete"
        elif text.strip():
            status = "completed"
        else:
            raise AdapterError("invalid_response", True)
        model = body.get("model", requested_model)
        request_id = body.get("_http_request_id")
        if not isinstance(model, str) or not model or (request_id is not None and not isinstance(request_id, str)):
            raise AdapterError("invalid_response", True)
        return Completion(text, input_tokens, output_tokens, status, model, request_id)
