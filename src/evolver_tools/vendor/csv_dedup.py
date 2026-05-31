#!/usr/bin/env python3
"""csv-dedup — Deduplicate CSV rows by key column or all columns.

Usage:
  csv-dedup <file.csv> [--key=col] [--keep=first|last] [--output=out.csv] [--count]
  cat file.csv | csv-dedup [--key=col] [--keep=first|last] [--output=out.csv] [--count]

Detects delimiter (comma, tab, semicolon) from file extension or content sniffing.
Zero-dependency (stdlib only).
"""

import sys
import csv
import os
import io


# ---------------------------------------------------------------------------
# Delimiter detection helpers
# ---------------------------------------------------------------------------

EXT_DELIMITERS = {
    '.csv': ',',
    '.tsv': '\t',
    '.tab': '\t',
    '.psv': '|',
    '.ssv': ';',
}


def sniff_delimiter(sample: str) -> str:
    """Heuristic delimiter detection by counting occurrences in the header line."""
    header = sample.split('\n')[0] if sample else ''
    counts = {
        ',': header.count(','),
        '\t': header.count('\t'),
        ';': header.count(';'),
        '|': header.count('|'),
    }
    # Only consider delimiters that appear at least once
    candidates = {d: c for d, c in counts.items() if c > 0}
    if not candidates:
        return ','  # fallback
    return max(candidates, key=candidates.get)


def resolve_delimiter(filepath: str | None, sample: str) -> str:
    """Resolve delimiter: file extension wins if unambiguous, else sniff content."""
    if filepath:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in EXT_DELIMITERS:
            return EXT_DELIMITERS[ext]
    return sniff_delimiter(sample)


# ---------------------------------------------------------------------------
# Core dedup logic
# ---------------------------------------------------------------------------

def build_key(row: list[str], header: list[str], key_col: str | None) -> tuple:
    """Build a hashable key from a row.

    If key_col is None, uses the entire row (all columns).
    If key_col names a column, uses the value at that index.
    """
    if key_col is None:
        return tuple(row)
    try:
        idx = header.index(key_col)
    except ValueError:
        print(f"Error: column '{key_col}' not found in header", file=sys.stderr)
        print(f"  Available columns: {', '.join(header)}", file=sys.stderr)
        sys.exit(1)
    return (row[idx].strip(),)


def dedup_rows(
    rows: list[list[str]],
    header: list[str],
    key_col: str | None = None,
    keep: str = 'first',
) -> list[list[str]]:
    """Return deduplicated rows preserving order.

    keep='first'  — keeps the first occurrence of each key.
    keep='last'   — keeps the last occurrence of each key.
    """
    seen: dict[tuple, list[str]] = {}
    for row in rows:
        k = build_key(row, header, key_col)
        if keep == 'first':
            if k not in seen:
                seen[k] = row
        else:  # last
            seen[k] = row  # overwrite, so last wins
    # Preserve original order
    if keep == 'first':
        # seen was populated in order; dict is insertion-ordered (3.7+)
        return list(seen.values())
    else:
        # For 'last', rebuild in order of first occurrence of each key
        ordered: dict[tuple, list[str]] = {}
        for row in rows:
            k = build_key(row, header, key_col)
            ordered[k] = row  # each row overwrites, last write wins
        return list(ordered.values())


# ---------------------------------------------------------------------------
# Argument parsing (stdlib-only, no argparse)
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> dict:
    """Return dict with keys: filepath, key, keep, output, count, help."""
    args = {
        'filepath': None,
        'key': None,
        'keep': 'first',
        'output': None,
        'count': False,
        'help': False,
    }
    positional = []
    for a in argv:
        if a in ('-h', '--help'):
            args['help'] = True
        elif a.startswith('--key='):
            args['key'] = a.split('=', 1)[1]
        elif a.startswith('--keep='):
            val = a.split('=', 1)[1].lower()
            if val not in ('first', 'last'):
                print(f"Error: --keep must be 'first' or 'last', got '{val}'", file=sys.stderr)
                sys.exit(1)
            args['keep'] = val
        elif a.startswith('--output='):
            args['output'] = a.split('=', 1)[1]
        elif a == '--count':
            args['count'] = True
        elif a.startswith('-'):
            print(f"Error: unknown flag {a}", file=sys.stderr)
            sys.exit(1)
        else:
            positional.append(a)

    if len(positional) > 1:
        print("Error: too many positional arguments (expected at most 1 file)", file=sys.stderr)
        sys.exit(1)
    if positional:
        args['filepath'] = positional[0]

    return args


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args(sys.argv[1:])

    if args['help']:
        print(__doc__.strip())
        return

    filepath = args['filepath']

    # Read input
    try:
        if filepath:
            with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
                raw = f.read()
        else:
            if sys.stdin.isatty():
                print("Error: no input file specified and no data piped on stdin",
                      file=sys.stderr)
                print(__doc__.strip())
                sys.exit(1)
            raw = sys.stdin.read()
    except FileNotFoundError:
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: permission denied: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    if not raw.strip():
        print("Error: input is empty", file=sys.stderr)
        sys.exit(1)

    # Detect delimiter
    delimiter = resolve_delimiter(filepath, raw)

    # Parse CSV
    reader = csv.reader(io.StringIO(raw), delimiter=delimiter)
    all_rows = list(reader)

    if not all_rows:
        print("Error: no rows found in CSV data", file=sys.stderr)
        sys.exit(1)

    header = all_rows[0]
    data_rows = all_rows[1:]

    total = len(data_rows)

    if args['count']:
        # Just show counts
        if filepath:
            print(f"File: {filepath}")
        print(f"Delimiter: {repr(delimiter)}")
        print(f"Header: {', '.join(header)}")
        print(f"Total rows (excluding header): {total}")
        if total == 0:
            return
        unique_first = len(dedup_rows(data_rows, header, args['key'], 'first'))
        unique_last = len(dedup_rows(data_rows, header, args['key'], 'last'))
        print(f"Unique rows (keep=first): {unique_first}")
        print(f"Unique rows (keep=last):  {unique_last}")
        print(f"Duplicates removed (first): {total - unique_first}")
        print(f"Duplicates removed (last):  {total - unique_last}")
        return

    # Perform dedup
    deduped = dedup_rows(data_rows, header, args['key'], args['keep'])
    removed = total - len(deduped)

    # Build output data
    output_rows = [header] + deduped

    # Write output
    if args['output']:
        out_path = args['output']
        try:
            with open(out_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerows(output_rows)
        except PermissionError:
            print(f"Error: permission denied writing to {out_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error writing to {out_path}: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Wrote {len(deduped)} rows to {out_path}")
    else:
        # Print to stdout
        writer = csv.writer(sys.stdout, delimiter=delimiter)
        writer.writerows(output_rows)

    # Stats on stderr so they don't corrupt piped CSV output
    key_info = f" (key='{args['key']}')" if args['key'] else ''
    print(f"Stats: {total} total rows, {len(deduped)} unique, {removed} duplicates removed{key_info}",
          file=sys.stderr)


TOOL_META = {
    "name": "csv-dedup",
    "func": "main",
    "desc": "Deduplicate CSV rows by key column or all columns",
}

if __name__ == '__main__':
    main()
