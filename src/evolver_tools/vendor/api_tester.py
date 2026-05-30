#!/usr/bin/env python3
"""api-tester — HTTP API testing tool with method, headers, body, JSON, and timing support."""

import sys
import os
import argparse
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import ssl

METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']


def build_request(method, url, headers=None, data=None, json_data=None, timeout=30):
    """Build and execute an HTTP request."""
    if json_data is not None:
        data = json.dumps(json_data).encode('utf-8')
        if headers is None:
            headers = {}
        if 'Content-Type' not in {k.lower() for k in headers}:
            headers['Content-Type'] = 'application/json'
    elif data is not None and isinstance(data, str):
        data = data.encode('utf-8')

    req = urllib.request.Request(url, data=data, method=method.upper())
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return req, ctx


def do_request(method, url, headers=None, data=None, json_data=None, timeout=30):
    """Execute a single request and return result dict."""
    req, ctx = build_request(method, url, headers, data, json_data, timeout)
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=timeout)
        elapsed = time.time() - start
        body = resp.read()
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                body_parsed = json.loads(body)
                body_str = json.dumps(body_parsed, indent=2)
            except (json.JSONDecodeError, ValueError):
                body_str = body.decode('utf-8', errors='replace')
        else:
            body_str = body.decode('utf-8', errors='replace')
        return {
            'status': resp.status,
            'reason': resp.reason,
            'headers': dict(resp.headers),
            'body': body_str,
            'elapsed': elapsed,
            'error': None,
        }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        body = e.read()
        body_str = body.decode('utf-8', errors='replace')
        return {
            'status': e.code,
            'reason': e.reason,
            'headers': dict(e.headers),
            'body': body_str,
            'elapsed': elapsed,
            'error': None,
        }
    except urllib.error.URLError as e:
        return {
            'status': 0,
            'reason': str(e.reason),
            'headers': {},
            'body': '',
            'elapsed': 0,
            'error': str(e.reason),
        }
    except Exception as e:
        return {
            'status': 0,
            'reason': str(e),
            'headers': {},
            'body': '',
            'elapsed': 0,
            'error': str(e),
        }


def print_result(result, show_headers=True, show_body=True, verbose=False):
    """Print a formatted request result."""
    elapsed = result['elapsed']
    status = result['status']

    if result['error']:
        print(f"\033[91mERROR: {result['error']}\033[0m", file=sys.stderr)
        return

    if status >= 200 and status < 300:
        color = '\033[92m'
    elif status >= 300 and status < 400:
        color = '\033[93m'
    else:
        color = '\033[91m'
    print(f"{color}{status} {result['reason']}\033[0m  (\033[94m{elapsed:.3f}s\033[0m)")

    if show_headers and result['headers']:
        print(f"\n\033[1mHeaders:\033[0m")
        for k, v in result['headers'].items():
            if verbose or k.lower() not in ('set-cookie', 'x-powered-by'):
                print(f"  \033[33m{k}\033[0m: {v}")

    if show_body and result['body']:
        print(f"\n\033[1mBody:\033[0m")
        print(result['body'])


def benchmark(method, url, count, headers=None, data=None, json_data=None, timeout=30):
    """Run multiple requests and show stats."""
    times = []
    statuses = {}
    errors = 0

    print(f"\033[1mBenchmarking: {method} {url}\033[0m")
    print(f"  Requests: {count}")
    print()

    for i in range(count):
        result = do_request(method, url, headers, data, json_data, timeout)
        times.append(result['elapsed'])
        if result['error']:
            errors += 1
        else:
            s = result['status']
            statuses[s] = statuses.get(s, 0) + 1

        elapsed_str = f"\033[94m{result['elapsed']:.3f}s\033[0m"
        if result['error']:
            print(f"  [{i+1}/{count}] \033[91mERROR\033[0m - {result['error']} ({elapsed_str})")
        else:
            print(f"  [{i+1}/{count}] {result['status']} ({elapsed_str})")

    if times:
        print(f"\n\033[1mSummary:\033[0m")
        print(f"  Total time:  \033[94m{sum(times):.3f}s\033[0m")
        print(f"  Avg time:    \033[94m{sum(times)/len(times):.3f}s\033[0m")
        print(f"  Min time:    \033[94m{min(times):.3f}s\033[0m")
        print(f"  Max time:    \033[94m{max(times):.3f}s\033[0m")
        if len(times) > 1:
            variance = sum((t - sum(times)/len(times))**2 for t in times) / len(times)
            print(f"  Std dev:     \033[94m{variance**0.5:.3f}s\033[0m")
        print(f"  Errors:      \033[91m{errors}\033[0m" if errors else f"  Errors:      0")
        if statuses:
            status_str = ', '.join(f"{k}={v}" for k, v in sorted(statuses.items()))
            print(f"  Statuses:    {status_str}")


def main():
    parser = argparse.ArgumentParser(
        description='HTTP API testing tool. Send requests and inspect responses.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  api-tester GET https://api.example.com/users
  api-tester POST https://api.example.com/users -H "Content-Type: application/json" -d '{"name":"test"}'
  api-tester --benchmark 5 GET https://example.com
  api-tester PUT https://api.example.com/users/1 -j '{"name":"updated"}'
  api-tester DELETE https://api.example.com/users/1
        """,
    )
    parser.add_argument('method', nargs='?', choices=METHODS, help='HTTP method')
    parser.add_argument('url', nargs='?', help='Target URL')
    parser.add_argument('-H', '--header', action='append', dest='headers', default=[],
                        help='Request header (key:value, repeatable)')
    parser.add_argument('-d', '--data', help='Request body data (string)')
    parser.add_argument('-j', '--json', dest='json_data', help='JSON body (parsed)')
    parser.add_argument('--benchmark', type=int, metavar='N', help='Run N requests for benchmarking')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--no-headers', action='store_true', help='Hide response headers')
    parser.add_argument('--no-body', action='store_true', help='Hide response body')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all headers including verbose ones')

    args = parser.parse_args()

    if not args.method or not args.url:
        parser.print_help()
        sys.exit(1)

    headers = {}
    for h in args.headers:
        if ':' in h:
            k, v = h.split(':', 1)
            headers[k.strip()] = v.strip()
        else:
            print(f"Invalid header format: {h} (expected key:value)", file=sys.stderr)
            sys.exit(1)

    json_data = None
    if args.json_data:
        try:
            json_data = json.loads(args.json_data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON data: {e}", file=sys.stderr)
            sys.exit(1)

    data = args.data

    try:
        if args.benchmark:
            benchmark(args.method, args.url, args.benchmark, headers, data, json_data, args.timeout)
        else:
            result = do_request(args.method, args.url, headers, data, json_data, args.timeout)
            print_result(result, show_headers=not args.no_headers, show_body=not args.no_body, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
