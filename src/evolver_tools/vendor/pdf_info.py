#!/usr/bin/env python3
"""pdf_info — Extract PDF metadata (pages, author, title, size, etc.)

Usage: pdf_info file.pdf
       pdf_info --json file.pdf

Zero-dependency PDF parser (basic metadata from PDF header/objects).
Full metadata requires PyMuPDF or similar — shows what's available.
"""

import os
import re
import sys

TOOL_META = {
    "name": "pdf_info",
    "func": "main",
    "desc": "Extract PDF metadata — pages, title, author, size",
}

def _scan_objects(data):
    """Scan PDF for key metadata objects."""
    info = {}
    # Find /Info dictionary
    m = re.search(rb'/Info\s+(\d+)\s+(\d+)\s+R', data)
    if m:
        obj_num = int(m.group(1))
        gen_num = int(m.group(2))
        # Find the actual Info object
        pattern = rf'{obj_num}\s+{gen_num}\s+obj.*?endobj'.encode()
        om = re.search(pattern, data, re.DOTALL)
        if om:
            chunk = om.group().decode('latin-1', errors='replace')
            for key in ['Title', 'Author', 'Subject', 'Keywords', 'Creator', 'Producer']:
                m2 = re.search(rf'/{key}\s+\(([^)]*)\)', chunk)
                if m2:
                    info[key.lower()] = m2.group(1)
            # Creation/Mod date
            m2 = re.search(r'/CreationDate\s+\(D:([^)]*)\)', chunk)
            if m2:
                info['creation_date'] = m2.group(1)
            m2 = re.search(r'/ModDate\s+\(D:([^)]*)\)', chunk)
            if m2:
                info['mod_date'] = m2.group(1)
    return info


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    path = args[0]
    json_mode = '--json' in args or '-j' in args

    if not os.path.exists(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        data = f.read()

    # Basic info
    result = {
        'file': os.path.basename(path),
        'size_bytes': size,
        'size_kb': round(size / 1024, 1),
    }

    # PDF version
    m = re.search(rb'%PDF-(\d+\.\d+)', data)
    if m:
        result['pdf_version'] = m.group(1).decode()

    # Page count (count Pages objects)
    pages = re.findall(rb'/Type\s*/Pages[^}]*/Count\s+(\d+)', data)
    if pages:
        result['pages'] = int(pages[0])

    # Encrypted?
    result['encrypted'] = '/Encrypt' in data.decode('latin-1', errors='replace')

    # Metadata from Info dict
    info = _scan_objects(data)
    result.update(info)

    if json_mode:
        import json
        print(json.dumps(result, indent=2))
        return

    print(f"  File:      {result['file']}")
    print(f"  Size:      {result['size_kb']} KB ({result['size_bytes']} bytes)")
    if 'pdf_version' in result:
        print(f"  PDF:       {result['pdf_version']}")
    if 'pages' in result:
        print(f"  Pages:     {result['pages']}")
    print(f"  Encrypted: {result['encrypted']}")
    for key in ('title', 'author', 'subject', 'creator', 'producer'):
        if key in result:
            print(f"  {key.title()}: {result[key]}")
    for key in ('creation_date', 'mod_date'):
        if key in result:
            print(f"  {key.replace('_', ' ').title()}: {result[key]}")
