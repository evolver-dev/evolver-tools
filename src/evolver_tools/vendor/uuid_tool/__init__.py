"""uuid — UUID generator tool.

Generates UUIDs in various versions (v1, v3, v4, v5, v7).
CLI entry point: python -m evolver_tools.vendor.uuid_tool [options]
"""

import argparse
import time
import os
import sys
import uuid as _uuid

# ── Custom uuid7 for Python < 3.14 ──────────────────────────────────────────

def _uuid7() -> _uuid.UUID:
    """Generate a UUID v7 (time-ordered) per RFC 9562.

    Works on all Python versions; no dependency on 3.14+ uuid.uuid7().
    Layout:
      - 48 bit Unix timestamp (ms)
      -  4 bit version (7)
      - 12 bit rand_a
      -  2 bit variant (10)
      - 62 bit rand_b
    """
    timestamp_ms = int(time.time() * 1000)

    # 74 random bits (12 rand_a + 62 rand_b)
    rand_raw = int.from_bytes(os.urandom(10), byteorder="big") >> 6  # 80 → 74 bits
    rand_a = (rand_raw >> 62) & 0xFFF  # top 12 bits
    rand_b = rand_raw & ((1 << 62) - 1)  # bottom 62 bits

    # Build 128-bit integer in standard UUID byte order (big-endian)
    value = (
        (timestamp_ms << 80)   # bits 127:80 = unix_ts_ms
        | (0x7 << 76)          # bits 79:76  = version
        | (rand_a << 64)       # bits 75:64  = rand_a
        | (0x2 << 62)          # bits 63:62  = variant (10xx)
        | rand_b               # bits 61:0   = rand_b
    )

    return _uuid.UUID(int=value)


# ── Namespace helpers ───────────────────────────────────────────────────────

_NAMESPACES = {
    "dns": _uuid.NAMESPACE_DNS,
    "url": _uuid.NAMESPACE_URL,
    "oid": _uuid.NAMESPACE_OID,
    "x500": _uuid.NAMESPACE_X500,
    "nil": _uuid.UUID(int=0),  # nil UUID (UUID.hex == "0000...0")
}


def _resolve_ns(value: str) -> _uuid.UUID:
    """Resolve a namespace string to a UUID object."""
    if value in _NAMESPACES:
        return _NAMESPACES[value]
    try:
        return _uuid.UUID(value)
    except ValueError:
        msg = (
            f"Invalid namespace: {value!r}. "
            f"Use a UUID string or one of: {', '.join(sorted(_NAMESPACES))}"
        )
        raise ValueError(msg)


# ── Main generator ──────────────────────────────────────────────────────────

def _format(u: _uuid.UUID, upper: bool, no_hyphen: bool) -> str:
    s = str(u)
    if no_hyphen:
        s = s.replace("-", "")
    if upper:
        s = s.upper()
    return s


def generate_uuid(
    version: int = 4,
    count: int = 1,
    upper: bool = False,
    no_hyphen: bool = False,
    name: str | None = None,
    ns: str | None = None,
) -> list[str]:
    """Generate one or more UUID strings.

    Args:
        version: UUID version (1, 3, 4, 5, 7).  Default 4.
        count:   How many to generate.  Default 1, max 100.
        upper:   Output uppercase hex.
        no_hyphen: Omit hyphen separators.
        name:    String to hash (v3/v5 only).
        ns:      Namespace UUID or well-known name (v3/v5 only).

    Returns:
        List of formatted UUID strings.
    """
    count = max(1, min(count, 100))
    results: list[str] = []

    for _ in range(count):
        if version == 1:
            u = _uuid.uuid1()
        elif version == 4:
            u = _uuid.uuid4()
        elif version == 7:
            u = _uuid7()
        elif version in (3, 5):
            if not name:
                raise ValueError("--name is required for UUID v3/v5")
            ns_uuid = _resolve_ns(ns or "url")
            if version == 3:
                u = _uuid.uuid3(ns_uuid, name)
            else:
                u = _uuid.uuid5(ns_uuid, name)
        else:
            raise ValueError(f"Unsupported UUID version: {version}")

        results.append(_format(u, upper=upper, no_hyphen=no_hyphen))

    return results


# ── CLI ─────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uuid",
        description="Generate UUIDs (v1, v3, v4, v5, v7).",
    )
    parser.add_argument(
        "-1",
        dest="version",
        action="store_const",
        const=1,
        help="Generate UUID v1 (time-based).",
    )
    parser.add_argument(
        "-3",
        dest="version",
        action="store_const",
        const=3,
        help="Generate UUID v3 (MD5 hash of name+namespace).",
    )
    parser.add_argument(
        "-4",
        dest="version",
        action="store_const",
        const=4,
        help="Generate UUID v4 (random).  This is the default.",
    )
    parser.add_argument(
        "-5",
        dest="version",
        action="store_const",
        const=5,
        help="Generate UUID v5 (SHA-1 hash of name+namespace).",
    )
    parser.add_argument(
        "-7",
        dest="version",
        action="store_const",
        const=7,
        help="Generate UUID v7 (time-ordered random).",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=1,
        metavar="N",
        help="Generate N UUIDs (1-100).  Default: 1.",
    )
    parser.add_argument(
        "--upper",
        action="store_true",
        help="Output uppercase hex.",
    )
    parser.add_argument(
        "--no-hyphen",
        action="store_true",
        help="Omit hyphen separators.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        metavar="STRING",
        help="Name/hash input for v3/v5 UUIDs.",
    )
    parser.add_argument(
        "--ns",
        type=str,
        default="url",
        metavar="NS",
        help=(
            "Namespace for v3/v5 UUIDs.  Either a UUID string or one of: "
            f"{', '.join(sorted(_NAMESPACES))}.  Default: url."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # No explicit version flag → default to v4
    if args.version is None:
        args.version = 4

    try:
        uuids = generate_uuid(
            version=args.version,
            count=args.n,
            upper=args.upper,
            no_hyphen=args.no_hyphen,
            name=args.name,
            ns=args.ns,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for u in uuids:
        print(u)

    return 0


if __name__ == "__main__":
    sys.exit(main())
