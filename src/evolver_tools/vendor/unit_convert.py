#!/usr/bin/env python3
"""unit-convert — Convert between units of length, weight, temperature, and volume."""

import argparse
import sys


# --- Conversion tables ---
# All convert TO a common base unit, then FROM that base to the target.

# Length base: meters
_LENGTH = {
    "m":  1.0,
    "km": 1000.0,
    "mi": 1609.344,
    "ft": 0.3048,
    "in": 0.0254,
}

# Weight base: grams
_WEIGHT = {
    "kg": 1000.0,
    "g":  1.0,
    "lb": 453.59237,
    "oz": 28.349523125,
}

# Volume base: liters
_VOLUME = {
    "L":   1.0,
    "ml":  0.001,
    "gal": 3.785411784,
    "cup": 0.2365882365,
}

# Temperature: special handling via formulas
_CATEGORIES = {
    "length": "length",
    "weight": "weight",
    "temp": "temp",
    "volume": "volume",
}

_UNIT_MAP = {}
for cat, tbl in [("length", _LENGTH), ("weight", _WEIGHT), ("volume", _VOLUME)]:
    for u in tbl:
        _UNIT_MAP[u] = cat
_UNIT_MAP.update({"C": "temp", "F": "temp", "K": "temp"})


def _convert_length(value, from_unit, to_unit):
    base = value * _LENGTH[from_unit]
    return base / _LENGTH[to_unit]


def _convert_weight(value, from_unit, to_unit):
    base = value * _WEIGHT[from_unit]
    return base / _WEIGHT[to_unit]


def _convert_volume(value, from_unit, to_unit):
    base = value * _VOLUME[from_unit]
    return base / _VOLUME[to_unit]


def _convert_temp(value, from_unit, to_unit):
    # Convert to Kelvin first
    if from_unit == "C":
        kelvin = value + 273.15
    elif from_unit == "F":
        kelvin = (value - 32) * 5 / 9 + 273.15
    elif from_unit == "K":
        kelvin = value
    else:
        raise ValueError(f"Unknown temperature unit: {from_unit}")
    # Convert from Kelvin to target
    if to_unit == "C":
        return kelvin - 273.15
    elif to_unit == "F":
        return (kelvin - 273.15) * 9 / 5 + 32
    elif to_unit == "K":
        return kelvin
    else:
        raise ValueError(f"Unknown temperature unit: {to_unit}")


_CONVERTERS = {
    "length": _convert_length,
    "weight": _convert_weight,
    "temp": _convert_temp,
    "volume": _convert_volume,
}


def main():
    parser = argparse.ArgumentParser(
        description="Convert between units of length, weight, temperature, and volume."
    )
    parser.add_argument("value", type=float, help="Numeric value to convert")
    parser.add_argument("from_unit", help="Source unit (e.g. m, kg, C, L)")
    parser.add_argument("to_unit", help="Target unit (e.g. ft, lb, F, gal)")
    parser.add_argument(
        "-p", "--precision", type=int, default=6,
        help="Number of decimal places (default: 6)"
    )
    args = parser.parse_args()

    f, t = args.from_unit, args.to_unit
    if f not in _UNIT_MAP:
        print(f"Unknown unit: {f}", file=sys.stderr)
        sys.exit(1)
    if t not in _UNIT_MAP:
        print(f"Unknown unit: {t}", file=sys.stderr)
        sys.exit(1)

    cat_f = _UNIT_MAP[f]
    cat_t = _UNIT_MAP[t]
    if cat_f != cat_t:
        print(
            f"Cannot convert {f} ({cat_f}) to {t} ({cat_t}) — incompatible categories",
            file=sys.stderr,
        )
        sys.exit(1)

    result = _CONVERTERS[cat_f](args.value, f, t)
    print(f"{result:.{args.precision}f}")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "unit-convert",
    "func": "main",
    "desc": "Unit converter (length, weight, temp, volume)",
}

if __name__ == "__main__":
    main()
