#!/usr/bin/env python3
"""
sysmon — 终端系统监控仪
实时显示 CPU、内存、磁盘、进程、网络、uptime
使用 curses TUI 渲染
"""

import curses
import time
import os
import socket
import subprocess
from datetime import datetime, timedelta

try:
    import psutil
except ImportError:
    print("sysmon requires psutil. Install it with: pip install psutil")
    print("Or install full evolver-tools with: pip install evolver-tools[sysmon]")
    raise SystemExit(1)

def get_hostname():
    try:
        return socket.gethostname()
    except:
        return "unknown"

def get_uptime():
    try:
        with open('/proc/uptime') as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        parts.append(f"{mins}m")
        return ''.join(parts)
    except:
        return "N/A"

def get_sysinfo():
    return {
        'hostname': get_hostname(),
        'uptime': get_uptime(),
        'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%m/%d %H:%M'),
    }

def get_cpu():
    return {
        'percent': psutil.cpu_percent(interval=0.1),
        'per_cpu': psutil.cpu_percent(interval=0.05, percpu=True),
        'count': psutil.cpu_count(),
        'freq': psutil.cpu_freq(),
        'load': psutil.getloadavg(),
    }

def get_memory():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        'total': mem.total,
        'used': mem.used,
        'percent': mem.percent,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_percent': swap.percent,
    }

def get_disk():
    parts = []
    for p in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(p.mountpoint)
            parts.append({
                'mount': p.mountpoint,
                'device': p.device,
                'total': usage.total,
                'used': usage.used,
                'percent': usage.percent,
            })
        except:
            pass
    return parts

def get_network():
    net = psutil.net_io_counters()
    return {
        'sent': net.bytes_sent,
        'recv': net.bytes_recv,
    }

def get_top_processes(n=8):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = p.info
            if info['cpu_percent'] is None: continue
            procs.append({
                'pid': info['pid'],
                'name': info['name'][:20] if info['name'] else '?',
                'cpu': info['cpu_percent'],
                'mem': info['memory_percent'] or 0,
                'status': info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    return procs[:n]

def format_bytes(b):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}P"

def draw_bar(win, y, x, width, percent, color_pair=2):
    """Draw a horizontal bar"""
    fill = int(width * percent / 100)
    bar = '█' * fill + '░' * (width - fill)
    try:
        win.addstr(y, x, bar[:width], curses.color_pair(color_pair))
    except:
        pass

def main(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # headers
    curses.init_pair(2, curses.COLOR_GREEN, -1)   # good
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # warning
    curses.init_pair(4, curses.COLOR_RED, -1)     # critical
    curses.init_pair(5, curses.COLOR_WHITE, -1)   # normal
    curses.init_pair(6, curses.COLOR_MAGENTA, -1) # labels

    prev_net = get_network()
    prev_time = time.time()

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        sysinfo = get_sysinfo()
        cpu = get_cpu()
        mem = get_memory()
        disks = get_disk()
        net = get_network()
        procs = get_top_processes()
        now = time.time()

        # Network rate
        dt = now - prev_time
        net_speed_sent = (net['sent'] - prev_net['sent']) / dt if dt > 0 else 0
        net_speed_recv = (net['recv'] - prev_net['recv']) / dt if dt > 0 else 0
        prev_net = net
        prev_time = now

        line = 0

        # ---- Header ----
        if line < h:
            stdscr.addstr(line, 2, f"╔══════════════════════════════════════╗", curses.color_pair(5))
            line += 1
        if line < h:
            stdscr.addstr(line, 2, f"║  sysmon — {sysinfo['hostname']:<15}  ║", curses.color_pair(1))
            line += 1
        if line < h:
            stdscr.addstr(line, 2, f"╚══════════════════════════════════════╝", curses.color_pair(5))
            line += 1

        # ---- Uptime & Load ----
        if line < h:
            stdscr.addstr(line, 2, f"Up {sysinfo['uptime']}  ", curses.color_pair(6))
            stdscr.addstr(f"(since {sysinfo['boot_time']})  ", curses.color_pair(5))
            stdscr.addstr(f"Load: {cpu['load'][0]:.2f} {cpu['load'][1]:.2f} {cpu['load'][2]:.2f}")
            line += 1

        line += 1  # blank

        # ---- CPU ----
        if line < h:
            stdscr.addstr(line, 2, "CPU", curses.color_pair(1))
            line += 1
        cpu_color = 2 if cpu['percent'] < 50 else (3 if cpu['percent'] < 80 else 4)
        if line < h:
            stdscr.addstr(line, 2, f" {cpu['percent']:5.1f}% ", curses.color_pair(cpu_color))
            draw_bar(stdscr, line, 12, min(w - 16, 30), cpu['percent'], cpu_color)
            if cpu['freq']:
                stdscr.addstr(f"  {cpu['freq'].current/1000:.1f}GHz")
            line += 1

        # Per-core
        if line < h:
            n_cols = min(4, cpu['count'])
            n_rows = (cpu['count'] + n_cols - 1) // n_cols
            for r in range(n_rows):
                if line >= h: break
                stdscr.addstr(line, 2, " ")
                for c in range(n_cols):
                    idx = r * n_cols + c
                    if idx >= len(cpu['per_cpu']): break
                    p = cpu['per_cpu'][idx]
                    pc = 2 if p < 50 else (3 if p < 80 else 4)
                    stdscr.addstr(f" [{idx}]", curses.color_pair(pc))
                    draw_bar(stdscr, line, 8 + c * 14, 8, p, pc)
                    stdscr.addstr(f"{p:4.0f}%", curses.color_pair(pc))
                line += 1

        line += 1

        # ---- Memory ----
        if line < h:
            stdscr.addstr(line, 2, "MEM", curses.color_pair(1))
            line += 1
        mem_color = 2 if mem['percent'] < 50 else (3 if mem['percent'] < 80 else 4)
        if line < h:
            used_s = format_bytes(mem['used'])
            total_s = format_bytes(mem['total'])
            stdscr.addstr(line, 2, f" {used_s:>7} / {total_s:<7}", curses.color_pair(mem_color))
            draw_bar(stdscr, line, 20, min(w - 28, 30), mem['percent'], mem_color)
            stdscr.addstr(f" {mem['percent']:.0f}%")
            line += 1

        if mem['swap_total'] > 0 and line < h:
            swap_s = format_bytes(mem['swap_used'])
            swap_t = format_bytes(mem['swap_total'])
            sw_color = 2 if mem['swap_percent'] < 50 else (3 if mem['swap_percent'] < 80 else 4)
            stdscr.addstr(line, 2, f" SWP {swap_s:>7} / {swap_t:<7}", curses.color_pair(sw_color))
            line += 1

        line += 1

        # ---- Disk ----
        if line < h:
            stdscr.addstr(line, 2, "DISK", curses.color_pair(1))
            line += 1
        for dsk in disks:
            if line >= h: break
            d_color = 2 if dsk['percent'] < 50 else (3 if dsk['percent'] < 80 else 4)
            mount = dsk['mount']
            if len(mount) > 8: mount = mount[:7] + '~'
            used_s = format_bytes(dsk['used'])
            total_s = format_bytes(dsk['total'])
            stdscr.addstr(line, 2, f" {mount:>8}", curses.color_pair(6))
            stdscr.addstr(f" {used_s:>7} / {total_s:<7}", curses.color_pair(d_color))
            draw_bar(stdscr, line, 30, min(w - 38, 25), dsk['percent'], d_color)
            stdscr.addstr(f" {dsk['percent']:.0f}%")
            line += 1

        line += 1

        # ---- Network ----
        if line < h:
            stdscr.addstr(line, 2, "NET", curses.color_pair(1))
            line += 1
        if line < h:
            stdscr.addstr(line, 4, f"↓ {format_bytes(net_speed_recv)}/s  ↑ {format_bytes(net_speed_sent)}/s", curses.color_pair(5))
            stdscr.addstr(f"   Total: ↓{format_bytes(net['recv'])}  ↑{format_bytes(net['sent'])}")
            line += 1

        line += 1

        # ---- Top Processes ----
        if line < h:
            stdscr.addstr(line, 2, "PROCESSES", curses.color_pair(1))
            line += 1
        if line < h:
            stdscr.addstr(line, 2, f" {'PID':>5}  {'CPU':>5}  {'MEM':>5}  STATUS  NAME", curses.color_pair(6))
            line += 1
        for proc in procs:
            if line >= h: break
            p_cpu_color = 2 if proc['cpu'] < 10 else (3 if proc['cpu'] < 30 else 4)
            stdscr.addstr(line, 2, f" {proc['pid']:>5}", curses.color_pair(5))
            stdscr.addstr(f"  {proc['cpu']:4.1f}%", curses.color_pair(p_cpu_color))
            stdscr.addstr(f"  {proc['mem']:4.1f}%", curses.color_pair(5))
            stdscr.addstr(f"  {proc['status'][:6]:<6}", curses.color_pair(6))
            stdscr.addstr(f"  {proc['name']}", curses.color_pair(5))
            line += 1

        # ---- Footer ----
        if line < h - 1:
            stdscr.addstr(h - 1, 2, f" {datetime.now().strftime('%H:%M:%S')}  |  q:quit  r:refresh", curses.color_pair(6))

        stdscr.refresh()

        # Wait for key with timeout (update interval ~1s)
        stdscr.timeout(1000)
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('r'):
            continue

def entry():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"sysmon error: {e}")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "sysmon",
    "func": "entry",
    "desc": 'Real-time system monitor (curses TUI)',
}

if __name__ == '__main__':
    entry()
