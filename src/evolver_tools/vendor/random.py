#!/usr/bin/env python3
"""random — Random generation utility: passwords, UUIDs, hex, integers."""

import string
import random
import uuid
import sys

TOOL_META = {
    "name": "random",
    "func": "main",
    "desc": "Random generation: password, uuid, hex, int. Usage: random password [len] | uuid | hex [bytes] | int [min] [max]",
}


def cmd_password(args):
    length = 16
    if args:
        try:
            length = int(args[0])
        except ValueError:
            print("Error: password length must be an integer", file=sys.stderr)
            sys.exit(1)
    if length < 1:
        print("Error: password length must be at least 1", file=sys.stderr)
        sys.exit(1)
    charset = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    pwd = "".join(random.SystemRandom().choice(charset) for _ in range(length))
    print(pwd)


def cmd_uuid(args):
    print(str(uuid.uuid4()))


def cmd_hex(args):
    num_bytes = 8
    if args:
        try:
            num_bytes = int(args[0])
        except ValueError:
            print("Error: byte count must be an integer", file=sys.stderr)
            sys.exit(1)
    if num_bytes < 1:
        print("Error: byte count must be at least 1", file=sys.stderr)
        sys.exit(1)
    data = random.SystemRandom().getrandbits(num_bytes * 8).to_bytes(num_bytes, "big")
    print(data.hex())


def cmd_int(args):
    min_val = 0
    max_val = 100
    if len(args) >= 2:
        try:
            min_val = int(args[0])
            max_val = int(args[1])
        except ValueError:
            print("Error: min and max must be integers", file=sys.stderr)
            sys.exit(1)
    elif len(args) == 1:
        try:
            max_val = int(args[0])
        except ValueError:
            print("Error: max must be an integer", file=sys.stderr)
            sys.exit(1)
    if min_val > max_val:
        print("Error: min must be <= max", file=sys.stderr)
        sys.exit(1)
    print(random.SystemRandom().randint(min_val, max_val))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: random <command> [args]")
        print()
        print("Commands:")
        print("  password [length]    Generate a random password (default: 16 chars)")
        print("  uuid                 Generate a random UUIDv4")
        print("  hex [bytes]          Generate random hex string (default: 8 bytes = 16 hex chars)")
        print("  int [min] [max]      Generate a random integer (default: 0-100)")
        return

    cmd = args[0]
    cmd_args = args[1:]

    commands = {
        "password": cmd_password,
        "uuid": cmd_uuid,
        "hex": cmd_hex,
        "int": cmd_int,
    }

    if cmd in commands:
        commands[cmd](cmd_args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Available: password, uuid, hex, int", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
