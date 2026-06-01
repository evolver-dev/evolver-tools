"""code-auditor — Code analysis suite (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "code-auditor", "desc": "Code analysis: complexity, security, style, deps — CLI+TUI", "func": "main"}

try:
    from code_auditor.cli import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/code-auditor/src")
    from code_auditor.cli import main
