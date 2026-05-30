"""CLI mode for Dev Dashboard — git status, system metrics, ports, and processes."""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

try:
    from dev_dashboard.tui import run_tui
except ImportError:
    run_tui = None


# ── ANSI Colors ──────────────────────────────────────────────────────────────

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"
    CLEAR_LINE = "\033[2K"


def colorize(text, color, bold=False):
    prefix = Colors.BOLD if bold else ""
    return f"{prefix}{color}{text}{Colors.RESET}"


def pct_color(val, warn=50, crit=80):
    if val >= crit:
        return Colors.RED
    elif val >= warn:
        return Colors.YELLOW
    return Colors.GREEN


def ok_fail(ok):
    return colorize("OK", Colors.GREEN) if ok else colorize("FAIL", Colors.RED)


# ── Git Helpers ──────────────────────────────────────────────────────────────

def _run_git(*args, cwd=None):
    """Run a git command silently. Returns (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            timeout=10,
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", "git not found or timeout", -1


def get_git_status(cwd=None):
    """Return a dict of git info, or empty dict if not a git repo."""
    out, _, rc = _run_git("rev-parse", "--is-inside-work-tree", cwd=cwd)
    if rc != 0:
        return {}

    info: dict = {}

    # Branch
    branch, _, _ = _run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    info["branch"] = branch or "(detached HEAD)"

    # Last commit
    log_out, _, _ = _run_git("log", "-1", "--format=%h %s (%ar)", cwd=cwd)
    info["last_commit"] = log_out or "(no commits)"

    # Counts
    status_out, _, _ = _run_git("status", "--porcelain", cwd=cwd)
    lines = [l for l in status_out.split("\n") if l] if status_out else []
    info["staged"] = sum(1 for l in lines if l[0] != " " and l[0] != "?" and l[1] == " ")
    info["modified"] = sum(1 for l in lines if l[1] != " " and l[0] != "?" and l[1] != "?")
    info["untracked"] = sum(1 for l in lines if l.startswith("??"))
    info["total_changes"] = len(lines)

    # Ahead / behind
    aah_out, _, _ = _run_git(
        "rev-list", "--left-right", "--count", "HEAD...@{u}", cwd=cwd
    )
    if aah_out:
        parts = aah_out.split()
        info["ahead"] = int(parts[0]) if parts else 0
        info["behind"] = int(parts[1]) if len(parts) > 1 else 0
    else:
        info["ahead"] = 0
        info["behind"] = 0

    return info


# ── System Helpers ───────────────────────────────────────────────────────────

def get_uptime():
    delta = timedelta(seconds=time.time() - psutil.boot_time())
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    mins, _ = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {mins}m"
    return f"{hours}h {mins}m"


def get_system_info():
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": cpu,
        "memory_percent": mem.percent,
        "memory_used": mem.used,
        "memory_total": mem.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "uptime": get_uptime(),
    }


def _human_bytes(b):
    for unit in ("B", "K", "M", "G", "T"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}P"


# ── Ports Helper ─────────────────────────────────────────────────────────────

COMMON_PORTS = [80, 3000, 4000, 4200, 5000, 5173, 8000, 8080, 8443, 8888, 9000, 9090, 3001, 3002]


def get_listening_ports():
    """Return sorted list of (port, pid, process_name) that are listening."""
    results = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "LISTEN" and conn.laddr:
                port = conn.laddr.port
                if not conn.pid:
                    results.append((port, 0, "unknown"))
                    continue
                try:
                    proc = psutil.Process(conn.pid)
                    name = proc.name() or "unknown"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    name = "unknown"
                results.append((port, conn.pid, name))
    except (psutil.AccessDenied, PermissionError):
        pass
    # Deduplicate by port — keep first
    seen = set()
    deduped = []
    for r in results:
        if r[0] not in seen:
            seen.add(r[0])
            deduped.append(r)
    return sorted(deduped, key=lambda x: x[0])


# ── Processes Helper ─────────────────────────────────────────────────────────

def get_top_processes(count=5):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
    return procs[:count]


# ── Display Functions ────────────────────────────────────────────────────────

def _print_header(title):
    term_width = shutil.get_terminal_size().columns
    print()
    print(colorize(f"═══ {title} ═══", Colors.CYAN, bold=True))
    print(colorize("━" * min(term_width, 60), Colors.DIM))


def show_git():
    info = get_git_status()
    _print_header("GIT STATUS")
    if not info:
        print(colorize("  Not a git repository.", Colors.YELLOW))
        return

    branch = info.get("branch", "?")
    print(f"  {colorize('Branch:', Colors.BOLD)} {colorize(branch, Colors.BLUE)}")

    staged = info.get("staged", 0)
    modified = info.get("modified", 0)
    untracked = info.get("untracked", 0)

    c_staged = colorize(str(staged), Colors.GREEN) if staged == 0 else colorize(str(staged), Colors.YELLOW)
    c_mod = colorize(str(modified), Colors.GREEN) if modified == 0 else colorize(str(modified), Colors.RED)
    c_unt = colorize(str(untracked), Colors.GREEN) if untracked == 0 else colorize(str(untracked), Colors.YELLOW)

    print(f"  {colorize('Staged:', Colors.BOLD)}    {c_staged}")
    print(f"  {colorize('Modified:', Colors.BOLD)}   {c_mod}")
    print(f"  {colorize('Untracked:', Colors.BOLD)}  {c_unt}")

    ahead = info.get("ahead", 0)
    behind = info.get("behind", 0)
    parts = []
    if ahead:
        parts.append(colorize(f"↑ {ahead}", Colors.GREEN))
    if behind:
        parts.append(colorize(f"↓ {behind}", Colors.RED))
    if parts:
        print(f"  {colorize('Ahead/Behind:', Colors.BOLD)} {' '.join(parts)}")
    else:
        print(f"  {colorize('Ahead/Behind:', Colors.BOLD)} {colorize('up to date', Colors.DIM)}")

    lc = info.get("last_commit", "")
    if lc:
        print(f"  {colorize('Last commit:', Colors.BOLD)} {lc}")


def show_system():
    sysinfo = get_system_info()
    _print_header("SYSTEM")

    cpu = sysinfo["cpu"]
    cpu_c = pct_color(cpu)
    bar = _bar(cpu, 20)
    print(f"  {colorize('CPU:', Colors.BOLD):12} {colorize(f'{cpu:5.1f}%', cpu_c)}{Colors.RESET} {bar}")

    mp = sysinfo["memory_percent"]
    mu = _human_bytes(sysinfo["memory_used"])
    mt = _human_bytes(sysinfo["memory_total"])
    m_c = pct_color(mp)
    mbar = _bar(mp, 20)
    print(f"  {colorize('Memory:', Colors.BOLD):12} {colorize(f'{mp:5.1f}%', m_c)}{Colors.RESET} {mbar}  {mu} / {mt}")

    dp = sysinfo["disk_percent"]
    du = _human_bytes(sysinfo["disk_used"])
    dt = _human_bytes(sysinfo["disk_total"])
    d_c = pct_color(dp, warn=70, crit=90)
    dbar = _bar(dp, 20)
    print(f"  {colorize('Disk:', Colors.BOLD):12} {colorize(f'{dp:5.1f}%', d_c)}{Colors.RESET} {dbar}  {du} / {dt}")

    print(f"  {colorize('Uptime:', Colors.BOLD)}   {sysinfo['uptime']}")


def _bar(pct, width=20):
    filled = int(round(pct / 100 * width))
    filled = max(0, min(filled, width))
    empty = width - filled
    c = pct_color(pct)
    return colorize("█" * filled, c) + colorize("░" * empty, Colors.DIM)


def show_ports():
    _print_header("OPEN PORTS")

    all_ports = get_listening_ports()

    # Filter to common ports + show all if --verbose
    interesting = [p for p in all_ports if p[0] in COMMON_PORTS]
    others = [p for p in all_ports if p[0] not in COMMON_PORTS]

    if not all_ports:
        print(colorize("  No listening ports found (try with sudo/root).", Colors.YELLOW))
        return

    if interesting:
        print(f"  {colorize('COMMON PORTS:', Colors.BOLD)}")
        for port, pid, name in interesting:
            label = f"  {colorize(name, Colors.CYAN)}"
            print(f"    {colorize(f'{port:5d}', Colors.GREEN)}  {label}  (pid={pid})")

    if others:
        print(f"\n  {colorize(f'OTHER PORTS ({len(others)}):', Colors.DIM)}")
        for port, pid, name in others[:10]:
            print(f"    {colorize(f'{port:5d}', Colors.DIM)}  {colorize(name, Colors.DIM)}  (pid={pid})")
        if len(others) > 10:
            print(f"    {colorize(f'... and {len(others)-10} more', Colors.DIM)}")

    print(f"\n  {colorize(f'Total listening sockets: {len(all_ports)}', Colors.DIM)}")


def show_processes():
    _print_header("TOP PROCESSES (by CPU)")

    procs = get_top_processes(5)
    if not procs:
        print(colorize("  No process info available.", Colors.YELLOW))
        return

    pid_hdr = colorize(f"{'PID':>7}", Colors.BOLD)
    cpu_hdr = colorize(f"{'CPU%':>6}", Colors.BOLD)
    mem_hdr = colorize(f"{'MEM%':>6}", Colors.BOLD)
    name_hdr = colorize("NAME", Colors.BOLD)
    print(f"  {pid_hdr}  {cpu_hdr}  {mem_hdr}  {name_hdr}")
    print(f"  {colorize('─' * 42, Colors.DIM)}")

    for p in procs:
        pid = p.get("pid", "?")
        cpu = p.get("cpu_percent", 0) or 0
        mem = p.get("memory_percent", 0) or 0
        name = p.get("name", "?")
        cpu_c = Colors.RED if cpu > 50 else Colors.YELLOW if cpu > 20 else Colors.GREEN
        mem_c = Colors.RED if mem > 50 else Colors.YELLOW if mem > 20 else Colors.GREEN
        print(f"  {colorize(f'{pid:>7}', Colors.DIM)}  "
              f"{colorize(f'{cpu:5.1f}%', cpu_c)}  "
              f"{colorize(f'{mem:5.1f}%', mem_c)}  "
              f"{colorize(name, Colors.CYAN)}")


def show_all():
    print()
    print(colorize("╔══════════════════════════════════════════════════════╗", Colors.CYAN))
    print(colorize("║         DEV DASHBOARD  —  Developer Overview        ║", Colors.CYAN))
    print(colorize("╚══════════════════════════════════════════════════════╝", Colors.CYAN))
    show_git()
    show_system()
    show_processes()
    show_ports()
    print()


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="dev-dashboard",
        description="One-stop terminal dashboard for developers.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="all",
        choices=["git", "sys", "system", "ports", "processes", "proc", "all"],
        help="What to display (default: all)",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch TUI (curses) mode with auto-refresh",
    )
    parser.add_argument(
        "--watch", "-w",
        type=int,
        metavar="SEC",
        help="Repeat CLI mode every N seconds (Ctrl+C to stop)",
    )

    args = parser.parse_args()

    # TUI mode
    if args.tui:
        if run_tui:
            run_tui()
        else:
            print(
                colorize(
                    "Error: TUI module not available (curses import failed).",
                    Colors.RED,
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return

    # Normalize mode name
    mode = args.mode
    if mode == "system":
        mode = "sys"
    if mode in ("processes", "proc"):
        mode = "processes"

    # One-shot or watch
    if args.watch:
        try:
            while True:
                _dispatch(mode)
                print(colorize(f"\n  Refreshing in {args.watch}s... (Ctrl+C to stop)", Colors.DIM))
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print()
            sys.exit(0)
    else:
        _dispatch(mode)


def _dispatch(mode):
    if mode == "git":
        show_git()
    elif mode == "sys":
        show_system()
    elif mode == "ports":
        show_ports()
    elif mode == "processes":
        show_processes()
    else:
        show_all()
