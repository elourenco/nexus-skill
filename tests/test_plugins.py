"""Package contracts and real helper execution from an immutable installed copy."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate import validate

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ('.claude-plugin/plugin.json', '.codex-plugin/plugin.json')
CATALOGS = ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json')


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        entry = self.root / 'skills/nexus/SKILL.md'
        entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: nexus\ndescription: Engineering workflow\n---\n')
        for path in MANIFESTS:
            self.write(path, {'name': 'nexus', 'version': '0.1.0',
                             'description': 'Engineering workflow', 'skills': './skills/'})
        self.write(CATALOGS[0], {'name': 'nexus-local', 'owner': {'name': 'NEXUS'},
                                'plugins': [{'name': 'nexus', 'source': './'}]})
        self.write(CATALOGS[1], {'name': 'nexus-local', 'plugins': [{
            'name': 'nexus', 'source': {'source': 'local', 'path': './'},
            'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
            'category': 'Developer Tools'}]})

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))

    def test_valid_shared_package(self):
        self.assertEqual(validate(self.root), [])

    def test_published_source_is_accepted_only_for_the_official_release_channel(self):
        for path in CATALOGS:
            catalog = json.loads((self.root / path).read_text())
            catalog['plugins'][0]['source'] = {'source': 'url',
                'url': 'https://github.com/elourenco/nexus-skill.git', 'ref': 'plugins'}
            self.write(path, catalog)
        self.assertEqual(validate(self.root), [])
        for path in CATALOGS:
            catalog = json.loads((self.root / path).read_text())
            catalog['plugins'][0]['source']['ref'] = 'main'
            self.write(path, catalog)
            self.assertTrue(validate(self.root))

    def test_claude_listing_fields_are_host_specific(self):
        listing = {
            'displayName': 'NEXUS',
            'documentationUrl': 'https://github.com/elourenco/nexus-skill#readme',
            'supportUrl': 'https://github.com/elourenco/nexus-skill/issues',
        }
        for path in MANIFESTS:
            with self.subTest(path=path):
                original = json.loads((self.root / path).read_text())
                self.write(path, {**original, **listing})
                errors = validate(self.root)
                if path.startswith('.claude-plugin/'):
                    self.assertEqual(errors, [])
                else:
                    self.assertTrue(any('unsupported fields' in e for e in errors), errors)
                self.write(path, original)

    def test_missing_manifest_or_catalog_fails(self):
        for path in MANIFESTS + CATALOGS:
            with self.subTest(path=path):
                target = self.root / path
                saved = target.read_bytes()
                target.unlink()
                self.assertTrue(validate(self.root), path)
                target.write_bytes(saved)

    def test_malformed_manifest_fails_without_exception(self):
        target = self.root / MANIFESTS[0]
        for value in ('{', '[]', 'null'):
            with self.subTest(value=value):
                target.write_text(value)
                self.assertTrue(validate(self.root))

    def test_version_drift_and_invalid_skill_location_fail(self):
        target = self.root / MANIFESTS[1]
        original = json.loads(target.read_text())
        for change in ({'version': '0.2.0'}, {'version': 'latest'},
                       {'skills': '../skills/'}, {'skills': './missing/'}):
            with self.subTest(change=change):
                self.write(MANIFESTS[1], {**original, **change})
                self.assertTrue(validate(self.root))

    def test_wrong_catalog_source_or_identity_fails(self):
        original = json.loads((self.root / CATALOGS[1]).read_text())
        for change in ({'name': 'different'}, {'source': {'source': 'local', 'path': '../'}},
                       {'source': {'source': 'url', 'url': 'https://example.invalid/plugin'}}):
            with self.subTest(change=change):
                value = {**original, 'plugins': [{**original['plugins'][0], **change}]}
                self.write(CATALOGS[1], value)
                self.assertTrue(validate(self.root))

    def test_automatic_components_require_a_new_scope(self):
        target = self.root / MANIFESTS[0]
        original = json.loads(target.read_text())
        self.write(MANIFESTS[0], {**original, 'hooks': './skills/nexus/assets/hooks.json'})
        self.assertTrue(validate(self.root))
        self.write(MANIFESTS[0], original)
        for path in ('hooks/hooks.json', '.mcp.json', '.app.json', 'agents/reviewer.md'):
            with self.subTest(path=path):
                target = self.root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{}')
                self.assertTrue(validate(self.root))
                target.unlink()


@unittest.skipUnless(os.name == 'posix', 'Optional helpers require POSIX')
class InstalledPackageTests(unittest.TestCase):
    def test_relocated_read_only_package_and_replacement_preserve_consumer_state(self):
        with tempfile.TemporaryDirectory(prefix='nexus plugin ') as temporary:
            base = Path(temporary)
            consumer = base / 'consumer workspace'
            consumer.mkdir()
            state = consumer / '.nexus/local/workflow.json'
            memory = consumer / '.nexus/local/memory'
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            states = []
            packages = []
            try:
                for version in ('first install', 'replacement install'):
                    package = base / version
                    packages.append(package)
                    shutil.copytree(ROOT / 'skills', package / 'skills',
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    for path in sorted(package.rglob('*'), reverse=True):
                        path.chmod(0o555 if path.is_dir() else 0o444)
                    package.chmod(0o555)
                    before = {str(p.relative_to(package)): p.read_bytes()
                              for p in package.rglob('*') if p.is_file()}

                    def call(script, *args):
                        result = subprocess.run(
                            [sys.executable, '-B', str(package / 'skills/nexus/scripts' / script), *args],
                            cwd=consumer, env=env, capture_output=True, text=True, timeout=15)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        return result.stdout

                    self.assertIn('#', call('workflow.py', 'template', 'task'))
                    self.assertEqual(json.loads(call('hook_engine.py', 'validate'))['status'], 'valid')
                    if not states:
                        call('workflow.py', '--state', str(state), 'init', '--workspace', str(consumer))
                        call('memory.py', '--root', str(memory), '--scope', 'project:synthetic',
                             'init', '--allow-write')
                    workflow = json.loads(call('workflow.py', '--state', str(state), 'show', '--format', 'json'))
                    states.append(workflow)
                    call('memory.py', '--root', str(memory), '--scope', 'project:synthetic',
                         'pack', '--task', 'Synthetic relocation check')
                    after = {str(p.relative_to(package)): p.read_bytes()
                             for p in package.rglob('*') if p.is_file()}
                    self.assertEqual(before, after)
                self.assertEqual(states[0], states[1])
                self.assertTrue(state.is_file())
                self.assertTrue(memory.is_dir())
            finally:
                # TemporaryDirectory must be able to remove the simulated read-only cache.
                for package in packages:
                    if package.exists():
                        package.chmod(0o755)
                        for path in package.rglob('*'):
                            path.chmod(0o755 if path.is_dir() else 0o644)


if __name__ == '__main__':
    unittest.main()
