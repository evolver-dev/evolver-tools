#!/usr/bin/env python3
"""pr-tool — Git PR helper: create, list, review PRs from terminal

Minimal wrapper around `gh pr` for GitHub PR workflow.

Usage:
    pr-tool create              # Create PR from current branch (gh pr create)
    pr-tool list                # List open PRs
    pr-tool review <number>     # Review PR (view diff + status)
    pr-tool status              # Check PR status for current branch
    pr-tool checkout <number>   # Checkout PR locally
"""
import sys
import subprocess
import json


def run_gh(*args):
    """Run gh command and return (output, exit_code)."""
    try:
        result = subprocess.run(['gh'] + list(args), capture_output=True, text=True)
        return result.stdout, result.returncode
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Install GitHub CLI: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)


def cmd_create():
    stdout, code = run_gh('pr', 'create', '--fill')
    if code == 0:
        print(stdout.strip())
    else:
        # Try again with web
        stdout2, code2 = run_gh('pr', 'create', '--fill', '--web')
        if code2 == 0:
            print("PR draft created. Complete in browser:")
        else:
            print("Error creating PR. Push your branch first.", file=sys.stderr)
            sys.exit(1)


def cmd_list():
    stdout, code = run_gh('pr', 'list', '--json', 'number,title,author,headRefName,state,createdAt', '--limit', '20')
    if code != 0 or not stdout.strip():
        print("No open PRs found.")
        return
    prs = json.loads(stdout)
    if not prs:
        print("No open PRs found.")
        return
    for pr in prs:
        print(f"  #{pr['number']:<5} {pr['state']:<8} {pr['title'][:65]:<65}")
        print(f"         by {pr['author']['login']:<20} branch: {pr['headRefName']}")


def cmd_review(number):
    # Show diff stat
    print(f"\n=== PR #{number} ===")
    stdout, code = run_gh('pr', 'view', str(number), '--json', 'title,body,additions,deletions,files,state,mergeable')
    if code != 0:
        sys.exit(1)
    data = json.loads(stdout)
    print(f"  Title: {data['title']}")
    print(f"  State: {data['state']}")
    print(f"  Lines: +{data['additions']} / -{data['deletions']}")
    print(f"  Files: {len(data['files'])} changed")
    print()
    # Show files
    for f in data['files']:
        print(f"    {'+' if f['additions']>0 else ' '}{f['additions']:>4}  {'-' if f['deletions']>0 else ' '}{f['deletions']:>4}  {f['path']}")


def cmd_status():
    stdout, code = run_gh('pr', 'status', '--json', 'number,title,state')
    if code != 0:
        print("No PR for current branch or error.")
        return
    print(stdout)


def cmd_checkout(number):
    stdout, code = run_gh('pr', 'checkout', str(number))
    print(stdout.strip())


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == 'create':
        cmd_create()
    elif cmd == 'list':
        cmd_list()
    elif cmd == 'review':
        if not rest:
            print("Error: PR number required. Usage: pr-tool review <number>", file=sys.stderr)
            sys.exit(1)
        cmd_review(rest[0])
    elif cmd == 'status':
        cmd_status()
    elif cmd == 'checkout':
        if not rest:
            print("Error: PR number required", file=sys.stderr)
            sys.exit(1)
        cmd_checkout(rest[0])
    else:
        print(f"Error: unknown command '{cmd}'", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
