#!/usr/bin/env python3
"""process-kill — Kill processes by name, port, or user with confirmation."""
import sys
import os
import argparse
import signal
import subprocess
import re


def find_procs_by_name(name):
    """Find processes by name using ps."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error running ps: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return []

        procs = []
        for line in lines[1:]:
            parts = line.split(None, 10)
            if len(parts) < 11:
                continue
            user = parts[0]
            pid = parts[1]
            cmd = parts[10]
            if name.lower() in cmd.lower():
                procs.append({
                    "pid": pid,
                    "user": user,
                    "cpu": parts[2],
                    "mem": parts[3],
                    "cmd": cmd[:80],
                })
        return procs
    except FileNotFoundError:
        print("Error: ps command not found", file=sys.stderr)
        sys.exit(1)


def find_procs_by_port(port):
    """Find processes listening on a port using lsof or ss."""
    try:
        # Try lsof first
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            procs = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    procs.append({
                        "pid": parts[1],
                        "user": parts[2],
                        "cmd": parts[0],
                        "fd": parts[3],
                        "type": parts[4],
                        "device": parts[7],
                        "name": parts[8],
                    })
            return procs

        # Fallback to ss
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            procs = []
            pid_pattern = re.compile(r"pid=(\d+)")
            for line in lines[1:]:
                if f":{port}" in line:
                    pid_match = pid_pattern.search(line)
                    if pid_match:
                        pid = pid_match.group(1)
                        procs.append({
                            "pid": pid,
                            "user": "?",
                            "cmd": line.strip(),
                        })
            return procs

        print("Error: Could not find process by port (need lsof or ss)", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: lsof not found. Install lsof or try with --name.", file=sys.stderr)
        sys.exit(1)


def find_procs_by_user(user):
    """Find processes by user."""
    try:
        result = subprocess.run(
            ["ps", "-u", user, "aux"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error: User '{user}' not found or ps failed", file=sys.stderr)
            sys.exit(1)

        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return []

        procs = []
        for line in lines[1:]:
            parts = line.split(None, 10)
            if len(parts) < 11:
                continue
            procs.append({
                "pid": parts[1],
                "user": parts[0],
                "cpu": parts[2],
                "mem": parts[3],
                "cmd": parts[10][:80],
            })
        return procs
    except FileNotFoundError:
        print("Error: ps command not found", file=sys.stderr)
        sys.exit(1)


def list_matching_procs(procs):
    """Display matching processes in a table."""
    if not procs:
        return
    print(f"{'PID':<8} {'USER':<10} {'CPU%':<6} {'MEM%':<6} COMMAND")
    print("-" * 80)
    for p in procs:
        cpu = p.get("cpu", "?")
        mem = p.get("mem", "?")
        print(f"{p['pid']:<8} {p['user']:<10} {cpu:<6} {mem:<6} {p['cmd']}")


def kill_procs(procs, sig, force):
    """Kill processes with given signal."""
    if not procs:
        print("No matching processes.")
        return

    list_matching_procs(procs)
    print(f"\n{len(procs)} process(es) will be killed with signal {sig} ({sig_name(sig)})")

    if not force:
        try:
            response = input("Proceed? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if response not in ("y", "yes"):
            print("Aborted.")
            return

    killed = 0
    failed = 0
    for p in procs:
        try:
            os.kill(int(p["pid"]), sig)
            print(f"  Killed PID {p['pid']} ({p['cmd'][:40]})")
            killed += 1
        except ProcessLookupError:
            print(f"  PID {p['pid']} already gone")
            killed += 1
        except PermissionError:
            print(f"  Permission denied for PID {p['pid']}", file=sys.stderr)
            failed += 1
        except OSError as e:
            print(f"  Error killing PID {p['pid']}: {e}", file=sys.stderr)
            failed += 1

    print(f"\nResult: {killed} killed, {failed} failed")


def sig_name(sig):
    """Get signal name."""
    names = {signal.SIGTERM: "SIGTERM", signal.SIGKILL: "SIGKILL", signal.SIGHUP: "SIGHUP",
             signal.SIGINT: "SIGINT", signal.SIGQUIT: "SIGQUIT", signal.SIGSTOP: "SIGSTOP",
             signal.SIGCONT: "SIGCONT"}
    return names.get(sig, str(sig))


def parse_signal(sig_str):
    """Parse signal name or number."""
    if not sig_str:
        return signal.SIGTERM
    sig_str = sig_str.upper()
    if sig_str.isdigit():
        return int(sig_str)
    sig_map = {"TERM": signal.SIGTERM, "KILL": signal.SIGKILL, "HUP": signal.SIGHUP,
               "INT": signal.SIGINT, "QUIT": signal.SIGQUIT, "STOP": signal.SIGSTOP,
               "CONT": signal.SIGCONT}
    if sig_str.startswith("SIG"):
        sig_str = sig_str[3:]
    return sig_map.get(sig_str, signal.SIGTERM)


def main():
    parser = argparse.ArgumentParser(
        description="Kill processes by name, port, or user."
    )
    parser.add_argument("--name", help="Kill processes by name match")
    parser.add_argument("--port", type=int, help="Kill processes listening on port")
    parser.add_argument("--user", help="Kill all processes for a user")
    parser.add_argument("--signal", "-s", default="TERM", help="Signal to send (default: TERM)")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    parser.add_argument("--list", action="store_true", help="Only list matching processes, don't kill")

    args = parser.parse_args()

    if not args.name and not args.port and not args.user:
        print("Error: Specify --name, --port, or --user", file=sys.stderr)
        sys.exit(1)

    sig = parse_signal(args.signal)
    procs = []

    try:
        if args.name:
            procs = find_procs_by_name(args.name)
        elif args.port:
            procs = find_procs_by_port(args.port)
        elif args.user:
            procs = find_procs_by_user(args.user)
    except Exception as e:
        print(f"Error finding processes: {e}", file=sys.stderr)
        sys.exit(1)

    if not procs:
        print("No matching processes found.")
        return

    if args.list:
        list_matching_procs(procs)
        print(f"\nTotal: {len(procs)} process(es)")
        return

    kill_procs(procs, sig, args.force)


if __name__ == "__main__":
    main()
