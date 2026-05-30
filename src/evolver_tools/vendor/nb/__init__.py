#!/usr/bin/env python3
"""
nb — 命令行笔记簿
终端下的轻量笔记管理工具。
"""

import json
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime

NOTES_DIR = Path.home() / '.nb'
NOTES_FILE = NOTES_DIR / 'notes.json'
NOTES_EXPORT = NOTES_DIR / 'export'

def ensure_db():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        with open(NOTES_FILE, 'w') as f:
            json.dump([], f)

def load_notes():
    ensure_db()
    try:
        with open(NOTES_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_notes(notes):
    ensure_db()
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def next_id(notes):
    if not notes:
        return 1
    return max(n['id'] for n in notes) + 1

def timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def cmd_new(args):
    """nb new <title> — 创建新笔记（从 stdin 读取内容或交互输入）"""
    title = ' '.join(args) if args else '未命名笔记'

    print(f"📝 标题: {title}")
    print("输入内容（空行 + Ctrl+D 结束）:")
    lines = []
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.rstrip('\n')
            if line == '' and lines and lines[-1] == '':
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass

    content = '\n'.join(lines).strip()
    if not content:
        print("✗ 笔记内容为空，取消")
        return

    notes = load_notes()
    note = {
        'id': next_id(notes),
        'title': title,
        'content': content,
        'created': timestamp(),
        'updated': timestamp(),
    }
    notes.insert(0, note)  # newest first
    save_notes(notes)
    print(f"✓ 笔记 #{note['id']} 已保存: {title}")


def cmd_list(args):
    """nb list [--all] — 列出笔记"""
    notes = load_notes()
    if not notes:
        print("(没有笔记)")
        return

    show_all = '--all' in args
    display = notes if show_all else notes[:20]

    for n in display:
        created = n.get('created', '?')
        title = n['title']
        preview = n['content'][:60].replace('\n', ' ')
        if len(preview) < len(n['content']):
            preview += '...'
        print(f"  [{n['id']:>3}] {created}  {title}")
        print(f"       {preview}")
        print()

    if not show_all and len(notes) > 20:
        print(f"... 还有 {len(notes) - 20} 条 (使用 --all 查看全部)")


def cmd_show(args):
    """nb show <id> — 显示笔记详情"""
    if not args:
        print("用法: nb show <id>")
        return
    try:
        nid = int(args[0])
    except ValueError:
        print("无效的 ID")
        return

    notes = load_notes()
    for n in notes:
        if n['id'] == nid:
            print(f"╔══════════════════════════════════════╗")
            print(f"║ #{n['id']}  {n['title']}")
            print(f"║  创建: {n.get('created', '?')}")
            print(f"║  更新: {n.get('updated', '?')}")
            print(f"╚══════════════════════════════════════╝")
            print()
            print(n['content'])
            return
    print(f"✗ 未找到笔记 #{nid}")


def cmd_search(args):
    """nb search <query> — 搜索笔记"""
    if not args:
        print("用法: nb search <query>")
        return
    query = ' '.join(args).lower()

    notes = load_notes()
    results = []
    for n in notes:
        if query in n['title'].lower() or query in n['content'].lower():
            results.append(n)

    if not results:
        print(f"(未找到匹配 '{query}' 的笔记)")
        return

    print(f"找到 {len(results)} 条匹配 '{query}':\n")
    for n in results:
        # Highlight matches
        title = n['title']
        preview = n['content'][:80].replace('\n', ' ')
        print(f"  [{n['id']:>3}] {n.get('created', '?')}  {title}")
        print(f"       {preview}")
        print()


def cmd_delete(args):
    """nb delete <id> — 删除笔记"""
    if not args:
        print("用法: nb delete <id>")
        return
    try:
        nid = int(args[0])
    except ValueError:
        print("无效的 ID")
        return

    notes = load_notes()
    for i, n in enumerate(notes):
        if n['id'] == nid:
            confirm = input(f"删除笔记 #{nid} 「{n['title']}」? (y/N) ").lower()
            if confirm == 'y':
                notes.pop(i)
                save_notes(notes)
                print(f"✓ 笔记 #{nid} 已删除")
            else:
                print("取消")
            return
    print(f"✗ 未找到笔记 #{nid}")


def cmd_edit(args):
    """nb edit <id> — 编辑笔记内容（替换内容）"""
    if not args:
        print("用法: nb edit <id>")
        return
    try:
        nid = int(args[0])
    except ValueError:
        print("无效的 ID")
        return

    notes = load_notes()
    for n in notes:
        if n['id'] == nid:
            print(f"编辑笔记 #{nid} 「{n['title']}」")
            print("当前内容:")
            print(n['content'])
            print("\n--- 输入新内容（空行 + Ctrl+D 结束）---")
            lines = []
            try:
                while True:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    line = line.rstrip('\n')
                    if line == '' and lines and lines[-1] == '':
                        break
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                pass
            content = '\n'.join(lines).strip()
            if content:
                n['content'] = content
                n['updated'] = timestamp()
                save_notes(notes)
                print(f"✓ 笔记 #{nid} 已更新")
            else:
                print("内容为空，未修改")
            return
    print(f"✗ 未找到笔记 #{nid}")


def cmd_export(args):
    """nb export — 导出所有笔记为 Markdown 文件"""
    notes = load_notes()
    if not notes:
        print("(没有笔记可导出)")
        return

    export_dir = NOTES_EXPORT
    export_dir.mkdir(parents=True, exist_ok=True)

    # Also clear old exports
    for f in export_dir.glob('*.md'):
        f.unlink()

    for n in notes:
        safe_title = re.sub(r'[^\w\s-]', '', n['title']).strip()[:40]
        safe_title = re.sub(r'[-\s]+', '-', safe_title).lower()
        if not safe_title:
            safe_title = f'note-{n["id"]}'
        filename = f"{n['id']:03d}-{safe_title}.md"

        md = f"# {n['title']}\n\n"
        md += f"- **ID**: #{n['id']}\n"
        md += f"- **创建**: {n.get('created', '?')}\n"
        md += f"- **更新**: {n.get('updated', '?')}\n\n"
        md += "---\n\n"
        md += n['content'] + '\n'

        with open(export_dir / filename, 'w') as f:
            f.write(md)

    print(f"✓ 已导出 {len(notes)} 条笔记到 {export_dir}")


def cmd_count(args):
    """nb count — 统计笔记数量"""
    notes = load_notes()
    total = len(notes)
    total_chars = sum(len(n['content']) for n in notes)
    print(f"📊 笔记数: {total}")
    print(f"📊 总字数: {total_chars}")


def show_help():
    print("nb — 命令行笔记簿")
    print()
    print("用法:")
    print("  nb new <title>          创建新笔记")
    print("  nb list [--all]         列出笔记")
    print("  nb show <id>            查看笔记")
    print("  nb search <query>       搜索笔记")
    print("  nb edit <id>            编辑笔记")
    print("  nb delete <id>          删除笔记")
    print("  nb export               导出 Markdown")
    print("  nb count                统计信息")
    print("  nb help                 显示帮助")
    print()
    print("创建笔记时，输入内容后 Ctrl+D 结束。")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('help', '--help', '-h'):
        show_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'new': cmd_new,
        'list': cmd_list,
        'ls': cmd_list,
        'show': cmd_show,
        'get': cmd_show,
        'search': cmd_search,
        'find': cmd_search,
        'edit': cmd_edit,
        'delete': cmd_delete,
        'rm': cmd_delete,
        'export': cmd_export,
        'count': cmd_count,
        'stats': cmd_count,
    }

    if cmd in commands:
        ensure_db()
        commands[cmd](args)
    else:
        print(f"未知命令: {cmd}")
        print("使用 'nb help' 查看帮助")



# === Auto-registration metadata ===
TOOL_META = {
    "name": "nb",
    "func": "main",
    "desc": 'nb',
}

if __name__ == '__main__':
    main()
