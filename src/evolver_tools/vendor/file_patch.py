#!/usr/bin/env python3
"""file-patch — Apply simple text patches (find/replace) to files.

Performs a single find-and-replace operation on a text file.
Supports dry-run mode and automatic backup creation.

Usage:
    file-patch --file README.md --old "foo" --new "bar"
    file-patch --file config.py --old "DEBUG = True" --new "DEBUG = False" --dry-run
    file-patch --file settings.ini --old "port=8080" --new "port=9090" --backup
    file-patch --file script.sh --old "some old text" --new ""

Options:
    --file PATH      Path to the file to patch (required)
    --old TEXT       Text to find (required)
    --new TEXT       Replacement text (required, may be empty string)
    --dry-run        Show what would be changed without modifying the file
    --backup         Create a .bak backup of the original file
    -h, --help       Show this help message
"""

import sys
import os
import argparse


TOOL_META = {
    "name": "file-patch",
    "func": "main",
    "desc": "Apply text patches to files",
}


def apply_patch(
    filepath: str,
    old_text: str,
    new_text: str,
    dry_run: bool = False,
    backup: bool = False,
) -> int:
    """Apply a find/replace patch to a file.

    Reads the file, performs exactly one replacement of *old_text* with
    *new_text*, and writes the result back.  If *old_text* is not found,
    or is found more than once, the function exits with an error.

    Args:
        filepath: Path to the file to patch.
        old_text: The exact text to search for.
        new_text: The text to replace it with.
        dry_run: If True, only display what would change.
        backup: If True, create a .bak copy before modifying.

    Returns:
        0 on success, 1 on failure.
    """
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return 1

    # Read the file
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: cannot read '{filepath}': {e}", file=sys.stderr)
        return 1

    # Count occurrences
    count = content.count(old_text)

    if count == 0:
        print(f"Error: string not found in '{filepath}'", file=sys.stderr)
        return 1

    if count > 1:
        print(
            f"Error: found {count} occurrences of the search string in "
            f"'{filepath}'.  Expected exactly 1.  Use a more specific "
            f"--old string.",
            file=sys.stderr,
        )
        return 1

    # Perform the replacement
    new_content = content.replace(old_text, new_text, 1)

    # Show diff-style output
    _show_patch(filepath, old_text, new_text, count)

    if dry_run:
        print(f"[DRY-RUN] No changes written to '{filepath}'.")
        return 0

    # Create backup if requested
    if backup:
        backup_path = filepath + ".bak"
        try:
            # Avoid overwriting an existing backup
            if os.path.exists(backup_path):
                base, ext = backup_path, ""
                idx = 1
                while os.path.exists(f"{base}.{idx}"):
                    idx += 1
                backup_path = f"{filepath}.bak.{idx}"
            with open(backup_path, "w", encoding="utf-8") as bf:
                bf.write(content)
            print(f"Backup created: {backup_path}")
        except OSError as e:
            print(f"Error: cannot create backup '{backup_path}': {e}", file=sys.stderr)
            return 1

    # Write the patched file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched: {filepath}")
    except OSError as e:
        print(f"Error: cannot write '{filepath}': {e}", file=sys.stderr)
        return 1

    return 0


def _show_patch(filepath: str, old_text: str, new_text: str, count: int) -> None:
    """Print a human-readable summary of the patch."""
    print(f"File: {filepath}  ({count} occurrence{'s' if count != 1 else ''})")
    # Show context: first line of old text
    old_first = old_text.split("\n")[0]
    new_first = new_text.split("\n")[0]
    if old_text == new_text:
        print("  (no change — old and new text are identical)")
    else:
        print(f"  -{old_first}")
        print(f"  +{new_first}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Apply a simple text find/replace patch to a file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  file-patch --file README.md --old \"foo\" --new \"bar\"\n"
            "  file-patch --file config.py --old \"DEBUG = True\" "
            "--new \"DEBUG = False\" --dry-run\n"
            "  file-patch --file settings.ini --old \"port=8080\" "
            "--new \"port=9090\" --backup\n"
            "  file-patch --file script.sh --old \"some old text\" --new \"\"\n"
        ),
    )
    parser.add_argument(
        "--file", required=True,
        help="Path to the file to patch",
    )
    parser.add_argument(
        "--old", required=True,
        help="Text to find (exact match)",
    )
    parser.add_argument(
        "--new", required=True,
        default="",
        help="Replacement text (may be empty string)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be changed without modifying the file",
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create a .bak backup of the original file before patching",
    )
    args = parser.parse_args()

    filepath = os.path.abspath(args.file)

    exit_code = apply_patch(
        filepath=filepath,
        old_text=args.old,
        new_text=args.new,
        dry_run=args.dry_run,
        backup=args.backup,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
