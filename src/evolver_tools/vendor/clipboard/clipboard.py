#!/usr/bin/env python3
"""clipboard — Terminal clipboard tool (copy/paste)

Cross-platform clipboard access from command line.
Supports Linux (xclip/xsel/wayland), macOS (pbcopy/pbpaste), Windows (clip/Get-Clipboard).

Usage:
    echo "hello" | clipboard copy       # Copy stdin to clipboard
    clipboard copy file.txt              # Copy file content to clipboard
    clipboard paste                      # Paste clipboard to stdout
    clipboard clear                      # Clear clipboard
"""
import sys
import os
import subprocess
import shutil


def _detect_backend():
    """Detect available clipboard backend."""
    # Wayland
    if os.environ.get('WAYLAND_DISPLAY'):
        if shutil.which('wl-copy'):
            return ('wl-copy', 'wl-paste')
    # macOS
    if sys.platform == 'darwin':
        return ('pbcopy', 'pbpaste')
    # Windows
    if sys.platform == 'win32':
        return ('clip', 'powershell')
    # Linux X11
    if shutil.which('xclip'):
        return ('xclip', 'xclip')
    if shutil.which('xsel'):
        return ('xsel', 'xsel')
    return None


def cmd_copy(source=None):
    """Copy content to clipboard."""
    backend = _detect_backend()
    if not backend:
        print("Error: No clipboard backend found (install xclip/xsel/wl-clipboard)", file=sys.stderr)
        sys.exit(1)

    if source:
        # Copy from file
        if not os.path.isfile(source):
            print(f"Error: file not found: {source}", file=sys.stderr)
            sys.exit(1)
        with open(source, 'rb') as f:
            data = f.read()
    else:
        # Copy from stdin
        data = sys.stdin.buffer.read()
        if not data:
            print("Warning: empty input, nothing copied", file=sys.stderr)
            return

    copy_cmd, _ = backend
    try:
        if copy_cmd == 'clip':
            # Windows clip.exe
            subprocess.run(['clip'], input=data, check=True)
        elif copy_cmd == 'powershell':
            # Windows PowerShell
            ps_cmd = ['powershell', '-command', '[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8; $input | Set-Clipboard']
            subprocess.run(ps_cmd, input=data, check=True)
        elif copy_cmd == 'xclip':
            subprocess.run(['xclip', '-selection', 'clipboard'], input=data, check=True)
        elif copy_cmd == 'xsel':
            subprocess.run(['xsel', '--clipboard', '--input'], input=data, check=True)
        elif copy_cmd == 'wl-copy':
            subprocess.run(['wl-copy'], input=data, check=True)
        elif copy_cmd in ('pbcopy',):
            subprocess.run(['pbcopy'], input=data, check=True)
        size = len(data)
        print(f"Copied {size} byte{'s' if size != 1 else ''} to clipboard")
    except subprocess.CalledProcessError as e:
        print(f"Error: copy failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_paste():
    """Paste clipboard to stdout."""
    backend = _detect_backend()
    if not backend:
        print("Error: No clipboard backend found", file=sys.stderr)
        sys.exit(1)

    _, paste_cmd = backend
    try:
        if paste_cmd == 'powershell':
            result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, check=True)
        elif paste_cmd == 'xclip':
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, check=True)
        elif paste_cmd == 'xsel':
            result = subprocess.run(['xsel', '--clipboard', '--output'], capture_output=True, check=True)
        elif paste_cmd == 'wl-paste':
            result = subprocess.run(['wl-paste'], capture_output=True, check=True)
        elif paste_cmd in ('pbpaste',):
            result = subprocess.run(['pbpaste'], capture_output=True, check=True)
        else:
            print("Error: paste not supported on this backend", file=sys.stderr)
            sys.exit(1)
        sys.stdout.buffer.write(result.stdout)
        if result.stdout and not result.stdout.endswith(b'\n'):
            sys.stdout.buffer.write(b'\n')
    except subprocess.CalledProcessError:
        print("Error: clipboard empty or inaccessible", file=sys.stderr)
        sys.exit(1)


def cmd_clear():
    """Clear clipboard."""
    backend = _detect_backend()
    if not backend:
        print("Error: No clipboard backend found", file=sys.stderr)
        sys.exit(1)
    cmd_copy(b'')
    print("Clipboard cleared")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == 'copy':
        cmd_copy(rest[0] if rest else None)
    elif cmd == 'paste':
        cmd_paste()
    elif cmd == 'clear':
        cmd_clear()
    else:
        print(f"Error: unknown command '{cmd}' (use copy/paste/clear)", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
