#!/usr/bin/env python3
"""json-schema-validate — Validate JSON data against a JSON schema."""
import json
import os
import sys

TOOL_META = {
    "name": "json-schema-validate",
    "func": "main",
    "desc": "Validate JSON against JSON Schema. Usage: json-schema-validate <data.json> <schema.json>",
}

def validate_fast(data, schema):
    """Simple fast validation without jsonschema library."""
    errors = []
    # Check type
    if "type" in schema:
        type_map = {
            "string": str, "number": (int, float), "integer": int,
            "boolean": bool, "null": type(None),
            "array": list, "object": dict,
        }
        expected_type = type_map.get(schema["type"])
        if expected_type and not isinstance(data, expected_type):
            errors.append(f"Expected type '{schema['type']}', got {type(data).__name__}")
            return errors
    # Check required properties
    if isinstance(data, dict):
        required = schema.get("required", [])
        for prop in required:
            if prop not in data:
                errors.append(f"Missing required property: '{prop}'")
        # Check properties
        for key, prop_schema in schema.get("properties", {}).items():
            if key in data:
                sub_errors = validate_fast(data[key], prop_schema)
                for e in sub_errors:
                    errors.append(f"{key}: {e}")
    # Check array items
    if isinstance(data, list) and "items" in schema:
        for i, item in enumerate(data):
            sub_errors = validate_fast(item, schema["items"])
            for e in sub_errors:
                errors.append(f"[{i}]: {e}")
    # Check enum
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"Value {data!r} not in enum: {schema['enum']}")
    # Check min/max
    if isinstance(data, (int, float)):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"Value {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"Value {data} > maximum {schema['maximum']}")
    if isinstance(data, str):
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"String length {len(data)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"String length {len(data)} > maxLength {schema['maxLength']}")
        if "pattern" in schema:
            import re
            if not re.match(schema["pattern"], data):
                errors.append(f"String '{data}' does not match pattern '{schema['pattern']}'")
    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"Array length {len(data)} < minItems {schema['minItems']}")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(f"Array length {len(data)} > maxItems {schema['maxItems']}")
    return errors

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print("Usage: json-schema-validate <data.json> <schema.json>")
        print("       json-schema-validate <data.json> <schema.json> --full (try jsonschema lib)")
        return
    data_path = args[0]
    schema_path = args[1]
    use_lib = "--full" in args
    for p in [data_path, schema_path]:
        if not os.path.exists(p):
            print(f"File not found: {p}", file=sys.stderr)
            sys.exit(1)
    with open(data_path) as f:
        data = json.load(f)
    with open(schema_path) as f:
        schema = json.load(f)
    # Try jsonschema library if requested
    if use_lib:
        try:
            from jsonschema import validate, ValidationError
            try:
                validate(data, schema)
                print(f"✓ {data_path}: valid against {schema_path}")
                return
            except ValidationError as e:
                print(f"✗ Validation error:")
                print(f"  {e.message}")
                print(f"  Path: {' → '.join(str(p) for p in e.absolute_path)}")
                sys.exit(1)
        except ImportError:
            print("Note: Install jsonschema for full validation: pip install jsonschema", file=sys.stderr)
    # Fallback to fast validation
    errors = validate_fast(data, schema)
    if not errors:
        print(f"✓ {data_path}: valid against {schema_path} (basic validation)")
    else:
        print(f"✗ Validation errors ({len(errors)}):")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
