#!/usr/bin/env python3
"""changelog-gen — Generate changelog from git log

Scans git log and groups commits by conventional commit type.

Usage:
    changelog-gen                    # Full changelog (last 100 commits)
    changelog-gen -n 50              # Last 50 commits
    changelog-gen --since=2024-01-01 # Since date
    changelog-gen --tag=v1.0.0       # Since a tag
    changelog-gen --format=json      # JSON output
    changelog-gen --stdout           # Output to stdout (default)
"""
import sys
import subprocess
import re
import os
from collections import OrderedDict


CONVENTIONAL_TYPES = OrderedDict([
    ('feat', ('Features', '🚀')),
    ('fix', ('Bug Fixes', '🐛')),
    ('docs', ('Documentation', '📝')),
    ('refactor', ('Refactoring', '♻️')),
    ('perf', ('Performance', '⚡')),
    ('test', ('Tests', '🧪')),
    ('chore', ('Chores', '🔧')),
    ('style', ('Style', '💄')),
    ('ci', ('CI', '👷')),
    ('build', ('Build', '📦')),
    ('revert', ('Reverts', '⏪')),
    ('other', ('Other', '📋')),
])


def run_git(*args):
    """Run git command and return output."""
    try:
        result = subprocess.run(['git'] + list(args), capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: git command failed: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'git' not found", file=sys.stderr)
        sys.exit(1)


def parse_commits(raw_log):
    """Parse git log --format output into structured commits."""
    commits = []
    for block in raw_log.split('\n\n----\n\n'):
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        if len(lines) < 3:
            continue

        commit_hash = lines[0].strip()
        author = lines[1].strip()
        date = lines[2].strip()
        msg_lines = lines[3:]

        # Parse commit message
        msg = '\n'.join(msg_lines).strip()

        # Conventional commit parsing
        conv_match = re.match(r'^(\w+)(?:\(([^)]*)\))?:\s*(.*)', msg.split('\n')[0])
        if conv_match:
            commit_type = conv_match.group(1)
            scope = conv_match.group(2) or ''
            description = conv_match.group(3)
            body = '\n'.join(msg.split('\n')[1:]).strip()
            # Check for breaking change
            breaking = bool(re.search(r'BREAKING CHANGE|!:', msg.split('\n')[0]))
        else:
            commit_type = 'other'
            scope = ''
            description = msg.split('\n')[0]
            body = '\n'.join(msg.split('\n')[1:]).strip()
            breaking = False

        commits.append({
            'hash': commit_hash[:7],
            'author': author,
            'date': date,
            'type': commit_type,
            'scope': scope,
            'description': description,
            'body': body,
            'breaking': breaking,
        })
    return commits


def format_changelog(commits, output_format='markdown'):
    """Format commits into changelog."""
    # Group by type
    groups = OrderedDict()
    for ctype in CONVENTIONAL_TYPES:
        groups[ctype] = []

    for c in commits:
        t = c['type']
        if t in groups:
            groups[t].append(c)
        else:
            groups['other'].append(c)

    if output_format == 'json':
        import json
        return json.dumps(commits, indent=2, ensure_ascii=False)

    lines = []
    lines.append('# Changelog')
    lines.append('')
    lines.append(f'Generated from {len(commits)} commits')
    lines.append('')

    for ctype, (title, emoji) in CONVENTIONAL_TYPES.items():
        type_commits = groups[ctype]
        if not type_commits:
            continue
        lines.append(f'## {emoji} {title}')
        lines.append('')
        for c in type_commits:
            scope = f'**{c["scope"]}**: ' if c['scope'] else ''
            breaking = ' 💥' if c['breaking'] else ''
            lines.append(f'- {scope}{c["description"]}{breaking}')
            lines.append(f'  ([{c["hash"]}](https://github.com/evolver-dev/evolver-tools/commit/{c["hash"]}), {c["author"]})')
        lines.append('')

    return '\n'.join(lines)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    num = 100
    since = None
    tag = None
    output_format = 'markdown'

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-n':
            i += 1
            if i < len(args):
                num = int(args[i])
        elif arg.startswith('--since='):
            since = arg.split('=', 1)[1]
        elif arg == '--since':
            i += 1
            if i < len(args):
                since = args[i]
        elif arg.startswith('--tag='):
            tag = arg.split('=', 1)[1]
        elif arg == '--tag':
            i += 1
            if i < len(args):
                tag = args[i]
        elif arg == '--format':
            i += 1
            if i < len(args):
                output_format = args[i]
        elif arg == '--stdout':
            pass  # default
        else:
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        i += 1

    # Build git log command
    git_args = ['log', f'--max-count={num}', '--format=%H%n%an%n%aI%n%B%n----']
    if tag:
        git_args.append(f'{tag}..HEAD')
    if since:
        git_args.append(f'--since={since}')

    raw = run_git(*git_args)
    commits = parse_commits(raw)

    if not commits:
        print("No commits found.")
        return

    result = format_changelog(commits, output_format)
    print(result)


if __name__ == '__main__':
    main()
