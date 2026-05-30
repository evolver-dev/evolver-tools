"""CLI entry point for urlparse — URL parser/debugger.

Usage:
    urlparse https://user:pass@example.com:8080/path;params?a=1&b=2#frag
    echo 'https://example.com/path?q=hello' | urlparse
    urlparse --encode 'hello world'
    urlparse --decode 'hello+world'
"""

import argparse
import sys
from urllib.parse import (
    urlparse,
    urlencode,
    parse_qs,
    parse_qsl,
    quote,
    unquote,
    urlunparse,
)


def parse_url(url: str) -> dict:
    """Parse a URL and return all components."""
    parsed = urlparse(url)
    result = {
        "url": url,
        "scheme": parsed.scheme or "",
        "netloc": parsed.netloc or "",
        "username": parsed.username or "",
        "password": parsed.password or "",
        "hostname": parsed.hostname or "",
        "port": parsed.port,
        "path": parsed.path or "",
        "params": parsed.params or "",
        "query": parsed.query or "",
        "fragment": parsed.fragment or "",
    }

    # Parse query string into key-value pairs
    if parsed.query:
        result["query_pairs"] = parse_qs(parsed.query, keep_blank_values=True)
        result["query_pairs_ordered"] = parse_qsl(parsed.query, keep_blank_values=True)
    else:
        result["query_pairs"] = {}
        result["query_pairs_ordered"] = []

    # Reconstruct the URL (canonical form)
    reconstructed = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    result["reconstructed"] = reconstructed

    return result


def format_parse_result(result: dict) -> str:
    """Format parsed URL components into a human-readable string."""
    lines = []
    lines.append(f"  URL:            {result['url']}")
    lines.append(f"  Reconstructed:  {result['reconstructed']}")
    lines.append("  ───────────────────────────────────────────")
    lines.append(f"  Scheme:         {result['scheme']}")
    lines.append(f"  Netloc:         {result['netloc']}")
    lines.append(f"    Username:     {result['username']}")
    lines.append(f"    Password:     {'●' * max(1, len(result['password'])) if result['password'] else ''}")
    lines.append(f"    Hostname:     {result['hostname']}")
    lines.append(f"    Port:         {result['port'] if result['port'] is not None else ''}")
    lines.append(f"  Path:           {result['path']}")
    lines.append(f"  Params:         {result['params']}")
    lines.append(f"  Query:          {result['query']}")
    lines.append(f"  Fragment:       {result['fragment']}")

    if result["query_pairs"]:
        lines.append("  ───────────────────────────────────────────")
        lines.append("  Query parameters:")
        for key, values in result["query_pairs"].items():
            for val in values:
                lines.append(f"    {key} = {val}")

    return "\n".join(lines)


def format_parse_result_json(result: dict) -> str:
    """Format parsed URL components as JSON."""
    import json

    output = {
        "url": result["url"],
        "scheme": result["scheme"],
        "netloc": result["netloc"],
        "username": result["username"],
        "password": result["password"],
        "hostname": result["hostname"],
        "port": result["port"],
        "path": result["path"],
        "params": result["params"],
        "query": result["query"],
        "fragment": result["fragment"],
    }

    if result["query_pairs"]:
        output["query_parameters"] = dict(result["query_pairs"])

    return json.dumps(output, indent=2)


def do_encode(text: str) -> str:
    """URL-encode a string."""
    return quote(text, safe="")


def do_decode(text: str) -> str:
    """URL-decode a string."""
    return unquote(text, encoding="utf-8", errors="replace")


def read_stdin() -> str:
    """Read raw input from stdin (pipe mode)."""
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="URL parser/debugger — parse, encode, and decode URLs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  urlparse https://example.com/path?q=hello#section\n"
            "  echo 'https://example.com/search?q=hello+world' | urlparse\n"
            "  urlparse --encode 'hello world'\n"
            "  urlparse --decode 'hello+world%21'\n"
            "  urlparse --json https://example.com?foo=1&bar=2\n"
        ),
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="URL to parse (omit to read from stdin)",
    )
    parser.add_argument(
        "--encode",
        nargs="?",
        const=True,
        metavar="TEXT",
        help="URL-encode the given text (or pipe input)",
    )
    parser.add_argument(
        "--decode",
        nargs="?",
        const=True,
        metavar="TEXT",
        help="URL-decode the given text (or pipe input)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output parse results as JSON",
    )

    args = parser.parse_args()

    # --- Encode mode ---
    if args.encode is not None:
        text = args.encode if isinstance(args.encode, str) else read_stdin()
        if not text:
            # If --encode was used as a flag with pipe, read_stdin already tried
            text = read_stdin()
        if not text:
            print("error: --encode requires text argument or pipe input", file=sys.stderr)
            sys.exit(1)
        print(do_encode(text))
        return

    # --- Decode mode ---
    if args.decode is not None:
        text = args.decode if isinstance(args.decode, str) else read_stdin()
        if not text:
            text = read_stdin()
        if not text:
            print("error: --decode requires text argument or pipe input", file=sys.stderr)
            sys.exit(1)
        print(do_decode(text))
        return

    # --- Parse mode ---
    url = args.url or read_stdin()

    if not url:
        parser.print_help()
        sys.exit(1)

    result = parse_url(url)

    if args.json:
        print(format_parse_result_json(result))
    else:
        print(format_parse_result(result))


if __name__ == "__main__":
    main()
