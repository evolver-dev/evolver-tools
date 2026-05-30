"""config-vault CLI module.

Provides all command-line functionality using only Python stdlib (zero deps).
Supports .env, JSON, YAML-like, and TOML config files.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Console helpers ────────────────────────────────────────────────────────


def _color(text: str, code: str) -> str:
    """Wrap text in ANSI color code if stdout is a terminal."""
    if not sys.stdout.isatty():
        return text
    codes = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def _ok(msg: str) -> None:
    print(f"{_color('✓', 'green')} {msg}")


def _warn(msg: str) -> None:
    print(f"{_color('!', 'yellow')} {_color('WARN', 'yellow')}: {msg}")


def _err(msg: str) -> None:
    print(f"{_color('✗', 'red')} {_color('ERROR', 'red')}: {msg}", file=sys.stderr)


def _die(msg: str, code: int = 1) -> None:
    _err(msg)
    sys.exit(code)


# ─── File format detection & parsing ────────────────────────────────────────

SUPPORTED_FORMATS = (".env", ".json", ".yaml", ".yml", ".toml")
_ENV_LINE_RE = re.compile(r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)")


def _detect_format(path: str) -> str:
    """Detect config format from file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        return "yaml"
    if ext == ".toml":
        return "toml"
    if ext == ".json":
        return "json"
    return "env"


def _parse_env(content: str) -> Dict[str, str]:
    """Parse a .env file into a dict."""
    config: Dict[str, str] = {}
    for line in content.splitlines():
        m = _ENV_LINE_RE.match(line)
        if m:
            key = m.group("key")
            raw = m.group("value").strip()
            # Strip surrounding quotes
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
                raw = raw[1:-1]
            config[key] = raw
    return config


def _serialize_env(config: Dict[str, str]) -> str:
    """Serialize a dict back into .env format."""
    lines: List[str] = []
    for k, v in config.items():
        if any(c in v for c in (' ', '#', '"', "'", "=")):
            v = f'"{v}"'
        lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"


def _parse_yaml_simple(content: str) -> Dict[str, Any]:
    """Parse a YAML-like file using only stdlib.

    Supports basic key: value, nested dicts, lists, and scalar types.
    This is a minimal parser — for full YAML use the 'yaml' package.
    """
    result: Dict[str, Any] = {}
    stack: List[Tuple[Dict[str, Any], int]] = [(result, -1)]
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Skip empty, comments, doc markers
        if not stripped or stripped.startswith("#") or stripped.startswith("---"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        # Pop stack back to correct indent level
        while stack and stack[-1][1] >= indent:
            stack.pop()
        if not stack:
            stack.append((result, -1))

        # List item
        if stripped.startswith("- "):
            list_val = stripped[2:].strip()
            parent = stack[-1][0]
            if not isinstance(parent, list):
                # Convert parent from dict to list context if needed
                continue
            parent.append(_parse_yaml_scalar(list_val))
            i += 1
            continue

        # key: value or key:
        if ":" in stripped:
            colon_pos = stripped.index(":")
            key = stripped[:colon_pos].strip()
            rest = stripped[colon_pos + 1:].strip()
            parent = stack[-1][0]
            if not rest or rest == "":
                # New nested dict or list
                next_indent = None
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.strip() and not nxt.strip().startswith("#"):
                        next_indent = len(nxt) - len(nxt.lstrip())
                        break
                    j += 1
                if next_indent is not None and next_indent > indent:
                    if j < len(lines) and lines[j].strip().startswith("- "):
                        parent[key] = []
                        stack.append((parent[key], indent))
                    else:
                        parent[key] = {}
                        stack.append((parent[key], indent))
                else:
                    parent[key] = None
            else:
                parent[key] = _parse_yaml_scalar(rest)
        i += 1
    return result


def _parse_yaml_scalar(val: str) -> Any:
    """Parse a YAML scalar value."""
    if val.lower() in ("true", "yes", "on"):
        return True
    if val.lower() in ("false", "no", "off"):
        return False
    if val.lower() == "null" or val == "~":
        return None
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
        return val[1:-1]
    return val


def _serialize_yaml_simple(data: Dict[str, Any], indent: int = 0) -> str:
    """Serialize a dict back to minimal YAML format."""
    lines: List[str] = []
    prefix = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_serialize_yaml_simple(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}:")
            for item in v:
                lines.append(f"{prefix}- {_yaml_repr(item)}")
        else:
            lines.append(f"{prefix}{k}: {_yaml_repr(v)}")
    return "\n".join(lines).rstrip()


def _yaml_repr(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        if any(c in val for c in (':', '#', '"', "'", "{", "}")):
            return f'"{val}"'
        return val
    return str(val)


def _parse_toml(content: str) -> Dict[str, Any]:
    """Parse a minimal TOML file using only stdlib.

    Supports: [table], key = value, strings, numbers, booleans, inline tables.
    """
    result: Dict[str, Any] = {}
    current_table = result
    current_path: List[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Table header
        m = re.match(r"^\[(.+)\]$", stripped)
        if m:
            current_path = m.group(1).split(".")
            current_table = result
            for part in current_path:
                part = part.strip()
                if part not in current_table:
                    current_table[part] = {}
                current_table[part] = current_table.get(part, {})
                if not isinstance(current_table[part], dict):
                    current_table[part] = {}
                current_table = current_table[part]
            continue
        # key = value
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', stripped)
        if m:
            key = m.group(1)
            raw_val = m.group(2).strip()
            current_table[key] = _parse_toml_value(raw_val)
    return result


def _parse_toml_value(raw: str) -> Any:
    """Parse a TOML value."""
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Inline table
    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1].strip()
        d: Dict[str, Any] = {}
        for pair in inner.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                d[k.strip()] = _parse_toml_value(v.strip())
        return d
    return raw


def _serialize_toml(data: Dict[str, Any], prefix: str = "") -> str:
    """Serialize dict to TOML format."""
    lines: List[str] = []
    scalars: List[str] = []
    tables: List[str] = []

    for k, v in data.items():
        if isinstance(v, dict):
            table_name = f"{prefix}.{k}" if prefix else k
            lines.append(f"\n[{table_name}]")
            lines.append(_serialize_toml(v, table_name))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    lines.append(f"\n[[{prefix}.{k}]]" if prefix else f"\n[[{k}]]")
                    lines.append(_serialize_toml(item))
                else:
                    scalars.append(f"{k} = {_toml_repr(v)}")
                    break
        else:
            scalars.append(f"{k} = {_toml_repr(v)}")
    result = "\n".join(scalars)
    if scalars and tables:
        result += "\n"
    result += "\n".join(tables)
    return result


def _toml_repr(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        return f'"{val}"'
    return str(val)


def load_config(path: str) -> Dict[str, Any]:
    """Load a config file of any supported format and return a dict."""
    fmt = _detect_format(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        _die(f"File not found: {path}")
    except PermissionError:
        _die(f"Permission denied: {path}")

    if fmt == "env":
        return _parse_env(content)  # type: ignore
    elif fmt == "json":
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            _die(f"Invalid JSON in {path}: {e}")
    elif fmt == "yaml":
        try:
            return _parse_yaml_simple(content)
        except Exception as e:
            _die(f"Invalid YAML in {path}: {e}")
    elif fmt == "toml":
        try:
            return _parse_toml(content)
        except Exception as e:
            _die(f"Invalid TOML in {path}: {e}")
    return {}


def save_config(path: str, data: Dict[str, Any]) -> None:
    """Save a dict to a config file."""
    fmt = _detect_format(path)
    try:
        if fmt == "env":
            content = _serialize_env(data)  # type: ignore
        elif fmt == "json":
            content = json.dumps(data, indent=2, default=str) + "\n"
        elif fmt == "yaml":
            content = _serialize_yaml_simple(data) + "\n"
        elif fmt == "toml":
            content = _serialize_toml(data) + "\n"
        else:
            content = _serialize_env(data)  # type: ignore
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        _die(f"Failed to write {path}: {e}")


def load_env(path: str) -> Dict[str, str]:
    """Load a .env file and return string-keyed dict."""
    return load_config(path)  # type: ignore


# ─── Validation ─────────────────────────────────────────────────────────────


def validate_env(path: str, required: Optional[List[str]] = None) -> int:
    """Validate a .env file. Returns number of errors."""
    errors = 0
    config = load_env(path)
    if not config:
        _warn(f"Empty or unparseable .env file: {path}")
        return 1

    _ok(f"Loaded {len(config)} variables from {path}")
    for key, val in config.items():
        issues: List[str] = []
        if not key.isidentifier():
            issues.append("invalid identifier")
        if val == "":
            issues.append("empty value")
        for issue in issues:
            _warn(f"  {key}: {issue}")
            errors += 1

    if required:
        for r in required:
            if r not in config:
                _err(f"Missing required variable: {r}")
                errors += 1
            elif config[r] == "":
                _err(f"Required variable is empty: {r}")
                errors += 1

    if errors == 0:
        _ok("All checks passed.")
    return errors


def validate_config(path: str) -> int:
    """Validate a JSON/YAML/TOML config file. Returns number of errors."""
    fmt = _detect_format(path)
    try:
        data = load_config(path)
    except Exception as e:
        _err(f"Failed to load {path}: {e}")
        return 1

    if not data:
        _warn(f"Empty config: {path}")
        return 1

    _ok(f"Valid {fmt.upper()} config: {len(data)} top-level keys")
    return 0


# ─── Encryption / Decryption ────────────────────────────────────────────────


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES-like key from password + salt using SHA-256."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, dklen=32)


def encrypt_value(plaintext: str, password: str) -> str:
    """Encrypt a value using XOR cipher with derived key.

    Returns base64-like encoded string with salt prefix.
    Uses CP437-safe encoding for portability.
    """
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    data = plaintext.encode("utf-8")
    encrypted = bytes(a ^ b for a, b in zip(data, key[:len(data)]))
    # Encode salt + encrypted data as hex for safe storage
    result = (salt + encrypted).hex()
    return f"$CV${result}"


def decrypt_value(ciphertext: str, password: str) -> Optional[str]:
    """Decrypt a value encrypted with encrypt_value."""
    if not ciphertext.startswith("$CV$"):
        return None
    try:
        raw = bytes.fromhex(ciphertext[4:])
    except ValueError:
        return None
    if len(raw) < 16:
        return None
    salt = raw[:16]
    encrypted = raw[16:]
    key = _derive_key(password, salt)
    try:
        decrypted = bytes(a ^ b for a, b in zip(encrypted, key[:len(encrypted)]))
        return decrypted.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None


def cmd_encrypt(path: str, password: str, key_filter: Optional[List[str]] = None) -> int:
    """Encrypt values in a .env file."""
    config = load_env(path)
    count = 0
    for k in list(config.keys()):
        if key_filter and k not in key_filter:
            continue
        val = config[k]
        if val.startswith("$CV$"):
            continue
        config[k] = encrypt_value(val, password)
        count += 1
    save_config(path, config)
    _ok(f"Encrypted {count} value(s) in {path}")
    return 0


def cmd_decrypt(path: str, password: str, key_filter: Optional[List[str]] = None) -> int:
    """Decrypt values in a .env file."""
    config = load_env(path)
    count = 0
    for k in list(config.keys()):
        if key_filter and k not in key_filter:
            continue
        val = config[k]
        if not val.startswith("$CV$"):
            continue
        dec = decrypt_value(val, password)
        if dec is None:
            _warn(f"  {k}: decryption failed (wrong password?)")
            continue
        config[k] = dec
        count += 1
    save_config(path, config)
    _ok(f"Decrypted {count} value(s) in {path}")
    return 0


# ─── Backup / Restore ────────────────────────────────────────────────────────


def cmd_backup(path: str) -> str:
    """Backup a config file to a timestamped .bak file. Returns backup path."""
    if not os.path.isfile(path):
        _die(f"Not a file: {path}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.{ts}.bak"
    try:
        shutil.copy2(path, backup_path)
        _ok(f"Backup created: {backup_path}")
    except IOError as e:
        _die(f"Backup failed: {e}")
    return backup_path


def cmd_restore(path: str) -> int:
    """Restore the most recent .bak file for a given path."""
    basedir = os.path.dirname(path) or "."
    pattern = os.path.basename(path) + ".*.bak"
    backups: List[str] = []
    for f in os.listdir(basedir):
        if f.startswith(os.path.basename(path)) and f.endswith(".bak"):
            backups.append(os.path.join(basedir, f))
    if not backups:
        _err(f"No backups found for {path}")
        return 1
    backups.sort(reverse=True)
    latest = backups[0]
    try:
        shutil.copy2(latest, path)
        _ok(f"Restored {path} from {latest}")
    except IOError as e:
        _err(f"Restore failed: {e}")
        return 1
    return 0


def cmd_list_backups(path: str) -> None:
    """List all backups for a given path."""
    basedir = os.path.dirname(path) or "."
    backups: List[str] = []
    for f in os.listdir(basedir):
        if f.startswith(os.path.basename(path)) and f.endswith(".bak"):
            backups.append(os.path.join(basedir, f))
    if not backups:
        print("No backups found.")
        return
    backups.sort(reverse=True)
    print(f"Backups for {path}:")
    for i, b in enumerate(backups, 1):
        fsize = os.path.getsize(b)
        mtime = datetime.fromtimestamp(os.path.getmtime(b)).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {i}. {b} ({fsize} bytes, {mtime})")


# ─── Secret Scanning ─────────────────────────────────────────────────────────

# Patterns for detecting hardcoded secrets
SECRET_PATTERNS: List[Tuple[str, str, re.Pattern]] = [
    ("AWS Access Key", "AKIA[0-9A-Z]{16}", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key", "wJalrXUt...", re.compile(r"(?i)(aws_secret_access_key|aws_secret_key)\s*[=:]\s*['\"][A-Za-z0-9/+=]{40}['\"]")),
    ("GitHub Token", "ghp_...", re.compile(r"(?i)(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36,}")),
    ("GitLab Token", "glpat-...", re.compile(r"glpat-[A-Za-z0-9_\-]{20,}")),
    ("Slack Token", "xox[baprs]-...", re.compile(r"xox[baprs]-\d{12}-\d{12}-\d{12}-[a-z0-9]{24,}")),
    ("Generic API Key", "api_key/api-key", re.compile(r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"]")),
    ("Generic Secret", "secret/password/token", re.compile(r"(?i)(secret|password|token|private_key)\s*[=:]\s*['\"][A-Za-z0-9_\-!@#$%^&*+=]{16,}['\"]")),
    ("JWT Token", "eyJ...", re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}")),
    ("Private SSH Key", "-----BEGIN", re.compile(r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PRIVATE)\s+KEY-----")),
    ("Heroku API Key", "heroku", re.compile(r"(?i)heroku[a-z_]*\s*[=:]\s*['\"][A-Za-z0-9\-]{36,}['\"]")),
    ("Slack Webhook", "hooks.slack.com", re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[a-zA-Z0-9]+")),
    ("Stripe API Key", "sk_live_...", re.compile(r"(?i)(sk_live_|pk_live_|sk_test_|pk_test_)[A-Za-z0-9]{20,}")),
    ("Google OAuth", "client_secret", re.compile(r"(?i)(client_secret|client_id)\s*[=:]\s*['\"][A-Za-z0-9_\-]{20,}['\"]")),
    ("Twilio API Key", "SK...", re.compile(r"(?i)(account_sid|auth_token)\s*[=:]\s*['\"][A-Za-z0-9]{32,}['\"]")),
    ("Password Field", "PASSWORD=", re.compile(r"(?i)^\s*(password|passwd|pwd)\s*[=:]")),
    ("Key Contains Password", "KEY=PASSWORD", re.compile(r"(?i)(_password|_secret|_token|_key)\s*=\s*['\"]?[A-Za-z0-9_\-!@#$%^&*+=]{8,}")),
]


def scan_file(path: str, context_lines: int = 2) -> List[Dict[str, Any]]:
    """Scan a single file for hardcoded secrets.

    Returns list of findings: {line, col, pattern_name, match, context}
    """
    findings: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except IOError as e:
        _err(f"Cannot read {path}: {e}")
        return findings

    for lineno, line in enumerate(lines, 1):
        for name, _, pattern in SECRET_PATTERNS:
            for m in pattern.finditer(line):
                # Skip if match is in a comment line that's just an example
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                    if "example" in stripped.lower() or "your-" in stripped.lower():
                        continue
                ctx_start = max(0, lineno - context_lines - 1)
                ctx_end = min(len(lines), lineno + context_lines)
                context = "".join(lines[ctx_start:ctx_end]).strip()
                findings.append({
                    "line": lineno,
                    "col": m.start() + 1,
                    "pattern": name,
                    "match": m.group()[:60],
                    "context": context,
                    "file": path,
                })
    return findings


def cmd_scan(paths: List[str], context: int = 2, quiet: bool = False) -> int:
    """Scan files for hardcoded secrets."""
    all_findings: List[Dict[str, Any]] = []
    total_files = 0

    expanded_paths: List[str] = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    expanded_paths.append(os.path.join(root, f))
        else:
            expanded_paths.append(p)

    for p in expanded_paths:
        if not os.path.isfile(p):
            continue
        total_files += 1
        findings = scan_file(p, context)
        all_findings.extend(findings)

    if not quiet:
        if total_files == 0:
            _warn("No files to scan.")
            return 0
        print(f"\n{_color('Secret Scan Results', 'bold')}")
        print(f"  Files scanned: {total_files}")
        print(f"  Findings:      {len(all_findings)}")
        print()

        if all_findings:
            current_file = None
            for f in all_findings:
                if f["file"] != current_file:
                    print(f"\n  {_color(f['file'], 'cyan')}:")
                    current_file = f["file"]
                sev = "HIGH" if "Password" in f["pattern"] or "Private" in f["pattern"] else "MED"
                sev_color = "red" if sev == "HIGH" else "yellow"
                print(f"    L{f['line']:04d} [{_color(sev, sev_color)}] {f['pattern']}: {_color(f['match'][:50], 'dim')}")
        else:
            _ok("No secrets detected.")

    return len(all_findings)


# ─── Config Diff ─────────────────────────────────────────────────────────────


def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    """Flatten nested dict to dot-separated keys."""
    result: Dict[str, str] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(_flatten_dict(v, key))
        elif isinstance(v, list):
            result[key] = json.dumps(v, default=str)
        else:
            result[key] = str(v)
    return result


def cmd_diff(path_a: str, path_b: str) -> int:
    """Compare two config files and show differences."""
    data_a = load_config(path_a)
    data_b = load_config(path_b)

    flat_a = _flatten_dict(data_a)
    flat_b = _flatten_dict(data_b)

    keys_a = set(flat_a.keys())
    keys_b = set(flat_b.keys())

    added = keys_b - keys_a
    removed = keys_a - keys_b
    common = keys_a & keys_b
    changed = {k for k in common if flat_a[k] != flat_b[k]}

    print(f"\n{_color('Config Diff', 'bold')}")
    print(f"  {_color('--- ' + path_a, 'red')}")
    print(f"  {_color('+++ ' + path_b, 'green')}")
    print(f"\n  {len(flat_a)} keys → {len(flat_b)} keys")
    print(f"  {len(removed)} removed, {len(added)} added, {len(changed)} changed")

    if removed:
        print(f"\n  {_color('Removed keys:', 'red')}")
        for k in sorted(removed):
            print(f"    - {k} = {flat_a[k]}")

    if added:
        print(f"\n  {_color('Added keys:', 'green')}")
        for k in sorted(added):
            print(f"    + {k} = {flat_b[k]}")

    if changed:
        print(f"\n  {_color('Changed keys:', 'yellow')}")
        for k in sorted(changed):
            print(f"    ~ {k}")
            print(f"      - {flat_a[k]}")
            print(f"      + {flat_b[k]}")

    if not added and not removed and not changed:
        _ok("Files are identical.")

    return len(removed) + len(added) + len(changed)


# ─── Template Generation ────────────────────────────────────────────────────


def cmd_template(path: str, output: Optional[str] = None, mask: str = "") -> int:
    """Generate a .env.example file from a .env file."""
    config = load_env(path)
    if not config:
        _err(f"No variables found in {path}")
        return 1

    out_path = output or (os.path.splitext(path)[0] + ".example" + os.path.splitext(path)[1])
    if not out_path:
        out_path = path + ".example"

    lines: List[str] = [
        "# .env.example",
        f"# Generated by config-vault from {os.path.basename(path)}",
        f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "#",
        "# Copy this file to .env and fill in your values:",
        "#   cp .env.example .env",
        ""
    ]

    for k, v in config.items():
        if mask:
            v = mask * min(len(v), 32) if v else ""
        else:
            v = ""  # Blank by default for example files
        comments = "" if not v else f"  # default: {v[:40]}"
        lines.append(f"{k}={v}{comments}")

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        _ok(f"Template written to {out_path} ({len(config)} variables)")
    except IOError as e:
        _err(f"Failed to write {out_path}: {e}")
        return 1
    return 0


# ─── Export / Import ─────────────────────────────────────────────────────────


def cmd_export_json(path: str, output: str) -> int:
    """Export config file to JSON format."""
    data = load_config(path)
    try:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        _ok(f"Exported to {output}")
    except IOError as e:
        _err(f"Export failed: {e}")
        return 1
    return 0


def cmd_import_json(path: str, target: str) -> int:
    """Import from JSON into another config format."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        _err(f"Failed to read JSON: {e}")
        return 1
    if not isinstance(data, dict):
        _err("JSON must contain a top-level object")
        return 1
    save_config(target, data)
    _ok(f"Imported {len(data)} keys into {target}")
    return 0


# ─── Main CLI Entry Point ────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="config-vault",
        description="Manage, validate, encrypt, and scan secrets in config files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              config-vault validate .env
              config-vault validate --required DB_HOST,DB_PORT .env
              config-vault encrypt .env --password mysecret
              config-vault decrypt .env --password mysecret
              config-vault backup .env
              config-vault restore config.json
              config-vault scan src/ .env
              config-vault diff config-v1.json config-v2.json
              config-vault template .env
              config-vault tui
        """),
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    vp = sub.add_parser("validate", help="Validate a .env or config file")
    vp.add_argument("path", help="Path to config file")
    vp.add_argument("--required", "-r", help="Comma-separated list of required keys")

    # encrypt
    ep = sub.add_parser("encrypt", help="Encrypt values in a .env file")
    ep.add_argument("path", help="Path to .env file")
    ep.add_argument("--password", "-p", required=True, help="Encryption password")
    ep.add_argument("--keys", "-k", help="Comma-separated key filter")

    # decrypt
    dp = sub.add_parser("decrypt", help="Decrypt values in a .env file")
    dp.add_argument("path", help="Path to .env file")
    dp.add_argument("--password", "-p", required=True, help="Decryption password")
    dp.add_argument("--keys", "-k", help="Comma-separated key filter")

    # backup
    bp = sub.add_parser("backup", help="Backup a config file")
    bp.add_argument("path", help="Path to config file")

    # restore
    rp = sub.add_parser("restore", help="Restore a config file from latest backup")
    rp.add_argument("path", help="Path to config file")

    # list-backups
    lb = sub.add_parser("list-backups", help="List backups for a config file")
    lb.add_argument("path", help="Path to config file")

    # scan
    sp = sub.add_parser("scan", help="Scan files for hardcoded secrets")
    sp.add_argument("paths", nargs="+", help="Files or directories to scan")
    sp.add_argument("--context", "-c", type=int, default=2, help="Context lines (default: 2)")
    sp.add_argument("--quiet", "-q", action="store_true", help="Only return exit code")

    # diff
    df = sub.add_parser("diff", help="Compare two config files")
    df.add_argument("file_a", help="First config file")
    df.add_argument("file_b", help="Second config file")

    # template
    tp = sub.add_parser("template", help="Generate .env.example from .env")
    tp.add_argument("path", help="Path to .env file")
    tp.add_argument("--output", "-o", help="Output file path")
    tp.add_argument("--mask", "-m", default="", help="Mask character for values")

    # export
    exp = sub.add_parser("export", help="Export config to JSON")
    exp.add_argument("path", help="Path to config file")
    exp.add_argument("--output", "-o", required=True, help="Output JSON file")

    # import
    imp = sub.add_parser("import", help="Import config from JSON")
    imp.add_argument("path", help="Path to JSON file")
    imp.add_argument("--target", "-t", required=True, help="Target config file")

    # tui
    sub.add_parser("tui", help="Launch interactive TUI config viewer")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the config-vault CLI."""
    if argv is None:
        argv = sys.argv[1:]

    # If no args, show help
    if not argv:
        build_parser().print_help()
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return _dispatch(args)
    except KeyboardInterrupt:
        print()
        return 1


def _dispatch(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate command handler."""
    cmd = args.command

    if cmd == "validate":
        required = args.required.split(",") if args.required else None
        path = args.path
        fmt = _detect_format(path)
        if fmt == "env":
            return validate_env(path, required)
        else:
            return validate_config(path)

    elif cmd == "encrypt":
        key_filter = args.keys.split(",") if args.keys else None
        return cmd_encrypt(args.path, args.password, key_filter)

    elif cmd == "decrypt":
        key_filter = args.keys.split(",") if args.keys else None
        return cmd_decrypt(args.path, args.password, key_filter)

    elif cmd == "backup":
        cmd_backup(args.path)
        return 0

    elif cmd == "restore":
        return cmd_restore(args.path)

    elif cmd == "list-backups":
        cmd_list_backups(args.path)
        return 0

    elif cmd == "scan":
        return cmd_scan(args.paths, args.context, args.quiet)

    elif cmd == "diff":
        return cmd_diff(args.file_a, args.file_b)

    elif cmd == "template":
        return cmd_template(args.path, args.output, args.mask)

    elif cmd == "export":
        return cmd_export_json(args.path, args.output)

    elif cmd == "import":
        return cmd_import_json(args.path, args.target)

    elif cmd == "tui":
        from config_vault.tui import run_tui
        return run_tui()

    else:
        parser = build_parser()
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
