#!/usr/bin/env python3
"""crontab-helper — Simplify crontab management. List, add, remove, edit cron jobs."""
import sys
import os
import argparse
import subprocess
import re
from datetime import datetime


HUMAN_SCHEDULES = {
    "every minute": "* * * * *",
    "every hour": "0 * * * *",
    "every 2 hours": "0 */2 * * *",
    "every 3 hours": "0 */3 * * *",
    "every 4 hours": "0 */4 * * *",
    "every 6 hours": "0 */6 * * *",
    "every 8 hours": "0 */8 * * *",
    "every 12 hours": "0 */12 * * *",
    "every day at midnight": "0 0 * * *",
    "every day at 1am": "0 1 * * *",
    "every day at 2am": "0 2 * * *",
    "every day at 3am": "0 3 * * *",
    "every day at 4am": "0 4 * * *",
    "every day at 5am": "0 5 * * *",
    "every day at 6am": "0 6 * * *",
    "every day at 7am": "0 7 * * *",
    "every day at 8am": "0 8 * * *",
    "every day at 9am": "0 9 * * *",
    "every day at 10am": "0 10 * * *",
    "every day at 11am": "0 11 * * *",
    "every day at noon": "0 12 * * *",
    "every day at 1pm": "0 13 * * *",
    "every day at 2pm": "0 14 * * *",
    "every day at 3pm": "0 15 * * *",
    "every day at 4pm": "0 16 * * *",
    "every day at 5pm": "0 17 * * *",
    "every day at 6pm": "0 18 * * *",
    "every day at 7pm": "0 19 * * *",
    "every day at 8pm": "0 20 * * *",
    "every day at 9pm": "0 21 * * *",
    "every day at 10pm": "0 22 * * *",
    "every day at 11pm": "0 23 * * *",
    "every weekday at midnight": "0 0 * * 1-5",
    "every weekday at 9am": "0 9 * * 1-5",
    "every weekday at 5pm": "0 17 * * 1-5",
    "every monday": "0 0 * * 1",
    "every tuesday": "0 0 * * 2",
    "every wednesday": "0 0 * * 3",
    "every thursday": "0 0 * * 4",
    "every friday": "0 0 * * 5",
    "every saturday": "0 0 * * 6",
    "every sunday": "0 0 * * 0",
    "every 1st of month": "0 0 1 * *",
    "every 15th of month": "0 0 15 * *",
    "every 30 minutes": "*/30 * * * *",
    "every 15 minutes": "*/15 * * * *",
    "every 10 minutes": "*/10 * * * *",
    "every 5 minutes": "*/5 * * * *",
    "@reboot": "@reboot",
    "@yearly": "@yearly",
    "@annually": "@annually",
    "@monthly": "@monthly",
    "@weekly": "@weekly",
    "@daily": "@daily",
    "@hourly": "@hourly",
}


def get_crontab():
    """Get current crontab content. Returns (lines, has_crontab)."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return [l for l in lines if l.strip() or l == ""], True
        elif "no crontab" in result.stderr.lower():
            return [], True
        else:
            print(f"Error accessing crontab: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("Error: crontab command not found", file=sys.stderr)
        sys.exit(1)


def set_crontab(lines):
    """Write crontab content."""
    content = "\n".join(lines) + "\n"
    try:
        result = subprocess.run(
            ["crontab", "-"],
            input=content,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error writing crontab: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("Error: crontab command not found", file=sys.stderr)
        sys.exit(1)


def parse_human_schedule(text):
    """Parse a human-readable schedule into cron format."""
    text = text.lower().strip()
    if text in HUMAN_SCHEDULES:
        return HUMAN_SCHEDULES[text]
    # Try pattern matching
    # "every X hours" where X is a number
    m = re.match(r"every\s+(\d+)\s+hours?", text)
    if m:
        return f"0 */{m.group(1)} * * *"
    # "every day at HH:MM" or "every day at HHam" or "every day at HHpm"
    m = re.match(r"every\s+day\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)?", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        meridian = m.group(3)
        if meridian:
            if meridian.lower() == "pm" and hour < 12:
                hour += 12
            elif meridian.lower() == "am" and hour == 12:
                hour = 0
        return f"{minute} {hour} * * *"
    # "every weekday at HH:MM"
    m = re.match(r"every\s+weekday\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)?", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        meridian = m.group(3)
        if meridian:
            if meridian.lower() == "pm" and hour < 12:
                hour += 12
            elif meridian.lower() == "am" and hour == 12:
                hour = 0
        return f"{minute} {hour} * * 1-5"
    # "every month on day D at HH:MM"
    m = re.match(r"every\s+month\s+on\s+day\s+(\d+)\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)?", text)
    if m:
        day = int(m.group(1))
        hour = int(m.group(2))
        minute = int(m.group(3)) if m.group(3) else 0
        meridian = m.group(4)
        if meridian:
            if meridian.lower() == "pm" and hour < 12:
                hour += 12
            elif meridian.lower() == "am" and hour == 12:
                hour = 0
        return f"{minute} {hour} {day} * *"
    return text


def describe_cron(expr):
    """Describe a cron expression in human-readable form."""
    # Check preset
    for desc, cron in HUMAN_SCHEDULES.items():
        if cron == expr:
            return desc
    parts = expr.strip().split()
    if len(parts) == 5:
        minute, hour, dom, month, dow = parts
        desc_parts = []
        if minute == "*" and hour == "*":
            desc_parts.append("every minute")
        elif minute == "0" and hour == "*":
            desc_parts.append("every hour")
        elif minute == "0":
            desc_parts.append(f"at {hour}:00")
        elif minute != "0":
            desc_parts.append(f"at {hour}:{minute}")
        if dom != "*":
            desc_parts.append(f"on day {dom}")
        if month != "*":
            desc_parts.append(f"in month {month}")
        if dow != "*":
            day_names = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
                         4: "Thursday", 5: "Friday", 6: "Saturday"}
            dow_desc = dow
            try:
                d = int(dow)
                dow_desc = day_names.get(d, dow)
            except ValueError:
                pass
            desc_parts.append(f"({dow_desc})")
        return " ".join(desc_parts) if desc_parts else expr
    return expr


def parse_cron_jobs(lines):
    """Parse crontab lines into named jobs."""
    jobs = []
    comment = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            comment = stripped.lstrip("#").strip()
            continue
        if not stripped:
            comment = ""
            continue
        # Check if it's a valid cron line
        parts = stripped.split()
        if len(parts) >= 6 and (re.match(r'^[\d*/,\-]+$', parts[0]) or parts[0] == '@'):
            # Could be a cron job
            schedule = " ".join(parts[:5])
            command = " ".join(parts[5:])
            jobs.append({
                "line": stripped,
                "schedule": schedule,
                "command": command,
                "comment": comment,
                "index": len(jobs),
            })
            comment = ""
        elif len(parts) >= 1 and parts[0].startswith("@"):
            # @reboot, @daily, etc.
            schedule = parts[0]
            command = " ".join(parts[1:])
            jobs.append({
                "line": stripped,
                "schedule": schedule,
                "command": command,
                "comment": comment,
                "index": len(jobs),
            })
            comment = ""
        else:
            comment = ""
    return jobs


def cmd_list(args):
    """List all cron jobs."""
    lines, has = get_crontab()
    if not lines or all(l.strip() == "" for l in lines):
        print("No cron jobs configured.")
        return

    jobs = parse_cron_jobs(lines)
    if not jobs:
        print("No cron jobs found.")
        return

    print(f"Cron jobs ({len(jobs)}):")
    print()
    for job in jobs:
        desc = describe_cron(job["schedule"])
        idx = job["index"] + 1
        if job["comment"]:
            print(f"  [{idx}] #{job['comment']}")
        print(f"      Schedule: {desc}")
        print(f"      Command:  {job['command']}")
        print()


def cmd_add(args):
    """Add a new cron job."""
    lines, has = get_crontab()

    # Parse schedule
    schedule = parse_human_schedule(args.schedule)

    if not args.command:
        print("Error: No command provided for cron job", file=sys.stderr)
        sys.exit(1)

    # Add entry
    comment_line = ""
    if args.label:
        comment_line = f"# {args.label}"

    if comment_line:
        lines.append(comment_line)
    lines.append(f"{schedule} {args.command}")

    set_crontab(lines)
    print(f"Added cron job: {schedule} {args.command}")

    desc = describe_cron(schedule)
    print(f"Schedule: {desc}")


def cmd_remove(args):
    """Remove a cron job by index."""
    lines, has = get_crontab()
    if not lines:
        print("No cron jobs to remove.")
        return

    jobs = parse_cron_jobs(lines)
    if args.index < 1 or args.index > len(jobs):
        print(f"Error: Invalid job index {args.index}. Valid range: 1-{len(jobs)}", file=sys.stderr)
        sys.exit(1)

    idx = args.index - 1
    job = jobs[idx]

    print(f"Removing job [{args.index}]:")
    if job["comment"]:
        print(f"  # {job['comment']}")
    print(f"  {job['schedule']} {job['command']}")

    if not args.force:
        try:
            response = input("Confirm removal? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if response not in ("y", "yes"):
            print("Aborted.")
            return

    # Remove the job line and its preceding comment
    line_idx = None
    comment_idx = None
    current_line = 0
    job_count = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("#"):
            comment_idx = i
            continue
        if s and not s.startswith("#"):
            # Check if it's a cron job line
            parts = s.split()
            if (len(parts) >= 6 and re.match(r'^[\d*/,\-]+$', parts[0])) or \
               (parts and parts[0].startswith("@")):
                job_count += 1
                if job_count == idx:
                    line_idx = i
                    break
            comment_idx = None

    if line_idx is not None:
        # Remove the comment line before this job if it exists
        remove_indices = [line_idx]
        if comment_idx is not None and comment_idx < line_idx:
            remove_indices.append(comment_idx)
        for i in sorted(remove_indices, reverse=True):
            lines.pop(i)
        set_crontab(lines)
        print("Removed.")
    else:
        print("Error: Could not locate job line.", file=sys.stderr)
        sys.exit(1)


def cmd_edit(args):
    """Edit cron jobs (opens crontab -e)."""
    try:
        subprocess.run(["crontab", "-e"])
    except FileNotFoundError:
        print("Error: crontab command not found", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Simplify crontab management. List, add, remove, edit cron jobs."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all cron jobs")

    # add
    p_add = sub.add_parser("add", help="Add a new cron job")
    p_add.add_argument("schedule", help="Cron expression or human-readable schedule")
    p_add.add_argument("command", nargs="?", help="Command to run")
    p_add.add_argument("--label", "-l", help="Label/comment for this job")

    # remove
    p_remove = sub.add_parser("remove", help="Remove a cron job by index")
    p_remove.add_argument("index", type=int, help="Job index (from 'list' output)")
    p_remove.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # edit
    p_edit = sub.add_parser("edit", help="Open crontab in editor")

    # resolve
    p_resolve = sub.add_parser("resolve", help="Resolve a human-readable schedule to cron expression")
    p_resolve.add_argument("schedule", help="Human-readable schedule (e.g., 'every day at 2am')")

    # describe
    p_describe = sub.add_parser("describe", help="Describe a cron expression")
    p_describe.add_argument("cron_expr", help="Cron expression to describe")

    args = parser.parse_args()

    try:
        if args.command == "list":
            cmd_list(args)
        elif args.command == "add":
            cmd_add(args)
        elif args.command == "remove":
            cmd_remove(args)
        elif args.command == "edit":
            cmd_edit(args)
        elif args.command == "resolve":
            resolved = parse_human_schedule(args.schedule)
            if resolved != args.schedule:
                print(f"{args.schedule} => {resolved}")
            else:
                desc = describe_cron(args.schedule)
                if desc != args.schedule:
                    print(f"{args.schedule} => {desc}")
                else:
                    print(resolved)
        elif args.command == "describe":
            print(describe_cron(args.cron_expr))
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "crontab-helper",
    "func": "main",
    "desc": 'Simplify crontab management',
}

if __name__ == "__main__":
    main()
