"""config-vault — Configuration security toolkit (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "config-vault", "desc": "Config security: validate, encrypt, scan secrets — CLI+TUI", "func": "main"}

try:
    from config_vault.cli import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/config-vault/src")
    from config_vault.cli import main
