"""Host packaging must survive relocation without duplicate command discovery."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from scripts.package_claude import render_claude_package, write_claude_package
from scripts.validate import validate_skills

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {'start', 'brainstorm', 'plan', 'build', 'debug', 'review'}


def source_files():
    paths = [ROOT / '.claude-plugin/plugin.json', *(ROOT / 'skills').rglob('*')]
    return {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in paths
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


class ClaudePackageTests(unittest.TestCase):
    def test_relocated_package_exposes_only_six_short_commands_and_valid_links(self):
        files = source_files()
        rendered = render_claude_package(files)
        self.assertEqual(rendered, render_claude_package(dict(reversed(list(files.items())))))
        with tempfile.TemporaryDirectory(prefix='nexus command package ') as tmp:
            package = Path(tmp) / 'relocated'
            write_claude_package(rendered, package)
            entries = list((package / 'skills').glob('*/SKILL.md'))
            self.assertEqual({p.parent.name for p in entries}, COMMANDS)
            for entry in entries:
                name = re.search(r'^name: (.+)$', entry.read_text(), re.MULTILINE)[1]
                self.assertEqual(name, entry.parent.name)
            self.assertEqual(validate_skills(package, core_entry='start', reference_only={'nexus'}), [])
            self.assertEqual((package / 'skills/nexus/references/build.md').read_bytes(),
                             files['skills/nexus/references/build.md'])
            self.assertEqual((package / 'skills/nexus/scripts/workflow.py').read_bytes(),
                             files['skills/nexus/scripts/workflow.py'])
            self.assertFalse((package / 'skills/nexus/SKILL.md').exists())
            self.assertNotIn('hooks', json.loads((package / '.claude-plugin/plugin.json').read_text()))

    def test_missing_source_fails_before_creating_a_package(self):
        files = source_files()
        del files['skills/nexus/SKILL.md']
        with self.assertRaisesRegex(ValueError, 'skills/nexus/SKILL.md'):
            render_claude_package(files)

    def test_generated_helpers_run_from_a_separate_consumer_without_writing_state(self):
        with tempfile.TemporaryDirectory(prefix='nexus Claude helpers ') as tmp:
            package = Path(tmp) / 'package'
            consumer = Path(tmp) / 'consumer'
            consumer.mkdir()
            rendered = render_claude_package(source_files())
            write_claude_package(rendered, package)
            for script, args in [('workflow.py', ['template', 'task']), ('hook_engine.py', ['validate'])]:
                result = subprocess.run([sys.executable, str(package / 'skills/nexus/scripts' / script), *args],
                                        cwd=consumer, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(consumer.iterdir()), [])
            write_claude_package(rendered, package)
            self.assertFalse(list(package.rglob('*.pyc')))

    def test_rebuild_removes_obsolete_generated_files_but_rejects_foreign_content(self):
        rendered = render_claude_package(source_files())
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / 'claude'
            write_claude_package({**rendered, 'obsolete.txt': b'old'}, package)
            write_claude_package(rendered, package)
            self.assertFalse((package / 'obsolete.txt').exists())
            foreign = package / 'consumer-state.json'
            foreign.write_text('{"preserve":true}')
            with self.assertRaisesRegex(ValueError, 'unmanaged'):
                write_claude_package(rendered, package)
            self.assertEqual(foreign.read_text(), '{"preserve":true}')


if __name__ == '__main__':
    unittest.main()
