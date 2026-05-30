#!/usr/bin/env python3
"""service-check — Check systemd service status. List, check, show logs."""
import sys
import os
import argparse
import subprocess
import json


def run_cmd(cmd):
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "command not found"
    except OSError as e:
        return -1, "", str(e)


def check_systemd_available():
    """Check if systemctl is available."""
    rc, _, _ = run_cmd(["which", "systemctl"])
    if rc != 0:
        print("Error: systemctl not found. Is this a systemd system?", file=sys.stderr)
        sys.exit(1)


def parse_service_line(line):
    """Parse a line from systemctl list-units output."""
    parts = line.split(None, 3)
    if len(parts) >= 3:
        return {
            "unit": parts[0],
            "load": parts[1],
            "active": parts[2],
            "desc": parts[3] if len(parts) > 3 else "",
        }
    return None


def cmd_list_all(args):
    """List all services."""
    check_systemd_available()
    cmd = ["systemctl", "list-units", "--type=service", "--no-pager", "--no-legend"]
    if args.all:
        cmd.append("--all")
    if args.user:
        cmd.insert(1, "--user")
    rc, stdout, stderr = run_cmd(cmd)
    if rc != 0:
        print(f"Error: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    services = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        s = parse_service_line(line)
        if s:
            services.append(s)

    return services


def cmd_failed(args):
    """List failed services."""
    check_systemd_available()
    cmd = ["systemctl", "list-units", "--type=service", "--state=failed", "--no-pager", "--no-legend"]
    if args.user:
        cmd.insert(1, "--user")
    rc, stdout, stderr = run_cmd(cmd)
    if rc != 0:
        print(f"Error: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    services = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        s = parse_service_line(line)
        if s:
            services.append(s)
    return services


def cmd_check_service(service_name, args):
    """Check status of a specific service."""
    check_systemd_available()
    cmd = ["systemctl", "status", service_name, "--no-pager"]
    if args.user:
        cmd.append("--user")
    if args.json:
        # Get JSON output
        json_cmd = ["systemctl", "show", service_name, "--no-pager"]
        if args.user:
            json_cmd.append("--user")
        rc, stdout, stderr = run_cmd(json_cmd)
        if rc != 0:
            print(f"Error: Service '{service_name}' not found or inaccessible", file=sys.stderr)
            print(stderr.strip(), file=sys.stderr)
            sys.exit(1)

        # Parse key=value pairs from systemctl show
        info = {}
        for line in stdout.strip().split("\n"):
            if "=" in line:
                key, val = line.split("=", 1)
                info[key] = val

        output = {
            "name": service_name,
            "description": info.get("Description", ""),
            "load_state": info.get("LoadState", ""),
            "active_state": info.get("ActiveState", ""),
            "sub_state": info.get("SubState", ""),
            "pid": info.get("MainPID", ""),
            "load": info.get("LoadState", ""),
            "active": info.get("ActiveState", ""),
            "since": info.get("ActiveEnterTimestamp", ""),
            "mem_current": info.get("MemoryCurrent", ""),
            "cpu_usage": info.get("CPUUsageNSec", ""),
            "exec_start": info.get("ExecStart", ""),
            "uptime": "",
        }
        print(json.dumps(output, indent=2))
    else:
        rc, stdout, stderr = run_cmd(cmd)
        if rc != 0:
            print(f"Warning: Service '{service_name}' may have issues:")
        print(stdout)


def cmd_logs(service_name, args):
    """Show recent logs for a service."""
    check_systemd_available()
    cmd = ["journalctl", "-u", service_name, "--no-pager", "-n", str(args.lines)]
    if args.user:
        cmd.insert(1, "--user")
    if args.follow:
        print("Warning: --follow requires interactive terminal. Showing last N lines instead.",
              file=sys.stderr)
    rc, stdout, stderr = run_cmd(cmd)
    if rc != 0:
        print(f"Error reading logs: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    print(stdout.strip())


def display_services(services, args):
    """Display services list."""
    if args.json:
        print(json.dumps(services, indent=2))
        return

    if not services:
        print("No services found.")
        return

    print(f"{'UNIT':<45} {'LOAD':<8} {'ACTIVE':<8} SUB")
    print("-" * 75)
    for s in services:
        unit = s["unit"][:44]
        status_symbols = {
            "active": "\033[32m●\033[0m",
            "failed": "\033[31m●\033[0m",
            "inactive": "\033[90m○\033[0m",
        }
        sym = status_symbols.get(s["active"], "?")
        print(f"{sym} {unit:<43} {s['load']:<8} {s['active']:<8} {s.get('desc', '')}")


def main():
    parser = argparse.ArgumentParser(
        description="Check systemd service status."
    )
    parser.add_argument("service", nargs="?", help="Service name to check")
    parser.add_argument("--failed", action="store_true", help="Show failed services only")
    parser.add_argument("--all", action="store_true", help="Show all services (including inactive)")
    parser.add_argument("--user", action="store_true", help="Check user services")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--logs", action="store_true", help="Show recent logs for service")
    parser.add_argument("--lines", type=int, default=20, help="Number of log lines (default: 20)")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")

    args = parser.parse_args()

    try:
        if args.service:
            if args.logs or args.follow:
                cmd_logs(args.service, args)
            else:
                cmd_check_service(args.service, args)
        elif args.failed:
            services = cmd_failed(args)
            display_services(services, args)
        else:
            services = cmd_list_all(args)
            display_services(services, args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
