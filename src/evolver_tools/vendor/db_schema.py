#!/usr/bin/env python3
"""db-schema — Display database schema as ASCII. Parse SQLite .db files or accept CREATE TABLE SQL statements."""

import sys
import os
import re
import argparse
import sqlite3


def parse_sql_create_table(sql_content):
    """Parse CREATE TABLE SQL statements and return schema dict."""
    schema = {}
    current_table = None
    current_columns = []

    lines = sql_content.split('\n')
    in_create = False

    for line in lines:
        stripped = line.strip()

        create_match = re.match(r'^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"?(\w+)\"?|(\w+))\s*\(', stripped, re.IGNORECASE)
        if create_match:
            if current_table and current_columns:
                schema[current_table] = current_columns
            current_table = create_match.group(1) or create_match.group(2)
            current_columns = []
            in_create = True
            continue

        if in_create:
            if stripped == ')' or stripped.startswith(');'):
                if current_table and current_columns:
                    schema[current_table] = current_columns
                current_table = None
                current_columns = []
                in_create = False
                continue

            col_match = re.match(r'^\s*(\w+)\s+(\w+(?:\s*\([^)]*\))?)(.*)', stripped)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                constraints = col_match.group(3).strip().rstrip(',')

                col_info = {
                    'name': col_name,
                    'type': col_type.upper(),
                    'not_null': 'NOT NULL' in constraints.upper(),
                    'primary_key': 'PRIMARY KEY' in constraints.upper(),
                    'default': None,
                    'unique': 'UNIQUE' in constraints.upper(),
                }

                def_match = re.search(r'DEFAULT\s+(\S+)', constraints, re.IGNORECASE)
                if def_match:
                    col_info['default'] = def_match.group(1)

                ref_match = re.search(r'REFERENCES\s+(\w+)\s*\((\w+)\)', constraints, re.IGNORECASE)
                if ref_match:
                    col_info['references'] = {'table': ref_match.group(1), 'column': ref_match.group(2)}

                current_columns.append(col_info)

    if current_table and current_columns:
        schema[current_table] = current_columns

    return schema


def get_schema_from_sqlite(db_path):
    """Extract schema from a SQLite database file."""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = cursor.fetchall()

        schema = {}
        for table_name, create_sql in tables:
            if create_sql:
                parsed = parse_sql_create_table(create_sql)
                if parsed:
                    schema.update(parsed)

        conn.close()
        return schema
    except sqlite3.DatabaseError as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)


def print_schema(schema, table_filter=None):
    """Print schema as formatted ASCII."""
    total_tables = len(schema)
    total_columns = 0

    for table_name in sorted(schema.keys()):
        if table_filter and table_name.lower() != table_filter.lower():
            continue

        columns = schema[table_name]
        total_columns += len(columns)

        max_name_len = max(len(c['name']) for c in columns) + 2 if columns else 10
        max_type_len = max(len(c['type']) for c in columns) + 2 if columns else 10

        separator = '+' + '-' * (max_name_len + 2) + '+' + '-' * (max_type_len + 2) + '+' + '-' * 30 + '+'
        header = '| ' + '\033[1mTable:\033[0m ' + f'\033[33m{table_name}\033[0m' + ' ' * (max_name_len + max_type_len + 26 - len(table_name) - 14) + '|'

        print()
        print(separator)
        print(header)
        print(separator)
        print(f"| {'Column':<{max_name_len}} | {'Type':<{max_type_len}} | {'Constraints':<28} |")
        print(separator)

        for col in columns:
            constraints = []
            if col.get('primary_key'):
                constraints.append('\033[93mPK\033[0m')
            if col.get('not_null'):
                constraints.append('\033[91mNN\033[0m')
            if col.get('unique'):
                constraints.append('\033[94mUQ\033[0m')
            if col.get('default') is not None:
                constraints.append(f'DEF={col["default"]}')
            if col.get('references'):
                ref = col['references']
                constraints.append(f'FK→{ref["table"]}.{ref["column"]}')

            constr_str = ', '.join(constraints) if constraints else ''
            name_str = f'\033[1m{col["name"]}\033[0m' if col.get('primary_key') else col['name']

            print(f"| {name_str:<{max_name_len}} | {col['type']:<{max_type_len}} | {constr_str:<28} |")

        print(separator)

    print(f"\n\033[1mSummary:\033[0m {total_tables} table(s), {total_columns} column(s)")


def print_as_json(schema):
    """Print schema as JSON."""
    import json
    output = {}
    for table_name in sorted(schema.keys()):
        output[table_name] = schema[table_name]
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description='Display database schema as ASCII. Supports SQLite .db files and SQL DDL files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  db-schema schema.sql
  db-schema database.db
  db-schema database.db --table users
  db-schema database.db --json
        """,
    )
    parser.add_argument('file', help='SQLite database file (.db) or SQL DDL file (.sql)')
    parser.add_argument('--table', '-t', help='Show only this table')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')

    args = parser.parse_args()

    try:
        ext = os.path.splitext(args.file)[1].lower()

        if ext == '.db' or ext == '.sqlite' or ext == '.sqlite3':
            schema = get_schema_from_sqlite(args.file)
        elif ext == '.sql':
            if not os.path.exists(args.file):
                print(f"File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            schema = parse_sql_create_table(content)
        else:
            print(f"Unknown file extension: {ext}. Use .db, .sqlite, or .sql.", file=sys.stderr)
            sys.exit(1)

        if not schema:
            print("No tables found.")
            sys.exit(1)

        if args.json:
            print_as_json(schema)
        else:
            print_schema(schema, args.table)

    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
