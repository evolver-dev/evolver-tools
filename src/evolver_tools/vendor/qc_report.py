#!/usr/bin/env python3
"""qc_report — 检验报告生成器 (QC Test Report)

电池回收/湿法冶金化验室专用。从 qc_calc 的结果数据生成格式化检验报告，
包含样品信息、检测结果、规格比对、判定结论。

用法:
  qc_report                   交互模式（一步步填入数据）
  qc_report --from-data      从 JSON 数据文件生成报告
"""

import sys
import json
from datetime import datetime

# ========== 模板 ==========

def generate_report(data):
    """生成格式化的检验报告。"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    lines = []
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
    
    # 统计合格率
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


def interactive_mode():
    """交互式生成检验报告。"""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║   检验报告生成器  v1.0                    ║")
    print("║   寒锐钴业（赣州）化验室专用               ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    data = {}
    
    try:
        # 样品信息
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
        
        # 检测结果
        print()
        print("--- 检测结果 ---")
        print("输入检测项目（回车结束）:")
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
        return
    
    print()
    print(generate_report(data))
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    
    interactive_mode()


# ========== 自动注册 ==========
TOOL_META = {
    "name": "qc_report",
    "func": "main",
    "desc": "检验报告生成器 — 寒锐钴业化验室格式",
}

if __name__ == "__main__":
    main()
