#!/usr/bin/env python3
"""scan-ports — TCP port scanner with range support.

Usage: scan-ports example.com [--ports=22,80,443]
       scan-ports 192.168.1.1 --ports=1-1000
       scan-ports localhost --ports=common  (scans 20 common ports)

Fast TCP port scanner using socket connection.
Zero-dependency (stdlib only).
"""

import sys, socket, time, concurrent.futures

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993,
                995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]

def parse_ports(port_str):
    ports = []
    for part in port_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            ports.extend(range(int(start), int(end)+1))
        else:
            ports.append(int(part))
    return sorted(set(ports))

def scan_port(host, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            # Try to get service banner
            try:
                service = socket.getservbyport(port, 'tcp')
            except:
                service = 'unknown'
            return port, 'open', service
        return port, 'closed', ''
    except:
        return port, 'filtered', ''

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    host = None
    port_str = 'common'
    timeout = 2
    max_workers = 50

    for a in args:
        if a.startswith('--ports='):
            port_str = a.split('=', 1)[1]
        elif a.startswith('--timeout='):
            timeout = int(a.split('=', 1)[1])
        elif a.startswith('--workers='):
            max_workers = min(200, int(a.split('=', 1)[1]))
        elif not a.startswith('-') and '.' in a or a == 'localhost':
            host = a
        elif not a.startswith('-'):
            host = a

    if not host:
        print("Error: host required")
        sys.exit(1)

    if port_str == 'common':
        ports = COMMON_PORTS
    else:
        ports = parse_ports(port_str)

    print(f"  Scanning {host} ({len(ports)} ports)")
    print(f"  Timeout: {timeout}s, Workers: {max_workers}")
    print()
    print(f"  {'PORT':<8} {'STATE':<10} {'SERVICE':<20}")
    print(f"  {'-'*8} {'-'*10} {'-'*20}")

    open_ports = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, host, p, timeout): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            port, state, service = future.result()
            if state == 'open':
                open_ports.append((port, service))
                print(f"  {port:<8} {state:<10} {service:<20}")
            sys.stderr.write(f"\r  Progress: {len([f for f in futures if f.done()])}/{len(ports)}")
            sys.stderr.flush()

    elapsed = time.time() - start_time
    sys.stderr.write('\n')
    print(f"\n  Scan complete: {len(open_ports)}/{len(ports)} open in {elapsed:.1f}s")

if __name__ == '__main__':
    main()
