#!/usr/bin/env python3
"""pdf-text — Extract text from PDF files.

Usage:
  pdf-text file.pdf
  pdf-text file.pdf -p 1-3,5
  pdf-text file.pdf --json -p 3
  pdf-text --path ./pdfs/ --output combined.txt
  pdf-text file.pdf -o output.txt

Extracts text using pdftotext (poppler-utils), PyMuPDF (fitz),
or falls back to a basic pure-Python extractor.
"""

import json
import os
import re
import struct
import subprocess
import sys
import zlib

TOOL_META = {
    "name": "pdf-text",
    "func": "main",
    "desc": "Extract text from PDF files",
}


# ── helpers ──────────────────────────────────────────────────────────

def _fmt_size(size):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _parse_page_spec(spec, total_pages):
    """Parse page spec like '1-3,5,7-9' into list of 1-based ints."""
    if not spec:
        return None
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                a, b = int(a.strip()), int(b.strip())
                pages.update(range(max(1, a), min(total_pages, b) + 1))
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p)
            except ValueError:
                continue
    return sorted(pages)


# ── detector ─────────────────────────────────────────────────────────

def _find_pdf_engine():
    """Return (engine_name, extract_fn) or raises."""
    # 1) pdftotext
    try:
        r = subprocess.run(
            ["pdftotext", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 or r.returncode == 1:  # 1 = -v prints to stderr but still exits 1 on some versions
            def _pdftotext(path, pages=None):
                cmd = ["pdftotext"]
                if pages:
                    cmd.extend(["-l", str(pages[-1])])
                    if pages[0] > 1:
                        cmd.extend(["-f", str(pages[0])])
                cmd.extend([path, "-"])
                r2 = subprocess.run(cmd, capture_output=True, timeout=120)
                if r2.returncode != 0:
                    raise RuntimeError(r2.stderr.strip() or f"pdftotext failed (exit {r2.returncode})")
                return r2.stdout.decode("utf-8", errors="replace")
            return ("pdftotext (poppler-utils)", _pdftotext)
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # 2) PyMuPDF
    try:
        import fitz

        def _pymupdf(path, pages=None):
            doc = fitz.open(path)
            try:
                text_parts = []
                if pages:
                    for p in pages:
                        if 0 <= p - 1 < len(doc):
                            text_parts.append(doc[p - 1].get_text())
                else:
                    for p in range(len(doc)):
                        text_parts.append(doc[p].get_text())
                return "\n".join(text_parts)
            finally:
                doc.close()

        return ("PyMuPDF", _pymupdf)
    except ImportError:
        pass

    # 3) Pure-Python fallback (basic content-stream extraction)
    return ("built-in (basic)", _extract_pure)


# ── pure-python fallback ─────────────────────────────────────────────

def _extract_pure(path, pages=None):
    """Crude pure-PDF text extraction using stdlib only.

    Parses PDF objects, decompresses streams, and extracts text from
    content streams via Tj / TJ operators. Works for simple PDFs.
    """
    with open(path, "rb") as f:
        raw = f.read()

    objects = _parse_pdf_objects(raw)

    # Find /Pages root
    pages_ref = None
    for obj_num, obj_data in objects.items():
        decoded = _decode_pdf_string(obj_data)
        m = re.search(r"/Type\s*/Pages", decoded)
        if m:
            m2 = re.search(r"/Kids\s*\[([^\]]+)\]", decoded)
            if m2:
                kids = m2.group(1)
                pages_ref = re.findall(r"(\d+)\s+\d+\s+R", kids)
                break

    if not pages_ref:
        # Try to find from root /Catalog
        for obj_num, obj_data in objects.items():
            decoded = _decode_pdf_string(obj_data)
            m = re.search(r"/Type\s*/Catalog", decoded)
            if m:
                m2 = re.search(r"/Pages\s+(\d+)\s+\d+\s+R", decoded)
                if m2:
                    root_ref = m2.group(1)
                    root_data = objects.get(int(root_ref), b"")
                    root_dec = _decode_pdf_string(root_data)
                    m3 = re.search(r"/Kids\s*\[([^\]]+)\]", root_dec)
                    if m3:
                        pages_ref = re.findall(r"(\d+)\s+\d+\s+R", m3.group(1))

    if not pages_ref:
        # Last resort: any /Contents references
        pages_ref = []
        for obj_num, obj_data in objects.items():
            decoded = _decode_pdf_string(obj_data)
            m = re.search(r"/Contents\s+(\d+)\s+\d+\s+R", decoded)
            if m:
                pages_ref.append(m.group(1))

    extracted = []
    selected = set(pages) if pages else None

    for idx, ref in enumerate(pages_ref):
        page_num = idx + 1
        if selected and page_num not in selected:
            continue

        page_data = objects.get(int(ref))
        if page_data is None:
            continue

        decoded = _decode_pdf_string(page_data, objects)
        text = _extract_text_from_content(decoded)
        extracted.append({"page": page_num, "text": text})

    if not extracted:
        # Try direct content stream extraction
        for obj_num, obj_data in objects.items():
            decoded = _decode_pdf_string(obj_data, objects)
            text = _extract_text_from_content(decoded)
            if text.strip():
                extracted.append({"page": obj_num, "text": text})

    result = "\n".join(e["text"] for e in extracted)
    return result


def _parse_pdf_objects(data):
    """Return dict {obj_num: raw_bytes_between_obj_and_endobj}."""
    objects = {}
    pattern = re.compile(rb"(\d+)\s+\d+\s+obj\s(.*?)endobj", re.DOTALL)
    for m in pattern.finditer(data):
        obj_num = int(m.group(1))
        obj_data = m.group(2)
        objects[obj_num] = obj_data
    return objects


def _decode_pdf_string(data, all_objects=None):
    """Try to decompress stream data or return latin-1 decoded."""
    # Check for stream keyword
    m = re.search(rb"stream\s(.+?)\s*endstream", data, re.DOTALL)
    if m:
        stream_data = m.group(1).strip()
        # Try FlateDecode
        if b"FlateDecode" in data or b"Fl" in data:
            try:
                return zlib.decompress(stream_data).decode("utf-8", errors="replace")
            except Exception:
                pass
        # Try returning raw
        try:
            return stream_data.decode("latin-1")
        except Exception:
            return stream_data.decode("utf-8", errors="replace")
    # Not a stream — plain object
    try:
        return data.decode("latin-1")
    except Exception:
        return data.decode("utf-8", errors="replace")


def _extract_text_from_content(content):
    """Extract text from PDF content stream operators."""
    text_parts = []

    # Tj operator: (text) Tj
    for m in re.finditer(r"\(([^)]*)\)\s*Tj", content):
        text_parts.append(m.group(1))

    # TJ operator: [(text) num (text) ...] TJ
    tj_arrays = re.finditer(r"\[([^\]]*)\]\s*TJ", content)
    for m in tj_arrays:
        parts = re.findall(r"\(([^)]*)\)", m.group(1))
        text_parts.extend(parts)

    result = "".join(text_parts)

    # PDF escape sequences
    result = result.replace("\\n", "\n").replace("\\r", "\r")
    result = result.replace("\\t", "\t").replace("\\(", "(").replace("\\)", ")")
    result = re.sub(r"\\\d{3}", lambda m: chr(int(m.group(0)[1:])), result)

    return result


# ── PDF info helpers ─────────────────────────────────────────────────

def _get_page_count_pdftotext(path):
    """Use pdfinfo to get page count."""
    try:
        r = subprocess.run(
            ["pdfinfo", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            m = re.search(r"Pages:\s*(\d+)", r.stdout)
            if m:
                return int(m.group(1))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return None


def _get_page_count_pure(path):
    """Count pages by scanning PDF objects."""
    with open(path, "rb") as f:
        data = f.read()
    # Try to find /Type /Pages with /Count
    m = re.search(rb"/Type\s*/Pages[^}]*?/Count\s+(\d+)", data)
    if m:
        return int(m.group(1))
    # Count /Type /Page entries
    return len(re.findall(rb"/Type\s*/Page", data)) or None


# ── main ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print((__doc__ or "").strip())
        return

    # Parse arguments
    path = None
    dir_path = None
    page_spec = None
    output = None
    json_mode = False

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--path",):
            i += 1
            if i < len(args):
                dir_path = args[i]
        elif a in ("-p", "--page"):
            i += 1
            if i < len(args):
                page_spec = args[i]
        elif a in ("-o", "--output"):
            i += 1
            if i < len(args):
                output = args[i]
        elif a in ("--json", "-j"):
            json_mode = True
        elif not a.startswith("-"):
            if path is None and dir_path is None:
                path = a
        i += 1

    # Detect PDF engine
    try:
        engine_name, extract_fn = _find_pdf_engine()
    except Exception:
        print(
            "No PDF extraction library available.\n"
            "Install one of:\n"
            "  sudo apt install poppler-utils   # provides pdftotext\n"
            "  pip install PyMuPDF\n"
            "  pip install pypdf\n"
            "  pip install pdfminer.six",
            file=sys.stderr,
        )
        sys.exit(1)

    engine_label = engine_name

    # Collect files to process
    files = []
    if dir_path:
        if not os.path.isdir(dir_path):
            print(f"Error: directory not found: {dir_path}", file=sys.stderr)
            sys.exit(1)
        for fname in sorted(os.listdir(dir_path)):
            if fname.lower().endswith(".pdf"):
                files.append(os.path.join(dir_path, fname))
        if not files:
            print(f"No PDF files found in: {dir_path}", file=sys.stderr)
            sys.exit(1)
    elif path:
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        files = [path]
    else:
        print((__doc__ or "").strip())
        return

    # Process
    all_results = []
    had_error = False

    for filepath in files:
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        size_str = _fmt_size(size)

        # Get page count
        try:
            page_count = _get_page_count_pdftotext(filepath)
        except Exception:
            page_count = None
        if page_count is None:
            try:
                page_count = _get_page_count_pure(filepath)
            except Exception:
                page_count = None

        # Resolve page numbers
        pages = _parse_page_spec(page_spec, page_count or 999999)

        # Extract text
        try:
            text = extract_fn(filepath, pages)
        except Exception as e:
            error_msg = str(e)
            print(f"  Error ({filename}): {error_msg}", file=sys.stderr)
            had_error = True
            all_results.append({
                "file": filename,
                "error": error_msg,
                "size_bytes": size,
                "size": size_str,
                "pages": page_count,
            })
            continue

        result = {
            "file": filename,
            "path": filepath,
            "size_bytes": size,
            "size": size_str,
            "pages": page_count,
            "page_count_extracted": len(pages) if pages else None,
            "engine": engine_label,
        }

        all_results.append(result)

        if json_mode:
            result["text"] = text
        else:
            # Print to terminal
            if len(files) > 1:
                print(f"\n{'='*60}")
                print(f"  File: {filename}")
                print(f"  Size: {size_str}  |  Pages: {page_count or '?'}")
                print(f"  Engine: {engine_label}")
                print(f"{'='*60}")
            else:
                print(f"  File:  {filename}")
                print(f"  Size:  {size_str}")
                print(f"  Pages: {page_count or '?'}")
                print(f"  Engine: {engine_label}")
                print()

            if text.strip():
                print(text)
            else:
                print("  (no text content extracted)")

    # ── JSON output ──
    if json_mode:
        if len(all_results) == 1:
            output_data = all_results[0]
        else:
            output_data = all_results

        json_str = json.dumps(output_data, indent=2, default=str)
        if output:
            with open(output, "w") as f:
                f.write(json_str)
            print(f"  Written to: {output}", file=sys.stderr)
        else:
            print(json_str)
        return

    # ── Text output to file ──
    if output:
        combined = []
        for r in all_results:
            if "error" in r:
                continue
            combined.append(r.get("text", ""))
        with open(output, "w") as f:
            f.write("\n".join(combined))
        print(f"\n  Written to: {output}", file=sys.stderr)

    if had_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
