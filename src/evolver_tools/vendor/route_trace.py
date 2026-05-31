#!/usr/bin/env python3
"""route-trace — Trace network route to a host."""
import os
import subprocess
import sys

TOOL_META = {
    "name": "route-trace",
    "func": "main",
    "desc": "Trace network route to host. Usage: route-trace <host> [--max-hops 30]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: route-trace <host> [--max-hops 30]", file=sys.stderr)
        sys.exit(1)
    host = args[0]
    max_hops = 30
    if "--max-hops" in args:
        idx = args.index("--max-hops")
        if idx + 1 < len(args):
            max_hops = int(args[idx + 1])
    # Try traceroute
    cmd = None
    for c in ["traceroute", "tracert"]:
        path = subprocess.run(["which", c], capture_output=True, text=True).stdout.strip()
        if path:
            cmd = [c, "-m", str(max_hops), host]
            break
    if cmd:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(result.stdout)
                return
            else:
                print(f"traceroute error: {result.stderr}", file=sys.stderr)
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            print("traceroute timed out", file=sys.stderr)
    # Fallback: use socket
    try:
        import socket
        print(f"Tracing route to {host} (using TCP)...")
        print(f"  Target: {host}")
        try:
            ip = socket.gethostbyname(host)
            print(f"  Resolved: {ip}")
        except socket.gaierror:
            print(f"  Could not resolve {host}")
            sys.exit(1)
        # Simulated traceroute using UDP
        import time
        for ttl in range(1, max_hops + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                start = time.time()
                sock.sendto(b"", (host, 33434 + ttl))
                data, addr = sock.recvfrom(512)
                elapsed = (time.time() - start) * 1000
                hop_ip = addr[0] if addr else "*"
                try:
                    hop_name = socket.gethostbyaddr(hop_ip)[0]
                except Exception:
                    hop_name = hop_ip
                print(f"  {ttl:>3}  {hop_name} ({hop_ip})  {elapsed:.1f}ms")
                if hop_ip == ip:
                    print(f"  Reached destination in {ttl} hops")
                    break
            except socket.timeout:
                print(f"  {ttl:>3}  * * *  Request timed out")
            except OSError as e:
                if ttl == 1:
                    print(f"  {ttl:>3}  * * *  {e}")
                break
            finally:
                sock.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Install traceroute: apt install traceroute", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
