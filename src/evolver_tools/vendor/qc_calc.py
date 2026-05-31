#!/usr/bin/env python3
"""qc_calc — QC 化验计算器 (Quality Control Lab Calculator)

电池回收 / 湿法冶金行业专用化验计算工具。
支持滴定计算、稀释校正、规格比对、单位换算。

交互模式：直接运行 qc_calc
快速模式：qc_calc --titrate Co 18.5 0.05 2.0
          qc_calc --dilute 5.0 100 10
          qc_calc --check Co 85 g/L 80 110

计算公式:
  EDTA 滴定: C(g/L) = V_EDTA(mL) × C_EDTA(mol/L) × M(g/mol) / V_sample(mL)
  酸碱滴定:  N = V_NaOH(mL) × C_NaOH(N) / V_sample(mL)
  稀释校正:  C_actual = C_measured × V_total / V_sample
"""

import sys
import argparse
import math

# ========== 元素数据 ==========

ELEMENTS = {
    # symbol: (name, atomic_mass, common_valence, notes)
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
    "Sc":  ("钪", 44.956, 3, "稀土杂质"),
    "Na":  ("钠", 22.990, 1, "杂质"),
    "S":   ("硫", 32.065, 0, "元素硫"),
}

# ========== 单位换算 ==========

UNIT_CONV = {
    "g/L": 1.0,
    "g/ml": 1000.0,
    "mg/L": 0.001,
    "mg/mL": 1.0,
    "%": 10.0,      # 1% = 10 g/L (for solutions)
    "ppm": 0.001,
    "ppb": 0.000001,
    "N": 1.0,       # Normality (保留原样)
    "mol/L": 0.0,   # 需要分子量转换
}

UNIT_NAMES = ["g/L", "mg/L", "%", "ppm", "N", "g/mL", "mg/mL"]

def convert_unit(value, from_unit, to_unit, element=None):
    """单位换算。"""
    if from_unit == to_unit:
        return value

    f_base = UNIT_CONV.get(from_unit)
    t_base = UNIT_CONV.get(to_unit)
    if f_base is None or t_base is None:
        return None  # 不支持的单位

    # g/L -> g/L is 1:1
    in_g_per_l = value * f_base
    return in_g_per_l / t_base


# ========== 滴定计算 ==========

def calc_edta_titration(v_edta_ml, c_edta_mol_l, v_sample_ml, element_symbol, dilution_factor=1.0):
    """
    EDTA 滴定计算。
    
    Co²⁺ + EDTA → Co-EDTA (1:1 络合)
    
    C(g/L) = V_EDTA(mL) × C_EDTA(mol/L) × M(g/mol) / V_sample(mL)
    
    如果样品经过稀释，乘以稀释倍数。
    """
    if element_symbol not in ELEMENTS:
        return None, f"未知元素: {element_symbol}"
    
    atomic_mass = ELEMENTS[element_symbol][1]
    c_g_per_l = (v_edta_ml * c_edta_mol_l * atomic_mass) / v_sample_ml
    
    if dilution_factor != 1.0:
        c_g_per_l *= dilution_factor
    
    return c_g_per_l, None


def calc_acid_base_titration(v_naoh_ml, c_naoh_n, v_sample_ml, dilution_factor=1.0):
    """
    酸碱滴定计算（酸度/碱度）。
    
    N = V_NaOH(mL) × C_NaOH(N) / V_sample(mL)
    """
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

def check_spec(value, unit, element, spec_lsl=None, spec_usl=None):
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


# ========== 格式输出 ==========

def format_result(title, element_cn, value, unit, details=None):
    """格式化的结果输出。"""
    lines = []
    lines.append("━" * 50)
    lines.append(f"  {title}")
    lines.append("━" * 50)
    lines.append(f"  元素: {element_cn}")
    lines.append(f"  结果: {value:.4f} {unit}")
    if details:
        for d in details:
            lines.append(d)
    lines.append("━" * 50)
    return "\n".join(lines)


# ========== 交互模式 ==========

def interactive_mode():
    """全交互模式 — 一步步引导用户完成计算。"""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║      QC 化验计算器 v1.0                  ║")
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
            interactive_edta()

        elif choice == "2":
            interactive_acid_base()

        elif choice == "3":
            interactive_dilution()

        elif choice == "4":
            interactive_unit_convert()

        elif choice == "5":
            interactive_spec_check()

        else:
            print("无效选择，请输入 0-5。")
        
        print()


def interactive_edta():
    """交互式 EDTA 滴定计算。"""
    print()
    print("--- EDTA 滴定计算 ---")
    print()
    
    # 选择元素
    print("可选元素:")
    for sym, (name, mass, valence, note) in sorted(ELEMENTS.items()):
        print(f"  {sym:>4s} - {name} (M={mass:.3f}g/mol, {note})")
    print()
    
    try:
        elem = input("元素符号 (如 Co): ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    
    resolved = _resolve_element(elem)
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
        print("❌ 输入无效，请输入数字。")
        return
    
    # 询问稀释
    dilute = input("样品是否稀释过? (y/N): ").strip().lower()
    dilution_factor = 1.0
    if dilute == "y" or dilute == "yes":
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
    
    # 可选单位换算
    print()
    print("  其他单位:")
    for u in ["mg/L", "%", "ppm"]:
        conv = convert_unit(result, "g/L", u)
        if conv is not None:
            print(f"    {conv:.4f} {u}")
    print("━" * 50)


def interactive_acid_base():
    """交互式酸碱滴定计算。"""
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
    print(f"  计算过程:")
    print(f"  N = {v_naoh}mL × {c_naoh}N / {v_sample}mL")
    if dilution_factor != 1.0:
        print(f"    × {dilution_factor:.4f} (稀释倍数)")
    print(f"    = {result:.4f} N")
    print()
    print(f"  📊 结果: {result:.4f} N")
    print("━" * 50)


def interactive_dilution():
    """交互式稀释校正计算。"""
    print()
    print("--- 稀释校正 ---")
    print()
    
    try:
        measured = float(input("测定浓度: ").strip())
        unit = input("单位 (g/L/mg/L/%/ppm): ").strip() or "g/L"
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
    print(f"  C_实际 = {measured} × {factor:.4f} = {result:.4f} {unit}")
    print(f"  📊 结果: {result:.4f} {unit}")
    print("━" * 50)


def interactive_unit_convert():
    """交互式单位换算。"""
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
    
    print()
    print(f"  📊 {value} {from_u} = {result:.6f} {to_u}")


def interactive_spec_check():
    """交互式规格比对。"""
    print()
    print("--- 规格比对 ---")
    print()
    
    try:
        value = float(input("测定值: ").strip())
        unit = input("单位 (g/L/mg/L/%/ppm): ").strip() or "g/L"
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
        print("未输入规格范围，无法比对。")
        return
    
    passed, details = check_spec(value, unit, None, lsl, usl)
    
    print()
    print("━" * 50)
    print(f"  📊 测定值: {value} {unit}")
    for d in details:
        print(d)
    print(f"  {'✅ 合格' if passed else '❌ 不合格'}")
    print("━" * 50)


def _resolve_element(symbol):
    """智能元素解析: Co/CO/co -> Co, NI/Ni -> Ni"""
    s = symbol.strip()
    if len(s) >= 2:
        s = s[0].upper() + s[1:].lower()
    else:
        s = s.upper()
    if s in ELEMENTS:
        return s
    # Fuzzy match
    for key in ELEMENTS:
        if key.upper() == symbol.upper():
            return key
    return None


# ========== 快速模式 (CLI) ==========

def quick_titrate(args):
    """快速滴定计算。"""
    v_edta = float(args[1])
    c_edta = float(args[2])
    v_sample = float(args[3])
    elem = _resolve_element(args[0])
    if elem is None:
        print(f"Error: 未知元素: {args[0]}", file=sys.stderr)
        return 1
    
    if len(args) > 4:
        dilution = float(args[4])
    else:
        dilution = 1.0
    
    result, err = calc_edta_titration(v_edta, c_edta, v_sample, elem, dilution)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    
    elem_cn = ELEMENTS[elem][0] if elem else args[0]
    print(f"{result:.4f}")
    return 0


def quick_acid_base(args):
    """快速酸碱滴定。"""
    v_naoh = float(args[0])
    c_naoh = float(args[1])
    v_sample = float(args[2])
    dilution = float(args[3]) if len(args) > 3 else 1.0
    
    result = calc_acid_base_titration(v_naoh, c_naoh, v_sample, dilution)
    print(f"{result:.4f}")
    return 0


def quick_dilute(args):
    """快速稀释校正。"""
    measured = float(args[0])
    sample_v = float(args[1])
    total_v = float(args[2])
    
    result, err = calc_dilution(measured, sample_v, total_v)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    print(f"{result:.4f}")
    return 0


def quick_convert(args):
    """快速单位换算。"""
    value = float(args[0])
    from_u = args[1]
    to_u = args[2]
    
    result = convert_unit(value, from_u, to_u)
    if result is None:
        print(f"Error: Unsupported conversion", file=sys.stderr)
        return 1
    print(f"{result:.6f}")
    return 0


def quick_check(args):
    """快速规格比对。"""
    value = float(args[0])
    unit = args[1]
    element = args[2] if len(args) > 2 and args[2] else None
    lsl = float(args[3]) if len(args) > 3 and args[3] else None
    usl = float(args[4]) if len(args) > 4 and args[4] else None
    
    passed, details = check_spec(value, unit, element, lsl, usl)
    
    for d in details:
        print(d)
    return 0 if passed else 1


# ========== 主入口 ==========

def build_parser():
    """构建参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="qc_calc",
        description="QC 化验计算器 — 电池回收/湿法冶金专用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速使用示例:
  # EDTA 滴定 Co: 消耗18.5mL EDTA(0.05mol/L), 取样2mL
  qc_calc --titrate Co 18.5 0.05 2.0
  
  # 带稀释校正: 消耗18.5mL, EDTA 0.05mol/L, 取样2mL, 稀释倍数5
  qc_calc --titrate Co 18.5 0.05 2.0 5.0
  
  # 酸碱滴定: 消耗12.3mL NaOH(0.1N), 取样5mL
  qc_calc --acid 12.3 0.1 5.0
  
  # 稀释校正: 测得5.0g/L, 取10mL定容100mL
  qc_calc --dilute 5.0 10 100
  
  # 单位换算: 85 g/L 转 %%
  qc_calc --convert 85 g/L %%
  
  # 规格比对: 85g/L Co, 规格80-110g/L
  qc_calc --check 85 g/L Co 80 110

交互模式（无参数）直接运行 qc_calc
        """
    )
    
    parser.add_argument("--titrate", nargs="+", metavar="ARG",
                        help="EDTA 滴定计算: --titrate Co 18.5 0.05 2.0 [稀释倍数]")
    parser.add_argument("--acid", nargs=3, metavar=("V_NAOH", "C_NAOH", "V_SAMPLE"),
                        help="酸碱滴定: NaOH消耗(mL) NaOH浓度(N) 取样(mL)")
    parser.add_argument("--dilute", nargs=3, metavar=("MEASURED", "SAMPLE_V", "TOTAL_V"),
                        help="稀释校正: 测定值 取样量(mL) 定容总量(mL)")
    parser.add_argument("--convert", nargs=3, metavar=("VALUE", "FROM", "TO"),
                        help="单位换算: 数值 从 到 (g/L/mg/L/%%/ppm)")
    parser.add_argument("--check", nargs="+", metavar="ARG",
                        help="规格比对: --check 85 g/L Co 80 110")
    
    return parser


def main():
    if len(sys.argv) < 2:
        interactive_mode()
        return
    
    parser = build_parser()
    args = parser.parse_args()
    
    if args.titrate:
        sys.exit(quick_titrate(args.titrate))
    elif args.acid:
        sys.exit(quick_acid_base(args.acid))
    elif args.dilute:
        sys.exit(quick_dilute(args.dilute))
    elif args.convert:
        sys.exit(quick_convert(args.convert))
    elif args.check:
        sys.exit(quick_check(args.check))
    else:
        parser.print_help()


# ========== 自动注册 ==========
TOOL_META = {
    "name": "qc_calc",
    "func": "main",
    "desc": "QC 化验计算器 — 滴定/稀释/单位换算/规格比对 (电池回收/湿法冶金)",
}

if __name__ == "__main__":
    main()
