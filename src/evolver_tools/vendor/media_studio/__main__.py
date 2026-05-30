#!/usr/bin/env python3
"""media-studio — CLI+TUI media utility toolkit.

Zero external dependencies. Pure Python stdlib only.
Combines: image metadata, QR code generator, ASCII art, banners, Morse code.

Usage:
    media-studio                  # Show help
    media-studio qr "text"        # Generate QR code
    media-studio ascii "text"     # ASCII art
    media-studio banner "text"    # Banner text
    media-studio morse "text"     # Text to Morse code
    media-studio meta image.jpg   # Image metadata
    media-studio figlet "text"    # Figlet-style ASCII
    media-studio tui              # Interactive TUI mode
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
