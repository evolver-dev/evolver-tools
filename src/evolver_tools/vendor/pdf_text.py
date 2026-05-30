#!/usr/bin/env python3
"""pdf-text — Extract text from PDF files."""
import os
import sys

TOOL_META = {
    "name": "pdf-text",
    "func": "main",
    "desc": "Extract text from PDF. Usage: pdf-text <file.pdf> [--pages 1-5]",
}

def extract_pymupdf(filepath, page_range=None):
    try:
        import fitz
    except ImportError:
        return None
    doc = fitz.open(filepath)
    texts = []
    pages = list(range(len(doc)))
    if page_range:
        parts = page_range.split("-")
        if len(parts) == 2:
            start = max(0, int(parts[0]) - 1)
            end = min(len(doc), int(parts[1]))
            pages = list(range(start, end))
        else:
            pages = [max(0, int(page_range) - 1)]
    for i in pages:
        page = doc[i]
        text = page.get_text()
        if text.strip():
            texts.append(f"--- Page {i+1} ---\n{text}")
    doc.close()
    return "\n\n".join(texts)

def extract_pypdf(filepath, page_range=None):
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        try:
            from pypdf import PdfReader
        except ImportError:
            return None
    reader = PdfReader(filepath)
    texts = []
    pages = list(range(len(reader.pages)))
    if page_range:
        parts = page_range.split("-")
        if len(parts) == 2:
            start = max(0, int(parts[0]) - 1)
            end = min(len(reader.pages), int(parts[1]))
            pages = list(range(start, end))
        else:
            pages = [max(0, int(page_range) - 1)]
    for i in pages:
        text = reader.pages[i].extract_text()
        if text.strip():
            texts.append(f"--- Page {i+1} ---\n{text}")
    return "\n\n".join(texts)

def extract_pdfminer(filepath, page_range=None):
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return None
    text = extract_text(filepath)
    return text

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: pdf-text <file.pdf> [--pages 1-5]", file=sys.stderr)
        print("Extracts text from PDF files.", file=sys.stderr)
        print("Supports: PyMuPDF, PyPDF2/pypdf, pdfminer.six", file=sys.stderr)
        sys.exit(1)
    filepath = args[0]
    page_range = None
    if "--pages" in args:
        idx = args.index("--pages")
        if idx + 1 < len(args):
            page_range = args[idx + 1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    for extractor in [extract_pymupdf, extract_pypdf, extract_pdfminer]:
        text = extractor(filepath, page_range)
        if text is not None:
            print(text)
            return
    print("Error: No PDF library found. Install one:", file=sys.stderr)
    print("  pip install pymupdf  (recommended)", file=sys.stderr)
    print("  pip install PyPDF2", file=sys.stderr)
    print("  pip install pdfminer.six", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
