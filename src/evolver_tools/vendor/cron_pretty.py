#!/usr/bin/env python3
"""cron-pretty — Pretty-print cron expressions in human-readable format."""
import re
import sys

TOOL_META = {
    "name": "cron-pretty",
    "func": "main",
    "desc": "Describe cron schedule in plain English. Usage: cron-pretty '*/5 * * * *'",
}

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS = [None, "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

def describe(minute, hour, dom, month, dow):
    parts = []
    # Minute
    if minute == "*":
        min_desc = "every minute"
    elif re.match(r"^\d+$", minute):
        min_desc = f"at minute {minute}"
    elif minute.startswith("*/"):
        step = minute[2:]
        min_desc = f"every {step} minutes"
    else:
        min_desc = f"minute {minute}"
    parts.append(min_desc)
    # Hour
    if hour == "*":
        hour_desc = "of every hour"
    elif re.match(r"^\d+$", hour):
        hour_desc = f"past hour {hour}"
    elif hour.startswith("*/"):
        step = hour[2:]
        hour_desc = f"every {step} hours"
    else:
        hour_desc = f"hour {hour}"
    parts.append(hour_desc)
    # Day of month
    if dom == "*":
        dom_desc = "every day"
    elif dom.startswith("*/"):
        step = dom[2:]
        dom_desc = f"every {step} days"
    elif "," in dom:
        days = dom.split(",")
        dom_desc = f"on days {', '.join(days)}"
    else:
        dom_desc = f"on day {dom}"
    parts.append(dom_desc)
    # Month
    if month == "*":
        month_desc = "of every month"
    elif re.match(r"^\d+$", month):
        m = int(month)
        month_desc = f"in {MONTHS[m] if m <= 12 else month}"
    elif month.startswith("*/"):
        step = month[2:]
        month_desc = f"every {step} months"
    else:
        month_desc = f"in month {month}"
    parts.append(month_desc)
    # Day of week
    if dow == "*":
        dow_desc = ""
    elif re.match(r"^\d+$", dow):
        d = int(dow)
        dow_desc = f"on {WEEKDAYS[d]}"
    elif "," in dow:
        days = [WEEKDAYS[int(d)] if d.isdigit() else d for d in dow.split(",")]
        dow_desc = f"on {', '.join(days)}"
    else:
        dow_desc = f"on {dow}"
    if dow_desc:
        parts.append(dow_desc)
    # Special cases
    if minute == "0" and hour == "0" and dom == "*" and month == "*" and dow == "*":
        return "At midnight, every day"
    if minute == "0" and hour == "12" and dom == "*" and month == "*" and dow == "*":
        return "At noon, every day"
    if minute == "0" and hour in ("0", "12") and dom == "1" and month == "*" and dow == "*":
        return f"At {hour}:00 AM, on the 1st of every month"
    if minute == "0" and hour == "9" and dom == "*" and month == "*" and dow in ("1", "1-5"):
        return "At 9:00 AM, Monday through Friday"
    if minute == "30" and hour == "9" and dom == "*" and month == "*" and dow in ("1", "1-5"):
        return "At 9:30 AM, Monday through Friday"
    # Build description
    result = f"{parts[0]} {parts[1]} {parts[2]} {parts[3]}"
    if len(parts) > 4:
        result += f" {parts[4]}"
    return result

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: cron-pretty '*/5 * * * *'", file=sys.stderr)
        print("       cron-pretty '30 9 * * 1-5'", file=sys.stderr)
        sys.exit(1)
    expr = args[0].strip()
    fields = expr.split()
    # Handle special strings
    special = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@hourly": "0 * * * *",
        "@reboot": None,
    }
    if expr in special:
        resolved = special[expr]
        if resolved is None:
            print(f"'{expr}' — runs at system startup/reboot")
            return
        fields = resolved.split()
    if len(fields) != 5:
        print(f"Invalid cron expression: '{expr}'", file=sys.stderr)
        print("Expected format: minute hour day-of-month month day-of-week", file=sys.stderr)
        sys.exit(1)
    minute, hour, dom, month, dow = fields
    description = describe(minute, hour, dom, month, dow)
    print(f"  {expr}")
    print(f"  → {description}")

if __name__ == "__main__":
    main()
