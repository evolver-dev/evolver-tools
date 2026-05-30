#!/usr/bin/env python3
"""cal — 终端日历与日期计算器

零依赖，基于 Python stdlib calendar 和 datetime。
支持日历展示、日期差计算、日期加减、年份概览。
"""

import argparse
import calendar
import datetime
import sys
import os


def get_terminal_width():
    """获取终端宽度，默认 80"""
    try:
        return os.get_terminal_size().columns
    except (ValueError, OSError):
        return 80


def print_calendar(year, month, highlight_today=True):
    """打印单月日历"""
    cal = calendar.TextCalendar()
    month_cal = cal.formatmonth(year, month)

    today = datetime.date.today()
    today_str = f"  {today.day} "
    today_hl = f"[{today.day:2d}]"

    lines = month_cal.split("\n")
    output_lines = []

    # Header: "   January 2026"
    header = lines[0].strip()
    output_lines.append(f"\n  \033[1;36m{header}\033[0m")
    output_lines.append("")

    # Day headers: "Mo Tu We Th Fr Sa Su"
    output_lines.append("  " + lines[1].strip())

    # Week rows
    for line in lines[2:]:
        if not line.strip():
            continue
        formatted = ""
        # Each day occupies 3 chars: " 1 " or " 10"
        for i in range(0, len(line), 3):
            day_str = line[i : i + 3]
            day = day_str.strip()
            if not day:
                formatted += "   "
                continue
            day_num = int(day)
            if highlight_today and today.year == year and today.month == month and today.day == day_num:
                formatted += f"\033[1;33m{day_str}\033[0m"
            else:
                formatted += day_str
        output_lines.append("  " + formatted)

    sys.stdout.write("\n".join(output_lines))
    sys.stdout.write("\n")


def print_year_calendar(year, highlight_today=True):
    """打印全年日历，每行3个月"""
    today = datetime.date.today()
    cal = calendar.TextCalendar()

    months_data = []
    for m in range(1, 13):
        month_lines = cal.formatmonth(year, m).split("\n")
        months_data.append(month_lines)

    # Pad all months to same height
    max_height = max(len(m) for m in months_data)
    for m in months_data:
        while len(m) < max_height:
            m.append("")

    # Print in groups of 3
    for group_start in range(0, 12, 3):
        group = months_data[group_start : group_start + 3]
        for row_idx in range(max_height):
            parts = []
            for month_idx, month_lines in enumerate(group):
                line = month_lines[row_idx]
                actual_month = group_start + month_idx + 1
                if row_idx == 0:
                    # Month name header - center in 20 chars
                    month_name = line.strip()
                    parts.append(f"  {month_name:^20}")
                elif row_idx == 1:
                    parts.append(f"  {'Mo Tu We Th Fr Sa Su':20}")
                else:
                    # Process day numbers with highlight
                    formatted = ""
                    if highlight_today and today.year == year:
                        for i in range(0, len(line), 3):
                            day_str = line[i : i + 3] if i + 3 <= len(line) else line[i:]
                            day = day_str.strip()
                            if day and today.month == actual_month and today.day == int(day):
                                formatted += f"\033[1;33m{day_str}\033[0m"
                            else:
                                formatted += day_str
                    else:
                        formatted = line
                    parts.append(f"  {formatted:20}")
            sys.stdout.write("".join(parts) + "\n")


def cmd_calendar(args):
    """日历展示子命令"""
    today = datetime.date.today()
    year = args.year or today.year
    month = args.month or today.month

    if month:
        print_calendar(year, month, highlight_today=not args.no_highlight)
    else:
        print_year_calendar(year, highlight_today=not args.no_highlight)


def cmd_diff(args):
    """日期差计算"""
    try:
        d1 = datetime.date.fromisoformat(args.diff[0])
        d2 = datetime.date.fromisoformat(args.diff[1])
    except ValueError:
        sys.stderr.write(f"错误: 日期格式无效，请使用 YYYY-MM-DD 格式\n")
        sys.exit(1)

    delta = abs((d2 - d1).days)
    years = delta // 365
    months_rem = (delta % 365) // 30
    weeks = delta // 7
    days_rem = delta % 7

    print(f"  {args.diff[0]} → {args.diff[1]}")
    print(f"  ─{'─' * 40}")
    print(f"  📅 {delta} 天")
    if years or months_rem:
        print(f"     ≈ {years} 年 {months_rem} 月")
    if weeks:
        print(f"     = {weeks} 周 {days_rem} 天")
    print(f"     = {delta * 24} 小时")
    print(f"     = {delta * 24 * 60} 分钟")
    print()


def cmd_add(args):
    """日期加减"""
    try:
        d = datetime.date.fromisoformat(args.date)
    except ValueError:
        sys.stderr.write(f"错误: 日期格式无效，请使用 YYYY-MM-DD\n")
        sys.exit(1)

    result = d + datetime.timedelta(days=args.days)
    direction = "后" if args.days >= 0 else "前"

    print(f"  {args.date} + {args.days}天 = {result.isoformat()}")
    print(f"  {args.date} 的 {abs(args.days)}天{direction}是 {result.isoformat()}")


def main():
    parser = argparse.ArgumentParser(
        description="终端日历与日期计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  cal                         显示本月日历
  cal 2025 3                  显示2025年3月
  cal --year 2026             显示2026全年日历
  cal --diff 2024-01-01 2024-12-31    计算日期差
  cal --add 2024-01-01 30     增加30天
  cal --add 2024-03-01 -7     减7天
        """,
    )

    # Diff mode
    parser.add_argument("--diff", nargs=2, metavar=("DATE1", "DATE2"), help="计算两个日期之间的天数")
    # Add mode
    parser.add_argument("--add", nargs=2, metavar=("DATE", "DAYS"), help="日期加减天数")

    # Calendar display args
    parser.add_argument("year", nargs="?", type=int, default=None, help="年份")
    parser.add_argument("month", nargs="?", type=int, default=None, help="月份 (1-12)")
    parser.add_argument("--year", dest="show_year", action="store_true", help="显示全年日历")
    parser.add_argument("--no-highlight", action="store_true", help="不突出显示今天")

    args = parser.parse_args()

    # Route to subcommands
    if args.diff:
        cmd_diff(args)
    elif args.add:
        # Parse days from string
        try:
            date_str, days_str = args.add
            days = int(days_str)
        except ValueError:
            sys.stderr.write("错误: DAYS 必须为整数\n")
            sys.exit(1)
        args.date = date_str
        args.days = days
        cmd_add(args)
    else:
        # Calendar mode
        if args.month is not None and (args.month < 1 or args.month > 12):
            sys.stderr.write("错误: 月份必须在 1-12 之间\n")
            sys.exit(1)

        calendar.setfirstweekday(calendar.MONDAY)

        today = datetime.date.today()
        year = args.year or today.year
        month = args.month

        if args.show_year:
            print_year_calendar(year, highlight_today=not args.no_highlight)
        elif month:
            print_calendar(year, month, highlight_today=not args.no_highlight)
        else:
            # Just year provided? Show whole year
            if args.year:
                print_year_calendar(args.year, highlight_today=not args.no_highlight)
            else:
                print_calendar(today.year, today.month, highlight_today=not args.no_highlight)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "cal",
    "func": "main",
    "desc": 'Cal',
}

if __name__ == "__main__":
    main()
