"""
log_hawk.cli — Command-line interface with argparse.

Usage:
    log-hawk [path...] [-f] [--level LEVEL] [--pattern PAT] [--ip IP]
             [--stats] [--format FMT] [--since TIME] [--until TIME]
             [--status-min N] [--status-max N] [--invert] [--json-out]
             [--no-color] [--lines N] [--tui]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from . import (
    LogEntry,
    Filter,
    build_stats,
    colorize,
    detect_format_from_file,
    gather,
    open_log,
    parse_line,
    render_stats_table,
)


def build_parser():
    p = argparse.ArgumentParser(
        prog="log-hawk",
        description="Flagship CLI+TUI log analyzer, tailer, and auditor.",
        epilog="Examples:\n"
               "  log-hawk /var/log/syslog\n"
               "  log-hawk access.log -f --ip 192.168\n"
               "  log-hawk app.log --level ERROR --stats\n"
               "  log-hawk --tui /var/log/syslog\n"
               "  tail -100 app.log | log-hawk -",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    p.add_argument("paths", nargs="*", default=["-"],
                   help="Log file(s) to process.  Use '-' or omit for stdin.")
    p.add_argument("-f", "--follow", action="store_true",
                   help="Follow/tail mode — wait for new lines (like tail -f).")
    p.add_argument("--level", "-l",
                   help="Filter by log level (DEBUG, INFO, WARNING, ERROR, ...).")
    p.add_argument("--pattern", "-p",
                   help="Case-insensitive regex pattern filter.")
    p.add_argument("--ip", "-i",
                   help="Filter by IP address or CIDR prefix (regex, e.g. '192\\.168' ).")
    p.add_argument("--host",
                   help="Filter by hostname (regex).")
    p.add_argument("--status-min", type=int,
                   help="Minimum HTTP status code (e.g. 400).")
    p.add_argument("--status-max", type=int,
                   help="Maximum HTTP status code (e.g. 499).")
    p.add_argument("--since",
                   help="Only show entries after this time (string contained in timestamp).")
    p.add_argument("--until",
                   help="Only show entries before this time.")
    p.add_argument("--invert", "-v", action="store_true",
                   help="Invert filter — show lines that do NOT match.")
    p.add_argument("--stats", "-s", action="store_true",
                   help="Show aggregated statistics instead of line-by-line output.")
    p.add_argument("--format", "-F", dest="fmt",
                   help="Force log format (syslog, combined, clf, json, raw).")
    p.add_argument("--json-out", action="store_true",
                   help="Output parsed entries as JSON lines.")
    p.add_argument("--no-color", action="store_true",
                   help="Disable ANSI color output.")
    p.add_argument("--lines", "-n", type=int, default=0,
                   help="Number of recent lines to show (default: all).  Implies seek-end.")
    p.add_argument("--tui", action="store_true",
                   help="Launch the curses-based interactive TUI.")
    p.add_argument("--auto-detect", action="store_true",
                   help="Print detected format and exit.")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    paths = args.paths

    # ── auto-detect ──
    if args.auto_detect:
        for p in paths:
            if p == "-":
                print("stdin: (cannot auto-detect stdin)")
                continue
            fmt = detect_format_from_file(p)
            print(f"{p}: {fmt or 'unknown'}")
        return 0

    # ── TUI mode ──
    if args.tui:
        from .tui import run_tui
        try:
            run_tui(paths)
        except KeyboardInterrupt:
            pass
        return 0

    # ── Build filter ──
    filt = Filter(
        level=args.level,
        pattern=args.pattern,
        ip_match=args.ip,
        host_match=args.host,
        status_min=args.status_min,
        status_max=args.status_max,
        since=args.since,
        until=args.until,
        invert=args.invert,
    )

    # Disable colour if not a TTY or --no-color
    use_color = not args.no_color and sys.stdout.isatty()

    # ── Read from files/stdin ──
    if len(paths) == 1 and paths[0] == "-":
        # stdin mode
        entries = []
        for raw in sys.stdin:
            entry = parse_line(raw, fmt_hint=args.fmt)
            if filt.match(entry):
                entries.append(entry)
        if args.stats:
            print(render_stats_table(build_stats(entries)))
        else:
            for e in entries:
                _emit(e, args.json_out, use_color)
        return 0

    # File(s) mode
    if args.lines:
        # Seek from end
        for p in paths:
            if not os.path.exists(p):
                print(f"{colorize('ERROR', 'red', 'bold')}: file not found: {p}")
                continue
            _process_file(p, args, filt, use_color, seek_end=True)

        if args.follow:
            _follow_files(paths, args, filt, use_color)
    elif args.follow:
        _follow_files(paths, args, filt, use_color)
    else:
        entries = []
        for p in paths:
            if not os.path.exists(p):
                print(f"{colorize('ERROR', 'red', 'bold')}: file not found: {p}")
                continue
            _process_file(p, args, filt, use_color, seek_end=False)

    return 0


def _process_file(path, args, filt, use_color, seek_end=False):
    """Read a file, apply filter, show output."""
    if args.stats:
        entries = gather(path, seek_end=seek_end)
        filtered = [e for e in entries if filt.match(e)]
        print(render_stats_table(build_stats(filtered)))
        return

    count = 0
    for raw in open_log(path, seek_end=seek_end):
        entry = parse_line(raw, fmt_hint=args.fmt)
        if filt.match(entry):
            _emit(entry, args.json_out, use_color)
            count += 1
            if args.lines and count >= args.lines:
                break


def _follow_files(paths, args, filt, use_color):
    """Tail -f mode: keep reading new lines from all files."""
    handles = {}
    try:
        for p in paths:
            if not os.path.exists(p):
                print(f"{colorize('ERROR', 'red', 'bold')}: file not found: {p}")
                continue
            fh = open(p, "rb")
            fh.seek(0, os.SEEK_END)
            handles[p] = fh

        if not handles:
            return

        print(colorize(f"  log-hawk: tailing {len(handles)} file(s) — Ctrl+C to stop", "bold", "cyan"))

        while True:
            for p, fh in list(handles.items()):
                line = fh.readline()
                if line:
                    try:
                        raw = line.decode("utf-8", errors="replace")
                    except UnicodeDecodeError:
                        raw = line.decode("latin-1", errors="replace")
                    entry = parse_line(raw, fmt_hint=args.fmt)
                    if filt.match(entry):
                        if len(handles) > 1:
                            print(colorize(f"[{Path(p).name}]", "magenta"), end=" ")
                        _emit(entry, args.json_out, use_color)
                else:
                    # Check if file was rotated
                    try:
                        st = os.stat(p)
                        if st.st_ino != os.fstat(fh.fileno()).st_ino:
                            fh.close()
                            fh = open(p, "rb")
                            handles[p] = fh
                    except OSError:
                        pass
            time.sleep(0.1)
    except KeyboardInterrupt:
        print()
        for fh in handles.values():
            fh.close()


def _emit(entry, json_out, use_color):
    """Print a single LogEntry."""
    if json_out:
        print(json.dumps(entry.as_dict(), default=str))
    elif use_color:
        print(entry.colorized_line())
    else:
        print(entry.raw)


def entry_point():
    """Entry-point wrapper for pip-installed console scripts."""
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(0)
    except BrokenPipeError:
        sys.exit(0)
    except Exception as exc:
        print(f"{colorize('FATAL', 'bg_red', 'bold')}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
