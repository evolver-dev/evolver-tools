#!/usr/bin/env python3
"""audit-log — Parse and filter system audit logs. Read /var/log/auth.log, syslog, journalctl output."""

import sys
import os
import re
import argparse
import datetime
import glob


def parse_syslog_line(line):
    """Parse a standard syslog-style line."""
    pattern = r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)$'
    m = re.match(pattern, line)
    if m:
        timestamp, host, service, pid, message = m.groups()
        return {
            'timestamp': timestamp,
            'host': host,
            'service': service,
            'pid': pid,
            'message': message,
            'raw': line.rstrip('\n'),
        }
    return None


def parse_auth_log_line(line):
    """Parse a auth.log style line."""
    pattern = r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)$'
    m = re.match(pattern, line)
    if m:
        timestamp, host, service, pid, message = m.groups()
        severity = 'info'
        if 'Failed' in message or 'failure' in message or 'error' in message:
            severity = 'error'
        elif 'Accepted' in message or 'success' in message:
            severity = 'info'
        elif 'Invalid' in message or 'invalid' in message:
            severity = 'warn'
        return {
            'timestamp': timestamp,
            'host': host,
            'service': service,
            'pid': pid,
            'message': message,
            'severity': severity,
            'raw': line.rstrip('\n'),
        }
    return None


def parse_journald_line(line):
    """Parse journalctl-style output."""
    m = re.match(r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)$', line)
    if not m:
        m = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)$', line)
    if m:
        timestamp, host, service, pid, message = m.groups()
        return {
            'timestamp': timestamp,
            'host': host,
            'service': service,
            'pid': pid,
            'message': message,
            'raw': line.rstrip('\n'),
        }
    return {'raw': line.rstrip('\n'), 'service': '', 'timestamp': '', 'message': line.rstrip('\n')}


def determine_severity(message):
    """Determine severity from message content."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ['error', 'failed', 'failure', 'fatal', 'critical', 'panic']):
        return 'error'
    if any(w in msg_lower for w in ['warn', 'warning', 'invalid', 'denied']):
        return 'warn'
    if any(w in msg_lower for w in ['info', 'accepted', 'started', 'connected']):
        return 'info'
    return 'debug'


def colorize_entry(entry, show_severity=True):
    """Colorize a log entry based on severity."""
    severity = entry.get('severity', determine_severity(entry.get('message', '')))
    if severity == 'error':
        color = '\033[91m'  # red
    elif severity == 'warn':
        color = '\033[93m'  # yellow
    elif severity == 'info':
        color = '\033[92m'  # green
    else:
        color = '\033[90m'  # gray

    ts = entry.get('timestamp', '')
    svc = entry.get('service', '')
    msg = entry.get('message', entry.get('raw', ''))
    reset = '\033[0m'
    return f"{color}{ts}\033[0m \033[94m{svc}\033[0m {color}{msg}{reset}"


def read_log_file(path):
    """Read log file, return list of lines."""
    if not os.path.exists(path):
        print(f"File not found: {path}", file=sys.stderr)
        return []
    try:
        with open(path, 'r', errors='replace') as f:
            return f.readlines()
    except PermissionError:
        print(f"Permission denied: {path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []


def filter_entries(entries, service=None, severity=None, since=None, until=None):
    """Filter log entries by service, severity, date range."""
    filtered = []
    for entry in entries:
        if service and entry.get('service', '').lower() != service.lower():
            continue
        if severity and entry.get('severity', '') != severity:
            sev = entry.get('severity', determine_severity(entry.get('message', '')))
            if sev != severity:
                continue
        entry['severity'] = entry.get('severity', determine_severity(entry.get('message', '')))
        filtered.append(entry)
    return filtered


def main():
    parser = argparse.ArgumentParser(
        description='Parse and filter system audit logs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  audit-log --service sshd
  audit-log --since "2024-01-01" --until "2024-01-02"
  audit-log --severity error
  audit-log /var/log/auth.log --service sshd --severity error
  cat /var/log/syslog | audit-log --severity warn
        """,
    )
    parser.add_argument('files', nargs='*', help='Log files to parse (default: stdin)')
    parser.add_argument('--service', '-s', help='Filter by service name (e.g., sshd)')
    parser.add_argument('--severity', '-S', choices=['error', 'warn', 'info', 'debug'], help='Filter by severity')
    parser.add_argument('--since', help='Show entries after this date (YYYY-MM-DD)')
    parser.add_argument('--until', help='Show entries before this date (YYYY-MM-DD)')
    parser.add_argument('--no-color', action='store_true', help='Disable colorized output')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON lines')
    parser.add_argument('--count', '-c', action='store_true', help='Show count only')

    args = parser.parse_args()

    lines = []
    if args.files:
        for f in args.files:
            if os.path.isdir(f):
                for pat in ['/var/log/auth.log*', '/var/log/syslog*', '/var/log/messages*']:
                    for gf in glob.glob(os.path.join(f, os.path.basename(pat))):
                        lines.extend(read_log_file(gf))
            else:
                lines.extend(read_log_file(f))
    else:
        if not sys.stdin.isatty():
            try:
                lines = sys.stdin.readlines()
            except KeyboardInterrupt:
                lines = []
        else:
            default_logs = glob.glob('/var/log/auth.log*') + glob.glob('/var/log/syslog*') + glob.glob('/var/log/messages*')
            if default_logs:
                for f in default_logs[:3]:
                    lines.extend(read_log_file(f))
            else:
                print("No log files found and no stdin input. Pipe logs or specify file paths.", file=sys.stderr)
                sys.exit(1)

    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        entry = parse_syslog_line(line)
        if not entry:
            entry = parse_auth_log_line(line)
        if not entry:
            entry = parse_journald_line(line)
        if entry:
            if 'severity' not in entry:
                entry['severity'] = determine_severity(entry.get('message', ''))
            entries.append(entry)
        else:
            entries.append({
                'timestamp': '',
                'host': '',
                'service': '',
                'pid': '',
                'message': line,
                'severity': 'info',
                'raw': line,
            })

    filtered = filter_entries(entries, service=args.service, severity=args.severity)

    if args.since or args.until:
        since_dt = None
        until_dt = None
        if args.since:
            try:
                since_dt = datetime.datetime.strptime(args.since, '%Y-%m-%d')
            except ValueError:
                pass
        if args.until:
            try:
                until_dt = datetime.datetime.strptime(args.until, '%Y-%m-%d')
            except ValueError:
                pass
        if since_dt or until_dt:
            filtered2 = []
            for entry in filtered:
                ts = entry.get('timestamp', '')
                if not ts:
                    filtered2.append(entry)
                    continue
                try:
                    if ts.count('-') >= 2:
                        entry_dt = datetime.datetime.strptime(ts[:10], '%Y-%m-%d')
                    else:
                        continue
                    if since_dt and entry_dt < since_dt:
                        continue
                    if until_dt and entry_dt > until_dt:
                        continue
                    filtered2.append(entry)
                except ValueError:
                    filtered2.append(entry)
            filtered = filtered2

    if args.count:
        print(len(filtered))
        return

    if args.json:
        import json
        for entry in filtered:
            print(json.dumps(entry))
        return

    for entry in filtered:
        if args.no_color:
            print(entry.get('raw', entry.get('message', '')))
        else:
            print(colorize_entry(entry))



# === Auto-registration metadata ===
TOOL_META = {
    "name": "audit-log",
    "func": "main",
    "desc": 'Parse and filter system audit logs',
}

if __name__ == '__main__':
    main()
