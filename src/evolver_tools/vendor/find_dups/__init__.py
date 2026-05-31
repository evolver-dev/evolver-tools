"""
find-dups — Find duplicate files by SHA256 content hash.

Zero external dependencies, stdlib only.
"""

__version__ = "1.0.0"

# === Auto-registration metadata ===
TOOL_META = {
    "name": "find-dups",
    "func": "main",
    "desc": 'Find duplicate files by SHA256 hash, size, or name',
    "submodule": "cli",
}
