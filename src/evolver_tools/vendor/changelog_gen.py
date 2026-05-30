#!/usr/bin/env python3
"""changelog-gen — Generate changelog from git log.

Usage: changelog-gen          — all tags
       changelog-gen v1.0.0   — from this tag
       changelog-gen v1.0.0..v2.0.0 — range

Outputs Markdown changelog with semantic commit grouping.
Zero-dependency (stdlib only, uses subprocess).
"""
import sys, subprocess, re

TYPES = {
    'feat': 'Features',
    'fix': 'Bug Fixes',
    'docs': 'Documentation',
    'style': 'Style',
    'refactor': 'Refactoring',
    'perf': 'Performance',
    'test': 'Tests',
    'chore': 'Chores',
    'ci': 'CI/CD',
}

def run_git(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ''

def main():
    args = sys.argv[1:]
    tag_range = args[0] if args else 'HEAD'
    
    log = run_git(['git', 'log', f'{tag_range}',
                   '--pretty=format:%s|||%b', '--no-merges'])
    if not log:
        # Try without tag
        log = run_git(['git', 'log', '--pretty=format:%s|||%b', '--no-merges', '-50'])
    
    commits = log.split('\n') if log else []
    grouped = {}
    ungrouped = []
    
    for c in commits:
        if '|||' in c:
            subject, body = c.split('|||', 1)
        else:
            subject, body = c, ''
        subject = subject.strip()
        if not subject:
            continue
        m = re.match(r'^(feat|fix|docs|style|refactor|perf|test|chore|ci)(\(.+\))?!?:\s*(.+)', subject, re.I)
        if m:
            typ = m.group(1).lower()
            msg = m.group(3).strip().rstrip('.')
            scope = m.group(2) or ''
            grouped.setdefault(typ, []).append(f"- {scope} {msg}")
        else:
            ungrouped.append(f"- {subject}")
    
    print('# Changelog\n')
    for typ in ['feat', 'fix', 'docs', 'refactor', 'perf', 'chore', 'ci', 'test', 'style']:
        if typ in grouped:
            print(f'## {TYPES.get(typ,typ.capitalize())}')
            for l in grouped[typ]:
                print(l)
            print()
    if ungrouped:
        print('## Other')
        for l in ungrouped:
            print(l)
        print()

if __name__ == '__main__':
    main()
