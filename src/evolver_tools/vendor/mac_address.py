#!/usr/bin/env python3
"""Generate and lookup MAC addresses."""

import argparse
import random
import sys
import os

TOOL_META = {
    "name": "mac-address",
    "func": "main",
    "desc": "Generate and lookup MAC addresses",
}

OUI_DB = {
    "00:1A:11": "Intel",
    "00:1B:21": "Dell",
    "00:0C:29": "VMware",
    "08:00:27": "Oracle/VirtualBox",
    "00:50:56": "VMware",
    "00:15:5D": "Microsoft Hyper-V",
    "00:1C:42": "Parallels",
    "00:0C:29": "VMware",
    "52:54:00": "QEMU/KVM",
    "00:1A:4A": "Broadcom",
    "00:1E:68": "Cisco",
    "00:1A:6B": "Nokia",
    "00:1B:3E": "IBM",
    "00:1D:60": "Hewlett-Packard",
    "00:1F:29": "Apple",
    "00:23:32": "Samsung",
    "00:24:BE": "Xerox",
    "00:26:AB": "Sony",
    "00:26:BB": "Panasonic",
    "CC:46:D6": "Cisco",
}


def _random_mac():
    """Generate a random MAC address."""
    octets = [random.randint(0x00, 0xFF) for _ in range(6)]
    octets[0] = (octets[0] & 0xFE) | 0x02  # set local + unicast
    return ":".join(f"{o:02X}" for o in octets)


def _lookup_oui(mac):
    """Look up vendor by OUI prefix."""
    oui = mac.strip().upper()[:8]
    return OUI_DB.get(oui, "Unknown")


def main():
    parser = argparse.ArgumentParser(
        description="Generate and lookup MAC addresses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  mac-address --random\n  mac-address --random --count 5\n  mac-address --oui 00:1A:11\n  mac-address 00:1A:11:22:33:44"
    )
    parser.add_argument("--random", action="store_true", help="Generate random MAC address")
    parser.add_argument("--count", type=int, default=1, help="Number of addresses to generate")
    parser.add_argument("--oui", type=str, help="Look up vendor by OUI prefix (e.g. 00:1A:11)")
    parser.add_argument("address", nargs="?", help="MAC address to look up")
    args = parser.parse_args()

    if args.oui:
        print(f"OUI: {args.oui.upper()}\nVendor: {_lookup_oui(args.oui)}")
        return

    if args.random:
        for i in range(args.count):
            mac = _random_mac()
            vendor = _lookup_oui(mac)
            print(f"{mac}  [{vendor}]")
        return

    if args.address:
        addr = args.address.strip()
        vendor = _lookup_oui(addr)
        print(f"Address: {addr}\nVendor:   {vendor}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
