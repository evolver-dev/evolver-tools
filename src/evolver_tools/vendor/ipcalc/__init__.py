"""ipcalc: IP address / CIDR calculator.

Pure Python stdlib implementation using ipaddress module.
"""

import sys
import ipaddress
import re

__version__ = "1.0.0"

# ANSI colors
BLUE = "\033[34m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
RESET = "\033[0m"


def format_ip(ip):
    """Format an IP address string."""
    return str(ip)


def calc_network(input_str):
    """Parse CIDR or IP/netmask and return network info."""
    input_str = input_str.strip()
    
    # Try direct CIDR notation (192.168.1.0/24)
    try:
        net = ipaddress.IPv4Network(input_str, strict=False)
        return net
    except (ValueError, ipaddress.AddressValueError):
        pass
    
    # Try IP address without netmask
    try:
        ip = ipaddress.IPv4Address(input_str)
        # Single IP, assume /32
        net = ipaddress.IPv4Network(f"{input_str}/32", strict=False)
        return net
    except (ValueError, ipaddress.AddressValueError):
        print(f"ipcalc: Invalid input: {input_str}", file=sys.stderr)
        sys.exit(1)


def describe_network(net):
    """Return formatted network description."""
    host_min = net.network_address + 1 if net.num_addresses > 2 else net.network_address
    host_max = net.broadcast_address - 1 if net.num_addresses > 2 else net.broadcast_address
    
    wildcard = ipaddress.IPv4Address(
        (2**32 - 1) ^ int(net.netmask)
    )
    
    lines = []
    lines.append(f"\n{BOLD}Address:    {CYAN}{net.network_address}/{net.prefixlen}{RESET}")
    lines.append(f"{BOLD}Netmask:    {GREEN}{net.netmask}{RESET}")
    lines.append(f"{BOLD}Wildcard:   {YELLOW}{wildcard}{RESET}")
    lines.append(f"{BOLD}Network:    {BLUE}{net.network_address}{RESET}")
    lines.append(f"{BOLD}Broadcast:  {RED}{net.broadcast_address}{RESET}")
    lines.append(f"{BOLD}HostMin:    {GREEN}{host_min}{RESET}")
    lines.append(f"{BOLD}HostMax:    {GREEN}{host_max}{RESET}")
    
    total = net.num_addresses
    usable = max(0, total - 2)
    lines.append(f"")
    lines.append(f"{BOLD}Total IPs:  {YELLOW}{total}{RESET}")
    lines.append(f"{BOLD}Usable IPs: {GREEN}{usable}{RESET}")
    lines.append(f"{BOLD}Prefix:     /{net.prefixlen}{RESET}")
    
    # Class info
    first_octet = int(str(net.network_address).split(".")[0])
    if 0 <= first_octet <= 127:
        ip_class = "A"
        default_prefix = 8
    elif 128 <= first_octet <= 191:
        ip_class = "B"
        default_prefix = 16
    elif 192 <= first_octet <= 223:
        ip_class = "C"
        default_prefix = 24
    elif 224 <= first_octet <= 239:
        ip_class = "D (Multicast)"
        default_prefix = 4
    else:
        ip_class = "E (Reserved)"
        default_prefix = 4
    
    # Private range detection
    if net.network_address.is_private:
        scope = "Private"
    elif net.network_address.is_loopback:
        scope = "Loopback"
    elif net.network_address.is_link_local:
        scope = "Link-Local"
    elif net.network_address.is_multicast:
        scope = "Multicast"
    elif net.network_address.is_unspecified:
        scope = "Unspecified"
    else:
        scope = "Public"
    
    lines.append(f"{BOLD}Class:      {MAGENTA}{ip_class}{RESET}")
    lines.append(f"{BOLD}Scope:      {'Private (RFC 1918)' if net.network_address.is_private else scope}{RESET}")
    
    if net.prefixlen != default_prefix:
        if net.prefixlen < default_prefix:
            lines.append(f"{BOLD}Note:       {YELLOW}Supernet (/{net.prefixlen} > /{default_prefix} default){RESET}")
        else:
            lines.append(f"{BOLD}Note:       {YELLOW}Subnet (/{net.prefixlen} < /{default_prefix} default){RESET}")
    
    return "\n".join(lines)


def print_help():
    print("Usage: ipcalc <CIDR_or_IP> [CIDR_or_IP ...]")
    print()
    print("Calculate and display IP network information.")
    print()
    print("Accepts:")
    print("  CIDR notation:  192.168.1.0/24")
    print("  IP + netmask:   192.168.1.0/255.255.255.0")
    print("  Single IP:      192.168.1.1 (treated as /32)")
    print()
    print("Examples:")
    print("  ipcalc 192.168.1.0/24")
    print("  ipcalc 10.0.0.0/8")
    print("  ipcalc 192.168.1.1")
    print("  ipcalc 172.16.0.0/12 10.0.0.0/8")


def main():
    args = sys.argv[1:]
    
    if not args or "-h" in args or "--help" in args:
        print_help()
        return
    
    first = True
    for arg in args:
        if arg.startswith("-"):
            continue
        net = calc_network(arg)
        if not first:
            print()
        print(describe_network(net))
        first = False



# === Auto-registration metadata ===
TOOL_META = {
    "name": "ipcalc",
    "func": "main",
    "desc": 'IP/CIDR calculator',
}

if __name__ == "__main__":
    main()
