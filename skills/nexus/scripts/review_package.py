#!/usr/bin/env python3
"""Collect local Git review inputs. Does not review, commit, or execute checks."""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MAX_FILE = 2 * 1024 * 1024
MAX_PACKAGE = 16 * 1024 * 1024


class PackageError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()


def git(root, *args, input_data=None):
    # Temporary output avoids retaining an unbounded subprocess result in RAM.
    # Git configuration cannot install an external diff/textconv through this call.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', LC_ALL='C')
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            process = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args], env=env,
                                     stdout=out, stderr=err, input=input_data,
                                     **({'stdin': subprocess.DEVNULL} if input_data is None else {}), timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PackageError('Git unavailable or timed out') from exc
        if process.returncode:
            raise PackageError('Git rejected the repository or revision')
        out.seek(0)
        value = out.read(MAX_PACKAGE + 1)
    if len(value) > MAX_PACKAGE:
        raise PackageError('Git output exceeds package limit')
    return value


def revision(root, ref):
    if not ref or ref.startswith('-') or '\x00' in ref:
        raise PackageError('Invalid revision')
    return git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()


def read_file(path):
    if path.is_symlink() or not path.is_file():
        raise PackageError('Only regular, non-symlink input files are supported')
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise PackageError('Input file exceeds 2 MiB limit')
    return data


def capture(root, base, head, include_untracked):
    current = revision(root, 'HEAD')
    if not head:
        tracked = git(root, 'ls-files', '--cached', '-z')
        attributes = git(root, 'check-attr', '-z', '--stdin', 'filter', input_data=tracked).split(b'\0')
        if any(value not in (b'unspecified', b'unset') for value in attributes[2::3]):
            raise PackageError('Worktree filters are unsupported; review an explicit --head commit instead')
    target = [head] if head else []
    diff = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames',
               '--submodule=short', '--full-index', base, *target, '--')
    untracked = [] if head else [os.fsdecode(x) for x in
        git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if x]
    omitted = untracked if not include_untracked else []
    files = []
    if include_untracked:
        for name in untracked:
            path = root / name
            if not path.resolve().is_relative_to(root):
                raise PackageError('Untracked file escapes workspace')
            data = read_file(path)
            files.append({'path': name, 'sha256': sha(data),
                          'executable': bool(path.stat().st_mode & 0o111)})
            # Filenames are escaped to keep patch headers unambiguous.
            label = json.dumps(name, ensure_ascii=True)
            try:
                content = data.decode('utf-8')
                if '\0' in content:
                    raise UnicodeError()
                lines = difflib.unified_diff([], content.splitlines(keepends=True),
                                            fromfile='/dev/null', tofile=label)
                diff += ''.join(line if line.endswith('\n') else
                                line + '\n\\ No newline at end of file\n'
                                for line in lines).encode()
            except UnicodeError:
                diff += ('\nBinary untracked file ' + label + ' (digest in manifest)\n').encode()
            if len(diff) > MAX_PACKAGE:
                raise PackageError('Diff exceeds package limit')
    # Commit mode has a fixed target; unrelated local changes do not change its identity.
    return {'head': head or current, 'diff_sha256': sha(diff), 'untracked': files,
            'omitted_untracked': omitted}, diff


def collect(workspace, base, output, head=None, include_untracked=False,
            briefs=(), evidence=(), gaps=()):
    root = Path(workspace).resolve()
    repository = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve()
    if root != repository:
        raise PackageError('Workspace must be the Git repository root')
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise PackageError('Output must not already exist')
    # Keep generated artifacts out of the snapshot and the installed package.
    if output.resolve().is_relative_to(root):
        raise PackageError('Output must be outside the reviewed workspace')
    if not output.parent.is_dir():
        raise PackageError('Output parent must already exist')
    base_sha = revision(root, base)
    head_sha = revision(root, head) if head else None
    if head_sha and include_untracked:
        raise PackageError('Untracked files belong to worktree mode, not a commit target')
    git(root, 'merge-base', '--is-ancestor', base_sha, head_sha or 'HEAD')
    state, diff = capture(root, base_sha, head_sha, include_untracked)
    attachments, contents = [], {}
    total = len(diff)
    for kind, paths in (('brief', briefs), ('evidence', evidence)):
        for path in paths:
            data = read_file(Path(path))
            total += len(data)
            if total > MAX_PACKAGE:
                raise PackageError('Package exceeds 16 MiB limit')
            name = f'{kind}-{len(attachments) + 1}.txt'
            attachments.append({'kind': kind, 'file': name, 'sha256': sha(data)})
            contents[name] = data
    second, _ = capture(root, base_sha, head_sha, include_untracked)
    if second != state:
        raise PackageError('Workspace changed during capture; reconcile and retry')
    for item, path in zip(attachments, [*briefs, *evidence]):
        if sha(read_file(Path(path))) != item['sha256']:
            raise PackageError('Attachment changed during capture')
    manifest = {'schema_version': 1, 'mode': 'commit' if head_sha else 'worktree',
                'base': base_sha, **state, 'attachments': attachments, 'gaps': list(gaps),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'limits': ['Capture is not a filesystem transaction; stop writers before review.',
                           'Ignored files and submodule contents are not collected.',
                           'Evidence attachments are caller data, not authenticated test results.']}
    manifest['artifact_id'] = sha(canonical(manifest))
    # Exclusive directory creation; manifest written last is the completion marker.
    output.mkdir(mode=0o700)
    try:
        (output / 'changes.diff').write_bytes(diff)
        for name, data in contents.items():
            (output / name).write_bytes(data)
        (output / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
    except BaseException:
        shutil.rmtree(output)
        raise
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--base', required=True)
    parser.add_argument('--head')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-untracked', action='store_true')
    parser.add_argument('--brief', type=Path, action='append', default=[])
    parser.add_argument('--evidence', type=Path, action='append', default=[])
    parser.add_argument('--gap', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        result = collect(args.workspace, args.base, args.output, args.head,
                         args.include_untracked, args.brief, args.evidence, args.gap)
        print(json.dumps({'artifact_id': result['artifact_id'], 'output': str(args.output)}))
        return 0
    except (PackageError, OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
