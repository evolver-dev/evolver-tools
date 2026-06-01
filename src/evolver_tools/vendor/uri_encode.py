#!/usr/bin/env python3
"""uri-encode — URI/URL encode and decode tool."""
import sys
import urllib.parse

TOOL_META = {
    "name": "uri-encode",
    "func": "main",
    "desc": "URI encode/decode. Usage: uri-encode encode <text> | uri-encode decode <text>",
}

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print("Usage:")
        print("  uri-encode encode <text>   URL-encode a string")
        print("  uri-encode decode <text>   URL-decode a string")
        print("  uri-encode component <t>   Encode URI component")
        return
    cmd = args[0]
    text = " ".join(args[1:])
    try:
        if cmd == "encode":
            print(urllib.parse.quote(text, safe=""))
        elif cmd == "decode":
            print(urllib.parse.unquote(text))
        elif cmd == "component":
            print(urllib.parse.quote(text, safe="/?&="))
        elif cmd == "full":
            print(urllib.parse.quote(text, safe=""))
        else:
            print(f"Unknown: {cmd}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
