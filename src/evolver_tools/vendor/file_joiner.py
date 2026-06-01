#!/usr/bin/env python3
"""file-joiner — Join split file chunks back together."""
import os
import re
import sys

TOOL_META = {
    "name": "file-joiner",
    "func": "main",
    "desc": "Join split file chunks. Usage: file-joiner <base_name> [--output file]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: file-joiner <base_name> [--output file]")
        print("  Joins files matching base_name.part*")
        return
    base = args[0]
    output = None
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output = args[idx + 1]
    # Find parts
    base_no_ext = os.path.splitext(base)[0]
    ext = os.path.splitext(base)[1]
    parts = []
    pattern = re.compile(re.escape(base_no_ext) + r"\.part(\d+)" + re.escape(ext) + "$")
    for f in os.listdir(os.path.dirname(base) or "."):
        m = pattern.match(f)
        if m:
            parts.append((int(m.group(1)), f))
    if not parts:
        # Try *.part* pattern
        pattern2 = re.compile(re.escape(base) + r"\.part(\d+)$")
        for f in os.listdir("."):
            m = pattern2.match(f)
            if m:
                parts.append((int(m.group(1)), f))
    if not parts:
        print(f"No parts found for: {base}", file=sys.stderr)
        sys.exit(1)
    parts.sort(key=lambda x: x[0])
    if not output:
        # Auto-detect output name
        name_only = os.path.basename(base)
        if ext:
            output = base
        else:
            # Remove .part suffix
            first_part = parts[0][1]
            output = re.sub(r"\.part\d+", "", first_part)
            if not os.path.splitext(output)[1]:
                output = base  # fallback
    total_size = 0
    is_binary = False
    for _, part_path in parts:
        try:
            with open(part_path, "rb") as f:
                header = f.read(1024)
                if b"\x00" in header:
                    is_binary = True
                    break
        except Exception:
            pass
    if is_binary:
        with open(output, "wb") as out:
            for _, part_path in parts:
                with open(part_path, "rb") as pf:
                    data = pf.read()
                    out.write(data)
                    total_size += len(data)
                print(f"  + {part_path}")
    else:
        with open(output, "w") as out:
            for _, part_path in parts:
                with open(part_path, "r") as pf:
                    data = pf.read()
                    out.write(data)
                    total_size += len(data.encode())
                print(f"  + {part_path}")
    print(f"\nJoined {len(parts)} parts → {output} ({total_size} bytes)")

if __name__ == "__main__":
    main()
