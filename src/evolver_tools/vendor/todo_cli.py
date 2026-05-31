#!/usr/bin/env python3
"""todo-cli — Simple prioritized TODO list manager.

Usage: todo-cli add "Buy groceries" [--priority=high]
       todo-cli list [--all|--done|--pending]
       todo-cli done <id>
       todo-cli rm <id>
       todo-cli clear

Data stored as JSON in ~/.config/evolver/todos.json.
Zero-dependency (stdlib only).
"""

import sys, os, json, time
from datetime import datetime

TODO_DIR = os.path.expanduser("~/.config/evolver")
TODO_FILE = os.path.join(TODO_DIR, "todos.json")

def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE) as f:
        return json.load(f)

def save_todos(todos):
    os.makedirs(TODO_DIR, exist_ok=True)
    with open(TODO_FILE, 'w') as f:
        json.dump(todos, f, indent=2)

def show_help():
    print(__doc__)

def cmd_add(args):
    priority = "medium"
    text_parts = []
    for a in args:
        if a.startswith('--priority='):
            priority = a.split('=', 1)[1]
        elif not a.startswith('-'):
            text_parts.append(a)
    
    if not text_parts:
        print("Error: todo text required")
        return

    todos = load_todos()
    todo = {
        "id": (max([t["id"] for t in todos], default=0) + 1),
        "text": ' '.join(text_parts),
        "priority": priority,
        "done": False,
        "created": datetime.now().isoformat(),
    }
    todos.append(todo)
    save_todos(todos)
    print(f"  Added: [{todo['id']}] {todo['text']} ({priority})")

def cmd_list(args):
    show_all = '--all' in args
    show_done = '--done' in args
    show_pending = '--pending' in args or (not show_all and not show_done)
    show_raw = '--raw' in args
    priority_filter = None
    
    for a in args:
        if a.startswith('--priority='):
            priority_filter = a.split('=', 1)[1]

    todos = load_todos()
    if not todos:
        print("  No todos. Use: todo-cli add <text>")
        return

    filtered = []
    for t in todos:
        if t.get('done') and not show_all and not show_done:
            continue
        if not t.get('done') and show_done:
            continue
        if priority_filter and t.get('priority') != priority_filter:
            continue
        filtered.append(t)

    if not filtered:
        print("  No todos match the filter.")
        return

    print(f"  {'ID':<4} {'Status':<8} {'Priority':<10} {'Text'}")
    print(f"  {'-'*4} {'-'*8} {'-'*10} {'-'*30}")
    for t in filtered:
        status = "✓ DONE" if t.get('done') else "○ PEND"
        pfx = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        pri = f"{pfx.get(t.get('priority','medium'),'')} {t.get('priority','medium')}"
        print(f"  {t['id']:<4} {status:<8} {pri:<10} {t['text']}")

def cmd_done(args):
    if not args:
        print("Usage: todo-cli done <id>")
        return
    try:
        todo_id = int(args[0])
    except ValueError:
        print("Error: id must be a number")
        return

    todos = load_todos()
    for t in todos:
        if t['id'] == todo_id:
            t['done'] = True
            t['completed'] = datetime.now().isoformat()
            save_todos(todos)
            print(f"  Marked done: [{todo_id}] {t['text']}")
            return
    print(f"  Todo #{todo_id} not found")

def cmd_rm(args):
    if not args:
        print("Usage: todo-cli rm <id>")
        return
    try:
        todo_id = int(args[0])
    except ValueError:
        print("Error: id must be a number")
        return
    
    todos = load_todos()
    for i, t in enumerate(todos):
        if t['id'] == todo_id:
            removed = todos.pop(i)
            save_todos(todos)
            print(f"  Removed: [{removed['id']}] {removed['text']}")
            return
    print(f"  Todo #{todo_id} not found")

def cmd_clear(args):
    todos = load_todos()
    done_todos = [t for t in todos if t.get('done')]
    if not done_todos:
        print("  No done todos to clear.")
        return
    todos = [t for t in todos if not t.get('done')]
    save_todos(todos)
    print(f"  Cleared {len(done_todos)} completed todos.")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        show_help()
        return

    cmd = args[0]
    cmd_args = args[1:]

    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'done': cmd_done,
        'rm': cmd_rm,
        'clear': cmd_clear,
    }

    if cmd in commands:
        commands[cmd](cmd_args)
    else:
        print(f"Unknown command: {cmd}")
        print("Available: add, list, done, rm, clear")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "todo-cli",
    "func": "main",
    "desc": 'Simple prioritized TODO list manager',
}

if __name__ == '__main__':
    main()
