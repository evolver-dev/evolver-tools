#!/usr/bin/env python3
"""http-status — Look up HTTP status code meanings.

Usage: http-status 404
       http-status 2xx  # all 2xx codes
       http-status --search "not found"
       http-status --list  # list all codes
"""

import sys


_STATUS_CODES = {
    100: "Continue", 101: "Switching Protocols", 102: "Processing", 103: "Early Hints",
    200: "OK", 201: "Created", 202: "Accepted", 203: "Non-Authoritative Information",
    204: "No Content", 205: "Reset Content", 206: "Partial Content", 207: "Multi-Status",
    208: "Already Reported", 226: "IM Used",
    300: "Multiple Choices", 301: "Moved Permanently", 302: "Found", 303: "See Other",
    304: "Not Modified", 307: "Temporary Redirect", 308: "Permanent Redirect",
    400: "Bad Request", 401: "Unauthorized", 402: "Payment Required", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed", 406: "Not Acceptable",
    407: "Proxy Authentication Required", 408: "Request Timeout", 409: "Conflict",
    410: "Gone", 411: "Length Required", 412: "Precondition Failed",
    413: "Payload Too Large", 414: "URI Too Long", 415: "Unsupported Media Type",
    416: "Range Not Satisfiable", 417: "Expectation Failed",
    418: "I'm a Teapot", 421: "Misdirected Request", 422: "Unprocessable Entity",
    423: "Locked", 424: "Failed Dependency", 425: "Too Early", 426: "Upgrade Required",
    428: "Precondition Required", 429: "Too Many Requests",
    431: "Request Header Fields Too Large", 451: "Unavailable For Legal Reasons",
    500: "Internal Server Error", 501: "Not Implemented", 502: "Bad Gateway",
    503: "Service Unavailable", 504: "Gateway Timeout", 505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates", 507: "Insufficient Storage", 508: "Loop Detected",
    510: "Not Extended", 511: "Network Authentication Required",
}


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    if '--list' in args:
        for code in sorted(_STATUS_CODES):
            cat = f"{code // 100}xx"
            print(f"  {code:>3}  {_STATUS_CODES[code]:<35} [{cat}]")
        return

    if '--search' in args:
        idx = args.index('--search')
        if idx + 1 < len(args):
            q = args[idx + 1].lower()
            for code, msg in sorted(_STATUS_CODES.items()):
                if q in msg.lower():
                    print(f"  {code:>3}  {msg}")
        return

    if not args:
        print(__doc__)
        return

    for arg in args:
        arg = arg.lower()
        if arg.endswith('xx'):
            prefix = int(arg[0])
            for code, msg in sorted(_STATUS_CODES.items()):
                if code // 100 == prefix:
                    print(f"  {code:>3}  {msg}")
        else:
            try:
                code = int(arg)
                if code in _STATUS_CODES:
                    print(f"  {code:>3}  {_STATUS_CODES[code]}")
                else:
                    print(f"  {code:>3}  Unknown status code")
            except ValueError:
                print(f"  Unknown: {arg}")


TOOL_META = {
    "name": "http-status",
    "func": "main",
    "desc": "Look up HTTP status code meanings (search/list/lookup)"
}
