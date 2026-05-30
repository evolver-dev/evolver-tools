#!/usr/bin/env python3
"""excel2csv — Convert Excel (.xlsx) to CSV. Parses XLSX directly using zipfile + xml.etree."""
import sys
import os
import argparse
import zipfile
import xml.etree.ElementTree as ET
import csv
import io
import re


XLSX_NS = {
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
}


def get_xml_content(zf, path):
    """Read an XML file from zip and return parsed ElementTree."""
    try:
        with zf.open(path) as f:
            return ET.parse(f).getroot()
    except KeyError:
        return None


def get_shared_strings(zf):
    """Extract shared strings from xl/sharedStrings.xml."""
    root = get_xml_content(zf, "xl/sharedStrings.xml")
    if root is None:
        return {}
    strings = {}
    for i, si in enumerate(root.findall(".//s:si", XLSX_NS)):
        texts = []
        for t in si.findall(".//s:t", XLSX_NS):
            if t.text:
                texts.append(t.text)
        strings[i] = "".join(texts)
    return strings


def get_styles(zf):
    """Extract number formats from styles.xml."""
    root = get_xml_content(zf, "xl/styles.xml")
    if root is None:
        return {}
    return root


def column_letter_to_index(col_str):
    """Convert column letter(s) to 0-based index. A=0, B=1, ..., Z=25, AA=26, etc."""
    result = 0
    for c in col_str:
        result = result * 26 + (ord(c.upper()) - ord("A") + 1)
    return result - 1


def parse_cell_reference(ref):
    """Parse a cell reference like 'A1' into (column_letter, row_number)."""
    match = re.match(r"^([A-Za-z]+)(\d+)$", ref)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def get_sheet_names(zf):
    """Get all sheet names from workbook.xml."""
    root = get_xml_content(zf, "xl/workbook.xml")
    if root is None:
        return []
    sheets = []
    for sheet in root.findall(".//s:sheet", XLSX_NS):
        name = sheet.get("name", "")
        sheet_id = sheet.get("sheetId", "")
        rid = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        sheets.append({"name": name, "id": sheet_id, "rid": rid})
    return sheets


def get_sheet_path_from_rid(zf, rid):
    """Get the sheet XML path from a relationship ID."""
    root = get_xml_content(zf, "xl/_rels/workbook.xml.rels")
    if root is None:
        # Try alternative location
        root = get_xml_content(zf, "xl/workbook.xml.rels")
    if root is None:
        return None
    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
        if rel.get("Id") == rid:
            target = rel.get("Target", "")
            if target:
                return f"xl/{target}"
    return None


def read_sheet(zf, sheet_path, shared_strings):
    """Read a sheet XML and yield rows of cell values."""
    root = get_xml_content(zf, sheet_path)
    if root is None:
        return []

    sheet_data = root.find(".//s:sheetData", XLSX_NS)
    if sheet_data is None:
        return []

    rows = []
    for row_elem in sheet_data.findall("s:row", XLSX_NS):
        row_num = int(row_elem.get("r", 0))
        cells = {}
        for cell in row_elem.findall("s:c", XLSX_NS):
            ref = cell.get("r", "")
            col_letter, _ = parse_cell_reference(ref)
            if col_letter is None:
                continue
            col_idx = column_letter_to_index(col_letter)
            cell_type = cell.get("t", "")
            cell_value_elem = cell.find("s:v", XLSX_NS)
            if cell_value_elem is not None and cell_value_elem.text:
                raw_value = cell_value_elem.text.strip()
                if cell_type == "s":
                    # Shared string
                    idx = int(raw_value)
                    value = shared_strings.get(idx, raw_value)
                elif cell_type == "b":
                    value = "TRUE" if raw_value == "1" else "FALSE"
                else:
                    value = raw_value
            else:
                value = ""
            cells[col_idx] = value

        if cells:
            max_col = max(cells.keys()) if cells else 0
            row_data = [cells.get(i, "") for i in range(max_col + 1)]
            rows.append((row_num, row_data))

    # Sort by row number
    rows.sort(key=lambda x: x[0])
    return [r[1] for r in rows]


def list_sheets(zf):
    """List all sheet names."""
    sheets = get_sheet_names(zf)
    if not sheets:
        print("No sheets found in workbook.")
        return
    print("Sheets:")
    for s in sheets:
        print(f"  {s['name']}")


def convert_sheet(zf, sheet_name, output_path, shared_strings):
    """Convert a specific sheet to CSV."""
    sheets = get_sheet_names(zf)
    target_sheet = None
    for s in sheets:
        if s["name"] == sheet_name:
            target_sheet = s
            break
    if target_sheet is None:
        print(f"Error: Sheet '{sheet_name}' not found. Use --list-sheets to see available sheets.",
              file=sys.stderr)
        sys.exit(1)

    sheet_path = get_sheet_path_from_rid(zf, target_sheet["rid"])
    if sheet_path is None:
        print(f"Error: Could not find sheet path for '{sheet_name}'", file=sys.stderr)
        sys.exit(1)

    rows = read_sheet(zf, sheet_path, shared_strings)

    if output_path:
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"Written {len(rows)} rows to {output_path}")
    else:
        writer = csv.writer(sys.stdout)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel (.xlsx) to CSV. Pure Python, no external dependencies."
    )
    parser.add_argument("file", help="Path to .xlsx file")
    parser.add_argument("-s", "--sheet", default=None, help="Sheet name to convert (default: first sheet)")
    parser.add_argument("--list-sheets", action="store_true", help="List all sheet names and exit")
    parser.add_argument("-o", "--output", default=None, help="Output CSV file path (default: stdout)")

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        zf = zipfile.ZipFile(args.file, "r")
    except zipfile.BadZipFile:
        print(f"Error: '{args.file}' is not a valid XLSX file (not a zip archive)", file=sys.stderr)
        sys.exit(1)

    try:
        shared_strings = get_shared_strings(zf)

        if args.list_sheets:
            list_sheets(zf)
            return

        sheets = get_sheet_names(zf)
        if not sheets:
            print("Error: No sheets found in workbook", file=sys.stderr)
            sys.exit(1)

        target_sheet = args.sheet if args.sheet else sheets[0]["name"]
        convert_sheet(zf, target_sheet, args.output, shared_strings)

    except ET.ParseError as e:
        print(f"Error parsing XML in XLSX: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        zf.close()


if __name__ == "__main__":
    main()
