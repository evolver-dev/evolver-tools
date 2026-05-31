#!/usr/bin/env python3
"""template — File scaffolding tool for projects and CLI tools."""

import os
import sys

TOOL_META = {
    "name": "template",
    "func": "main",
    "desc": "Project scaffolding. Usage: template init <name> | template python <name> | template cli <name>",
}


def create_file(path, content):
    """Create a file with given content, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  Created: {path}")


def cmd_init(args):
    if not args:
        print("Error: missing project name. Usage: template init <name>", file=sys.stderr)
        sys.exit(1)
    name = args[0]
    base = os.path.join(os.getcwd(), name)
    print(f"Creating project: {name}")
    print()

    create_file(os.path.join(base, "README.md"), f"# {name}\n\nProject description.\n")
    create_file(os.path.join(base, ".gitignore"), "*.pyc\n__pycache__/\n.env\nvenv/\nnode_modules/\n")
    create_file(os.path.join(base, "LICENSE"), "MIT License\n\nCopyright (c) 2025\n")
    create_file(os.path.join(base, "src", "__init__.py"), "")
    create_file(os.path.join(base, "tests", "__init__.py"), "")
    create_file(os.path.join(base, "Makefile"), f""".PHONY: test clean

test:
\tpython -m pytest

clean:
\trm -rf __pycache__ .pytest_cache
\trm -rf *.egg-info dist build
""")

    print()
    print(f"Project '{name}' created at {base}")


def cmd_python(args):
    if not args:
        print("Error: missing project name. Usage: template python <name>", file=sys.stderr)
        sys.exit(1)
    name = args[0]
    base = os.path.join(os.getcwd(), name)
    pkg = name.replace("-", "_").replace(" ", "_")
    print(f"Creating Python project: {name}")
    print()

    create_file(os.path.join(base, "README.md"), f"# {name}\n\nPython project description.\n")
    create_file(os.path.join(base, "pyproject.toml"), f"""[build-system]
requires = ["setuptools>=64.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = ""
requires-python = ">=3.8"
""")
    create_file(os.path.join(base, ".gitignore"), "*.pyc\n__pycache__/\n.env\nvenv/\n*.egg-info\ndist/\nbuild/\n")
    create_file(os.path.join(base, "src", pkg, "__init__.py"), f'"""TODO: package description."""\n__version__ = "0.1.0"\n')
    create_file(os.path.join(base, "src", pkg, "main.py"), f"""#!/usr/bin/env python3
\"\"\"Main entry point for {name}.\"\"\"

import sys


def main():
    args = sys.argv[1:]
    print(f"{name}: hello world, got args: {{args}}")


if __name__ == "__main__":
    main()
""")
    create_file(os.path.join(base, "tests", "__init__.py"), "")
    create_file(os.path.join(base, "tests", "test_main.py"), f"""import pytest
from {pkg}.main import main


def test_main():
    # TODO: write tests
    pass
""")
    create_file(os.path.join(base, "Makefile"), f""".PHONY: test clean install

install:
\tpip install -e .

test:
\tpython -m pytest

clean:
\trm -rf __pycache__ .pytest_cache
\trm -rf *.egg-info dist build
""")

    print()
    print(f"Python project '{name}' created at {base}")


def cmd_cli(args):
    if not args:
        print("Error: missing CLI tool name. Usage: template cli <name>", file=sys.stderr)
        sys.exit(1)
    name = args[0]
    base = os.path.join(os.getcwd(), name)
    script_name = name.replace("-", "_")
    print(f"Creating CLI tool skeleton: {name}")
    print()

    create_file(os.path.join(base, "README.md"), f"# {name}\n\nCLI tool description.\n")
    create_file(os.path.join(base, "setup.py"), f"""from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    packages=find_packages(),
    entry_points={{
        "console_scripts": [
            "{name}={script_name}.cli:main",
        ],
    }},
)
""")
    create_file(os.path.join(base, ".gitignore"), "*.pyc\n__pycache__/\n*.egg-info\ndist/\nbuild/\n")
    create_file(os.path.join(base, script_name, "__init__.py"), f'"""TODO: package description."""\n__version__ = "0.1.0"\n')
    create_file(os.path.join(base, script_name, "cli.py"), f"""#!/usr/bin/env python3
\"\"\"{name} CLI — description here.\"\"\"

import sys


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: {name} <command> [args]")
        print()
        print("Commands:")
        print("  hello              Print a greeting")
        return

    cmd = args[0]
    if cmd == "hello":
        print("Hello from {name}!")
    else:
        print(f"Unknown command: {{cmd}}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
""")
    create_file(os.path.join(base, "tests", "__init__.py"), "")
    create_file(os.path.join(base, "tests", "test_cli.py"), f"""from {script_name}.cli import main


def test_cli():
    # TODO: write tests
    pass
""")

    print()
    print(f"CLI tool '{name}' created at {base}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: template <command> [name]")
        print()
        print("Commands:")
        print("  init <name>       Create a basic project structure")
        print("  python <name>     Create a Python project skeleton")
        print("  cli <name>        Create a CLI tool skeleton")
        return

    cmd = args[0]
    cmd_args = args[1:]

    commands = {
        "init": cmd_init,
        "python": cmd_python,
        "cli": cmd_cli,
    }

    if cmd in commands:
        commands[cmd](cmd_args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Available: init, python, cli", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
