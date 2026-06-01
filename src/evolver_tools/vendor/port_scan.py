#!/usr/bin/env python3
"""port_scan — Quick TCP port scan on a host."""

import sys
import socket
from concurrent.futures import ThreadPoolExecutor

TOOL_META = {
    "name": "port_scan",
    "func": "main",
    "desc": "Quick TCP port scan on a host",
}


def _scan_port(host, port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return (port, result == 0)
    except Exception:
        return (port, False)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: evolver port_scan <host> [ports]")
        print()
        print("Examples:")
        print("  evolver port_scan localhost")
        print("  evolver port_scan 192.168.1.1 22,80,443")
        print("  evolver port_scan example.com 1-1024")
        return

    host = args[0]
    ports = args[1] if len(args) > 1 else "22,80,443,8080"

    # Parse port spec
    port_set = set()
    for part in ports.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            for p in range(int(a), int(b) + 1):
                port_set.add(p)
        else:
            port_set.add(int(part))

    ports_list = sorted(port_set)
    print(f"Scanning {host} ({len(ports_list)} ports)...")

    open_ports = []
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = [pool.submit(_scan_port, host, p) for p in ports_list]
        for i, f in enumerate(futures):
            port, is_open = f.result()
            if is_open:
                service = {22: "SSH", 80: "HTTP", 443: "HTTPS", 8080: "HTTP-Alt",
                           3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis",
                           27017: "MongoDB"}.get(port, "")
                tag = f"  ({service})" if service else ""
                print(f"  \033[32mOPEN\033[0m  {port}/tcp{tag}")
                open_ports.append(port)

    if not open_ports:
        print("  No open ports found.")
    else:
        print(f"\nFound {len(open_ports)} open port(s) on {host}")


if __name__ == "__main__":
    main()
