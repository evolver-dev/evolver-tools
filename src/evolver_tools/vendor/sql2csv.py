#!/usr/bin/env python3
"""sql2csv — Run SQL query on CSV files. Loads CSV files as tables for SQL queries."""
import sys
import os
import argparse
import csv
import re
from collections import OrderedDict


class SimpleTable:
    """An in-memory table loaded from a CSV file."""

    def __init__(self, name, headers, rows):
        self.name = name
        self.headers = headers
        self.rows = rows
        self.col_index = {h.lower(): i for i, h in enumerate(headers)}

    def get_column_index(self, name):
        return self.col_index.get(name.lower(), -1)

    def __len__(self):
        return len(self.rows)


class JoinResult:
    """Represents a joined table for display."""

    def __init__(self, headers, rows):
        self.headers = headers
        self.rows = rows


def load_table(path, name=None):
    """Load a CSV file into a SimpleTable."""
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    rows = []
    headers = []
    try:
        with open(path, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            if not headers:
                print(f"Error: Empty CSV file: {path}", file=sys.stderr)
                sys.exit(1)
            for row in reader:
                if row and any(c.strip() for c in row):
                    # Pad or truncate to match headers
                    while len(row) < len(headers):
                        row.append("")
                    rows.append(row[:len(headers)])
    except csv.Error as e:
        print(f"CSV error in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)

    base_name = name or os.path.splitext(os.path.basename(path))[0]
    return SimpleTable(base_name, headers, rows)


def parse_sql_select(query):
    """Parse a simple SELECT query. Returns dict with parts."""
    query = query.strip()

    # Normalize whitespace
    query = re.sub(r"\s+", " ", query)

    parts = {"select": [], "from": "", "where": "", "join": [], "order_by": "", "limit": None}

    # Extract LIMIT
    limit_match = re.search(r"\bLIMIT\s+(\d+)", query, re.IGNORECASE)
    if limit_match:
        parts["limit"] = int(limit_match.group(1))
        query = query[:limit_match.start()]

    # Extract ORDER BY
    order_match = re.search(r"\bORDER\s+BY\s+(.+?)$", query, re.IGNORECASE)
    if order_match:
        parts["order_by"] = order_match.group(1).strip()
        query = query[:order_match.start()]

    # Extract WHERE clause
    where_match = re.search(r"\bWHERE\s+(.+?)$", query, re.IGNORECASE)
    if where_match:
        parts["where"] = where_match.group(1).strip()
        query = query[:where_match.start()]

    # Extract JOIN clauses
    # Simple JOIN: ... FROM table1 JOIN table2 ON condition ...
    join_pattern = re.compile(
        r"\b(LEFT\s+)?(INNER\s+)?(OUTER\s+)?JOIN\s+(\w+)\s+(\w+)?\s*(?:\bON\s+(.+?))?(?=\b(?:WHERE|ORDER|LIMIT|$)|JOIN)",
        re.IGNORECASE
    )
    for match in join_pattern.finditer(query):
        join_type = "LEFT" if match.group(1) else "INNER"
        join_table = match.group(4)
        join_alias = match.group(5)
        join_on = match.group(6) if match.group(6) else ""
        parts["join"].append({
            "type": join_type,
            "table": join_table,
            "alias": join_alias,
            "on": join_on.strip() if join_on else "",
        })
        query = query[:match.start()] + query[match.end():]

    # Extract FROM clause
    from_match = re.search(r"\bFROM\s+(\w+)(?:\s+(\w+))?", query, re.IGNORECASE)
    if from_match:
        parts["from"] = from_match.group(1)
        parts["from_alias"] = from_match.group(2) if from_match.group(2) else ""
        query = query[:from_match.start()]

    # Extract SELECT columns
    select_match = re.search(r"\bSELECT\s+(.+?)$", query, re.IGNORECASE)
    if select_match:
        select_part = select_match.group(1).strip()
        cols = [c.strip() for c in select_part.split(",")]
        parts["select"] = cols

    return parts


def resolve_column(col_expr, tables):
    """Resolve a column expression to (table_name, column_name, value_getter)."""
    col_expr = col_expr.strip()

    # Handle COUNT(*), COUNT(col)
    count_all_match = re.match(r"^COUNT\(\*\)$", col_expr, re.IGNORECASE)
    if count_all_match:
        return ("__aggregate__", "COUNT(*)", lambda: str(len(tables[0].rows)))

    count_col_match = re.match(r"^COUNT\((\w+(?:\.\w+)?)\)$", col_expr, re.IGNORECASE)
    if count_col_match:
        inner = count_col_match.group(1)
        return ("__aggregate__", f"COUNT({inner})", lambda: str(len(tables[0].rows)))

    # Handle AS alias
    as_match = re.match(r"(.+?)\s+AS\s+(\w+)$", col_expr, re.IGNORECASE)
    if as_match:
        col_expr = as_match.group(1).strip()
        alias = as_match.group(2)
    else:
        alias = None

    # Check if it's table.column format
    if "." in col_expr:
        parts = col_expr.split(".")
        table_ref = parts[0].strip()
        col_name = parts[1].strip()
        for t in tables:
            if t.name.lower() == table_ref.lower():
                idx = t.get_column_index(col_name)
                if idx >= 0:
                    display = alias or f"{table_ref}.{col_name}"
                    return (t.name, display, lambda row, tidx=tables.index(t): row[tidx])
        # Also check aliases
        return None

    # Simple column name - search all tables
    for t in tables:
        idx = t.get_column_index(col_expr)
        if idx >= 0:
            display = alias or col_expr
            return (t.name, display, lambda row, tidx=tables.index(t): row[tidx])

    return None


def evaluate_condition(condition, tables, join_mode=False):
    """Evaluate a WHERE or JOIN ON condition for a row combination. Returns bool."""
    condition = condition.strip()

    # Handle AND
    if " AND " in condition.upper():
        parts = re.split(r"\s+AND\s+", condition, flags=re.IGNORECASE)
        results = [evaluate_condition(p.strip(), tables) for p in parts]
        return all(results)

    # Handle OR
    if " OR " in condition.upper():
        parts = re.split(r"\s+OR\s+", condition, flags=re.IGNORECASE)
        results = [evaluate_condition(p.strip(), tables) for p in parts]
        return any(results)

    # Try to find comparison operators: =, !=, <>, <, >, <=, >=, LIKE
    op_pattern = re.compile(
        r"(.+?)\s*(=|!=|<>|<=|>=|<|>|\bLIKE\b)\s*(.+)", re.IGNORECASE
    )
    match = op_pattern.match(condition)
    if not match:
        # Try IS NULL / IS NOT NULL
        null_match = re.match(r"(.+?)\s+IS\s+(NOT\s+)?NULL$", condition, re.IGNORECASE)
        if null_match:
            lhs_expr = null_match.group(1).strip()
            is_not = null_match.group(2) is not None
            try:
                lhs_val = resolve_and_get_value(lhs_expr, tables)
            except IndexError:
                return False if not is_not else True
            if lhs_val is None or lhs_val == "":
                return is_not
            return not is_not
        return True  # If we can't parse, assume true

    lhs_expr = match.group(1).strip()
    operator = match.group(2).strip().upper()
    rhs_expr = match.group(3).strip()

    try:
        lhs_val = resolve_and_get_value(lhs_expr, tables)
    except IndexError:
        return False

    # Handle string literals vs column references for RHS
    if (rhs_expr.startswith("'") and rhs_expr.endswith("'")) or \
       (rhs_expr.startswith('"') and rhs_expr.endswith('"')):
        rhs_val = rhs_expr[1:-1]
    else:
        try:
            rhs_val = resolve_and_get_value(rhs_expr, tables)
        except IndexError:
            rhs_val = rhs_expr

    # Try numeric comparison
    try:
        lhs_num = float(lhs_val) if lhs_val else 0
        rhs_num = float(rhs_val) if rhs_val else 0
        use_numeric = True
    except (ValueError, TypeError):
        use_numeric = False

    if operator == "=":
        return lhs_val == rhs_val
    elif operator in ("!=", "<>"):
        return lhs_val != rhs_val
    elif operator == "<":
        if use_numeric:
            return lhs_num < rhs_num
        return (lhs_val or "") < (rhs_val or "")
    elif operator == ">":
        if use_numeric:
            return lhs_num > rhs_num
        return (lhs_val or "") > (rhs_val or "")
    elif operator == "<=":
        if use_numeric:
            return lhs_num <= rhs_num
        return (lhs_val or "") <= (rhs_val or "")
    elif operator == ">=":
        if use_numeric:
            return lhs_num >= rhs_num
        return (lhs_val or "") >= (rhs_val or "")
    elif operator == "LIKE":
        pattern = rhs_val.replace("%", ".*").replace("_", ".")
        return bool(re.match(pattern, lhs_val, re.IGNORECASE))

    return True


def resolve_and_get_value(expr, tables):
    """Resolve an expression to a value from the current row combination."""
    expr = expr.strip()

    # String literal
    if (expr.startswith("'") and expr.endswith("'")) or \
       (expr.startswith('"') and expr.endswith('"')):
        return expr[1:-1]

    # Number
    try:
        float(expr)
        return expr
    except ValueError:
        pass

    # Table.column format
    if "." in expr:
        parts = expr.split(".", 1)
        table_ref = parts[0].strip().lower()
        col_name = parts[1].strip()
        for t_idx, t in enumerate(tables):
            if isinstance(t, SimpleTable) and t.name.lower() == table_ref:
                col_idx = t.get_column_index(col_name)
                if col_idx >= 0:
                    if isinstance(tables[t_idx], SimpleTable):
                        return t.rows[0][col_idx]
        return expr

    # Simple column - search all tables
    for t in tables:
        idx = t.get_column_index(expr)
        if idx >= 0:
            return t.rows[0][idx]

    return expr


def execute_query(query, tables):
    """Execute a SELECT query on tables."""
    parsed = parse_sql_select(query)

    # Find main table
    main_table = None
    main_alias = parsed.get("from_alias", "")
    for t in tables:
        if t.name.lower() == parsed["from"].lower():
            main_table = t
            break
    if main_table is None:
        print(f"Error: Table '{parsed['from']}' not found", file=sys.stderr)
        sys.exit(1)

    # Handle joins
    if parsed["join"]:
        # Perform join
        all_tables = [main_table]
        join_tables = []
        for j in parsed["join"]:
            jt = None
            for t in tables:
                if t.name.lower() == j["table"].lower():
                    jt = t
                    break
            if jt is None:
                print(f"Error: Join table '{j['table']}' not found", file=sys.stderr)
                sys.exit(1)
            join_tables.append(jt)

        # Perform the joins
        result_rows = []
        result_headers = main_table.headers[:]

        for row in main_table.rows:
            # For each join table, try to match
            matched = False
            for j_idx, jt in enumerate(join_tables):
                join_condition = parsed["join"][j_idx]["on"]
                for jrow in jt.rows:
                    # Build temporary table set for condition evaluation
                    class TempRowTable:
                        def __init__(self, t, r):
                            self.name = t.name
                            self.headers = t.headers
                            self.rows = [r]

                    temp_tables = [TempRowTable(main_table, row)]
                    for jt2 in join_tables:
                        temp_tables.append(TempRowTable(jt2, jrow))

                    if evaluate_condition(join_condition, temp_tables):
                        result_rows.append(row + jrow)
                        if j_idx == 0:
                            result_headers = main_table.headers + jt.headers
                        matched = True

                if not matched and parsed["join"][j_idx]["type"] == "LEFT":
                    # Left join: add NULLs
                    result_rows.append(row + [""] * len(jt.headers))
                    if j_idx == 0:
                        result_headers = main_table.headers + jt.headers

            if not matched and not join_tables:
                result_rows.append(row)

        if not result_rows:
            return JoinResult([], [])

        # Apply WHERE clause
        if parsed["where"]:
            filtered_rows = []
            for row in result_rows:
                if check_row_condition(row, result_headers, parsed["where"]):
                    filtered_rows.append(row)
            result_rows = filtered_rows

        # Process SELECT columns
        headers = []
        col_getters = []

        if parsed["select"] and parsed["select"][0].upper() == "COUNT(*)":
            return JoinResult(["COUNT(*)"], [[str(len(result_rows))]])

        for sel in parsed["select"]:
            sel = sel.strip()
            if sel == "*":
                headers = result_headers
                col_getters = list(range(len(result_headers)))
            elif sel.upper().startswith("COUNT("):
                headers.append(sel)
                col_getters.append(lambda row: str(len(result_rows)))
            else:
                resolved = resolve_column_select(sel, result_headers)
                if resolved:
                    headers.append(resolved[0])
                    col_getters.append(resolved[1])

        final_rows = []
        for row in result_rows:
            final_row = []
            for getter in col_getters:
                if callable(getter):
                    final_row.append(getter(row))
                elif isinstance(getter, int):
                    final_row.append(row[getter] if getter < len(row) else "")
            final_rows.append(final_row)

        # Apply ORDER BY
        if parsed["order_by"]:
            order_col = parsed["order_by"].strip()
            asc = True
            if order_col.upper().endswith(" DESC"):
                asc = False
                order_col = order_col[:-5].strip()
            elif order_col.upper().endswith(" ASC"):
                order_col = order_col[:-4].strip()

            col_idx = -1
            for i, h in enumerate(headers):
                if h.lower() == order_col.lower():
                    col_idx = i
                    break

            if col_idx >= 0:
                def sort_key(row, idx=col_idx, asc=asc):
                    try:
                        return float(row[idx]) if row[idx] else 0
                    except (ValueError, IndexError):
                        return row[idx] if row[idx] else ""
                final_rows.sort(key=sort_key, reverse=not asc)

        # Apply LIMIT
        if parsed["limit"] is not None:
            final_rows = final_rows[:parsed["limit"]]

        return JoinResult(headers, final_rows)

    else:
        # No joins: simple SELECT on one table
        rows = main_table.rows

        # Apply WHERE
        if parsed["where"]:
            filtered = []
            for row in rows:
                if check_row_condition(row, main_table.headers, parsed["where"]):
                    filtered.append(row)
            rows = filtered

        # Process SELECT columns
        headers = []
        col_getters = []

        if parsed["select"]:
            for sel in parsed["select"]:
                sel = sel.strip()
                if sel == "*":
                    headers = main_table.headers
                    col_getters = list(range(len(main_table.headers)))
                elif sel.upper().startswith("COUNT("):
                    headers.append(sel)
                    col_getters.append(lambda row, count=len(rows): str(count))
                else:
                    resolved = resolve_column_select(sel, main_table.headers)
                    if resolved:
                        headers.append(resolved[0])
                        col_getters.append(resolved[1])
        else:
            headers = main_table.headers
            col_getters = list(range(len(main_table.headers)))

        final_rows = []
        for row in rows:
            final_row = []
            for getter in col_getters:
                if callable(getter):
                    final_row.append(getter(row))
                elif isinstance(getter, int):
                    final_row.append(row[getter] if getter < len(row) else "")
            final_rows.append(final_row)

        # Apply ORDER BY
        if parsed["order_by"]:
            order_col = parsed["order_by"].strip()
            asc = True
            if order_col.upper().endswith(" DESC"):
                asc = False
                order_col = order_col[:-5].strip()
            elif order_col.upper().endswith(" ASC"):
                order_col = order_col[:-4].strip()

            col_idx = -1
            for i, h in enumerate(headers):
                if h.lower() == order_col.lower():
                    col_idx = i
                    break

            if col_idx >= 0:
                def sort_key(row, idx=col_idx, asc=asc):
                    try:
                        return float(row[idx]) if row[idx] else 0
                    except (ValueError, IndexError):
                        return row[idx] if row[idx] else ""
                final_rows.sort(key=sort_key, reverse=not asc)

        # Apply LIMIT
        if parsed["limit"] is not None:
            final_rows = final_rows[:parsed["limit"]]

        return JoinResult(headers, final_rows)


def resolve_column_select(sel, all_headers):
    """Resolve a SELECT column expression to (display_name, getter_or_index)."""
    sel = sel.strip()

    # Handle AS alias
    alias = None
    as_match = re.match(r"(.+?)\s+AS\s+(\w+)$", sel, re.IGNORECASE)
    if as_match:
        sel = as_match.group(1).strip()
        alias = as_match.group(2)

    # Check table.column format
    if "." in sel:
        col_name = sel.split(".", 1)[1].strip()
    else:
        col_name = sel

    for i, h in enumerate(all_headers):
        if h.lower() == col_name.lower():
            display = alias or h
            return (display, i)

    return None


def check_row_condition(row, headers, condition):
    """Check if a row matches a WHERE condition."""
    # Create a single-row table
    class SingleTable:
        def __init__(self, headers, row):
            self.name = "_"
            self.headers = headers
            self.rows = [row]

        def get_column_index(self, name):
            for i, h in enumerate(self.headers):
                if h.lower() == name.lower():
                    return i
            return -1

    st = SingleTable(headers, row)

    return evaluate_condition(condition, [st])


def main():
    parser = argparse.ArgumentParser(
        description="Run SQL query on CSV files. Loads CSVs as tables, runs SQL."
    )
    parser.add_argument("query", help="SQL SELECT query (e.g., 'SELECT * FROM data WHERE age > 30')")
    parser.add_argument("files", nargs="+", help="CSV files to load as tables")
    parser.add_argument("--no-header", action="store_true", help="Treat first row as data, not header")

    args = parser.parse_args()

    if len(args.files) == 0:
        print("Error: At least one CSV file required", file=sys.stderr)
        sys.exit(1)

    try:
        tables = []
        for f in args.files:
            table = load_table(f)
            tables.append(table)

        result = execute_query(args.query, tables)

        if not result.headers:
            print("No results.")
            return

        # Output as CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(result.headers)
        for row in result.rows:
            writer.writerow(row)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "sql2csv",
    "func": "main",
    "desc": 'Run SQL on CSV files',
}

if __name__ == "__main__":
    main()
