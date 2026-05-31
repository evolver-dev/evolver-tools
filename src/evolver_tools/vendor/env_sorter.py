#!/usr/bin/env python3
"""env-sorter — Sort environment variables in .env files alphabetically.

Usage:
  env-sorter --file .env
  env-sorter --file .env --in-place
  env-sorter --file .env --sort-by value
  env-sorter --file .env --group
  env-sorter --file .env --remove-dups
  env-sorter --file .env --in-place --group --sort-by value --remove-dups

Sorts the content of dotenv-style files while preserving comments and
blank lines as best possible. Supports grouping by common prefix,
sorting by name or value, and deduplication.
"""

import sys
import os


TOOL_META = {
    "name": "env-sorter",
    "func": "main",
    "desc": "Sort environment variables in .env files",
}


# ---------------------------------------------------------------------------
# .env parsing & writing
# ---------------------------------------------------------------------------

def parse_env(text):
    """Parse .env text into a list of (kind, key, value) tuples.

    Each tuple is one of:
      ('blank', None, None)      — empty line
      ('comment', None, text)    — comment line (includes leading ``#``)
      ('var', key, value)        — KEY=VALUE assignment
    Order is preserved as-is.
    """
    entries = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == "":
            entries.append(("blank", None, None))
        elif stripped.startswith("#"):
            entries.append(("comment", None, line))
        elif "=" in stripped:
            # Split on first '=' only
            key, _, val = line.partition("=")
            entries.append(("var", key.rstrip(), val))
        else:
            # Lines that don't match any pattern — treat as literal
            entries.append(("comment", None, line))
    return entries


def _get_prefix(key, sep="_"):
    """Return the prefix of *key* (everything before the first separator)."""
    idx = key.find(sep)
    if idx == -1:
        return ""
    return key[:idx]


def group_sort(entries, sort_key="name", group=True, remove_dups=False):
    """Sort *entries* by variable key/value with optional grouping & dedup.

    Parameters
    ----------
    entries : list[tuple]
        Parsed entries from :func:`parse_env`.
    sort_key : str
        ``"name"`` (default) sorts by variable name; ``"value"`` sorts by
        value (ties broken by name).
    group : bool
        When *True*, entries are grouped by prefix (everything before the
        first ``_``).  Blank lines and comments stay in their relative
        position between groups.
    remove_dups : bool
        When *True*, only the *last* occurrence of a variable name is kept.
    """
    # Separate non-variable entries and variable entries
    non_vars = [(i, e) for i, e in enumerate(entries) if e[0] != "var"]
    var_entries = [(i, e) for i, e in enumerate(entries) if e[0] == "var"]

    if remove_dups:
        seen = {}
        # Iterate in original order so the *last* occurrence wins
        for idx, e in var_entries:
            seen[e[1]] = (idx, e)
        var_entries = sorted(seen.values(), key=lambda x: x[0])

    # Build sort key for each variable entry
    def _sort_key(item):
        idx, e = item
        key = e[1]
        val = e[2].lstrip()
        if sort_key == "value":
            primary = val.lower() if val else ""
            secondary = key.lower()
        else:
            primary = key.lower()
            secondary = ""
        if group:
            prefix = _get_prefix(key)
            return (prefix, primary, secondary, idx)
        return (primary, secondary, idx)

    var_entries.sort(key=_sort_key)

    if group:
        return _interleave_groups(var_entries, non_vars, entries)
    else:
        return _rebuild(var_entries, non_vars)


def _interleave_groups(var_entries, non_vars, original_entries):
    """Interleave non-variable lines between groups of variable entries.

    Non-variable lines (blanks, comments) that appeared *between* groups
    in the original file are placed before each group.  Trailing
    non-variable lines are appended at the end.
    """
    # Determine groups
    groups = []
    current_group_key = None
    current_group = []
    for idx, e in var_entries:
        prefix = _get_prefix(e[1])
        if prefix != current_group_key:
            if current_group:
                groups.append((current_group_key, current_group))
            current_group_key = prefix
            current_group = []
        current_group.append((idx, e))
    if current_group:
        groups.append((current_group_key, current_group))

    # Map original index to its entry
    original_by_idx = {i: e for i, e in enumerate(original_entries)}

    # Assign non-var lines to groups based on proximity in original file
    # Simple approach: split non_vars at the boundaries between groups
    if not groups:
        return [e for _, e in sorted(non_vars, key=lambda x: x[0])]

    # Collect boundaries: the indices where each group started in the original
    group_boundaries = [(g[0][0], g) for g in groups]  # (start_idx, group_data)

    result = []
    non_var_iter = iter(sorted(non_vars, key=lambda x: x[0]))
    consumed = set()

    for g_idx, (g_start, (g_prefix, g_entries)) in enumerate(group_boundaries):
        # Add non-var lines that appeared before this group in the original
        while True:
            try:
                nv_idx, nv_entry = next(non_var_iter)
            except StopIteration:
                break
            if nv_idx > g_start and g_idx > 0:
                # This non-var belongs to the previous group, put it back
                # Actually let's just insert any non-var that's before the group start
                if nv_idx < g_start:
                    result.append(nv_entry)
                    consumed.add(nv_idx)
                else:
                    # Put it back by recreating the iterator
                    # Simple: just add all remaining non-vars at the end
                    non_var_iter = iter([(nv_idx, nv_entry)] + list(non_var_iter))
                    break
            else:
                if nv_idx < g_start:
                    result.append(nv_entry)
                    consumed.add(nv_idx)
                else:
                    non_var_iter = iter([(nv_idx, nv_entry)] + list(non_var_iter))
                    break

        # Add the group entries
        for _, e in g_entries:
            result.append(e)

    # Add any remaining non-var lines
    for nv_idx, nv_entry in sorted(non_vars, key=lambda x: x[0]):
        if nv_idx not in consumed and nv_idx not in {id(e) for e in result}:
            result.append(nv_entry)

    return result


def _rebuild(var_entries, non_vars):
    """Merge sorted variable entries with non-variable lines.

    Non-variable lines are inserted in their original relative positions
    where possible; otherwise appended at the end.
    """
    result = []
    non_var_sorted = sorted(non_vars, key=lambda x: x[0])
    nv_idx = 0

    # Place non-var lines that appeared before the first variable at top
    while nv_idx < len(non_var_sorted) and non_var_sorted[nv_idx][0] < var_entries[0][0]:
        result.append(non_var_sorted[nv_idx][1])
        nv_idx += 1

    for idx, e in var_entries:
        result.append(e)
        # Add any non-var lines that sit between this var and the next
        while nv_idx < len(non_var_sorted) and (
            nv_idx + 1 >= len(non_var_sorted)
            or (
                idx < non_var_sorted[nv_idx][0]
                and (
                    nv_idx + 1 >= len(var_entries)
                    or non_var_sorted[nv_idx][0] < var_entries[nv_idx + 1][0]
                    if nv_idx + 1 < len(var_entries)
                    else True
                )
            )
        ):
            result.append(non_var_sorted[nv_idx][1])
            nv_idx += 1

    # Any leftover non-var lines
    while nv_idx < len(non_var_sorted):
        result.append(non_var_sorted[nv_idx][1])
        nv_idx += 1

    return result


def serialize_entries(entries):
    """Convert a list of entry tuples back into a single string."""
    lines = []
    for e in entries:
        kind = e[0]
        if kind == "blank":
            lines.append("\n")
        elif kind == "comment":
            lines.append(e[2])  # e[2] is the full line
        elif kind == "var":
            lines.append(f"{e[1]}={e[2]}")
    return "".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print(__doc__)
        return

    filepath = None
    in_place = False
    sort_by = "name"
    group = False
    remove_dups = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--file" and i + 1 < len(args):
            filepath = args[i + 1]
            i += 2
        elif a == "--in-place":
            in_place = True
            i += 1
        elif a == "--sort-by" and i + 1 < len(args):
            val = args[i + 1].lower()
            if val not in ("name", "value"):
                print(f"Error: --sort-by must be 'name' or 'value', got '{val}'", file=sys.stderr)
                sys.exit(1)
            sort_by = val
            i += 2
        elif a == "--group":
            group = True
            i += 1
        elif a == "--remove-dups":
            remove_dups = True
            i += 1
        else:
            print(f"Error: unknown argument '{a}'", file=sys.stderr)
            sys.exit(1)

    # Read input
    if filepath:
        try:
            with open(filepath, "r") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: file not found '{filepath}'", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print(f"Error: permission denied '{filepath}'", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        text = sys.stdin.read()

    entries = parse_env(text)
    sorted_entries = group_sort(entries, sort_by, group, remove_dups)
    output = serialize_entries(sorted_entries)

    if in_place:
        if not filepath:
            print("Error: --in-place requires --file", file=sys.stderr)
            sys.exit(1)
        with open(filepath, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
