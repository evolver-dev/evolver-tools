#!/usr/bin/env python3
"""timer-pro — Advanced timer with laps, alarms, and countdown

Usage:
    timer-pro 5m                    # Countdown 5 minutes
    timer-pro 1h30m                 # Countdown 1h 30m
    timer-pro 90s                   # Countdown 90 seconds
    timer-pro --stopwatch           # Stopwatch mode (start counting up)
    timer-pro --lap                 # Stopwatch with lap support
    timer-pro --alarm 07:00         # Set alarm for 7:00 AM
    timer-pro --alarm 19:30         # Set alarm for 7:30 PM
    timer-pro list                  # List active alarms
"""
import sys
import time
import re
import json
import os
import threading
from datetime import datetime, timedelta


ALARM_FILE = os.path.expanduser('~/.evolver_alarms.json')


def parse_duration(text):
    """Parse duration string like 5m, 1h30m, 90s into total seconds."""
    total = 0
    # Match hours, minutes, seconds
    h = re.search(r'(\d+)\s*h', text)
    m = re.search(r'(\d+)\s*m(?!\w)', text)
    s = re.search(r'(\d+)\s*s', text)

    if h:
        total += int(h.group(1)) * 3600
    if m:
        total += int(m.group(1)) * 60
    if s:
        total += int(s.group(1))

    if total == 0:
        # Try bare number as seconds
        try:
            total = int(text)
        except ValueError:
            pass
    return total


def parse_time(text):
    """Parse time string like 07:00 or 7:00 PM into datetime."""
    text = text.strip().upper()
    now = datetime.now()
    try:
        if 'PM' in text or 'AM' in text:
            t = datetime.strptime(text, '%I:%M %p')
        else:
            t = datetime.strptime(text, '%H:%M')
        target = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target
    except ValueError:
        print(f"Error: invalid time format '{text}' (use HH:MM)", file=sys.stderr)
        sys.exit(1)


def format_duration(seconds):
    """Format seconds to human-readable duration."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"


def countdown_mode(duration):
    """Run countdown timer."""
    try:
        start = time.time()
        end = start + duration
        while time.time() < end:
            remaining = int(end - time.time())
            sys.stdout.write(f"\r⏱  {format_duration(remaining)}  ")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r⏰ Time\'s up!              \n')
        # Bell
        sys.stdout.write('\a')
    except KeyboardInterrupt:
        elapsed = int(time.time() - start)
        sys.stdout.write(f'\n⏹  Stopped after {format_duration(elapsed)}\n')


def stopwatch_mode(lap_mode=False):
    """Run stopwatch, optionally with lap support."""
    print("⏱  Stopwatch started. Press Ctrl+C to stop.")
    if lap_mode:
        print("   Press Enter to record a lap.")
    start = time.time()
    lap_num = 1
    lap_start = start

    try:
        while True:
            elapsed = time.time() - start
            sys.stdout.write(f"\r  {format_duration(int(elapsed))}  ")
            sys.stdout.flush()
            time.sleep(0.1)
    except KeyboardInterrupt:
        if lap_mode:
            pass
        total = int(time.time() - start)
        sys.stdout.write(f'\n⏹  Total: {format_duration(total)}\n')


def save_alarm(alarm_time):
    """Save alarm to persistent file."""
    alarms = []
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE) as f:
                alarms = json.load(f)
        except (json.JSONDecodeError, IOError):
            alarms = []
    alarms.append(alarm_time.isoformat())
    with open(ALARM_FILE, 'w') as f:
        json.dump(alarms, f)
    return len(alarms)


def load_alarms():
    """Load alarms from persistent file."""
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def alarm_worker():
    """Background thread that checks alarms."""
    while True:
        now = datetime.now()
        alarms = load_alarms()
        active_alarms = []
        for alarm_str in alarms:
            try:
                alarm_time = datetime.fromisoformat(alarm_str)
                if alarm_time <= now:
                    print(f'\n⏰ ALARM! {alarm_time.strftime("%H:%M")}')
                    sys.stdout.write('\a')
                else:
                    active_alarms.append(alarm_str)
            except ValueError:
                continue
        # Save back without fired alarms
        if len(active_alarms) != len(alarms):
            with open(ALARM_FILE, 'w') as f:
                json.dump(active_alarms, f)
        time.sleep(30)


def alarm_mode(time_str):
    """Set alarm."""
    target = parse_time(time_str)
    save_alarm(target)
    print(f"⏰ Alarm set for {target.strftime('%H:%M')} ({format_duration(int((target - datetime.now()).total_seconds()))} from now)")


def list_alarms():
    """List active alarms."""
    alarms = load_alarms()
    if not alarms:
        print("No active alarms.")
        return
    now = datetime.now()
    print(f"Active alarms ({len(alarms)}):")
    for alarm_str in sorted(alarms):
        try:
            alarm_time = datetime.fromisoformat(alarm_str)
            remaining = int((alarm_time - now).total_seconds())
            if remaining > 0:
                print(f"  {alarm_time.strftime('%H:%M')} (in {format_duration(remaining)})")
            else:
                print(f"  {alarm_time.strftime('%H:%M')} (past)")
        except ValueError:
            pass


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    if args[0] == 'list':
        list_alarms()
        return

    if args[0] == '--alarm':
        if len(args) < 2:
            print("Error: time required for --alarm", file=sys.stderr)
            sys.exit(1)
        alarm_mode(args[1])
        return

    if args[0] == '--stopwatch':
        stopwatch_mode(lap_mode='--lap' in args)
        return

    if args[0] == '--lap':
        stopwatch_mode(lap_mode=True)
        return

    # Default: countdown mode
    duration = parse_duration(args[0])
    if duration <= 0:
        print(f"Error: could not parse duration '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    countdown_mode(duration)


if __name__ == '__main__':
    main()
