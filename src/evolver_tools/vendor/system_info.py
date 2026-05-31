#!/usr/bin/env python3
"""system-info — Display comprehensive system information."""
import os
import platform
import sys

TOOL_META = {
    "name": "system-info",
    "func": "main",
    "desc": "Display system information. Usage: system-info [--all]",
}

def get_cpu_info():
    info = {}
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "model name":
                        info["model"] = val
                    elif key == "cpu cores":
                        info["cores"] = int(val)
                    elif key == "siblings":
                        info["threads"] = int(val)
    except Exception:
        info["model"] = platform.processor() or "Unknown"
    return info

def get_mem_info():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "MemTotal":
                        info["total"] = int(val.split()[0]) // 1024
                    elif key == "MemAvailable":
                        info["available"] = int(val.split()[0]) // 1024
    except Exception:
        pass
    return info

def get_disk_info():
    info = {}
    try:
        result = os.statvfs("/")
        total = result.f_frsize * result.f_blocks
        free = result.f_frsize * result.f_bfree
        info["total"] = total // (1024**3)
        info["free"] = free // (1024**3)
    except Exception:
        pass
    return info

def get_network_info():
    info = {}
    try:
        import socket
        hostname = socket.gethostname()
        info["hostname"] = hostname
        # Get IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return info

def main():
    args = sys.argv[1:]
    show_all = "--all" in args
    print(f"System Information — {platform.node()}")
    print("=" * 50)
    # OS
    print(f"OS:          {platform.system()} {platform.release()}")
    print(f"Platform:    {platform.platform()}")
    print(f"Python:      {platform.python_version()}")
    # CPU
    cpu = get_cpu_info()
    if cpu:
        print(f"CPU:         {cpu.get('model', 'Unknown')}")
        print(f"  Cores:     {cpu.get('cores', '?')}")
        print(f"  Threads:   {cpu.get('threads', '?')}")
    # Memory
    mem = get_mem_info()
    if mem:
        used = mem.get("total", 0) - mem.get("available", 0)
        print(f"Memory:      {used} MB / {mem.get('total', 0)} MB ({mem.get('available', 0)} MB free)")
    # Disk
    disk = get_disk_info()
    if disk:
        used = disk.get("total", 0) - disk.get("free", 0)
        print(f"Disk (/):    {disk.get('total', 0):.1f}G total, {disk.get('free', 0):.1f}G free")
    # Network
    net = get_network_info()
    if net:
        print(f"Hostname:    {net.get('hostname')}")
        print(f"IP Address:  {net.get('ip')}")
    # Uptime
    try:
        with open("/proc/uptime") as f:
            uptime_sec = float(f.read().split()[0])
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        mins = int((uptime_sec % 3600) // 60)
        print(f"Uptime:      {days}d {hours}h {mins}m")
    except Exception:
        pass
    if show_all:
        # Process count
        try:
            proc_count = len(os.listdir("/proc")) - 2  # subtract . and ..
            print(f"Processes:   ~{proc_count}")
        except Exception:
            pass
        # Load average
        try:
            with open("/proc/loadavg") as f:
                load = f.read().strip()
            print(f"Load Avg:    {load.split()[:3]}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
