"""media-studio — Media utility toolkit (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "media-studio", "desc": "Media utilities: QR, ASCII art, banner, Morse, figlet — CLI+TUI", "func": "main"}

try:
    from media_studio.cli import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/media-studio/src")
    from media_studio.cli import main
