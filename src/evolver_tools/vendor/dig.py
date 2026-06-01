#!/usr/bin/env python3
"""dig.py — DNS lookup tool (pure Python stdlib)."""

import argparse
import os
import socket
import struct
import sys
import time

TOOL_META = {
    "name": "dig",
    "func": "main",
    "desc": "DNS lookup tool - resolve domains, find DNS records",
}

# DNS record type constants
QTYPE_MAP = {
    "A": 1,
    "AAAA": 28,
    "MX": 15,
    "NS": 2,
    "TXT": 16,
    "CNAME": 5,
}
QTYPE_REV = {v: k for k, v in QTYPE_MAP.items()}
CLASS_IN = 1


def _encode_domain(domain):
    """Encode a domain name into DNS label format."""
    labels = []
    for part in domain.rstrip(".").split("."):
        labels.append(bytes([len(part)]) + part.encode("ascii", errors="replace"))
    labels.append(b"\x00")
    return b"".join(labels)


def _decode_name(data, offset):
    """Decode a DNS domain name from data starting at offset. Handles pointers."""
    labels = []
    jumped = False
    orig_offset = offset
    while True:
        if offset >= len(data):
            break
        length = data[offset]
        if length & 0xC0:  # pointer (two bytes)
            if not jumped:
                orig_offset = offset + 2
                jumped = True
            ptr = struct.unpack_from("!H", data, offset)[0] & 0x3FFF
            offset = ptr
            continue
        offset += 1
        if length == 0:
            break
        if offset + length > len(data):
            break
        labels.append(data[offset : offset + length].decode("ascii", errors="replace"))
        offset += length
    name = ".".join(labels)
    end_offset = orig_offset if jumped else offset
    return name, end_offset


def _build_query(domain, qtype):
    """Build a raw DNS query packet."""
    tid = struct.unpack("!H", os.urandom(2))[0]
    # flags: 0x0100 = standard query + recursion desired
    header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    qname = _encode_domain(domain)
    question = qname + struct.pack("!HH", qtype, CLASS_IN)
    return header + question, tid


def _parse_response(data, qtype):
    """Parse a DNS response and return list of (type_str, value, ttl)."""
    records = []
    if len(data) < 12:
        return records

    # Parse header
    tid, flags, qdcount, ancount, nscount, arcount = struct.unpack_from("!HHHHHH", data, 0)

    # Check response code (last 4 bits)
    rcode = flags & 0x0F
    if rcode != 0:
        rcode_msgs = {
            1: "Format error",
            2: "Server failure",
            3: "NXDOMAIN (domain does not exist)",
            4: "Not implemented",
            5: "Refused",
        }
        raise RuntimeError(rcode_msgs.get(rcode, f"DNS error code {rcode}"))

    offset = 12

    # Skip question section
    for _ in range(qdcount):
        name, offset = _decode_name(data, offset)
        offset += 4  # skip QTYPE + QCLASS

    # Parse answer section
    for _ in range(ancount):
        name, offset = _decode_name(data, offset)
        if offset + 10 > len(data):
            break
        rtype, rclass, ttl, rdlength = struct.unpack_from("!HHIH", data, offset)
        offset += 10
        if offset + rdlength > len(data):
            break
        rdata_offset = offset
        rdata = data[offset : offset + rdlength]
        offset += rdlength

        type_str = QTYPE_REV.get(rtype, f"TYPE{rtype}")

        if rtype == 1:  # A
            if len(rdata) >= 4:
                val = ".".join(str(b) for b in rdata[:4])
                records.append((type_str, val, ttl))
        elif rtype == 28:  # AAAA
            if len(rdata) >= 16:
                parts = []
                for i in range(0, 16, 2):
                    parts.append(f"{rdata[i]:02x}{rdata[i+1]:02x}")
                # Collapse zeros like typical IPv6 representation
                val = _collapse_ipv6(":".join(parts))
                records.append((type_str, val, ttl))
        elif rtype == 15:  # MX
            if len(rdata) >= 3:
                pref = struct.unpack_from("!H", rdata, 0)[0]
                exchange, _ = _decode_name(data, rdata_offset + 2)
                records.append((type_str, f"{pref} {exchange}", ttl))
        elif rtype == 2:  # NS
            ns, _ = _decode_name(data, rdata_offset)
            records.append((type_str, ns, ttl))
        elif rtype == 5:  # CNAME
            cname, _ = _decode_name(data, rdata_offset)
            records.append((type_str, cname, ttl))
        elif rtype == 16:  # TXT
            txt_parts = []
            pos = 0
            while pos < len(rdata):
                slen = rdata[pos]
                pos += 1
                if pos + slen > len(rdata):
                    break
                txt_parts.append(rdata[pos : pos + slen].decode("utf-8", errors="replace"))
                pos += slen
            val = '"' + "".join(txt_parts) + '"'
            records.append((type_str, val, ttl))

    return records


def _collapse_ipv6(addr):
    """Collapse IPv6 address (simple zero compression)."""
    # Replace longest run of :0:0:... with ::
    groups = addr.split(":")
    # Find longest run of zeros
    best_start = -1
    best_len = 0
    cur_start = -1
    cur_len = 0
    for i, g in enumerate(groups):
        if g == "0000":
            if cur_start == -1:
                cur_start = i
                cur_len = 1
            else:
                cur_len += 1
        else:
            if cur_len > best_len:
                best_start = cur_start
                best_len = cur_len
            cur_start = -1
            cur_len = 0
    if cur_len > best_len:
        best_start = cur_start
        best_len = cur_len

    if best_len >= 2:
        before = groups[:best_start]
        after = groups[best_start + best_len :]
        parts = [g.lstrip("0") or "0" for g in before]
        parts.append("")
        parts.extend(g.lstrip("0") or "0" for g in after)
        collapsed = ":".join(parts)
        # Replace ::... with ::
        collapsed = collapsed.replace("::", "::")
        if collapsed.startswith(":"):
            collapsed = ":" + collapsed
        if collapsed.endswith(":"):
            collapsed += ":"
        return collapsed
    return ":".join(g.lstrip("0") or "0" for g in groups)


def _get_system_dns():
    """Get the system DNS server from /etc/resolv.conf, or fall back to 8.8.8.8."""
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                line = line.strip()
                if line.startswith("nameserver"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return "8.8.8.8"


def _query_dns(domain, qtype, server, timeout=5):
    """Send a DNS query via UDP and return parsed records."""
    qtype_val = QTYPE_MAP.get(qtype, 1)
    packet, tid = _build_query(domain, qtype_val)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (server, 53))
        data, _ = sock.recvfrom(65535)
    except socket.timeout:
        raise RuntimeError(f"DNS query timed out (server: {server})")
    except OSError as e:
        raise RuntimeError(f"Network error: {e}")
    finally:
        sock.close()

    # Verify transaction ID matches
    if len(data) >= 2:
        resp_tid = struct.unpack_from("!H", data, 0)[0]
        if resp_tid != tid:
            raise RuntimeError("Transaction ID mismatch (possible spoof)")

    return _parse_response(data, qtype_val)


def resolve_a_aaaa(domain, qtype):
    """Resolve A/AAAA records using socket.getaddrinfo."""
    family = socket.AF_INET if qtype == "A" else socket.AF_INET6
    try:
        result = socket.getaddrinfo(domain, None, family)
        seen = set()
        records = []
        for r in result:
            addr = r[4][0]
            if addr not in seen:
                seen.add(addr)
                # getaddrinfo doesn't give TTL, show 0
                records.append((qtype, addr, 0))
        return records
    except socket.gaierror as e:
        raise RuntimeError(f"Lookup failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="DNS lookup tool - resolve domains and find DNS records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  dig.py example.com
  dig.py example.com --type MX
  dig.py example.com --type TXT --server 8.8.8.8
  dig.py example.com --type AAAA""",
    )
    parser.add_argument("domain", help="Domain name to look up")
    parser.add_argument(
        "--type", "-t",
        dest="qtype",
        default="A",
        choices=sorted(QTYPE_MAP.keys()),
        help="DNS record type (default: A)",
    )
    parser.add_argument(
        "--server", "-s",
        dest="server",
        default=None,
        help="DNS server to query (default: system resolver)",
    )

    args = parser.parse_args()
    domain = args.domain.rstrip(".")
    qtype = args.qtype.upper()
    server = args.server

    try:
        # Use socket.getaddrinfo for A/AAAA (uses system resolver),
        # unless a custom server is specified
        if qtype in ("A", "AAAA") and server is None:
            records = resolve_a_aaaa(domain, qtype)
        else:
            if server is None:
                server = _get_system_dns()
            records = _query_dns(domain, qtype, server)

        if not records:
            print(f"No {qtype} records found for {domain}")
            sys.exit(1)

        # Determine column widths
        max_type = max(len(r[0]) for r in records) if records else 4
        max_type = max(max_type, 4)
        type_width = max(max_type, 8)

        # Print header
        print(f"{'TYPE':<{type_width}} {'VALUE':<48} {'TTL':>8}")
        print("-" * (type_width + 57))

        for rtype, value, ttl in records:
            # Truncate long values for clean display
            val_str = str(value)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            ttl_str = str(ttl) if ttl > 0 else "-"
            print(f"{rtype:<{type_width}} {val_str:<48} {ttl_str:>8}")

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
