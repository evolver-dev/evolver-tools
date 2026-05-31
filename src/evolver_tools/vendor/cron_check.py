#!/usr/bin/env python3
"""cron-check — Validate and describe cron expressions.

Usage: cron-check "*/5 * * * *"
       cron-check --describe "0 9 * * 1-5"
       cron-check --next 5 "*/15 * * * *"
       cron-check --validate "0 0 1 * *"
"""
import argparse
import calendar
import re
import sys
from datetime import datetime, timedelta

TOOL_META = {
    "name": "cron-check",
    "func": "main",
    "desc": "Validate and describe cron expressions",
}

WEEKDAY_NAMES = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday",
]
MONTH_NAMES = [
    None, "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SPECIAL = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


def _parse_field(field, lo, hi, name):
    """Parse a single cron field. Returns set of accepted values or None if wildcard.

    Raises ValueError on invalid syntax.
    """
    if field == "*":
        return None  # wildcard
    if field.startswith("*/"):
        step = field[2:]
        if not step.isdigit() or int(step) < 1:
            raise ValueError(f"Invalid step in {name}: '{field}'")
        return range(lo, hi + 1, int(step))
    values = set()
    for part in field.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"Empty element in {name}: '{field}'")
        if "-" in part:
            parts = part.split("-", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid range in {name}: '{part}'")
            a_str, b_str = parts
            if not a_str.isdigit() or not b_str.isdigit():
                raise ValueError(f"Non-numeric range in {name}: '{part}'")
            a, b = int(a_str), int(b_str)
            if a > b:
                raise ValueError(f"Range inverted in {name}: '{part}'")
            for v in range(a, b + 1):
                if v < lo or v > hi:
                    raise ValueError(f"Value {v} out of range [{lo}-{hi}] in {name}")
                values.add(v)
        elif part.isdigit():
            v = int(part)
            if v < lo or v > hi:
                raise ValueError(f"Value {v} out of range [{lo}-{hi}] in {name}")
            values.add(v)
        else:
            raise ValueError(f"Invalid token in {name}: '{part}'")
    return values


def parse_cron(expr):
    """Parse a 5-field cron expression. Returns (minute, hour, dom, month, dow)
    where each is a set of values or None for wildcard."""
    stripped = expr.strip()
    if stripped in SPECIAL:
        stripped = SPECIAL[stripped]

    fields = stripped.split()
    if len(fields) != 5:
        raise ValueError(
            f"Expected 5 fields, got {len(fields)}. "
            "Format: minute hour day-of-month month day-of-week"
        )

    minute = _parse_field(fields[0], 0, 59, "minute")
    hour = _parse_field(fields[1], 0, 23, "hour")
    dom = _parse_field(fields[2], 1, 31, "day-of-month")
    month = _parse_field(fields[3], 1, 12, "month")
    dow = _parse_field(fields[4], 0, 7, "day-of-week")

    # Normalize DOW: 7 -> 0 (both mean Sunday)
    if dow is not None:
        dow = {0 if d == 7 else d for d in dow}

    return minute, hour, dom, month, dow


def _describe_value(val, lo, hi, singular, plural, range_map):
    """Describe a single field value."""
    if val is None:
        return f"every {plural}" if lo == 0 or lo is None else f"every {singular}"
    if isinstance(val, range) or hasattr(val, "__iter__") and not isinstance(val, (set, frozenset)):
        # step range
        lst = list(val)
        if len(lst) > 1:
            step = lst[1] - lst[0]
            return f"every {step} {plural}"
    if isinstance(val, set):
        # Check if it's a range like 1-5
        if len(val) > 1:
            sorted_vals = sorted(val)
            if sorted_vals == list(range(sorted_vals[0], sorted_vals[-1] + 1)):
                lo_v, hi_v = sorted_vals[0], sorted_vals[-1]
                if range_map and lo_v in range_map and hi_v in range_map:
                    return f"{range_map[lo_v]}-{range_map[hi_v]}"
                return f"{lo_v}-{hi_v}"
            items = [range_map.get(v, str(v)) if range_map else str(v) for v in sorted_vals]
            return ", ".join(items)
    return str(val)


def _field_desc(field, lo, hi, singular, plural, range_map=None):
    """Describe a single cron field as English."""
    if field is None:
        return f"every {singular}" if lo == 0 else f"every {singular}"

    if isinstance(field, range):
        step = field[1] - field[0]
        if step == 1:
            return f"every {singular}"
        return f"every {step} {plural}"

    sorted_vals = sorted(field)
    if len(sorted_vals) == 1:
        v = sorted_vals[0]
        if range_map and v in range_map:
            name = range_map[v]
            if lo == 1:  # day-of-month
                suffix = "st" if v == 1 else "nd" if v == 2 else "rd" if v == 3 else "th"
                return f"on the {v}{suffix}"
            return f"on {name}"
        return str(v)

    # Multiple values
    if sorted_vals == list(range(sorted_vals[0], sorted_vals[-1] + 1)):
        lo_v, hi_v = sorted_vals[0], sorted_vals[-1]
        if range_map:
            if lo_v == 1:
                # Check if all values covered = "every"
                if sorted_vals == list(range(lo, hi + 1)):
                    return f"every {singular}"
            return f"every {singular} ({lo_v}-{hi_v})"
        return f"every {singular} ({lo_v}-{hi_v})"

    # Mixed values
    items = []
    for v in sorted_vals:
        if range_map and v in range_map:
            items.append(range_map[v])
        else:
            items.append(str(v))
    return ", ".join(items)


def describe(expr):
    """Produce a human-readable description of a cron expression."""
    minute, hour, dom, month, dow = parse_cron(expr)

    # Build parts
    parts = []

    # Time specification
    time_parts = []

    if minute is None and hour is None:
        time_parts.append("every minute")
    elif hour is None:
        # Every hour, specific minute(s)
        min_desc = _field_desc(minute, 0, 59, "minute", "minutes")
        if minute is not None and len(minute) == 1:
            v = list(minute)[0]
            time_parts.append(f"at minute {v} of every hour")
        else:
            time_parts.append(f"{min_desc} of every hour")
    elif minute is None:
        # Every minute of specific hour
        hour_desc = _field_desc(hour, 0, 23, "hour", "hours")
        time_parts.append(f"every minute past {hour_desc}")
    else:
        # Specific time
        min_desc = _field_desc(minute, 0, 59, "minute", "minutes")
        hour_desc = _field_desc(hour, 0, 23, "hour", "hours")

        if len(hour) == 1 and len(minute) == 1:
            h = list(hour)[0]
            m = list(minute)[0]
            ampm = "AM" if h < 12 else "PM"
            h12 = h if h <= 12 else h - 12
            if h12 == 0:
                h12 = 12
            time_parts.append(f"at {h12}:{m:02d} {ampm}")
        elif len(hour) == 1:
            h = list(hour)[0]
            ampm = "AM" if h < 12 else "PM"
            h12 = h if h <= 12 else h - 12
            if h12 == 0:
                h12 = 12
            time_parts.append(f"at minute {min_desc} past {h12}:00 {ampm}")
        else:
            time_parts.append(f"at {min_desc} past {hour_desc}")

    # Day of week
    dow_desc = ""
    if dow is not None and dom is None:
        sorted_dow = sorted(dow)
        if sorted_dow == list(range(sorted_dow[0], sorted_dow[-1] + 1)):
            lo, hi = sorted_dow[0], sorted_dow[-1]
            if lo == 1 and hi == 5:
                dow_desc = ", Monday through Friday"
            elif lo == 0 and hi == 6:
                dow_desc = ", every day of the week"
            elif lo == 0 and hi == 5:
                dow_desc = ", Monday through Saturday"
            else:
                dow_desc = f", {WEEKDAY_NAMES[lo]} through {WEEKDAY_NAMES[hi]}"
        elif len(sorted_dow) == 1:
            dow_desc = f", on {WEEKDAY_NAMES[sorted_dow[0]]}"
        else:
            names = [WEEKDAY_NAMES[d] for d in sorted_dow]
            dow_desc = f", on {' and '.join(n for n in names)}"

    # Day of month
    dom_desc = ""
    if dom is not None:
        sorted_dom = sorted(dom)
        if len(sorted_dom) == 1:
            v = sorted_dom[0]
            suffix = "st" if v == 1 else "nd" if v == 2 else "rd" if v == 3 else "th"
            dom_desc = f" on the {v}{suffix}"
        elif sorted_dom == list(range(sorted_dom[0], sorted_dom[-1] + 1)):
            lo, hi = sorted_dom[0], sorted_dom[-1]
            if lo == 1 and hi == 31:
                dom_desc = " every day"
            else:
                dom_desc = f" on days {lo}-{hi}"
        else:
            items = []
            for v in sorted_dom:
                suffix = "st" if v == 1 else "nd" if v == 2 else "rd" if v == 3 else "th"
                items.append(f"{v}{suffix}")
            dom_desc = f" on {' and '.join(items)}"

    # Month
    month_desc = ""
    if month is not None:
        sorted_m = sorted(month)
        if len(sorted_m) == 1:
            month_desc = f" in {MONTH_NAMES[sorted_m[0]]}"
        elif sorted_m == list(range(sorted_m[0], sorted_m[-1] + 1)):
            lo, hi = sorted_m[0], sorted_m[-1]
            if lo == 1 and hi == 12:
                month_desc = " every month"
            else:
                month_desc = f" from {MONTH_NAMES[lo]} to {MONTH_NAMES[hi]}"
        else:
            names = [MONTH_NAMES[m] for m in sorted_m]
            month_desc = f" in {' and '.join(n for n in names)}"

    # Combine
    result = "".join(time_parts) + dom_desc + month_desc + dow_desc

    # Clean up
    if result.startswith("every minute every hour"):
        result = "every minute" + result[len("every minute every hour"):]

    return result.strip().capitalize()


def _matches(field, value):
    """Check if a value matches a parsed field."""
    if field is None:
        return True
    return value in field


def next_times(expr, count):
    """Calculate the next N execution times for a cron expression."""
    minute, hour, dom, month, dow = parse_cron(expr)

    now = datetime.now()
    # Start from the next minute
    current = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    results = []
    max_iterations = 100000  # safety valve
    iterations = 0

    while len(results) < count and iterations < max_iterations:
        iterations += 1

        # Check month
        if not _matches(month, current.month):
            # Skip to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1, hour=0, minute=0)
            else:
                current = current.replace(month=current.month + 1, day=1, hour=0, minute=0)
            continue

        # Check day of month
        if not _matches(dom, current.day):
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
            continue

        # Check day of week
        if not _matches(dow, current.weekday()):
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
            continue

        # Check hour
        if not _matches(hour, current.hour):
            current += timedelta(hours=1)
            current = current.replace(minute=0)
            continue

        # Check minute
        if not _matches(minute, current.minute):
            current += timedelta(minutes=1)
            continue

        # Match!
        results.append(current)
        current += timedelta(minutes=1)

    return results


def validate(expr):
    """Validate a cron expression. Returns True if valid, False otherwise."""
    try:
        parse_cron(expr)
        return True
    except (ValueError, IndexError):
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate and describe cron expressions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  cron-check "*/5 * * * *"\n'
            '  cron-check -d "0 9 * * 1-5"\n'
            '  cron-check --next 5 "*/15 * * * *"\n'
            '  cron-check --validate "0 0 1 * *"\n'
            '\n'
            "Exit codes:\n"
            "  0  expression is valid\n"
            "  1  expression is invalid (with --validate)\n"
        ),
    )
    parser.add_argument("expression", nargs="?", help="Cron expression (5 fields: minute hour dom month dow)")
    parser.add_argument("-d", "--describe", action="store_true", help="Show human-readable description")
    parser.add_argument("--next", nargs="?", const=5, type=int, default=None,
                        help="Show next N execution times (default: 5)")
    parser.add_argument("--validate", action="store_true", help="Just validate; exit 0 (valid) or 1 (invalid)")

    args = parser.parse_args()

    if not args.expression:
        parser.print_help()
        sys.exit(1)

    expr = args.expression

    # Handle special strings for validation
    if expr.strip() in SPECIAL:
        if args.validate:
            sys.exit(0)
        if args.describe:
            name = expr.strip()
            print(f"  {name}")
            desc_map = {
                "@yearly": "Once a year, at midnight on January 1st",
                "@annually": "Once a year, at midnight on January 1st",
                "@monthly": "Once a month, at midnight on the 1st",
                "@weekly": "Once a week, at midnight on Sunday",
                "@daily": "Every day at midnight",
                "@midnight": "Every day at midnight",
                "@hourly": "Every hour at minute 0",
            }
            print(f"  \u2192 {desc_map.get(name, '')}")
            return
        if args.next is not None:
            expr = SPECIAL[expr.strip()]

    # Parse and validate
    try:
        parsed = parse_cron(expr)
    except ValueError as e:
        print(f"Invalid cron expression: {e}", file=sys.stderr)
        if args.validate:
            sys.exit(1)
        sys.exit(1)

    if args.validate:
        sys.exit(0)

    # Resolve special strings for display
    display_expr = expr.strip()
    for key, val in SPECIAL.items():
        if val == display_expr and key != display_expr:
            break
    else:
        key = None

    # Describe mode
    if args.describe:
        print(f"  {expr}")
        if key:
            print(f"  ({key})")
        print(f"  \u2192 {describe(expr)}")
        return

    # Next times mode
    if args.next is not None:
        count = args.next
        times = next_times(expr, min(count, 100))
        if not times:
            print(f"No future execution times found for: {expr}", file=sys.stderr)
            sys.exit(1)
        print(f"  Next {len(times)} execution time{'s' if len(times) != 1 else ''} for:")
        print(f"  {expr}")
        if key:
            print(f"  ({key})")
        print()
        for when in times:
            print(f"    \u2022 {when.strftime('%Y-%m-%d %H:%M  %A')}")

        if len(times) < count:
            print()
            print(f"  (Only {len(times)} found within search range)")
        return

    # Default: validate + describe
    print(f"  Expression: {expr}")
    print(f"  Valid:      \u2713 yes")
    print(f"  Schedule:   {describe(expr)}")


if __name__ == "__main__":
    main()
