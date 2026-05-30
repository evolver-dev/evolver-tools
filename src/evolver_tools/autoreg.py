#!/usr/bin/env python3
"""
EVOLVER Auto-Registration — eliminates the TOOLS dict bottleneck.

Instead of manually editing cli.py's TOOLS dict, any module in the vendor/
directory that exports TOOL_META is automatically discovered and registered.

Tool authors just need to add to their Python file:
    TOOL_META = {"name": "my-tool", "desc": "What it does"}

The auto-register scans vendor/ at import time and builds the full registry.
"""

import importlib
import importlib.util
import inspect
import os
import pkgutil
import sys

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")


def auto_discover():
    """
    Scan the vendor/ directory and discover all tools with TOOL_META.

    Returns:
        dict: {tool_name: {"module": "module.path", "func": "main", "desc": "..."}}
    """
    tools = {}
    vendor_path = VENDOR_DIR

    if not os.path.isdir(vendor_path):
        return tools

    # Scan all items in vendor directory
    for entry in sorted(os.listdir(vendor_path)):
        entry_path = os.path.join(vendor_path, entry)
        mod_name = None

        # Case 1: Single .py file (e.g., colorize.py)
        if entry.endswith(".py") and entry != "__init__.py":
            mod_name = f"evolver_tools.vendor.{entry[:-3]}"

        # Case 2: Package directory (e.g., b64/)
        elif os.path.isdir(entry_path) and not entry.startswith("_"):
            init_path = os.path.join(entry_path, "__init__.py")
            cli_path = os.path.join(entry_path, "cli.py")
            main_path = os.path.join(entry_path, "__main__.py")
            if os.path.isfile(init_path) or os.path.isfile(cli_path) or os.path.isfile(main_path):
                mod_name = f"evolver_tools.vendor.{entry}"

        if mod_name is None:
            continue

        # Try to import and read TOOL_META
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            # Silently skip modules that can't be imported
            continue

        # Check for TOOL_META
        meta = getattr(mod, "TOOL_META", None)
        if meta is None:
            # No TOOL_META defined — skip this module
            continue

        tool_name = meta.get("name", entry.replace("_", "-").replace(".py", ""))
        tool_desc = meta.get("desc", getattr(mod, "__doc__", "") or f"Tool: {entry}")
        func_name = meta.get("func", "main")

        # Determine the correct function reference
        if func_name and "." in func_name:
            # e.g., "cli:main" — handled differently
            pass

        # Prefer `main` function, fallback to entry, then any callable
        actual_func = func_name
        if not hasattr(mod, actual_func):
            candidates = ["main", "entry", "run"]
            for c in candidates:
                if hasattr(mod, c):
                    actual_func = c
                    break

        tools[tool_name] = {
            "module": mod_name,
            "func": actual_func,
            "desc": tool_desc,
        }

    return tools


def auto_generate_pyproject(vendor_dir=None):
    """
    Generate the [project.scripts] section for pyproject.toml.
    Useful for batch-updating the console_scripts entries.

    Returns:
        str: The scripts section as TOML text (no leading indent)
    """
    if vendor_dir is None:
        vendor_dir = VENDOR_DIR

    lines = ["[project.scripts]"]
    lines.append('evtool = "evolver_tools.cli:main"')

    for entry in sorted(os.listdir(vendor_dir)):
        # Same logic as above
        entry_path = os.path.join(vendor_dir, entry)
        if entry.endswith(".py") and entry != "__init__.py":
            mod_path = f"evolver_tools.vendor.{entry[:-3]}"
            tool_name = entry[:-3].replace("_", "-")
            lines.append(f'{tool_name} = "{mod_path}:main"')
        elif os.path.isdir(entry_path) and not entry.startswith("_"):
            init_path = os.path.join(entry_path, "__init__.py")
            cli_path = os.path.join(entry_path, "cli.py")
            main_path = os.path.join(entry_path, "__main__.py")
            if os.path.isfile(init_path) or os.path.isfile(cli_path) or os.path.isfile(main_path):
                mod_path = f"evolver_tools.vendor.{entry}"
                # Try to determine the entry function
                func = "main"
                try:
                    spec = importlib.util.find_spec(mod_path)
                    if spec and spec.loader:
                        mod = importlib.import_module(mod_path)
                        if hasattr(mod, "entry"):
                            func = "entry"
                        elif hasattr(mod, "run"):
                            func = "run"
                except Exception:
                    pass
                tool_name = entry.replace("_", "-")
                lines.append(f'{tool_name} = "{mod_path}:{func}"')

    return "\n".join(lines)


if __name__ == "__main__":
    tools = auto_discover()
    print(f"Auto-discovered {len(tools)} tools:")
    for name, info in sorted(tools.items()):
        print(f"  {name:<20} → {info['module']}.{info['func']}  ({info['desc']})")
    print()
    print("=" * 60)
    print("Generated pyproject.toml scripts section:")
    print(auto_generate_pyproject())
