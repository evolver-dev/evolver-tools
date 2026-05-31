#!/usr/bin/env python3
"""env_template — Generate .env.example from .env (strip values, keep keys).

Usage: env_template              # Reads .env, writes .env.example
       env_template .env.prod    # Reads specific file
       env_template --stdout     # Print to stdout instead

Strip all values from .env files, keeping only the keys and comments.
Useful for committing a safe .env.example to version control.
"""

import sys
import os
import re

TOOL_META = {
    "name": "env_template",
    "func": "main",
    "desc": "Generate .env.example from .env (strip values, keep keys)",
}


def main():
    args = sys.argv[1:]
    input_file = '.env'
    stdout_mode = False
    output_file = '.env.example'

    for arg in args:
        if arg == '--stdout':
            stdout_mode = True
        elif arg in ('-h', '--help'):
            print(__doc__)
            return
        elif not arg.startswith('--'):
            input_file = arg
        else:
            print(f"Unknown flag: {arg}", file=sys.stderr)
            sys.exit(1)

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_file) as f:
        lines = f.readlines()

    result = []
    for line in lines:
        stripped = line.rstrip('\n')
        # Comment line — keep as-is
        if stripped.strip().startswith('#'):
            result.append(stripped)
        # Empty line — keep
        elif not stripped.strip():
            result.append('')
        # Key=value line — strip value
        elif '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            # Detect inline comments after key
            comment = ''
            cm = re.search(r'\s+#.*$', stripped)
            if cm:
                comment = cm.group()
            result.append(f"{key}={comment.strip() if comment else ''}")
        else:
            # Keep lines that don't match known patterns
            result.append(stripped)

    output = '\n'.join(result)

    if stdout_mode:
        print(output)
    else:
        if not output_file:
            base, _ = os.path.splitext(input_file)
            output_file = f"{base}.example"
        with open(output_file, 'w') as f:
            f.write(output)
            f.write('\n')
        print(f"Written {output_file} ({len([l for l in result if '=' in l])} keys)")
