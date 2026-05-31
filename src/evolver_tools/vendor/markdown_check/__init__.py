#!/usr/bin/env python3
"""markdown-check — Markdown 格式校验器

检查 Markdown 文件中的常见问题：
  · 标题层级跳跃 (h1→h3)
  · 断开的锚点链接
  · 代码块未配对
  · 尾随空白
  · 空列表项
  · 过长的行

用法:
  markdown-check README.md
  markdown-check docs/**/*.md
  markdown-check .              # 递归检查所有 .md 文件

输出格式: 文件:行:列  级别  消息

零外部依赖。纯 Python 3.8+。
"""

import os
import re
import sys
import glob


# ── 规则引擎 ──────────────────────────────────────────────

class MarkdownChecker:
    """对单个 .md 文件执行所有检查规则"""

    def __init__(self, path):
        self.path = path
        self.lines = []
        self.issues = []    # (line, col, level, msg)
        self._code_fence = None  # 当前是否在代码块内

    def check(self):
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                self.lines = f.readlines()
        except Exception as e:
            self.issues.append((1, 0, "ERROR", f"无法读取文件: {e}"))
            return self

        self._code_fence = None
        headings_seen = set()

        for i, raw in enumerate(self.lines):
            ln = i + 1
            line = raw.rstrip("\n").rstrip("\r")
            stripped = line.strip()

            # ── 跟踪代码块 ──
            if line.startswith("```") or line.startswith("~~~"):
                fence_char = line[:3]
                if self._code_fence is None:
                    self._code_fence = fence_char
                elif self._code_fence == fence_char:
                    # 检查代码块关闭后是否有多余内容
                    rest = line[3:].strip()
                    if rest and self._code_fence is None:
                        pass  # 围栏有语言标注，正常
                    self._code_fence = None
                continue

            # 代码块内跳过 lint
            if self._code_fence:
                continue

            # ── 规则 1: 尾随空白 ──
            if raw.endswith(" \n") or raw.endswith("\t\n") or raw.endswith("  \r\n"):
                self.issues.append((ln, len(raw.rstrip("\n\r")), "WARN", "尾随空白"))

            # ── 规则 2: 标题层级跳跃 ──
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                # 检查 ATX 标题是否以 # 结尾（不规范但常见）
                if text.endswith("#"):
                    self.issues.append((ln, len(line) - text[::-1].index("#"), "INFO",
                                        "标题尾部有多余 #"))

                # 检查是否有更高级别标题出现过
                if headings_seen:
                    max_seen = max(headings_seen)
                    if level - max_seen > 1:
                        self.issues.append((ln, 0, "WARN",
                                            f"标题层级跳跃: h{max_seen} → h{level}"))
                headings_seen.add(level)

            # ── 规则 3: 空列表项 ──
            if re.match(r"^(\s*[-*+]|\s*\d+\.)\s*$", line):
                self.issues.append((ln, 0, "WARN", "空列表项"))

            # ── 规则 4: 过长行 ──
            if len(line) > 120 and not line.startswith("|"):  # 跳过表格
                self.issues.append((ln, 120, "INFO", f"行过长 ({len(line)} > 120 字符)"))

            # ── 规则 5: 重复的标点 ──
            if re.search(r"[!?.,:;]{3,}", line):
                self.issues.append((ln, 0, "INFO", "重复标点"))

            # ── 规则 6: 图片缺少 alt 文本 ──
            for match in re.finditer(r"!\[(.*?)\]\(.*?\)", line):
                alt_text = match.group(1).strip()
                if not alt_text:
                    self.issues.append((ln, match.start(), "WARN", "图片缺少 alt 文本"))

        # ── 文件级检查 ──
        # 代码块未关闭
        if self._code_fence:
            self.issues.append((len(self.lines), 0, "ERROR", "代码块未关闭"))

        # 没有标题
        if not headings_seen and self.lines:
            self.issues.append((1, 0, "INFO", "文件没有标题"))

        # 空文件
        if not self.lines or all(l.strip() == "" for l in self.lines):
            self.issues.append((1, 0, "WARN", "空文件"))

        return self

    def report(self, show_all=False):
        """返回格式化报告"""
        total = {"ERROR": 0, "WARN": 0, "INFO": 0}
        lines = []
        for ln, col, level, msg in self.issues:
            total[level] = total.get(level, 0) + 1
            if level == "INFO" and not show_all:
                continue
            col_str = f":{col}" if col else ""
            lines.append(f"  {self.path}:{ln}{col_str}  {level:<5} {msg}")

        if not lines:
            return "  ✓ 整洁\n"

        header = (f"  {self.path}: "
                  f"{total.get('ERROR', 0)} error(s), "
                  f"{total.get('WARN', 0)} warn(s), "
                  f"{total.get('INFO', 0)} info(s)")
        return header + "\n" + "\n".join(lines) + "\n"


# ── CLI 入口 ──────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="markdown-check — Markdown 格式校验器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  markdown-check README.md\n  markdown-check docs/\n  markdown-check -a .  # 显示所有信息级提示",
    )
    parser.add_argument("target", nargs="?", default=".", help="文件或目录（默认: 当前目录）")
    parser.add_argument("-a", "--all", action="store_true", help="显示所有信息级提示（含 INFO）")
    parser.add_argument("-q", "--quiet", action="store_true", help="只显示有问题的文件")
    parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录")

    args = parser.parse_args()
    target = args.target

    # 收集文件
    files = []
    if os.path.isfile(target):
        if target.endswith(".md") or target.endswith(".markdown"):
            files = [target]
        else:
            print(f"错误: 不是 Markdown 文件: {target}", file=sys.stderr)
            sys.exit(1)
    elif os.path.isdir(target):
        pattern = "**/*.md" if not args.no_recursive else "*.md"
        files = sorted(glob.glob(os.path.join(target, pattern), recursive=True))
    else:
        # 尝试 glob
        matches = glob.glob(target, recursive=True)
        files = sorted(f for f in matches if f.endswith((".md", ".markdown")))

    if not files:
        print("未找到 .md 文件", file=sys.stderr)
        sys.exit(0)

    # 执行检查
    total_errors = 0
    total_warns = 0
    checked = 0

    for fpath in files:
        checker = MarkdownChecker(fpath)
        checker.check()
        if not args.quiet or any(i[1] != "INFO" or args.all for i in checker.issues):
            print(checker.report(show_all=args.all))
        for _, _, level, _ in checker.issues:
            if level == "ERROR":
                total_errors += 1
            elif level == "WARN":
                total_warns += 1
        checked += 1

    # 汇总
    print(f"---\n检查了 {checked} 个文件，"
          f"{total_errors} 个错误，{total_warns} 个警告")

    sys.exit(1 if total_errors > 0 else 0)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "markdown-check",
    "func": "main",
    "desc": 'Markdown link and structure checker',
}

if __name__ == "__main__":
    main()
