#!/usr/bin/env python3
"""Auto-discovery module for EVOLVER tools.

Scans all vendor modules for TOOL_META exports and returns them
as a unified registry. Enables parallel agent workflows: each vendor
tool defines its own TOOL_META, eliminating merge conflicts on cli.py.

Usage:
    from evolver_tools.autoreg import auto_discover
    tools = auto_discover()  # Returns dict[str, dict]
"""

import importlib
import os
import pkgutil

# Cache after first discovery
_TOOLS_CACHE = None


def _vendor_dir():
    """Return the absolute path to the vendor directory."""
    # vendor is a namespace package (no __init__.py), so __file__ is None
    # Walk up from autoreg.py location
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "vendor")


def auto_discover():
    """Scan all vendor modules and return a unified TOOLS dict.

    Each vendor module (file or package) that exports TOOL_META dict
    is discovered automatically. No manual registration needed.

    Returns:
        dict[str, dict]: Tool name -> {module, func, desc}
    """
    global _TOOLS_CACHE
    if _TOOLS_CACHE is not None:
        return _TOOLS_CACHE

    tools = {}
    vendor_dir = _vendor_dir()

    for importer, modname, ispkg in pkgutil.iter_modules([vendor_dir]):
        try:
            mod = importlib.import_module(f"evolver_tools.vendor.{modname}")
        except Exception:
            continue

        meta = getattr(mod, "TOOL_META", None)
        if meta is None:
            continue

        tool_name = meta.get("name")
        if not tool_name:
            continue

        func_name = meta.get("func", "main")
        desc = meta.get("desc", "")

        # If the package has a submodule (e.g. cal_tool/cli.py), use that
        submodule = meta.get("submodule", "")
        if submodule:
            module_path = f"evolver_tools.vendor.{modname}.{submodule}"
        else:
            module_path = f"evolver_tools.vendor.{modname}"

        tools[tool_name] = {
            "module": module_path,
            "func": func_name,
            "desc": desc,
        }

    _TOOLS_CACHE = tools
    return tools


def list_tools():
    """Print all discovered tools to stdout."""
    tools = auto_discover()
    print(f"Discovered {len(tools)} tools:")
    for name in sorted(tools.keys()):
        print(f"  - {name}")


if __name__ == "__main__":
    list_tools()
