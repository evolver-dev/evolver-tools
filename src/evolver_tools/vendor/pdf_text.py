#!/usr/bin/env python3
"""pdf-text — Extract text from PDF files (pure Python, no external deps)."""
import os, sys, re, json, struct, zlib
from pathlib import Path

TOOL_META = {
    "name": "pdf-text",
    "desc": "Extract text from PDF files (pure Python, no external deps)",
    "func": "main",
}

class SimplePDFExtractor:
    """Minimal PDF text extractor. Handles simple PDFs without external libs."""

    def __init__(self, path):
        self.path = path
        self.content = b""
        self.objects = {}

    def load(self):
        with open(self.path, "rb") as f:
            self.content = f.read()
        return self

    def _find_xref(self):
        """Find the xref table location."""
        idx = self.content.rfind(b"startxref")
        if idx < 0:
            return 0
        line_end = self.content.find(b"\n", idx)
        if line_end < 0:
            return 0
        xref_pos = self.content[idx+10:line_end].strip()
        try:
            return int(xref_pos)
        except ValueError:
            return 0

    def _parse_object(self, obj_num):
        """Extract a PDF object by number."""
        marker = f"{obj_num} 0 obj".encode()
        start = self.content.find(marker)
        if start < 0:
            return None
        end = self.content.find(b"endobj", start)
        if end < 0:
            return None
        obj_data = self.content[start + len(marker):end]
        return obj_data.strip()

    def _decompress_stream(self, data):
        """Try to decompress a stream."""
        try:
            return zlib.decompress(data)
        except:
            return data

    def extract_text(self):
        """Extract text from all pages."""
        self.load()
        text_parts = []
        stream_pattern = re.compile(rb"stream\s(.+?)\s*endstream", re.DOTALL)
        text_pattern = re.compile(rb"\((.*?)\)\s*Tj")
        tj_text_pattern = re.compile(rb"\[(.*?)\]\s*TJ")
        hex_pattern = re.compile(rb"<([0-9A-Fa-f]+)>\s*Tj")

        for match in stream_pattern.finditer(self.content):
            raw = match.group(1).strip()
            data = self._decompress_stream(raw)
            page_text = []

            # Extract Tj operators ( (text) Tj )
            for m in text_pattern.finditer(data):
                t = m.group(1)
                try:
                    decoded = t.decode("latin-1").replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
                    # Unescape PDF string escapes
                    decoded = re.sub(r"\\([nrt\(\)\\])", lambda m: {"n": "\n", "r": "\r", "t": "\t", "(": "(", ")": ")", "\\": "\\"}.get(m.group(1), m.group(1)), decoded)
                    page_text.append(decoded)
                except:
                    pass

            # Extract TJ operators ( [(text) num (text) ...] TJ )
            for m in tj_text_pattern.finditer(data):
                inner = m.group(1)
                parts = re.findall(rb"\(([^)]*)\)", inner)
                for p in parts:
                    try:
                        decoded = p.decode("latin-1").replace("\\n", "\n").replace("\\r", "\r")
                        page_text.append(decoded)
                    except:
                        pass

            # Extract hex strings
            for m in hex_pattern.finditer(data):
                hex_str = m.group(1).decode("ascii", errors="replace")
                try:
                    page_text.append(bytes.fromhex(hex_str).decode("latin-1", errors="replace"))
                except:
                    pass

            if page_text:
                text_parts.append("".join(page_text))

        return "\n".join(text_parts)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract text from PDF files")
    parser.add_argument("input", nargs="?", help="PDF file to extract")
    parser.add_argument("-o", "--output", default="", help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--pages", action="store_true", help="Show page info")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        return

    path = Path(args.input)
    if not path.exists():
        print(f"File not found: {args.input}")
        sys.exit(1)

    try:
        extractor = SimplePDFExtractor(str(path))
        text = extractor.extract_text()

        if args.output:
            with open(args.output, "w") as f:
                f.write(text)
            print(f"Text extracted to: {args.output}")
        elif args.json:
            print(json.dumps({
                "file": str(path),
                "size_bytes": path.stat().st_size,
                "text": text,
                "char_count": len(text),
            }, indent=2))
        else:
            print(text)

        print(f"\n--- {path.name}: {len(text)} chars extracted ---", file=sys.stderr)

    except Exception as e:
        print(f"Error extracting text: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
