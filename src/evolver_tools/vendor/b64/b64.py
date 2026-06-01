#!/usr/bin/env python3
"""b64 — 零依赖 Base64 编解码工具

Usage:
    echo "hello" | b64 encode          # 从 stdin 编码
    echo "aGVsbG8K" | b64 decode       # 从 stdin 解码
    b64 encode file.txt                 # 从文件编码
    b64 decode file.b64                 # 从文件解码
    b64 -n "hello" encode               # 从参数编码
    b64 -n "aGVsbG8K" decode            # 从参数解码
"""

import sys
import base64
import os


STDIN_MODE_AUTO = 'auto'  # read stdin if no file and no -n


def encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def decode_bytes(data: bytes, strict: bool = False) -> bytes:
    try:
        if strict:
            # Strict mode: reject non-base64 characters
            return base64.b64decode(data.strip(), validate=True)
        return base64.b64decode(data.strip())
    except Exception as e:
        print(f"Error: invalid base64 input — {e}", file=sys.stderr)
        sys.exit(1)

def is_valid_base64(data: bytes) -> bool:
    """Check if data is valid base64 by testing decode+re-encode roundtrip."""
    try:
        # Use strict validation to reject non-base64 chars
        decoded = base64.b64decode(data.strip(), validate=True)
        # Verify roundtrip: re-encode and compare (stripped)
        reencoded = base64.b64encode(decoded).rstrip(b'=')
        cleaned = data.strip().rstrip(b'=')
        return reencoded == cleaned
    except Exception:
        return False


def read_stdin() -> bytes:
    try:
        return sys.stdin.buffer.read()
    except KeyboardInterrupt:
        sys.exit(1)


def main():
    args = sys.argv[1:]
    
    # Parse --help / -h
    if not args:
        # Check for piped stdin — auto-detect mode
        if not sys.stdin.isatty():
            raw_stdin = read_stdin()
            if not raw_stdin:
                sys.exit(0)
            if is_valid_base64(raw_stdin):
                result = base64.b64decode(raw_stdin.strip()).decode('utf-8', errors='replace')
                sys.stdout.write(result)
                if not result.endswith('\n'):
                    sys.stdout.write('\n')
            else:
                sys.stdout.write(base64.b64encode(raw_stdin).decode('ascii') + '\n')
            return
        print(__doc__.strip())
        return
    
    if args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return
    
    # Check for -n (inline value)
    if args[0] == '-n':
        if len(args) < 3:
            print("Error: -n requires both <value> and <action>", file=sys.stderr)
            sys.exit(1)
        value = args[1]
        action = args[2]
        
        if action == 'encode':
            result = encode_bytes(value.encode('utf-8'))
        elif action == 'decode':
            result = decode_bytes(value)
            result = result.decode('utf-8', errors='replace')
        else:
            print(f"Error: unknown action '{action}' (use encode/decode)", file=sys.stderr)
            sys.exit(1)
        
        sys.stdout.write(result)
        if not result.endswith('\n'):
            sys.stdout.write('\n')
        return
    
    # Parse <file> <action> or stdin
    action = None
    file_path = None
    
    for i, arg in enumerate(args):
        if arg in ('encode', 'decode'):
            action = arg
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            file_path = arg
    
    if action is None and file_path:
        if not os.path.isfile(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        # Auto-detect: read file, check if it's valid base64
        raw = open(file_path, 'rb').read()
        if is_valid_base64(raw):
            action = 'decode'
        else:
            action = 'encode'
    
    if action is None:
        # Remaining args are just the action
        for arg in args:
            if arg in ('encode', 'decode'):
                action = arg
            else:
                file_path = arg
    
    if action is None:
        # Try to auto-detect from stdin content if piped
        if not sys.stdin.isatty():
            raw_stdin = read_stdin()
            if not raw_stdin:
                sys.exit(0)
            # Heuristic: if looks like base64, decode; else encode
            try:
                base64.b64decode(raw_stdin.strip())
                result = base64.b64decode(raw_stdin.strip()).decode('utf-8', errors='replace')
                sys.stdout.write(result)
                if not result.endswith('\n'):
                    sys.stdout.write('\n')
            except Exception:
                sys.stdout.write(base64.b64encode(raw_stdin).decode('ascii') + '\n')
            return
        print(__doc__.strip())
        return
    
    # Read source
    if file_path:
        if not os.path.isfile(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        raw = open(file_path, 'rb').read()
    else:
        raw = read_stdin()
        if not raw:
            sys.exit(0)
    
    if action == 'encode':
        result = encode_bytes(raw)
    else:
        decoded = decode_bytes(raw)
        result = decoded.decode('utf-8', errors='replace')
    
    sys.stdout.write(result)
    if not result.endswith('\n'):
        sys.stdout.write('\n')


if __name__ == '__main__':
    main()
