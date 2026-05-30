#!/usr/bin/env python3
"""file-encrypt — Simple file encryption/decryption using XOR + key derivation (SHA-256)."""

import sys
import os
import hashlib
import argparse


CHUNK_SIZE = 65536
SALT_SIZE = 16


def derive_key(password, salt, iterations=100000):
    """Derive a key from password using PBKDF2-like approach."""
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
    return key


def xor_data(data, key):
    """XOR data with repeating key."""
    result = bytearray(len(data))
    key_len = len(key)
    for i in range(len(data)):
        result[i] = data[i] ^ key[i % key_len]
    return bytes(result)


def encrypt_file(input_path, output_path, password, strength='medium'):
    """Encrypt a file using XOR with derived key."""
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    iterations = {'low': 10000, 'medium': 100000, 'high': 500000}.get(strength, 100000)

    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt, iterations)

    try:
        with open(input_path, 'rb') as fin:
            plaintext = fin.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    ciphertext = xor_data(plaintext, key)

    header = b'EFX1'
    header += salt
    header += iterations.to_bytes(4, 'big')
    header += hashlib.sha256(plaintext).digest()

    try:
        with open(output_path, 'wb') as fout:
            fout.write(header)
            fout.write(ciphertext)
    except Exception as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

    orig_size = os.path.getsize(input_path)
    enc_size = os.path.getsize(output_path)
    print(f"Encrypted: {input_path}")
    print(f"  Output:   {output_path} ({enc_size} bytes)")
    print(f"  Original: {orig_size} bytes")
    print(f"  Overhead: {enc_size - orig_size} bytes")
    print(f"  Strength: {strength} ({iterations} iterations)")


def decrypt_file(input_path, output_path, password):
    """Decrypt a file encrypted with encrypt_file."""
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, 'rb') as fin:
            data = fin.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if len(data) < 53:
        print(f"File too small to be a valid encrypted file ({len(data)} bytes).", file=sys.stderr)
        sys.exit(1)

    magic = data[:4]
    if magic != b'EFX1':
        print(f"Invalid magic bytes: {magic.hex()} (expected EFX1).", file=sys.stderr)
        sys.exit(1)

    salt = data[4:20]
    iterations = int.from_bytes(data[20:24], 'big')
    stored_hash = data[24:56]
    ciphertext = data[56:]

    key = derive_key(password, salt, iterations)
    plaintext = xor_data(ciphertext, key)

    computed_hash = hashlib.sha256(plaintext).digest()
    if computed_hash != stored_hash:
        print("Decryption failed: incorrect password or corrupted file.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(output_path, 'wb') as fout:
            fout.write(plaintext)
    except Exception as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Decrypted: {output_path} ({len(plaintext)} bytes)")
    print(f"  Original hash verified: {stored_hash.hex()[:16]}...")


def main():
    parser = argparse.ArgumentParser(
        description='Simple file encryption/decryption using XOR + SHA-256 key derivation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  file-encrypt encrypt file.txt -p "mypassword"
  file-encrypt decrypt file.txt.enc -p "mypassword"
  file-encrypt encrypt --strength high file.txt -p "mypassword"
  file-encrypt encrypt file.txt -p "mypassword" -o output.enc
        """,
    )
    parser.add_argument('action', choices=['encrypt', 'decrypt'], help='Action to perform')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-p', '--password', required=True, help='Encryption/decryption password')
    parser.add_argument('-o', '--output', help='Output file path (default: input.enc for encrypt, input.dec for decrypt)')
    parser.add_argument('--strength', choices=['low', 'medium', 'high'], default='medium',
                        help='Key derivation strength (default: medium)')

    args = parser.parse_args()

    input_path = os.path.expanduser(args.input)

    if args.output:
        output_path = os.path.expanduser(args.output)
    else:
        if args.action == 'encrypt':
            output_path = input_path + '.enc'
        else:
            base, ext = os.path.splitext(input_path)
            if ext == '.enc':
                output_path = base + '.dec'
            else:
                output_path = input_path + '.dec'

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        print("Input and output paths must be different.", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(output_path):
        confirm = input(f"Output file '{output_path}' exists. Overwrite? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(1)

    try:
        if args.action == 'encrypt':
            encrypt_file(input_path, output_path, args.password, args.strength)
        else:
            decrypt_file(input_path, output_path, args.password)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
