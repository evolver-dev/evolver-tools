#!/usr/bin/env python3
"""subnet — IPv4 subnet/CIDR calculator.

Usage: subnet 192.168.1.0/24
       subnet 10.0.0.0 255.255.255.0
       subnet --list 192.168.1.0/28   # List all hosts

Shows network address, broadcast, usable range, mask, CIDR.
Zero-dependency (stdlib only).
"""

import sys
import ipaddress


def main():
    args = sys.argv[1:]
    list_hosts = False

    for a in args[:]:
        if a in ('--list', '-l'):
            list_hosts = True
            args.remove(a)
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    if not args:
        print("Usage: subnet <CIDR> [--list]")
        print("       subnet <ip> <netmask>")
        print("Example: subnet 192.168.1.0/24")
        return

    try:
        if len(args) >= 2:
            network = ipaddress.IPv4Network(f"{args[0]}/{args[1]}", strict=False)
        else:
            network = ipaddress.IPv4Network(args[0], strict=False)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    netmask = network.netmask
    num_addresses = network.num_addresses
    host_count = max(0, num_addresses - 2)

    print(f"  Address:     {network.network_address}")
    print(f"  Netmask:     {netmask}")
    print(f"  Wildcard:    {network.hostmask}")
    print(f"  CIDR:        /{network.prefixlen}")
    print(f"  Network:     {network.network_address}")
    print(f"  Broadcast:   {network.broadcast_address}")
    print(f"  Usable:      {network.network_address + 1} - {network.broadcast_address - 1}")
    print(f"  Hosts/Net:   {host_count}")
    print(f"  Total IPs:   {num_addresses}")
    print(f"  Class:       {'A' if network.prefixlen < 16 else 'B' if network.prefixlen < 24 else 'C' if network.prefixlen < 30 else 'Special'}")

    if list_hosts and host_count < 256:
        hosts = list(network.hosts())
        print(f"\n  Hosts ({len(hosts)}):")
        for i, h in enumerate(hosts):
            print(f"    {h}")
            if i >= 254:
                print(f"    ... ({len(hosts) - 255} more)")
                break


# === Auto-registration metadata ===
TOOL_META = {
    "name": "subnet",
    "func": "main",
    "desc": 'IPv4 subnet/CIDR calculator',
}

if __name__ == '__main__':
    main()
