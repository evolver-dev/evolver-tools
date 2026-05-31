#!/usr/bin/env python3
"""evolver CLI - Unified interface for all EVOLVER tools.

Tools are auto-discovered via TOOL_META in each vendor module.
No manual registration needed — just add TOOL_META to your vendor file.
"""

import sys
import importlib

from evolver_tools.autoreg import auto_discover


def list_tools():
    """Display all available tools."""
    tools = auto_discover()
    print(f'\x1b[1;36m===== EVOLVER Tools v31.0.0 =====\x1b[0m')
    print()
    for name, info in sorted(tools.items()):
        print(f'  \033[1;33m{name:<18}\033[0m {info["desc"]}')
    print()
    print(f'  Total: {len(tools)} tools')
    print()
    print('Usage: evolver <toolname> [args...]')
    print('       evolver list')


def run_tool(tool_name, args):
    tools = auto_discover()
    if tool_name not in tools:
        print(f'Unknown tool: {tool_name}')
        sys.exit(1)
    info = tools[tool_name]
    mod_path = info["module"]
    func_name = info["func"]
    old_argv = sys.argv
    sys.argv = [tool_name] + args
    try:
        mod = importlib.import_module(mod_path)
        func = getattr(mod, func_name)
        result = func()
        if result is not None:
            print(result)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error running {tool_name}: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        sys.argv = old_argv


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        list_tools()
        return
    tool_name = sys.argv[1]
    args = sys.argv[2:]
    if tool_name == "list":
        list_tools()
        return
    run_tool(tool_name, args)


if __name__ == "__main__":
    main()
