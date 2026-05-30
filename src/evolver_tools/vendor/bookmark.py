#!/usr/bin/env python3
"""bookmark — Terminal bookmark manager. Add, list, search, remove, open bookmarks with tags."""

import sys
import os
import json
import argparse
import subprocess
import platform


BOOKMARK_FILE = os.path.expanduser('~/.config/evolver-bookmarks.json')


def load_bookmarks():
    """Load bookmarks from JSON file."""
    if not os.path.exists(BOOKMARK_FILE):
        return {'bookmarks': [], 'counter': 1}
    try:
        with open(BOOKMARK_FILE, 'r') as f:
            data = json.load(f)
            if 'bookmarks' not in data:
                data['bookmarks'] = []
            if 'counter' not in data:
                data['counter'] = max((b.get('id', 0) for b in data['bookmarks']), default=0) + 1
            return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading bookmarks: {e}", file=sys.stderr)
        return {'bookmarks': [], 'counter': 1}


def save_bookmarks(data):
    """Save bookmarks to JSON file."""
    os.makedirs(os.path.dirname(BOOKMARK_FILE), exist_ok=True)
    try:
        with open(BOOKMARK_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        print(f"Error saving bookmarks: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    """Add a new bookmark."""
    data = load_bookmarks()
    bm = {
        'id': data['counter'],
        'name': args.name,
        'url': args.url,
        'tags': args.tags.split(',') if args.tags else [],
        'description': args.description or '',
    }
    data['bookmarks'].append(bm)
    data['counter'] += 1
    save_bookmarks(data)
    print(f"Bookmarked \033[1m{args.name}\033[0m → \033[94m{args.url}\033[0m (id: {bm['id']})")


def cmd_list(args):
    """List all bookmarks."""
    data = load_bookmarks()
    bms = data['bookmarks']

    if args.tag:
        bms = [b for b in bms if args.tag in b.get('tags', [])]

    if not bms:
        print("No bookmarks found.")
        return

    if args.json:
        print(json.dumps(bms, indent=2))
        return

    for bm in bms:
        bid = bm['id']
        name = bm['name']
        url = bm['url']
        tags = bm.get('tags', [])
        desc = bm.get('description', '')
        tag_str = f" \033[90m[{','.join(tags)}]\033[0m" if tags else ""
        desc_str = f" \033[90m– {desc}\033[0m" if desc else ""
        print(f"  \033[33m{bid:>3}\033[0m. \033[1m{name}\033[0m \033[94m{url}\033[0m{tag_str}{desc_str}")


def cmd_search(args):
    """Search bookmarks by query string."""
    data = load_bookmarks()
    query = args.query.lower()
    results = []
    for bm in data['bookmarks']:
        if query in bm['name'].lower() or query in bm['url'].lower():
            results.append(bm)
            continue
        for tag in bm.get('tags', []):
            if query in tag.lower():
                results.append(bm)
                break
        if query in bm.get('description', '').lower():
            if bm not in results:
                results.append(bm)

    if not results:
        print(f"No bookmarks matching '{args.query}'.")
        return

    for bm in results:
        bid = bm['id']
        name = bm['name']
        url = bm['url']
        tags = bm.get('tags', [])
        tag_str = f" \033[90m[{','.join(tags)}]\033[0m" if tags else ""
        print(f"  \033[33m{bid:>3}\033[0m. \033[1m{name}\033[0m \033[94m{url}\033[0m{tag_str}")


def cmd_remove(args):
    """Remove a bookmark by id."""
    data = load_bookmarks()
    target_id = args.id
    new_bms = [b for b in data['bookmarks'] if b['id'] != target_id]
    if len(new_bms) == len(data['bookmarks']):
        print(f"No bookmark with id {target_id}.", file=sys.stderr)
        sys.exit(1)
    data['bookmarks'] = new_bms
    save_bookmarks(data)
    print(f"Removed bookmark #{target_id}.")


def cmd_open(args):
    """Open a bookmark in the default browser."""
    data = load_bookmarks()
    target_id = args.id
    found = None
    for bm in data['bookmarks']:
        if bm['id'] == target_id:
            found = bm
            break
    if not found:
        print(f"No bookmark with id {target_id}.", file=sys.stderr)
        sys.exit(1)

    url = found['url']
    try:
        system = platform.system()
        if system == 'Darwin':
            subprocess.run(['open', url], check=True)
        elif system == 'Linux':
            subprocess.run(['xdg-open', url], check=True)
        elif system == 'Windows':
            subprocess.run(['cmd', '/c', 'start', url], check=True)
        else:
            print(f"Unsupported platform: {system}", file=sys.stderr)
            sys.exit(1)
        print(f"Opened \033[94m{url}\033[0m in browser.")
    except subprocess.CalledProcessError as e:
        print(f"Error opening URL: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("No browser opener found (xdg-open/open).", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Export bookmarks to JSON or text."""
    data = load_bookmarks()
    if args.format == 'json':
        print(json.dumps(data['bookmarks'], indent=2))
    else:
        for bm in data['bookmarks']:
            print(f"{bm['name']}\t{bm['url']}")


def cmd_import_cmd(args):
    """Import bookmarks from a file."""
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    data = load_bookmarks()
    imported = 0
    try:
        with open(args.file, 'r') as f:
            content = f.read().strip()
            if content.startswith('['):
                items = json.loads(content)
                for item in items:
                    if isinstance(item, dict) and 'url' in item:
                        bm = {
                            'id': data['counter'],
                            'name': item.get('name', item['url']),
                            'url': item['url'],
                            'tags': item.get('tags', []),
                            'description': item.get('description', ''),
                        }
                        data['bookmarks'].append(bm)
                        data['counter'] += 1
                        imported += 1
            else:
                for line in content.split('\n'):
                    line = line.strip()
                    if '\t' in line:
                        name, url = line.split('\t', 1)
                    elif ' ' in line:
                        parts = line.split(' ', 1)
                        name, url = parts[0], parts[1]
                    else:
                        continue
                    bm = {'id': data['counter'], 'name': name, 'url': url, 'tags': [], 'description': ''}
                    data['bookmarks'].append(bm)
                    data['counter'] += 1
                    imported += 1
    except Exception as e:
        print(f"Error importing: {e}", file=sys.stderr)
        sys.exit(1)
    save_bookmarks(data)
    print(f"Imported {imported} bookmark(s).")


def main():
    parser = argparse.ArgumentParser(
        description='Terminal bookmark manager.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command', help='Subcommand')

    p_add = sub.add_parser('add', help='Add a new bookmark')
    p_add.add_argument('name', help='Bookmark name')
    p_add.add_argument('url', help='Bookmark URL')
    p_add.add_argument('--tags', '-t', help='Comma-separated tags')
    p_add.add_argument('--description', '-d', help='Bookmark description')

    p_list = sub.add_parser('list', help='List all bookmarks')
    p_list.add_argument('--tag', '-t', help='Filter by tag')
    p_list.add_argument('--json', '-j', action='store_true', help='JSON output')

    p_search = sub.add_parser('search', help='Search bookmarks')
    p_search.add_argument('query', help='Search query')

    p_rm = sub.add_parser('remove', help='Remove a bookmark by ID')
    p_rm.add_argument('id', type=int, help='Bookmark ID to remove')

    p_open = sub.add_parser('open', help='Open a bookmark in browser')
    p_open.add_argument('id', type=int, help='Bookmark ID to open')

    p_export = sub.add_parser('export', help='Export bookmarks')
    p_export.add_argument('--format', choices=['json', 'text'], default='text')

    p_import = sub.add_parser('import', help='Import bookmarks from file')
    p_import.add_argument('file', help='File to import from')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        commands = {
            'add': cmd_add,
            'list': cmd_list,
            'search': cmd_search,
            'remove': cmd_remove,
            'open': cmd_open,
            'export': cmd_export,
            'import': cmd_import_cmd,
        }
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
