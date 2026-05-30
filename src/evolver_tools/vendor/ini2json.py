#!/usr/bin/env python3
"""ini2json — Convert INI/CFG files to JSON."""
import json
import sys

TOOL_META = {
    "name": "ini2json",
    "func": "main",
    "desc": "Convert INI to JSON. Usage: ini2json <file.ini> [--pretty]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: ini2json <file.ini> [--pretty]")
        print("       cat file.ini | ini2json")
        return
    pretty = "--pretty" in args
    filepath = None
    for a in args:
        if not a.startswith("-"):
            filepath = a
            break
    import configparser
    config = configparser.ConfigParser()
    try:
        if filepath:
            config.read(filepath)
        else:
            config.read_string(sys.stdin.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    result = {}
    for section in config.sections():
        result[section] = dict(config[section])
    indent = 2 if pretty else None
    print(json.dumps(result, indent=indent, default=str))

if __name__ == "__main__":
    main()
