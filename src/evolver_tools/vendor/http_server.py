#!/usr/bin/env python3
"""http_server — Simple static file HTTP server.

Usage: http_server              # Port 8080, current dir
       http_server 3000         # Port 3000
       http_server 8080 ./docs  # Port 8080, serve ./docs
       http_server --bind 0.0.0.0 9090

Lightweight alternative to 'python -m http.server' with
better defaults and cleaner output.
"""

import os
import sys
import http.server
import socketserver

TOOL_META = {
    "name": "http_server",
    "func": "main",
    "desc": "Simple static file HTTP server",
}


def main():
    args = sys.argv[1:]
    port = 8080
    directory = os.getcwd()
    bind = '127.0.0.1'

    i = 0
    while i < len(args):
        if args[i] == '--bind' and i + 1 < len(args):
            bind = args[i + 1]
            i += 2
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            try:
                port = int(args[i])
            except ValueError:
                directory = os.path.abspath(args[i])
            i += 1

    if not os.path.isdir(directory):
        print(f"Error: directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler

    class SilentHandler(handler):
        def log_message(self, fmt, *args):
            sys.stderr.write(f"[HTTP] {args[0]} {args[1]} {args[2]}\n")

    try:
        with socketserver.TCPServer((bind, port), SilentHandler) as httpd:
            print(f"Serving {directory} at http://{bind}:{port}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")
