#!/usr/bin/env python3
"""hex-tool — Hex encode/decode and conversion tool."""
import binascii
import sys

TOOL_META = {
    "name": "hex-tool",
    "func": "main",
    "desc": "Hex encode/decode. Usage: hex-tool encode <text> | hex-tool decode <hex>",
}

def encode(data):
    return binascii.hexlify(data.encode()).decode()

def decode(hex_str):
    try:
        return binascii.unhexlify(hex_str.replace(" ", "").replace("\n", "")).decode()
    except UnicodeDecodeError:
        return str(binascii.unhexlify(hex_str.replace(" ", "")))
    except binascii.Error as e:
        return f"Error: {e}"

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print("Usage:")
        print("  hex-tool encode <text>     Encode text to hex")
        print("  hex-tool decode <hex>      Decode hex to text")
        print("  hex-tool dump <file>       Hex dump a file")
        print("  hex-tool                       Interactive mode")
        return
    cmd = args[0]
    if cmd == "encode":
        text = " ".join(args[1:])
        print(encode(text))
    elif cmd == "decode":
        hex_str = " ".join(args[1:])
        print(decode(hex_str))
    elif cmd == "dump":
        filepath = args[1]
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            offset = 0
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                print(f"{offset:08x}  {hex_part:<48}  {ascii_part}")
                offset += 16
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
