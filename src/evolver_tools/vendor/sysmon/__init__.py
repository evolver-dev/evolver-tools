#!/usr/bin/env python3
"""
sysmon-pro — 旗舰级终端系统监控仪
==================================
功能:
- 实时 TUI 监控 (CPU/内存/磁盘/网络/进程/温度)
- CLI 模式 (JSON 输出, CSV 导出, 单次快照)
- 告警阈值 (自定义 CPU/内存/磁盘阈值)
- 历史记录 (保存到 ~/.sysmon/history/)
- TUI 增强: 进程排序/搜索/kill
- 设备温度检测
- GPU 监控 (NVIDIA nvidia-smi)
- 网络连接追踪 (ss/端口)

Usage:
  evtool sysmon           # TUI 交互模式
  evtool sysmon --once    # 单次快照 (JSON)
  evtool sysmon --csv     # 单次快照 (CSV)
  evtool sysmon --watch   # 连续监控输出 (CLI)
  evtool sysmon --alert   # 告警模式 (阈值)
  evtool sysmon --history # 查看历史
"""

import curses
import time
import os
import socket
import json
import csv
import sys
import argparse
from datetime import datetime, timedelta

# ─── 可选依赖 ─────────────────────────────────────────────
try:
    import psutil
except ImportError:
    print("sysmon-pro requires psutil. Install with: pip install psutil")
    raise SystemExit(1)

# ─── 常量 ────────────────────────────────────────────────
HISTORY_DIR = os.path.expanduser("~/.sysmon/history")
ALERT_CONFIG_PATH = os.path.expanduser("~/.sysmon/alerts.json")
DEFAULT_ALERTS = {
    "cpu_percent": 90,
    "mem_percent": 85,
    "disk_percent": 90,
    "swap_percent": 80,
}
VERSION = "2.0.0"


# ═══════════════════════════════════════════════════════════
# 数据采集层
# ═══════════════════════════════════════════════════════════

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
        return ''.join(parts), seconds
    except:
        return "N/A", 0

def get_cpu():
    return {
        'percent': psutil.cpu_percent(interval=0.1),
        'per_cpu': psutil.cpu_percent(interval=0.05, percpu=True),
        'count': psutil.cpu_count(),
        'logical': psutil.cpu_count(logical=True),
        'freq': psutil.cpu_freq(),
        'load': psutil.getloadavg(),
        'stats': psutil.cpu_stats(),
        'times': psutil.cpu_times_percent(interval=0),
    }

def get_memory():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        'total': mem.total,
        'available': mem.available,
        'used': mem.used,
        'free': mem.free,
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
                'fstype': p.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
            })
        except:
            pass
    # Sort by mount for stable output, / first
    parts.sort(key=lambda d: (d['mount'] != '/', d['mount']))
    return parts

def get_network():
    net = psutil.net_io_counters()
    return {
        'sent': net.bytes_sent,
        'recv': net.bytes_recv,
        'packets_sent': net.packets_sent,
        'packets_recv': net.packets_recv,
        'errin': net.errin,
        'errout': net.errout,
    }

def get_network_interfaces():
    """Get per-interface stats."""
    stats = psutil.net_if_stats()
    io = psutil.net_io_counters(pernic=True)
    addrs = psutil.net_if_addrs()
    result = []
    for name in sorted(stats.keys()):
        s = stats[name]
        nic_io = io.get(name)
        nic_addrs = addrs.get(name, [])
        ip_addrs = [a.address for a in nic_addrs if a.family == socket.AF_INET]
        result.append({
            'name': name,
            'up': s.isup,
            'speed': s.speed,
            'mtu': s.mtu,
            'ips': ip_addrs,
            'bytes_sent': nic_io.bytes_sent if nic_io else 0,
            'bytes_recv': nic_io.bytes_recv if nic_io else 0,
        })
    return result

def get_temp():
    """采集温度 (仅 Linux)"""
    temps = {}
    try:
        for name, entries in psutil.sensors_temperatures().items():
            for entry in entries:
                label = entry.label or name
                temps[label] = entry.current
    except:
        pass
    return temps

def get_fans():
    """采集风扇转速"""
    try:
        fans = psutil.sensors_fans()
        return {name: [{'label': f.label or name, 'rpm': f.current} for f in entries]
                for name, entries in fans.items()}
    except:
        return {}

def get_gpu():
    """NVIDIA GPU 监控 (通过 nvidia-smi)"""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                gpus.append({
                    'index': parts[0],
                    'name': parts[1],
                    'gpu_util': int(parts[2]),
                    'mem_used': int(parts[3]),
                    'mem_total': int(parts[4]),
                    'temp': int(parts[5]),
                })
        return gpus
    except:
        return []

def get_top_processes(n=12, sort_by='cpu'):
    """获取 Top N 进程，支持多种排序。"""
    sort_key_map = {
        'cpu': 'cpu_percent',
        'mem': 'memory_percent',
        'pid': 'pid',
        'name': 'name',
    }
    key = sort_key_map.get(sort_by, 'cpu_percent')
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username', 'create_time']):
        try:
            info = p.info
            if info['cpu_percent'] is None: continue
            info['cpu_percent'] = info.get('cpu_percent', 0) or 0
            info['memory_percent'] = info.get('memory_percent', 0) or 0
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    reverse = key not in ('name', 'pid')
    procs.sort(key=lambda x: x.get(key, 0) or 0, reverse=reverse)
    return procs[:n]

def get_connections():
    """网络连接统计"""
    try:
        conns = psutil.net_connections(kind='inet')
        states = {}
        for c in conns:
            s = c.status or 'UNKNOWN'
            states[s] = states.get(s, 0) + 1
        return states
    except:
        return {}

def get_disks_io():
    """磁盘 I/O 统计"""
    try:
        return psutil.disk_io_counters(perdisk=False)
    except:
        return None

def collect_all():
    """一次采集所有数据返回 dict"""
    cpu = get_cpu()
    mem = get_memory()
    disks = get_disk()
    net = get_network()
    temp = get_temp()
    gpu = get_gpu()
    procs = get_top_processes()
    uptime_str, uptime_secs = get_uptime()
    boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
    net_ifaces = get_network_interfaces()
    conns = get_connections()

    return {
        'timestamp': datetime.now().isoformat(),
        'hostname': get_hostname(),
        'uptime': uptime_str,
        'uptime_seconds': uptime_secs,
        'boot_time': boot_time,
        'cpu': {
            'percent': cpu['percent'],
            'per_cpu': cpu['per_cpu'],
            'count': cpu['count'],
            'logical': cpu['logical'],
            'freq_mhz': cpu['freq'].current if cpu['freq'] else None,
            'load_1': cpu['load'][0],
            'load_5': cpu['load'][1],
            'load_15': cpu['load'][2],
        },
        'memory': {
            'total': mem['total'],
            'used': mem['used'],
            'available': mem['available'],
            'percent': mem['percent'],
            'swap_total': mem['swap_total'],
            'swap_used': mem['swap_used'],
            'swap_percent': mem['swap_percent'],
        },
        'disks': disks,
        'network': {
            'bytes_sent': net['sent'],
            'bytes_recv': net['recv'],
            'packets_sent': net['packets_sent'],
            'packets_recv': net['packets_recv'],
            'interfaces': net_ifaces,
        },
        'temperature': temp,
        'gpu': gpu,
        'connections': conns,
        'processes': [{
            'pid': p['pid'],
            'name': p['name'],
            'cpu_percent': p['cpu_percent'],
            'memory_percent': p['memory_percent'],
            'status': p['status'],
            'username': p.get('username', ''),
        } for p in procs],
    }


# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def format_bytes(b):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}P"

def load_alerts():
    """加载告警配置"""
    if not os.path.exists(ALERT_CONFIG_PATH):
        return DEFAULT_ALERTS.copy()
    try:
        with open(ALERT_CONFIG_PATH) as f:
            cfg = json.load(f)
            return {**DEFAULT_ALERTS, **cfg}
    except:
        return DEFAULT_ALERTS.copy()

def save_alerts(alerts):
    """保存告警配置"""
    os.makedirs(os.path.dirname(ALERT_CONFIG_PATH), exist_ok=True)
    with open(ALERT_CONFIG_PATH, 'w') as f:
        json.dump(alerts, f, indent=2)

def check_alerts(data):
    """检查所有阈值，返回告警列表 [(level, msg), ...]"""
    alerts = []
    cfg = load_alerts()

    cpu_pct = data['cpu']['percent']
    if cpu_pct >= cfg.get('cpu_percent', 90):
        alerts.append(('CRITICAL', f"CPU at {cpu_pct:.1f}% (threshold: {cfg['cpu_percent']}%)"))

    mem_pct = data['memory']['percent']
    if mem_pct >= cfg.get('mem_percent', 85):
        level = 'CRITICAL' if mem_pct >= 95 else 'WARNING'
        alerts.append((level, f"MEM at {mem_pct:.1f}% (threshold: {cfg['mem_percent']}%)"))

    for d in data['disks']:
        disk_pct = d['percent']
        if disk_pct >= cfg.get('disk_percent', 90):
            alerts.append(('WARNING', f"DISK {d['mount']} at {disk_pct:.1f}%"))

    swap_pct = data['memory']['swap_percent']
    if swap_pct >= cfg.get('swap_percent', 80):
        alerts.append(('WARNING', f"SWAP at {swap_pct:.1f}%"))

    return alerts

def save_history(data):
    """保存快照到历史目录"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(HISTORY_DIR, f"snapshot_{ts}.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def list_history(limit=10):
    """列出最近的历史快照"""
    if not os.path.isdir(HISTORY_DIR):
        return []
    files = sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')], reverse=True)
    result = []
    for fname in files[:limit]:
        path = os.path.join(HISTORY_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            result.append({
                'file': fname,
                'timestamp': data.get('timestamp', 'unknown'),
                'hostname': data.get('hostname', '?'),
                'cpu': data.get('cpu', {}).get('percent', 0),
                'mem': data.get('memory', {}).get('percent', 0),
            })
        except:
            result.append({'file': fname, 'timestamp': 'corrupt'})
    return result


# ═══════════════════════════════════════════════════════════
# TUI 模式
# ═══════════════════════════════════════════════════════════

def draw_bar(win, y, x, width, percent, color_pair=2):
    fill = int(width * percent / 100)
    bar = '█' * fill + '░' * (width - fill)
    try:
        win.addstr(y, x, bar[:width], curses.color_pair(color_pair))
    except:
        pass

def tui_mode():
    """TUI 交互模式"""
    def main(stdscr):
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        curses.init_pair(7, curses.COLOR_BLUE, -1)

        prev_net = get_network()
        prev_disk_io = get_disks_io()
        prev_time = time.time()
        sort_by = 'cpu'
        show_help = False
        log_messages = []
        record_history = False

        while True:
            h, w = stdscr.getmaxyx()
            if h < 10 or w < 40:
                stdscr.erase()
                stdscr.addstr(0, 0, "Terminal too small (min 40x10)")
                stdscr.refresh()
                stdscr.timeout(2000)
                if stdscr.getch() == ord('q'):
                    break
                continue

            stdscr.erase()

            data = collect_all()
            now = time.time()

            # Network rate
            dt = now - prev_time
            net = data['network']
            net_speed_sent = (net['bytes_sent'] - prev_net['sent']) / dt if dt > 0 else 0
            net_speed_recv = (net['bytes_recv'] - prev_net['recv']) / dt if dt > 0 else 0
            prev_net = {'sent': net['bytes_sent'], 'recv': net['bytes_recv']}

            # Disk I/O rate
            disk_io = get_disks_io()
            if prev_disk_io and disk_io:
                disk_read_speed = (disk_io.read_bytes - prev_disk_io.read_bytes) / dt if dt > 0 else 0
                disk_write_speed = (disk_io.write_bytes - prev_disk_io.write_bytes) / dt if dt > 0 else 0
            else:
                disk_read_speed = disk_write_speed = 0
            prev_disk_io = disk_io

            # Save history
            if record_history:
                save_history(data)

            # Check alerts
            alerts = check_alerts(data)
            for level, msg in alerts:
                log_messages.append(f"[{level}] {msg}")
            log_messages = log_messages[-5:]

            cpu = data['cpu']
            mem = data['memory']
            disks = data['disks']
            temp = data['temperature']
            gpu = data['gpu']
            conns = data['connections']
            hostname = data['hostname']
            uptime_str = data['uptime']
            boot_time_str = data.get('boot_time', '')[:16]

            line = 0
            title = f" sysmon-pro v{VERSION} — {hostname} "
            pad = max(0, (w - 2 - len(title)) // 2)

            # ── Header ──
            if line < h:
                stdscr.addstr(line, 0, "┌" + "─" * (w - 2) + "┐", curses.color_pair(5))
                line += 1
            if line < h:
                stdscr.addstr(line, 0, "│", curses.color_pair(5))
                stdscr.addstr(line, pad, title, curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(line, w - 1, "│", curses.color_pair(5))
                line += 1
            if line < h:
                stdscr.addstr(line, 0, "└" + "─" * (w - 2) + "┘", curses.color_pair(5))
                line += 1

            # ── Uptime & Load ──
            if line < h:
                stdscr.addstr(line, 2, f"Up {uptime_str}  ", curses.color_pair(6))
                load = cpu['load_1']
                load_color = 2 if load < 2 else (3 if load < 4 else 4)
                stdscr.addstr(f"Load: ", curses.color_pair(5))
                stdscr.addstr(f"{cpu['load_1']:.2f} {cpu['load_5']:.2f} {cpu['load_15']:.2f}", curses.color_pair(load_color))
                if temp:
                    t = list(temp.values())[0]
                    tc = 2 if t < 60 else (3 if t < 80 else 4)
                    stdscr.addstr(f"  Temp: ", curses.color_pair(5))
                    stdscr.addstr(f"{t:.0f}°C", curses.color_pair(tc))
                line += 1
            line += 1

            # ── CPU ──
            if line < h:
                stdscr.addstr(line, 2, "CPU", curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(f" ({cpu['count']}C/{cpu['logical']}T)", curses.color_pair(6))
                line += 1
            cpu_color = 2 if cpu['percent'] < 50 else (3 if cpu['percent'] < 80 else 4)
            bar_width = min(w - 30, 40)
            if line < h:
                stdscr.addstr(line, 2, f" {cpu['percent']:5.1f}% ", curses.color_pair(cpu_color))
                draw_bar(stdscr, line, 12, bar_width, cpu['percent'], cpu_color)
                bar_end = 12 + bar_width
                if cpu['freq_mhz']:
                    stdscr.addstr(line, bar_end + 1, f"{cpu['freq_mhz']/1000:.2f}GHz", curses.color_pair(5))
                line += 1

            # Per-core (compact: one row)
            if line < h:
                n_cols = min(w // 12, cpu['count'])
                for i in range(0, cpu['count'], n_cols):
                    if line >= h: break
                    stdscr.addstr(line, 2, " ")
                    for j in range(n_cols):
                        idx = i + j
                        if idx >= len(cpu['per_cpu']): break
                        p = cpu['per_cpu'][idx]
                        pc = 2 if p < 50 else (3 if p < 80 else 4)
                        try:
                            stdscr.addstr(f" [{idx:2d}]", curses.color_pair(pc))
                            if bar_width > 15:
                                draw_bar(stdscr, line, 8 + j * 12, 5, p, pc)
                            stdscr.addstr(f"{p:3.0f}%", curses.color_pair(pc))
                        except:
                            pass
                    line += 1
            line += 1

            # GPU
            for g in gpu:
                if line >= h: break
                gpu_color = 2 if g['gpu_util'] < 50 else (3 if g['gpu_util'] < 80 else 4)
                stdscr.addstr(line, 2, f" GPU{g['index']} {g['name'][:10]}", curses.color_pair(6))
                stdscr.addstr(f"  {g['gpu_util']:3d}%", curses.color_pair(gpu_color))
                draw_bar(stdscr, line, 28, 8, g['gpu_util'], gpu_color)
                stdscr.addstr(f"  {format_bytes(g['mem_used']*1024*1024):>6}/{format_bytes(g['mem_total']*1024*1024):<6}", curses.color_pair(5))
                stdscr.addstr(f"  {g['temp']}°C", curses.color_pair(2 if g['temp'] < 70 else 4))
                line += 1
            if gpu:
                line += 1

            # ── Memory ──
            if line < h:
                stdscr.addstr(line, 2, "MEM", curses.color_pair(1) | curses.A_BOLD)
                line += 1
            mem_color = 2 if mem['percent'] < 50 else (3 if mem['percent'] < 80 else 4)
            if line < h:
                used_s = format_bytes(mem['used'])
                total_s = format_bytes(mem['total'])
                stdscr.addstr(line, 2, f" {used_s:>7} / {total_s:<7}", curses.color_pair(mem_color))
                draw_bar(stdscr, line, 20, bar_width, mem['percent'], mem_color)
                bar_end = 20 + bar_width
                stdscr.addstr(line, bar_end + 1, f"{mem['percent']:.0f}%", curses.color_pair(mem_color))
                line += 1

            if mem['swap_total'] > 0 and line < h:
                swp_s = format_bytes(mem['swap_used'])
                swp_t = format_bytes(mem['swap_total'])
                sw_color = 2 if mem['swap_percent'] < 50 else (3 if mem['swap_percent'] < 80 else 4)
                stdscr.addstr(line, 2, f" SWP {swp_s:>7} / {swp_t:<7}", curses.color_pair(sw_color))
                line += 1
            line += 1

            # ── Disk ──
            if line < h:
                stdscr.addstr(line, 2, "DISK", curses.color_pair(1) | curses.A_BOLD)
                if disk_read_speed > 0 or disk_write_speed > 0:
                    stdscr.addstr(f"  R: {format_bytes(disk_read_speed)}/s  W: {format_bytes(disk_write_speed)}/s", curses.color_pair(6))
                line += 1
            for dsk in disks:
                if line >= h: break
                d_color = 2 if dsk['percent'] < 50 else (3 if dsk['percent'] < 80 else 4)
                mount = dsk['mount']
                if len(mount) > 10:
                    mount = mount[:9] + '~'
                used_s = format_bytes(dsk['used'])
                total_s = format_bytes(dsk['total'])
                stdscr.addstr(line, 2, f" {mount:>10}", curses.color_pair(6))
                stdscr.addstr(f" {used_s:>7} / {total_s:<7}", curses.color_pair(d_color))
                draw_bar(stdscr, line, 34, 15, dsk['percent'], d_color)
                stdscr.addstr(f" {dsk['percent']:.0f}%", curses.color_pair(d_color))
                line += 1
            line += 1

            # ── Network ──
            if line < h:
                stdscr.addstr(line, 2, "NET", curses.color_pair(1) | curses.A_BOLD)
                line += 1
            if line < h:
                stdscr.addstr(line, 2, " ")
                stdscr.addstr(f"↓ {format_bytes(net_speed_recv):>8}/s", curses.color_pair(3))
                stdscr.addstr(f"  ↑ {format_bytes(net_speed_sent):>8}/s", curses.color_pair(4))
                total_r = format_bytes(net['bytes_recv'])
                total_s_val = format_bytes(net['bytes_sent'])
                stdscr.addstr(f"  Total: ↓{total_r}  ↑{total_s_val}", curses.color_pair(5))
                line += 1

            # Connections
            if conns and line < h:
                stdscr.addstr(line, 2, " ", curses.color_pair(5))
                conn_str = "  ".join([f"{s}:{c}" for s, c in sorted(conns.items())])
                stdscr.addstr(f"Conn: {conn_str}", curses.color_pair(6))
                line += 1
            line += 1

            # ── Top Processes ──
            if line < h:
                sort_label = sort_by.upper()
                stdscr.addstr(line, 2, f"PROCESSES (sorted by {sort_label})", curses.color_pair(1) | curses.A_BOLD)
                line += 1
            if line < h:
                stdscr.addstr(line, 2, f" {'PID':>5}  {'CPU%':>5}  {'MEM%':>5}  USER      STATUS  NAME", curses.color_pair(6))
                line += 1
            procs = get_top_processes(n=h - line - 3, sort_by=sort_by)
            for proc in procs:
                if line >= h: break
                p_cpu_color = 2 if proc['cpu_percent'] < 10 else (3 if proc['cpu_percent'] < 30 else 4)
                username = (proc.get('username') or '?')[:8]
                try:
                    stdscr.addstr(line, 2, f" {proc['pid']:>5}", curses.color_pair(5))
                    stdscr.addstr(f"  {proc['cpu_percent']:4.1f}%", curses.color_pair(p_cpu_color))
                    stdscr.addstr(f"  {proc['memory_percent']:4.1f}%", curses.color_pair(5))
                    stdscr.addstr(f"  {username:<8}", curses.color_pair(6))
                    stdscr.addstr(f"  {proc['status'][:6]:<6}", curses.color_pair(6))
                    stdscr.addstr(f"  {proc['name'][:20]}", curses.color_pair(5))
                except:
                    pass
                line += 1

            # ── Alert bar ──
            if log_messages and line < h:
                line += 1
                for msg in log_messages[-2:]:
                    if line >= h: break
                    if msg.startswith('[CRITICAL]'):
                        stdscr.addstr(line, 2, msg[:w-4], curses.color_pair(4) | curses.A_BOLD)
                    else:
                        stdscr.addstr(line, 2, msg[:w-4], curses.color_pair(3))
                    line += 1

            # ── Footer ──
            footer = f" {datetime.now().strftime('%H:%M:%S')}  |  q:quit  s:sort({sort_by})  h:history{' ON' if record_history else ' OFF'}  ?:help  "
            if line < h:
                try:
                    stdscr.addstr(h - 1, 0, footer[:w-1], curses.color_pair(6))
                except:
                    pass

            stdscr.refresh()
            stdscr.timeout(1000)
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key == ord('s'):
                # Cycle sort: cpu -> mem -> pid -> name
                sort_order = ['cpu', 'mem', 'pid', 'name']
                idx = (sort_order.index(sort_by) + 1) % len(sort_order)
                sort_by = sort_order[idx]
            elif key == ord('h'):
                record_history = not record_history
                log_messages.append(f"[INFO] History recording {'ON' if record_history else 'OFF'}")
            elif key == ord('?'):
                log_messages.append("[INFO] Keys: q=quit  s=sort  h=history toggle  ?=help")
            elif key == ord('k'):
                log_messages.append("[INFO] Kill mode: use 'kill <pid>' in separate terminal")

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"sysmon-pro TUI error: {e}")


# ═══════════════════════════════════════════════════════════
# CLI 模式
# ═══════════════════════════════════════════════════════════

def once_mode(output_format='json'):
    """单次快照输出"""
    data = collect_all()
    if output_format == 'json':
        print(json.dumps(data, indent=2, default=str))
    elif output_format == 'csv':
        # Flat CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(['timestamp', 'hostname', 'cpu_percent', 'mem_percent',
                         'mem_used', 'mem_total', 'disk_percent', 'net_sent', 'net_recv',
                         'load_1', 'load_5', 'load_15'])
        disks_pct = ';'.join([str(d['percent']) for d in data['disks']])
        writer.writerow([
            data['timestamp'], data['hostname'],
            data['cpu']['percent'], data['memory']['percent'],
            data['memory']['used'], data['memory']['total'],
            disks_pct,
            data['network']['bytes_sent'], data['network']['bytes_recv'],
            data['cpu']['load_1'], data['cpu']['load_5'], data['cpu']['load_15'],
        ])

def watch_mode(interval=2):
    """连续监控输出 (CLI)"""
    prev_net = get_network()
    prev_time = time.time()
    try:
        while True:
            data = collect_all()
            now = time.time()
            dt = now - prev_time
            net = data['network']
            net_speed_sent = (net['bytes_sent'] - prev_net['sent']) / dt if dt > 0 else 0
            net_speed_recv = (net['bytes_recv'] - prev_net['recv']) / dt if dt > 0 else 0
            prev_net = {'sent': net['bytes_sent'], 'recv': net['bytes_recv']}
            prev_time = now

            print(f"\033[2J\033[H", end='')  # Clear screen
            print(f"sysmon-pro v{VERSION} — {data['hostname']}  [{data['timestamp'][:19]}]")
            print(f"Up {data['uptime']}  |  Load: {data['cpu']['load_1']:.2f} {data['cpu']['load_5']:.2f} {data['cpu']['load_15']:.2f}")
            print(f"")
            print(f"CPU: {data['cpu']['percent']:5.1f}%  ({data['cpu']['count']}C/{data['cpu']['logical']}T)")
            mem_pct = data['memory']['percent']
            print(f"MEM: {format_bytes(data['memory']['used']):>8} / {format_bytes(data['memory']['total']):<8}  {mem_pct:.0f}%")
            if data['memory']['swap_total'] > 0:
                print(f"SWP: {format_bytes(data['memory']['swap_used']):>8} / {format_bytes(data['memory']['swap_total']):<8}  {data['memory']['swap_percent']:.0f}%")
            for d in data['disks'][:3]:
                print(f"DSK: {d['mount']:>10}  {format_bytes(d['used']):>8} / {format_bytes(d['total']):<8}  {d['percent']:.0f}%")
            print(f"NET: ↓{format_bytes(net_speed_recv):>8}/s  ↑{format_bytes(net_speed_sent):>8}/s")

            alerts = check_alerts(data)
            for level, msg in alerts:
                print(f"\033[91m[{level}] {msg}\033[0m")

            print(f"\n[Press Ctrl+C to stop]  (refresh every {interval}s)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nsysmon-pro stopped.")

def alert_daemon(interval=60):
    """告警守护模式：后台运行，只在超阈值时输出"""
    try:
        while True:
            data = collect_all()
            alerts = check_alerts(data)
            ts = datetime.now().strftime('%H:%M:%S')
            for level, msg in alerts:
                print(f"[{ts}] [{level}] {msg}")
            if not alerts:
                # Silent: no news is good news
                pass
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nsysmon-pro alert daemon stopped.")

def history_mode():
    """查看历史记录"""
    records = list_history(20)
    if not records:
        print("No history records found. Run 'evtool sysmon --history-on' to start recording.")
        return
    print(f"{'File':<30} {'Timestamp':<25} {'CPU%':>6} {'MEM%':>6}")
    print("-" * 70)
    for r in records:
        fname = r['file'][:28]
        ts = r.get('timestamp', '?')[:22]
        cpu = r.get('cpu', 0)
        mem = r.get('mem', 0)
        print(f"{fname:<30} {ts:<25} {cpu:>5.1f}% {mem:>5.1f}%")

def set_alerts(args_list):
    """设置告警阈值"""
    alerts = load_alerts()
    for arg in args_list:
        if '=' in arg:
            key, val = arg.split('=', 1)
            try:
                alerts[key.strip()] = int(val.strip())
                print(f"Set {key} = {val}")
            except ValueError:
                print(f"Invalid value for {key}: {val}")
        elif arg == '--default':
            alerts = DEFAULT_ALERTS.copy()
            print("Reset to default alerts")
    save_alerts(alerts)
    print(f"\nCurrent alerts: {json.dumps(alerts, indent=2)}")


# ═══════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════

def entry():
    parser = argparse.ArgumentParser(
        prog='sysmon',
        description='sysmon-pro — 旗舰级系统监控 (TUI+CLI)',
        epilog='Example: evtool sysmon --once | jq .cpu.percent'
    )
    parser.add_argument('--once', action='store_true', help='单次快照 (默认JSON)')
    parser.add_argument('--csv', action='store_true', help='单次快照 (CSV)')
    parser.add_argument('--watch', type=int, nargs='?', const=2, metavar='N',
                        help='连续监控 (默认每2秒刷新)')
    parser.add_argument('--alert', type=int, nargs='?', const=60, metavar='N',
                        help='告警守护模式 (默认60秒检测)')
    parser.add_argument('--history', action='store_true', help='查看历史记录')
    parser.add_argument('--set-alert', nargs='*', metavar='KEY=VALUE',
                        help='设置告警阈值 (e.g. cpu_percent=95)')
    parser.add_argument('--version', action='store_true', help='显示版本')

    args = parser.parse_args()

    if args.version:
        print(f"sysmon-pro v{VERSION}")
        return

    if args.set_alert is not None:
        set_alerts(args.set_alert)
        return

    if args.once:
        once_mode('json')
        return

    if args.csv:
        once_mode('csv')
        return

    if args.watch:
        watch_mode(args.watch)
        return

    if args.alert:
        alert_daemon(args.alert)
        return

    if args.history:
        history_mode()
        return

    # Default: start TUI
    tui_mode()


# === Auto-registration metadata ===
TOOL_META = {
    "name": "sysmon-pro",
    "func": "entry",
    "desc": "Flagship system monitor — TUI/CLI/JSON/alerts/history/GPU",
}

if __name__ == '__main__':
    entry()
