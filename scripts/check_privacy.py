#!/usr/bin/env python3
"""Check tracked/staged Git blobs, optionally all history reachable from HEAD.

This catches common accidents, not every possible personal name or financial fact.
Review source changes manually as well. Never print matched sensitive values.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import PurePosixPath

PRIVATE_DIRS = {'data', 'private', 'review', 'work', 'backups', 'node_modules', '.nuxt', '.output', '.venv', '__pycache__', '.idea', '.codex', '.agents', '.claude'}
PRIVATE_SUFFIXES = {'.csv', '.tsv', '.pdf', '.xlsx', '.xls', '.ofx', '.qfx', '.qif', '.sqlite', '.db', '.zip', '.log', '.pem', '.key', '.bundle'}
PATTERNS = [
    ('private key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ('API token', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,})\b')),
    ('bank account', re.compile(r'(?<![\w])(?:[A-Z]{2}\s?)?\d{2}(?: ?\d{4}){6}(?![\w])')),
    ('long numeric identifier', re.compile(r'(?<![\w])\+?\d{11,16}(?![\w])')),
    ('personal local path', re.compile(r'(?:[/]home[/][^/\s\x27\x22]+/|[A-Z]:\\Users\\[^\\\s]+\\)')),
]
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], stderr=subprocess.PIPE)


def path_issue(name: str) -> bool:
    path = PurePosixPath(name)
    return (bool(PRIVATE_DIRS.intersection(path.parts)) or path.suffix.lower() in PRIVATE_SUFFIXES
            or 'Zone.Identifier' in name or (path.name.startswith('.env') and path.name != '.env.example')
            or '.local.' in path.name)


def content_issues(content: bytes, name: str) -> list[str]:
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        return ['unreviewed binary file']
    # npm's lockfile includes hashes and public upstream contact metadata.
    patterns = PATTERNS[:2] if name == 'package-lock.json' else PATTERNS
    found = [label for label, pattern in patterns if pattern.search(text)]
    if name != 'package-lock.json':
        for email in EMAIL.findall(text):
            if not email.endswith(('@users.noreply.github.com', '@example.invalid', '@example.com')):
                found.append('email address')
                break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    failures = []
    checked = set()
    trees = git('rev-list', 'HEAD').decode().splitlines() if args.history else [None]
    for tree in trees:
        if tree:
            entries = git('ls-tree', '-rz', '--full-tree', tree).split(b'\0')
        else:
            entries = git('ls-files', '--stage', '-z').split(b'\0')
        for entry in entries:
            if not entry:
                continue
            meta, raw_name = entry.split(b'\t', 1)
            name = raw_name.decode('utf-8')
            parts = meta.split()
            blob = parts[2] if tree else parts[1]
            key = (name, blob)
            if key in checked:
                continue
            checked.add(key)
            if parts[0] in (b'120000', b'160000'):
                failures.append((name, 'symlink or submodule requires manual review'))
                continue
            if path_issue(name):
                failures.append((name, 'private/generated file must not be tracked'))
            for issue in content_issues(git('cat-file', 'blob', blob.decode()), name):
                failures.append((name, issue))
        if tree:
            metadata = git('show', '-s', '--format=%an%n%ae%n%cn%n%ce%n%B', tree)
            for issue in content_issues(metadata, 'commit metadata'):
                failures.append((tree[:10], issue))
    for name, issue in failures:
        print(f'FAIL {name}: {issue}')
    print(f'Privacy check: {len(checked)} file versions checked; {len(failures)} findings.')
    return int(bool(failures))


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError:
        print('Privacy check could not read Git. Run inside the repository with a valid index/HEAD.', file=sys.stderr)
        raise SystemExit(2)
