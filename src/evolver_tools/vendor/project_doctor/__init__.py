#!/usr/bin/env python3
"""
project-doctor — 项目健康检查工具
扫描项目目录，检查基础设施完整性，评分并提建议。
"""

import sys
import os
import re
import json
from pathlib import Path

def red(s): return f"\033[91m{s}\033[0m"
def green(s): return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s): return f"\033[96m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"

class ProjectDoctor:
    """Project health checker"""

    def __init__(self, path, verbose=False):
        self.root = Path(path).resolve()
        self.verbose = verbose
        self.checks = []
        self.score = 0
        self.max_score = 0
        self.findings = []  # (category, severity, message, weight)

    def check(self, name, weight, fn):
        """Run a check function"""
        self.max_score += weight
        try:
            result = fn()
            if result:
                self.score += weight
                self.findings.append(('pass', 'ok', f"{name}: {result}", 0))
            else:
                self.findings.append(('fail', 'warn', f"{name}: {red('未通过')}", weight))
            return result
        except Exception as e:
            if self.verbose:
                self.findings.append(('error', 'error', f"{name}: 检查出错 ({e})", 0))
            return False

    def check_file(self, *paths):
        """Check if a file exists (relative to project root)"""
        return any((self.root / p).is_file() for p in paths)

    def check_dir(self, path):
        """Check if directory exists"""
        return (self.root / path).is_dir()

    def read_file(self, path):
        """Read a file if it exists"""
        f = self.root / path
        if f.is_file():
            try:
                return f.read_text(encoding='utf-8', errors='replace')
            except:
                return None
        return None

    def scan(self):
        """Run all checks"""

        # ---- 1. 元文件检查 ----
        self.findings.append(('section', 'info', bold('\n📦 元文件'), 0))

        # README
        self.check('README', 10, lambda:
            green(f"✓ {self._find_file('README*')}") if self._find_file('README*') else None)

        # LICENSE
        self.check('LICENSE', 5, lambda:
            green(f"✓ {self._find_file('LICENSE*')}") if self._find_file('LICENSE*') else None)

        # .gitignore
        self.check('.gitignore', 8, lambda:
            self._check_gitignore() if self.check_file('.gitignore') else None)

        # .git
        self.check('.git (版本控制)', 10, lambda:
            green(f"✓ {self._check_git_health()}") if self.check_dir('.git') else None)

        # CHANGELOG
        self.check('CHANGELOG', 3, lambda:
            green(f"✓ {self._find_file('CHANGELOG*')}") if self._find_file('CHANGELOG*') else None)

        # ---- 2. Python 项目检查 ----
        has_python = self._has_python_files()
        if has_python:
            self.findings.append(('section', 'info', bold('\n🐍 Python 项目'), 0))

            # requirements.txt / pyproject.toml
            self.check('依赖管理', 8, lambda:
                green(f"✓ {self._find_file('requirements.txt') or self._find_file('pyproject.toml') or self._find_file('setup.py') or self._find_file('Pipfile')}")
                if self._find_file('requirements.txt') or self._find_file('pyproject.toml') or self._find_file('setup.py') or self._find_file('Pipfile') else None)

            # venv / .venv
            self.check('虚拟环境', 6, lambda:
                green(f"✓ {self._find_dir('venv') or self._find_dir('.venv')}") if self.check_dir('venv') or self.check_dir('.venv') else yellow("⚠ 建议: 创建虚拟环境"))

            # __init__.py in packages
            packages = list(self.root.rglob('__init__.py'))
            self.check('包结构', 3, lambda:
                cyan(f"{len(packages)} 个包") if packages else yellow("无 Python 包"))

            # Python version pinning
            py_version = self.read_file('.python-version')
            if py_version:
                self.findings.append(('pass', 'info', f"  Python 版本固定: {py_version.strip()}", 0))

        # ---- 3. JavaScript/Node 项目检查 ----
        has_js = self.check_file('package.json')
        if has_js:
            self.findings.append(('section', 'info', bold('\n📦 Node.js 项目'), 0))

            # package.json validity
            pkg = self._read_json('package.json')
            if pkg:
                scripts = pkg.get('scripts', {})
                has_test = 'test' in scripts
                has_build = 'build' in scripts
                deps = len(pkg.get('dependencies', {}))
                dev_deps = len(pkg.get('devDependencies', {}))
                self.findings.append(('pass', 'info',
                    f"  依赖: {deps} 生产 + {dev_deps} 开发", 0))
                if has_test:
                    self.score += 2
                    self.findings.append(('pass', 'ok', f"  test 脚本: {green('✓')}", 0))
                if has_build:
                    self.score += 2
                    self.findings.append(('pass', 'ok', f"  build 脚本: {green('✓')}", 0))

            # node_modules
            nm = self.check_dir('node_modules')
            if nm:
                self.findings.append(('pass', 'info', f"  node_modules: {green('已安装')}", 0))
            else:
                self.findings.append(('pass', 'info', f"  node_modules: {yellow('未安装 (需先 npm install)')}", 0))

            # .nvmrc
            if self.check_file('.nvmrc'):
                nvm = self.read_file('.nvmrc')
                self.findings.append(('pass', 'info', f"  Node 版本: {nvm.strip()}", 0))

        # ---- 4. 项目结构检查 ----
        self.findings.append(('section', 'info', bold('\n📁 项目结构'), 0))

        # Entry point detection
        entry = self._find_entry_point()
        if entry:
            self.check('入口文件', 5, lambda: green(entry))

        # Test directory
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        found_test = False
        for td in test_dirs:
            if self.check_dir(td):
                test_count = len(list((self.root / td).rglob('*.py' if has_python else '*.js')))
                self.findings.append(('pass', 'info', f"  测试目录: {green(td)} ({test_count} 个测试文件)", 0))
                found_test = True
                break
        if not found_test:
            self.findings.append(('fail', 'warn', f"  测试目录: {yellow('⚠ 未发现 (建议: 创建 tests/)')}", 3))

        # CI config
        ci_files = ['.github/workflows', '.gitlab-ci.yml', '.circleci', 'Jenkinsfile',
                    '.travis.yml', 'azure-pipelines.yml']
        self.check('CI/CD 配置', 5, lambda:
            green(f"✓ {self._find_first_ci()}") if self._find_first_ci() else None)

        # Docker
        if self.check_file('Dockerfile', 'docker-compose.yml', 'compose.yaml'):
            self.findings.append(('pass', 'info', f"  Docker: {green('已配置')}", 0))

        # Makefile
        if self.check_file('Makefile', 'makefile', 'Justfile', 'Taskfile.yml'):
            self.findings.append(('pass', 'info', f"  构建工具: {green('已配置')}", 0))

        # ---- 5. 代码质量检查 ----
        self.findings.append(('section', 'info', bold('\n🔍 代码质量'), 0))

        # Linter config
        lint_configs = ['.pylintrc', '.flake8', '.eslintrc*', '.eslintrc.json',
                       '.eslintrc.js', '.prettierrc', 'pyproject.toml',
                       '.ruff.toml', 'ruff.toml']
        self.check('Linter 配置', 5, lambda:
            green(f"✓ {self._find_any(lint_configs)}") if self._find_any(lint_configs) else None)

        # Editor config
        if self.check_file('.editorconfig'):
            self.findings.append(('pass', 'info', f"  EditorConfig: {green('✓')}", 0))

        # File count and sizes
        all_files = list(self.root.rglob('*'))
        file_count = len([f for f in all_files if f.is_file()])
        dir_count = len([f for f in all_files if f.is_dir()])

        # Largest files
        py_files = list(self.root.rglob('*.py'))
        if py_files:
            total_loc = sum(len(f.read_text().splitlines()) for f in py_files if f.is_file())
            self.findings.append(('pass', 'info',
                f"  Python 代码: {len(py_files)} 个文件, {total_loc} 行", 0))

        self.findings.append(('pass', 'info',
            f"  项目结构: {file_count} 个文件, {dir_count} 个目录", 0))

        # ---- Summary ----
        return {
            'root': str(self.root),
            'score': self.score,
            'max_score': self.max_score,
            'percentage': round(self.score / max(1, self.max_score) * 100, 1),
            'findings': self.findings,
        }

    def _find_file(self, pattern):
        """Find a file by glob pattern"""
        matches = list(self.root.glob(pattern))
        if matches:
            return matches[0].name
        # Try with case-insensitive
        for f in self.root.iterdir():
            if f.is_file() and f.name.lower().startswith(pattern.lower().replace('*', '')):
                return f.name
        return None

    def _find_dir(self, name):
        """Find a directory"""
        d = self.root / name
        if d.is_dir():
            return name
        return None

    def _has_python_files(self):
        return len(list(self.root.glob('*.py'))) > 0

    def _read_json(self, path):
        try:
            content = self.read_file(path)
            if content:
                return json.loads(content)
        except:
            pass
        return None

    def _find_entry_point(self):
        """Detect main entry point"""
        candidates = ['main.py', 'app.py', 'cli.py', 'index.js', 'index.ts',
                     'server.py', 'run.py', 'manage.py', 'src/main.py',
                     'cmd/main.go']
        for c in candidates:
            if self.check_file(c):
                return c
        # Check for __main__.py
        if self._find_any(['__main__.py', '*/__main__.py']):
            return '__main__.py'
        return None

    def _check_gitignore(self):
        content = self.read_file('.gitignore')
        if not content:
            return "文件为空"
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
        return f"{len(lines)} 条规则"

    def _check_git_health(self):
        """Check git repo health"""
        try:
            import subprocess
            # Count commits
            result = subprocess.run(
                ['git', '-C', str(self.root), 'rev-list', '--count', 'HEAD'],
                capture_output=True, text=True, timeout=5
            )
            commits = result.stdout.strip()
            # Check for recent commit
            result2 = subprocess.run(
                ['git', '-C', str(self.root), 'log', '-1', '--format=%cr'],
                capture_output=True, text=True, timeout=5
            )
            recent = result2.stdout.strip()
            return f"{commits} 次提交 (最近: {recent})"
        except:
            return "存在 .git 目录"

    def _find_first_ci(self):
        """Find CI/CD config"""
        ci_map = {
            '.github/workflows/': '.github/workflows',
            '.gitlab-ci.yml': '.gitlab-ci.yml',
            '.circleci/config.yml': '.circleci/config.yml',
            'Jenkinsfile': 'Jenkinsfile',
            '.travis.yml': '.travis.yml',
        }
        for name, path in ci_map.items():
            if self.check_file(path) or self.check_dir(path):
                return name.rstrip('/')
        return None

    def _find_any(self, patterns):
        """Find first matching pattern"""
        for p in patterns:
            matches = list(self.root.glob(p))
            if matches:
                return matches[0].name
            # Also check as exact name
            if self.check_file(p):
                return p
        return None


def print_report(result):
    """Print formatted health report"""
    root = result['root']
    score = result['score']
    max_score = result['max_score']
    pct = result['percentage']

    # Header
    print(f"\n  {bold('🏥 项目健康检查报告')}")
    print(f"  {dim('─' * 55)}")
    print(f"  {dim('项目:')}  {root}")
    print(f"  {dim('时间:')}  {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  {dim('─' * 55)}")

    # Score bar
    if pct >= 80:
        score_color = green
        grade = '优秀'
    elif pct >= 60:
        score_color = yellow
        grade = '良好'
    elif pct >= 40:
        score_color = yellow
        grade = '需改进'
    else:
        score_color = red
        grade = '不健康'

    bar_w = 30
    filled = int(bar_w * pct / 100)
    bar = '█' * filled + '░' * (bar_w - filled)
    print(f"\n  {bold('健康评分:')} {score_color(f'{score}/{max_score} ({pct}%)')} {bold(grade)}")
    print(f"  {score_color(bar)}")
    print()

    # Findings by category
    current_section = ''
    warnings = []
    suggestions = []

    for finding in result['findings']:
        ftype, severity, msg, weight = finding

        if ftype == 'section':
            print(msg)
            continue

        if ftype == 'pass':
            if severity == 'ok':
                print(f"    {green('✓')} {msg}")
            elif severity == 'info':
                print(f"    {cyan('ℹ')} {dim(msg)}")

        elif ftype == 'fail':
            if weight > 0:
                warnings.append((msg, weight))
            print(f"    {yellow('⚠')} {msg}")

    # Suggestions section
    if warnings:
        print(f"\n  {bold('💡 改进建议')}")
        print(f"  {dim('─' * 55)}")
        for msg, weight in sorted(warnings, key=lambda x: -x[1]):
            icon = {10: '🔴', 8: '🟠', 5: '🟡', 3: '🟢'}.get(weight, '⚪')
            print(f"    {icon} {msg} (权重: {weight})")
        print()

    # Legend
    print(f"  {dim('评分标准: ≥80 优秀 | ≥60 良好 | ≥40 需改进 | <40 不健康')}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='项目健康检查工具')
    parser.add_argument('path', nargs='?', default='.', help='项目目录路径 (默认: 当前目录)')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    args = parser.parse_args()

    path = Path(args.path).resolve()
    if not path.is_dir():
        print(f"{red('✗ 目录不存在:')} {path}")
        sys.exit(1)

    doctor = ProjectDoctor(path, verbose=args.verbose)
    result = doctor.scan()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "project-doctor",
    "func": "main",
    "desc": 'Project Doctor',
}

if __name__ == '__main__':
    main()
