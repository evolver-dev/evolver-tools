#!/usr/bin/env python3
"""uuid_gen — UUID generator (v1, v4, v5, v7).

Usage: uuid_gen              # v4 random UUID
       uuid_gen 5            # Generate 5 UUIDs
       uuid_gen --v1         # Time-based UUID
       uuid_gen --v5 myns myname  # Namespace + name UUID
       uuid_gen --v7         # Time-ordered UUID (Python 3.14+)

Generate one or more UUIDs. Default: UUID v4 (random).
"""

import sys
import uuid

TOOL_META = {
    "name": "uuid_gen",
    "func": "main",
    "desc": "UUID generator (v1/v4/v5/v7)",
}

def main():
    args = sys.argv[1:]

    version = 'v4'
    count = 1
    namespace = None
    name = None

    i = 0
    while i < len(args):
        if args[i] in ('-h', '--help'):
            print(__doc__)
            return
        elif args[i] == '--v1':
            version = 'v1'
            i += 1
        elif args[i] == '--v4':
            version = 'v4'
            i += 1
        elif args[i] == '--v5':
            version = 'v5'
            i += 1
            if i + 2 <= len(args):
                namespace = args[i + 1]
                name = args[i + 2]
                i += 3
            else:
                print("Error: --v5 requires NAMESPACE and NAME", file=sys.stderr)
                sys.exit(1)
        elif args[i] == '--v7':
            version = 'v7'
            i += 1
        else:
            try:
                count = int(args[i])
            except ValueError:
                print(f"Unknown argument: {args[i]}", file=sys.stderr)
                sys.exit(1)
            i += 1

    for _ in range(count):
        if version == 'v1':
            print(str(uuid.uuid1()))
        elif version == 'v4':
            print(str(uuid.uuid4()))
        elif version == 'v5':
            ns_map = {'dns': uuid.NAMESPACE_DNS, 'url': uuid.NAMESPACE_URL,
                      'oid': uuid.NAMESPACE_OID, 'x500': uuid.NAMESPACE_X500}
            ns = ns_map.get(namespace.lower(), uuid.NAMESPACE_DNS)
            print(str(uuid.uuid5(ns, name)))
        elif version == 'v7':
            try:
                print(str(uuid.uuid7()))
            except AttributeError:
                print("Error: UUID v7 requires Python 3.14+", file=sys.stderr)
                sys.exit(1)
