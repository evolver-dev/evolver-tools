"""TUI mode for Dev Dashboard — curses-based auto-refreshing dashboard."""

import curses
import os
import shutil
import subprocess
import time
from datetime import timedelta

import psutil


# ── Color pairs ──────────────────────────────────────────────────────────────

CP_HEADER = 1
CP_TITLE = 2
CP_GREEN = 3
CP_YELLOW = 4
CP_RED = 5
CP_CYAN = 6
CP_DIM = 7
CP_BOLD = 8
CP_WHITE = 9
CP_BAR_GREEN = 10
CP_BAR_YELLOW = 11
CP_BAR_RED = 12


def _init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_TITLE, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(CP_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(CP_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_RED, curses.COLOR_RED, -1)
    curses.init_pair(CP_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_DIM, 8, -1)  # dark gray
    curses.init_pair(CP_BOLD, curses.COLOR_WHITE, -1)
    curses.init_pair(CP_WHITE, curses.COLOR_WHITE, -1)
    curses.init_pair(CP_BAR_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(CP_BAR_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_BAR_RED, curses.COLOR_RED, -1)


def _color_pair(val, warn=50, crit=80):
    if val >= crit:
        return CP_RED
    elif val >= warn:
        return CP_YELLOW
    return CP_GREEN


# ── Data collectors ──────────────────────────────────────────────────────────

def _run_git(*args):
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", "error", -1


def collect_git():
    out, _, rc = _run_git("rev-parse", "--is-inside-work-tree")
    if rc != 0:
        return None
    info = {}
    branch, _, _ = _run_git("rev-parse", "--abbrev-ref", "HEAD")
    info["branch"] = branch or "(detached)"
    lc, _, _ = _run_git("log", "-1", "--format=%h %s (%ar)")
    info["last_commit"] = lc or "(no commits)"
    st, _, _ = _run_git("status", "--porcelain")
    lines = [l for l in st.split("\n") if l] if st else []
    info["staged"] = sum(1 for l in lines if l[0] != " " and l[0] != "?" and l[1] == " ")
    info["modified"] = sum(1 for l in lines if l[1] != " " and l[0] != "?" and l[1] != "?")
    info["untracked"] = sum(1 for l in lines if l.startswith("??"))
    aah, _, _ = _run_git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    if aah:
        parts = aah.split()
        info["ahead"] = int(parts[0]) if parts else 0
        info["behind"] = int(parts[1]) if len(parts) > 1 else 0
    else:
        info["ahead"] = 0
        info["behind"] = 0
    return info


def collect_system():
    cpu = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    delta = timedelta(seconds=time.time() - psutil.boot_time())
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    mins, _ = divmod(rem, 60)
    if days:
        uptime = f"{days}d {hours}h {mins}m"
    else:
        uptime = f"{hours}h {mins}m"
    return {
        "cpu": cpu,
        "mem_pct": mem.percent,
        "mem_used": mem.used,
        "mem_total": mem.total,
        "disk_pct": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "uptime": uptime,
    }


def collect_ports():
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
    seen = set()
    deduped = []
    for r in results:
        if r[0] not in seen:
            seen.add(r[0])
            deduped.append(r)
    return sorted(deduped, key=lambda x: x[0])


COMMON_PORTS = {80, 3000, 4000, 4200, 5000, 5173, 8000, 8080, 8443, 8888, 9000, 9090, 3001, 3002}


def collect_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
    return procs[:8]


def _human_bytes(b):
    for unit in ("B", "K", "M", "G", "T"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}P"


def _bar_str(pct, width=16):
    filled = int(round(pct / 100 * width))
    filled = max(0, min(filled, width))
    empty = width - filled
    return "█" * filled + "░" * empty


# ── Panel drawing ────────────────────────────────────────────────────────────

def _draw_panel(stdscr, y, x, width, title, lines, header_cp=CP_HEADER):
    """Draw a bordered panel with title and list of (text, color_pair) tuples."""
    height = len(lines) + 2  # border top + bottom
    max_y, max_w = stdscr.getmaxyx()

    if y + height >= max_y or x + width >= max_w:
        return height  # clipped

    # Top border with title
    try:
        stdscr.addstr(y, x, "┌", curses.color_pair(CP_DIM))
        title_str = f" {title} "
        avail = width - 2
        tl = len(title_str)
        if tl < avail:
            stdscr.addstr(f"{title_str}─" * (avail - tl), curses.color_pair(CP_DIM))
            stdscr.addstr("┐", curses.color_pair(CP_DIM))
        else:
            stdscr.addstr("─" * (avail), curses.color_pair(CP_DIM))
            stdscr.addstr("┐", curses.color_pair(CP_DIM))
    except curses.error:
        pass

    # Body lines
    for i, (text, cp) in enumerate(lines):
        ly = y + 1 + i
        if ly >= max_y - 1:
            break
        try:
            stdscr.addstr(ly, x, "│", curses.color_pair(CP_DIM))
            # Truncate text to fit
            display = text[: width - 4] if len(text) > width - 4 else text.ljust(width - 4)
            stdscr.addstr(display, curses.color_pair(cp) | curses.A_BOLD if cp == CP_BOLD else curses.color_pair(cp))
            # Fill remaining
            pad = width - 2 - len(display) - 1
            if pad > 0:
                stdscr.addstr(" " * pad)
            stdscr.addstr("│", curses.color_pair(CP_DIM))
        except curses.error:
            pass

    # Bottom border
    bottom_y = y + height - 1
    if bottom_y < max_y:
        try:
            stdscr.addstr(bottom_y, x, "└", curses.color_pair(CP_DIM))
            stdscr.addstr("─" * (width - 2), curses.color_pair(CP_DIM))
            stdscr.addstr("┘", curses.color_pair(CP_DIM))
        except curses.error:
            pass

    return height


def _make_git_lines(info):
    if info is None:
        return [("  (not a git repo)", CP_DIM)]
    lines = []
    branch = info.get("branch", "?")
    lines.append((f"  Branch:  {branch}", CP_CYAN))

    staged = info.get("staged", 0)
    modified = info.get("modified", 0)
    untracked = info.get("untracked", 0)
    lines.append((f"  Staged:  {staged}", CP_GREEN if staged == 0 else CP_YELLOW))
    lines.append((f"  Modif:   {modified}", CP_GREEN if modified == 0 else CP_RED))
    lines.append((f"  Untrack: {untracked}", CP_GREEN if untracked == 0 else CP_YELLOW))

    ahead = info.get("ahead", 0)
    behind = info.get("behind", 0)
    if ahead or behind:
        a = f"↑{ahead}" if ahead else ""
        b = f"↓{behind}" if behind else ""
        lines.append((f"  ─ {a} {b}".strip(), CP_DIM))
    else:
        lines.append((f"  up to date", CP_DIM))

    lc = info.get("last_commit", "")
    if lc:
        lines.append((f"  {lc}", CP_DIM))
    return lines


def _make_sys_lines(sysinfo):
    cpu = sysinfo["cpu"]
    cpu_c = _color_pair(cpu)
    lines = []
    lines.append((f"  CPU: {cpu:5.1f}%  {_bar_str(cpu, 14)}", cpu_c))

    mp = sysinfo["mem_pct"]
    mu = _human_bytes(sysinfo["mem_used"])
    mt = _human_bytes(sysinfo["mem_total"])
    m_c = _color_pair(mp)
    lines.append((f"  MEM: {mp:5.1f}%  {_bar_str(mp, 14)}  {mu}/{mt}", m_c))

    dp = sysinfo["disk_pct"]
    du = _human_bytes(sysinfo["disk_used"])
    dt = _human_bytes(sysinfo["disk_total"])
    d_c = _color_pair(dp, warn=70, crit=90)
    lines.append((f"  DSK: {dp:5.1f}%  {_bar_str(dp, 14)}  {du}/{dt}", d_c))

    lines.append((f"  Up: {sysinfo['uptime']}", CP_DIM))
    return lines


def _make_port_lines(all_ports):
    if not all_ports:
        return [("  (no ports / permission denied)", CP_DIM)]

    common = [p for p in all_ports if p[0] in COMMON_PORTS]
    others = [p for p in all_ports if p not in common]

    lines = []
    for port, pid, name in common[:6]:
        lines.append((f"  {port:5d}  {name}  (pid={pid})", CP_GREEN))
    if len(common) > 6:
        lines.append((f"  ... +{len(common)-6} more common", CP_DIM))

    if others:
        for port, pid, name in others[:3]:
            lines.append((f"  {port:5d}  {name}", CP_DIM))
        if len(others) > 3:
            lines.append((f"  ... +{len(others)-3} more", CP_DIM))

    if not common and not others:
        lines.append((f"  {len(all_ports)} sockets total", CP_DIM))

    lines.append((f"  Total: {len(all_ports)} listening", CP_DIM))
    return lines


def _make_proc_lines(procs):
    if not procs:
        return [("  (no data)", CP_DIM)]
    lines = []
    for p in procs:
        pid = p.get("pid", "?")
        cpu = p.get("cpu_percent", 0) or 0
        mem = p.get("memory_percent", 0) or 0
        name = p.get("name", "?")[:18]
        cpu_c = CP_RED if cpu > 50 else CP_YELLOW if cpu > 20 else CP_GREEN
        lines.append((f"  {pid:>6}  {cpu:5.1f}%  {mem:5.1f}%  {name}", cpu_c))
    return lines


def _make_recent_files_lines():
    """Scan recent files from home dir — last 5 modified files."""
    home = os.path.expanduser("~")
    files = []
    try:
        for root, dirs, fnames in os.walk(home):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") or d in (".config", ".git")]
            for fn in fnames:
                if fn.startswith(".") or fn.endswith((".pyc", ".o", ".so")):
                    continue
                fp = os.path.join(root, fn)
                try:
                    mtime = os.path.getmtime(fp)
                    files.append((mtime, fp))
                except OSError:
                    continue
            if len(files) >= 50:
                break
    except OSError:
        pass

    files.sort(reverse=True)
    lines = []
    for _, fp in files[:5]:
        name = os.path.basename(fp)
        dname = os.path.dirname(fp)
        short_dir = dname.replace(home, "~") if dname.startswith(home) else dname
        lines.append((f"  {name:20}  {short_dir[:30]}", CP_DIM))
    if not lines:
        lines.append(("  (no recent files)", CP_DIM))
    return lines


# ── Main TUI Loop ────────────────────────────────────────────────────────────

def run_tui():
    try:
        curses.wrapper(_main_loop)
    except KeyboardInterrupt:
        pass


def _main_loop(stdscr):
    _init_colors()
    curses.curs_set(0)  # hide cursor
    stdscr.nodelay(1)  # non-blocking getch

    refresh_interval = 3
    last_tick = 0

    # Data cache
    git_info = None
    sys_info = None
    port_data = []
    proc_data = []

    while True:
        now = time.monotonic()
        if now - last_tick >= refresh_interval:
            git_info = collect_git()
            sys_info = collect_system()
            port_data = collect_ports()
            proc_data = collect_processes()
            last_tick = now

        max_y, max_w = stdscr.getmaxyx()
        stdscr.erase()

        # Title bar
        title_text = " DEV DASHBOARD  (q: quit, r: refresh now) "
        try:
            stdscr.addstr(0, 0, title_text, curses.color_pair(CP_TITLE))
            stdscr.addstr(
                f"  {time.strftime('%H:%M:%S')}  |  auto-refresh every {refresh_interval}s",
                curses.color_pair(CP_DIM),
            )
            stdscr.addstr(" " * (max_w - 1), curses.color_pair(CP_DIM))
        except curses.error:
            pass

        # Calculate panel layout
        p_width = max(42, max_w // 2 - 2)
        left_x = 1
        right_x = left_x + p_width + 2

        y = 2  # start below title

        # ── LEFT COLUMN ──

        # GIT PANEL
        git_lines = _make_git_lines(git_info)
        h = _draw_panel(stdscr, y, left_x, p_width, " GIT ", git_lines)
        y += h + 1

        # SYSTEM PANEL
        sys_lines = _make_sys_lines(sys_info) if sys_info else [("(loading...)", CP_DIM)]
        h = _draw_panel(stdscr, y, left_x, p_width, " SYSTEM ", sys_lines)
        y += h + 1

        # RECENT FILES PANEL
        recent_lines = _make_recent_files_lines()
        # Only draw if room
        if y + len(recent_lines) + 3 < max_y:
            h = _draw_panel(stdscr, y, left_x, p_width, " RECENT FILES ", recent_lines)
            y += h + 1

        # ── RIGHT COLUMN ──

        ry = 2
        # PROCESSES PANEL
        proc_lines = _make_proc_lines(proc_data)
        h = _draw_panel(stdscr, ry, right_x, p_width, " TOP PROCESSES ", proc_lines)
        ry += h + 1

        # PORTS PANEL
        port_lines = _make_port_lines(port_data)
        h = _draw_panel(stdscr, ry, right_x, p_width, " OPEN PORTS ", port_lines)
        ry += h + 1

        # Footer
        footer_y = max_y - 1
        try:
            stdscr.addstr(footer_y, 0, " q: quit  r: refresh  ↑↓: scroll", curses.color_pair(CP_DIM))
        except curses.error:
            pass

        stdscr.refresh()

        # ── Handle input ──
        try:
            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == ord("r"):
                last_tick = 0  # force refresh on next loop
        except OSError:
            pass

        # Sleep a bit to avoid busy-wait
        time.sleep(0.2)
