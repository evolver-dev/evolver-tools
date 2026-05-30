#!/usr/bin/env python3
"""json-schema — Validate data against JSON Schema (draft-07 compatible)."""
import sys, os, json, re
from pathlib import Path

TOOL_META = {
    "name": "json-schema",
    "desc": "JSON Schema validation and generation (draft-07)",
    "func": "main",
}

def validate_type(value, schema_type, schema):
    """Check if value matches schema type."""
    if schema_type == "string":
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        # String constraints
        if "minLength" in schema and len(value) < schema["minLength"]:
            return False, f"String too short (min {schema['minLength']})"
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            return False, f"String too long (max {schema['maxLength']})"
        if "pattern" in schema and not re.match(schema["pattern"], value):
            return False, f"String doesn't match pattern: {schema['pattern']}"
        if "enum" in schema and value not in schema["enum"]:
            return False, f"Value not in enum: {value}"
    elif schema_type in ("integer", "number"):
        if schema_type == "integer" and not isinstance(value, int):
            return False, f"Expected integer, got {type(value).__name__}"
        if schema_type == "number" and not isinstance(value, (int, float)):
            return False, f"Expected number, got {type(value).__name__}"
        if "minimum" in schema and value < schema["minimum"]:
            return False, f"Value below minimum ({schema['minimum']})"
        if "maximum" in schema and value > schema["maximum"]:
            return False, f"Value above maximum ({schema['maximum']})"
    elif schema_type == "boolean":
        if not isinstance(value, bool):
            return False, f"Expected boolean, got {type(value).__name__}"
    elif schema_type == "array":
        if not isinstance(value, list):
            return False, f"Expected array, got {type(value).__name__}"
        if "minItems" in schema and len(value) < schema["minItems"]:
            return False, f"Array too short (min {schema['minItems']})"
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return False, f"Array too long (max {schema['maxItems']})"
        if "items" in schema:
            for i, item in enumerate(value):
                ok, err = validate(item, schema["items"])
                if not ok:
                    return False, f"Array item [{i}]: {err}"
    elif schema_type == "object":
        if not isinstance(value, dict):
            return False, f"Expected object, got {type(value).__name__}"
        if "required" in schema:
            for prop in schema["required"]:
                if prop not in value:
                    return False, f"Missing required property: {prop}"
        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                if prop in value:
                    ok, err = validate(value[prop], prop_schema)
                    if not ok:
                        return False, f"Property '{prop}': {err}"
        if "additionalProperties" in schema and not schema["additionalProperties"]:
            allowed = set(schema.get("properties", {}).keys())
            for k in value:
                if k not in allowed:
                    return False, f"Unexpected property: {k}"
    return True, "OK"

def validate(value, schema):
    """Validate a value against a JSON Schema."""
    if "const" in schema:
        if value != schema["const"]:
            return False, f"Expected const {json.dumps(schema['const'])}, got {json.dumps(value)}"
        return True, "OK"

    if "enum" in schema and isinstance(value, (str, int, float, bool)):
        if value not in schema["enum"]:
            return False, f"Value {json.dumps(value)} not in enum {json.dumps(schema['enum'])}"

    if "type" in schema:
        return validate_type(value, schema["type"], schema)

    if "allOf" in schema:
        for sub in schema["allOf"]:
            ok, err = validate(value, sub)
            if not ok:
                return False, f"allOf: {err}"
    if "anyOf" in schema:
        for sub in schema["anyOf"]:
            ok, _ = validate(value, sub)
            if ok:
                return True, "OK"
        return False, "anyOf: no match"
    if "oneOf" in schema:
        matches = 0
        for sub in schema["oneOf"]:
            ok, _ = validate(value, sub)
            if ok:
                matches += 1
        if matches != 1:
            return False, f"oneOf: {matches} matches (expected 1)"

    if "$ref" in schema:
        # Basic local ref support
        ref_path = schema["$ref"]
        if ref_path.startswith("#/definitions/"):
            ref_key = ref_path.split("/")[-1]
            if "definitions" in schema:
                return validate(value, schema["definitions"][ref_key])

    return True, "OK"

def generate_schema(data, name="GeneratedSchema"):
    """Generate a JSON Schema from a data sample."""
    schema = {}
    if data is None:
        schema["type"] = "null"
    elif isinstance(data, bool):
        schema["type"] = "boolean"
    elif isinstance(data, int):
        schema["type"] = "integer"
    elif isinstance(data, float):
        schema["type"] = "number"
    elif isinstance(data, str):
        schema["type"] = "string"
    elif isinstance(data, list):
        schema["type"] = "array"
        if data:
            # Use first item as example
            item_schemas = [generate_schema(item) for item in data if item is not None]
            if item_schemas:
                schema["items"] = item_schemas[0]
    elif isinstance(data, dict):
        schema["type"] = "object"
        schema["properties"] = {}
        for key, val in data.items():
            schema["properties"][key] = generate_schema(val, key)
        schema["required"] = list(data.keys())
    return schema

def main():
    import argparse
    parser = argparse.ArgumentParser(description="JSON Schema validation and generation")
    parser.add_argument("action", nargs="?", choices=["validate", "generate"], default="validate", help="Action")
    parser.add_argument("data", nargs="?", help="Data JSON file or string")
    parser.add_argument("-s", "--schema", default="", help="Schema JSON file")
    args = parser.parse_args()

    if args.action == "generate":
        data_path = args.data or sys.stdin.read()
        if os.path.exists(data_path):
            with open(data_path) as f:
                data = json.load(f)
        else:
            data = json.loads(data_path)
        schema = generate_schema(data)
        print(json.dumps(schema, indent=2))
        return

    if not args.schema:
        parser.print_help()
        return

    # Load schema
    with open(args.schema) as f:
        schema = json.load(f)

    # Load data
    if args.data:
        if os.path.exists(args.data):
            with open(args.data) as f:
                data = json.load(f)
        else:
            data = json.loads(args.data)
    else:
        data = json.load(sys.stdin)

    ok, err = validate(data, schema)
    if ok:
        print(json.dumps(data, indent=2))
        print(f"\n✓ Schema validation PASSED")
    else:
        print(f"✗ Schema validation FAILED: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
