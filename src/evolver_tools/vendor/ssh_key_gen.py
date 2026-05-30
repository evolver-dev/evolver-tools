#!/usr/bin/env python3
"""ssh-key-gen — Generate SSH key pairs. Wrapper around ssh-keygen with convenience options."""

import sys
import os
import subprocess
import stat

def generate_key(key_path, key_type="ed25519", comment="", passphrase="", bits=0):
    """Generate an SSH key pair."""
    if os.path.exists(key_path):
        return False, f"Key already exists: {key_path}"

    args = ["ssh-keygen", "-t", key_type, "-f", key_path, "-N", passphrase or ""]

    if comment:
        args.extend(["-C", comment])

    if key_type == "rsa" and bits > 0:
        args.extend(["-b", str(bits)])

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip()

    pub_path = key_path + ".pub"
    if os.path.exists(pub_path):
        os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
        os.chmod(pub_path, stat.S_IRUSR | stat.S_IWUSR)  # 600

    return True, f"Generated: {key_path}"

def list_keys(directory):
    """List SSH keys in directory."""
    keys = []
    for f in os.listdir(directory):
        fpath = os.path.join(directory, f)
        if os.path.isfile(fpath) and not f.endswith(".pub"):
            pub = fpath + ".pub"
            if os.path.exists(pub):
                keys.append((f, fpath))
    return keys

def show_fingerprint(key_path):
    """Show key fingerprint."""
    result = subprocess.run(["ssh-keygen", "-lf", key_path], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate SSH key pairs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ssh-key-gen                    # Generate ed25519 key in ~/.ssh/id_ed25519
  ssh-key-gen --type rsa --bits 4096
  ssh-key-gen --list             # List all keys in ~/.ssh
  ssh-key-gen --fingerprint ~/.ssh/id_ed25519
        """)
    parser.add_argument("--type", default="ed25519", choices=["ed25519", "rsa", "ecdsa", "dsa"],
                        help="Key type (default: ed25519)")
    parser.add_argument("--bits", type=int, default=0,
                        help="Key size in bits (for RSA: 2048-4096)")
    parser.add_argument("--comment", default="", help="Key comment")
    parser.add_argument("--passphrase", default="", help="Key passphrase")
    parser.add_argument("--output", default="", help="Output path (default: ~/.ssh/id_<type>)")
    parser.add_argument("--list", action="store_true", help="List existing keys")
    parser.add_argument("--fingerprint", nargs="?", const="~/.ssh/id_ed25519", default="",
                        help="Show fingerprint of a key")
    args = parser.parse_args()

    # List keys
    if args.list:
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.isdir(ssh_dir):
            print("No ~/.ssh directory found")
            return
        keys = list_keys(ssh_dir)
        if not keys:
            print("No SSH keys found in ~/.ssh")
            return
        print(f"SSH keys in {ssh_dir}:")
        print()
        for name, fpath in keys:
            fp = show_fingerprint(fpath)
            print(f"  {name}")
            if fp:
                print(f"    {fp}")
        print()
        print(f"  Total: {len(keys)} keys")
        return

    # Show fingerprint
    if args.fingerprint:
        fpath = os.path.expanduser(args.fingerprint)
        if not os.path.exists(fpath):
            print(f"Key not found: {fpath}")
            sys.exit(1)
        fp = show_fingerprint(fpath)
        print(fp)
        return

    # Generate key
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.isdir(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)

    key_path = args.output or os.path.join(ssh_dir, f"id_{args.type}")
    if args.output:
        key_path = os.path.expanduser(args.output)

    success, message = generate_key(key_path, args.type, args.comment, args.passphrase, args.bits)
    print(message)

    if success:
        fp = show_fingerprint(key_path)
        if fp:
            print(f"Fingerprint: {fp}")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "ssh-key-gen",
    "func": "main",
    "desc": 'Generate SSH key pairs',
}

if __name__ == "__main__":
    main()
