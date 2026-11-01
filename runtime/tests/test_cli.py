import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from runtime.nexus_runtime.cli import main
from runtime.tests.test_engine import configuration


class CLITests(unittest.TestCase):
    def invoke(self, command, request=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = configuration()
            config["providers"][0]["enabled"] = False
            (root / "config.json").write_text(json.dumps(config))
            args = ["--config", str(root / "config.json"), command]
            if request is not None:
                (root / "request.json").write_text(json.dumps(request))
                args += ["--task", str(root / "request.json")]
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(args)
            return exit_code, json.loads(stdout.getvalue())

    def test_inspect_does_not_claim_authentication(self):
        code, output = self.invoke("inspect")
        self.assertEqual(code, 0)
        self.assertEqual(output["execution"], "text_only")
        self.assertFalse(output["providers"][0]["authenticated_execution_verified"])

    def test_unavailable_provider_returns_blocked_exit_code(self):
        code, output = self.invoke("run", {"task_id": "x", "agent": "planner", "prompt": "plan"})
        self.assertEqual(code, 3)
        self.assertEqual(output["result"]["status"], "blocked")
        self.assertEqual(output["usage"]["attempts"], [])

    def test_bad_task_is_sanitized_and_never_executed(self):
        code, output = self.invoke("run", {"task_id": "x", "agent": "planner", "prompt": "secret", "shell": "unsafe"})
        self.assertEqual(code, 2)
        self.assertEqual(output["error"], "invalid_input_or_configuration")
        self.assertNotIn("secret", json.dumps(output))

    def test_route_is_read_only(self):
        code, output = self.invoke("route", {"task_id": "x", "agent": "planner", "prompt": "plan"})
        self.assertEqual(code, 3)
        self.assertEqual(output["candidates"], [])


if __name__ == "__main__":
    unittest.main()
