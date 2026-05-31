#!/usr/bin/env python3
"""xml2json — Convert XML to JSON.

Usage: xml2json < file.xml
       cat file.xml | xml2json [--pretty] [--indent=2]
       xml2json file.xml [--pretty]

Converts XML documents to JSON format using Python stdlib (no external deps).
Handles attributes (@ prefix), text content (#text), and nested elements.
"""

import sys, json, xml.etree.ElementTree as ET
from collections import OrderedDict

def elem_to_dict(elem):
    """Convert XML element to a dict, handling attributes and children."""
    result = OrderedDict()
    if elem.attrib:
        for k, v in elem.attrib.items():
            result[f"@{k}"] = v

    # Collect text
    text = (elem.text or "").strip()
    children = list(elem)

    if children:
        child_dict = OrderedDict()
        for child in children:
            tag = child.tag
            child_data = elem_to_dict(child)
            if tag in child_dict:
                if not isinstance(child_dict[tag], list):
                    child_dict[tag] = [child_dict[tag]]
                child_dict[tag].append(child_data)
            else:
                child_dict[tag] = child_data
        result.update(child_dict)
        tail_text = (elem.tail or "").strip()
    else:
        if text:
            result["#text"] = text

    return result

def main():
    args = sys.argv[1:]
    pretty = False
    indent = 2

    files = []
    for a in args:
        if a == '--pretty':
            pretty = True
        elif a.startswith('--indent='):
            indent = int(a.split('=', 1)[1])
        elif not a.startswith('-'):
            files.append(a)

    if files:
        for f in files:
            with open(f) as fh:
                raw = fh.read()
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("Error: empty input")
        sys.exit(1)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"XML parse error: {e}", file=sys.stderr)
        sys.exit(1)

    data = {root.tag: elem_to_dict(root)}
    if pretty:
        print(json.dumps(data, indent=indent, ensure_ascii=False))
    else:
        print(json.dumps(data, ensure_ascii=False))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "xml2json",
    "func": "main",
    "desc": 'XML to JSON converter',
}

if __name__ == '__main__':
    main()
