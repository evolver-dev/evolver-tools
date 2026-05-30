
import sys
import json
import csv
import io

def flatten(obj, prefix=""):
    """Flatten nested dict to single level"""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict,)):
                items.update(flatten(v, key))
            elif isinstance(v, (list, tuple)):
                items[key] = json.dumps(v, ensure_ascii=False)
            else:
                items[key] = v
    else:
        items[prefix or "value"] = obj
    return items

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert JSON to CSV")
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--flatten", action="store_true", help="Flatten nested objects")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: comma)")
    parser.add_argument("--no-header", action="store_true", help="Do not write header row")
    args = parser.parse_args()
    
    # Read input
    if args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    # Normalize to list
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print("Error: JSON must be an array or object", file=sys.stderr)
        sys.exit(1)
    
    # Flatten if requested
    if args.flatten:
        data = [flatten(item) for item in data]
    
    # Get all field names
    fields = []
    for item in data:
        if isinstance(item, dict):
            for k in item:
                if k not in fields:
                    fields.append(k)
    
    if not fields:
        # Simple values list
        fields = ["value"]
        data = [{"value": v} for v in data]
    
    # Write CSV
    out = open(args.output, "w", newline="") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=fields, delimiter=args.delimiter,
                                extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        if not args.no_header:
            writer.writeheader()
        for item in data:
            if isinstance(item, dict):
                writer.writerow(item)
            else:
                writer.writerow({"value": item})
    finally:
        if args.output:
            out.close()

if __name__ == "__main__":
    main()
