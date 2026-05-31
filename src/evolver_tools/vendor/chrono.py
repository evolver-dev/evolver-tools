#!/usr/bin/env python3
"""chrono — Advanced date/time calculator.

Calculate durations, add/subtract time, find business days,
convert timezones, and generate date ranges.

Usage:
    chrono now                              # Current timestamp
    chrono days 2024-01-01 2024-12-31       # Days between dates
    chrono add 2024-01-01 90 days           # Add/subtract time
    chrono workdays 2024-01-01 2024-12-31   # Business days between dates
    chrono range 2024-01-01 2024-01-31 3d   # Generate date range with step
    chrono age 1990-06-15                   # Age from birthdate
"""

import sys
import os
import re
from datetime import datetime, date, timedelta

TOOL_META = {
    "name": "chrono",
    "func": "main",
    "desc": "Advanced date/time calculator (durations, business days, ranges, age)",
}

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

UNITS = {
    "d": "days", "day": "days", "days": "days",
    "w": "weeks", "week": "weeks", "weeks": "weeks",
    "m": "months", "month": "months", "months": "months",
    "y": "years", "year": "years", "years": "years",
}


def parse_date(s):
    """Parse a date string into a date object."""
    s = s.strip().strip('"').strip("'")

    if s.lower() in ("now", "today"):
        return date.today()

    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
        "%m-%d-%Y", "%m/%d/%Y", "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    print(f"Error: cannot parse date '{s}'", file=sys.stderr)
    print("Supported formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY", file=sys.stderr)
    sys.exit(1)


def parse_delta(s):
    """Parse a time delta string like '90 days', '2w', '3m', '1y'."""
    s = s.strip()
    m = re.match(r"^(-?\d+)\s*(day|days|d|week|weeks|w|month|months|m|year|years|y)$", s, re.I)
    if not m:
        print(f"Error: cannot parse duration '{s}'", file=sys.stderr)
        print("Examples: 90 days, 2w, 3m, 1y, -7d", file=sys.stderr)
        sys.exit(1)

    num = int(m.group(1))
    unit = m.group(2).lower()

    if unit in ("d", "day", "days"):
        return timedelta(days=num)
    elif unit in ("w", "week", "weeks"):
        return timedelta(weeks=num)
    else:
        # For months/years, return a proxy that we handle specially
        return ("month_year", num, unit in ("y", "year", "years"))


def format_date(d):
    """Format a date nicely."""
    return f"{WEEKDAYS[d.weekday()]}, {d.strftime('%Y-%m-%d')}"


def cmd_now(*_):
    now = datetime.now()
    d = now.date()
    t = now.time()
    print(f"Today:  {format_date(d)}")
    print(f"Time:   {t.strftime('%H:%M:%S')}")
    print(f"ISO:    {now.isoformat()}")
    print(f"Epoch:  {int(now.timestamp())}")
    print(f"DOY:    {d.timetuple().tm_yday}/366")


def cmd_days(args):
    if len(args) < 2:
        print("Usage: chrono days <date1> <date2>", file=sys.stderr)
        sys.exit(1)
    d1 = parse_date(args[0])
    d2 = parse_date(args[1])
    delta = (d2 - d1).days
    print(f"{format_date(d1)} → {format_date(d2)}")
    print(f"Difference: {abs(delta)} day{'s' if abs(delta) != 1 else ''}")
    if delta < 0:
        print("Direction:  backward")
    elif delta > 0:
        print("Direction:  forward")


def cmd_add(args):
    if len(args) < 1:
        print("Usage: chrono add <date> <delta> [--format ISO|full]", file=sys.stderr)
        sys.exit(1)
    d = parse_date(args[0])

    if len(args) >= 2:
        delta = parse_delta(args[1])
        if isinstance(delta, tuple):
            _, num, is_year = delta
            if is_year:
                new_year = d.year + num
                try:
                    d = d.replace(year=new_year)
                except ValueError:
                    # Handle Feb 29 edge case
                    import calendar
                    last_day = calendar.monthrange(new_year, d.month)[1]
                    d = d.replace(year=new_year, day=min(d.day, last_day))
            else:
                new_month = d.month + num
                year_shift = (new_month - 1) // 12
                new_month = ((new_month - 1) % 12) + 1
                new_year = d.year + year_shift
                import calendar
                last_day = calendar.monthrange(new_year, new_month)[1]
                d = d.replace(year=new_year, month=new_month, day=min(d.day, last_day))
        else:
            d = d + delta

    show_fmt = "--format" in args
    if show_fmt:
        idx = args.index("--format")
        fmt_type = args[idx + 1] if idx + 1 < len(args) else "full"

    print(format_date(d))


def cmd_workdays(args):
    if len(args) < 2:
        print("Usage: chrono workdays <date1> <date2>", file=sys.stderr)
        sys.exit(1)
    d1 = parse_date(args[0])
    d2 = parse_date(args[1])

    if d1 > d2:
        d1, d2 = d2, d1

    count = 0
    current = d1
    while current <= d2:
        if current.weekday() < 5:  # Mon-Fri
            count += 1
        current += timedelta(days=1)

    print(f"{format_date(d1)} → {format_date(d2)}")
    print(f"Calendar days: {(d2 - d1).days}")
    print(f"Workdays:      {count}")
    print(f"Weekends:      {(d2 - d1).days - count}")


def cmd_range(args):
    if len(args) < 2:
        print("Usage: chrono range <start> <end> [step]", file=sys.stderr)
        print("  step examples: 1d (default), 2d, 1w, 1m")
        sys.exit(1)

    start = parse_date(args[0])
    end = parse_date(args[1])

    step_delta = timedelta(days=1)
    if len(args) >= 3:
        delta = parse_delta(args[2])
        if isinstance(delta, tuple):
            print("Error: step must be days or weeks only", file=sys.stderr)
            sys.exit(1)
        step_delta = delta
        if step_delta.days <= 0:
            print("Error: step must be positive", file=sys.stderr)
            sys.exit(1)

    current = start
    count = 0
    while current <= end:
        print(format_date(current))
        current += step_delta
        count += 1

    print(f"\n{count} dates in range")


def cmd_age(args):
    if not args:
        print("Usage: chrono age <birthdate> [reference_date]", file=sys.stderr)
        sys.exit(1)

    birth = parse_date(args[0])
    ref = parse_date(args[1]) if len(args) >= 2 else date.today()

    if birth > ref:
        print(f"Error: birthdate {birth} is after reference date {ref}", file=sys.stderr)
        sys.exit(1)

    years = ref.year - birth.year
    months = ref.month - birth.month
    days = ref.day - birth.day

    if days < 0:
        months -= 1
        import calendar
        days += calendar.monthrange(ref.year, ref.month - 1 if ref.month > 1 else 12)[0]
    if months < 0:
        years -= 1
        months += 12

    total_days = (ref - birth).days

    print(f"Birth:      {format_date(birth)}")
    print(f"Reference:  {format_date(ref)}")
    print(f"Age:        {years} years, {months} months, {days} days")
    print(f"Total days: {total_days}")


COMMANDS = {
    "now": cmd_now,
    "days": cmd_days,
    "add": cmd_add,
    "workdays": cmd_workdays,
    "range": cmd_range,
    "age": cmd_age,
}


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: chrono <command> [args...]")
        print()
        print("Commands:")
        print("  now                          Current date/time info")
        print("  days <d1> <d2>               Days between two dates")
        print("  add <date> <delta>            Add/subtract time (90d, 2w, 3m, 1y, -7d)")
        print("  workdays <d1> <d2>           Business days between dates")
        print("  range <start> <end> [step]   Generate date range")
        print("  age <birthdate> [ref]        Calculate age")
        print()
        print("Date formats: YYYY-MM-DD (YYYY/MM/DD, DD-MM-YYYY)")
        print("              'now' or 'today' for current date")
        return

    cmd = args[0]
    cmd_args = args[1:]

    if cmd not in COMMANDS:
        print(f"Error: unknown command '{cmd}'", file=sys.stderr)
        print(f"Available: {', '.join(COMMANDS.keys())}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[cmd](cmd_args)


if __name__ == "__main__":
    main()
