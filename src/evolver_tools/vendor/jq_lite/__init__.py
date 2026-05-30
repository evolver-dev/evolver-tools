"""jq-lite: Zero-dependency JSON query tool (pure Python stdlib jq alternative)."""

import sys
import json
import re
import operator
from pathlib import Path


__version__ = "1.0.0"


def parse_query(query: str):
    """Parse a jq-like query string into a chain of filters."""
    if not query:
        return [("identity",)]

    # Split by pipe
    stages = []
    for part in query.split("|"):
        part = part.strip()
        if not part:
            continue
        stages.append(part)

    if not stages:
        return [("identity",)]

    filters = []
    for stage in stages:
        filters.append(parse_stage(stage))
    return filters


def parse_stage(stage: str):
    """Parse a single pipeline stage."""
    stage = stage.strip()

    if stage == ".":
        return ("identity",)

    # Array iteration: .[]
    m = re.match(r'^\.\[\]$', stage)
    if m:
        return ("iterate",)

    # Array iteration with index: .[0], .[1:3], .[-1]
    m = re.match(r'^\.\[([^\]]+)\]$', stage)
    if m:
        idx_str = m.group(1)
        return parse_index(idx_str)

    # Object key access: .key, .key.subkey, .key[0].subkey
    if stage.startswith("."):
        parts = stage[1:].split(".")
        # Parse each part, handling key[index] patterns
        chain = []
        for p in parts:
            # Check for array index suffix like [0], [1:3]
            bracket_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)(\[([^\]]+)\])?$', p)
            if bracket_match and bracket_match.group(2):
                # Part has both key and index: e.g. "users[0]"
                chain.append(("key", bracket_match.group(1)))
                idx_part = parse_index(bracket_match.group(3))
                if isinstance(idx_part, tuple):
                    chain.append(idx_part)
                else:
                    chain.append(idx_part)
            else:
                chain.append(("key", p))
        if len(chain) == 1:
            return chain[0]
        return ("chain", chain)

    # Key access without dot prefix
    m = re.match(r'^"([^"]+)"$', stage)
    if m:
        return ("key", m.group(1))

    return ("identity",)


def parse_index(idx_str: str):
    """Parse array index expression."""
    idx_str = idx_str.strip()

    # Slice: 0:2, :3, 1:, -1:
    if ":" in idx_str:
        parts = idx_str.split(":")
        start = int(parts[0]) if parts[0] else None
        end = int(parts[1]) if len(parts) > 1 and parts[1] else None
        return ("slice", start, end)

    # Negative index
    return ("index", int(idx_str))


def apply_filters(data, filters):
    """Apply a chain of filters to data, yielding results."""
    results = [data]

    for filter_type, *args in filters:
        new_results = []
        for item in results:
            try:
                if filter_type == "identity":
                    new_results.append(item)
                elif filter_type == "key":
                    key = args[0]
                    if isinstance(item, dict):
                        new_results.append(item[key])
                    else:
                        return []
                elif filter_type == "index":
                    idx = args[0]
                    if isinstance(item, (list, tuple)):
                        new_results.append(item[idx])
                    else:
                        return []
                elif filter_type == "slice":
                    start, end = args
                    if isinstance(item, (list, tuple)):
                        new_results.extend(item[start:end])
                    else:
                        return []
                elif filter_type == "iterate":
                    if isinstance(item, (list, tuple)):
                        new_results.extend(item)
                    elif isinstance(item, dict):
                        new_results.extend(item.values())
                    else:
                        return []
                elif filter_type == "chain":
                    # Apply sub-filters in sequence
                    sub_results = [item]
                    for sub_filter in args[0]:
                        tmp = []
                        for sr in sub_results:
                            ft, *fa = sub_filter
                            try:
                                if ft == "key":
                                    if isinstance(sr, dict):
                                        tmp.append(sr[fa[0]])
                                elif ft == "index":
                                    if isinstance(sr, (list, tuple)):
                                        tmp.append(sr[fa[0]])
                                else:
                                    tmp.append(sr)
                            except (KeyError, IndexError, TypeError):
                                return []
                        sub_results = tmp
                    new_results.extend(sub_results)
            except (KeyError, IndexError, TypeError):
                return []
        results = new_results
        if not results:
            return []

    return results


def format_result(value, raw=False):
    """Format a single result value."""
    if raw:
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return json.dumps(value, ensure_ascii=False)
    else:
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool, type(None))):
            return json.dumps(value, ensure_ascii=False)
        else:
            return json.dumps(value, ensure_ascii=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="jq-lite — Zero-dependency JSON query tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jq-lite '.name' data.json                # Extract key
  jq-lite '.users[0].name' data.json        # Nested + array
  jq-lite '.items[] | .id' data.json        # Iterate + pipe
  echo '{"a":1,"b":2}' | jq-lite '.[]'      # Iterate values
  jq-lite '.' data.json                     # Pretty-print entire file
  jq-lite -r '.name' data.json              # Raw output (no string quotes)
        """
    )
    parser.add_argument("query", help="jq-like query expression (e.g. '.key', '.key[0]', '.[] | .name')")
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("-r", "--raw-output", action="store_true", help="Output raw strings without JSON quoting")
    parser.add_argument("--compact", action="store_true", help="Compact output (no pretty-print for objects)")

    args = parser.parse_args()

    # Read input
    if args.input:
        try:
            with open(args.input, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            print("Error: no input (pipe JSON or provide a file)", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(stdin_data)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    # Parse and apply query
    try:
        filters = parse_query(args.query)
    except Exception as e:
        print(f"Error: invalid query: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        results = apply_filters(data, filters)
    except Exception as e:
        print(f"Error: query failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        sys.exit(0)

    # Format and output
    output_lines = []
    for r in results:
        formatted = format_result(r, raw=args.raw_output)
        if isinstance(r, (dict, list)) and not args.compact:
            formatted = json.dumps(r, ensure_ascii=False, indent=2)
        output_lines.append(formatted)

    print("\n".join(output_lines))



# === Auto-registration metadata ===
TOOL_META = {
    "name": "jq-lite",
    "func": "main",
    "desc": 'Jq Lite',
}

if __name__ == "__main__":
    main()
