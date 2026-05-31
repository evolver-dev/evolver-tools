#!/usr/bin/env python3
"""cron — 定时任务表达式解析器 / Cron expression parser.

Zero-dependency CLI for parsing, describing, and calculating cron schedules.
"""

import sys
from datetime import datetime, timedelta

# ── Constants ──────────────────────────────────────────────────────────

MONTH_NAMES = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
}

DOW_FULL = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']

DOW_ABBR = {
    'SUN': 0, 'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6,
}

MONTH_FULL = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
              5: 'May', 6: 'June', 7: 'July', 8: 'August',
              9: 'September', 10: 'October', 11: 'November', 12: 'December'}

MONTH_SHORT = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
               7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

SPECIAL_STRINGS = {
    '@yearly':   '0 0 1 1 *',
    '@annually': '0 0 1 1 *',
    '@monthly':  '0 0 1 * *',
    '@weekly':   '0 0 * * 0',
    '@daily':    '0 0 * * *',
    '@hourly':   '0 * * * *',
}

# ── Field Parsing ──────────────────────────────────────────────────────


def _resolve_names(text, name_map):
    """Resolve month/DOW names in a field expression to numbers."""
    result = text.upper()
    for name, num in name_map.items():
        result = result.replace(name, str(num))
    return result


def parse_field(field_text, min_val, max_val, name_map=None):
    """Parse a single cron field into a set of allowed values.

    Supports: *, */N, N, N-M, N-M/K, and comma-separated combinations.
    """
    values = set()

    # Resolve named constants before splitting on commas
    if name_map:
        field_text = _resolve_names(field_text, name_map)

    for part in field_text.split(','):
        part = part.strip()
        if not part:
            continue

        if part == '*':
            values.update(range(min_val, max_val + 1))
        elif '/' in part:
            base, step_str = part.split('/', 1)
            step = int(step_str)
            if base == '*':
                values.update(range(min_val, max_val + 1, step))
            else:
                start, end = _parse_range(base, min_val, max_val, name_map)
                for v in range(start, end + 1, step):
                    if min_val <= v <= max_val:
                        values.add(v)
        else:
            start, end = _parse_range(part, min_val, max_val, name_map)
            values.update(range(start, end + 1))

    return values


def _parse_range(part, min_val, max_val, name_map=None):
    """Parse a range like '1-5' or single value '3'."""
    if '-' in part:
        pieces = part.split('-', 1)
        start = int(pieces[0].strip())
        end = int(pieces[1].strip())
    else:
        start = end = int(part.strip())
    return start, end


# ── Cron Expression ────────────────────────────────────────────────────


class CronExpr:
    """Parsed cron expression (5-field standard: min hour dom mon dow)."""

    def __init__(self, expression):
        expr = expression.strip()

        # Handle special string aliases
        if expr.lower() in SPECIAL_STRINGS:
            expr = SPECIAL_STRINGS[expr.lower()]
        elif expr.startswith('@'):
            raise ValueError(f"Unknown special string: {expr}")

        fields = expr.split()
        if len(fields) != 5:
            raise ValueError(
                f"Expected 5 fields (min hour dom mon dow), got {len(fields)}: {expr}"
            )

        self.raw = expr
        self.minutes = parse_field(fields[0], 0, 59)
        self.hours = parse_field(fields[1], 0, 23)
        self.days = parse_field(fields[2], 1, 31)
        self.months = parse_field(fields[3], 1, 12, MONTH_NAMES)
        self.dows = parse_field(fields[4], 0, 7)

        # Normalize DOW: 7 -> 0 (Sunday)
        if 7 in self.dows:
            self.dows.discard(7)
            self.dows.add(0)

        self._validate()

    def _validate(self):
        if not self.minutes:
            raise ValueError("Minute field is empty")
        if not self.hours:
            raise ValueError("Hour field is empty")
        if not self.days:
            raise ValueError("Day-of-month field is empty")
        if not self.months:
            raise ValueError("Month field is empty")
        if not self.dows:
            raise ValueError("Day-of-week field is empty")

    def matches(self, dt):
        """Check whether *dt* satisfies this cron expression."""
        if dt.month not in self.months:
            return False
        if dt.hour not in self.hours:
            return False
        if dt.minute not in self.minutes:
            return False

        # Day-of-week / day-of-month OR logic (standard cron semantics):
        # If either is restricted (not *), both must match only when BOTH are restricted.
        all_dom = set(range(1, 32))
        all_dow = set(range(0, 7))
        dom_restricted = self.days != all_dom
        dow_restricted = self.dows != all_dow

        dom_match = dt.day in self.days
        dow_match = dt.weekday() in self.dows

        if dom_restricted and dow_restricted:
            return dom_match and dow_match
        if dom_restricted:
            return dom_match
        if dow_restricted:
            return dow_match
        return True  # both are wildcards

    def next_n(self, n=5, from_dt=None):
        """Return the next *n* execution datetimes (list of datetime)."""
        if from_dt is None:
            from_dt = datetime.now()
        # Start scanning from the next full minute
        dt = from_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        results = []
        # Safety limit: scan at most 1 year ahead (525600 minutes)
        max_iter = 525600
        while len(results) < n and max_iter > 0:
            if self.matches(dt):
                results.append(dt)
            dt += timedelta(minutes=1)
            max_iter -= 1
        return results

    def describe(self):
        """Return a human-readable description of this cron expression."""

        # ── Named shortcuts ──────────────────────────────────────────
        all_min = set(range(0, 60))
        all_hour = set(range(0, 24))
        all_dom = set(range(1, 32))
        all_mon = set(range(1, 13))
        all_dow = set(range(0, 7))

        if (self.minutes == {0} and self.hours == {0} and self.days == {1}
                and self.months == {1} and self.dows == all_dow):
            return "At midnight on January 1st — annually (@yearly / @annually)"

        if (self.minutes == {0} and self.hours == {0} and self.days == {1}
                and self.months == all_mon and self.dows == all_dow):
            return "At midnight on the 1st of every month — monthly (@monthly)"

        if (self.minutes == {0} and self.hours == {0}
                and self.days == all_dom and self.months == all_mon
                and self.dows == {0}):
            return "At midnight on Sunday — weekly (@weekly)"

        if (self.minutes == {0} and self.hours == {0}
                and self.days == all_dom and self.months == all_mon
                and self.dows == all_dow):
            return "At midnight every day — daily (@daily)"

        if (self.minutes == {0} and self.hours == all_hour
                and self.days == all_dom and self.months == all_mon
                and self.dows == all_dow):
            return "At the start of every hour — hourly (@hourly)"

        # ── Build field descriptions ─────────────────────────────────
        parts = []

        # Minutes
        if self.minutes == all_min:
            parts.append("Every minute")
        elif len(self.minutes) == 1:
            v = next(iter(self.minutes))
            parts.append(f"At minute {v}")
        else:
            parts.append(f"At minutes {_fmt_set(self.minutes)}")

        # Hours
        if self.hours != all_hour:
            if len(self.hours) == 1:
                v = next(iter(self.hours))
                if v == 0:
                    parts.append("past midnight")
                elif v < 12:
                    parts.append(f"past {v}:00 AM")
                elif v == 12:
                    parts.append("past noon")
                else:
                    parts.append(f"past {v-12}:00 PM")
            else:
                parts.append(f"past hours {_fmt_set(self.hours)}")

        # Days of month
        dom_restricted = self.days != all_dom
        if dom_restricted:
            if len(self.days) == 1:
                v = next(iter(self.days))
                parts.append(f"on day {v}")
            else:
                parts.append(f"on days {_fmt_set(self.days)}")

        # Months
        if self.months != all_mon:
            if len(self.months) == 1:
                v = next(iter(self.months))
                parts.append(f"in {MONTH_FULL[v]}")
            else:
                parts.append(f"in {_fmt_month(self.months)}")

        # Days of week
        if self.dows != all_dow:
            if len(self.dows) == 1:
                v = next(iter(self.dows))
                parts.append(f"on {DOW_FULL[v]}")
            else:
                parts.append(f"on {_fmt_dow(self.dows)}")

        return ' '.join(parts)


def _fmt_set(values):
    """Format a set of integers as 'a, b, c' or 'a-b'."""
    sv = sorted(values)
    if len(sv) == 1:
        return str(sv[0])
    if all(sv[i + 1] - sv[i] == 1 for i in range(len(sv) - 1)):
        return f"{sv[0]}-{sv[-1]}"
    return ', '.join(str(v) for v in sv)


def _fmt_month(values):
    sv = sorted(values)
    if all(sv[i + 1] - sv[i] == 1 for i in range(len(sv) - 1)):
        return f"{MONTH_SHORT[sv[0]]}-{MONTH_SHORT[sv[-1]]}"
    return ', '.join(MONTH_SHORT[v] for v in sv)


def _fmt_dow(values):
    sv = sorted(values)
    if all(sv[i + 1] - sv[i] == 1 for i in range(len(sv) - 1)):
        return f"{DOW_FULL[sv[0]]}-{DOW_FULL[sv[-1]]}"
    return ', '.join(DOW_FULL[v] for v in sv)


# ── CLI ────────────────────────────────────────────────────────────────


def print_help():
    print("""cron — Cron 表达式解析器 / Cron expression parser

用法:
  cron '<expression>'              解析并显示描述 + 接下来5次执行
  cron --next <expression> [N]     显示接下来 N 次执行时间 (默认: 5)
  cron --describe <expression>     仅显示人类可读描述
  cron --help                      显示此帮助

表达式格式:
  分钟(0-59) 小时(0-23) 日(1-31) 月(1-12) 星期(0-7)

  支持通配:  *         全部
            */N       每 N 个单位
            A-B       范围
            A-B/N     范围每 N 个
            A,B,C     列表

  月份别名: JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
  星期别名: SUN MON TUE WED THU FRI SAT  (0 或 7 = 周日)

特殊字符串:
  @yearly / @annually   每年1月1日0点
  @monthly              每月1日0点
  @weekly               每周日0点
  @daily                每天0点
  @hourly               每小时0分

示例:
  cron '*/5 * * * *'              每5分钟
  cron --next '0 9 * * 1-5'       工作日早上9点
  cron --next '0 9 * * 1-5' 10    显示接下来10次
  cron --describe '30 4 * * 1-5'  仅描述
  cron '@daily'                   每天午夜
  cron '0 0 1 1 *'                每年元旦""")


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print_help()
        return

    mode = 'all'
    expr_str = None
    n = 5

    if args[0] == '--next':
        mode = 'next'
        if len(args) >= 2:
            expr_str = args[1]
        if len(args) >= 3:
            try:
                n = int(args[2])
            except ValueError:
                print(f"错误: 无效的数字 '{args[2]}'", file=sys.stderr)
                sys.exit(1)
    elif args[0] == '--describe':
        mode = 'describe'
        if len(args) >= 2:
            expr_str = args[1]
    else:
        # First positional arg is the expression
        expr_str = args[0]
        if len(args) >= 2:
            try:
                n = int(args[1])
            except ValueError:
                pass  # ignore extra non-numeric arg

    if not expr_str:
        print("错误: 缺少 cron 表达式", file=sys.stderr)
        print()
        print_help()
        sys.exit(1)

    try:
        cron = CronExpr(expr_str)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    if mode in ('describe', 'all'):
        print(f"表达式:  {cron.raw}")
        print(f"描述:     {cron.describe()}")
        print()

    if mode in ('next', 'all'):
        times = cron.next_n(n)
        if not times:
            print("(在合理扫描范围内未找到匹配的执行时间)")
        else:
            if n == 1:
                print(f"下一次执行时间:")
            else:
                print(f"接下来 {len(times)} 次执行时间:")
            now = datetime.now()
            today = now.date()
            tomorrow = (now + timedelta(days=1)).date()
            for i, t in enumerate(times, 1):
                suffix = ''
                if t.date() == today:
                    suffix = ' (今天)'
                elif t.date() == tomorrow:
                    suffix = ' (明天)'
                print(f"  {i}. {t.strftime('%Y-%m-%d %H:%M')}{suffix}  {DOW_FULL[t.weekday()]}")
        print()



# === Auto-registration metadata ===
TOOL_META = {
    "name": "cron",
    "func": "main",
    "desc": 'Cron expression parser',
}

if __name__ == '__main__':
    main()
