#!/usr/bin/env python3
"""toml2json — Convert TOML to JSON."""
import json
import sys

TOOL_META = {
    "name": "toml2json",
    "func": "main",
    "desc": "Convert TOML to JSON. Usage: toml2json <file.toml> [--pretty]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: toml2json <file.toml> [--pretty]")
        print("       cat file.toml | toml2json")
        return
    pretty = "--pretty" in args
    filepath = None
    for a in args:
        if not a.startswith("-"):
            filepath = a
            break
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            try:
                import toml  # toml package
                if filepath:
                    with open(filepath) as f:
                        data = toml.load(f)
                else:
                    import io
                    data = toml.loads(sys.stdin.read())
                indent = 2 if pretty else None
                print(json.dumps(data, indent=indent, default=str))
                return
            except ImportError:
                # Minimal TOML parser
                print("No TOML library found. Install: pip install tomli", file=sys.stderr)
                sys.exit(1)
    try:
        if filepath:
            with open(filepath, "rb") as f:
                data = tomllib.load(f)
        else:
            data = tomllib.loads(sys.stdin.read())
        indent = 2 if pretty else None
        print(json.dumps(data, indent=indent, default=str))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
