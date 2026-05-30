#!/usr/bin/env python3
"""config-validator — Validate config files (JSON, YAML, TOML). Parse, show structure, check required fields.

Note: Uses only stdlib — implements basic YAML and TOML parsers without external deps."""

import sys
import os
import re
import json
import argparse


def parse_basic_yaml(content):
    """Parse a basic subset of YAML using stdlib only."""
    lines = content.split('\n')
    result = {}
    current_key = None
    current_indent = 0
    list_key = None
    list_items = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith('---'):
            continue

        indent = len(line) - len(line.lstrip())
        is_list_item = stripped.startswith('- ')

        if is_list_item:
            value = stripped[2:].strip()
            if list_key is None:
                continue
            list_items.append(value)
            continue
        else:
            if list_items and list_key:
                result[list_key] = list_items
                list_items = []
                list_key = None

        if ':' in stripped:
            colon_pos = stripped.index(':')
            key = stripped[:colon_pos].strip()
            value = stripped[colon_pos+1:].strip()
            if value == '':
                list_key = key
                list_items = []
            elif value:
                result[key] = parse_yaml_value(value)

    if list_items and list_key:
        result[list_key] = list_items

    return result


def parse_yaml_value(value):
    """Parse a YAML scalar value."""
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null' or value.lower() == '~':
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_basic_toml(content):
    """Parse a basic subset of TOML using stdlib only."""
    result = {}
    current_section = result
    current_path = []

    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith('[') and stripped.endswith(']'):
            section_name = stripped[1:-1].strip()
            current_path = section_name.split('.')
            current_section = result
            for part in current_path:
                if part not in current_section:
                    current_section[part] = {}
                current_section = current_section[part]
            continue
        if '=' in stripped:
            equals_pos = stripped.index('=')
            key = stripped[:equals_pos].strip()
            value = stripped[equals_pos+1:].strip()
            current_section[key] = parse_toml_value(value)

    return result


def parse_toml_value(value):
    """Parse a TOML value."""
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = []
        for item in inner.split(','):
            item = item.strip()
            if item:
                items.append(parse_toml_value(item))
        return items
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def detect_format(filepath):
    """Detect config file format from extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ('.json',):
        return 'json'
    if ext in ('.yaml', '.yml'):
        return 'yaml'
    if ext in ('.toml',):
        return 'toml'
    return None


def load_file(path):
    """Load file content, handling errors."""
    if not os.path.exists(path):
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def get_structure(data, indent=0):
    """Get structure representation of data."""
    lines = []
    prefix = '  ' * indent
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[90m{{...}}\033[0m")
                lines.extend(get_structure(val, indent + 1))
            elif isinstance(val, list):
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[90m[...]\033[0m (\033[33m{len(val)} items\033[0m)")
            elif isinstance(val, bool):
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[92m{val}\033[0m")
            elif isinstance(val, (int, float)):
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[94m{val}\033[0m")
            elif val is None:
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[90mnull\033[0m")
            else:
                val_str = str(val)
                if len(val_str) > 60:
                    val_str = val_str[:57] + '...'
                lines.append(f"{prefix}\033[1m{key}\033[0m: \033[93m\"{val_str}\"\033[0m")
    return lines


def check_required(data, required_fields, strict=False, prefix=''):
    """Check that required fields exist in data."""
    missing = []
    for field in required_fields:
        parts = field.split('.')
        current = data
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if not found:
            missing.append(field)
    return missing


def main():
    parser = argparse.ArgumentParser(
        description='Validate config files (JSON, YAML, TOML). Parse, show structure, check required fields.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  config-validator config.json
  config-validator --schema schema.json data.yaml
  config-validator --strict config.toml
  config-validator --show-structure config.json
        """,
    )
    parser.add_argument('file', help='Config file to validate')
    parser.add_argument('--schema', '-s', help='JSON schema file with required fields list')
    parser.add_argument('--strict', action='store_true', help='Strict mode (fail on warnings)')
    parser.add_argument('--show-structure', '-t', action='store_true', help='Show file structure')
    parser.add_argument('--required', '-r', help='Comma-separated list of required fields (e.g., "name,version,dependencies")')

    args = parser.parse_args()

    try:
        fmt = detect_format(args.file)
        if not fmt:
            print(f"Unknown format for {args.file}. Use .json, .yaml/.yml, or .toml extension.", file=sys.stderr)
            sys.exit(1)

        content = load_file(args.file)
        data = None
        errors = []
        warnings = []

        if fmt == 'json':
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON parse error: {e}")

        elif fmt == 'yaml':
            try:
                data = parse_basic_yaml(content)
            except Exception as e:
                errors.append(f"YAML parse error: {e}")

        elif fmt == 'toml':
            try:
                data = parse_basic_toml(content)
            except Exception as e:
                errors.append(f"TOML parse error: {e}")

        if errors:
            for e in errors:
                print(f"\033[91mERROR: {e}\033[0m", file=sys.stderr)
            sys.exit(1)

        print(f"\033[92m✓ Valid {fmt.upper()} file.\033[0m")

        if args.show_structure:
            print(f"\n\033[1mStructure:\033[0m")
            for line in get_structure(data):
                print(line)

        required_fields = []
        if args.required:
            required_fields.extend(args.required.split(','))
        if args.schema:
            schema_content = load_file(args.schema)
            try:
                schema = json.loads(schema_content)
                if isinstance(schema, list):
                    required_fields.extend(schema)
                elif isinstance(schema, dict) and 'required' in schema:
                    required_fields.extend(schema['required'])
            except json.JSONDecodeError as e:
                warnings.append(f"Schema file parse error: {e}")

        if required_fields:
            missing = check_required(data, required_fields, args.strict)
            if missing:
                for f in missing:
                    print(f"\033[91m✗ Missing required field: {f}\033[0m", file=sys.stderr)
                if args.strict:
                    sys.exit(1)
            else:
                print(f"\033[92m✓ All required fields present.\033[0m")

        if warnings:
            for w in warnings:
                print(f"\033[93mWARNING: {w}\033[0m", file=sys.stderr)

        if args.strict and not isinstance(data, dict):
            print(f"\033[91mERROR: Root element must be a dict in strict mode, got {type(data).__name__}\033[0m", file=sys.stderr)
            sys.exit(1)

        print(f"\033[92m✓ Validation complete.\033[0m")

    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
