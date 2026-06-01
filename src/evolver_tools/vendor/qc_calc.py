#!/usr/bin/env python3
"""qc-calc — QC 化验计算器 (Quality Control Lab Calculator) v2.0

电池回收/湿法冶金行业专用化验计算工具。
支持滴定计算、稀释校正、规格比对、单位换算、批量CSV处理。

快速模式:
  qc-calc --titrate Co 18.5 0.05 2.0          # EDTA 滴定
  qc-calc --acid-base 15.2 0.1 25.0            # 酸碱滴定
  qc-calc --dilute 5.0 100 10                  # 稀释校正
  qc-calc --check 85 g/L Co 80 110             # 规格比对
  qc-calc --convert 15000 mg/L g/L             # 单位换算

批量模式:
  qc-calc --batch samples.csv                  # 从CSV批量计算
  qc-calc --batch in.csv --output out.csv      # 结果写入文件
  qc-calc --batch in.csv --format csv          # CSV格式输出

保存结果:
  qc-calc --save results.txt                   # 交互模式保存结果

版本:
  qc-calc --version                            # 显示版本号
"""

import sys
import math
import csv
import os
from typing import Optional

VERSION = "2.0.0"

# ========== 元素数据 ==========
# 格式: 符号 -> (中文名, 原子量, 化合价, 备注)

ELEMENTS = {
    # 原有元素
    "Co":  ("钴", 58.933, 2, "主产品，EDTA滴定"),
    "Ni":  ("镍", 58.693, 2, "副产品/杂质，EDTA滴定"),
    "Cu":  ("铜", 63.546, 2, "杂质，EDTA滴定"),
    "Mn":  ("锰", 54.938, 2, "杂质，EDTA滴定"),
    "Fe":  ("铁", 55.845, 3, "杂质，重铬酸钾滴定"),
    "Zn":  ("锌", 65.38,  2, "杂质"),
    "Ca":  ("钙", 40.078, 2, "杂质，EDTA滴定"),
    "Mg":  ("镁", 24.305, 2, "杂质"),
    "Li":  ("锂", 6.941,  1, "主产品，火焰光度/AAS"),
    "Al":  ("铝", 26.982, 3, "杂质"),
    "Na":  ("钠", 22.990, 1, "杂质"),
    "S":   ("硫", 32.065, 0, "元素硫"),
    # 新增元素 v2.0
    "Pb":  ("铅", 207.2,  2, "杂质/电池材料"),
    "Cd":  ("镉", 112.414, 2, "杂质/电池材料"),
    "Cr":  ("铬", 51.996, 3, "杂质/不锈钢"),
    "As":  ("砷", 74.922, 3, "杂质"),
    "Sb":  ("锑", 121.760, 3, "杂质/阻燃剂"),
    "Bi":  ("铋", 208.980, 3, "杂质"),
    "Pt":  ("铂", 195.084, 2, "贵金属"),
    "Pd":  ("钯", 106.42,  2, "贵金属"),
    "Rh":  ("铑", 102.906, 3, "贵金属"),
}

# ========== 单位换算 ==========

UNIT_CONV = {
    "g/L": 1.0,
    "g/ml": 1000.0,
    "mg/L": 0.001,
    "mg/mL": 1.0,
    "%": 10.0,
    "ppm": 0.001,
    "ppb": 0.000001,
    "N": 1.0,
}

def convert_unit(value, from_unit, to_unit):
    """单位换算。"""
    if from_unit == to_unit:
        return value
    f_base = UNIT_CONV.get(from_unit)
    t_base = UNIT_CONV.get(to_unit)
    if f_base is None or t_base is None:
        return None
    in_g_per_l = value * f_base
    return in_g_per_l / t_base

# ========== 滴定计算 ==========

def calc_edta_titration(v_edta_ml, c_edta_mol_l, v_sample_ml, element_symbol, dilution_factor=1.0):
    """EDTA 滴定: C(g/L) = V_EDTA × C_EDTA × M / V_sample"""
    if element_symbol not in ELEMENTS:
        return None, f"未知元素: {element_symbol}"
    atomic_mass = ELEMENTS[element_symbol][1]
    c_g_per_l = (v_edta_ml * c_edta_mol_l * atomic_mass) / v_sample_ml
    if dilution_factor != 1.0:
        c_g_per_l *= dilution_factor
    return c_g_per_l, None


def calc_acid_base_titration(v_naoh_ml, c_naoh_n, v_sample_ml, dilution_factor=1.0):
    """酸碱滴定: N = V_NaOH × C_NaOH / V_sample"""
    normality = (v_naoh_ml * c_naoh_n) / v_sample_ml
    if dilution_factor != 1.0:
        normality *= dilution_factor
    return normality


def calc_dilution(measured_conc, sample_ml, total_volume_ml):
    """稀释校正: C_actual = C_measured × V_total / V_sample"""
    if sample_ml <= 0 or total_volume_ml <= 0:
        return None, "样品体积和最终体积必须大于0"
    factor = total_volume_ml / sample_ml
    return measured_conc * factor, None


# ========== 规格比对 ==========

def check_spec(value, unit, spec_lsl=None, spec_usl=None):
    """检查结果是否在规格范围内。"""
    results = []
    passed = True
    if spec_lsl is not None:
        if value < spec_lsl:
            results.append(f"  ❌ 低于下限: {value:.4f} < {spec_lsl} {unit}")
            passed = False
        else:
            results.append(f"  ✅ 高于下限: {value:.4f} ≥ {spec_lsl} {unit}")
    if spec_usl is not None:
        if value > spec_usl:
            results.append(f"  ❌ 高于上限: {value:.4f} > {spec_usl} {unit}")
            passed = False
        else:
            results.append(f"  ✅ 低于上限: {value:.4f} ≤ {spec_usl} {unit}")
    return passed, results


# ========== 元素解析 ==========

def resolve_element(symbol):
    """智能元素解析: Co/CO/co -> Co, NI/Ni -> Ni"""
    s = symbol.strip()
    if len(s) >= 2:
        s = s[0].upper() + s[1:].lower()
    else:
        s = s.upper()
    if s in ELEMENTS:
        return s
    for key in ELEMENTS:
        if key.upper() == symbol.upper():
            return key
    return None


# ========== 批量 CSV 处理 ==========

def process_batch_csv(input_path, output_path=None, fmt="text"):
    """批量从CSV读取样品数据，逐行计算，输出结果。

    CSV格式: 类型,元素,V_EDTA,C_EDTA,V_sample,稀释倍数
    示例: EDTA,Co,18.5,0.05,2.0,1.0

    支持从文件或stdin读取（input_path=None 或 '-' 时从stdin读取）
    """
    rows = []
    try:
        if input_path is None or input_path == "-":
            source = sys.stdin
        else:
            source = open(input_path, "r", encoding="utf-8-sig")
        with source as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if not row or all(c.strip() == "" for c in row):
                    continue
                # 第一行如果是列标题则跳过
                if i == 0 and row[0].strip().lower() in ("类型", "type", "element"):
                    continue
                rows.append(row)
    except FileNotFoundError:
        print(f"文件未找到: {input_path}", file=sys.stderr)
        return

    if not rows:
        print("❌ CSV 文件为空或无有效数据行。", file=sys.stderr)
        return

    results = []
    errors = []
    result_headers = ["类型", "元素", "V_EDTA", "C_EDTA", "V_sample", "稀释倍数", "结果(g/L)", "状态"]

    for row_idx, row in enumerate(rows):
        if len(row) < 5:
            errors.append((row_idx, f"列数不足 (需要 ≥5, 实际 {len(row)})"))
            continue

        calc_type = row[0].strip().upper()
        elem_str = row[1].strip()
        try:
            v_edta = float(row[2])
            c_edta = float(row[3])
            v_sample = float(row[4])
        except ValueError as e:
            errors.append((row_idx, f"数值解析错误: {e}"))
            continue

        dilution = 1.0
        if len(row) > 5 and row[5].strip():
            try:
                dilution = float(row[5])
            except ValueError:
                errors.append((row_idx, f"稀释倍数解析错误: {row[5]}"))
                continue

        if calc_type == "EDTA":
            elem = resolve_element(elem_str)
            if elem is None:
                errors.append((row_idx, f"未知元素: {elem_str}"))
                continue
            result_val, err_msg = calc_edta_titration(v_edta, c_edta, v_sample, elem, dilution)
            if err_msg:
                errors.append((row_idx, err_msg))
                continue
            results.append([
                calc_type, elem, f"{v_edta}", f"{c_edta}", f"{v_sample}",
                f"{dilution}", f"{result_val:.4f}", "OK"
            ])
        else:
            errors.append((row_idx, f"不支持的计算类型: {calc_type}"))

    # ========== 输出 ==========

    # 收集输出文本
    out_lines = []

    if fmt == "csv":
        # CSV 格式输出
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(result_headers)
        for r in results:
            writer.writerow(r)
        out_lines.append(buf.getvalue().rstrip())
    else:
        # 文本表格格式
        out_lines.append(f"批量计算结果 ({len(results)} 条成功, {len(errors)} 条失败)")
        out_lines.append("")
        out_lines.append(f"{'类型':<8} {'元素':<6} {'V_EDTA':<10} {'C_EDTA':<10} {'V_sample':<10} {'稀释':<8} {'结果(g/L)':<12} {'状态':<6}")
        out_lines.append("-" * 70)
        for r in results:
            out_lines.append(f"{r[0]:<8} {r[1]:<6} {r[2]:<10} {r[3]:<10} {r[4]:<10} {r[5]:<8} {r[6]:<12} {r[7]:<6}")
        if errors:
            out_lines.append("")
            out_lines.append(f"错误 ({len(errors)} 条):")
            for idx, err in errors:
                out_lines.append(f"  行 {idx+1}: {err}")

    output_text = "\n".join(out_lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"✅ 结果已写入: {output_path}")
    else:
        print(output_text)


# ========== 交互模式 ==========

def interactive_calc(save_file=None):
    """全交互模式。save_file: 可选路径，将每次计算结果追加保存。"""
    collected = []  # 收集的结果文本
    print()
    print("╔══════════════════════════════════════════╗")
    print(f"║      QC 化验计算器 v{VERSION}               ║")
    print("║      电池回收/湿法冶金专用                  ║")
    print("╚══════════════════════════════════════════╝")
    print()

    while True:
        print("选择计算类型:")
        print("  1) EDTA 滴定计算 (Co/Ni/Cu/Mn 等)")
        print("  2) 酸碱滴定计算 (酸度/碱度)")
        print("  3) 稀释校正")
        print("  4) 单位换算")
        print("  5) 规格比对")
        print("  0) 退出")
        print()

        try:
            choice = input("请输入编号 [0-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break

        if choice == "0":
            print("再见！")
            break
        elif choice == "1":
            _interactive_edta(collected)
        elif choice == "2":
            _interactive_acid_base(collected)
        elif choice == "3":
            _interactive_dilution(collected)
        elif choice == "4":
            _interactive_unit_convert(collected)
        elif choice == "5":
            _interactive_spec_check(collected)
        else:
            print("无效选择，请输入 0-5。")
        print()

    # 如果指定了保存文件且有结果
    if save_file and collected:
        try:
            with open(save_file, "w", encoding="utf-8") as f:
                f.write(f"QC 化验计算器 v{VERSION} - 结果记录\n")
                f.write(f"{'='*60}\n\n")
                for entry in collected:
                    f.write(entry + "\n")
                    f.write("\n")
            print(f"✅ 计算结果已保存到: {save_file}")
        except IOError as e:
            print(f"❌ 保存失败: {e}")


def _interactive_edta(collected=None):
    print()
    print("--- EDTA 滴定计算 ---")
    print()
    print("可选元素:")
    for sym, (name, mass, valence, note) in sorted(ELEMENTS.items()):
        print(f"  {sym:>4s} - {name} (M={mass:.3f}g/mol, {note})")
    print()
    try:
        elem = input("元素符号 (如 Co): ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    resolved = resolve_element(elem)
    if resolved is None:
        print(f"❌ 未知元素: {elem}")
        return
    elem_name = ELEMENTS[resolved][0]
    elem_mass = ELEMENTS[resolved][1]
    try:
        v_edta = float(input("EDTA 消耗体积 (mL): ").strip())
        c_edta = float(input("EDTA 标准浓度 (mol/L): ").strip())
        v_sample = float(input("取样体积 (mL): ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        print("❌ 输入无效。")
        return
    dilute = input("样品是否稀释过? (y/N): ").strip().lower()
    dilution_factor = 1.0
    if dilute in ("y", "yes"):
        try:
            orig_v = float(input("原始取样体积 (mL): ").strip())
            final_v = float(input("稀释后总体积 (mL): ").strip())
            dilution_factor = final_v / orig_v
            print(f"  稀释倍数: {dilution_factor:.4f}")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("  未应用稀释校正。")

    result, err = calc_edta_titration(v_edta, c_edta, v_sample, resolved, dilution_factor)
    if err:
        print(f"❌ {err}")
        return
    print()
    print("━" * 50)
    print(f"  计算过程:")
    print(f"  C({elem}) = {v_edta}mL × {c_edta}mol/L × {elem_mass}g/mol / {v_sample}mL")
    if dilution_factor != 1.0:
        print(f"           × {dilution_factor:.4f} (稀释倍数)")
    print(f"          = {result:.4f} g/L")
    print()
    print(f"  📊 结果: {result:.4f} g/L  ({elem_name})")
    print()
    print("  其他单位:")
    for u in ["mg/L", "%", "ppm"]:
        conv = convert_unit(result, "g/L", u)
        if conv is not None:
            print(f"    {conv:.4f} {u}")
    print("━" * 50)

    # 收集结果用于保存
    if collected is not None:
        entry = (
            f"[EDTA滴定] {elem_name}({resolved}): "
            f"C = {result:.4f} g/L "
            f"(V_EDTA={v_edta}mL, C_EDTA={c_edta}mol/L, V_sample={v_sample}mL"
            + (f", 稀释={dilution_factor:.4f}" if dilution_factor != 1.0 else "")
            + ")"
        )
        collected.append(entry)


def _interactive_acid_base(collected=None):
    print()
    print("--- 酸碱滴定计算 (酸度/碱度) ---")
    print()
    try:
        v_naoh = float(input("NaOH 消耗体积 (mL): ").strip())
        c_naoh = float(input("NaOH 标准浓度 (N): ").strip())
        v_sample = float(input("取样体积 (mL): ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        print("❌ 输入无效。")
        return
    dilute = input("样品是否稀释过? (y/N): ").strip().lower()
    dilution_factor = 1.0
    if dilute in ("y", "yes"):
        try:
            orig_v = float(input("原始取样体积 (mL): ").strip())
            final_v = float(input("稀释后总体积 (mL): ").strip())
            dilution_factor = final_v / orig_v
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
    result = calc_acid_base_titration(v_naoh, c_naoh, v_sample, dilution_factor)
    print()
    print("━" * 50)
    print(f"  N = {v_naoh}mL × {c_naoh}N / {v_sample}mL")
    if dilution_factor != 1.0:
        print(f"    × {dilution_factor:.4f} (稀释倍数)")
    print(f"    = {result:.4f} N")
    print(f"  📊 结果: {result:.4f} N")
    print("━" * 50)

    if collected is not None:
        entry = (
            f"[酸碱滴定] 酸度/碱度: N = {result:.4f} N "
            f"(V_NaOH={v_naoh}mL, C_NaOH={c_naoh}N, V_sample={v_sample}mL"
            + (f", 稀释={dilution_factor:.4f}" if dilution_factor != 1.0 else "")
            + ")"
        )
        collected.append(entry)


def _interactive_dilution(collected=None):
    print()
    print("--- 稀释校正 ---")
    print()
    try:
        measured = float(input("测定浓度: ").strip())
        sample_v = float(input("取样体积 (mL): ").strip())
        total_v = float(input("定容总体积 (mL): ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        print("❌ 输入无效。")
        return
    result, err = calc_dilution(measured, sample_v, total_v)
    if err:
        print(f"❌ {err}")
        return
    factor = total_v / sample_v
    print()
    print("━" * 50)
    print(f"  稀释倍数: {factor:.4f}")
    print(f"  C_实际 = {measured} × {factor:.4f} = {result:.4f}")
    print(f"  📊 结果: {result:.4f}")
    print("━" * 50)

    if collected is not None:
        entry = (
            f"[稀释校正] C_实际 = {result:.4f} "
            f"(测定={measured}, V_sample={sample_v}mL, V_total={total_v}mL, 倍数={factor:.4f})"
        )
        collected.append(entry)


def _interactive_unit_convert(collected=None):
    print()
    print("--- 单位换算 ---")
    print()
    try:
        value = float(input("输入数值: ").strip())
        from_u = input("从单位 (g/L/mg/L/%/ppm): ").strip() or "g/L"
        to_u = input("到单位 (g/L/mg/L/%/ppm): ").strip() or "%"
    except (ValueError, EOFError, KeyboardInterrupt):
        print("❌ 输入无效。")
        return
    result = convert_unit(value, from_u, to_u)
    if result is None:
        print("❌ 不支持的转换。")
        return
    print(f"  📊 {value} {from_u} = {result:.6f} {to_u}")

    if collected is not None:
        entry = f"[单位换算] {value} {from_u} = {result:.6f} {to_u}"
        collected.append(entry)


def _interactive_spec_check(collected=None):
    print()
    print("--- 规格比对 ---")
    print()
    try:
        value = float(input("测定值: ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        print("❌ 输入无效。")
        return
    print()
    print("规格范围 (留空跳过):")
    try:
        lsl = input("下限 (LSL): ").strip()
        usl = input("上限 (USL): ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    lsl = float(lsl) if lsl else None
    usl = float(usl) if usl else None
    if lsl is None and usl is None:
        print("未输入规格范围。")
        return
    passed, details = check_spec(value, "", lsl, usl)
    print()
    print("━" * 50)
    print(f"  📊 测定值: {value}")
    for d in details:
        print(d)
    print(f"  {'✅ 合格' if passed else '❌ 不合格'}")
    print("━" * 50)

    if collected is not None:
        status = "合格" if passed else "不合格"
        entry = (
            f"[规格比对] 测定值={value}, "
            + (f"LSL={lsl}, " if lsl is not None else "")
            + (f"USL={usl}, " if usl is not None else "")
            + f"判定={status}"
        )
        collected.append(entry)


# ========== CLI 入口 ==========

def main():
    args = sys.argv[1:]

    # 无参数 → 交互模式
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    # --version 参数
    if args[0] == "--version":
        print(f"qc-calc v{VERSION}")
        return

    # 解析 --save 参数 (可出现在任何位置)
    save_file = None
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == "--save" and i + 1 < len(args):
            save_file = args[i + 1]
            i += 2
        else:
            filtered_args.append(args[i])
            i += 1
    args = filtered_args

    if not args:
        interactive_calc(save_file=save_file)
        return

    mode = args[0]

    # --batch 批量CSV模式
    if mode == "--batch":
        # 解析 --output 和 --format
        output_path = None
        fmt = "text"
        input_path = None
        j = 1
        while j < len(args):
            if args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            elif args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j].startswith("--"):
                j += 1
            else:
                input_path = args[j]
                j += 1
        if fmt == "csv" and output_path is None and input_path:
            base, _ = os.path.splitext(input_path)
            output_path = base + "_result.csv"
        process_batch_csv(input_path, output_path, fmt)
        return

    if mode == "--titrate":
        # qc-calc --titrate Co 18.5 0.05 2.0 [dilution] [--format csv] [--output file]
        if len(args) < 4:
            print("用法: qc-calc --titrate <元素> <V_EDTA_mL> <C_EDTA_mol/L> <V_sample_mL> [稀释倍数] [--format csv] [--output file]")
            return
        elem = resolve_element(args[1])
        if elem is None:
            print(f"Error: 未知元素: {args[1]}", file=sys.stderr)
            return
        v_edta = float(args[2])
        c_edta = float(args[3])
        v_sample = float(args[4])
        dilution = 1.0

        # 解析可选参数
        fmt = "text"
        output_path = None
        j = 5
        while j < len(args):
            if args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            else:
                # 尝试解析为稀释倍数数值
                try:
                    dilution = float(args[j])
                    j += 1
                except ValueError:
                    j += 1

        result, err = calc_edta_titration(v_edta, c_edta, v_sample, elem, dilution)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return

        if fmt == "csv":
            output_text = f"类型,元素,V_EDTA,C_EDTA,V_sample,稀释倍数,结果(g/L)\nEDTA,{elem},{v_edta},{c_edta},{v_sample},{dilution},{result:.4f}\n"
        else:
            output_text = f"{result:.4f}"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"✅ 结果已写入: {output_path}")
        else:
            print(output_text, end="" if output_text.endswith("\n") else "\n")

    elif mode == "--acid-base":
        if len(args) < 3:
            print("用法: qc-calc --acid-base <V_NaOH_mL> <C_NaOH_N> <V_sample_mL> [稀释倍数] [--format csv] [--output file]")
            return
        v_naoh = float(args[1])
        c_naoh = float(args[2])
        v_sample = float(args[3])
        dilution = 1.0

        fmt = "text"
        output_path = None
        j = 4
        while j < len(args):
            if args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            else:
                try:
                    dilution = float(args[j])
                    j += 1
                except ValueError:
                    j += 1

        result = calc_acid_base_titration(v_naoh, c_naoh, v_sample, dilution)

        if fmt == "csv":
            output_text = f"类型,V_NaOH,C_NaOH,V_sample,稀释倍数,结果(N)\n酸碱滴定,{v_naoh},{c_naoh},{v_sample},{dilution},{result:.4f}\n"
        else:
            output_text = f"{result:.4f}"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"✅ 结果已写入: {output_path}")
        else:
            print(output_text, end="" if output_text.endswith("\n") else "\n")

    elif mode == "--dilute":
        if len(args) < 3:
            print("用法: qc-calc --dilute <测定浓度> <取样体积_mL> <定容总体积_mL> [--format csv] [--output file]")
            return
        measured = float(args[1])
        sample_v = float(args[2])
        total_v = float(args[3])

        fmt = "text"
        output_path = None
        j = 4
        while j < len(args):
            if args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            else:
                j += 1

        result, err = calc_dilution(measured, sample_v, total_v)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return

        if fmt == "csv":
            output_text = f"类型,测定浓度,取样体积,定容总体积,稀释倍数,结果\n稀释校正,{measured},{sample_v},{total_v},{total_v/sample_v:.4f},{result:.4f}\n"
        else:
            output_text = f"{result:.4f}"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"✅ 结果已写入: {output_path}")
        else:
            print(output_text, end="" if output_text.endswith("\n") else "\n")

    elif mode == "--convert":
        if len(args) < 3:
            print("用法: qc-calc --convert <数值> <从单位> <到单位> [--format csv] [--output file]")
            return
        value = float(args[1])
        from_u = args[2]
        to_u = args[3]

        fmt = "text"
        output_path = None
        j = 4
        while j < len(args):
            if args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            else:
                j += 1

        result = convert_unit(value, from_u, to_u)
        if result is None:
            print(f"Error: 不支持的转换", file=sys.stderr)
            return

        if fmt == "csv":
            output_text = f"类型,数值,从单位,到单位,结果\n单位换算,{value},{from_u},{to_u},{result:.6f}\n"
        else:
            output_text = f"{result:.6f}"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"✅ 结果已写入: {output_path}")
        else:
            print(output_text, end="" if output_text.endswith("\n") else "\n")

    elif mode == "--check":
        if len(args) < 3:
            print("用法: qc-calc --check <值> <单位> [下限] [上限] [--format csv] [--output file]")
            return
        value = float(args[1])
        unit = args[2]

        fmt = "text"
        output_path = None
        lsl = None
        usl = None
        # 解析: 值, 单位, 然后可能是数字参数, 然后 --format/--output
        j = 3
        pending = []
        while j < len(args):
            if args[j] == "--format" and j + 1 < len(args):
                fmt = args[j + 1].lower()
                j += 2
            elif args[j] == "--output" and j + 1 < len(args):
                output_path = args[j + 1]
                j += 2
            else:
                try:
                    fv = float(args[j])
                    pending.append(fv)
                    j += 1
                except ValueError:
                    j += 1
        if len(pending) >= 1:
            lsl = pending[0]
        if len(pending) >= 2:
            usl = pending[1]

        passed, details = check_spec(value, unit, lsl, usl)

        if fmt == "csv":
            status = "合格" if passed else "不合格"
            output_text = f"类型,测定值,单位,下限,上限,判定\n规格比对,{value},{unit},{lsl or ''},{usl or ''},{status}\n"
        else:
            output_text = f"测定值: {value} {unit}\n" + "\n".join(details) + f"\n{'✅ 合格' if passed else '❌ 不合格'}"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"✅ 结果已写入: {output_path}")
        else:
            print(output_text)

    else:
        # 没有匹配的模式参数 → 进交互模式
        interactive_calc(save_file=save_file)


if __name__ == "__main__":
    main()
