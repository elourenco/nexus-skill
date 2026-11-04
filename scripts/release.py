#!/usr/bin/env python3
"""Publish one ordered, retry-safe GitHub release for a validated primary-branch push."""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import io
import tarfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

if __package__:
    from .package_claude import render_claude_package
else:
    from package_claude import render_claude_package

VERSION = re.compile(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')
WORKFLOW = '.github/workflows/release.yml'
DISTRIBUTION_REF = 'refs/heads/plugins'
PROVENANCE = '.nexus-release.json'
MANIFESTS = ('.claude-plugin/plugin.json', '.codex-plugin/plugin.json')
CATALOGS = ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json')
PUBLISHED_SOURCE = {'source': 'url', 'url': 'https://github.com/elourenco/nexus-skill.git',
                    'ref': 'plugins'}
CLAUDE_PUBLISHED_SOURCE = {**PUBLISHED_SOURCE, 'source': 'git-subdir', 'path': 'build/claude'}


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
            if (method == 'GET' and exc.code == 404
                    and (path.startswith('releases/tags/') or path == 'git/ref/heads/plugins'
                         or path.startswith('git/ref/tags/plugin-v'))):
                return None
            # Never retry a write whose outcome might be unknown. Rerun reconciles tags/releases.
            raise RuntimeError(f'GitHub {method} {path} failed: HTTP {exc.code}') from None


def published(release):
    return release is not None and not release['draft'] and not release['prerelease']


def source_manifests(root, sha):
    manifests = {path: json.loads(git(root, 'show', f'{sha}:{path}')) for path in MANIFESTS}
    versions = {manifest.get('version') for manifest in manifests.values()}
    if len(versions) != 1 or not all(isinstance(v, str) and VERSION.fullmatch('v' + v) for v in versions):
        raise ValueError('Plugin manifest versions must agree and use numeric major.minor.patch')
    if any(m.get('name') != 'nexus' or m.get('skills') != './skills/' for m in manifests.values()):
        raise ValueError('Distribution requires the shared nexus skills-only package')
    return manifests


def distribution_snapshot(root, sha, tag):
    """Render versions and Claude's package from the immutable source commit."""
    if not VERSION.fullmatch(tag) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Distribution requires a version tag and full source SHA')
    git(root, 'rev-parse', '--verify', f'{sha}^{{commit}}')
    if git(root, 'ls-tree', '--name-only', sha, '--', PROVENANCE):
        raise ValueError('Source snapshot must not contain generated distribution provenance')
    files = {path: json.dumps({**manifest, 'version': tag[1:]}, ensure_ascii=False, indent=2) + '\n'
             for path, manifest in source_manifests(root, sha).items()}
    # This source-file marker makes older package trees reproducible even when
    # their catalogs already used the same remote published channel.
    short_commands = bool(git(root, 'ls-tree', '--name-only', sha, '--', 'scripts/package_claude.py'))
    if short_commands:
        archive = subprocess.check_output(['git', 'archive', '--format=tar', sha, '--',
                                          'skills', '.claude-plugin'], cwd=root, timeout=30)
        with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
            sources = {entry.name: snapshot.extractfile(entry).read() for entry in snapshot if entry.isfile()}
        sources['.claude-plugin/plugin.json'] = files['.claude-plugin/plugin.json'].encode('utf-8')
        for path, content in render_claude_package(sources).items():
            try:
                files[f'build/claude/{path}'] = content.decode('utf-8')
            except UnicodeDecodeError:
                files[f'build/claude/{path}'] = content
    files[PROVENANCE] = json.dumps({'schema_version': 1, 'source_sha': sha, 'tag': tag}, indent=2) + '\n'
    if short_commands:
        files[f'build/claude/{PROVENANCE}'] = files[PROVENANCE]
    claude_source = './build/claude' if short_commands else './'
    for path, local_source in zip(CATALOGS, (claude_source, {'source': 'local', 'path': './'})):
        # Historical local catalogs must retain their exact bytes/tree hashes.
        if not git(root, 'ls-tree', '--name-only', sha, '--', path):
            continue
        catalog = json.loads(git(root, 'show', f'{sha}:{path}'))
        for entry in catalog.get('plugins', []):
            source = entry.get('source')
            published_source = source == PUBLISHED_SOURCE or (
                short_commands and path == CATALOGS[0] and source == CLAUDE_PUBLISHED_SOURCE)
            if entry.get('name') == 'nexus' and published_source:
                entry['source'] = local_source
                files[path] = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
    # A temporary index leaves the checkout, staging area and refs untouched.
    with tempfile.TemporaryDirectory(prefix='nexus-distribution-') as temporary:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(temporary) / 'index')}

        def indexed(*args, input=None):
            return subprocess.check_output(['git', *args], cwd=root, env=env, input=input,
                                           text=True, stderr=subprocess.PIPE, timeout=30).strip()

        indexed('read-tree', sha)
        for path, content in files.items():
            # Package assets can be binary; hash bytes without text decoding.
            blob = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=root,
                                           input=content.encode('utf-8') if isinstance(content, str) else content,
                                           stderr=subprocess.PIPE, timeout=30).decode().strip()
            indexed('update-index', '--add', '--cacheinfo', '100644', blob, path)
        tree = indexed('write-tree')
    return files, tree


def verify_remote_tag(api, tag, sha):
    """A just-created GitHub tag is not present in the local checkout yet."""
    obj = api.request('GET', f'git/ref/tags/{tag}')['object']
    for _ in range(5):
        if obj.get('type') == 'commit' and obj.get('sha') == sha:
            return
        if obj.get('type') != 'tag' or not re.fullmatch(r'[0-9a-f]{40}', obj.get('sha', '')):
            break
        obj = api.request('GET', f'git/tags/{obj["sha"]}')['object']
    raise RuntimeError('Remote distribution tag does not identify the source commit')


def ensure_package_tag(root, api, sha, tag, files, tree):
    """Reconcile a versioned package without ever moving an existing tag."""
    package_tag = f'plugin-{tag}'
    ref = api.request('GET', f'git/ref/tags/{package_tag}')
    if ref:
        obj = ref['object']
        for _ in range(5):
            if obj.get('type') != 'tag':
                break
            obj = api.request('GET', f'git/tags/{obj["sha"]}')['object']
        if obj.get('type') != 'commit' or not re.fullmatch(r'[0-9a-f]{40}', obj.get('sha', '')):
            raise RuntimeError('Invalid immutable plugin package tag')
        commit = api.request('GET', f'git/commits/{obj["sha"]}')
        if commit['tree']['sha'] != tree:
            raise RuntimeError('Immutable plugin package differs from its release snapshot')
        return
    entries = []
    for path, content in files.items():
        entry = {'path': path, 'mode': '100644', 'type': 'blob'}
        if isinstance(content, bytes):
            # Binary assets are copied from the source; GitHub already owns the blob.
            entry['sha'] = git(root, 'rev-parse', f'{sha}:{path.removeprefix("build/claude/")}')
        else:
            entry['content'] = content
        entries.append(entry)
    created = api.request('POST', 'git/trees', {
        'base_tree': git(root, 'rev-parse', f'{sha}^{{tree}}'),
        'tree': entries,
    })
    if created['sha'] != tree:
        raise RuntimeError('Generated distribution tree differs from the validated snapshot')
    commit = api.request('POST', 'git/commits', {
        'message': f'Package NEXUS {tag}\n\nSource: {sha}', 'tree': tree, 'parents': [sha],
    })
    api.request('POST', 'git/refs', {'ref': f'refs/tags/{package_tag}', 'sha': commit['sha']})


def promote_distribution(root, api, sha, tag):
    """Expose a complete package with one non-forced ref update after publication."""
    files, tree = distribution_snapshot(root, sha, tag)
    if not published(api.request('GET', f'releases/tags/{tag}')):
        raise RuntimeError('Distribution requires a published stable release')
    verify_remote_tag(api, tag, sha)
    ref = api.request('GET', 'git/ref/heads/plugins')
    tip = ref['object']['sha'] if ref else None
    if tip:
        if not re.fullmatch(r'[0-9a-f]{40}', tip):
            raise ValueError('Invalid distribution branch tip')
        encoded = api.request('GET', f'contents/{PROVENANCE}?ref={tip}')
        if encoded.get('encoding') != 'base64':
            raise ValueError('Distribution provenance must use base64 encoding')
        previous = json.loads(base64.b64decode(''.join(encoded['content'].split()), validate=True))
        previous_tag, previous_sha = previous.get('tag'), previous.get('source_sha')
        if (previous.get('schema_version') != 1 or not isinstance(previous_tag, str)
                or not VERSION.fullmatch(previous_tag) or not isinstance(previous_sha, str)
                or not re.fullmatch(r'[0-9a-f]{40}', previous_sha)):
            raise ValueError('Invalid distribution provenance')
        _, previous_tree = distribution_snapshot(root, previous_sha, previous_tag)
        verify_remote_tag(api, previous_tag, previous_sha)
        commit = api.request('GET', f'git/commits/{tip}')
        if commit['tree']['sha'] != previous_tree:
            raise RuntimeError('Distribution branch differs from its source provenance')
        old_version = tuple(map(int, VERSION.fullmatch(previous_tag).groups()))
        new_version = tuple(map(int, VERSION.fullmatch(tag).groups()))
        if old_version >= new_version:
            if (old_version == new_version and previous_sha != sha
                    or not git_succeeds(root, 'merge-base', '--is-ancestor', sha, previous_sha)):
                raise RuntimeError('Distribution version or source history conflicts')
            if not published(api.request('GET', f'releases/tags/{previous_tag}')):
                raise RuntimeError('Distribution provenance has no published release')
            ensure_package_tag(root, api, sha, tag, files, tree)
            print(f'Distribution already at {previous_tag}')
            return
        if not git_succeeds(root, 'merge-base', '--is-ancestor', previous_sha, sha):
            raise RuntimeError('Distribution source must advance its previous source')

    ensure_package_tag(root, api, sha, tag, files, tree)
    commit = api.request('POST', 'git/commits', {
        'message': f'Distribute NEXUS {tag}\n\nSource: {sha}', 'tree': tree,
        'parents': [tip] if tip else [sha],
    })
    if tip:
        # With tip as parent, an unrelated concurrent advancement makes this
        # non-fast-forward and GitHub rejects it. Never overwrite that advancement.
        api.request('PATCH', 'git/refs/heads/plugins', {'sha': commit['sha'], 'force': False})
    else:
        api.request('POST', 'git/refs', {'ref': DISTRIBUTION_REF, 'sha': commit['sha']})
    print(f'Distributed {tag} on plugins: {commit["sha"]}')


def publish(root, api, sha, before, recover_from=None):
    for value in (sha, before):
        if not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValueError('Expected full commit SHA')
        git(root, 'rev-parse', '--verify', f'{value}^{{commit}}')
    if not git_succeeds(root, 'merge-base', '--is-ancestor', before, sha):
        raise RuntimeError('Previous push must be an ancestor; force pushes are unsupported')
    source_manifests(root, sha)

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
            promote_distribution(root, api, sha, current[0][1])
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
        promote_distribution(root, api, latest[2], latest[1])
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
        manifest = source_manifests(root, sha)[MANIFESTS[0]]
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
    promote_distribution(root, api, sha, tag)
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
