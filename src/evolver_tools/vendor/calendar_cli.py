#!/usr/bin/env python3
"""calendar-cli — Display a terminal calendar."""
import calendar
import sys
from datetime import datetime

TOOL_META = {
    "name": "calendar-cli",
    "func": "main",
    "desc": "Display terminal calendar. Usage: calendar-cli [year] [month]",
}

def main():
    args = sys.argv[1:]
    now = datetime.now()
    year = now.year
    month = now.month
    if len(args) >= 2:
        try:
            year = int(args[0])
            month = int(args[1])
        except ValueError:
            print("Usage: calendar-cli [year] [month]", file=sys.stderr)
            sys.exit(1)
    elif len(args) >= 1:
        try:
            year = int(args[0])
            month = None
        except ValueError:
            print("Usage: calendar-cli [year] [month]", file=sys.stderr)
            sys.exit(1)
    cal = calendar.TextCalendar()
    if month:
        cal_str = cal.formatmonth(year, month)
        # Highlight today
        if year == now.year and month == now.month:
            today = str(now.day)
            cal_str = cal_str.replace(f" {today} ", f"[{today}]")
            cal_str = cal_str.replace(f"{today} ", f"[{today}]")
        print(cal_str)
    else:
        print(cal.formatyear(year))

if __name__ == "__main__":
    main()
