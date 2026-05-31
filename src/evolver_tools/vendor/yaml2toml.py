#!/usr/bin/env python3
"""yaml2toml — Convert YAML to TOML format."""
import sys

TOOL_META = {
    "name": "yaml2toml",
    "func": "main",
    "desc": "Convert YAML to TOML. Usage: yaml2toml <file.yaml>",
}

def py_to_toml(data, prefix=""):
    lines = []
    if isinstance(data, dict):
        for key, val in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(val, dict):
                lines.append(f"[{full_key}]")
                lines.append(py_to_toml(val, full_key))
            elif isinstance(val, list):
                lines.append(f"{full_key} = {toml_repr(val)}")
            else:
                lines.append(f"{full_key} = {toml_repr(val)}")
    return "\n".join(l for l in lines if l)

def toml_repr(val):
    if isinstance(val, bool):
        return str(val).lower()
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, str):
        if '"' in val:
            return f"'{val}'"
        return f'"{val}"'
    elif isinstance(val, list):
        items = ", ".join(toml_repr(v) for v in val)
        return f"[{items}]"
    elif val is None:
        return '""'
    return str(val)

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: yaml2toml <file.yaml>")
        return
    filepath = args[0]
    try:
        import yaml
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if data is None:
            print("# Empty document")
            return
        print(py_to_toml(data))
    except ImportError:
        print("Install PyYAML: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
