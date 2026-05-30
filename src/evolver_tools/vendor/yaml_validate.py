#!/usr/bin/env python3
"""yaml-validate — Validate YAML files."""
import sys

TOOL_META = {
    "name": "yaml-validate",
    "func": "main",
    "desc": "Validate YAML syntax. Usage: yaml-validate <file.yaml>",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: yaml-validate <file.yaml>")
        return
    filepath = args[0]
    # Try PyYAML first
    try:
        import yaml
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            if data is not None:
                print(f"✓ {filepath}: valid YAML")
            else:
                print(f"⚠ {filepath}: valid YAML (empty/null document)")
        except yaml.YAMLError as e:
            print(f"✗ YAML error in {filepath}:")
            if hasattr(e, 'problem_mark'):
                print(f"  Line {e.problem_mark.line + 1}, column {e.problem_mark.column + 1}:")
            print(f"  {e}")
            sys.exit(1)
    except ImportError:
        # Fallback: basic validation
        try:
            with open(filepath) as f:
                lines = f.readlines()
            issues = []
            for i, line in enumerate(lines, 1):
                stripped = line.rstrip("\n")
                if "\t" in stripped:
                    issues.append(f"Line {i}: contains tab (YAML uses spaces)")
                if stripped and not stripped.startswith(" "):
                    if ":" not in stripped and not stripped.startswith("#"):
                        if i > 1 and lines[i-2].strip():
                            pass  # Might be a list item
            if issues:
                print(f"⚠ Potential issues ({len(issues)}):")
                for iss in issues:
                    print(f"  {iss}")
            else:
                print(f"✓ {filepath}: passes basic check")
            print("Tip: Install PyYAML for full validation: pip install pyyaml", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
