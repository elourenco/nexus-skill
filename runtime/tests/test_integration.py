"""Real CLI -> router -> Council -> HTTP -> parser, using only a loopback fixture."""

import contextlib
import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from runtime.nexus_runtime.cli import main
from runtime.tests.test_engine import configuration
from runtime.tests.test_council import request, finding, response


class IntegrationTests(unittest.TestCase):
    def test_cli_council_over_each_http_protocol(self):
        for kind in ("openai_responses", "anthropic_messages"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                req = request()
                captured = []

                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *args):
                        pass

                    def do_POST(self):
                        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                        captured.append(body)
                        prompt = body["input"] if kind == "openai_responses" else body["messages"][0]["content"]
                        payload = json.loads(prompt)
                        out = response(req, payload["reviewer_id"], tuple(payload["pillars"]), [finding()])
                        text = json.dumps(out)
                        common = {"model": "fixture-model", "usage": {"input_tokens": 100, "output_tokens": 50}}
                        if kind == "openai_responses":
                            remote = {**common, "status": "completed", "output": [{"type": "message",
                                      "role": "assistant", "status": "completed",
                                      "content": [{"type": "output_text", "text": text}]}]}
                        else:
                            remote = {**common, "stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}
                        raw = json.dumps(remote).encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(raw)))
                        self.end_headers()
                        self.wfile.write(raw)

                server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    data = configuration()
                    data["providers"][0].update(kind=kind, api_key_env=None,
                                                endpoint=f"http://127.0.0.1:{server.server_port}/test")
                    root = Path(directory)
                    config_path, request_path = root / "config.json", root / "request.json"
                    config_path.write_text(json.dumps(data))
                    request_path.write_text(json.dumps(req.__dict__))
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        code = main(["--config", str(config_path), "review", "--request", str(request_path)])
                    report = json.loads(output.getvalue())
                    self.assertEqual(code, 5)
                    self.assertEqual(report["decision"], "CHANGES_REQUESTED")
                    self.assertEqual(report["artifact_id"], req.artifact_id)
                    self.assertTrue(report["findings"][0]["evidence_reference_verified"])
                    self.assertEqual(report["usage"]["attempts"][0]["effective_model"], "fixture-model")
                    self.assertEqual(report["usage"]["attempts"][0]["input_tokens"], 100)
                    self.assertEqual(len(captured), 1)
                    self.assertNotIn("tools", captured[0])
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
