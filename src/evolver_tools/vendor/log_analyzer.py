#!/usr/bin/env python3
"""log-analyzer — Log file analyzer. Parse common log formats and show stats."""

import sys
import os
import re
import time
import argparse
from collections import Counter, defaultdict


APACHE_PATTERN = re.compile(
    r'^(\S+)\s+(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+(\S+)"\s+(\d+)\s+(\d+|-)'
    r'(?:\s+"([^"]*)"\s+"([^"]*)")?'
)

SYSLOG_PATTERN = re.compile(
    r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)$'
)

CUSTOM_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2})?)\s+'
    r'\[?(\w+)\]?\s*(.*)$'
)


def read_lines_from_file_or_stdin(filepath=None):
    """Read lines from a file or stdin."""
    if filepath:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(filepath, 'r', errors='replace') as f:
                return f.readlines()
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            return []
        try:
            return sys.stdin.readlines()
        except KeyboardInterrupt:
            return []


def parse_apache(lines):
    """Parse Apache/Nginx log lines."""
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = APACHE_PATTERN.match(line)
        if m:
            entries.append({
                'ip': m.group(1),
                'ident': m.group(2),
                'user': m.group(3),
                'time': m.group(4),
                'method': m.group(5),
                'path': m.group(6),
                'protocol': m.group(7),
                'status': int(m.group(8)),
                'size': m.group(9),
                'referer': m.group(10) or '-',
                'ua': m.group(11) or '-',
                'raw': line,
            })
    return entries


def parse_syslog(lines):
    """Parse syslog-style log lines."""
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = SYSLOG_PATTERN.match(line)
        if m:
            severity = 'info'
            msg = m.group(5).lower()
            if any(w in msg for w in ['error', 'failed', 'fatal']):
                severity = 'error'
            elif any(w in msg for w in ['warn', 'warning']):
                severity = 'warn'
            entries.append({
                'timestamp': m.group(1),
                'host': m.group(2),
                'service': m.group(3),
                'pid': m.group(4),
                'message': m.group(5),
                'severity': severity,
                'raw': line,
            })
    return entries


def parse_custom(lines):
    """Parse custom log format (ISO timestamp + level + message)."""
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = CUSTOM_PATTERN.match(line)
        if m:
            entries.append({
                'timestamp': m.group(1),
                'level': m.group(2),
                'message': m.group(3),
                'raw': line,
            })
    return entries


def show_stats(entries, format_type, top_ips=False, top_n=10):
    """Display statistics from parsed log entries."""
    if not entries:
        print("No entries to analyze.")
        return

    print(f"\033[1mLog Analysis Summary\033[0m")
    print(f"  Total entries: \033[33m{len(entries)}\033[0m")
    print()

    if format_type == 'apache':
        status_counts = Counter(e['status'] for e in entries)
        method_counts = Counter(e['method'] for e in entries)
        path_counts = Counter(e['path'] for e in entries)
        ip_counts = Counter(e['ip'] for e in entries)

        code_ranges = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0}
        for status, count in status_counts.items():
            if 200 <= status < 300:
                code_ranges['2xx'] += count
            elif 300 <= status < 400:
                code_ranges['3xx'] += count
            elif 400 <= status < 500:
                code_ranges['4xx'] += count
            elif 500 <= status < 600:
                code_ranges['5xx'] += count

        print(f"  \033[1mStatus Codes:\033[0m")
        for rng in ['2xx', '3xx', '4xx', '5xx']:
            color = '\033[92m' if rng == '2xx' else '\033[93m' if rng == '3xx' else '\033[91m' if rng == '4xx' else '\033[91m'
            print(f"    {color}{rng}\033[0m: {code_ranges[rng]}")

        print(f"\n  \033[1mHTTP Methods:\033[0m")
        for method, count in method_counts.most_common():
            print(f"    \033[94m{method}\033[0m: {count} ({count/len(entries)*100:.1f}%)")

        print(f"\n  \033[1mTop Paths:\033[0m")
        for path, count in path_counts.most_common(top_n):
            print(f"    \033[33m{path}\033[0m: {count}")

        if top_ips:
            print(f"\n  \033[1mTop IPs:\033[0m")
            for ip, count in ip_counts.most_common(top_n):
                print(f"    \033[35m{ip}\033[0m: {count}")

    elif format_type == 'syslog':
        severity_counts = Counter(e['severity'] for e in entries)
        service_counts = Counter(e['service'] for e in entries)

        print(f"  \033[1mSeverity:\033[0m")
        for sev in ['error', 'warn', 'info']:
            color = '\033[91m' if sev == 'error' else '\033[93m' if sev == 'warn' else '\033[92m'
            count = severity_counts.get(sev, 0)
            print(f"    {color}{sev}\033[0m: {count}")

        print(f"\n  \033[1mTop Services:\033[0m")
        for svc, count in service_counts.most_common(top_n):
            print(f"    \033[94m{svc}\033[0m: {count}")

    elif format_type == 'custom':
        level_counts = Counter(e['level'] for e in entries)
        print(f"  \033[1mLevels:\033[0m")
        for level, count in level_counts.most_common():
            print(f"    \033[94m{level}\033[0m: {count}")

    # Timeline
    print(f"\n  \033[1mTimeline:\033[0m")
    time_groups = Counter()
    for e in entries:
        ts = e.get('timestamp', e.get('time', ''))
        if ts:
            if ':' in ts:
                date_part = ts.split()[0] if ' ' in ts else ts[:10]
                time_groups[date_part] += 1
    for date, count in sorted(time_groups.items())[:20]:
        bar = '█' * min(count, 50)
        print(f"    \033[90m{date}\033[0m {bar} \033[33m{count}\033[0m")


def tail_follow(filepath):
    """Tail-follow a log file (like tail -f)."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(filepath, 'r') as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Log file analyzer. Parse and analyze common log formats.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  log-analyzer access.log
  log-analyzer --format apache access.log --top-ips
  log-analyzer --tail-follow /var/log/syslog
  log-analyzer --format syslog /var/log/syslog
        """,
    )
    parser.add_argument('file', nargs='?', help='Log file to analyze (default: stdin)')
    parser.add_argument('--format', '-f', choices=['apache', 'syslog', 'custom'], default='apache',
                        help='Log format (default: auto-detect from file)')
    parser.add_argument('--top-ips', action='store_true', help='Show top IP addresses (apache format)')
    parser.add_argument('--top', type=int, default=10, help='Number of top items to show')
    parser.add_argument('--tail-follow', '-F', action='store_true', help='Follow file in real-time')

    args = parser.parse_args()

    if args.tail_follow and args.file:
        tail_follow(args.file)
        return

    lines = read_lines_from_file_or_stdin(args.file)
    if not lines:
        print("No input provided.", file=sys.stderr)
        sys.exit(1)

    file_format = args.format
    if args.file and file_format == 'apache':
        basename = os.path.basename(args.file).lower()
        if 'syslog' in basename or 'auth.log' in basename or 'messages' in basename:
            file_format = 'syslog'

    try:
        if file_format == 'apache':
            entries = parse_apache(lines)
        elif file_format == 'syslog':
            entries = parse_syslog(lines)
        elif file_format == 'custom':
            entries = parse_custom(lines)
        else:
            entries = []

        show_stats(entries, file_format, top_ips=args.top_ips, top_n=args.top)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "log-analyzer",
    "func": "main",
    "desc": 'Log file analyzer',
}

if __name__ == '__main__':
    main()
