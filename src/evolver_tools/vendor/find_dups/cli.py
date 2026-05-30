#!/usr/bin/env python3
"""find-dups — Find duplicate files by SHA256 content hash."""

from __future__ import annotations

import argparse
import hashlib
import os
import fnmatch
import sys
import time

# ── Progress helper ──────────────────────────────────────────────────────────


def _human_size(n: int) -> str:
    """Format a byte count in human-readable form."""
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n}{unit}"
        n //= 1024
    return f"{n}PiB"


class Progress:
    """Simple terminal progress reporter (zero-dependency)."""

    def __init__(self, interval: float = 0.25) -> None:
        self._last = 0.0
        self._interval = interval
        self._scanned = 0
        self._hashed = 0
        self._errors = 0
        self._start = time.time()

    def tick_scanned(self) -> None:
        self._scanned += 1
        self._maybe_print()

    def tick_hashed(self) -> None:
        self._hashed += 1
        self._maybe_print()

    def tick_error(self) -> None:
        self._errors += 1
        self._maybe_print()

    def _maybe_print(self) -> None:
        now = time.time()
        if now - self._last < self._interval:
            return
        self._last = now
        elapsed = now - self._start
        rate = self._scanned / elapsed if elapsed > 0 else 0
        print(
            f"  scanned {self._scanned:,}  |  hashed {self._hashed:,}  "
            f"|  errors {self._errors:,}  |  {rate:.0f} files/s       \r",
            end="",
            file=sys.stderr,
            flush=True,
        )

    def finish(self) -> None:
        elapsed = time.time() - self._start
        print(
            f"  scanned {self._scanned:,}  |  hashed {self._hashed:,}  "
            f"|  errors {self._errors:,}  |  {elapsed:.1f}s total       ",
            file=sys.stderr,
            flush=True,
        )


# ── Core logic ───────────────────────────────────────────────────────────────


def _sha256_file(path: str, buffer_size: int = 2**20, *, progress: Progress | None = None) -> str | None:
    """Return hex SHA256 digest of *path*, or ``None`` on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(buffer_size)
                if not chunk:
                    break
                h.update(chunk)
    except (OSError, PermissionError) as exc:
        if progress:
            progress.tick_error()
        print(f"  [error] {path}: {exc}", file=sys.stderr)
        return None
    if progress:
        progress.tick_hashed()
    return h.hexdigest()


def _walk_files(
    root: str,
    *,
    min_size: int = 0,
    max_size: int | None = None,
    excludes: list[str] | None = None,
    progress: Progress | None = None,
) -> list[str]:
    """Recursively collect file paths under *root* matching filters."""
    excludes = excludes or []
    files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Skip excluded directories eagerly
        dirnames[:] = [
            d
            for d in dirnames
            if not any(fnmatch.fnmatch(os.path.join(dirpath, d), pat) for pat in excludes)
        ]

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)

            # Check exclude patterns against full path
            if any(fnmatch.fnmatch(fpath, pat) for pat in excludes):
                if progress:
                    progress.tick_scanned()
                continue

            # Stat the file
            try:
                st = os.lstat(fpath)
            except OSError:
                if progress:
                    progress.tick_scanned()
                    progress.tick_error()
                continue

            # Skip non-regular files (symlinks, devices, sockets, etc.)
            if not os.path.isfile(fpath):
                if progress:
                    progress.tick_scanned()
                continue

            size = st.st_size

            # Size filters
            if size < min_size:
                if progress:
                    progress.tick_scanned()
                continue
            if max_size is not None and size > max_size:
                if progress:
                    progress.tick_scanned()
                continue

            if progress:
                progress.tick_scanned()

            files.append(fpath)

    return files


def find_duplicates(
    paths: list[str],
    *,
    min_size: int = 0,
    max_size: int | None = None,
    excludes: list[str] | None = None,
    progress: bool = True,
) -> dict[str, list[str]]:
    """
    Return a dict mapping SHA256 hex digest -> list of duplicate file paths.

    Only groups with **two or more** files are included.
    """
    prog = Progress() if progress else None

    # Phase 1: collect candidate files
    all_files: list[str] = []
    for p in paths:
        if os.path.isfile(p):
            # Single file — still apply size/exclude rules
            skip = False
            if excludes:
                if any(fnmatch.fnmatch(p, pat) for pat in excludes):
                    skip = True
            if not skip:
                try:
                    st = os.lstat(p)
                    if os.path.isfile(p):
                        size = st.st_size
                        if size >= min_size and (max_size is None or size <= max_size):
                            all_files.append(p)
                except OSError:
                    pass
        else:
            all_files.extend(
                _walk_files(
                    p,
                    min_size=min_size,
                    max_size=max_size,
                    excludes=excludes,
                    progress=prog,
                )
            )

    prog2 = Progress() if progress else None
    if prog:
        print(f"  Files to hash: {len(all_files):,}", file=sys.stderr)

    # Phase 2: hash all files
    hash_map: dict[str, list[str]] = {}
    for fpath in all_files:
        digest = _sha256_file(fpath, progress=prog2)
        if digest is None:
            continue
        hash_map.setdefault(digest, []).append(fpath)

    if prog2:
        prog2.finish()

    # Phase 3: keep only groups with 2+ files
    return {digest: paths for digest, paths in hash_map.items() if len(paths) >= 2}


# ── CLI ──────────────────────────────────────────────────────────────────────


def _size_arg(value: str) -> int:
    """Parse a size argument like ``10``, ``1K``, ``2M``, ``1G``."""
    value = value.strip().upper()
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    if value[-1] in multipliers:
        return int(value[:-1]) * multipliers[value[-1]]
    return int(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="find-dups",
        description="Find duplicate files by SHA256 content hash.",
        epilog="Examples:\n"
        "  find-dups /home/user/Documents\n"
        "  find-dups . --min-size 1M\n"
        "  find-dups /data --exclude '*.tmp' --exclude '__pycache__/*' --delete\n"
        "  find-dups /a /b --max-size 10K",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more file or directory paths to scan",
    )
    parser.add_argument(
        "--min-size",
        type=_size_arg,
        default=0,
        help='Minimum file size (e.g. "1K", "5M", "1G"). Default: 0',
    )
    parser.add_argument(
        "--max-size",
        type=_size_arg,
        default=None,
        help='Maximum file size (e.g. "10M", "500K"). Default: no limit',
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="excludes",
        help='Glob patterns to exclude (can be repeated). E.g. --exclude "*.tmp"',
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicate files, keeping only the first in each group",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress indicator",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    return parser


def _color(text: str, code: str, *, no_color: bool = False) -> str:
    if no_color:
        return text
    codes = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print(_color("find-dups", "bold") + _color(" — scanning for duplicate files…", "dim"), file=sys.stderr)
    print(file=sys.stderr)

    duplicates = find_duplicates(
        args.paths,
        min_size=args.min_size,
        max_size=args.max_size,
        excludes=args.excludes or None,
        progress=not args.quiet,
    )

    print(file=sys.stderr)

    if not duplicates:
        print(_color("  No duplicate files found.", "green", no_color=args.no_color))
        return 0

    total_dup_files = sum(len(paths) for paths in duplicates.values())
    total_wasted = 0

    for i, (digest, paths) in enumerate(sorted(duplicates.items())):
        # Size of the kept file (first)
        kept_path = paths[0]
        try:
            kept_size = os.path.getsize(kept_path)
        except OSError:
            kept_size = 0
        wasted = kept_size * (len(paths) - 1)
        total_wasted += wasted

        group_label = (
            _color(f"  Duplicate group {i+1}", "bold", no_color=args.no_color)
            + _color(f"  [{digest[:12]}…]", "dim", no_color=args.no_color)
            + _color(f"  ({len(paths)} files, {_human_size(wasted)} wasted)", "yellow", no_color=args.no_color)
        )
        print(group_label)
        print(f"  {'─' * 60}")
        for j, fpath in enumerate(paths):
            prefix = _color("  ✓ kept", "green", no_color=args.no_color) if j == 0 else _color("  ✗ dup", "red", no_color=args.no_color)
            print(f"{prefix}  {fpath}")
        print()

    summary = (
        _color(f"  Found {len(duplicates)} duplicate groups", "bold", no_color=args.no_color)
        + _color(f" ({total_dup_files} files, {_human_size(total_wasted)} reclaimable)", "yellow", no_color=args.no_color)
    )
    print(summary, file=sys.stderr)

    # ── Delete mode ──────────────────────────────────────────────────────
    if args.delete:
        deleted_count = 0
        deleted_size = 0
        print(file=sys.stderr)
        print(_color("  — Delete mode enabled —", "bold", no_color=args.no_color), file=sys.stderr)

        for digest, paths in duplicates.items():
            kept = paths[0]
            for fpath in paths[1:]:
                try:
                    sz = os.path.getsize(fpath)
                    os.remove(fpath)
                    deleted_count += 1
                    deleted_size += sz
                    print(
                        _color("  ✗ deleted", "red", no_color=args.no_color)
                        + f"  {fpath}",
                    )
                except OSError as exc:
                    print(
                        _color("  ! error", "red", no_color=args.no_color)
                        + f"  {fpath}: {exc}",
                        file=sys.stderr,
                    )

        print(file=sys.stderr)
        print(
            _color(f"  Removed {deleted_count} files", "green", no_color=args.no_color)
            + _color(f" ({_human_size(deleted_size)} reclaimed)", "yellow", no_color=args.no_color),
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
