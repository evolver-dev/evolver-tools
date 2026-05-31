#!/usr/bin/env python3
"""qc_sample — 样品送检单生成器 (Sample Submission Form)

电池回收/湿法冶金化验室专用。生成格式化的样品送检单，
包含样品信息、检测项目、规格要求、送检信息等。

用法:
  qc_sample                   交互模式
  qc_sample --quick          快速生成（问答式）
"""

import sys
from datetime import datetime

# ========== 车间列表 ==========

WORKSHOPS = [
    "102 萃取车间",
    "103 钴盐车间", 
    "105 浸出车间",
    "106 车间",
    "109 电钴车间",
    "301 四钴车间",
    "2108 车间",
    "水处理车间",
    "原料库",
    "其他",
]

PROCESS_LINES = {
    "102 萃取车间": ["P204一线", "P204二线", "P507一线", "P507二线", "CY272", "综合"],
    "103 钴盐车间": ["硫酸钴结晶", "氯化钴制备", "碳酸钴制备", "溶解"],
    "105 浸出车间": ["一段浸出", "二段浸出", "浓密", "压滤"],
    "106 车间": ["进料", "反应", "出料"],
    "109 电钴车间": ["电解液", "阳极液", "阴极液", "成品"],
    "301 四钴车间": ["前驱体", "煅烧", "粉碎", "包装"],
    "2108 车间": ["进料", "反应"],
    "水处理车间": ["进水", "出水", "中间池"],
    "原料库": ["黑粉", "钴中间品", "辅料"],
    "其他": ["其他"],
}

TEST_ITEMS = [
    ("Co", "钴含量", "g/L", "主元素"),
    ("Ni", "镍含量", "g/L", "主元素/杂质"),
    ("Cu", "铜含量", "g/L", "杂质"),
    ("Mn", "锰含量", "g/L", "杂质"),
    ("Fe", "铁含量", "g/L", "杂质"),
    ("Ca", "钙含量", "g/L", "杂质"),
    ("Mg", "镁含量", "g/L", "杂质"),
    ("Zn", "锌含量", "g/L", "杂质"),
    ("pH", "pH值", "", "酸碱度"),
    ("N", "酸度", "N", "酸度"),
    ("SC", "固含量", "%", "悬浮物"),
    ("Density", "密度", "g/mL", "物理性质"),
    ("CL", "氯根", "g/L", "杂质"),
    ("SO4", "硫酸根", "g/L", "杂质"),
]


def generate_form(data):
    """生成格式化的送检单。"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    serial = data.get("serial", f"S{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}")
    
    lines = []
    lines.append("═" * 60)
    lines.append("  寒锐钴业（赣州）—— 化验室样品送检单")
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"  送检编号: {serial}")
    lines.append(f"  送检日期: {date_str}   时间: {time_str}")
    lines.append(f"  送检人: {data.get('sender', '')}")
    lines.append("")
    lines.append("─" * 60)
    lines.append("  样品信息")
    lines.append("─" * 60)
    lines.append(f"  样品编号: {data.get('sample_id', '')}")
    lines.append(f"  样品名称: {data.get('sample_name', '')}")
    lines.append(f"  样品状态: {data.get('sample_state', '液体')}")
    lines.append(f"  来源车间: {data.get('workshop', '')}")
    lines.append(f"  工艺环节: {data.get('process', '')}")
    lines.append(f"  取样点位: {data.get('sampling_point', '')}")
    lines.append(f"  取样时间: {data.get('sampling_time', '')}")
    lines.append("")
    lines.append("─" * 60)
    lines.append("  检测项目")
    lines.append("─" * 60)
    
    items = data.get("items", [])
    if items:
        lines.append(f"  {'检测项目':<8} {'元素':<6} {'单位':<8} {'规格要求':<20} {'备注'}")
        lines.append("  " + "-" * 54)
        for item in items:
            elem = item.get("element", "")
            cn = item.get("name", "")
            unit = item.get("unit", "")
            spec = item.get("spec", "")
            note = item.get("note", "")
            lines.append(f"  {cn:<8} {elem:<6} {unit:<8} {spec:<20} {note}")
    else:
        lines.append("  (见附页)")
    
    lines.append("")
    lines.append("─" * 60)
    lines.append("  判定标准")
    lines.append("─" * 60)
    lines.append(f"  标准依据: {data.get('standard_ref', 'QC工程图')}")
    lines.append("")
    
    lines.append("─" * 60)
    lines.append("  检测结果")
    lines.append("─" * 60)
    if data.get("results"):
        for r in data["results"]:
            elem = r.get("element", "")
            val = r.get("value", "")
            unit = r.get("unit", "")
            judge = r.get("judge", "")
            lines.append(f"  {elem:<6} {str(val):<12} {unit:<8} {judge}")
    else:
        lines.append("  (待填写)")
    
    lines.append("")
    lines.append("─" * 60)
    lines.append(f"  检验人: ________    复核人: ________")
    lines.append(f"  报告日期: ________")
    lines.append("═" * 60)
    
    return "\n".join(lines)


def interactive_mode():
    """交互式生成送检单。"""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║   样品送检单生成器  v1.0                 ║")
    print("║   寒锐钴业（赣州）化验室专用              ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    data = {}
    
    try:
        # 样品信息
        print("--- 样品信息 ---")
        data["sample_id"] = input("样品编号: ").strip()
        data["sample_name"] = input("样品名称: ").strip()
        data["sample_state"] = input("样品状态 (液体/固体/气体) [液体]: ").strip() or "液体"
        data["sampling_time"] = input("取样时间 (如 2026-05-31 08:00): ").strip()
        data["sender"] = input("送检人: ").strip()
        
        # 车间选择
        print()
        print("来源车间:")
        for i, w in enumerate(WORKSHOPS, 1):
            print(f"  {i}) {w}")
        ws_idx = int(input("选择车间编号: ").strip()) - 1
        data["workshop"] = WORKSHOPS[ws_idx]
        
        # 工艺环节
        processes = PROCESS_LINES.get(data["workshop"], ["其他"])
        print(f"\n工艺环节 ({data['workshop']}):")
        for i, p in enumerate(processes, 1):
            print(f"  {i}) {p}")
        pr_idx = int(input("选择工艺环节编号: ").strip()) - 1
        data["process"] = processes[pr_idx]
        
        data["sampling_point"] = input("取样点位: ").strip()
        
        # 检测项目
        print()
        print("--- 检测项目 ---")
        print("可选检测项目:")
        for i, (elem, name, unit, note) in enumerate(TEST_ITEMS, 1):
            print(f"  {i:2d}) {name:<8} ({elem:<4})  {unit:<6}  {note}")
        
        selected = input("\n选择项目编号（逗号分隔，如 1,2,3）: ").strip()
        selected_idx = [int(x.strip()) - 1 for x in selected.split(",") if x.strip()]
        
        data["items"] = []
        for idx in selected_idx:
            if 0 <= idx < len(TEST_ITEMS):
                elem, name, unit, note = TEST_ITEMS[idx]
                spec = input(f"  {name} 规格要求 (如 80-110 g/L, 留空跳过): ").strip()
                data["items"].append({
                    "element": elem, "name": name, "unit": unit,
                    "spec": spec, "note": note
                })
        
        # 标准依据
        data["standard_ref"] = input("\n标准依据 [QC工程图]: ").strip() or "QC工程图"
        
        # 可选填写结果
        has_results = input("\n是否填写检测结果? (y/N): ").strip().lower()
        data["results"] = []
        if has_results in ("y", "yes"):
            for item in data["items"]:
                val = input(f"  {item['name']} ({item['element']}) 结果: ").strip()
                if val:
                    judge = input(f"   判定 (合格/不合格): ").strip()
                    data["results"].append({
                        "element": item["element"],
                        "value": val,
                        "unit": item["unit"],
                        "judge": judge
                    })
        
    except (EOFError, KeyboardInterrupt):
        print("\n\n取消。")
        return
    except ValueError:
        print("\n输入无效。")
        return
    
    print()
    print(generate_form(data))
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    
    interactive_mode()


# ========== 自动注册 ==========
TOOL_META = {
    "name": "qc_sample",
    "func": "main",
    "desc": "样品送检单生成器 — 寒锐钴业化验室专用格式",
}

if __name__ == "__main__":
    main()
