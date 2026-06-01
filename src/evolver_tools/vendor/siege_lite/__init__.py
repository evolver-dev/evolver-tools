# -*- coding: utf-8 -*-
"""siege-lite — 轻量 HTTP 压力测试工具，零外部依赖"""

__version__ = "1.0.0"

import sys
import time
import json
import urllib.request
import urllib.error
import concurrent.futures
import statistics
from collections import Counter

# ANSI helpers
def red(s): return "\033[91m" + s + "\033[0m"
def green(s): return "\033[92m" + s + "\033[0m"
def yellow(s): return "\033[93m" + s + "\033[0m"
def dim(s): return "\033[2m" + s + "\033[0m"
def bold(s): return "\033[1m" + s + "\033[0m"

# Unicode chars (defined as constants to avoid f-string backslash issues in py<3.12)
CHECK = "\u2713"
CROSS = "\u2717"
BAR_FULL = "\u2588"
BAR_EMPTY = "\u2591"
HR = "\u2500" * 35
CHART = "\U0001f4ca"  # 📊

L = {
    'target': "\u76ee\u6807",
    'concurrency': "\u5e76\u53d1",
    'requests': "\u8bf7\u6c42\u6570",
    'timeout': "\u8d85\u65f6",
    'results': "\u7ed3\u679c",
    'metrics': "\u6307\u6807",
    'value': "\u503c",
    'total_time': "\u603b\u8017\u65f6",
    'success': "\u6210\u529f\u8bf7\u6c42",
    'failed': "\u5931\u8d25\u8bf7\u6c42",
    'throughput': "\u541e\u5410\u91cf",
    'avg_latency': "\u5e73\u5747\u5ef6\u8fdf",
    'min_max': "\u6700\u5c0f/\u6700\u5927",
    'status_dist': "\u72b6\u6001\u7801\u5206\u5e03",
    'latency_pct': "\u5ef6\u8fdf\u767e\u5206\u4f4d (ms)",
    'data': "\u4f20\u8f93\u6570\u636e",
    'rate': "\u4f20\u8f93\u901f\u7387",
}


def make_request(url, timeout=10):
    """Make a single HTTP request"""
    start = time.time()
    try:
        req = urllib.request.Request(url, method='GET',
            headers={'User-Agent': 'siege-lite/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.time() - start) * 1000
            content = resp.read()
            return {
                'success': True,
                'status': resp.status,
                'latency_ms': round(latency, 1),
                'size': len(content),
            }
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        return {
            'success': True,
            'status': e.code,
            'latency_ms': round(latency, 1),
            'size': 0,
        }
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            'success': False,
            'status': 0,
            'latency_ms': round(latency, 1),
            'error': str(e),
            'size': 0,
        }


def compute_percentiles(values, pts=None):
    """Compute latency percentiles"""
    if not values:
        return {}
    if pts is None:
        pts = [50, 75, 90, 95, 99, 99.9]
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    result = {}
    for p in pts:
        idx = min(int(n * p / 100), n - 1)
        result[p] = sorted_vals[idx]
    return result


def fmt_duration(seconds):
    if seconds < 1:
        return str(int(seconds * 1000)) + "ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        return f"{int(seconds // 60)}m{seconds % 60:.0f}s"


def run_benchmark(url, concurrency=10, requests=100, timeout=10):
    """Run the benchmark and print results"""
    # Header
    print()
    print(bold("⚡ siege-lite") + " \u2014 HTTP \u538b\u529b\u6d4b\u8bd5")
    print("  " + dim(L['target'] + ":") + " " + url)
    print("  " + dim(L['concurrency'] + ":") + " " + str(concurrency))
    print("  " + dim(L['requests'] + ":") + " " + str(requests))
    print("  " + dim(L['timeout'] + ":") + " " + str(timeout) + "s")
    print()

    results = []
    latencies = []
    status_counts = Counter()
    errors = 0

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url, timeout) for _ in range(requests)]

        done = 0
        for future in concurrent.futures.as_completed(futures):
            r = future.result()
            results.append(r)
            done += 1

            if r['success']:
                latencies.append(r['latency_ms'])
                status_counts[r['status']] += 1
            else:
                errors += 1
                status_counts['error'] += 1

            if done % max(1, requests // 10) == 0 or done == requests:
                pct = done * 100 // requests
                bar = BAR_FULL * (pct // 5) + BAR_EMPTY * (20 - pct // 5)
                sys.stdout.write(f"\r  {bar} {done}/{requests} ({pct}%)")
                sys.stdout.flush()

    total_time = time.time() - start_time

    print("\n\n" + bold(CHART + " " + L['results']))

    success_count = sum(1 for r in results if r['success'] and r['status'] < 500)

    def kv(key, val):
        print("  " + key.ljust(20) + val)

    kv(L['total_time'], fmt_duration(total_time))
    kv(L['success'], str(success_count) + " " + green(CHECK))
    if errors:
        kv(L['failed'], str(errors) + " " + red(CROSS))
    else:
        kv(L['failed'], "0")

    if total_time > 0:
        kv(L['throughput'], f"{success_count/total_time:.1f} req/s")
        if latencies:
            kv(L['avg_latency'], f"{statistics.mean(latencies):.1f}ms")
            kv(L['min_max'], f"{min(latencies):.1f}ms / {max(latencies):.1f}ms")

    # Status codes
    print("\n  " + L['status_dist'])
    total_status = sum(status_counts.values()) or 1
    for code, count in sorted(status_counts.items()):
        bar_len = int(count / total_status * 20)
        bar = BAR_FULL * bar_len
        label = str(code) if code != 'error' else red('error')
        print("    " + label.ljust(8) + bar + " " + str(count))

    # Percentiles
    if latencies:
        p = compute_percentiles(latencies)
        print("\n  " + L['latency_pct'])
        print("  " + HR)
        print("  P50     P75     P90     P95     P99     P99.9")
        print("  " + HR)
        print("  " + f"{p[50]:<8.1f}{p.get(75,0):<8.1f}{p[90]:<8.1f}"
                     f"{p[95]:<8.1f}{p[99]:<8.1f}{p.get(99.9,0):<8.1f}")

    # Data transfer
    total_bytes = sum(r.get('size', 0) for r in results)
    if total_bytes > 0:
        mb = total_bytes / 1048576
        print()
        kv(L['data'], f"{mb:.2f} MB")
        if total_time > 0:
            kv(L['rate'], f"{mb/total_time:.2f} MB/s")

    print()

    return {
        'url': url,
        'concurrency': concurrency,
        'requests': requests,
        'total_time': round(total_time, 3),
        'success_count': success_count,
        'error_count': errors,
        'throughput': round(success_count / total_time, 1) if total_time > 0 else 0,
        'avg_latency': round(statistics.mean(latencies), 1) if latencies else 0,
        'max_latency': round(max(latencies), 1) if latencies else 0,
        'min_latency': round(min(latencies), 1) if latencies else 0,
        'percentiles': {str(k): round(v, 1) for k, v in p.items()},
        'status_codes': dict(status_counts),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="\u8f7b\u91cf HTTP \u538b\u529b\u6d4b\u8bd5\u5de5\u5177")
    parser.add_argument('url', help="\u76ee\u6807 URL")
    parser.add_argument('-c', '--concurrency', type=int, default=10,
                        help="\u5e76\u53d1\u6570 (\u9ed8\u8ba4: 10)")
    parser.add_argument('-n', '--requests', type=int, default=100,
                        help="\u8bf7\u6c42\u603b\u6570 (\u9ed8\u8ba4: 100)")
    parser.add_argument('-t', '--timeout', type=int, default=10,
                        help="\u8d85\u65f6\u79d2\u6570 (\u9ed8\u8ba4: 10)")
    parser.add_argument('--json', action='store_true',
                        help="JSON 格式输出")
    args = parser.parse_args()

    try:
        result = run_benchmark(
            url=args.url,
            concurrency=args.concurrency,
            requests=args.requests,
            timeout=args.timeout,
        )

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
        print("\n" + yellow("\u6d4b\u8bd5\u88ab\u7528\u6237\u4e2d\u65ad"))
    except Exception as e:
        print("\n" + red(f"\u9519\u8bef: {e}"))
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "siege-lite",
    "func": "main",
    "desc": 'HTTP load tester (concurrency, latency percentile)',
}

if __name__ == '__main__':
    main()
