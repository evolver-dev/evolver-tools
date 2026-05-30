#!/usr/bin/env python3
"""
envcheck — 环境变量验证器

验证环境变量存在、格式、类型，检查默认值，显示缺失项。

Features:
  - 检查必需变量是否存在
  - 验证变量格式（email, url, port, path, regex模式）
  - 转换为指定类型（int, float, bool, list）
  - 检查默认值是否被覆盖
  - 显示所有缺失的必需变量
  - 0依赖，纯Python标准库

Usage:
  envcheck                    # 扫描所有env文件并检查
  envcheck path/to/.env       # 检查指定env文件
  envcheck --require DB_HOST DB_PORT  # 指定必需变量
  envcheck --template .env.example    # 对比模板
  envcheck --json              # JSON输出（用于CI）
"""

import os
import re
import sys
import json
import argparse

# ─── 格式验证器 ─────────────────────────────────────────────

VALIDATORS = {
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "url": re.compile(r"^https?://[^\s]+$"),
    "port": re.compile(r"^\d+$"),
    "integer": re.compile(r"^-?\d+$"),
    "float": re.compile(r"^-?\d+(\.\d+)?$"),
    "boolean": re.compile(r"^(true|false|yes|no|1|0)$", re.I),
    "path": re.compile(r"^[/~.]"),
    "hex_color": re.compile(r"^#[0-9a-fA-F]{3,8}$"),
    "uuid": re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    ),
    "semver": re.compile(r"^\d+\.\d+\.\d+"),
    "datetime_iso": re.compile(
        r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}"
    ),
}

FORMAT_HELP = {
    "email": "格式应为 user@domain.com",
    "url": "格式应为 https://...",
    "port": "应为数字 (1-65535)",
    "integer": "应为整数",
    "float": "应为数字（可含小数）",
    "boolean": "应为 true/false/yes/no/1/0",
    "path": "应为路径 (以 / ~ 或 . 开头)",
    "hex_color": "应为 #RGB/#RRGGBB/#RRGGBBAA",
    "uuid": "应为 UUID 格式",
    "semver": "应为语义版本号 (x.y.z)",
    "datetime_iso": "应为 ISO 日期时间",
}


def validate_format(value, fmt):
    """验证值格式"""
    pattern = VALIDATORS.get(fmt)
    if not pattern:
        return True, "未知格式检查"
    if pattern.match(str(value).strip()):
        return True, None
    return False, FORMAT_HELP.get(fmt, f"格式不匹配: {fmt}")


def cast_type(value, target_type):
    """类型转换"""
    try:
        if target_type == "int":
            return int(value), True, None
        elif target_type == "float":
            return float(value), True, None
        elif target_type == "bool":
            return value.lower() in ("true", "yes", "1"), True, None
        elif target_type == "list":
            import shlex
            parts = shlex.split(value)
            return parts, True, None
        else:
            return value, True, None
    except (ValueError, TypeError) as e:
        return value, False, str(e)


# ─── .env 文件解析 ────────────────────────────────────────

def find_env_files(start_dir=None):
    """递归查找 .env 文件"""
    if start_dir is None:
        start_dir = os.getcwd()
    results = []
    for root, dirs, files in os.walk(start_dir):
        # 跳过隐藏目录和 node_modules, .git, __pycache__
        dirs[:] = [d for d in dirs
                   if not d.startswith('.') and
                   d not in ('node_modules', '__pycache__', 'venv', '.venv')]
        for f in files:
            if f == '.env' or f.endswith('.env') or f == '.env.example':
                results.append(os.path.join(root, f))
    return results


def parse_env_file(filepath):
    """解析 .env 文件"""
    variables = {}
    errors = []
    try:
        with open(filepath, "r") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    errors.append((i, line[:60], "格式错误: 缺少 ="))
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # 去掉引号
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                variables[key] = val
        return variables, errors
    except FileNotFoundError:
        return None, [(0, "", "文件未找到")]


# ─── 报告输出 ──────────────────────────────────────────────

def color(text, code):
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(text):
    return color(text, "92")


def red(text):
    return color(text, "91")


def yellow(text):
    return color(text, "93")


def blue(text):
    return color(text, "94")


def print_report(result, json_output=False):
    """打印检查报告"""
    if json_output:
        print(json.dumps(result, indent=2, default=str))
        return

    total = result.get("total", 0)
    present = result.get("present", 0)
    missing = result.get("missing", 0)
    format_issues = result.get("format_issues", 0)
    type_issues = result.get("type_issues", 0)

    print()
    print(f"  {blue('envcheck')} — 环境变量检查报告")
    print(f"  {'='*40}")
    print(f"  来源: {result.get('source', '未知')}")
    print()

    if result.get("errors"):
        for err in result["errors"]:
            print(f"  {red('⚠')} 解析错误 (行 {err[0]}): {err[1]}")
        print()

    if missing > 0:
        print(f"  {red('✗')} 缺失变量 ({missing}):")
        for v in result.get("missing_vars", []):
            print(f"    • {v}")
        print()

    if format_issues > 0:
        print(f"  {yellow('⚠')} 格式问题 ({format_issues}):")
        for v in result.get("format_issues_list", []):
            print(f"    • {v['var']} = {v['value'][:40]} — {v['hint']}")
        print()

    if type_issues > 0:
        print(f"  {yellow('⚠')} 类型转换问题 ({type_issues}):")
        for v in result.get("type_issues_list", []):
            print(f"    • {v['var']} = {v['value'][:40]} — {v['hint']}")
        print()

    print(f"  {green('✓')} 已定义: {present}/{total}")

    if result.get("has_defaults"):
        overridden = result.get("overridden_defaults", 0)
        print(f"  {blue('ℹ')} 覆盖默认值: {overridden}")

    # 总体评分
    score = result.get("score", 100)
    if score >= 90:
        c = green
    elif score >= 70:
        c = yellow
    else:
        c = red
    print(f"  {c('★')} 健康度: {c(str(score))}/100")
    print()


def check(args):
    """主检查逻辑"""
    # 确定检查范围
    if args.file:
        files = [args.file]
    else:
        files = find_env_files()

    if not files:
        result = {
            "status": "error",
            "message": "未找到 .env 文件",
            "total": 0, "present": 0, "missing": 0,
            "format_issues": 0, "type_issues": 0,
            "score": 0,
            "source": "无文件",
        }
        print_report(result, args.json)
        return 1

    # 处理每个文件
    all_vars = {}
    all_errors = []
    source_file = files[0]

    for f in files:
        vars_dict, errs = parse_env_file(f)
        if vars_dict is not None:
            all_vars.update(vars_dict)
        all_errors.extend([(f, e[0], e[1]) for e in errs])
        if source_file == files[0] and vars_dict is not None:
            source_file = f

    # 必需变量检查
    required_vars = list(args.require) if args.require else []
    if args.template:
        tmpl_vars, _ = parse_env_file(args.template)
        if tmpl_vars is not None:
            required_vars = list(tmpl_vars.keys())

    # 如果没有指定必需变量，把所有变量视为可选
    if not required_vars:
        required_vars = list(all_vars.keys())

    missing_vars = [v for v in required_vars if v not in all_vars]

    # 格式验证
    format_issues_list = []
    type_issues_list = []
    format_count = 0
    type_count = 0

    for var_name in all_vars:
        val = all_vars[var_name]

        # 按变量名推断格式
        hints = _infer_format_checks(var_name, val)
        for fmt in hints:
            ok, hint = validate_format(val, fmt)
            if not ok:
                format_issues_list.append({
                    "var": var_name, "value": val,
                    "check": fmt, "hint": hint
                })
                format_count += 1

        # 类型转换检查
        type_hints = _infer_type_checks(var_name, val)
        for t in type_hints:
            _, ok, hint = cast_type(val, t)
            if not ok:
                type_issues_list.append({
                    "var": var_name, "value": val,
                    "target": t, "hint": hint
                })
                type_count += 1

    # 默认值覆盖
    overridden = 0
    has_defaults = False
    if args.template:
        has_defaults = True
        tmpl_vars, _ = parse_env_file(args.template)
        if tmpl_vars:
            for k in tmpl_vars:
                if k in all_vars and all_vars[k] != tmpl_vars[k]:
                    overridden += 1

    # 评分
    checks = len(required_vars) + format_count + type_count
    passed = len(required_vars) - len(missing_vars) + (format_count + type_count) * 0
    score = max(0, int((passed / max(checks, 1)) * 100 - len(missing_vars) * 10))

    result = {
        "status": "warning" if (missing_vars or format_issues_list)
                  else "ok",
        "source": str(source_file),
        "total": len(required_vars) if required_vars else len(all_vars),
        "present": len(all_vars),
        "missing": len(missing_vars),
        "missing_vars": missing_vars,
        "format_issues": format_count,
        "format_issues_list": format_issues_list,
        "type_issues": type_count,
        "type_issues_list": type_issues_list,
        "has_defaults": has_defaults,
        "overridden_defaults": overridden,
        "score": score,
        "errors": all_errors,
    }

    print_report(result, args.json)
    return 0 if result["status"] == "ok" else 1


def _infer_format_checks(var_name, value):
    """根据变量名推断应该检查什么格式"""
    name_upper = var_name.upper()
    checks = []

    # 端口
    if ("PORT" in name_upper or "PORT_" in name_upper or
        name_upper.endswith("_PORT")):
        checks.append("port")

    # URL
    if ("URL" in name_upper or "URI" in name_upper or
        "ENDPOINT" in name_upper or "HOST" in name_upper):
        checks.append("url")

    # Email
    if "EMAIL" in name_upper or "MAIL" in name_upper:
        checks.append("email")

    # 路径
    if ("PATH" in name_upper or "DIR" in name_upper or
        "FILE" in name_upper or "HOME" in name_upper):
        checks.append("path")

    # 颜色
    if "COLOR" in name_upper or "COLOUR" in name_upper:
        checks.append("hex_color")

    # UUID
    if "UUID" in name_upper or "GUID" in name_upper:
        checks.append("uuid")

    # 版本号
    if "VERSION" in name_upper:
        checks.append("semver")

    return checks


def _infer_type_checks(var_name, value):
    """根据变量名推断类型转换"""
    name_upper = var_name.upper()
    checks = []

    if ("COUNT" in name_upper or "LIMIT" in name_upper or
        "SIZE" in name_upper or "MAX" in name_upper or
        "MIN" in name_upper or "TTL" in name_upper or
        "TIMEOUT" in name_upper or "PORT" in name_upper):
        checks.append("int")

    if ("ENABLED" in name_upper or "DEBUG" in name_upper or
        "DISABLE" in name_upper or "DRY_RUN" in name_upper or
        "VERBOSE" in name_upper):
        checks.append("bool")

    if ("LIST" in name_upper or "ARGS" in name_upper or
        "OPTIONS" in name_upper or "ITEMS" in name_upper):
        checks.append("list")

    return checks


def main():
    parser = argparse.ArgumentParser(
        description="环境变量验证器 — 检查 .env 文件中的变量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  envcheck                         扫描当前目录的 .env
  envcheck .env.production         指定文件
  envcheck --require DB_HOST DB_PORT  指定必需变量
  envcheck --template .env.example   对比模板
  envcheck --json                   JSON 输出
        """,
    )
    parser.add_argument("file", nargs="?", help="指定 .env 文件路径")
    parser.add_argument("--require", "-r", nargs="+", help="必需的变量名列表")
    parser.add_argument("--template", "-t", help="参考模板文件")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    try:
        sys.exit(check(args))
    except KeyboardInterrupt:
        print()
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
