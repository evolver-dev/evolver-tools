#!/usr/bin/env python3
"""treedir — 目录树可视化工具。零外部依赖（替代 tree 命令）。"""
import os
import sys

PIPE = "│   "
BRANCH = "├── "
LAST = "└── "

def build_tree(root_path, max_depth=3, show_hidden=False, dirs_only=False):
    """递归构建目录树"""
    root_path = os.path.abspath(root_path)
    if not os.path.isdir(root_path):
        print(f"❌ 不是目录: {root_path}", file=sys.stderr)
        return
    
    basename = os.path.basename(root_path) or root_path
    print(basename)
    
    def _walk(dirpath, prefix="", depth=0):
        if depth >= max_depth:
            return
        
        try:
            entries = sorted(os.listdir(dirpath))
        except PermissionError:
            print(f"{prefix}{LAST} [权限不足]")
            return
        
        if not show_hidden:
            entries = [e for e in entries if not e.startswith(".")]
        
        # Separate dirs and files
        dirs = []
        files = []
        for e in entries:
            full = os.path.join(dirpath, e)
            if os.path.isdir(full):
                dirs.append(e)
            else:
                files.append(e)
        
        if dirs_only:
            items = dirs
        else:
            items = dirs + files
        
        for i, entry in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = LAST if is_last else BRANCH
            full = os.path.join(dirpath, entry)
            
            if os.path.isdir(full):
                print(f"{prefix}{connector}{entry}/")
                next_prefix = prefix + ("    " if is_last else PIPE)
                _walk(full, next_prefix, depth + 1)
            else:
                # Show file size
                try:
                    size = os.path.getsize(full)
                    size_str = format_size(size)
                    print(f"{prefix}{connector}{entry}  ({size_str})")
                except OSError:
                    print(f"{prefix}{connector}{entry}")
    
    _walk(root_path)
    print(f"\n{count_items(root_path, show_hidden, dirs_only)}")

def count_items(root_path, show_hidden=False, dirs_only=False):
    """统计目录内容"""
    dcount = 0
    fcount = 0
    for root, dirs, files in os.walk(root_path):
        if not show_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]
        dcount += len(dirs)
        if not dirs_only:
            fcount += len(files)
        # Only first level for dirs_only
        if dirs_only:
            break
    if dirs_only:
        return f"{dcount} 个目录"
    return f"{dcount} 个目录, {fcount} 个文件"

def format_size(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def main():
    args = sys.argv[1:]
    
    if "-h" in args or "--help" in args:
        print("用法: treedir [选项] [目录]")
        print("选项:")
        print("  -d, --max-depth N   最大深度 (默认: 3)")
        print("  -a, --all           显示隐藏文件")
        print("  --dirs-only         只显示目录")
        print("  如果不指定目录，使用当前目录")
        return
    
    root = "."
    max_depth = 3
    show_hidden = False
    dirs_only = False
    
    i = 0
    while i < len(args):
        if args[i] in ("-d", "--max-depth"):
            i += 1
            if i < len(args):
                max_depth = int(args[i])
        elif args[i] in ("-a", "--all"):
            show_hidden = True
        elif args[i] == "--dirs-only":
            dirs_only = True
        else:
            root = args[i]
        i += 1
    
    build_tree(root, max_depth, show_hidden, dirs_only)

if __name__ == "__main__":
    main()
