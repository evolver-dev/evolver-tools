#!/usr/bin/env python3
"""network-scan — Scan active hosts on the local network."""
import subprocess
import sys
import re

TOOL_META = {
    "name": "network-scan",
    "func": "main",
    "desc": "Scan active hosts on network. Usage: network-scan [subnet] [--ping]",
}

def get_local_subnet():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return "192.168.1.0/24"

def ping_scan(subnet):
    """Scan using ping."""
    base = ".".join(subnet.split(".")[:3])
    alive = []
    print(f"Scanning {base}.1-254...")
    for i in range(1, 255):
        ip = f"{base}.{i}"
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                # Get hostname if possible
                try:
                    import socket
                    hostname = socket.gethostbyaddr(ip)[0]
                except Exception:
                    hostname = ""
                alive.append((ip, hostname))
                print(f"  ✓ {ip:<16} {hostname}")
        except Exception:
            pass
    return alive

def arp_scan():
    """Use ARP table to find hosts."""
    hosts = []
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+)", line)
            if m:
                hosts.append((m.group(1), m.group(2)))
    except FileNotFoundError:
        pass
    return hosts

def main():
    args = sys.argv[1:]
    subnet = args[0] if args and not args[0].startswith("-") else get_local_subnet()
    use_ping = "--ping" in args
    # Try ARP first
    arp_hosts = arp_scan()
    if arp_hosts and not use_ping:
        print(f"Found {len(arp_hosts)} hosts in ARP cache:")
        print(f"{'IP':<20} {'MAC Address'}")
        print("-" * 40)
        for ip, mac in arp_hosts:
            print(f"{ip:<20} {mac}")
        print("\nTip: Use --ping for active scan")
        return
    # Ping scan
    ping_scan(subnet)

if __name__ == "__main__":
    main()
