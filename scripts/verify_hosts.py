#!/usr/bin/env python3
"""Read native skill discovery in temporary host profiles; never run inference."""
import argparse
import json
import os
import re
from pathlib import Path
import selectors
import shutil
import subprocess
import tempfile
import time

if __package__:
    from .package_claude import build_claude_package
else:
    from package_claude import build_claude_package

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'nexus', 'nexus-brainstorm', 'nexus-plan', 'nexus-build', 'nexus-debug', 'nexus-review'}
EXPECTED_CLAUDE = {'start', 'brainstorm', 'plan', 'build', 'debug', 'review'}


def discover_skills(executable, cwd, env, response_timeout=30, cleanup_timeout=2,
                    max_response_bytes=1024 * 1024):
    """Bound both protocol reads and process cleanup, including unterminated lines."""
    process = subprocess.Popen([executable, 'app-server', '--stdio'], cwd=cwd, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, bufsize=0)
    selector = selectors.DefaultSelector()
    buffer = bytearray()
    try:
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ)

        def receive(request_id):
            deadline = time.monotonic() + response_timeout
            received = len(buffer)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError('app-server discovery timed out')
                if b'\n' in buffer:
                    line, _, rest = buffer.partition(b'\n')
                    buffer[:] = rest
                    response = json.loads(line)
                    if not isinstance(response, dict):
                        raise ValueError('app-server response must be an object')
                    if response.get('id') == request_id:
                        if 'error' in response:
                            raise ValueError(f"app-server returned error: {response['error']}")
                        if not isinstance(response.get('result'), dict):
                            raise ValueError('app-server result must be an object')
                        return response['result']
                    continue
                if not selector.select(timeout=remaining):
                    raise RuntimeError('app-server discovery timed out')
                try:
                    chunk = os.read(process.stdout.fileno(), min(65536, max_response_bytes + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    raise RuntimeError('app-server closed before response')
                received += len(chunk)
                if received > max_response_bytes:
                    raise ValueError('app-server response exceeds byte limit')
                buffer.extend(chunk)

        requests = [
            {'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'nexus-validation', 'version': '1'}}},
            {'method': 'initialized', 'params': {}},
            {'id': 2, 'method': 'skills/list', 'params': {'cwds': [str(cwd)], 'forceReload': True}}]
        result = None
        for request in requests:
            process.stdin.write((json.dumps(request) + '\n').encode())
            if 'id' in request:
                result = receive(request['id'])
        if not isinstance(result.get('data'), list):
            raise ValueError('skills/list data must be an array')
        skills = []
        for group in result['data']:
            if not isinstance(group, dict) or not isinstance(group.get('skills'), list):
                raise ValueError('skills/list group must contain skills array')
            for skill in group['skills']:
                if not isinstance(skill, dict):
                    raise ValueError('skill must be an object')
                if skill.get('pluginId') == 'nexus@nexus-local':
                    if not isinstance(skill.get('name'), str) or type(skill.get('enabled')) is not bool:
                        raise ValueError('plugin skill requires name and enabled flag')
                    skills.append(skill)
        return skills
    finally:
        selector.close()
        try:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=cleanup_timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=cleanup_timeout)
        finally:
            process.stdin.close()
            process.stdout.close()


def prepare_local_package(destination):
    """Copy the candidate into a new directory with explicitly local catalogs."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for directory in ('skills', '.claude-plugin', '.codex-plugin', '.agents/plugins'):
        shutil.copytree(ROOT / directory, destination / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    build_claude_package(destination, destination / 'build/claude')
    for path, source in [('.claude-plugin/marketplace.json', './build/claude'),
                         ('.agents/plugins/marketplace.json', {'source': 'local', 'path': './'})]:
        target = destination / path
        catalog = json.loads(target.read_text())
        for entry in catalog['plugins']:
            entry['source'] = source
        target.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')


def verify(codex, claude):
    receipts = []
    with tempfile.TemporaryDirectory(prefix='nexus-host-discovery-') as tmp:
        base = Path(tmp)
        package = base / 'candidate'
        prepare_local_package(package)
        consumer = base / 'consumer'
        consumer.mkdir()
        # Profiles are empty. Do not copy authentication or global configuration.
        env = {**os.environ, 'CODEX_HOME': str(base / 'codex'),
               'CLAUDE_CONFIG_DIR': str(base / 'claude'), 'NO_COLOR': '1'}
        Path(env['CODEX_HOME']).mkdir()
        Path(env['CLAUDE_CONFIG_DIR']).mkdir()

        def call(host, args):
            started = time.monotonic()
            result = subprocess.run([host, *args], cwd=consumer, env=env,
                                    capture_output=True, text=True, timeout=60)
            receipts.append({'command': [host, *args], 'returncode': result.returncode,
                             'stdout': result.stdout, 'stderr': result.stderr,
                             'latency_ms': round((time.monotonic() - started) * 1000)})
            if result.returncode:
                raise RuntimeError(f'host command failed: {args}')
            return result.stdout

        result = {'schema_version': 2, 'package_version': json.loads((ROOT / '.codex-plugin/plugin.json').read_text())['version'],
                  'expected_entries': {'codex': sorted(EXPECTED), 'claude': sorted(EXPECTED_CLAUDE)}, 'inference_executed': False,
                  'profiles': 'isolated temporary directories; no credentials copied', 'commands': receipts}
        for name, executable in [('codex', codex), ('claude', claude)]:
            try:
                call(executable, ['--version'])
                if name == 'codex':
                    call(executable, ['plugin', 'marketplace', 'add', str(package), '--json'])
                    call(executable, ['plugin', 'add', 'nexus@nexus-local', '--json'])
                    call(executable, ['plugin', 'list', '--json'])
                    skills = discover_skills(executable, consumer, env)
                    names = {skill['name'].split(':')[-1] for skill in skills}
                    result[name] = {'status': 'pass' if names == EXPECTED and len(skills) == len(EXPECTED) and all(s['enabled'] for s in skills) else 'fail',
                                    'entries': sorted(names), 'skills': skills}
                else:
                    call(executable, ['plugin', 'validate', str(package / 'build/claude/.claude-plugin/plugin.json'), '--strict', '--json'])
                    call(executable, ['plugin', 'marketplace', 'add', str(package), '--json'])
                    call(executable, ['plugin', 'install', 'nexus@nexus-local', '--json'])
                    installed = json.loads(call(executable, ['plugin', 'list', '--json']))
                    if not isinstance(installed, list) or any(not isinstance(plugin, dict) for plugin in installed):
                        raise ValueError('Claude installed plugin list must be an array of objects')
                    matches = [p for p in installed if p.get('id') == 'nexus@nexus-local']
                    enabled = len(matches) == 1 and matches[0].get('enabled') is True
                    inventory = call(executable, ['plugin', 'details', 'nexus@nexus-local'])
                    # Parse an exact native inventory field, not response keywords or quality.
                    match = re.search(r'^\s*Skills \((\d+)\)\s+(.+)$', inventory, re.MULTILINE)
                    names = {n.strip() for n in match[2].split(',')} if match else set()
                    result[name] = {'status': ('pass' if names == EXPECTED_CLAUDE and int(match[1]) == 6 and enabled else
                                                'fail' if match else 'inconclusive'),
                                    'entries': sorted(names), 'enabled': enabled, 'native_inventory': inventory}
            except (OSError, RuntimeError, subprocess.TimeoutExpired, KeyError, ValueError, TypeError) as error:
                result[name] = {'status': 'inconclusive', 'error': str(error)}
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', default=shutil.which('codex'))
    parser.add_argument('--claude', default=shutil.which('claude'))
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument('--output', type=Path)
    output.add_argument('--prepare-local', type=Path,
                        help='Copy this checkout to a new local development package directory')
    args = parser.parse_args(argv)
    if args.prepare_local:
        prepare_local_package(args.prepare_local)
        print(args.prepare_local.resolve())
        return
    result = verify(args.codex, args.claude)
    with args.output.open('x') as output:
        json.dump(result, output, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
