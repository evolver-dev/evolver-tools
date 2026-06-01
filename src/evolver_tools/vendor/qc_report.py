#!/usr/bin/env python3
"""qc-report — 检验报告生成器 (QC Test Report) v2.0

电池回收/湿法冶金化验室专用。生成格式化检验报告，
包含样品信息、检测结果、规格比对、判定结论。

用法:
  qc-report                     交互模式
  qc-report --demo              演示报告
  qc-report --json data.json    从JSON输入
  qc-report --certificate      证书模式（简洁版）
  qc-report --template 1       预设模板（标准/精简/证书）
  qc-report --format html      输出HTML格式
  qc-report --output report.txt 输出到文件
  qc-report --format csv       输出为CSV格式
  qc-report --version          显示版本号
"""

import sys
import json
import csv
import io
from datetime import datetime

VERSION = "2.0.0"

# ========== 报告生成 ==========

def generate_report(data, template="standard"):
    """生成格式化检验报告。"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    lines = []
    
    if template == "certificate":
        # 简洁证书模式
        lines.append("╔══════════════════════════════════════════════════════════╗")
        lines.append("║              检 验 证 书                                ║")
        lines.append("╚══════════════════════════════════════════════════════════╝")
        lines.append("")
        default_id = f"C{now.strftime('%Y%m%d%H%M%S')}"
        lines.append(f"  证书编号: {data.get('report_id', default_id)}")
        lines.append(f"  签发日期: {data.get('report_date', date_str)}")
        lines.append("")
        lines.append(f"  兹证明样品 {data.get('sample_id', '')} ({data.get('sample_name', '')})")
        results = data.get("results", [])
        if results:
            for r in results:
                lines.append(f"    {r.get('item','')} = {r.get('value','')} {r.get('unit','')}")
        lines.append("")
        lines.append(f"  {'✅ 合格' if all(r.get('judge') == '合格' for r in results) else '❌ 不合格'}"
                     if results else "  （待判定）")
        lines.append("")
        lines.append("  ── 以下空白 ──")
    else:
        # 标准模式
        lines.append("╔══════════════════════════════════════════════════════════╗")
        lines.append("║              寒锐钴业（赣州）化验室                       ║")
        lines.append("║              检 验 报 告 单                              ║")
        lines.append("╚══════════════════════════════════════════════════════════╝")
        lines.append("")
        default_id = f"R{now.strftime('%Y%m%d%H%M%S')}"
        lines.append(f"  报告编号: {data.get('report_id', default_id)}")
        lines.append(f"  报告日期: {data.get('report_date', date_str)}")
        lines.append(f"  共 {data.get('total_pages', 1)} 页  第 1 页")
        lines.append("")
        lines.append("┌──────────────────────────────────────────────────────────┐")
        lines.append("│  样品信息                                               │")
        lines.append("├──────────────────────────────────────────────────────────┤")
        lines.append(f"│  样品编号: {data.get('sample_id', ''):<46s}│")
        lines.append(f"│  样品名称: {data.get('sample_name', ''):<46s}│")
        lines.append(f"│  样品批号: {data.get('batch_no', ''):<46s}│")
        lines.append(f"│  来样单位: {data.get('workshop', ''):<46s}│")
        lines.append(f"│  采样日期: {data.get('sampling_date', ''):<46s}│")
        lines.append(f"│  样品状态: {data.get('sample_state', '液体'):<46s}│")
        lines.append(f"│  检验类别: {data.get('test_type', '常规检测'):<46s}│")
        lines.append("└──────────────────────────────────────────────────────────┘")
        lines.append("")
        lines.append("┌──────────────────────────────────────────────────────────┐")
        lines.append("│  检测结果                                               │")
        lines.append("├──────┬────────┬────────┬──────────┬──────────┬──────────┤")
        lines.append("│ 序号 │ 检测项目 │ 单位  │ 标准要求 │ 检测结果 │ 单项判定 │")
        lines.append("├──────┼────────┼────────┼──────────┼──────────┼──────────┤")

        results = data.get("results", [])
        if results:
            for i, r in enumerate(results, 1):
                item = r.get("item", "")
                unit = r.get("unit", "")
                spec = r.get("spec", "")
                value = r.get("value", "")
                judge = r.get("judge", "")
                lines.append(f"│ {i:^4d} │ {item:<6s} │ {unit:<6s} │ {spec:<8s} │ {str(value):<8s} │ {judge:<6s} │")
        else:
            lines.append("│  -   │   -     │   -    │    -      │    -      │    -    │")

        lines.append("├──────┴────────┴────────┴──────────┴──────────┴──────────┤")

        if results:
            passed = sum(1 for r in results if r.get("judge") == "合格")
            total = len(results)
            pct = passed / total * 100 if total > 0 else 0
            lines.append(f"│  合格率: {passed}/{total} ({pct:.1f}%){' ' * 30}│")
        else:
            lines.append(f"│  合格率: --/-- (--%){' ' * 36}│")

        lines.append("└──────────────────────────────────────────────────────────┘")
        lines.append("")
        lines.append("┌──────────────────────────────────────────────────────────┐")
        lines.append("│  结论                                                   │")
        lines.append("├──────────────────────────────────────────────────────────┤")

        if results:
            all_passed = all(r.get("judge") == "合格" for r in results)
            if all_passed:
                conclusion = "经检验，该样品所检项目符合标准要求，判定为合格。"
            else:
                failed_items = [r.get("item", "") for r in results if r.get("judge") != "合格"]
                conclusion = f"经检验，{', '.join(failed_items)}项目不符合标准要求，判定为不合格。"
        else:
            conclusion = "（待判定）"

        lines.append(f"│  {conclusion:<54s}│")
        lines.append("└──────────────────────────────────────────────────────────┘")
        lines.append("")
        lines.append("  ── 以下空白 ──")
        lines.append("")
        lines.append("  ┌──────────────────────┬──────────────────────┐")
        lines.append("  │  检验人:              │  复核人:              │")
        lines.append(f"  │  {data.get('tester', ''):<20s}│  {data.get('reviewer', ''):<20s}│")
        lines.append("  │  日期: ________       │  日期: ________       │")
        lines.append("  └──────────────────────┴──────────────────────┘")

    return "\n".join(lines)


def generate_html(data):
    """生成HTML格式报告。"""
    results = data.get("results", [])
    total = len(results)
    passed = sum(1 for r in results if r.get("judge") == "合格") if results else 0
    pct = passed / total * 100 if total > 0 else 0
    all_passed = all(r.get("judge") == "合格" for r in results) if results else True

    rows = ""
    if results:
        for i, r in enumerate(results, 1):
            rows += f"""    <tr>
      <td>{i}</td>
      <td>{r.get('item', '')}</td>
      <td>{r.get('unit', '')}</td>
      <td>{r.get('spec', '')}</td>
      <td>{r.get('value', '')}</td>
      <td style="color:{'green' if r.get('judge') == '合格' else 'red'};font-weight:bold">{r.get('judge', '')}</td>
    </tr>
"""

    now = datetime.now()
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>检验报告 - {data.get('report_id', '')}</title>
<style>
  body {{ font-family: 'Microsoft YaHei', 'SimSun', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }}
  h1 {{ text-align: center; color: #1a1a2e; border-bottom: 3px solid #1a1a2e; padding-bottom: 10px; }}
  h2 {{ color: #1a1a2e; margin-top: 30px; }}
  .company {{ text-align: center; font-size: 14px; color: #666; margin-bottom: 30px; }}
  .info-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  .info-table td {{ padding: 6px 10px; border: 1px solid #ddd; }}
  .info-table td:first-child {{ font-weight: bold; background: #f5f5f5; width: 120px; }}
  .result-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  .result-table th {{ background: #1a1a2e; color: white; padding: 8px; text-align: center; }}
  .result-table td {{ padding: 8px; text-align: center; border: 1px solid #ddd; }}
  .result-table tr:nth-child(even) {{ background: #f9f9f9; }}
  .conclusion {{ background: #f0f8ff; border: 2px solid #1a1a2e; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; font-size: 16px; }}
  .pass {{ color: green; font-weight: bold; }}
  .fail {{ color: red; font-weight: bold; }}
  .signature {{ display: flex; justify-content: space-between; margin-top: 40px; }}
  .signature div {{ text-align: center; }}
  hr {{ border: none; border-top: 1px dashed #ccc; margin: 20px 0; }}
</style>
</head>
<body>
<h1>检验报告</h1>
<div class="company">寒锐钴业（赣州）化验室</div>

<table class="info-table">
  <tr><td>报告编号</td><td>{data.get('report_id', '')}</td></tr>
  <tr><td>报告日期</td><td>{data.get('report_date', now.strftime('%Y-%m-%d'))}</td></tr>
  <tr><td>样品编号</td><td>{data.get('sample_id', '')}</td></tr>
  <tr><td>样品名称</td><td>{data.get('sample_name', '')}</td></tr>
  <tr><td>样品批号</td><td>{data.get('batch_no', '')}</td></tr>
  <tr><td>来样单位</td><td>{data.get('workshop', '')}</td></tr>
  <tr><td>采样日期</td><td>{data.get('sampling_date', '')}</td></tr>
  <tr><td>样品状态</td><td>{data.get('sample_state', '液体')}</td></tr>
  <tr><td>检验类别</td><td>{data.get('test_type', '常规检测')}</td></tr>
</table>

<h2>检测结果</h2>
<table class="result-table">
  <thead><tr><th>序号</th><th>检测项目</th><th>单位</th><th>标准要求</th><th>检测结果</th><th>判定</th></tr></thead>
  <tbody>
{rows}
  </tbody>
</table>

<p>合格率: <span class="{'pass' if pct == 100 else 'fail'}">{passed}/{total} ({pct:.1f}%)</span></p>

<div class="conclusion">
  {'✅ 经检验，该样品所检项目符合标准要求，判定为合格。' if all_passed else '❌ 部分项目不符合标准要求。'}
</div>

<hr>

<div class="signature">
  <div>检验人: {data.get('tester', '________')}<br>日期: ________</div>
  <div>复核人: {data.get('reviewer', '________')}<br>日期: ________</div>
</div>
</body>
</html>"""
    return html


def generate_csv(data):
    """生成CSV格式检测结果。"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["报告编号", "报告日期", "样品编号", "样品名称", "批号", "来样单位",
                      "检测项目", "单位", "标准要求", "检测结果", "判定", "合格率"])
    results = data.get("results", [])
    total = len(results)
    passed = sum(1 for r in results if r.get("judge") == "合格") if results else 0
    pct = f"{passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "--/-- (--%)"

    if results:
        for r in results:
            writer.writerow([
                data.get("report_id", ""),
                data.get("report_date", ""),
                data.get("sample_id", ""),
                data.get("sample_name", ""),
                data.get("batch_no", ""),
                data.get("workshop", ""),
                r.get("item", ""),
                r.get("unit", ""),
                r.get("spec", ""),
                r.get("value", ""),
                r.get("judge", ""),
                pct
            ])
    else:
        writer.writerow([data.get("report_id", ""), data.get("report_date", ""),
                         data.get("sample_id", ""), data.get("sample_name", ""),
                         data.get("batch_no", ""), data.get("workshop", ""),
                         "", "", "", "", "", pct])
    return output.getvalue()


# ========== 演示数据 ==========

TEMPLATES = {
    1: {  # 标准
        "report_id": "R20260531-001",
        "report_date": "2026-05-31",
        "sample_id": "S20260531-001",
        "sample_name": "浸出液（黑粉）",
        "batch_no": "BATCH-20260530",
        "workshop": "105 浸出车间",
        "sampling_date": "2026-05-30 09:00",
        "sample_state": "液体",
        "test_type": "常规检测",
        "tester": "张三",
        "reviewer": "李四",
        "total_pages": 1,
        "results": [
            {"item": "Co", "unit": "g/L", "spec": "80-110", "value": "85.25", "judge": "合格"},
            {"item": "Ni", "unit": "g/L", "spec": "≤1.0", "value": "0.85", "judge": "合格"},
            {"item": "Cu", "unit": "g/L", "spec": "≤0.5", "value": "0.12", "judge": "合格"},
            {"item": "Mn", "unit": "g/L", "spec": "≤5.0", "value": "2.34", "judge": "合格"},
            {"item": "Fe", "unit": "g/L", "spec": "≤0.1", "value": "0.05", "judge": "合格"},
            {"item": "pH", "unit": "", "spec": "1.5-2.5", "value": "2.1", "judge": "合格"},
        ]
    },
    2: {  # 精简
        "report_id": "R20260531-002",
        "report_date": "2026-05-31",
        "sample_id": "S20260531-002",
        "sample_name": "萃取液",
        "batch_no": "BATCH-20260530",
        "workshop": "102 萃取车间",
        "sample_state": "液体",
        "test_type": "常规检测",
        "tester": "张三",
        "reviewer": "李四",
        "results": [
            {"item": "Co", "unit": "g/L", "spec": "80-110", "value": "92.15", "judge": "合格"},
            {"item": "Ni", "unit": "g/L", "spec": "≤1.0", "value": "0.45", "judge": "合格"},
            {"item": "pH", "unit": "", "spec": "1.5-2.5", "value": "1.8", "judge": "合格"},
        ]
    },
    3: {  # 证书
        "report_id": "C20260531-001",
        "report_date": "2026-05-31",
        "sample_id": "S20260531-003",
        "sample_name": "硫酸钴成品",
        "batch_no": "BATCH-20260530",
        "workshop": "103 钴盐车间",
        "sample_state": "固体",
        "test_type": "出厂检验",
        "tester": "张三",
        "reviewer": "李四",
        "results": [
            {"item": "Co", "unit": "%", "spec": "≥20.0", "value": "20.5", "judge": "合格"},
            {"item": "Ni", "unit": "%", "spec": "≤0.05", "value": "0.02", "judge": "合格"},
            {"item": "Cu", "unit": "%", "spec": "≤0.01", "value": "0.005", "judge": "合格"},
            {"item": "Fe", "unit": "%", "spec": "≤0.01", "value": "0.003", "judge": "合格"},
            {"item": "Ca", "unit": "%", "spec": "≤0.02", "value": "0.01", "judge": "合格"},
            {"item": "Mg", "unit": "%", "spec": "≤0.02", "value": "0.008", "judge": "合格"},
        ]
    }
}


def demo_report():
    """生成演示报告。"""
    return generate_report(TEMPLATES[1])


# ========== 交互模式 ==========

def interactive_mode():
    """交互式生成检验报告。"""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║   检验报告生成器  v2.0                    ║")
    print("║   电池回收化验室专用                      ║")
    print("╚══════════════════════════════════════════╝")
    print()

    data = {}

    try:
        print("--- 样品信息 ---")
        data["sample_id"] = input("样品编号: ").strip()
        data["sample_name"] = input("样品名称: ").strip()
        data["batch_no"] = input("批号: ").strip()
        data["workshop"] = input("来样单位/车间: ").strip()
        data["sampling_date"] = input("采样日期: ").strip()
        data["sample_state"] = input("样品状态 [液体]: ").strip() or "液体"
        data["test_type"] = input("检验类别 [常规检测]: ").strip() or "常规检测"
        data["tester"] = input("检验人: ").strip()
        data["reviewer"] = input("复核人: ").strip()

        print()
        print("--- 检测结果 ---")
        print("输入检测项目（空行结束）:")
        print("格式: 项目名 单位 标准要求 检测值 判定(合格/不合格)")
        print("示例: Co g/L 80-110 85.2 合格")
        print()

        data["results"] = []
        while True:
            line = input("  > ").strip()
            if not line:
                break
            parts = line.split()
            if len(parts) >= 3:
                item = parts[0]
                unit = parts[1] if len(parts) > 1 else ""
                spec = parts[2] if len(parts) > 2 else ""
                value = parts[3] if len(parts) > 3 else ""
                judge = parts[4] if len(parts) > 4 else ""

                data["results"].append({
                    "item": item, "unit": unit, "spec": spec,
                    "value": value, "judge": judge
                })
                print(f"    ✓ 已添加: {item}")

    except (EOFError, KeyboardInterrupt):
        print("\n\n取消。")
        return None

    return data


# ========== CLI 入口 ==========

def main():
    args = sys.argv[1:]

    if "--version" in args:
        print(f"qc-report v{VERSION}")
        return

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    # 解析参数
    output_file = None
    fmt = "text"
    template = "standard"
    data = None

    # 提取 --output
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_file = args[idx + 1]

    # 提取 --format
    if "--format" in args:
        idx = args.index("--format")
        if idx + 1 < len(args):
            fmt = args[idx + 1].lower()

    # 提取 --template
    if "--template" in args:
        idx = args.index("--template")
        if idx + 1 < len(args):
            t = int(args[idx + 1])
            if t in TEMPLATES:
                data = TEMPLATES[t].copy()
                template = "standard"

    # 提取 --json
    if "--json" in args:
        idx = args.index("--json")
        if idx + 1 < len(args):
            try:
                with open(args[idx + 1], "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error: 读取JSON失败 - {e}", file=sys.stderr)
                return

    # 提取 --certificate
    if "--certificate" in args:
        template = "certificate"

    # 执行
    if args[0] == "--demo":
        data = TEMPLATES[1].copy()
    elif args[0] == "--json":
        pass  # already handled above
    elif args[0] == "--template":
        pass  # already handled above
    elif args[0] == "--certificate":
        if data is None:
            data = TEMPLATES[3].copy()
    elif args[0] == "--format":
        # interactive with format override
        pass
    elif args[0] == "--output":
        # interactive with output
        pass
    else:
        data = interactive_mode()
        if data is None:
            return

    # 如果还没有数据，用默认
    if data is None:
        data = TEMPLATES[1].copy()

    # 生成输出
    if fmt == "html":
        output = generate_html(data)
    elif fmt == "csv":
        output = generate_csv(data)
    else:
        output = generate_report(data, template)

    # 输出
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ 已保存到: {output_file}")
    else:
        print()
        print(output)


TOOL_META = {
    "name": "qc-report",
    "func": "main",
    "desc": "检验报告生成器 v2.0 -- Text/HTML/CSV/证书",
}

if __name__ == "__main__":
    main()
