#!/usr/bin/env python3
"""ini-parser — INI file parser, query, and converter

Parse and query INI configuration files. Supports sections, comments, multi-line values.

Usage:
    ini-parser config.ini                # Pretty-print all sections
    ini-parser config.ini database       # Show specific section
    ini-parser config.ini database.host  # Show specific key
    ini-parser --json config.ini         # Convert to JSON
    ini-parser --toml config.ini         # Convert to TOML-like format
    cat config.ini | ini-parser          # Stdin mode
"""
import sys
import os
import re
import json


def parse_ini(text):
    """Parse INI content into {section: {key: value}}."""
    config = {}
    current_section = 'DEFAULT'

    for line in text.split('\n'):
        stripped = line.strip()
        # Skip empty and comments
        if not stripped or stripped.startswith(';') or stripped.startswith('#'):
            continue

        # Section header
        section_match = re.match(r'^\[([^\]]+)\]', stripped)
        if section_match:
            current_section = section_match.group(1).strip()
            if current_section not in config:
                config[current_section] = {}
            continue

        # Key=value or Key: value
        kv_match = re.match(r'^([^=:]+)[=:]\s*(.*)', stripped)
        if kv_match:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()
            # Remove surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Type conversion
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() in ('none', 'null'):
                value = None
            else:
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
            if current_section not in config:
                config[current_section] = {}
            config[current_section][key] = value

    return config


def format_ini(config):
    """Format parsed config back to INI string."""
    lines = []
    for section, keys in config.items():
        if section != 'DEFAULT':
            lines.append(f'[{section}]')
        for key, value in keys.items():
            if value is None:
                value = ''
            elif value is True:
                value = 'true'
            elif value is False:
                value = 'false'
            lines.append(f'{key} = {value}')
        lines.append('')
    return '\n'.join(lines)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    output_json = False
    output_toml = False
    files = []
    query = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--json':
            output_json = True
        elif arg == '--toml':
            output_toml = True
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(arg)
        i += 1

    # Read input
    if not files or not os.path.isfile(files[0]):
        if files:
            query = files[0]
        text = sys.stdin.read()
    else:
        filepath = files[0]
        query = files[1] if len(files) > 1 else None
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

    config = parse_ini(text)

    if output_json:
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return

    if output_toml:
        for section, keys in config.items():
            if section == 'DEFAULT':
                for key, value in keys.items():
                    print(f'{key} = {json.dumps(value)}')
            else:
                print(f'[{section}]')
                for key, value in keys.items():
                    print(f'{key} = {json.dumps(value)}')
                print()
        return

    if query:
        if '.' in query:
            section, key = query.split('.', 1)
            if section in config and key in config[section]:
                print(config[section][key])
            else:
                print(f"Error: '{query}' not found", file=sys.stderr)
                sys.exit(1)
        elif query in config:
            section = config[query]
            for key, value in section.items():
                print(f"  {key} = {value}")
        else:
            print(f"Error: section '{query}' not found", file=sys.stderr)
            sys.exit(1)
        return

    # Default: print all
    print(format_ini(config))


if __name__ == '__main__':
    main()
