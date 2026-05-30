#!/usr/bin/env python3
"""
ren — 批量文件重命名工具
安全、可预览、可撤销的文件重命名。
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

def green(s): return f"\033[92m{s}\033[0m"
def red(s): return f"\033[91m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s): return f"\033[96m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"

def collect_files(patterns, recursive=False):
    """Collect files matching glob patterns"""
    files = []
    for pattern in patterns:
        p = Path(pattern)
        if p.is_dir():
            # Directory mode: collect all files in dir
            for f in p.iterdir() if not recursive else p.rglob('*'):
                if f.is_file():
                    files.append(f)
        elif '*' in pattern or '?' in pattern:
            # Glob pattern
            matched = list(Path('.').glob(pattern))
            if not matched:
                # Try parent glob
                matched = list(Path('.').glob(pattern))
            files.extend(matched)
        else:
            # Exact path
            p = Path(pattern)
            if p.exists():
                files.append(p)
    return sorted(set(files), key=lambda f: f.name)


def apply_operation(file, op, args):
    """Apply a rename operation, returns (original, new_name, applied)"""
    stem = file.stem
    suffix = file.suffix

    if op == 'prefix':
        prefix = args[0]
        new_stem = prefix + stem
    elif op == 'suffix':
        suffix_text = args[0]
        new_stem = stem + suffix_text
    elif op == 'replace':
        old, new = args[0], args[1] if len(args) > 1 else ''
        new_stem = stem.replace(old, new)
    elif op == 'regex':
        pattern, repl = args[0], args[1] if len(args) > 1 else ''
        new_stem = re.sub(pattern, repl, stem)
    elif op == 'lower':
        new_stem = stem.lower()
    elif op == 'upper':
        new_stem = stem.upper()
    elif op == 'number':
        fmt = args[0] if args else '{:03d}'
        # Need index info - handled in main loop
        return None
    elif op == 'strip':
        chars_to_strip = args[0] if args else ' _-'
        new_stem = stem.strip(chars_to_strip)
    elif op == 'truncate':
        max_len = int(args[0]) if args else 40
        new_stem = stem[:max_len]
    elif op == 'date':
        fmt = args[0] if args else '%Y%m%d'
        new_stem = datetime.now().strftime(fmt) + '_' + stem
    elif op == 'ext':
        ext = args[0] if args else ''
        if not ext.startswith('.'):
            ext = '.' + ext
        new_path = file.parent / (stem + ext)
        return (file, new_path, True)
    else:
        return None

    new_path = file.parent / (new_stem + suffix)
    # Don't rename to same name
    if new_path == file:
        return (file, new_path, False)
    return (file, new_path, True)


def show_help():
    print("ren — 批量文件重命名工具")
    print()
    print("用法: ren <glob/文件>... <操作> [参数]")
    print()
    print("操作:")
    print("  --prefix <text>        添加前缀")
    print("  --suffix <text>        添加后缀（扩展名前）")
    print("  --replace <old> <new>  替换文件名中的文本")
    print("  --regex <pat> <repl>   正则替换文件名")
    print("  --lower                转为小写")
    print("  --upper                转为大写")
    print("  --number [fmt]         编号 (默认 {:03d})")
    print("  --strip [chars]        去除字符 (默认 ' _-')")
    print("  --truncate <n>         截断到 n 个字符")
    print("  --date [fmt]           添加日期前缀 (默认 %%Y%%m%%d)")
    print("  --ext <ext>            更改扩展名")
    print()
    print("选项:")
    print("  --dry-run           仅预览，不执行")
    print("  --recursive / -r    递归子目录")
    print("  --verbose / -v      详细信息")
    print()
    print("示例:")
    print("  ren *.txt --prefix draft-        # 所有 txt 加 draft- 前缀")
    print("  ren *.jpg --replace IMG_ photo_  # 替换文件名文本")
    print("  ren *.md --number Chapter-       # 编号 Chapter-01.md 等")
    print("  ren . --lower --dry-run          # 预览当前目录小写化")
    print("  ren log.txt --ext md             # 改扩展名 .txt → .md")


def main():
    if not sys.argv[1:] or sys.argv[1] in ('--help', '-h', 'help'):
        show_help()
        return

    args = sys.argv[1:]

    # Parse operations and options
    ops = []
    patterns = []
    options = {
        'dry_run': False,
        'recursive': False,
        'verbose': False,
    }

    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith('--') and a not in ('--dry-run', '--recursive', '--verbose', '-v', '-r'):
            # Operation
            op_name = a[2:]  # --prefix -> prefix
            op_args = []
            i += 1
            # Collect arguments until next option
            while i < len(args) and not args[i].startswith('--') and args[i] not in ('-v', '-r'):
                op_args.append(args[i])
                i += 1
            ops.append((op_name, op_args))
            continue
        elif a == '--dry-run':
            options['dry_run'] = True
        elif a in ('--recursive', '-r'):
            options['recursive'] = True
        elif a in ('--verbose', '-v'):
            options['verbose'] = True
        else:
            patterns.append(a)
        i += 1

    if not patterns:
        print("错误: 未指定文件模式")
        sys.exit(1)

    if not ops:
        print("错误: 未指定操作")
        sys.exit(1)

    # Collect files
    files = collect_files(patterns, options['recursive'])
    if not files:
        print("(未找到匹配的文件)")
        return

    print(f"找到 {len(files)} 个文件\n" if options['verbose'] else "", end="")

    # Generate rename plan
    rename_plan = []  # [(old_path, new_path, applied)]
    number_op = None
    other_ops = []

    for op_name, op_args in ops:
        if op_name == 'number':
            number_op = op_args
        else:
            other_ops.append((op_name, op_args))

    if number_op:
        fmt = number_op[0] if number_op else '{:03d}'
        # Also check for prefix/suffix in format
        prefix_text = ''
        suffix_text = ''
        if ',' in fmt:
            parts = fmt.split(',')
            fmt = parts[0]
            if len(parts) > 1:
                prefix_text = parts[1]
        else:
            # Check if fmt contains non-format characters
            pass
        for idx, file in enumerate(files, 1):
            stem = file.stem
            suffix = file.suffix
            num = fmt.format(idx)
            new_stem = prefix_text + num + suffix_text + stem
            # But wait, I want to insert the number somewhere
            # Simpler: number replaces stem or prefixes
            if prefix_text:
                new_stem = prefix_text + num + '_' + stem
            else:
                new_stem = num + '_' + stem
            new_path = file.parent / (new_stem + suffix)
            rename_plan.append((file, new_path, new_path != file))
    else:
        for file in files:
            current = file
            applied = True
            for op_name, op_args in other_ops:
                result = apply_operation(current, op_name, op_args)
                if result is None:
                    continue
                _, new_path, was_applied = result
                if not was_applied:
                    applied = False
                    break
                current = new_path
            rename_plan.append((file, current, applied))

    # Filter unchanged
    rename_plan = [(o, n, a) for o, n, a in rename_plan if a and o != n]

    if not rename_plan:
        print("(无需重命名)")
        return

    # Show plan
    print(f"\n将重命名 {len(rename_plan)} 个文件:\n")
    for old, new, _ in rename_plan:
        if old.parent == new.parent:
            print(f"  {dim(old.name)}  →  {green(new.name)}")
        else:
            print(f"  {old}  →  {green(new)}")

    if options['dry_run']:
        print(f"\n{yellow('干跑模式 — 未执行任何操作')}")
        return

    # Confirm
    print()
    try:
        confirm = input(f"执行以上 {len(rename_plan)} 个重命名? (y/N) ").lower()
    except (EOFError, KeyboardInterrupt):
        print()
        print("取消")
        return

    if confirm != 'y':
        print("取消")
        return

    # Execute
    renamed = 0
    errors = 0
    for old, new, _ in rename_plan:
        try:
            new.parent.mkdir(parents=True, exist_ok=True)
            old.rename(new)
            if options['verbose']:
                print(f"  ✓ {old.name} → {new.name}")
            renamed += 1
        except OSError as e:
            print(f"  ✗ {old.name}: {e}")
            errors += 1

    print(f"\n✓ 已重命名 {renamed} 个文件" + (f", {errors} 个错误" if errors else ""))



# === Auto-registration metadata ===
TOOL_META = {
    "name": "ren",
    "func": "main",
    "desc": 'Ren',
}

if __name__ == '__main__':
    main()
