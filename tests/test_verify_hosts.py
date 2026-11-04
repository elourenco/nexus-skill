"""Native discovery must remain bounded on a faulty local host protocol."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts.verify_hosts import EXPECTED, discover_skills, main, verify
import scripts.verify_hosts as host_verifier


class HostDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def host(self, body):
        path = self.root / 'fake-host'
        path.write_text(f'#!{sys.executable}\n' + body)
        path.chmod(0o755)
        return str(path)

    def test_partial_line_times_out_and_kills_ignoring_process(self):
        pidfile = self.root / 'pid'
        host = self.host('import os, signal, sys, time\n'
                         'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
                         f'open({str(pidfile)!r}, "w").write(str(os.getpid()))\n'
                         'sys.stdout.write("{"); sys.stdout.flush()\n'
                         'time.sleep(30)\n')
        started = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, 'timed out'):
            discover_skills(host, self.root, os.environ, response_timeout=.5, cleanup_timeout=.1)
        self.assertLess(time.monotonic() - started, 3)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)

    def test_malformed_json_and_schema_are_inconclusive(self):
        for line in ('invalid', '[]', '{"id":1,"result":[]}'):
            with self.subTest(line=line):
                host = self.host(f'import sys\nprint({line!r}, flush=True)\nsys.stdin.read()\n')
                with self.assertRaises(ValueError):
                    discover_skills(host, self.root, os.environ, response_timeout=.5)
                with patch('scripts.verify_hosts.discover_skills', side_effect=ValueError('invalid protocol')):
                    result = verify(host, host)
                self.assertEqual(result['codex']['status'], 'inconclusive')

    def test_byte_limit_prevents_unterminated_output_flood(self):
        host = self.host('import sys\nsys.stdout.write("x" * 4096); sys.stdout.flush()\nsys.stdin.read()\n')
        with self.assertRaisesRegex(ValueError, 'byte limit'):
            discover_skills(host, self.root, os.environ, response_timeout=.5, max_response_bytes=1024)

    def test_disabled_plugins_cannot_pass(self):
        host = self.host('import json, sys\n'
                         'if sys.argv[1:] == ["plugin", "list", "--json"]:\n'
                         ' print(json.dumps([{"id":"nexus@nexus-local","enabled":False}]))\n'
                         'elif sys.argv[1:3] == ["plugin", "details"]:\n'
                         f' print("  Skills (6)  {", ".join(sorted(EXPECTED))}")\n'
                         'else:\n print("{}")\n')
        skills = [{'name': f'nexus:{name}', 'pluginId': 'nexus@nexus-local', 'enabled': False}
                  for name in EXPECTED]
        with patch('scripts.verify_hosts.discover_skills', return_value=skills):
            result = verify(host, host)
        self.assertEqual(result['codex']['status'], 'fail')
        self.assertEqual(result['claude']['status'], 'fail')

    def test_crash_does_not_publish_empty_output(self):
        output = self.root / 'result.json'
        with patch('scripts.verify_hosts.verify', side_effect=RuntimeError('unexpected crash')):
            with self.assertRaises(RuntimeError):
                main(['--output', str(output)])
        self.assertFalse(output.exists())

    def test_checkout_package_installs_candidate_bytes_without_remote_catalog_redirects(self):
        destination = self.root / 'candidate'
        host_verifier.prepare_local_package(destination)
        for path, expected in [('.claude-plugin/marketplace.json', './'),
                               ('.agents/plugins/marketplace.json', {'source': 'local', 'path': './'})]:
            catalog = json.loads((destination / path).read_text())
            self.assertEqual(catalog['plugins'][0]['source'], expected)
        candidate = host_verifier.ROOT / 'skills/nexus/SKILL.md'
        self.assertEqual((destination / 'skills/nexus/SKILL.md').read_bytes(), candidate.read_bytes())
        with self.assertRaises(FileExistsError):
            host_verifier.prepare_local_package(destination)

    def test_valid_fragmented_protocol_and_bad_skill_schema(self):
        for skills in ([{'name': 'nexus:nexus', 'pluginId': 'nexus@nexus-local', 'enabled': True}], [None]):
            with self.subTest(skills=skills):
                host = self.host('import json, sys, time\n'
                                 f'skills = {skills!r}\n'
                                 'for line in sys.stdin:\n'
                                 ' request = json.loads(line)\n'
                                 ' if "id" not in request: continue\n'
                                 ' result = {} if request["id"] == 1 else {"data":[{"skills": skills}]}\n'
                                 ' response = json.dumps({"id":request["id"],"result":result}) + "\\n"\n'
                                 ' sys.stdout.write(response[:3]); sys.stdout.flush(); time.sleep(.01)\n'
                                 ' sys.stdout.write(response[3:]); sys.stdout.flush()\n')
                if skills == [None]:
                    with self.assertRaises(ValueError):
                        discover_skills(host, self.root, os.environ, response_timeout=.5)
                else:
                    self.assertEqual(discover_skills(host, self.root, os.environ, response_timeout=.5), skills)


if __name__ == '__main__':
    unittest.main()
