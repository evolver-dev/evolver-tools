"""crypto-box — Security toolkit (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "crypto-box", "desc": "Security: encrypt, hash, password, OTP, SSL — CLI+TUI", "func": "cli_main"}

try:
    from crypto_box.cli import cli_main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/crypto-box/src")
    from crypto_box.cli import cli_main
