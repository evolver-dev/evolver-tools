#!/usr/bin/env python3
"""
smellfinder — Python 代码异味检测器
静态分析 Python 源码，报告代码质量问题。
"""

import ast
import os
import sys
import re
from pathlib import Path

# ---- 配置 ----
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 5
MAX_NESTING_DEPTH = 3
MAX_CLASS_METHODS = 15
MAX_FILE_LINES = 400
MIN_DOCSTRING_LENGTH = 10

class CodeSmellVisitor(ast.NodeVisitor):
    def __init__(self, source_lines):
        self.source_lines = source_lines
        self.smells = []
        self.depth = 0
        self.current_function = None
        self.current_class = None

    def add_smell(self, line, severity, category, message):
        self.smells.append({
            'line': line,
            'severity': severity,  # 'info', 'warning', 'error'
            'category': category,
            'message': message,
        })

    def check_docstring(self, node, kind):
        """Check if node has a proper docstring"""
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module))
            and node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
            doc = node.body[0].value.value.strip()
            if len(doc) < MIN_DOCSTRING_LENGTH:
                self.add_smell(node.lineno, 'info', 'docstring',
                    f"{kind} 文档字符串过短 ({len(doc)} 字符)")
            return True
        return False

    def visit_FunctionDef(self, node):
        self._visit_function(node, 'def')

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node, 'async def')

    def _visit_function(self, node, kind):
        old_func = self.current_function
        self.current_function = node.name

        # Check docstring
        if not self.check_docstring(node, f"函数 {node.name}"):
            self.add_smell(node.lineno, 'warning', 'docstring',
                f"函数 '{node.name}' 缺少文档字符串")

        # Check arguments
        args = node.args.args + node.args.kwonlyargs
        if node.args.vararg: args.append(node.args.vararg)
        if node.args.kwarg: args.append(node.args.kwarg)
        # Exclude self/cls
        real_args = [a for a in args if a.arg not in ('self', 'cls')]
        if len(real_args) > MAX_ARGUMENTS:
            self.add_smell(node.lineno, 'warning', 'arguments',
                f"函数 '{node.name}' 参数过多 ({len(real_args)} 个，建议 ≤{MAX_ARGUMENTS})")

        # Check function length
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_lines = node.end_lineno - node.lineno
            if func_lines > MAX_FUNCTION_LINES:
                self.add_smell(node.lineno, 'warning', 'length',
                    f"函数 '{node.name}' 过长 ({func_lines} 行，建议 ≤{MAX_FUNCTION_LINES})")

        # Check complexity (if/else branches)
        branch_count = sum(1 for n in ast.walk(node)
                          if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                           ast.ExceptHandler, ast.Try)))
        if branch_count > 12:
            self.add_smell(node.lineno, 'warning', 'complexity',
                f"函数 '{node.name}' 分支过多 ({branch_count} 个控制流分支)")

        # Visit body (track nesting)
        self.depth += 1
        old_depth = self.depth
        self.generic_visit(node)
        self.depth = old_depth - 1

        self.current_function = old_func

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name

        # Check docstring
        if not self.check_docstring(node, f"类 {node.name}"):
            self.add_smell(node.lineno, 'info', 'docstring',
                f"类 '{node.name}' 缺少文档字符串")

        # Count methods
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) > MAX_CLASS_METHODS:
            self.add_smell(node.lineno, 'warning', 'design',
                f"类 '{node.name}' 方法过多 ({len(methods)} 个，建议 ≤{MAX_CLASS_METHODS})")

        # Check for __init__
        has_init = any(m.name == '__init__' for m in methods)
        if not has_init:
            self.add_smell(node.lineno, 'info', 'design',
                f"类 '{node.name}' 没有 __init__ 方法")

        self.generic_visit(node)
        self.current_class = old_class

    def visit_If(self, node):
        self.depth += 1
        if self.depth > MAX_NESTING_DEPTH and self.current_function:
            self.add_smell(node.lineno, 'warning', 'nesting',
                f"嵌套深度 {self.depth} 层 (在 '{self.current_function}' 中)")
        self.generic_visit(node)
        self.depth -= 1

    def visit_Try(self, node):
        # Check bare except
        for handler in node.handlers:
            if handler.type is None:
                self.add_smell(handler.lineno, 'error', 'exception',
                    "裸 except: 应该指定异常类型")
        self.depth += 1
        if self.depth > MAX_NESTING_DEPTH and self.current_function:
            self.add_smell(node.lineno, 'warning', 'nesting',
                f"嵌套深度 {self.depth} 层 (在 '{self.current_function}' 中)")
        self.generic_visit(node)
        self.depth -= 1

    def visit_Global(self, node):
        self.add_smell(node.lineno, 'warning', 'design',
            f"使用了全局变量: {', '.join(node.names)}")

    def visit_Call(self, node):
        # Check for print() in non-script code
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.add_smell(node.lineno, 'info', 'debug',
                "print() 调用 (生产代码中请使用 logging)")
        self.generic_visit(node)


def check_file_patterns(source, filename):
    """Regex-based checks not possible with AST"""
    smells = []
    lines = source.split('\n')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # TODO/FIXME/HACK
        if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', stripped):
            match = re.search(r'\b(TODO|FIXME|HACK|XXX)\b', stripped)
            smells.append({
                'line': i,
                'severity': 'info',
                'category': 'marker',
                'message': f"标记: {match.group(0)}"
            })

        # Line too long
        if len(line.rstrip('\n')) > 100:
            smells.append({
                'line': i,
                'severity': 'warning',
                'category': 'style',
                'message': f"行过长 ({len(line.rstrip())} 字符，建议 ≤100)"
            })

        # Trailing whitespace
        if line.rstrip('\n') != line.rstrip():
            smells.append({
                'line': i,
                'severity': 'info',
                'category': 'style',
                'message': "行尾有空白字符"
            })

    return smells


def check_module_level(source, filename):
    """Module-level checks"""
    smells = []

    # Module docstring
    lines = source.split('\n')
    first_line = lines[0].strip() if lines else ''
    if not (first_line.startswith('"""') or first_line.startswith("'''") or
            first_line.startswith('#!')):
        # Check if there's any top-level comment/docstring
        has_header = False
        for line in lines[:5]:
            if line.strip().startswith(('"""', "'''", '# ')):
                has_header = True
                break
        if not has_header:
            smells.append({
                'line': 1,
                'severity': 'info',
                'category': 'docstring',
                'message': "文件缺少模块级文档"
            })

    # File length
    if len(lines) > MAX_FILE_LINES:
        smells.append({
            'line': len(lines),
            'severity': 'info',
            'category': 'length',
            'message': f"文件过长 ({len(lines)} 行，建议 ≤{MAX_FILE_LINES})"
        })

    return smells


def analyze_file(filepath):
    """Analyze a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except Exception as e:
        return {
            'file': str(filepath),
            'error': str(e),
            'smells': [],
            'loc': 0,
        }

    lines = source.split('\n')
    loc = len(lines)

    # Pattern checks (before AST)
    smells = check_file_patterns(source, filepath)
    smells += check_module_level(source, filepath)

    # AST analysis
    try:
        tree = ast.parse(source, filename=filepath)
        visitor = CodeSmellVisitor(lines)
        visitor.visit(tree)
        smells += visitor.smells
    except SyntaxError as e:
        smells.append({
            'line': e.lineno or 0,
            'severity': 'error',
            'category': 'syntax',
            'message': f"语法错误: {e.msg}"
        })

    # Sort by line
    smells.sort(key=lambda s: s['line'])

    return {
        'file': str(filepath),
        'loc': loc,
        'smells': smells,
        'error': None,
    }


def print_report(results, verbose=True):
    """Print formatted report"""
    total_smells = 0
    total_errors = 0
    total_warnings = 0
    total_info = 0

    print(f"\n{'='*60}")
    print(f"  代码异味检测报告")
    print(f"{'='*60}\n")

    for result in results:
        if result['error']:
            print(f"  ✗ {result['file']} — 错误: {result['error']}")
            continue

        file_smells = result['smells']
        fn = result['file']

        # Count severity
        errors = sum(1 for s in file_smells if s['severity'] == 'error')
        warnings = sum(1 for s in file_smells if s['severity'] == 'warning')
        infos = sum(1 for s in file_smells if s['severity'] == 'info')
        total_errors += errors
        total_warnings += warnings
        total_info += infos

        if not file_smells:
            print(f"  ✓ {fn} ({result['loc']} 行) — 干净")
            continue

        total_smells += len(file_smells)

        if verbose:
            print(f"  {fn} ({result['loc']} 行) — {len(file_smells)} 个异味 "
                  f"(🔴{errors} ⚠{warnings} ℹ{infos})")
            for s in file_smells:
                prefix = {
                    'error': '  🔴',
                    'warning': '  ⚠',
                    'info': '  ℹ',
                }[s['severity']]
                print(f"  {prefix} L{s['line']:>4} [{s['category']}] {s['message']}")
            print()

    # Summary
    print(f"{'='*60}")
    print(f"  摘要: {len(results)} 个文件, {total_smells} 个异味")
    if total_errors:
        print(f"  🔴 错误: {total_errors}")
    if total_warnings:
        print(f"  ⚠ 警告: {total_warnings}")
    if total_info:
        print(f"  ℹ 提示: {total_info}")
    print(f"{'='*60}\n")

    return total_smells


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Python 代码异味检测器')
    parser.add_argument('paths', nargs='+', help='文件或目录路径')
    parser.add_argument('-q', '--quiet', action='store_true', help='简洁输出')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    args = parser.parse_args()

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file() and path.suffix == '.py':
            files.append(path)
        elif path.is_dir():
            for f in sorted(path.rglob('*.py')):
                # Skip common non-source dirs
                skip_dirs = {'__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules',
                            'build', 'dist', '.tox', '.mypy_cache', '.pytest_cache'}
                if not any(d in f.parts for d in skip_dirs):
                    files.append(f)

    files = sorted(set(files))
    if not files:
        print("未找到 .py 文件")
        return

    results = [analyze_file(f) for f in files]

    if args.json:
        import json
        output = []
        for r in results:
            output.append({
                'file': r['file'],
                'loc': r['loc'],
                'smells': r['smells'],
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_report(results, verbose=not args.quiet)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "smellfinder",
    "func": "main",
    "desc": 'Smellfinder',
}

if __name__ == '__main__':
    main()
