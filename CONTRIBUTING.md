# Contributing to EVOLVER Tools

First off, thanks for being here. This project grows through contributions — every new tool, every bug fix, every doc improvement matters.

## Quick Start

```bash
# Clone + install
git clone https://github.com/evolver-dev/evolver-tools.git
cd evolver-tools
pip install -e .

# Verify it works
evtool list
```

## How to Add a New Tool

Each tool is a single Python file in `src/evolver_tools/vendor/`. It must depend only on the standard library.

### 1. Create the tool file

```python
# src/evolver_tools/vendor/my-tool.py
"""description: Do something useful from the command line."""

import sys
import argparse

TOOL_META = {
    "name": "my-tool",
    "func": "main",
    "desc": "Do something useful from the command line",
}

def main():
    parser = argparse.ArgumentParser(description="Do something useful")
    parser.add_argument("input", help="Input value")
    args = parser.parse_args()
    print(f"Result: {args.input}")
    return 0

if __name__ == "__main__":
    main()
```

### 2. Rules for every tool

| Rule | Why |
|------|-----|
| **Zero external dependencies** | Only `import` from Python stdlib. No PyPI packages. |
| **`TOOL_META` dict at module top-level** | Auto-discovery reads this. Required fields: `name`, `func`, `desc`. Optional: `category`, `example`. |
| **Standalone runnable** | `python vendor/my-tool.py` must work. |
| **Single file** | No sub-packages. One `.py` file = one tool. |
| **`main()` returns int** | Exit code. 0 = success, non-zero = error. |
| **`argparse` for arguments** | Consistent UX. Use `ArgumentParser(prog="my-tool")`. |
| **Works cross-platform** | Windows paths, line endings, and encoding. |

### 3. That's it

Create the file, run `evtool list` — your tool is automatically discovered. No registration, no config changes.

## How to Fix a Bug

1. **Find the tool** in `src/evolver_tools/vendor/<tool-name>.py`
2. **Fix the bug**
3. **Test it**: `evtool <tool-name> <test-args>`
4. **Submit a PR** with a clear description of what was wrong

## Code Style

- Python stdlib only (exception: `evolver_tools/` core code may use `argparse`, `os`, `sys`, `json`, `csv`, etc.)
- Functions should be small and focused
- Include `"""description: ..."""` docstring at the top of every tool file
- Use `argparse` for CLI argument parsing
- Return int from `main()` for exit codes

## Pull Request Process

1. **One PR = one tool or one fix.** Keeps reviews fast.
2. Include a brief description of what the tool does.
3. Make sure `evtool list` shows your tool.
4. Make sure your tool runs: `evtool <name> --help`
5. PRs are merged after review.

## Reporting Issues

Open an issue at https://github.com/evolver-dev/evolver-tools/issues

Good bug reports include:
- What you ran (`evtool <name> <args>`)
- What you expected
- What happened instead
- Your OS and Python version (`python --version`)

## Questions?

Open an issue with the "question" label, or reach us at evolver@evolver.dev.

---

**The whole point is: 276 tools today, more tomorrow. Your tool could be #255.**
