import json
import os
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from runtime.nexus_runtime.adapters import AdapterError, HTTPAdapter


def response():
    return {"status": "completed", "model": "remote-v1", "output": [
        {"type": "message", "role": "assistant", "status": "completed", "content": [
            {"type": "output_text", "text": "Review ready"}]}],
        "usage": {"input_tokens": 10, "output_tokens": 3}}


class AdapterTests(unittest.TestCase):
    def call(self, body, kind="openai_responses"):
        adapter = HTTPAdapter(kind, "https://provider.example/v1", transport=lambda *args: body)
        return adapter.complete("configured-model", "Review only", "Diff", 123, 2.5)

    def test_openai_request_and_result(self):
        requests = []
        def transport(*args):
            requests.append(args)
            return response()
        with patch.dict(os.environ, {"TEST_KEY": "secret"}):
            result = HTTPAdapter("openai_responses", "https://provider.example/responses", "TEST_KEY", transport=transport).complete(
                "configured-model", "Review only", "Diff", 123, 2.5)
        self.assertEqual(result.text, "Review ready")
        self.assertEqual((result.input_tokens, result.output_tokens, result.status, result.remote_model), (10, 3, "completed", "remote-v1"))
        url, headers, payload, timeout = requests[0]
        self.assertEqual(url, "https://provider.example/responses")
        self.assertEqual(headers["Authorization"], "Bearer secret")
        self.assertEqual(payload, {"model": "configured-model", "instructions": "Review only", "input": "Diff", "max_output_tokens": 123, "store": False})
        self.assertEqual(timeout, 2.5)

    def test_anthropic_request_and_cache_usage(self):
        calls = []
        body = {"model": "remote-v2", "stop_reason": "end_turn", "content": [{"type": "text", "text": "OK"}],
                "usage": {"input_tokens": 10, "output_tokens": 2, "cache_creation_input_tokens": 4, "cache_read_input_tokens": 6}}
        with patch.dict(os.environ, {"TEST_KEY": "secret"}):
            result = HTTPAdapter("anthropic_messages", "https://provider.example/messages", "TEST_KEY", "configured-version", lambda *args: (calls.append(args), body)[1]).complete("model", "System", "Prompt", 9, 1)
        self.assertEqual(result.input_tokens, 20)
        self.assertEqual(calls[0][1]["x-api-key"], "secret")
        self.assertEqual(calls[0][1]["anthropic-version"], "configured-version")
        self.assertEqual(calls[0][2], {"model": "model", "system": "System", "messages": [{"role": "user", "content": "Prompt"}], "max_tokens": 9})

    def test_nonfinal_results_never_complete(self):
        body = response()
        body.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        self.assertEqual(self.call(body).status, "incomplete")
        body["incomplete_details"]["reason"] = "content_filter"
        body["output"][0]["status"] = "incomplete"
        self.assertEqual(self.call(body).status, "refused")
        body = response()
        body["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
        self.assertEqual(self.call(body).status, "refused")
        for reason, want in (("end_turn", "completed"), ("max_tokens", "incomplete"), ("refusal", "refused")):
            self.assertEqual(self.call({"model": "m", "stop_reason": reason, "content": [{"type": "text", "text": "Text"}]}, "anthropic_messages").status, want)

    def test_openai_failures_pending_and_unknown_are_not_model_truncation(self):
        for status in ("failed", "queued", "in_progress", "cancelled", "unknown", None, "incomplete"):
            body = response()
            body["status"] = status
            with self.subTest(status=status):
                with self.assertRaises(AdapterError) as error:
                    self.call(body)
                self.assertEqual(error.exception.code, "invalid_response")

    def test_provider_error_envelopes_are_sanitized_and_never_completions(self):
        for kind in ("openai_responses", "anthropic_messages"):
            for provider_code, want in (("server_error", "transport"), ("rate_limit_error", "rate_limit"), ("authentication_error", "auth"), ("invalid_request_error", "invalid_request"), ("unknown", "invalid_response")):
                body = response()
                body.update(type="error", error={"type": provider_code, "message": "secret-provider-error"})
                with self.subTest(kind=kind, code=provider_code):
                    with self.assertRaises(AdapterError) as error:
                        self.call(body, kind)
                    self.assertEqual(error.exception.code, want)
                    self.assertNotIn("secret", str(error.exception))

    def test_unexpected_tools_and_pause_never_trigger_model_escalation(self):
        for reason in ("tool_use", "pause_turn", "unknown", None, {}):
            with self.subTest(reason=reason):
                with self.assertRaises(AdapterError) as error:
                    self.call({"stop_reason": reason, "content": [{"type": "text", "text": "Some text"}]}, "anthropic_messages")
                self.assertEqual(error.exception.code, "invalid_response")
        body = response()
        body["output"].append({"type": "function_call", "name": "shell"})
        with self.assertRaises(AdapterError) as error:
            self.call(body)
        self.assertEqual(error.exception.code, "invalid_response")
        with self.assertRaises(AdapterError):
            self.call({"stop_reason": "end_turn", "content": [{"type": "tool_use", "name": "shell"}]}, "anthropic_messages")

    def test_missing_usage_and_invalid_usage(self):
        body = response()
        del body["usage"]
        result = self.call(body)
        self.assertIsNone(result.input_tokens)
        self.assertIsNone(result.output_tokens)
        for invalid in (True, -1, 1.5, "10", 10 ** 500):
            body["usage"] = {"input_tokens": invalid}
            with self.assertRaises(AdapterError) as error:
                self.call(body)
            self.assertEqual(error.exception.code, "invalid_response")
            self.assertTrue(error.exception.outcome_unknown)

    def test_ignores_convenience_text_and_checks_message_completion(self):
        body = response()
        body["output_text"] = "Untrusted convenience value"
        body["output"][0]["content"][0]["text"] = "  "
        with self.assertRaises(AdapterError):
            self.call(body)
        body = response()
        body["output"][0]["status"] = "incomplete"
        with self.assertRaises(AdapterError):
            self.call(body)
        body = response()
        body["output"].append({"type": "function_call", "name": "shell"})
        with self.assertRaises(AdapterError):
            self.call(body)

    def test_malformed_response_and_cache_counts_are_rejected(self):
        for body in ([], {"output": None}, {"output": [None]}, {"output": [{"type": "message", "role": "assistant", "content": {}}]}, {"output": [], "usage": []}):
            with self.assertRaises(AdapterError) as error:
                self.call(body)
            self.assertEqual(error.exception.code, "invalid_response")
        for value in (False, -1, "3"):
            with self.assertRaises(AdapterError):
                self.call({"stop_reason": "end_turn", "content": [], "usage": {"cache_read_input_tokens": value}}, "anthropic_messages")

    def test_transport_errors_are_unknown_sanitized_and_not_retried(self):
        for failure, code in ((TimeoutError("secret"), "timeout"), (OSError("secret"), "transport")):
            attempts = []
            def transport(*args):
                attempts.append(args)
                raise failure
            adapter = HTTPAdapter("openai_responses", "https://provider.example", transport=transport)
            with self.assertRaises(AdapterError) as error:
                adapter.complete("m", "s", "p", 1, 1)
            self.assertEqual((error.exception.code, error.exception.outcome_unknown), (code, True))
            self.assertNotIn("secret", str(error.exception))
            self.assertEqual(len(attempts), 1)

    def test_invalid_request_never_contacts_provider(self):
        calls = []
        adapter = HTTPAdapter("openai_responses", "https://provider.example", transport=lambda *args: calls.append(args))
        for model, tokens, timeout in (("", 1, 1), ("m", True, 1), ("m", 0, 1), ("m", 1, float("inf")), ("m", 1, 0)):
            with self.assertRaises(AdapterError) as error:
                adapter.complete(model, "s", "p", tokens, timeout)
            self.assertEqual(error.exception.code, "invalid_request")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AdapterError) as error:
                HTTPAdapter("openai_responses", "https://provider.example", "MISSING", transport=lambda *args: calls.append(args)).complete("m", "s", "p", 1, 1)
        self.assertEqual(error.exception.code, "unavailable")
        self.assertEqual(calls, [])

    def test_invalid_endpoint_types_are_sanitized(self):
        for endpoint in (None, False, 123):
            with self.assertRaises(AdapterError) as error:
                HTTPAdapter("openai_responses", endpoint)
            self.assertEqual(error.exception.code, "invalid_request")

    def test_availability_and_endpoint_validation(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(HTTPAdapter("openai_responses", "https://provider.example", "MISSING").available())
        self.assertTrue(HTTPAdapter("openai_responses", "http://127.0.0.1:1234").available())
        for url in ("http://example.com", "https://user:secret@example.com", "https://example.com?k=secret", "https://example.com/#secret", "file:///tmp/a"):
            with self.assertRaises(AdapterError) as error:
                HTTPAdapter("openai_responses", url)
            self.assertNotIn("secret", str(error.exception))


class HTTPTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                cls.received.append((self.path, dict(self.headers), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                if self.path == "/redirect":
                    self.send_response(307)
                    self.send_header("Location", "/target")
                    self.end_headers()
                    return
                if self.path.startswith("/status/"):
                    self.send_response(int(self.path.rsplit("/", 1)[1]))
                    self.end_headers()
                    self.wfile.write(b"secret-error-payload")
                    return
                self.send_response(200)
                self.send_header("x-request-id", "request-123")
                self.end_headers()
                if self.path == "/slow-drip":
                    payload = json.dumps(response()).encode()
                    try:
                        for byte in payload[:30]:
                            self.wfile.write(bytes([byte]))
                            self.wfile.flush()
                            time.sleep(0.01)
                        self.wfile.write(payload[30:])
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    return
                payload = b"x" * (2 * 1024 * 1024 + 1) if self.path == "/large" else (b"not-json-secret" if self.path == "/invalid" else json.dumps(response()).encode())
                self.wfile.write(payload)
            def log_message(self, *args):
                pass
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def call(self, path):
        return HTTPAdapter("openai_responses", f"http://127.0.0.1:{self.server.server_port}{path}").complete("m", "s", "p", 10, 1)

    def test_real_request_and_request_id(self):
        self.assertEqual(self.call("/ok").request_id, "request-123")
        self.assertEqual(self.received[-1][2]["input"], "p")

    def test_errors_are_sanitized_without_retry(self):
        for code, want, unknown in ((400, "invalid_request", False), (401, "auth", False), (403, "auth", False), (429, "rate_limit", False), (500, "transport", True)):
            before = len(self.received)
            with self.assertRaises(AdapterError) as error:
                self.call(f"/status/{code}")
            self.assertEqual((error.exception.code, error.exception.outcome_unknown), (want, unknown))
            self.assertNotIn("secret", str(error.exception))
            self.assertEqual(len(self.received), before + 1)

    def test_redirect_not_followed(self):
        before = len(self.received)
        with self.assertRaises(AdapterError):
            self.call("/redirect")
        self.assertEqual(len(self.received), before + 1)
        self.assertEqual(self.received[-1][0], "/redirect")

    def test_invalid_or_oversize_response_is_unknown(self):
        for path in ("/invalid", "/large"):
            with self.assertRaises(AdapterError) as error:
                self.call(path)
            self.assertEqual(error.exception.code, "invalid_response")
            self.assertTrue(error.exception.outcome_unknown)

    def test_continuous_slow_response_exceeds_total_read_budget(self):
        # Bytes arrive more frequently than the socket inactivity timeout.
        # The whole valid response nevertheless exceeds the request budget.
        adapter = HTTPAdapter("openai_responses", f"http://127.0.0.1:{self.server.server_port}/slow-drip")
        with self.assertRaises(AdapterError) as error:
            adapter.complete("m", "s", "p", 10, 0.08)
        self.assertEqual(error.exception.code, "timeout")
        self.assertTrue(error.exception.outcome_unknown)


if __name__ == "__main__":
    unittest.main()
