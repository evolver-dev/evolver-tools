#!/usr/bin/env python3
"""macrogen — Code generation from templates (Python, CLI, scripts)."""
import os, sys, re, json, textwrap
from pathlib import Path
from datetime import datetime

TOOL_META = {
    "name": "macrogen",
    "desc": "Code generation from templates (Python, CLI, scripts)",
    "func": "main",
}

TEMPLATES = {
    "python-script": {
        "desc": "Basic Python script with argparse",
        "ext": ".py",
        "content": """#!/usr/bin/env python3
\"\"\"{name} — {desc}\"\"\"
import sys, os, argparse

def main():
    parser = argparse.ArgumentParser(description=\"{desc}\")
    parser.add_argument(\"input\", nargs=\"?\", help=\"Input file\")
    parser.add_argument(\"-v\", \"--verbose\", action=\"store_true\", help=\"Verbose\")
    args = parser.parse_args()

    if args.verbose:
        print(f\"Running {name}...\")
    # TODO: implement
    print(\"Hello from {name}!\")

if __name__ == \"__main__\":
    main()
""",
    },
    "cli-tool": {
        "desc": "CLI tool with TOOL_META for evolver-tools",
        "ext": ".py",
        "content": """#!/usr/bin/env python3
\"\"\"{name} — {desc}\"\"\"
import sys, os, argparse

TOOL_META = {{
    "name": "{name}",
    "desc": "{desc}",
    "func": "main",
}}

def main():
    parser = argparse.ArgumentParser(description=\"{desc}\")
    parser.add_argument(\"input\", nargs=\"?\", help=\"Input\")
    args = parser.parse_args()
    # TODO: implement
    print(\"{name}: hello!\")

if __name__ == \"__main__\":
    main()
""",
    },
    "flask-api": {
        "desc": "Flask REST API skeleton",
        "ext": ".py",
        "content": '''"""Flask REST API — {name} — {desc}"""
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({{"status": "ok"}})

@app.route("/api/v1/{name}", methods=["GET"])
def list_items():
    return jsonify({{"items": []}})

@app.route("/api/v1/{name}", methods=["POST"])
def create_item():
    data = request.get_json()
    return jsonify({{"created": data}}), 201

if __name__ == "__main__":
    app.run(debug=True)
''',
    },
    "makefile": {
        "desc": "Basic Makefile for Python projects",
        "ext": "",
        "content": """# {name} — {desc}
.PHONY: install test clean build publish

install:
\tpip install -e .

test:
\tpython -m pytest tests/ -v

clean:
\trm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache

build: clean
\tpython -m build

publish: build
\ttwine upload dist/*
""",
    },
    "github-actions": {
        "desc": "GitHub Actions CI workflow",
        "ext": ".yml",
        "content": """# {name} — {desc}
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{{{ matrix.python-version }}}}
    - name: Install
      run: pip install -e .
    - name: Test
      run: python -m pytest tests/ -v
""",
    },
}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Code generation from templates")
    parser.add_argument("template", nargs="?", help="Template name")
    parser.add_argument("-o", "--output", default="", help="Output filename/dir")
    parser.add_argument("-d", "--desc", default="Auto-generated tool", help="Description")
    parser.add_argument("-n", "--name", default="my_tool", help="Project/tool name")
    parser.add_argument("-l", "--list", action="store_true", help="List available templates")
    args = parser.parse_args()

    if args.list or not args.template:
        print("Available templates:")
        for name, tpl in sorted(TEMPLATES.items()):
            print(f"  {name:20s} {tpl['desc']}")
        print(f"\nUsage: macrogen <template> -n my_tool -o output_path")
        return

    if args.template not in TEMPLATES:
        print(f"Unknown template: {args.template}")
        print(f"Use --list to see available templates")
        sys.exit(1)

    tpl = TEMPLATES[args.template]
    content = tpl["content"].format(name=args.name, desc=args.desc)

    output = args.output or args.name + tpl.get("ext", "")
    with open(output, "w") as f:
        f.write(content)
    print(f"Generated: {output} ({len(content.splitlines())} lines)")

    if tpl["ext"] == ".py":
        os.chmod(output, 0o755)

if __name__ == "__main__":
    main()
