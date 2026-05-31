#!/usr/bin/env python3
"""macrogen — Macro/code template generator with built-in templates.

Takes a template file or built-in template and renders it with variables
using string.Template substitution ($var or ${var}).

Usage:
    macrogen <template_name> [key=value ...]
    macrogen --template <path> [key=value ...]
    macrogen --list
    cat template.tpl | macrogen [key=value ...]
"""

import argparse
import os
import sys
import string
from pathlib import Path

TOOL_META = {
    "name": "macrogen",
    "func": "main",
    "desc": "Macro/code template generator with built-in templates. "
    "Usage: macrogen <name> [key=val ...] | macrogen --list | "
    "macrogen -t <path> [key=val ...]",
}

# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

BUILTIN_TEMPLATES = {}

BUILTIN_TEMPLATES["app.py"] = r'''#!/usr/bin/env python3
"""${description}"""

from ${framework} import ${imports}

app = ${app_var}(__name__)
app.config["DEBUG"] = ${debug}


@app.route("/")
def index():
    return "${index_message}"


@app.route("/${health_endpoint}")
def health():
    return jsonify({"status": "${health_status}"})


if __name__ == "__main__":
    app.run(host="${host}", port=${port})
'''

BUILTIN_TEMPLATES["app.js"] = r'''#!/usr/bin/env node

const express = require("${express_pkg}");
const app = express();
const port = process.env.PORT || ${port};

app.use(express.json());
app.use(express.urlencoded({ extended: ${extended} }));

app.get("/", (req, res) => {
  res.json({ message: "${index_message}" });
});

app.get("/${health_endpoint}", (req, res) => {
  res.json({ status: "${health_status}" });
});

app.listen(port, () => {
  console.log("${app_name} listening on port ${port}");
});
'''

BUILTIN_TEMPLATES["Dockerfile"] = r'''# syntax=docker/dockerfile:1
FROM ${base_image}

WORKDIR ${workdir}

${copy_cmds}

COPY . .

EXPOSE ${port}

CMD ${cmd}
'''

BUILTIN_TEMPLATES["Makefile"] = r'''.PHONY: all clean test build run ${extra_phony}

${project_name}:
	@echo "Running ${project_name}"

all: ${all_targets}

test:
	${test_cmd}

build:
	${build_cmd}

run:
	${run_cmd}

clean:
	rm -rf ${clean_targets}

${extra_rules}
'''

BUILTIN_TEMPLATES[".gitignore"] = r'''# ${project_name} .gitignore

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
env/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

${extra_ignore}
'''

BUILTIN_TEMPLATES["README.md"] = r'''# ${project_name}

${description}

## Installation

${install_cmd}

## Usage

${usage_cmd}

## License

${license}
'''

BUILTIN_TEMPLATES["config.yaml"] = r'''# ${project_name} configuration
---
server:
  host: "${host}"
  port: ${port}
  debug: ${debug}

logging:
  level: "${log_level}"
  format: "${log_format}"

${extra_config}
'''


def get_builtin_template(name: str) -> str:
    """Return the template string for a built-in template."""
    if name in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[name]
    available = sorted(BUILTIN_TEMPLATES.keys())
    raise KeyError(
        f"Unknown built-in template: {name!r}. "
        f"Available: {', '.join(available)}"
    )


def list_builtin_templates() -> str:
    """Return a formatted listing of all built-in templates."""
    lines = ["Available built-in templates:", ""]
    for name in sorted(BUILTIN_TEMPLATES.keys()):
        preview = BUILTIN_TEMPLATES[name].strip().split("\n")[0][:60]
        lines.append(f"  {name:20s}  {preview}")
    lines.append("")
    lines.append("Usage:  macrogen <name> [key=value ...]")
    lines.append("        macrogen -t <path/to/template> [key=value ...]")
    lines.append("        cat template.tpl | macrogen [key=value ...]")
    return "\n".join(lines)


def render_template(template_str: str, variables: dict) -> str:
    """Render a template using string.Template substitution.

    Uses the safe_substitute method so undefined placeholders are
    left as-is rather than raising KeyError.
    """
    t = string.Template(template_str)
    return t.safe_substitute(**variables)


def parse_key_value_pairs(items: list) -> dict:
    """Parse a list of 'key=value' strings into a dict.

    Accepts bare keys (no '=') as boolean flags (set to 'true').
    """
    variables = {}
    for item in items:
        if "=" in item:
            key, _, value = item.partition("=")
            variables[key.strip()] = value.strip()
        else:
            variables[item.strip()] = "true"
    return variables


def load_template_file(path: str) -> str:
    """Read a template file from disk."""
    p = Path(path)
    if not p.exists():
        print(f"Error: template file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def main(argv: list | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="macrogen",
        description="Macro/code template generator with built-in templates.",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Template name followed by key=value pairs, or just key=value pairs",
    )
    parser.add_argument(
        "-t", "--template",
        dest="template_path",
        metavar="PATH",
        help="Path to a custom template file",
    )
    parser.add_argument(
        "--vars",
        nargs="+",
        metavar="KEY=VALUE",
        help="Additional variable definitions (key=value pairs)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all built-in templates and exit",
    )

    parsed = parser.parse_args(argv)

    # --list flag
    if parsed.list:
        print(list_builtin_templates())
        return

    # Collect variable definitions from positional args and --vars
    positional = list(parsed.args)
    variables = {}
    template_name = None
    template_source = None

    # If --template is given, all positional args are variable definitions
    if parsed.template_path:
        template_source = load_template_file(parsed.template_path)
        variables.update(parse_key_value_pairs(positional))
    else:
        # Separate template name from variable definitions
        if positional and "=" not in positional[0] and positional[0] not in ("-",):
            template_name = positional[0]
            variables.update(parse_key_value_pairs(positional[1:]))
        else:
            # No template name — check stdin or use all as vars
            variables.update(parse_key_value_pairs(positional))

    # Apply --vars if provided
    if parsed.vars:
        variables.update(parse_key_value_pairs(parsed.vars))

    # Resolve template source
    if template_source is None:
        if template_name is not None:
            try:
                template_source = get_builtin_template(template_name)
            except KeyError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif not sys.stdin.isatty():
            template_source = sys.stdin.read()
        else:
            print(
                "Error: no template provided. Use a built-in name, "
                "--template <path>, or pipe a template via stdin.",
                file=sys.stderr,
            )
            print(file=sys.stderr)
            print(list_builtin_templates(), file=sys.stderr)
            sys.exit(1)

    # Render
    result = render_template(template_source, variables)

    # Output
    if parsed.output:
        output_path = Path(parsed.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
        print(f"Written to: {output_path.resolve()}")
    else:
        sys.stdout.write(result)
        # Ensure trailing newline
        if not result.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
