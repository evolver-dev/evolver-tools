#!/usr/bin/env python3
"""firewall-rule — iptables/nftables helper. List, add, and remove firewall rules."""

import sys
import os
import re
import subprocess
import argparse


def run_iptables_save():
    """Run iptables-save and return output."""
    try:
        result = subprocess.run(['iptables-save'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"iptables-save failed: {result.stderr.strip()}", file=sys.stderr)
            return None
        return result.stdout
    except FileNotFoundError:
        print("iptables-save not found. Try running as root.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("iptables-save timed out.", file=sys.stderr)
        return None
    except PermissionError:
        print("Permission denied. Try running as root.", file=sys.stderr)
        return None


def run_iptables(args_list):
    """Run iptables with given arguments."""
    try:
        cmd = ['iptables'] + args_list
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"iptables error: {result.stderr.strip()}", file=sys.stderr)
            return False
        if result.stdout:
            print(result.stdout.strip())
        return True
    except FileNotFoundError:
        print("iptables not found. Try running as root.", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("iptables timed out.", file=sys.stderr)
        return False
    except PermissionError:
        print("Permission denied. Try running as root.", file=sys.stderr)
        return False


def parse_rules_from_save(output):
    """Parse iptables-save output into structured rules."""
    rules = []
    current_chain = None
    current_table = None

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith('#'):
            continue

        if line.startswith('*'):
            current_table = line[1:]
            current_chain = None
            continue

        if line.startswith(':'):
            parts = line[1:].split()
            if parts:
                current_chain = parts[0]
            continue

        if line.startswith('COMMIT'):
            continue

        if line.startswith('-A') or line.startswith('['):
            chain = None
            rest = line

            if line.startswith('-A'):
                parts = line.split()
                if len(parts) >= 2:
                    chain = parts[1]
                    rest = ' '.join(parts[2:])
            elif line.startswith('['):
                m = re.match(r'^\[(\d+):(\d+)\](.*)', line)
                if m:
                    rest = m.group(3).strip()

            rules.append({
                'raw': line,
                'table': current_table,
                'chain': chain or current_chain or 'unknown',
                'text': rest,
            })

    return rules


def display_rules(rules):
    """Display numbered rules."""
    if not rules:
        print("No rules found.")
        return

    table_map = {}
    for rule in rules:
        t = rule['table'] or 'filter'
        if t not in table_map:
            table_map[t] = []
        table_map[t].append(rule)

    num = 1
    for table, tbl_rules in table_map.items():
        chain_map = {}
        for r in tbl_rules:
            c = r['chain'] or 'unknown'
            if c not in chain_map:
                chain_map[c] = []
            chain_map[c].append(r)

        for chain, chain_rules in chain_map.items():
            print(f"\033[1;36mTable: {table} / Chain: {chain}\033[0m")
            for r in chain_rules:
                print(f"  \033[33m[{num:>3}]\033[0m {r['raw']}")
                num += 1
            print()

    print(f"\033[1mTotal: {len(rules)} rule(s)\033[0m")


def cmd_list(args):
    """List all current firewall rules."""
    output = run_iptables_save()
    if output is None:
        # Try nftables
        try:
            result = subprocess.run(['nft', 'list', 'ruleset'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(result.stdout)
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        sys.exit(1)

    rules = parse_rules_from_save(output)
    display_rules(rules)


def cmd_add(args):
    """Add a firewall rule."""
    cmd_parts = []

    if args.tcp:
        proto = 'tcp'
        port = args.tcp
    elif args.udp:
        proto = 'udp'
        port = args.udp
    else:
        print("Specify --tcp or --udp with port number.", file=sys.stderr)
        sys.exit(1)

    action = 'ACCEPT' if args.accept else 'DROP' if args.drop else 'REJECT' if args.reject else 'ACCEPT'

    cmd_parts = ['-A', args.chain or 'INPUT', '-p', proto, '--dport', str(port), '-j', action]

    if args.dry_run:
        print(f"\033[93mDRY RUN: iptables {' '.join(cmd_parts)}\033[0m")
        return

    success = run_iptables(cmd_parts)
    if success:
        print(f"Added rule: {proto} port {port} → {action} in {args.chain or 'INPUT'} chain.")


def cmd_remove(args):
    """Remove a rule by number."""
    output = run_iptables_save()
    if not output:
        sys.exit(1)

    rules = parse_rules_from_save(output)
    target_num = args.number

    if target_num < 1 or target_num > len(rules):
        print(f"Rule number {target_num} out of range (1-{len(rules)}).", file=sys.stderr)
        sys.exit(1)

    target_rule = rules[target_num - 1]
    raw = target_rule['raw']

    if raw.startswith('-A'):
        rule_num = 1
        chain = target_rule['chain']
        # Count how many -A rules for this chain come before
        for r in rules[:target_num]:
            if r['raw'].startswith('-A') and r['chain'] == chain:
                pass

        chain_rules = [r for r in rules if r['raw'].startswith('-A') and r['chain'] == chain]
        for i, r in enumerate(chain_rules):
            if r['raw'] == raw:
                rule_num = i + 1
                break

        cmd_parts = ['-D', chain, str(rule_num)]
        if args.dry_run:
            print(f"\033[93mDRY RUN: iptables {' '.join(cmd_parts)}\033[0m")
            return
        success = run_iptables(cmd_parts)
        if success:
            print(f"Removed rule #{target_num} from {chain} chain.")
    else:
        print("Cannot remove non-standard rule.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='iptables/nftables firewall rule helper.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  firewall-rule list
  firewall-rule add --tcp 8080 --accept
  firewall-rule remove 3
  firewall-rule --dry-run add --udp 53
        """,
    )
    parser.add_argument('action', choices=['list', 'add', 'remove'], help='Action to perform')
    parser.add_argument('--tcp', type=int, metavar='PORT', help='TCP port number')
    parser.add_argument('--udp', type=int, metavar='PORT', help='UDP port number')
    parser.add_argument('--accept', action='store_true', help='Accept packets (default for add)')
    parser.add_argument('--drop', action='store_true', help='Drop packets')
    parser.add_argument('--reject', action='store_true', help='Reject packets')
    parser.add_argument('--chain', '-c', default='INPUT', help='Chain name (default: INPUT)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be done')
    parser.add_argument('number', nargs='?', type=int, help='Rule number for remove action')

    args = parser.parse_args()

    if not os.geteuid() == 0:
        print("\033[93mWarning: Most firewall operations require root privileges.\033[0m", file=sys.stderr)

    try:
        if args.action == 'list':
            cmd_list(args)
        elif args.action == 'add':
            cmd_add(args)
        elif args.action == 'remove':
            if not args.number:
                print("Rule number required for remove action.", file=sys.stderr)
                sys.exit(1)
            cmd_remove(args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print("Permission denied. Try running as root.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
