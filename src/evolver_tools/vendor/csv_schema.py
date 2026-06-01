#!/usr/bin/env python3
"""csv-schema — Infer CSV schema from a CSV file.

Detects column names, inferred types, null counts,
distinct values, min/max for numerics, and sample values.

Usage:
    csv-schema data.csv
    csv-schema --detailed data.csv
    csv-schema --summary data.csv
"""

import csv
import sys
import os

TOOL_META = {
    "name": "csv-schema",
    "func": "main",
    "desc": "Infer CSV schema (column types, nulls, stats, samples)",
}


def infer_type(values):
    """Infer the most specific type for a list of non-empty string values."""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "empty"

    # Check boolean first (strict: only true/false/yes/no/0/1)
    bool_vals = {"true", "false", "yes", "no"}
    if all(v.strip().lower() in bool_vals for v in non_empty):
        return "boolean"

    # Check integer
    all_int = True
    for v in non_empty:
        try:
            int(v.strip())
        except ValueError:
            all_int = False
            break
    if all_int:
        return "integer"

    # Check float
    all_float = True
    for v in non_empty:
        try:
            float(v.strip())
        except ValueError:
            all_float = False
            break
    if all_float:
        return "float"

    # Check date patterns (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)
    import re
    date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$|^\d{4}/\d{2}/\d{2}$")
    if all(date_pat.match(v.strip()) for v in non_empty):
        return "date"

    return "string"


def analyze_column(values):
    """Analyze a column's values."""
    non_empty = [v for v in values if v.strip()]
    empty_count = len(values) - len(non_empty)
    distinct = len(set(values))

    inferred = infer_type(values)
    stats = {"type": inferred, "nulls": empty_count, "non_null": len(non_empty),
             "distinct": distinct, "total": len(values)}

    if inferred in ("integer", "float"):
        nums = []
        for v in non_empty:
            try:
                nums.append(float(v.strip()))
            except ValueError:
                continue
        if nums:
            stats["min"] = min(nums)
            stats["max"] = max(nums)
            stats["mean"] = sum(nums) / len(nums)

    # Sample values (up to 5)
    seen = set()
    samples = []
    for v in values:
        if v.strip() and v not in seen:
            samples.append(v[:60])
            seen.add(v)
            if len(samples) >= 5:
                break
    stats["samples"] = samples

    return stats


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: csv-schema <file.csv> [--detailed] [--summary]")
        print("Analyze CSV structure: types, nulls, distinct values.")
        print("  --detailed    Show per-column stats")
        print("  --summary     Show brief column list only")
        sys.exit(0)

    path = args[0]
    detailed = "--detailed" in args
    summary = "--summary" in args

    if not os.path.exists(path):
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                print("Error: empty CSV file (no header)", file=sys.stderr)
                sys.exit(1)

            rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    num_cols = len(header)
    num_rows = len(rows)

    print(f"CSV Schema: {os.path.basename(path)}")
    print(f"  Columns: {num_cols}")
    print(f"  Rows:    {num_rows}")
    print()

    if summary:
        print(f"{'#':>3}  {'Name':<25} {'Type':<10}")
        print(f"{'---':>3}  {'----':<25} {'----':<10}")
        for i, col in enumerate(header, 1):
            values = [r[i - 1] if i - 1 < len(r) else "" for r in rows]
            t = infer_type(values)
            print(f"{i:>3}  {col:<25} {t:<10}")
        return

    # Detailed output
    for i, col in enumerate(header, 1):
        values = [r[i - 1] if i - 1 < len(r) else "" for r in rows]
        stats = analyze_column(values)

        print(f"[{i}] {col}")
        print(f"    Type:      {stats['type']}")
        print(f"    Non-null:  {stats['non_null']}/{stats['total']}")
        null_pct = (stats['nulls'] / stats['total'] * 100) if stats['total'] else 0
        if stats['nulls']:
            print(f"    Nulls:     {stats['nulls']} ({null_pct:.1f}%)")
        print(f"    Distinct:  {stats['distinct']}")

        if "min" in stats and "max" in stats:
            print(f"    Range:     {stats['min']} — {stats['max']}")
        if "mean" in stats:
            print(f"    Mean:      {stats['mean']:.2f}")

        if stats['samples']:
            print(f"    Samples:   {', '.join(stats['samples'])}")
        print()


if __name__ == "__main__":
    main()
