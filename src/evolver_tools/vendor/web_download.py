#!/usr/bin/env python3
"""web-download — Download files from the web with progress."""
import os
import sys
import urllib.request
import time

TOOL_META = {
    "name": "web-download",
    "func": "main",
    "desc": "Download files with progress. Usage: web-download <url> [--output file]",
}

def format_bytes(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: web-download <url> [--output file]")
        return
    url = args[0]
    output = None
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output = args[idx + 1]
    if not output:
        import pathlib
        try:
            parsed = urllib.parse.urlparse(url)
            output = os.path.basename(parsed.path) or "downloaded_file"
        except Exception:
            output = "downloaded_file"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "evolver-tools/13.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start = time.time()
            with open(output, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.time() - start
                    if elapsed > 0:
                        speed = downloaded / elapsed
                        if total > 0:
                            pct = downloaded * 100 / total
                            bar_len = 30
                            filled = int(bar_len * pct / 100)
                            bar = "█" * filled + "░" * (bar_len - filled)
                            eta = (total - downloaded) / max(speed, 1)
                            print(f"\r  |{bar}| {pct:.0f}% {format_bytes(downloaded)}/{format_bytes(total)} @ {format_bytes(speed)}/s ETA:{eta:.0f}s", end="", file=sys.stderr)
                        else:
                            print(f"\r  {format_bytes(downloaded)} @ {format_bytes(speed)}/s [{elapsed:.0f}s]", end="", file=sys.stderr)
            print(f"\n  ✓ Downloaded: {output}", file=sys.stderr)
            if total > 0:
                print(f"  Size: {format_bytes(total)}", file=sys.stderr)
                elapsed = time.time() - start
                speed = total / max(elapsed, 0.1)
                print(f"  Speed: {format_bytes(speed)}/s", file=sys.stderr)
        # Print the output path to stdout for piping
        print(output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
