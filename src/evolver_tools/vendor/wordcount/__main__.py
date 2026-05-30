#!/usr/bin/env python3
"""wordcount — 增强版文本计数工具。零外部依赖。"""
import os
import sys

def count_text(text, name="<stdin>"):
    lines = text.split("\n")
    line_count = len(lines)
    # Last empty line doesn't count for most wc conventions
    if text.endswith("\n"):
        line_count -= 0  # We count trailing newline as a line (like wc -l)
    
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    byte_count = len(text.encode("utf-8"))
    
    # Non-empty lines
    non_empty = sum(1 for l in lines if l.strip())
    
    return {
        "file": name,
        "lines": line_count,
        "words": word_count,
        "chars": char_count,
        "bytes": byte_count,
        "non_empty_lines": non_empty,
    }

def format_output(stats, mode="default"):
    fname = stats["file"]
    if mode == "lines":
        return f"{stats['lines']:>8} {fname}"
    elif mode == "words":
        return f"{stats['words']:>8} {fname}"
    elif mode == "chars":
        return f"{stats['chars']:>8} {fname}"
    else:
        return f"{stats['lines']:>8} {stats['words']:>8} {stats['chars']:>8} {fname}"

def main():
    args = sys.argv[1:]
    mode = "default"
    
    if "-h" in args or "--help" in args:
        print("用法: wordcount [选项] [文件...]")
        print("选项:")
        print("  -l, --lines     只显示行数")
        print("  -w, --words     只显示词数")
        print("  -c, --chars     只显示字符数")
        print("  --no-header     不显示表头")
        print("如果没有文件，从 stdin 读取")
        return
    
    # Parse flags
    files = []
    for a in args:
        if a in ("-l", "--lines"): mode = "lines"
        elif a in ("-w", "--words"): mode = "words"
        elif a in ("-c", "--chars"): mode = "chars"
        else: files.append(a)
    
    if not files:
        # Read from stdin
        text = sys.stdin.read()
        stats = count_text(text)
        if mode == "default":
            print(f"{'Lines':>8} {'Words':>8} {'Chars':>8} File")
            print("-" * 40)
        print(format_output(stats, mode))
        return
    
    all_stats = []
    for fpath in files:
        if not os.path.isfile(fpath):
            print(f"❌ 文件不存在: {fpath}", file=sys.stderr)
            continue
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        all_stats.append(count_text(text, fpath))
    
    if not all_stats:
        return
    
    if mode == "default":
        print(f"{'Lines':>8} {'Words':>8} {'Chars':>8} File")
        print("-" * 40)
    for s in all_stats:
        print(format_output(s, mode))
    
    if len(all_stats) > 1 and mode == "default":
        total = {
            "lines": sum(s["lines"] for s in all_stats),
            "words": sum(s["words"] for s in all_stats),
            "chars": sum(s["chars"] for s in all_stats),
        }
        print("-" * 40)
        print(f"{total['lines']:>8} {total['words']:>8} {total['chars']:>8} (总计)")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "wordcount",
    "func": "main",
    "desc": 'Wordcount',
}

if __name__ == "__main__":
    main()
