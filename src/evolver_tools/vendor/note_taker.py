#!/usr/bin/env python3
"""note-taker — Take quick notes from the terminal.

Usage: note-taker add "My note text" [--tag=work]
       note-taker list [--tag=work]
       note-taker search <keyword>
       note-taker recent [--count=10]

Simple CLI note-taking tool. Notes stored as JSON.
Zero-dependency (stdlib only).
"""

import sys, os, json, datetime

NOTES_DIR = os.path.expanduser("~/.config/evolver")
NOTES_FILE = os.path.join(NOTES_DIR, "notes.json")

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        return json.load(f)

def save_notes(notes):
    os.makedirs(NOTES_DIR, exist_ok=True)
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)

def cmd_add(args):
    tag = None
    text_parts = []
    for a in args:
        if a.startswith('--tag='):
            tag = a.split('=', 1)[1]
        elif not a.startswith('-'):
            text_parts.append(a)
    if not text_parts:
        print("Error: note text required")
        return
    notes = load_notes()
    note = {
        "id": len(notes) + 1,
        "text": ' '.join(text_parts),
        "tag": tag or 'general',
        "created": datetime.datetime.now().isoformat(),
    }
    notes.append(note)
    save_notes(notes)
    print(f"  Note saved: [{note['id']}] {note['text'][:50]}")

def cmd_list(args):
    tag_filter = None
    for a in args:
        if a.startswith('--tag='):
            tag_filter = a.split('=', 1)[1]
    notes = load_notes()
    if tag_filter:
        notes = [n for n in notes if n.get('tag') == tag_filter]
    if not notes:
        print("  No notes found.")
        return
    for n in reversed(notes[-50:]):  # Last 50
        created = n.get('created', '')[:16].replace('T', ' ')
        tag = n.get('tag', '')
        print(f"  [{n['id']:>4}] {created} [{tag}] {n['text']}")

def cmd_search(args):
    if not args:
        print("Usage: note-taker search <keyword>")
        return
    keyword = ' '.join(args).lower()
    notes = load_notes()
    matches = [n for n in notes if keyword in n['text'].lower()]
    if not matches:
        print(f"  No notes matching: {keyword}")
        return
    for n in reversed(matches[-20:]):
        created = n.get('created', '')[:16].replace('T', ' ')
        tag = n.get('tag', '')
        # Highlight keyword
        text = n['text']
        print(f"  [{n['id']:>4}] {created} [{tag}] {text}")

def cmd_recent(args):
    count = 10
    for a in args:
        if a.startswith('--count='):
            count = int(a.split('=', 1)[1])
    notes = load_notes()
    if not notes:
        print("  No notes yet.")
        return
    for n in reversed(notes[-count:]):
        created = n.get('created', '')[:16].replace('T', ' ')
        tag = n.get('tag', '')
        text = n['text'][:60] + ('...' if len(n['text']) > 60 else '')
        print(f"  [{n['id']:>4}] {created} [{tag}] {text}")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return
    cmd = args[0]
    cmd_args = args[1:]
    cmds = {
        'add': cmd_add, 'list': cmd_list,
        'search': cmd_search, 'recent': cmd_recent,
    }
    if cmd in cmds:
        cmds[cmd](cmd_args)
    else:
        print(f"Unknown: {cmd}. Commands: add, list, search, recent")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "note-taker",
    "func": "main",
    "desc": 'CLI note-taking (add, list, search)',
}

if __name__ == '__main__':
    main()
