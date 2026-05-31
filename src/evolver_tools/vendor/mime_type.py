#!/usr/bin/env python3
"""mime-type — Detect file MIME types by extension and magic bytes."""
TOOL_META = {"name": "mime-type", "func": "main", "desc": "Detect MIME type of files by extension and magic bytes"}

MIME_DB = {
    ".txt": "text/plain", ".html": "text/html", ".htm": "text/html",
    ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript",
    ".json": "application/json", ".xml": "application/xml", ".yaml": "text/yaml",
    ".yml": "text/yaml", ".toml": "text/x-toml", ".ini": "text/plain",
    ".csv": "text/csv", ".tsv": "text/tab-separated-values",
    ".md": "text/markdown", ".rst": "text/x-rst",
    ".py": "text/x-python", ".pyw": "text/x-python",
    ".java": "text/x-java", ".c": "text/x-c", ".cpp": "text/x-c++",
    ".h": "text/x-c-header", ".hpp": "text/x-c++-header",
    ".go": "text/x-go", ".rs": "text/x-rust", ".rb": "text/x-ruby",
    ".php": "text/x-php", ".pl": "text/x-perl",
    ".sh": "application/x-sh", ".bash": "application/x-sh",
    ".bat": "application/x-bat", ".ps1": "text/x-powershell",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".ico": "image/x-icon", ".bmp": "image/bmp", ".tiff": "image/tiff",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
    ".flac": "audio/flac", ".aac": "audio/aac", ".m4a": "audio/mp4",
    ".mp4": "video/mp4", ".avi": "video/x-msvideo", ".mov": "video/quicktime",
    ".mkv": "video/x-matroska", ".webm": "video/webm", ".flv": "video/x-flv",
    ".pdf": "application/pdf", ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip", ".tar": "application/x-tar",
    ".gz": "application/gzip", ".bz2": "application/x-bzip2",
    ".xz": "application/x-xz", ".7z": "application/x-7z-compressed",
    ".rar": "application/vnd.rar",
    ".exe": "application/x-msdownload", ".dll": "application/x-msdownload",
    ".so": "application/x-sharedlib", ".dylib": "application/x-mach-binary",
    ".deb": "application/vnd.debian.binary-package",
    ".rpm": "application/x-rpm",
    ".iso": "application/x-iso9660-image",
    ".bin": "application/octet-stream",
    ".woff": "font/woff", ".woff2": "font/woff2",
    ".ttf": "font/ttf", ".otf": "font/otf",
    ".eot": "application/vnd.ms-fontobject",
    ".wasm": "application/wasm",
    ".sql": "text/x-sql", ".db": "application/x-sqlite3",
    ".log": "text/plain", ".env": "text/plain", ".cfg": "text/plain",
    ".conf": "text/plain", ".lock": "text/plain",
}

MAGIC_BYTES = {
    bytes([0xFF, 0xD8, 0xFF]): "image/jpeg",
    bytes([0x89, 0x50, 0x4E, 0x47]): "image/png",
    bytes([0x47, 0x49, 0x46, 0x38]): "image/gif",
    bytes([0x52, 0x49, 0x46, 0x46]): "image/webp",
    bytes([0x25, 0x50, 0x44, 0x46]): "application/pdf",
    bytes([0x50, 0x4B, 0x03, 0x04]): "application/zip",
    bytes([0x1F, 0x8B, 0x08]): "application/gzip",
    bytes([0x42, 0x5A, 0x68]): "application/x-bzip2",
    bytes([0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00]): "application/x-xz",
    bytes([0x7F, 0x45, 0x4C, 0x46]): "application/x-elf",
    bytes([0xCA, 0xFE, 0xBA, 0xBE]): "application/java-vm",
    bytes([0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70]): "video/mp4",
    bytes([0x1A, 0x45, 0xDF, 0xA3]): "video/x-matroska",
    bytes([0x4D, 0x5A]): "application/x-msdownload",
    bytes([0x23, 0x21]): "text/x-script",
    bytes([0xEF, 0xBB, 0xBF]): "text/plain; charset=utf-8-bom",
    bytes([0xFF, 0xFE]): "text/plain; charset=utf-16le",
    bytes([0xFE, 0xFF]): "text/plain; charset=utf-16be",
}


def detect_mime(path):
    """Detect MIME type, preferring magic bytes over extension."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
        for magic, mime in MAGIC_BYTES.items():
            if head[:len(magic)] == magic:
                return mime, "magic"
    except Exception:
        pass

    import os
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in MIME_DB:
        return MIME_DB[ext], "extension"
    return "application/octet-stream", "unknown"


def main():
    import sys, os
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: mime-type <file> [file...]")
        print("Detect MIME type of one or more files.")
        print("  mime-type foo.pdf bar.png")
        return

    for path in args:
        if not os.path.exists(path):
            print(f"Error: {path} not found", file=sys.stderr)
            continue
        mime, source = detect_mime(path)
        if len(args) > 1:
            print(f"{path}: {mime} ({source})")
        else:
            print(mime)


if __name__ == "__main__":
    main()
