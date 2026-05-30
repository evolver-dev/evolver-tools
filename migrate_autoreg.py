#!/usr/bin/env python3
"""Phase 1: Migrate evolver-tools to auto-registration architecture.

Reads the current TOOLS dict from cli.py, injects TOOL_META into each
vendor file, creates autoreg.py, rewrites cli.py to use auto_discover(),
and bumps to v3.0.0.
"""

import ast
import os
import re
import sys

VENDOR_DIR = "src/evolver_tools/vendor"
CLI_PATH = "src/evolver_tools/cli.py"
AUTOREG_PATH = "src/evolver_tools/autoreg.py"
PYPROJECT_PATH = "pyproject.toml"
INIT_PATH = "src/evolver_tools/__init__.py"


def parse_tools_from_cli():
    """Parse the TOOLS dict from cli.py using AST."""
    with open(CLI_PATH) as f:
        source = f.read()
    
    tree = ast.parse(source)
    tools_dict = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TOOLS":
                    # Found the TOOLS dict
                    val = node.value
                    if isinstance(val, ast.Dict):
                        for key, val_node in zip(val.keys, val.values):
                            if isinstance(key, ast.Str):
                                name = key.s
                            elif isinstance(key, ast.Constant):
                                name = key.value
                            else:
                                continue
                            
                            info = {}
                            if isinstance(val_node, ast.Dict):
                                for k, v in zip(val_node.keys, val_node.values):
                                    if isinstance(k, (ast.Str, ast.Constant)):
                                        k_str = k.s if isinstance(k, ast.Str) else k.value
                                        if isinstance(v, (ast.Str, ast.Constant)):
                                            info[k_str] = v.s if isinstance(v, ast.Str) else v.value
                            tools_dict[name] = info
    
    return tools_dict


def get_file_path(module_path):
    """Convert module path to actual file path."""
    parts = module_path.split(".")
    
    if len(parts) == 3:
        # evolver_tools.vendor.name -> vendor/name.py or vendor/name/__init__.py
        name = parts[2]
        py_path = os.path.join(VENDOR_DIR, f"{name}.py")
        init_path = os.path.join(VENDOR_DIR, name, "__init__.py")
        
        if os.path.exists(py_path):
            return py_path, "file"
        elif os.path.exists(init_path):
            return init_path, "dir"
        else:
            return py_path, "unknown"
    
    elif len(parts) == 4:
        # evolver_tools.vendor.name.sub -> vendor/name/sub.py
        name = parts[2]
        sub = parts[3]
        path = os.path.join(VENDOR_DIR, name, f"{sub}.py")
        return path, "submodule"
    
    elif len(parts) == 5:
        # evolver_tools.vendor.name.sub.sub2 -> vendor/name/sub/sub2.py
        name = parts[2]
        sub = parts[3]
        sub2 = parts[4]
        path = os.path.join(VENDOR_DIR, name, sub, f"{sub2}.py")
        return path, "submodule"
    
    return None, "unknown"


def append_tool_meta(filepath, tool_name, func_name, desc):
    """Append TOOL_META dict to a vendor file."""
    with open(filepath) as f:
        content = f.read()
    
    meta_block = f"""
# === Auto-registration metadata ===
TOOL_META = {{
    "name": "{tool_name}",
    "func": "{func_name}",
    "desc": {repr(desc)},
}}
"""
    
    # Check if TOOL_META already exists
    if "TOOL_META" in content:
        print(f"  SKIP {tool_name}: TOOL_META already exists")
        return False
    
    # Find the best place to insert: after __main__ block, or at end of file
    # Look for `if __name__ == "__main__":` and insert before it
    main_patterns = [
        r'if\s+__name__\s*==\s*["\']__main__["\']\s*:',
        r'if\s+__name__\s*==\s*["\']__main__["\']\s*:\s*\n',
    ]
    
    inserted = False
    for pattern in main_patterns:
        m = re.search(pattern, content)
        if m:
            insert_pos = m.start()
            content = content[:insert_pos] + meta_block + "\n" + content[insert_pos:]
            inserted = True
            break
    
    if not inserted:
        # Append to end
        content += meta_block
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True


def create_autoreg():
    """Create the autoreg.py module."""
    content = '''#!/usr/bin/env python3
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

import evolver_tools.vendor as vendor_pkg

# Cache after first discovery
_TOOLS_CACHE = None


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
    vendor_dir = os.path.dirname(vendor_pkg.__file__)

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

        tools[tool_name] = {
            "module": f"evolver_tools.vendor.{modname}",
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
'''
    with open(AUTOREG_PATH, 'w') as f:
        f.write(content)
    print(f"Created {AUTOREG_PATH}")


def rewrite_cli(tools_dict):
    """Rewrite cli.py to use auto_discover() instead of the hardcoded TOOLS dict."""
    new_cli = '''#!/usr/bin/env python3
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
    print(f'\\x1b[1;36m===== EVOLVER Tools v3.0.0 =====\\x1b[0m')
    print()
    for name, info in sorted(tools.items()):
        print(f'  \\033[1;33m{name:<18}\\033[0m {info["desc"]}')
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
'''
    with open(CLI_PATH, 'w') as f:
        f.write(new_cli)
    print(f"Rewrote {CLI_PATH}")


def bump_version():
    """Bump version to 3.0.0 in pyproject.toml."""
    with open(PYPROJECT_PATH) as f:
        content = f.read()
    
    content = re.sub(r'version = "2\.4\.0"', 'version = "3.0.0"', content)
    content = re.sub(r'v2\.4\.0', 'v3.0.0', content)
    
    with open(PYPROJECT_PATH, 'w') as f:
        f.write(content)
    print(f"Updated version in {PYPROJECT_PATH}")


def main():
    print("=" * 50)
    print("EVOLVER Auto-Registration Migration")
    print("=" * 50)
    
    # Step 1: Parse existing tools
    print("\n[1/6] Parsing TOOLS from cli.py...")
    tools_dict = parse_tools_from_cli()
    print(f"  Found {len(tools_dict)} tools")
    
    # Step 2: Create autoreg.py
    print("\n[2/6] Creating autoreg.py...")
    create_autoreg()
    
    # Step 3: Inject TOOL_META into vendor files
    print("\n[3/6] Injecting TOOL_META into vendor files...")
    injected = 0
    errors = []
    for name, info in sorted(tools_dict.items()):
        module_path = info["module"]
        func_name = info["func"]
        desc = info["desc"]
        
        filepath, filetype = get_file_path(module_path)
        if not filepath or not os.path.exists(filepath):
            errors.append(f"  MISSING {name}: {module_path} -> {filepath}")
            continue
        
        try:
            if append_tool_meta(filepath, name, func_name, desc):
                injected += 1
        except Exception as e:
            errors.append(f"  ERROR {name}: {e}")
    
    print(f"  Injected TOOL_META into {injected} files")
    if errors:
        print(f"  Errors ({len(errors)}):")
        for e in errors:
            print(f"    {e}")
    
    # Step 4: Rewrite cli.py
    print("\n[4/6] Rewriting cli.py to use auto_discover()...")
    rewrite_cli(tools_dict)
    
    # Step 5: Bump version
    print("\n[5/6] Bumping version to 3.0.0...")
    bump_version()
    
    # Step 6: Update __init__.py to export auto_discover
    print("\n[6/6] Updating __init__.py...")
    if os.path.exists(INIT_PATH):
        with open(INIT_PATH) as f:
            init_content = f.read()
        if 'auto_discover' not in init_content:
            init_content += "\nfrom .autoreg import auto_discover\n"
            with open(INIT_PATH, 'w') as f:
                f.write(init_content)
            print(f"  Updated {INIT_PATH}")
    
    print("\n" + "=" * 50)
    print("Migration complete! Run tests to verify:")
    print("  python -m evolver_tools.autoreg")
    print("  python -m evolver_tools.cli list")
    print("  evolver list")
    print("=" * 50)


if __name__ == "__main__":
    main()
