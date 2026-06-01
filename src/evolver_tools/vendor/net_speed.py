#!/usr/bin/env python3
"""net-speed — Simple internet speed test.

Usage: net-speed [--timeout=5] [--size=1M]
       net-speed --server=example.com

Downloads a test file and measures throughput.
Zero-dependency (stdlib only — uses urllib).
"""

import sys, time, urllib.request, os

def format_speed(bytes_per_sec):
    if bytes_per_sec > 1_000_000:
        return f"{bytes_per_sec/1_000_000:.2f} MB/s"
    elif bytes_per_sec > 1_000:
        return f"{bytes_per_sec/1_000:.2f} KB/s"
    else:
        return f"{bytes_per_sec:.0f} B/s"

def format_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def main():
    args = sys.argv[1:]
    timeout = 10
    test_url = "http://speedtest.tele2.net/1MB.zip"

    for a in args:
        if a.startswith('--timeout='):
            timeout = int(a.split('=', 1)[1])
        elif a.startswith('--size='):
            size = a.split('=', 1)[1]
            if size == '1M':
                test_url = "http://speedtest.tele2.net/1MB.zip"
            elif size == '10M':
                test_url = "http://speedtest.tele2.net/10MB.zip"
            elif size == '100M':
                test_url = "http://speedtest.tele2.net/100MB.zip"
        elif a.startswith('--server='):
            test_url = a.split('=', 1)[1]

    print(f"  Testing download speed...")
    print(f"  Server: {test_url}")
    print()

    try:
        start = time.time()
        req = urllib.request.Request(test_url, headers={'User-Agent': 'net-speed/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = 0
            chunk_size = 8192
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                elapsed = time.time() - start
                if elapsed > 0:
                    speed = total / elapsed
                    sys.stderr.write(f"\r  Downloaded: {format_size(total)} @ {format_speed(speed)}")
                    sys.stderr.flush()

        elapsed = time.time() - start
        speed = total / elapsed if elapsed > 0 else 0
        sys.stderr.write("\n\n")
        print(f"  {'='*40}")
        print(f"  Size:      {format_size(total)}")
        print(f"  Time:      {elapsed:.2f}s")
        print(f"  Speed:     {format_speed(speed)}")
        print(f"  {'='*40}")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "net-speed",
    "func": "main",
    "desc": 'Internet download speed test',
}

if __name__ == '__main__':
    main()
