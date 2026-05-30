"""
log_hawk — Core parsing, detection, filtering, and display logic.

Zero external dependencies.  Supports syslog, Apache/Nginx common/combined,
JSON line-per-record, and custom-regex formats.
"""

import datetime
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Colour helpers  (ANSI 256 / named)
# ──────────────────────────────────────────────────────────────
_COLORS = {
    "reset":     "\033[0m",
    "bold":      "\033[1m",
    "dim":       "\033[2m",
    "red":       "\033[31m",
    "green":     "\033[32m",
    "yellow":    "\033[33m",
    "blue":      "\033[34m",
    "magenta":   "\033[35m",
    "cyan":      "\033[36m",
    "white":     "\033[37m",
    "bg_red":    "\033[41m",
    "bg_green":  "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue":   "\033[44m",
    "bg_magenta":"\033[45m",
    "bg_cyan":   "\033[46m",
    "bg_white":  "\033[47m",
}


def colorize(text, *names):
    """Wrap *text* with ANSI codes for each *name* in *names*, then reset."""
    codes = "".join(_COLORS.get(n, "") for n in names)
    return f"{codes}{text}{_COLORS['reset']}"


LEVEL_COLORS = {
    "DEBUG":    "dim",
    "INFO":     "green",
    "WARNING":  "yellow",
    "ERROR":    "red",
    "CRITICAL": ("red", "bold"),
    "FATAL":    ("bg_red", "bold", "white"),
    "ALERT":    ("bg_red", "bold"),
    "EMERG":    ("bg_magenta", "bold", "white"),
    "NOTICE":   "cyan",
    "TRACE":    "dim",
}

# ──────────────────────────────────────────────────────────────
# Log format definitions
# ──────────────────────────────────────────────────────────────

# RFC 3164 syslog  (BSD)
# <priority>?timestamp hostname process[pid]: message
_RE_SYSLOG = re.compile(
    r"^(?:<\d+>\s*)?"
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(\S+)\s+"
    r"(\S+?)(?:\[(\d+)\])?:\s+(.*)$"
)

# RFC 5424 syslog
_RE_SYSLOG5424 = re.compile(
    r"^<\d+>\d+\s+"
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+"
    r"(\S+)\s+"
    r"(\S+?)\s+"
    r"(\S+)\s+"
    r"(\S+\s+)?"
    r"(.*)$"
)

# Apache / Nginx Common Log Format
_RE_CLF = re.compile(
    r"^(\S+)\s+"           # host / IP
    r"\S+\s+"              # ident (usually -)
    r"\S+\s+"              # authuser (usually -)
    r"\[([^\]]+)\]\s+"     # date
    r'"(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+'
    r"(\S+)\s+"            # path
    r"\S+"                 # protocol
    r'"\s+'
    r"(\d{3})\s+"          # status
    r"(\d+|-)",            # size
)

# Combined Log Format (Apache) — extends CLF
_RE_COMBINED = re.compile(
    r"^(\S+)\s+"           # host / IP
    r"\S+\s+"
    r"\S+\s+"
    r"\[([^\]]+)\]\s+"
    r'"(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+'
    r"(\S+)\s+"
    r"\S+"
    r'"\s+'
    r"(\d{3})\s+"
    r"(\d+|-)\s+"
    r'"(.*?)"\s+'          # referer
    r'"(.*?)"',            # user-agent
)

# JSON line-per-record
_RE_JSON_LINE = re.compile(r"^\s*[{[]")


class LogEntry:
    """A single parsed log line."""

    __slots__ = (
        "raw", "timestamp", "host", "process", "pid",
        "level", "message", "ip", "path", "status", "size",
        "format_name", "json_fields",
    )

    def __init__(self):
        self.raw = ""
        self.timestamp = None  # datetime or str
        self.host = ""
        self.process = ""
        self.pid = ""
        self.level = ""
        self.message = ""
        self.ip = ""
        self.path = ""
        self.status = ""
        self.size = ""
        self.format_name = ""
        self.json_fields = None

    def as_dict(self):
        return {
            "timestamp": str(self.timestamp) if self.timestamp else "",
            "host": self.host,
            "process": self.process,
            "pid": self.pid,
            "level": self.level,
            "message": self.message,
            "ip": self.ip,
            "path": self.path,
            "status": self.status,
            "size": self.size,
            "format": self.format_name,
        }

    def colorized_line(self, highlight=None):
        """Return a colorized one-line string representation."""
        parts = []
        ts = str(self.timestamp) if self.timestamp else ""
        ts_colored = colorize(ts, "dim") if ts else ""
        if self.format_name in ("clf", "combined"):
            ip_colored = colorize(self.ip, "cyan")
            status_colored = self._color_status(self.status)
            path_colored = colorize(self.path, "blue")
            parts.append(f"{ip_colored} — [{ts_colored}] \"{path_colored}\" {status_colored} {self.size}")
        elif self.format_name in ("syslog", "syslog5424"):
            host_colored = colorize(self.host, "magenta")
            lvl_colored = self._color_level()
            proc = f"{self.process}[{self.pid}]" if self.pid else self.process
            parts.append(f"{ts_colored} {host_colored} {colorize(proc, 'dim')}: {lvl_colored} {self.message}")
        elif self.format_name == "json":
            lvl_colored = self._color_level()
            json_str = json.dumps(self.json_fields, default=str) if self.json_fields else self.message
            parts.append(f"{ts_colored} {lvl_colored} {json_str}")
        else:
            lvl_colored = self._color_level()
            parts.append(f"{ts_colored} {lvl_colored} {self.message}")

        line = "  ".join(parts)
        if highlight and highlight.lower() in self.raw.lower():
            # Re-apply highlighting by overlaying ANSI
            idx = line.lower().find(highlight.lower())
            if idx >= 0:
                end = idx + len(highlight)
                line = (line[:idx] + colorize(highlight, "bg_yellow", "bold") +
                        line[end:])
        return line

    def _color_level(self):
        styles = LEVEL_COLORS.get(self.level.upper(), ())
        if isinstance(styles, str):
            styles = (styles,)
        return colorize(self.level.upper(), *styles) if self.level else ""

    @staticmethod
    def _color_status(status):
        if not status or status == "-":
            return status
        code = int(status)
        if code < 300:
            return colorize(status, "green")
        elif code < 400:
            return colorize(status, "cyan")
        elif code < 500:
            return colorize(status, "yellow")
        else:
            return colorize(status, "red", "bold")

    def __repr__(self):
        return f"<LogEntry {self.format_name} {self.timestamp} {self.level}>"


# ──────────────────────────────────────────────────────────────
# Auto-detect format
# ──────────────────────────────────────────────────────────────

def detect_format(line):
    """Return a format name string ('syslog', 'combined', 'json', etc.) or None."""
    if not line or line.startswith("#") or line.strip() == "":
        return None

    if _RE_SYSLOG.match(line):
        return "syslog"
    if _RE_SYSLOG5424.match(line):
        return "syslog5424"
    if _RE_COMBINED.match(line):
        return "combined"
    if _RE_CLF.match(line):
        return "clf"
    if _RE_JSON_LINE.match(line):
        return "json"
    return "raw"


# ──────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────

def parse_line(line, fmt_hint=None):
    """Parse *line* into a LogEntry.  Auto-detect if *fmt_hint* is None."""
    entry = LogEntry()
    entry.raw = line.rstrip("\n\r")

    fmt = fmt_hint or detect_format(line)
    if fmt is None:
        entry.format_name = "raw"
        entry.message = line
        return entry

    entry.format_name = fmt

    if fmt in ("syslog",):
        m = _RE_SYSLOG.match(line)
        if m:
            ts_str, host, proc, pid, msg = m.groups()
            entry.timestamp = _parse_syslog_ts(ts_str)
            entry.host = host
            entry.process = proc
            entry.pid = pid or ""
            entry.message = msg
            entry.level = _extract_level(msg)
            entry.ip = host if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host) else ""
        else:
            entry.message = line
        return entry

    if fmt in ("syslog5424",):
        m = _RE_SYSLOG5424.match(line)
        if m:
            ts_str, host, app, procid, msgid, msg = m.groups()
            entry.timestamp = ts_str
            entry.host = host
            entry.process = app
            entry.pid = procid or ""
            entry.message = (msg or "").strip()
            entry.level = _extract_level(entry.message)
        else:
            entry.message = line
        return entry

    if fmt in ("combined",):
        m = _RE_COMBINED.match(line)
        if m:
            ip, date_str, path, status, size, ref, ua = m.groups()
            entry.ip = ip
            entry.timestamp = _parse_clf_date(date_str)
            entry.path = path
            entry.status = status
            entry.size = size
            entry.host = ip
            entry.message = f"{path} {status} {size}"
            entry.level = "INFO" if status and int(status) < 400 else "ERROR"
        else:
            entry.message = line
        return entry

    if fmt in ("clf",):
        m = _RE_CLF.match(line)
        if m:
            ip, date_str, path, status, size = m.groups()
            entry.ip = ip
            entry.timestamp = _parse_clf_date(date_str)
            entry.path = path
            entry.status = status
            entry.size = size
            entry.host = ip
            entry.message = f"{path} {status} {size}"
            entry.level = "INFO" if status and int(status) < 400 else "ERROR"
        else:
            entry.message = line
        return entry

    if fmt == "json":
        try:
            obj = json.loads(line)
            entry.json_fields = obj
            entry.message = json.dumps(obj, default=str)
            entry.timestamp = (obj.get("time") or obj.get("timestamp") or
                               obj.get("@timestamp") or obj.get("date") or "")
            entry.level = (obj.get("level") or obj.get("severity") or
                           obj.get("lvl") or obj.get("log_level") or "")
            entry.host = obj.get("host") or obj.get("hostname") or ""
            entry.process = obj.get("process") or obj.get("app") or ""
            entry.ip = obj.get("ip") or obj.get("client_ip") or obj.get("remote_addr") or ""
        except (json.JSONDecodeError, TypeError):
            entry.message = line
        return entry

    # raw / fallback
    entry.message = line
    return entry


def _parse_syslog_ts(ts_str):
    """Parse syslog timestamp like 'Dec 15 14:23:45' -> datetime."""
    now = datetime.datetime.now()
    try:
        dt = datetime.datetime.strptime(ts_str, "%b %d %H:%M:%S")
        return dt.replace(year=now.year)
    except ValueError:
        return ts_str


def _parse_clf_date(date_str):
    """Parse CLF date like '10/Dec/2024:13:55:36 +0000' -> datetime."""
    try:
        dt = datetime.datetime.strptime(date_str.split()[0], "%d/%b/%Y:%H:%M:%S")
        return dt
    except (ValueError, IndexError):
        return date_str


_LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL|FATAL|ALERT|EMERG|NOTICE|TRACE)\b",
    re.IGNORECASE,
)


def _extract_level(message):
    m = _LEVEL_RE.search(message)
    return m.group(1).upper() if m else ""


# ──────────────────────────────────────────────────────────────
# Filter chain
# ──────────────────────────────────────────────────────────────

class Filter:
    def __init__(self, level=None, pattern=None, ip_match=None,
                 host_match=None, status_min=None, status_max=None,
                 since=None, until=None, invert=False):
        self.level = level.upper() if level else None
        self.pattern = re.compile(pattern, re.IGNORECASE) if pattern else None
        self.ip_match = re.compile(ip_match, re.IGNORECASE) if ip_match else None
        self.host_match = re.compile(host_match, re.IGNORECASE) if host_match else None
        self.status_min = status_min
        self.status_max = status_max
        self.since = since
        self.until = until
        self.invert = invert

    def match(self, entry):
        ok = True
        if self.level and entry.level.upper() != self.level:
            ok = False
        if self.pattern and not self.pattern.search(entry.raw):
            ok = False
        if self.ip_match and not self.ip_match.search(entry.ip):
            ok = False
        if self.host_match and not self.host_match.search(entry.host):
            ok = False
        if self.status_min and entry.status and entry.status != "-":
            try:
                if int(entry.status) < self.status_min:
                    ok = False
            except ValueError:
                pass
        if self.status_max and entry.status and entry.status != "-":
            try:
                if int(entry.status) > self.status_max:
                    ok = False
            except ValueError:
                pass
        if self.invert:
            return not ok
        return ok


# ──────────────────────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────────────────────

def build_stats(entries):
    """Return dict of statistics from a list of LogEntry."""
    stats = {
        "total": len(entries),
        "by_level": Counter(),
        "by_ip": Counter(),
        "by_host": Counter(),
        "by_status": Counter(),
        "by_hour": Counter(),
        "by_process": Counter(),
        "top_errors": Counter(),
    }
    for e in entries:
        if e.level:
            stats["by_level"][e.level] += 1
        if e.ip:
            stats["by_ip"][e.ip] += 1
        if e.host:
            stats["by_host"][e.host] += 1
        if e.status and e.status != "-":
            stats["by_status"][e.status] += 1
        if e.timestamp:
            if isinstance(e.timestamp, datetime.datetime):
                hour_key = e.timestamp.strftime("%Y-%m-%d %H:00")
            else:
                hour_key = str(e.timestamp)[:13]
            stats["by_hour"][hour_key] += 1
        if e.process:
            stats["by_process"][e.process] += 1
        if e.level in ("ERROR", "CRITICAL", "FATAL"):
            stats["top_errors"][e.message[:80]] += 1
    return stats


def render_stats_table(stats, top_n=10):
    """Return a colorized multi-line string of statistics."""
    lines = []
    lines.append("")
    lines.append(colorize("══════════════════  LOG-HAWK STATISTICS  ══════════════════", "bold", "cyan"))
    lines.append(f"  Total entries:      {colorize(str(stats['total']), 'bold', 'white')}")
    lines.append("")

    def _section(title, counter, fmt="{k}: {v}"):
        if not counter:
            return
        lines.append(colorize(f"  ── {title} ──", "bold"))
        for k, v in counter.most_common(top_n):
            bar = "█" * min(v, 40) if v < 100 else "█" * min(v // 2, 40)
            lines.append(f"    {fmt.format(k=k or '(empty)', v=v)}  {colorize(bar, 'dim')}")
        lines.append("")

    _section("By Level", stats["by_level"], "{k}: {v}")
    _section("By Status Code", stats["by_status"])
    _section("By IP Address", stats["by_ip"], "{k}  ({v})")
    _section("By Host", stats["by_host"], "{k}  ({v})")
    _section("By Process", stats["by_process"])
    _section("Timeline (top hours)", stats["by_hour"])

    if stats["top_errors"]:
        lines.append(colorize("  ── Most Frequent Errors ──", "bold", "red"))
        for msg, cnt in stats["top_errors"].most_common(top_n):
            lines.append(f"    [{cnt}x] {msg}")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# File I/O helpers
# ──────────────────────────────────────────────────────────────

def open_log(path, follow=False, seek_end=False):
    """Generator yielding raw lines from *path*.

    If *follow* is True, blocks like ``tail -f`` (uses simple polling).
    If *seek_end* is True, starts from the end of the file.
    """
    p = Path(path)
    if not p.exists():
        yield f"[log-hawk] ERROR: file not found: {path}"
        return

    mode = "rb"
    with open(p, mode) as fh:
        if seek_end:
            fh.seek(0, os.SEEK_END)

        while True:
            line = fh.readline()
            if line:
                try:
                    yield line.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    yield line.decode("latin-1", errors="replace")
            else:
                if not follow:
                    break
                fh.flush()
                time.sleep(0.1)


def gather(path, follow=False, seek_end=False, max_lines=0):
    """Return a list of LogEntry from *path*."""
    entries = []
    for raw in open_log(path, follow=follow, seek_end=seek_end):
        entry = parse_line(raw)
        entries.append(entry)
        if max_lines and len(entries) >= max_lines:
            break
    return entries


# ──────────────────────────────────────────────────────────────
# High-level helpers for CLI/TUI
# ──────────────────────────────────────────────────────────────

def detect_format_from_file(path, sample_size=20):
    """Read first *sample_size* non-empty lines and return most common format."""
    counts = Counter()
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", errors="replace") as fh:
        for i, line in enumerate(fh):
            if line.strip():
                fmt = detect_format(line)
                if fmt:
                    counts[fmt] += 1
            if i >= sample_size * 2:
                break
    if not counts:
        return None
    return counts.most_common(1)[0][0]

# === Auto-registration ===
TOOL_META = {
    "name": "log-hawk",
    "desc": "Log analysis: tail, grep, stats, patterns, TUI — CLI+TUI",
    "func": "main",
}
