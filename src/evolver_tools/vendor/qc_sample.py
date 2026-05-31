#!/usr/bin/env python3
"""qc-sample — 样品送检单生成器 (Sample Submission Form) v2.0

电池回收/湿法冶金化验室专用。生成格式化的样品送检单，
包含样品信息、检测项目、规格要求、送检信息等。

用法:
  qc-sample                       交互模式（一步步填入数据）
  qc-sample --quick               快速模式（只问必填项）
  qc-sample --template <1|2|3>    使用预设模板快速生成
  qc-sample --batch <csv_file>    从CSV模板批量生成送检单
  qc-sample --output <file>       输出到文件
  qc-sample --format <text|csv>   输出格式（text=送检单, csv=LIMS导入格式）
  qc-sample --version             显示版本号
"""

import argparse
import csv
import sys
from datetime import datetime

VERSION = "2.0"

# ========== 常量 ==========

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

# ========== 预设模板 ==========

TEMPLATES = {
    1: {
        "name": "浸出液",
        "items": ["Co", "Ni", "Cu", "Mn", "Fe", "pH"],
        "sample_state": "液体",
        "workshop": "105 浸出车间",
        "process": "一段浸出",
    },
    2: {
        "name": "萃取液",
        "items": ["Co", "Ni", "pH"],
        "sample_state": "液体",
        "workshop": "102 萃取车间",
        "process": "P204一线",
    },
    3: {
        "name": "成品钴盐",
        "items": ["Co", "Ni", "Cu", "Fe", "Ca", "Mg"],
        "sample_state": "固体",
        "workshop": "103 钴盐车间",
        "process": "硫酸钴结晶",
    },
}

# 查找元素在 TEST_ITEMS 中的索引
ELEMENT_INDEX = {elem: i for i, (elem, _, _, _) in enumerate(TEST_ITEMS)}


# ========== 输出生成 ==========

def generate_form(data):
    """生成格式化的送检单（text格式）。"""
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
            lines.append(f"  {item.get('name',''):<8} {item.get('element',''):<6} "
                         f"{item.get('unit',''):<8} {item.get('spec',''):<20} {item.get('note','')}")
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
            lines.append(f"  {r.get('element',''):<6} {str(r.get('value','')):<12} "
                         f"{r.get('unit',''):<8} {r.get('judge','')}")
    else:
        lines.append("  (待填写)")

    lines.append("")
    lines.append("─" * 60)
    lines.append(f"  检验人: ________    复核人: ________")
    lines.append(f"  报告日期: ________")
    lines.append("═" * 60)

    return "\n".join(lines)


def generate_csv(data):
    """生成CSV格式数据（用于LIMS系统导入）。

    输出字段: sample_id, sample_name, workshop, process, element, name, unit, note, spec, value, judge
    """
    now = datetime.now()
    serial = data.get("serial", f"S{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}")
    sample_id = data.get("sample_id", serial)
    sample_name = data.get("sample_name", "")
    workshop = data.get("workshop", "")
    process = data.get("process", "")

    rows = []
    items = data.get("items", [])
    results_map = {}
    for r in data.get("results", []):
        results_map[r.get("element")] = r

    for item in items:
        elem = item.get("element", "")
        r = results_map.get(elem, {})
        rows.append({
            "sample_id": sample_id,
            "sample_name": sample_name,
            "workshop": workshop,
            "process": process,
            "element": elem,
            "name": item.get("name", ""),
            "unit": item.get("unit", ""),
            "note": item.get("note", ""),
            "spec": item.get("spec", ""),
            "value": r.get("value", ""),
            "judge": r.get("judge", ""),
        })

    return rows


def write_output(data, fmt, output_file=None):
    """根据格式输出数据。"""
    if fmt == "text":
        output = generate_form(data)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"送检单已保存至: {output_file}")
        else:
            print()
            print(output)
            print()

    elif fmt == "csv":
        rows = generate_csv(data)
        if not rows:
            print("警告: 没有检测项目，CSV输出为空。", file=sys.stderr)
            return

        fieldnames = ["sample_id", "sample_name", "workshop", "process",
                      "element", "name", "unit", "note", "spec", "value", "judge"]

        if output_file:
            with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"CSV已保存至: {output_file}")
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


# ========== 交互模式 ==========

def prompt_int(prompt_text, min_val, max_val, default=None):
    """提示输入整数，带范围校验。"""
    while True:
        val = input(prompt_text).strip()
        if not val and default is not None:
            return default
        try:
            n = int(val)
            if min_val <= n <= max_val:
                return n
            print(f"  请输入 {min_val}-{max_val} 之间的数字。")
        except ValueError:
            print("  请输入有效数字。")


def prompt_select(options, prompt_text="请选择: "):
    """打印编号列表并让用户选择一项。"""
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    idx = prompt_int(prompt_text, 1, len(options))
    return options[idx - 1], idx


def interactive_mode(quick=False):
    """交互式生成送检单。

    quick=True: 只问必填项（样品编号、名称、车间、工艺、检测项目），其余用默认值。
    """
    print()
    print("╔══════════════════════════════════════════╗")
    print(f"║   样品送检单生成器  v{VERSION}                 ║")
    print("║   电池回收化验室专用                      ║")
    print("╚══════════════════════════════════════════╝")
    if quick:
        print("  快速模式 — 仅填写必填项")
    print()

    data = {}

    try:
        # === 样品信息 ===
        print("--- 样品信息 ---")
        data["sample_id"] = input("样品编号: ").strip()
        data["sample_name"] = input("样品名称: ").strip()

        if quick:
            data["sample_state"] = "液体"
            data["sampling_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            data["sender"] = ""
        else:
            data["sample_state"] = input("样品状态 (液体/固体/气体) [液体]: ").strip() or "液体"
            data["sampling_time"] = input("取样时间 (如 2026-05-31 08:00): ").strip()
            data["sender"] = input("送检人: ").strip()

        # === 车间选择 ===
        print()
        print("来源车间:")
        data["workshop"], _ = prompt_select(WORKSHOPS, "选择车间编号: ")

        # === 工艺环节 ===
        processes = PROCESS_LINES.get(data["workshop"], ["其他"])
        print(f"\n工艺环节 ({data['workshop']}):")
        data["process"], _ = prompt_select(processes, "选择工艺环节编号: ")

        if quick:
            data["sampling_point"] = ""
        else:
            data["sampling_point"] = input("取样点位: ").strip()

        # === 检测项目 ===
        print()
        print("--- 检测项目 ---")
        print("可选检测项目:")
        for i, (elem, name, unit, note) in enumerate(TEST_ITEMS, 1):
            print(f"  {i:2d}) {name:<8} ({elem:<4})  {unit:<6}  {note}")

        selected = input("\n选择项目编号（逗号分隔，如 1,2,3）: ").strip()
        selected_idx = [int(x.strip()) - 1 for x in selected.split(",") if x.strip()]

        data["items"] = []
        if quick:
            for idx in selected_idx:
                if 0 <= idx < len(TEST_ITEMS):
                    elem, name, unit, note = TEST_ITEMS[idx]
                    data["items"].append({
                        "element": elem, "name": name, "unit": unit,
                        "spec": "", "note": note,
                    })
        else:
            for idx in selected_idx:
                if 0 <= idx < len(TEST_ITEMS):
                    elem, name, unit, note = TEST_ITEMS[idx]
                    spec = input(f"  {name} 规格要求 (如 80-110 g/L, 留空跳过): ").strip()
                    data["items"].append({
                        "element": elem, "name": name, "unit": unit,
                        "spec": spec, "note": note,
                    })

        if quick:
            data["standard_ref"] = "QC工程图"
            data["results"] = []
        else:
            # === 标准依据 ===
            data["standard_ref"] = input("\n标准依据 [QC工程图]: ").strip() or "QC工程图"

            # === 可选填写结果 ===
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
                            "judge": judge,
                        })

    except (EOFError, KeyboardInterrupt):
        print("\n\n取消。")
        return None
    except ValueError:
        print("\n输入无效。")
        return None

    return data


def template_mode(template_num, output_file=None, fmt="text"):
    """使用预设模板快速生成送检单。

    交互式询问必填项（样品编号、样品名称、送检人），其余使用模板默认值。
    """
    tmpl = TEMPLATES.get(template_num)
    if not tmpl:
        print(f"错误：无效的模板编号 {template_num}。可用: 1, 2, 3", file=sys.stderr)
        return

    print()
    print(f"  使用模板: {tmpl['name']}")
    print(f"  车间: {tmpl['workshop']}  |  工艺: {tmpl['process']}")
    print(f"  样品状态: {tmpl['sample_state']}")
    print(f"  检测项目: {', '.join(tmpl['items'])}")
    print()

    data = {
        "sample_state": tmpl["sample_state"],
        "workshop": tmpl["workshop"],
        "process": tmpl["process"],
        "sender": "",
        "sampling_point": "",
        "sampling_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "standard_ref": "QC工程图",
        "results": [],
    }

    try:
        data["sample_id"] = input("样品编号: ").strip()
        data["sample_name"] = input("样品名称: ").strip()
        data["sender"] = input("送检人 [自动]: ").strip() or ""

        # 根据模板指定的元素名构建 items
        data["items"] = []
        for elem in tmpl["items"]:
            idx = ELEMENT_INDEX.get(elem)
            if idx is not None:
                e, n, u, note = TEST_ITEMS[idx]
                data["items"].append({
                    "element": e, "name": n, "unit": u,
                    "spec": "", "note": note,
                })

    except (EOFError, KeyboardInterrupt):
        print("\n\n取消。")
        return

    write_output(data, fmt, output_file)


def batch_mode(csv_path, output_file=None, fmt="text"):
    """从CSV模板批量生成送检单。

    CSV格式要求:
      sample_id,sample_name,workshop,process,items
    items列为逗号分隔的元素符号，如 "Co,Ni,Cu"
    """
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"错误：文件不存在: {csv_path}", file=sys.stderr)
        return
    except Exception as e:
        print(f"错误：读取CSV失败: {e}", file=sys.stderr)
        return

    if not rows:
        print("警告: CSV文件为空。", file=sys.stderr)
        return

    # 校验列名
    required_cols = {"sample_id", "sample_name", "workshop", "process", "items"}
    actual_cols = set(reader.fieldnames or [])
    missing = required_cols - actual_cols
    if missing:
        print(f"错误：CSV缺少必要列: {', '.join(sorted(missing))}", file=sys.stderr)
        print(f"      现有列: {', '.join(actual_cols)}", file=sys.stderr)
        return

    now = datetime.now()
    all_outputs = []

    for row_idx, row in enumerate(rows, 1):
        sample_id = row.get("sample_id", "").strip()
        sample_name = row.get("sample_name", "").strip()
        workshop = row.get("workshop", "").strip()
        process = row.get("process", "").strip()
        items_str = row.get("items", "").strip()

        if not sample_id:
            print(f"  第{row_idx}行: sample_id为空，跳过。", file=sys.stderr)
            continue

        # 解析检测项目
        elem_names = [x.strip() for x in items_str.split(",") if x.strip()]
        items = []
        for elem in elem_names:
            idx = ELEMENT_INDEX.get(elem)
            if idx is not None:
                e, n, u, note = TEST_ITEMS[idx]
                items.append({"element": e, "name": n, "unit": u, "spec": "", "note": note})
            else:
                print(f"  第{row_idx}行: 未知元素 '{elem}'，跳过。", file=sys.stderr)

        data = {
            "sample_id": sample_id,
            "sample_name": sample_name,
            "workshop": workshop,
            "process": process,
            "sample_state": "液体",
            "sampling_point": row.get("sampling_point", "").strip(),
            "sampling_time": row.get("sampling_time", now.strftime("%Y-%m-%d %H:%M")),
            "sender": row.get("sender", "").strip(),
            "standard_ref": row.get("standard_ref", "QC工程图"),
            "items": items,
            "results": [],
            "serial": f"S{now.strftime('%Y%m%d')}-{sample_id}",
        }

        all_outputs.append(data)

    if not all_outputs:
        print("没有有效数据可生成。", file=sys.stderr)
        return

    print(f"\n共处理 {len(all_outputs)} 条送检单。\n")

    if fmt == "csv":
        # CSV模式：合并所有数据输出为一个CSV文件
        fieldnames = ["sample_id", "sample_name", "workshop", "process",
                      "element", "name", "unit", "note", "spec", "value", "judge"]
        all_rows = []
        for data in all_outputs:
            all_rows.extend(generate_csv(data))

        if output_file:
            with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"CSV已保存至: {output_file}")
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    else:
        # text模式：逐条输出（或整体到文件）
        combined = []
        for data in all_outputs:
            combined.append(generate_form(data))
        output_text = "\n\n".join(combined)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_text + "\n")
            print(f"送检单已保存至: {output_file}")
        else:
            print(output_text)


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(
        description="qc-sample — 样品送检单生成器 v" + VERSION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  qc-sample                             交互模式
  qc-sample --quick                     快速模式
  qc-sample --template 1                浸出液模板 (Co,Ni,Cu,Mn,Fe,pH)
  qc-sample --template 2                萃取液模板 (Co,Ni,pH)
  qc-sample --template 3                成品钴盐模板 (Co,Ni,Cu,Fe,Ca,Mg)
  qc-sample --batch samples.csv         批量生成
  qc-sample --format csv                输出CSV (LIMS导入格式)
  qc-sample --output result.txt         输出到文件
  qc-sample --quick --format csv --output result.csv  快速+CSV+文件
""",
    )
    parser.add_argument("--quick", action="store_true", help="快速模式（只问必填项，其余用默认值）")
    parser.add_argument("--output", "-o", type=str, help="输出到指定文件")
    parser.add_argument("--format", choices=["text", "csv"], default="text",
                        help="输出格式: text=送检单(默认), csv=LIMS导入格式")
    parser.add_argument("--batch", "-b", type=str, metavar="CSV_FILE",
                        help="批量生成: 从CSV模板读取送检单数据")
    parser.add_argument("--template", "-t", type=int, choices=[1, 2, 3],
                        help="使用预设模板: 1=浸出液, 2=萃取液, 3=成品钴盐")
    parser.add_argument("--version", "-v", action="version",
                        version=f"qc-sample v{VERSION}")

    args = parser.parse_args()

    # --version 由 argparse 自动处理

    if args.batch:
        # 批量模式
        batch_mode(args.batch, args.output, args.format)

    elif args.template:
        # 模板模式
        template_mode(args.template, args.output, args.format)

    else:
        # 交互模式（普通或快速）
        data = interactive_mode(quick=args.quick)
        if data:
            write_output(data, args.format, args.output)


TOOL_META = {
    "name": "qc-sample",
    "func": "main",
    "desc": "样品送检单生成器 v2.0 -- 交互/模板/批量",
}

if __name__ == "__main__":
    main()
