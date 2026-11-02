#!/usr/bin/env python3
"""Publish one ordered, retry-safe GitHub release for a validated primary-branch push."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

VERSION = re.compile(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')
WORKFLOW = '.github/workflows/release.yml'


def git(root, *args):
    return subprocess.check_output(
        ['git', *args], cwd=root, text=True, stderr=subprocess.PIPE, timeout=30).strip()


def git_succeeds(root, *args):
    result = subprocess.run(['git', *args], cwd=root, capture_output=True, timeout=30)
    if result.returncode not in (0, 1):
        raise RuntimeError(f'Git failed while checking {args[0]}')
    return result.returncode == 0


class GitHub:
    def __init__(self, repository, token):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid GITHUB_REPOSITORY')
        self.base = f'https://api.github.com/repos/{repository}/'
        self.token = token

    def request(self, method, path, data=None):
        request = Request(self.base + path, method=method, headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.token}',
            'X-GitHub-Api-Version': '2022-11-28',
            'Content-Type': 'application/json',
            'User-Agent': 'nexus-release',
        }, data=json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            exc.close()
            if method == 'GET' and path.startswith('releases/tags/') and exc.code == 404:
                return None
            # Never retry a write whose outcome might be unknown. Rerun reconciles tags/releases.
            raise RuntimeError(f'GitHub {method} {path} failed: HTTP {exc.code}') from None


def published(release):
    return release is not None and not release['draft'] and not release['prerelease']


def publish(root, api, sha, before, recover_from=None):
    for value in (sha, before):
        if not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Expected full commit SHA')
        git(root, 'rev-parse', '--verify', f'{value}^{{commit}}')
    if not git_succeeds(root, 'merge-base', '--is-ancestor', before, sha):
        raise RuntimeError('Previous push must be an ancestor; force pushes are unsupported')

    tags = []
    for tag in git(root, 'tag', '--list', 'v*').splitlines():
        match = VERSION.fullmatch(tag)
        if match:
            tags.append((tuple(map(int, match.groups())), tag,
                         git(root, 'rev-parse', f'{tag}^{{commit}}')))
    tags.sort()
    current = [entry for entry in tags if entry[2] == sha]
    if len(current) > 1:
        raise RuntimeError('Multiple release tags point at this commit')
    if current:
        existing = api.request('GET', f'releases/tags/{current[0][1]}')
        if published(existing):
            print(f'Already published: {current[0][1]}')
            return existing
        if existing is not None:
            raise RuntimeError('Existing draft/prerelease requires manual resolution')

    previous = [entry for entry in tags if entry[2] != sha]
    latest = previous[-1] if previous else None
    if recover_from is not None and recover_from != (latest[1] if latest else 'initial'):
        raise RuntimeError('Recovery base changed; inspect releases before dispatching again')
    if latest:
        if not git_succeeds(root, 'merge-base', '--is-ancestor', latest[2], sha):
            raise RuntimeError('Latest version must be an ancestor of the release commit')
        if recover_from is None and latest[2] != before:
            raise RuntimeError('Release the previous push first, then rerun this workflow')
        if not published(api.request('GET', f'releases/tags/{latest[1]}')):
            raise RuntimeError('Recover the previous release first, then rerun this workflow')
    else:
        # Bootstrap only the push that installs this workflow. Later pushes cannot
        # silently absorb a failed first release or an event queued out of order.
        files = git(root, 'ls-tree', '--name-only', before, '--', WORKFLOW)
        if recover_from is None and files:
            raise RuntimeError('Release the previous push first, then rerun this workflow')

    if current:
        tag = current[0][1]
        if latest and current[0][0] <= latest[0]:
            raise RuntimeError('Existing tag does not advance the previous version')
    elif latest:
        major, minor, patch = latest[0]
        tag = f'v{major}.{minor}.{patch + 1}'
    else:
        manifest = json.loads(git(root, 'show', f'{sha}:.claude-plugin/plugin.json'))
        tag = f"v{manifest['version']}"
        if not VERSION.fullmatch(tag):
            raise ValueError('Invalid initial version in plugin manifest')

    note_request = {'tag_name': tag, 'target_commitish': sha,
                    'configuration_file_path': '.github/release.yml'}
    if latest:
        note_request['previous_tag_name'] = latest[1]
    notes = api.request('POST', 'releases/generate-notes', note_request)
    if not notes.get('body', '').strip():
        raise RuntimeError('GitHub returned empty release notes')
    if not current:
        api.request('POST', 'git/refs', {'ref': f'refs/tags/{tag}', 'sha': sha})
    release = api.request('POST', 'releases', {
        'tag_name': tag, 'target_commitish': sha, 'name': tag,
        'body': notes['body'], 'draft': False, 'prerelease': False,
        'make_latest': 'true',
    })
    print(f"Published {tag}: {release['html_url']}")
    return release


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    branch = event['repository']['default_branch']
    event_name = os.environ['GITHUB_EVENT_NAME']
    if (event_name not in ('push', 'workflow_dispatch') or branch not in ('main', 'master')
            or os.environ['GITHUB_REF'] != f'refs/heads/{branch}'
            or event.get('deleted') or event.get('forced')):
        raise RuntimeError('Releases require the default main/master branch without force pushes')
    root = Path(__file__).resolve().parents[1]
    sha = os.environ['GITHUB_SHA']
    if git(root, 'rev-parse', 'HEAD') != sha:
        raise RuntimeError('Checkout does not match the validated event commit')
    recover_from = None
    if event_name == 'workflow_dispatch':
        recover_from = event['inputs']['previous_tag']
        if recover_from != 'initial' and not VERSION.fullmatch(recover_from):
            raise ValueError('Recovery requires the previous vX.Y.Z tag or initial')
    publish(root, GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GH_TOKEN']),
            sha, event['before'] if event_name == 'push' else sha, recover_from)


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'Release failed: {exc}', file=sys.stderr)
        sys.exit(1)
