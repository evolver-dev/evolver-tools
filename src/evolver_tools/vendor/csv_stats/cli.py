#!/usr/bin/env python3
"""csv-stats — CLI entry point."""

import sys
from pathlib import Path

from .analyzer import analyze_csv, print_report


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="csv-stats — CSV data analysis tool (zero dependencies)"
    )
    parser.add_argument("file", help="Path to CSV file")
    parser.add_argument("-d", "--delimiter", default=",", help="Delimiter (default: ,)")
    parser.add_argument("--max-rows", type=int, default=100000, help="Max rows to read")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--sample",
        type=int,
        default=10000,
        help="Only analyze first N rows (default: 10000, 0 = all)",
    )
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"✗ File not found: {args.file}")
        sys.exit(1)

    max_rows = args.sample if args.sample > 0 else None
    result = analyze_csv(args.file, max_rows=max_rows, delimiter=args.delimiter)

    if args.json:
        import json
        for h, s in result.get("col_stats", {}).items():
            if s and "histogram" in s:
                del s["histogram"]
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print_report(result)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "csv-stats",
    "func": "main",
    "desc": 'csv-stats',
}

if __name__ == "__main__":
    main()
