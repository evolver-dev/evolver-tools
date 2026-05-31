#!/usr/bin/env python3
"""math_eval — Safe mathematical expression evaluator.

Usage: math_eval "2 + 2"
       math_eval "sin(pi/4)"
       math_eval "sqrt(144) * log10(100)"
       math_eval "random()"  # 0.0-1.0

Safe evaluation using a restricted namespace with math module functions.
No file access, no exec, no eval of arbitrary code.
"""

import sys
import math
import random

TOOL_META = {
    "name": "math_eval",
    "func": "main",
    "desc": "Safe mathematical expression evaluator",
}

# Safe namespace with math functions
SAFE_NS = {
    # Constants
    'pi': math.pi, 'e': math.e, 'tau': math.tau, 'inf': math.inf, 'nan': math.nan,
    # Basic math
    'abs': abs, 'round': round, 'int': int, 'float': float, 'min': min, 'max': max,
    'sum': sum, 'pow': pow,
    # Trig
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'degrees': math.degrees, 'radians': math.radians,
    # Log
    'log': math.log, 'log2': math.log2, 'log10': math.log10, 'log1p': math.log1p,
    'exp': math.exp, 'expm1': math.expm1,
    # Root/Power
    'sqrt': math.sqrt, 'cbrt': math.cbrt if hasattr(math, 'cbrt') else lambda x: x ** (1/3),
    'hypot': math.hypot, 'isclose': math.isclose,
    # Rounding
    'floor': math.floor, 'ceil': math.ceil, 'trunc': math.trunc,
    'factorial': math.factorial,
    # Special
    'gamma': math.gamma, 'lgamma': math.lgamma, 'erf': math.erf, 'erfc': math.erfc,
    # Random
    'random': random.random, 'randint': random.randint, 'uniform': random.uniform,
    'gauss': random.gauss,
    # Constants
    '__builtins__': {},
}

ALLOWED_NAMES = set(SAFE_NS.keys())


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    expr = ' '.join(args)

    try:
        # Parse AST and check it's safe
        code = compile(expr, '<math_eval>', 'eval', flags=0, dont_inherit=True)
        for name in code.co_names:
            if name not in ALLOWED_NAMES:
                print(f"Error: '{name}' is not allowed in safe mode", file=sys.stderr)
                sys.exit(1)

        result = eval(code, SAFE_NS)
        if isinstance(result, float):
            if result == int(result):
                print(int(result))
            else:
                print(f"{result:.10g}".rstrip('0').rstrip('.'))
        else:
            print(result)
    except ZeroDivisionError:
        print("Error: division by zero", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
