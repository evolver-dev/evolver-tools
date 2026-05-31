#!/usr/bin/env python3
"""
file-type — Detect file type using magic bytes (no external deps).

Usage: file-type somefile.bin
       file-type *  (batch mode)
       file-type --mime somefile
       file-type --describe somefile
"""

import os
import sys
import struct


MAGIC_BYTES: list[tuple[str, str, str, bytes | None]] = [
    # (name, mime, description, magic_hex)
    ("png", "image/png", "PNG image", b"\x89PNG\r\n\x1a\n"),
    ("jpeg", "image/jpeg", "JPEG image", b"\xff\xd8\xff"),
    ("gif", "image/gif", "GIF image", b"GIF87a"),
    ("gif", "image/gif", "GIF image", b"GIF89a"),
    ("pdf", "application/pdf", "PDF document", b"%PDF"),
    ("zip", "application/zip", "ZIP archive", b"PK\x03\x04"),
    ("gzip", "application/gzip", "GZIP compressed", b"\x1f\x8b\x08"),
    ("elf", "application/x-elf", "ELF binary", b"\x7fELF"),
    ("bmp", "image/bmp", "BMP image", b"BM"),
    ("ico", "image/x-icon", "ICO icon", b"\x00\x00\x01\x00"),
    ("sqlite", "application/x-sqlite3", "SQLite database", b"SQLite format 3\x00"),
    # WebP: RIFF....WEBP  (RIFF + 4 bytes size + WEBP)
    ("webp", "image/webp", "WebP image", None),  # special-cased below
]

# Extension-based fallbacks
EXT_MAP: dict[str, tuple[str, str]] = {
    ".py":     ("python", "Python script"),
    ".js":     ("javascript", "JavaScript source"),
    ".c":      ("c", "C source"),
    ".h":      ("c-header", "C header"),
    ".cpp":    ("cpp", "C++ source"),
    ".hpp":    ("cpp-header", "C++ header"),
    ".rs":     ("rust", "Rust source"),
    ".go":     ("go", "Go source"),
    ".rb":     ("ruby", "Ruby source"),
    ".java":   ("java", "Java source"),
    ".md":     ("markdown", "Markdown document"),
    ".markdown": ("markdown", "Markdown document"),
    ".csv":    ("csv", "CSV spreadsheet"),
    ".yml":    ("yaml", "YAML data"),
    ".yaml":   ("yaml", "YAML data"),
    ".toml":   ("toml", "TOML data"),
    ".svg":    ("svg", "SVG vector image"),
    ".ts":     ("typescript", "TypeScript source"),
    ".tsx":    ("tsx", "TypeScript JSX source"),
    ".jsx":    ("jsx", "JavaScript JSX source"),
    ".kt":     ("kotlin", "Kotlin source"),
    ".swift":  ("swift", "Swift source"),
}


def _read_chunk(path: str, size: int = 16) -> bytes:
    """Read first *size* bytes from *path*."""
    with open(path, "rb") as f:
        return f.read(size)


def _check_webp(data: bytes) -> bool:
    """Detect WebP: starts with RIFF, 4-byte size, then WEBP."""
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def detect(path: str) -> tuple[str, str, str]:
    """
    Return (type_name, mime, description) for *path*.

    Detection order:
      1. Magic bytes (first 16 bytes)
      2. Shebang analysis (reads up to 256 bytes)
      3. Content heuristics (JSON/XML/HTML/YAML/TOML)
      4. Extension fallback
      5. Binary / text classification
    """
    try:
        data = _read_chunk(path)
    except (OSError, IOError) as exc:
        return ("error", "application/octet-stream", str(exc))

    ext = os.path.splitext(path)[1].lower()

    # --- Magic bytes ------------------------------------------------------------
    # WebP (special pattern)
    if _check_webp(data):
        return ("webp", "image/webp", "WebP image")

    for name, mime, desc, magic in MAGIC_BYTES:
        if magic and data.startswith(magic):
            return (name, mime, desc)

    # --- Shebang ----------------------------------------------------------------
    if data.startswith(b"#!"):
        # Read up to 256 bytes to capture the full shebang line
        shebang_data = _read_chunk(path, size=256)
        shebang_end = shebang_data.find(b"\n")
        if shebang_end > 0:
            shebang_line = shebang_data[:shebang_end].decode("utf-8", errors="replace").strip()
        else:
            shebang_line = shebang_data.decode("utf-8", errors="replace").strip()
        shebang_lower = shebang_line.lower()

        if "python" in shebang_lower:
            return ("python", "text/x-python", "Python script (shebang)")
        if "/bin/sh" in shebang_lower or "/bin/bash" in shebang_lower or "bash" in shebang_lower:
            return ("shell", "text/x-shellscript", "Shell script (shebang)")

        if "node" in shebang_lower:
            return ("javascript", "text/javascript", "JavaScript script (shebang)")
        if "ruby" in shebang_lower:
            return ("ruby", "text/x-ruby", "Ruby script (shebang)")
        if "perl" in shebang_lower:
            return ("perl", "text/x-perl", "Perl script (shebang)")
        if "lua" in shebang_lower:
            return ("lua", "text/x-lua", "Lua script (shebang)")
        if "env" in shebang_lower:
            return ("script", "text/plain", f"Script ({shebang_line[2:].strip()})")

    # --- Content heuristics ----------------------------------------------------
    text_sample = data.decode("utf-8", errors="replace").strip() if data else ""

    if text_sample:
        stripped = text_sample.strip()
        first_line = text_sample.split("\n")[0].strip()

        # TOML (check before JSON — [section] headers look like JSON arrays)
        if "[package]" in text_sample or (first_line.startswith("[") and first_line.endswith("]")):
            return ("toml", "application/toml", "TOML data")

        # JSON
        if stripped.startswith("{") or stripped.startswith("["):
            # A single [text] is TOML, not JSON — already caught above.
            # JSON starts with {obj} or [arr] — verify there's content after.
            return ("json", "application/json", "JSON data")

        # XML / HTML
        if "<" in text_sample:
            # Check for <?xml declaration (may span >16 bytes)
            if text_sample.lstrip().startswith("<?xml"):
                return ("xml", "application/xml", "XML document")
            # HTML doctype
            upper = text_sample.strip().upper()
            if upper.startswith("<!DOCTYPE") or text_sample.strip().lower().startswith("<html"):
                return ("html", "text/html", "HTML document")
            # SVG inline
            if "<svg" in text_sample.lower():
                return ("svg", "image/svg+xml", "SVG vector image")
            # Generic XML — starts with <, ends with > (or starts with <?)
            if stripped.startswith("<") and (">" in text_sample):
                stripped_end = stripped.rstrip()
                if stripped_end.endswith(">"):
                    return ("xml", "application/xml", "XML document")

        # YAML
        yaml_starts = ("---", "name:", "version:", "apiVersion:", "kind:", "spec:")
        if first_line in ("---", "...") or first_line.startswith(yaml_starts):
            return ("yaml", "application/x-yaml", "YAML data")

    # --- Extension fallback ----------------------------------------------------
    if ext in EXT_MAP:
        name, desc = EXT_MAP[ext]
        # Derive MIME from name
        _mime_map = {
            "python": "text/x-python",
            "javascript": "text/javascript",
            "c": "text/x-c",
            "c-header": "text/x-c",
            "cpp": "text/x-c++",
            "cpp-header": "text/x-c++",
            "rust": "text/x-rust",
            "go": "text/x-go",
            "ruby": "text/x-ruby",
            "java": "text/x-java",
            "markdown": "text/markdown",
            "csv": "text/csv",
            "yaml": "application/x-yaml",
            "toml": "application/toml",
            "svg": "image/svg+xml",
            "typescript": "text/typescript",
            "tsx": "text/typescript-jsx",
            "jsx": "text/jsx",
            "kotlin": "text/x-kotlin",
            "swift": "text/x-swift",
        }
        mime = _mime_map.get(name, "text/plain")
        return (name, mime, desc)

    # --- Binary / text classification -----------------------------------------
    # Check if data is mostly text
    if not data:
        return ("empty", "application/x-empty", "Empty file")

    text_chars = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
    ratio = text_chars / len(data) if data else 1.0

    if ratio > 0.9:
        return ("text", "text/plain", "Text file")
    else:
        return ("binary", "application/octet-stream", "Binary data")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    show_mime = False
    show_describe = True
    brief = False

    # Filter out flags
    files = []
    for a in args:
        if a == "--mime":
            show_mime = True
            show_describe = False
        elif a == "--describe":
            show_mime = False
            show_describe = True
        elif a == "--brief":
            brief = True
        elif a.startswith("-"):
            print(f"Unknown option: {a}", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(a)

    if not files:
        print(__doc__.strip())
        sys.exit(1)

    # Expand globs
    expanded = []
    for f in files:
        if "*" in f or "?" in f:
            import glob
            expanded.extend(sorted(glob.glob(f)))
        else:
            expanded.append(f)
    files = expanded

    batch = len(files) > 1
    exit_code = 0

    if show_mime:
        for path in files:
            if not os.path.exists(path):
                if batch:
                    print(f"{path}: error: File not found")
                else:
                    print("File not found")
                exit_code = 1
                continue
            name, mime, _ = detect(path)
            prefix = f"{path}: " if batch else ""
            print(f"{prefix}{mime}")
    elif brief:
        for path in files:
            if not os.path.exists(path):
                if batch:
                    print(f"{path}: error: File not found")
                else:
                    print("error")
                exit_code = 1
                continue
            name, _, _ = detect(path)
            prefix = f"{path}: " if batch else ""
            print(f"{prefix}{name}")
    else:
        for path in files:
            if not os.path.exists(path):
                if batch:
                    print(f"{path}: error: File not found")
                else:
                    print("File not found")
                exit_code = 1
                continue
            name, _, desc = detect(path)
            prefix = f"{path}: " if batch else ""
            print(f"{prefix}{desc}")

    sys.exit(exit_code)


TOOL_META = {
    "name": "file-type",
    "func": "main",
    "desc": "Detect file type using magic bytes"
}

if __name__ == "__main__":
    main()
