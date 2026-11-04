#!/usr/bin/env python3
"""Build Claude's six short entrypoints from the portable skills; no inference."""
import argparse
from importlib.util import source_from_cache
import json
import posixpath
from pathlib import Path, PurePosixPath
import re

ENTRY_NAMES = {
    'nexus': 'start', 'nexus-brainstorm': 'brainstorm', 'nexus-plan': 'plan',
    'nexus-build': 'build', 'nexus-debug': 'debug', 'nexus-review': 'review',
}
MARKER = '.nexus-claude-package.json'


def render_claude_package(files: dict[str, bytes]) -> dict[str, bytes]:
    """Render from a filesystem or immutable Git snapshot with identical results."""
    required = ['.claude-plugin/plugin.json', *(f'skills/{name}/SKILL.md' for name in ENTRY_NAMES)]
    for path in required:
        if path not in files:
            raise ValueError(f'Missing package source: {path}')
    rendered = {'.claude-plugin/plugin.json': files['.claude-plugin/plugin.json']}
    for path, content in files.items():
        if path.startswith('skills/nexus/') and path not in {
                'skills/nexus/SKILL.md', 'skills/nexus/agents/openai.yaml'}:
            rendered[path] = content
    for source, command in ENTRY_NAMES.items():
        text = files[f'skills/{source}/SKILL.md'].decode('utf-8')
        text, count = re.subn(r'\A---\nname: [^\n]+', f'---\nname: {command}', text, count=1)
        if count != 1:
            raise ValueError(f'Invalid package entry: {source}')
        if source == 'nexus':
            text = re.sub(r'(?<=\]\()(references|assets|scripts)/', r'../nexus/\1/', text)
        rendered[f'skills/{command}/SKILL.md'] = text.encode('utf-8')
    # References back to the router must follow its generated entrypoint too.
    for path, content in list(rendered.items()):
        if not path.endswith('.md'):
            continue
        def router_link(match):
            target, separator, anchor = match[1].partition('#')
            if posixpath.normpath(posixpath.join(posixpath.dirname(path), target)) == 'skills/nexus/SKILL.md':
                target = posixpath.relpath('skills/start/SKILL.md', posixpath.dirname(path))
            return '](' + target + separator + anchor + ')'
        rendered[path] = re.sub(r'\]\(([^)\n]+)\)', router_link, content.decode('utf-8')).encode('utf-8')
    return rendered


def write_claude_package(files: dict[str, bytes], output: Path) -> None:
    """Replace only our generated files; refuse symlinks and unmanaged content."""
    output = Path(output)
    for path in files:
        relative = PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts or str(relative) != path or path == MARKER:
            raise ValueError(f'Invalid generated path: {path}')
    if output.is_symlink() or any(p.is_symlink() for p in output.rglob('*')):
        raise ValueError('Package output must not contain symlinks')
    previous = set()
    marker = output / MARKER
    if marker.exists():
        previous = set(json.loads(marker.read_text())['files'])
    existing = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    bytecode = set()
    for path in existing - previous - {MARKER}:
        if not path.endswith('.pyc'):
            continue
        try:
            source = Path(source_from_cache(str(output / path))).relative_to(output).as_posix()
        except ValueError:
            continue
        if source in previous:
            bytecode.add(path)
    if existing - previous - bytecode - {MARKER}:
        raise ValueError('Package output contains unmanaged files; choose another directory')
    # Validate prior paths too before deleting any obsolete generated files.
    for path in previous:
        if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
            raise ValueError('Invalid previous package inventory')
    for path in (previous - files.keys()) | bytecode:
        (output / path).unlink(missing_ok=True)
    for path, content in sorted(files.items()):
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    marker.write_text(json.dumps({'schema_version': 1, 'files': sorted(files)}, indent=2) + '\n')


def build_claude_package(root: Path, output: Path) -> Path:
    paths = [root / '.claude-plugin/plugin.json', *(root / 'skills').rglob('*')]
    files = {}
    for path in paths:
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Package source escapes repository: {path}')
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    write_claude_package(render_claude_package(files), output)
    return output


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=root / 'build/claude')
    args = parser.parse_args()
    print(build_claude_package(root, args.output))


if __name__ == '__main__':
    main()
