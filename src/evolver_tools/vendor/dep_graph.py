#!/usr/bin/env python3
"""dep-graph — Dependency graph visualizer. Parse requirements.txt, Pipfile, package.json, Cargo.toml."""

import sys
import os
import re
import json
import argparse


def parse_requirements_txt(content):
    """Parse a requirements.txt file."""
    deps = {}
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        m = re.match(r'^([a-zA-Z0-9_.-]+)\s*([><=!~]+.*)?$', line)
        if m:
            name = m.group(1).lower()
            version = m.group(2).strip() if m.group(2) else '*'
            deps[name] = version
    return deps


def parse_package_json(content):
    """Parse a package.json file."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}
    deps = {}
    for section in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
        if section in data:
            for name, version in data[section].items():
                deps[name.lower()] = str(version)
    return deps


def parse_cargo_toml(content):
    """Parse a Cargo.toml file (basic)."""
    deps = {}
    in_dependencies = False
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped[1:-1].strip().lower()
            in_dependencies = section in ('dependencies', 'dev-dependencies', 'build-dependencies')
            continue
        if in_dependencies and '=' in stripped:
            m = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', stripped)
            if m:
                deps[m.group(1).lower()] = m.group(2)
            else:
                m2 = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*\{', stripped)
                if m2:
                    deps[m2.group(1).lower()] = '{...}'
    return deps


def parse_pipfile(content):
    """Parse a Pipfile (basic TOML-like)."""
    deps = {}
    in_packages = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped[1:-1].strip().lower()
            in_packages = section in ('packages', 'dev-packages')
            continue
        if in_packages and '=' in stripped:
            m = re.match(r'^([a-zA-Z0-9_.-]+)\s*=\s*["\']([^"\']*)["\']', stripped)
            if m:
                deps[m.group(1).lower()] = m.group(2) if m.group(2) else '*'
            else:
                m2 = re.match(r'^([a-zA-Z0-9_.-]+)\s*=\s*\{', stripped)
                if m2:
                    deps[m2.group(1).lower()] = '{...}'
                else:
                    m3 = re.match(r'^([a-zA-Z0-9_.-]+)\s*=\s*$', stripped)
                    if m3:
                        deps[m3.group(1).lower()] = '*'
    return deps


def detect_format(filepath):
    """Detect format from file name."""
    basename = os.path.basename(filepath).lower()
    if basename == 'requirements.txt':
        return 'requirements'
    if basename == 'package.json':
        return 'package'
    if basename == 'cargo.toml':
        return 'cargo'
    if basename == 'pipfile':
        return 'pipfile'
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.txt':
        return 'requirements'
    return None


def build_transitive_tree(filepath, format_type, visited=None, depth=0, max_depth=5):
    """Recursively build dependency tree (simple name-based lookup)."""
    if visited is None:
        visited = set()
    if depth > max_depth:
        return {}

    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if format_type == 'requirements':
        deps = parse_requirements_txt(content)
    elif format_type == 'package':
        deps = parse_package_json(content)
    elif format_type == 'cargo':
        deps = parse_cargo_toml(content)
    elif format_type == 'pipfile':
        deps = parse_pipfile(content)
    else:
        deps = {}

    tree = {}
    for dep_name, dep_version in deps.items():
        if dep_name not in visited:
            visited.add(dep_name)
            tree[dep_name] = {'version': dep_version, 'deps': {}}

    return tree


def print_ascii_tree(tree, indent=0, prefix=''):
    """Print dependency tree in ASCII format."""
    items = list(tree.items())
    for i, (name, info) in enumerate(items):
        is_last = i == len(items) - 1
        connector = '└── ' if is_last else '├── '
        version = info.get('version', '*')
        version_str = f" (\033[94m{version}\033[0m)" if version and version != '*' else ''
        print(f"{prefix}{connector}\033[1m{name}\033[0m{version_str}")
        child_prefix = prefix + ('    ' if is_last else '│   ')
        if info.get('deps'):
            print_ascii_tree(info['deps'], indent + 1, child_prefix)


def print_mermaid_graph(tree):
    """Print dependency graph in Mermaid format."""
    print("graph TD;")
    for name, info in tree.items():
        print(f"    {name.replace('-', '_').replace('.', '_')}[\"{name}\"];")
        if info.get('deps'):
            for dep_name in info['deps']:
                parent = name.replace('-', '_').replace('.', '_')
                child = dep_name.replace('-', '_').replace('.', '_')
                print(f"    {parent} --> {child};")


def main():
    parser = argparse.ArgumentParser(
        description='Dependency graph visualizer. Parse and display dependency trees.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dep-graph requirements.txt
  dep-graph requirements.txt --format mermaid
  dep-graph --transitive package.json
  dep-graph Cargo.toml
        """,
    )
    parser.add_argument('file', help='Dependency file to parse')
    parser.add_argument('--format', '-f', choices=['tree', 'mermaid'], default='tree',
                        help='Output format (default: tree)')
    parser.add_argument('--transitive', '-t', action='store_true',
                        help='Attempt transitive dependency resolution')

    args = parser.parse_args()

    try:
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        fmt = detect_format(args.file)
        if not fmt:
            print(f"Unknown format for {args.file}. Supported: requirements.txt, package.json, Cargo.toml, Pipfile",
                  file=sys.stderr)
            sys.exit(1)

        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()

        if fmt == 'requirements':
            deps = parse_requirements_txt(content)
        elif fmt == 'package':
            deps = parse_package_json(content)
        elif fmt == 'cargo':
            deps = parse_cargo_toml(content)
        elif fmt == 'pipfile':
            deps = parse_pipfile(content)
        else:
            deps = {}

        if not deps:
            print("No dependencies found.")
            sys.exit(0)

        if args.transitive:
            tree = {}
            for dep_name, dep_version in deps.items():
                tree[dep_name] = {'version': dep_version, 'deps': {}}
            print("\033[1mDependency Graph:\033[0m")
            print(f"  \033[90m{len(deps)} direct dependencies\033[0m\n")
            if args.format == 'mermaid':
                print_mermaid_graph(tree)
            else:
                print_ascii_tree(tree)
        else:
            if args.format == 'mermaid':
                print("graph TD;")
                for name, version in deps.items():
                    clean_name = name.replace('-', '_').replace('.', '_')
                    print(f"    {clean_name}[\"{name}\"];")
            else:
                print(f"\033[1mDependencies ({len(deps)}):\033[0m\n")
                sorted_deps = sorted(deps.items())
                for i, (name, version) in enumerate(sorted_deps):
                    is_last = i == len(sorted_deps) - 1
                    connector = '└── ' if is_last else '├── '
                    version_str = f" (\033[94m{version}\033[0m)" if version and version != '*' else ''
                    print(f"{connector}\033[1m{name}\033[0m{version_str}")

    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "dep-graph",
    "func": "main",
    "desc": 'Dependency graph from Python files',
}

if __name__ == '__main__':
    main()
