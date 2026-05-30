"""
net-analyzer CLI module — all network analysis commands.

Implements ping, traceroute, port scan, DNS resolution, whois lookup,
and speedtest using only the Python standard library + subprocess for
system ping/traceroute commands.
"""

import os
import sys
import json
import socket
import struct
import time
import platform
import subprocess
import select
import re
import textwrap
import threading
import urllib.request
import urllib.error
from typing import Optional, List, Tuple

# ── ANSI color codes ──────────────────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR_LINE = "\033[2K\r"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if abs(n) != 1 else ''}"


# ── Helper: resolve host ──────────────────────────────────────────────────────
def _resolve(host: str) -> Optional[str]:
    """Resolve hostname to IP. Returns None on failure."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


# ── 1. Ping ───────────────────────────────────────────────────────────────────
def cmd_ping(host: str, count: int = 4, timeout: float = 10.0, raw: bool = False) -> str:
    """
    ICMP ping using a raw socket. Sends 'count' echo requests and collects stats.
    Falls back to system ping if raw sockets fail (common without root).
    """
    if not raw:
        return _ping_system(host, count, timeout)
    return _ping_raw(host, count, timeout)


def _ping_system(host: str, count: int, timeout: float) -> str:
    """Fallback: use system ping command."""
    lines: List[str] = []
    ip = _resolve(host)
    lines.append(f"{BOLD}{CYAN}▸ PING{RESET}  {BOLD}{host}{RESET}  →  {ip or '(unresolved)'}")
    lines.append(f"  {DIM}system ping{RESET}\n")

    if platform.system() == "Windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout)), host]

    sent = count
    received = 0
    times: List[float] = []

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        output = result.stdout + result.stderr

        if platform.system() == "Windows":
            # Parse Windows ping output
            for line in output.splitlines():
                m = re.search(r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms", line, re.I)
                if m:
                    received += 1
                    times.append(float(m.group(1)))
            if "100% loss" in output or "Destination host unreachable" in output:
                received = 0
        else:
            for line in output.splitlines():
                m = re.match(
                    r".*bytes from.*time=(\d+(?:\.\d+)?)\s*ms", line, re.I
                )
                if m:
                    received += 1
                    times.append(float(m.group(1)))

        for i, t in enumerate(times, 1):
            lines.append(
                f"  {GREEN}✔{RESET}  seq={i}  time={CYAN}{t:.1f}{RESET} ms"
            )
        for _ in range(sent - received):
            lines.append(f"  {RED}✘{RESET}  {DIM}timeout / lost{RESET}")

    except subprocess.TimeoutExpired:
        lines.append(f"  {RED}✘{RESET}  ping timed out")
        sent = count
        received = 0
    except FileNotFoundError:
        lines.append(f"  {RED}✘{RESET}  ping command not found on this system")
        return "\n".join(lines)

    loss = (sent - received) / sent * 100 if sent else 100
    lines.append("")
    lines.append(
        f"  {BOLD}---{RESET} {host} ping statistics {BOLD}---{RESET}"
    )
    lines.append(f"  {_plural(sent, 'packet')} transmitted, {_plural(received, 'packet')} received, "
                 f"{RED if loss > 0 else GREEN}{loss:.1f}%{RESET} packet loss")
    if times:
        avg = sum(times) / len(times)
        mmin = min(times)
        mmax = max(times)
        lines.append(f"  rtt min/avg/max = {mmin:.2f}/{avg:.2f}/{mmax:.2f} ms")
    return "\n".join(lines)


def _ping_raw(host: str, count: int, timeout: float) -> str:
    """Raw ICMP ping via raw socket (requires root/Administrator)."""
    lines: List[str] = []
    ip = _resolve(host)
    lines.append(f"{BOLD}{CYAN}▸ PING{RESET}  {BOLD}{host}{RESET}  →  {ip or '(unresolved)'}")
    lines.append(f"  {DIM}raw ICMP{RESET}\n")

    if not ip:
        return f"{RED}Could not resolve {host}{RESET}"

    # ICMP Echo Request
    def _checksum(data: bytes) -> int:
        s = 0
        for i in range(0, len(data), 2):
            w = data[i] + (data[i + 1] << 8) if i + 1 < len(data) else data[i]
            s += w
        s = (s >> 16) + (s & 0xFFFF)
        s += s >> 16
        return (~s) & 0xFFFF

    sent = 0
    received = 0
    times: List[float] = []
    errors: List[str] = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout / max(count, 1))
    except PermissionError:
        return _ping_system(host, count, timeout) + (
            f"\n{DIM}(raw socket requires root/Administrator; fell back to system ping){RESET}"
        )

    for seq in range(count):
        sent += 1
        icmp_id = os.getpid() & 0xFFFF
        header = struct.pack("!BBHHH", 8, 0, 0, icmp_id, seq)
        payload = struct.pack("!d", time.time()) + b" net-analyzer ping " + bytes(range(48, 56))
        pkt = header + payload
        csum = _checksum(pkt)
        header = struct.pack("!BBHHH", 8, 0, csum, icmp_id, seq)
        pkt = header + payload

        try:
            sock.sendto(pkt, (ip, 0))
            start = time.time()
            data, addr = sock.recvfrom(1024)
            elapsed = (time.time() - start) * 1000

            # Extract ICMP header from IP packet (IP header is 20 bytes)
            icmp_header = data[20:28]
            icmp_type, icmp_code, _, _, _ = struct.unpack("!BBHHH", icmp_header)

            if icmp_type == 0 and icmp_code == 0:
                received += 1
                times.append(elapsed)
                lines.append(f"  {GREEN}✔{RESET}  seq={seq+1}  time={CYAN}{elapsed:.1f}{RESET} ms  from={addr[0]}")
            elif icmp_type == 3:
                errors.append(f"  {RED}✘{RESET}  seq={seq+1}  Destination Unreachable (code {icmp_code})")
            elif icmp_type == 11:
                errors.append(f"  {YELLOW}✘{RESET}  seq={seq+1}  TTL Exceeded")

        except socket.timeout:
            errors.append(f"  {RED}✘{RESET}  seq={seq+1}  timeout")
        except OSError as e:
            errors.append(f"  {RED}✘{RESET}  seq={seq+1}  {e}")

    sock.close()
    lines.extend(errors)

    loss = (sent - received) / sent * 100 if sent else 100
    lines.append("")
    lines.append(f"  {BOLD}---{RESET} {host} ping statistics {BOLD}---{RESET}")
    lines.append(f"  {_plural(sent, 'packet')} transmitted, {_plural(received, 'packet')} received, "
                 f"{RED if loss > 0 else GREEN}{loss:.1f}%{RESET} packet loss")
    if times:
        avg = sum(times) / len(times)
        mmin = min(times)
        mmax = max(times)
        lines.append(f"  rtt min/avg/max = {mmin:.2f}/{avg:.2f}/{mmax:.2f} ms")
    return "\n".join(lines)


# ── 2. Traceroute ─────────────────────────────────────────────────────────────
def cmd_trace(host: str, max_hops: int = 30, timeout: float = 3.0) -> str:
    """Traceroute via UDP with increasing TTL (like classic Unix traceroute)."""
    lines: List[str] = []
    ip = _resolve(host)
    lines.append(f"{BOLD}{CYAN}▸ TRACEROUTE{RESET}  {BOLD}{host}{RESET}  →  {ip or '(unresolved)'}")
    lines.append(f"  {DIM}max {_plural(max_hops, 'hop')}, UDP probes{RESET}\n")

    if not ip:
        return f"{RED}Could not resolve {host}{RESET}"

    dest_addr = (ip, 33434)  # classic traceroute base port

    for ttl in range(1, max_hops + 1):
        got_reply = False
        hop_ip = "*"
        hop_time = "*"
        hop_hostname = ""

        for _ in range(3):  # 3 probes per hop
            try:
                send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                send_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                send_sock.settimeout(timeout)

                recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                recv_sock.settimeout(timeout)

                start = time.time()
                send_sock.sendto(b"", dest_addr)

                data, addr = recv_sock.recvfrom(512)
                elapsed = (time.time() - start) * 1000

                send_sock.close()
                recv_sock.close()

                hop_ip = addr[0]
                hop_time = f"{elapsed:.1f} ms"
                got_reply = True

                try:
                    hop_hostname = socket.gethostbyaddr(hop_ip)[0]
                except (socket.herror, socket.gaierror):
                    hop_hostname = ""

                break  # got a response for this hop

            except socket.timeout:
                send_sock.close()
                recv_sock.close()
                continue
            except PermissionError:
                # fall back to system traceroute
                send_sock.close()
                recv_sock.close()
                lines.append(f"{DIM}(permission denied for raw sockets; falling back to system traceroute){RESET}")
                return _trace_system(host, max_hops)

        ttl_str = f"{ttl:2d}"
        if hop_ip == "*":
            lines.append(f"  {ttl_str}  {DIM}*{RESET}")
        else:
            name_part = f" ({BOLD}{hop_hostname}{RESET})" if hop_hostname else ""
            lines.append(f"  {ttl_str}  {hop_ip}{name_part}  {CYAN}{hop_time}{RESET}")

        if hop_ip == ip:
            lines.append(f"\n  {GREEN}✔ Destination reached in {_plural(ttl, 'hop')}{RESET}")
            break
    else:
        lines.append(f"\n  {YELLOW}⚠ Max hops ({max_hops}) reached without reaching destination{RESET}")

    return "\n".join(lines)


def _trace_system(host: str, max_hops: int) -> str:
    """Fallback: use system traceroute/tracert."""
    lines: List[str] = []
    ip = _resolve(host)
    lines.append(f"{BOLD}{CYAN}▸ TRACEROUTE{RESET}  {BOLD}{host}{RESET}  →  {ip or '(unresolved)'}")
    lines.append(f"  {DIM}system traceroute{RESET}\n")

    if platform.system() == "Windows":
        cmd = ["tracert", "-h", str(max_hops), host]
    else:
        cmd = ["traceroute", "-m", str(max_hops), "-n", host]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout or result.stderr
        for line in output.splitlines():
            stripped = line.strip()
            if stripped:
                lines.append(f"  {stripped}")
    except FileNotFoundError:
        lines.append(f"  {RED}traceroute command not available{RESET}")
    except subprocess.TimeoutExpired:
        lines.append(f"  {RED}traceroute timed out{RESET}")

    return "\n".join(lines)


# ── 3. Port Scan ──────────────────────────────────────────────────────────────
COMMON_PORTS: List[Tuple[int, str, str]] = [
    (21, "FTP", "File Transfer Protocol"),
    (22, "SSH", "Secure Shell"),
    (23, "Telnet", "Telnet"),
    (25, "SMTP", "Simple Mail Transfer"),
    (53, "DNS", "Domain Name System"),
    (80, "HTTP", "Hypertext Transfer"),
    (110, "POP3", "Post Office Protocol v3"),
    (143, "IMAP", "Internet Message Access"),
    (443, "HTTPS", "HTTP Secure"),
    (445, "SMB", "SMB/CIFS"),
    (993, "IMAPS", "IMAP over SSL"),
    (995, "POP3S", "POP3 over SSL"),
    (1433, "MSSQL", "Microsoft SQL Server"),
    (3306, "MySQL", "MySQL Database"),
    (3389, "RDP", "Remote Desktop Protocol"),
    (5432, "PostgreSQL", "PostgreSQL Database"),
    (5900, "VNC", "Virtual Network Computing"),
    (6379, "Redis", "Redis Cache"),
    (8080, "HTTP-Alt", "HTTP Alternate"),
    (8443, "HTTPS-Alt", "HTTPS Alternate"),
]


def cmd_scan(host: str, ports: Optional[List[int]] = None, timeout: float = 1.5) -> str:
    """Port scan common 20 ports (or custom list) via TCP connect scan."""
    lines: List[str] = []
    ip = _resolve(host)
    lines.append(f"{BOLD}{CYAN}▸ PORT SCAN{RESET}  {BOLD}{host}{RESET}  →  {ip or '(unresolved)'}")
    lines.append(f"  {DIM}TCP connect scan{RESET}\n")

    if not ip:
        return f"{RED}Could not resolve {host}{RESET}"

    scan_ports: List[Tuple[int, str, str]]
    if ports:
        scan_ports = [(p, str(p), "") for p in ports]
    else:
        scan_ports = COMMON_PORTS

    open_ports: List[Tuple[int, str, str]] = []
    closed = 0
    filtered = 0

    lines.append(f"  Scanning {len(scan_ports)} ports with {timeout}s timeout...\n")

    for port, name, desc in scan_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            desc_str = f" ({BLUE}{desc}{RESET})" if desc else ""
            lines.append(f"  {GREEN}✔ OPEN{RESET}  {port:>5}/{name:<7}{desc_str}")
            open_ports.append((port, name, desc))
        elif result == 11:  # EAGAIN/EWOULDBLOCK = filtered
            lines.append(f"  {YELLOW}? FILT{RESET}  {port:>5}/{name:<7}")
            filtered += 1
        else:
            closed += 1

    lines.append("")
    lines.append(f"  {BOLD}---{RESET} scan results {BOLD}---{RESET}")
    lines.append(f"  {GREEN}{_plural(len(open_ports), 'open port')}{RESET}, "
                 f"{DIM}{closed} closed{RESET}, "
                 f"{YELLOW}{filtered} filtered{RESET}")
    if open_ports:
        lines.append(f"  Open: {', '.join(f'{p}/{n}' for p, n, _ in open_ports)}")

    return "\n".join(lines)


# ── 4. Whois (via DNS whois servers for stdlib-only) ──────────────────────────
def cmd_whois(domain: str, server: str = "whois.iana.org", timeout: float = 10.0) -> str:
    """
    Whois lookup via TCP connection to whois server.
    Uses whois.iana.org as a starting point (it refers to the right registry).
    """
    lines: List[str] = []
    lines.append(f"{BOLD}{CYAN}▸ WHOIS{RESET}  {BOLD}{domain}{RESET}")
    lines.append(f"  {DIM}connecting to {server}{RESET}\n")

    # Strip protocol prefix if present
    domain = re.sub(r"^https?://(www\.)?", "", domain).split("/")[0].split("?")[0]

    try:
        data = _whois_query(domain, server, timeout)
        # Check for referral to another whois server
        ref_match = re.search(r"refer:\s*(\S+)", data, re.I)
        if ref_match and "whois.iana.org" in server:
            ref_server = ref_match.group(1)
            lines.append(f"{DIM}→ referred to {ref_server}{RESET}\n")
            data = _whois_query(domain, ref_server, timeout)

        # Also check for WHOIS_SERVER lines (common in RIR responses)
        if not ref_match:
            ws_match = re.search(r"Whois Server:\s*(\S+)", data, re.I)
            if ws_match:
                ref_server = ws_match.group(1)
                if ref_server.lower() != server.lower():
                    lines.append(f"{DIM}→ referred to {ref_server}{RESET}\n")
                    data = _whois_query(domain, ref_server, timeout)

        # Pretty-print
        for line in data.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("%") or stripped.startswith("#"):
                continue
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                lines.append(f"  {BOLD}{key.strip()}{RESET}: {val.strip()}")
            else:
                lines.append(f"  {stripped}")

    except (socket.timeout, OSError) as e:
        lines.append(f"  {RED}Whois query failed: {e}{RESET}")

    if len(lines) <= 3:
        lines.append(f"  {YELLOW}No whois data returned for {domain}{RESET}")

    return "\n".join(lines)


def _whois_query(domain: str, server: str, timeout: float) -> str:
    """Perform a raw TCP whois query."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((server, 43))
    sock.sendall(f"{domain}\r\n".encode())
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    sock.close()
    return data.decode("utf-8", errors="replace")


# ── 5. DNS Resolution ─────────────────────────────────────────────────────────
def cmd_dns(domain: str) -> str:
    """DNS resolution — A, AAAA, CNAME, MX, NS, TXT records."""
    lines: List[str] = []
    lines.append(f"{BOLD}{CYAN}▸ DNS RESOLUTION{RESET}  {BOLD}{domain}{RESET}\n")

    # A record
    try:
        a_records = socket.getaddrinfo(domain, None, socket.AF_INET)
        ips = sorted(set(ai[4][0] for ai in a_records))
        lines.append(f"  {BOLD}A (IPv4){RESET}")
        for ip in ips:
            lines.append(f"    {GREEN}{ip}{RESET}")
    except socket.gaierror:
        lines.append(f"  {DIM}A (IPv4): no records{RESET}")

    # AAAA record
    try:
        aaaa_records = socket.getaddrinfo(domain, None, socket.AF_INET6)
        ips6 = sorted(set(ai[4][0] for ai in aaaa_records))
        lines.append(f"  {BOLD}AAAA (IPv6){RESET}")
        for ip in ips6:
            lines.append(f"    {CYAN}{ip}{RESET}")
    except socket.gaierror:
        lines.append(f"  {DIM}AAAA (IPv6): no records{RESET}")

    # CNAME — check if domain is an alias
    try:
        cname = socket.getnameinfo((ips[0], 0), 0) if ips else None
    except Exception:
        cname = None

    # MX records via DNS query (stdlib can't query MX directly, so we show what we can)
    lines.append(f"  {BOLD}Nameservers (system default){RESET}")
    lines.append(f"    {DIM}{socket.getfqdn(domain)}{RESET}")

    # Canonical name
    try:
        host_info = socket.gethostbyname_ex(domain)
        if host_info[0] != domain:
            lines.append(f"  {BOLD}CNAME{RESET}")
            lines.append(f"    {YELLOW}{host_info[0]}{RESET}  →  {domain}")
    except socket.gaierror:
        pass

    lines.append(f"\n  {DIM}Note: MX, NS, TXT records require a DNS library (dnspython).{RESET}")
    lines.append(f"  {DIM}Install with: pip install dnspython{RESET}")

    return "\n".join(lines)


# ── 6. Speedtest ──────────────────────────────────────────────────────────────
SPEEDTEST_FILES = [
    # Large test files from various speed test services
    ("100MB", "https://speedtest.tele2.net/100MB.zip"),
    ("50MB", "https://speedtest.tele2.net/50MB.zip"),
    ("10MB", "https://speedtest.tele2.net/10MB.zip"),
    ("1MB", "https://speedtest.tele2.net/1MB.zip"),
]


def cmd_speedtest(target_size: str = "10MB", timeout: float = 30.0) -> str:
    """
    Speed test by downloading a test file and measuring throughput.
    Uses urllib (stdlib). Sizes: 1MB, 10MB, 50MB, 100MB.
    """
    lines: List[str] = []
    lines.append(f"{BOLD}{CYAN}▸ SPEEDTEST{RESET}")
    lines.append(f"  {DIM}measuring download speed{RESET}\n")

    # Find the closest matching file
    selected_url = None
    selected_label = target_size
    for label, url in SPEEDTEST_FILES:
        if label.lower() == target_size.lower() or label == target_size:
            selected_url = url
            selected_label = label
            break

    if not selected_url:
        # Use closest match
        selected_url = SPEEDTEST_FILES[2][1]  # default 10MB
        selected_label = SPEEDTEST_FILES[2][0]

    lines.append(f"  {BOLD}Test file:{RESET} {selected_label}")
    lines.append(f"  {BOLD}URL:{RESET} {selected_url}")
    lines.append(f"  {BOLD}Timeout:{RESET} {timeout}s\n")
    lines.append(f"  {YELLOW}Downloading...{RESET}")

    try:
        start = time.time()
        req = urllib.request.Request(selected_url, headers={
            "User-Agent": "net-analyzer/1.0",
            "Accept": "*/*",
        })

        downloaded = 0
        last_update = time.time()
        speeds: List[float] = []

        with urllib.request.urlopen(req, timeout=timeout) as response:
            total = int(response.headers.get("Content-Length", 0))
            if total:
                lines.append(f"  {DIM}Content-Length: {_format_bytes(total)}{RESET}\n")

            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                downloaded += len(chunk)
                now = time.time()
                elapsed = now - start

                if elapsed > 0:
                    speed_bps = downloaded / elapsed
                    # Report every ~second
                    if now - last_update >= 1.0:
                        speeds.append(speed_bps)
                        last_update = now
                        progress = (downloaded / total * 100) if total else 0
                        pct = f"{progress:.0f}%" if total else "?"
                        line = (
                            f"  {DIM}{pct}{RESET}"
                            f"  {_format_bytes(downloaded):>10}"
                            f"  @ {_format_speed(speed_bps):>12}/s"
                        )
                        lines.append(line)

        elapsed = time.time() - start
        if elapsed == 0:
            elapsed = 0.001
        total_speed = downloaded / elapsed

        lines.append("")
        lines.append(f"  {BOLD}---{RESET} speed test results {BOLD}---{RESET}")
        lines.append(f"  Downloaded: {GREEN}{_format_bytes(downloaded)}{RESET}")
        lines.append(f"  Time:       {CYAN}{elapsed:.2f}s{RESET}")
        lines.append(f"  Speed:      {BOLD}{_format_speed(total_speed)}/s{RESET}   "
                     f"({_format_speed_bits(total_speed)})")

        if speeds:
            peak = max(speeds)
            avg = sum(speeds) / len(speeds)
            lines.append(f"  Peak:       {_format_speed(peak)}/s")
            lines.append(f"  Avg:        {_format_speed(avg)}/s")

    except urllib.error.HTTPError as e:
        lines.append(f"\n  {RED}HTTP error: {e.code} {e.reason}{RESET}")
    except urllib.error.URLError as e:
        lines.append(f"\n  {RED}URL error: {e.reason}{RESET}")
    except (socket.timeout, OSError) as e:
        lines.append(f"\n  {RED}Network error: {e}{RESET}")

    return "\n".join(lines)


def _format_bytes(n: int) -> str:
    """Format byte count to human-readable."""
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TiB"


def _format_speed(bps: float) -> str:
    """Format bytes per second to human-readable."""
    return _format_bytes(int(bps))


def _format_speed_bits(bps: float) -> str:
    """Format bytes/s to bits/s representation."""
    bps_bits = bps * 8
    for unit in ("bps", "kbps", "Mbps", "Gbps"):
        if abs(bps_bits) < 1000.0:
            return f"{bps_bits:.1f} {unit}"
        bps_bits /= 1000.0
    return f"{bps_bits:.1f} Tbps"


# ── 7. All-in-one run ─────────────────────────────────────────────────────────
def cmd_all(host: str, ping_count: int = 3) -> str:
    """Run all network checks against a host."""
    sections: List[str] = []
    separator = f"\n  {DIM}{'─' * 50}{RESET}\n"

    sections.append(f"{BOLD}{MAGENTA}{'=' * 54}{RESET}")
    sections.append(f"{BOLD}{MAGENTA}  COMPREHENSIVE NETWORK ANALYSIS{RESET}")
    sections.append(f"{BOLD}{MAGENTA}  Target: {host}{RESET}")
    sections.append(f"{BOLD}{MAGENTA}{'=' * 54}{RESET}\n")

    # 1. DNS
    sections.append(cmd_dns(host))
    sections.append(separator)

    # 2. Ping
    sections.append(cmd_ping(host, count=ping_count))
    sections.append(separator)

    # 3. Traceroute (quick, 15 hops)
    sections.append(cmd_trace(host, max_hops=15))
    sections.append(separator)

    # 4. Port scan
    sections.append(cmd_scan(host))
    sections.append(separator)

    # 5. Whois
    sections.append(cmd_whois(host))

    sections.append(f"\n{BOLD}{GREEN}✔ All checks complete{RESET}")
    return "\n".join(sections)


# ── Output formatting helpers ─────────────────────────────────────────────────
def colorize_output(text: str, use_color: bool = True) -> str:
    """Return text with or without ANSI codes."""
    if use_color:
        return text
    return re.sub(r"\033\[[0-9;]*m", "", text)


def print_banner() -> None:
    """Print the net-analyzer banner."""
    banner = f"""
{BOLD}{CYAN}  ╔══════════════════════════════════════════╗
  ║       net-analyzer  v{__import__('net_analyzer').__version__:<11}║
  ║   Network Analysis CLI/TUI Tool             ║
  ╚══════════════════════════════════════════╝{RESET}
"""
    print(banner)


# ── CLI dispatch ──────────────────────────────────────────────────────────────
def dispatch(args: List[str]) -> None:
    """Parse and dispatch CLI commands."""
    if not args or args[0] in ("-h", "--help"):
        print_help()
        return

    if args[0] in ("-v", "--version"):
        print(f"net-analyzer v{__import__('net_analyzer').__version__}")
        return

    command = args[0]
    cmd_args = args[1:]

    commands = {
        "ping": _do_ping,
        "trace": _do_trace,
        "scan": _do_scan,
        "whois": _do_whois,
        "dns": _do_dns,
        "speedtest": _do_speedtest,
        "all": _do_all,
    }

    if command in commands:
        print_banner()
        result = commands[command](cmd_args)
        print(colorize_output(result))
    else:
        print(f"{RED}Unknown command: {command}{RESET}")
        print_help()
        sys.exit(1)


def print_help() -> None:
    """Print usage help."""
    print(f"""{BOLD}net-analyzer{RESET} — Network Analysis Tool

{BOLD}Usage:{RESET}
  net-analyzer {CYAN}<command>{RESET} {DIM}[options]{RESET}
  net-analyzer {CYAN}--tui{RESET}

{BOLD}Commands:{RESET}
  {CYAN}ping{RESET}     {DIM}<host>{RESET}               ICMP ping with statistics
  {CYAN}trace{RESET}    {DIM}<host>{RESET}               Traceroute to host
  {CYAN}scan{RESET}     {DIM}<host>{RESET}               Port scan (20 common ports)
  {CYAN}whois{RESET}    {DIM}<domain>{RESET}             Whois domain lookup
  {CYAN}dns{RESET}      {DIM}<domain>{RESET}             DNS record resolution
  {CYAN}speedtest{RESET} {DIM}[size]{RESET}              Download speed test (1MB/10MB/50MB/100MB)
  {CYAN}all{RESET}      {DIM}<host>{RESET}               Run all network checks

{BOLD}Options:{RESET}
  {YELLOW}--tui{RESET}                  Launch TUI mode
  {YELLOW}-h, --help{RESET}            Show this help
  {YELLOW}-v, --version{RESET}         Show version

{BOLD}Examples:{RESET}
  net-analyzer ping google.com
  net-analyzer trace cloudflare.com
  net-analyzer scan localhost
  net-analyzer whois example.com
  net-analyzer dns github.com
  net-analyzer speedtest 10MB
  net-analyzer all example.com
  net-analyzer --tui
""")


def _require_arg(args: List[str], cmd: str) -> str:
    """Require at least one argument."""
    if not args:
        print(f"{RED}Error: {cmd} requires a host/domain argument{RESET}")
        print_help()
        sys.exit(1)
    return args[0]


def _do_ping(args: List[str]) -> str:
    host = _require_arg(args, "ping")
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 4
    return cmd_ping(host, count=count)


def _do_trace(args: List[str]) -> str:
    host = _require_arg(args, "trace")
    return cmd_trace(host)


def _do_scan(args: List[str]) -> str:
    host = _require_arg(args, "scan")
    return cmd_scan(host)


def _do_whois(args: List[str]) -> str:
    domain = _require_arg(args, "whois")
    return cmd_whois(domain)


def _do_dns(args: List[str]) -> str:
    domain = _require_arg(args, "dns")
    return cmd_dns(domain)


def _do_speedtest(args: List[str]) -> str:
    size = args[0] if args else "10MB"
    return cmd_speedtest(size)


def _do_all(args: List[str]) -> str:
    host = _require_arg(args, "all")
    return cmd_all(host)
