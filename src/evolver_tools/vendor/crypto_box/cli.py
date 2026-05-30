"""CLI interface for crypto-box."""

import os
import sys
import json
import argparse
from . import (
    encrypt_file, decrypt_file,
    password_strength, password_strength_feedback,
    generate_totp_secret, totp,
    hash_file, hash_directory, checksum_verify,
    get_ssl_cert_info, cert_info_from_file,
    colorize, print_banner, __version__,
)


def cmd_encrypt(args):
    """Encrypt a file."""
    if not os.path.exists(args.input):
        print(colorize(f"Error: file not found: {args.input}", "red"))
        sys.exit(1)
    out = args.output or args.input + ".enc"
    result = encrypt_file(args.input, out, args.password)
    print(colorize(f"Encrypted: {result}", "green"))


def cmd_decrypt(args):
    """Decrypt a file."""
    if not os.path.exists(args.input):
        print(colorize(f"Error: file not found: {args.input}", "red"))
        sys.exit(1)
    out = args.output or args.input.replace(".enc", ".dec", 1) if args.input.endswith(".enc") else args.input + ".dec"
    try:
        result = decrypt_file(args.input, out, args.password)
        print(colorize(f"Decrypted: {result}", "green"))
    except (ValueError, Exception) as e:
        print(colorize(f"Decryption failed: {e}", "red"))
        sys.exit(1)


def cmd_password(args):
    """Check password strength."""
    pw = args.password
    if not pw and not args.stdin:
        pw = os.environ.get("CRYPTOBOX_PASSWORD", "")
    if not pw and args.stdin:
        pw = sys.stdin.read().strip()
    if not pw:
        print(colorize("Error: no password provided", "red"))
        sys.exit(1)
    score = password_strength(pw)
    label = password_strength_feedback(score)
    bar_len = 20
    filled = int(score / 100 * bar_len)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(colorize(f"  Strength: {bar} {score}/100", "cyan"))
    print(colorize(f"  Rating: {label}", "green" if score >= 60 else "yellow" if score >= 40 else "red", bold=True))


def cmd_totp(args):
    """Generate TOTP codes."""
    secret = args.secret or os.environ.get("CRYPTOBOX_TOTP_SECRET", "")
    if not secret:
        new_secret = generate_totp_secret()
        print(colorize(f"Generated new TOTP secret:", "yellow"))
        print(f"  {new_secret}")
        print(colorize("  (pass this as --secret to generate codes)", "cyan"))
        return
    try:
        code, remaining = totp(secret, args.digits, args.interval)
        print(colorize(f"  Code: {colorize(code, 'green', bold=True)}", "cyan"))
        print(colorize(f"  Expires in: {remaining}s", "yellow"))
    except Exception as e:
        print(colorize(f"TOTP error: {e}", "red"))
        sys.exit(1)


def cmd_hash(args):
    """Hash files or directories."""
    algo = args.algo
    targets = args.paths
    if not targets:
        print(colorize("Error: no paths specified", "red"))
        sys.exit(1)
    for path in targets:
        if not os.path.exists(path):
            print(colorize(f"File not found: {path}", "red"))
            continue
        if os.path.isdir(path):
            results = hash_directory(path, algo)
            print(colorize(f"\nDirectory: {path} ({algo.upper()})", "blue", bold=True))
            for fname, digest in results.items():
                print(f"  {digest}  {fname}")
        else:
            digest = hash_file(path, algo)
            print(f"{digest}  {path}")


def cmd_checksum(args):
    """Verify files against a checksum file."""
    if not os.path.exists(args.checksum_file):
        print(colorize(f"Checksum file not found: {args.checksum_file}", "red"))
        sys.exit(1)
    results = checksum_verify(args.checksum_file, args.algo)
    total = len(results)
    ok = sum(1 for r in results if r[2] == "OK")
    failed = [r for r in results if r[2] != "OK"]
    print(colorize(f"Verified {total} entries ({args.algo}):", "blue"))
    for fname, actual, status in results:
        if status == "OK":
            print(colorize(f"  [OK]  {fname}", "green"))
        elif status == "MISSING":
            print(colorize(f"  [MISSING]  {fname}", "yellow"))
        else:
            print(colorize(f"  [FAIL]  {fname}", "red"))
            print(colorize(f"         expected: {actual}", "red"))
    if failed:
        print(colorize(f"\n{len(failed)} failures", "red"))
        sys.exit(1)
    else:
        print(colorize(f"\nAll {total} entries verified OK.", "green"))


def cmd_ssl(args):
    """Check SSL certificate info."""
    host = args.host
    port = args.port
    try:
        info = get_ssl_cert_info(host, port, args.timeout)
        print(colorize(f"\nSSL Certificate for {host}:{port}", "blue", bold=True))
        print(colorize(f"  Subject:      ", "cyan"), info.get("subject", {}))
        print(colorize(f"  Issuer:       ", "cyan"), info.get("issuer", {}))
        print(colorize(f"  Serial:       ", "cyan"), info.get("serialNumber", ""))
        print(colorize(f"  Version:      ", "cyan"), info.get("version", ""))
        print(colorize(f"  Valid From:   ", "cyan"), info.get("notBefore", ""))
        print(colorize(f"  Valid Until:  ", "cyan"), info.get("notAfter", ""))
        days = info.get("daysRemaining")
        if days is not None:
            color = "green" if days > 30 else "yellow" if days > 0 else "red"
            expired = info.get("isExpired", False)
            label = "EXPIRED" if expired else f"{days} days remaining"
            print(colorize(f"  Status:       ", "cyan"), colorize(label, color, bold=True))
        print(colorize(f"  SANs:         ", "cyan"))
        for san in info.get("subjectAltName", []):
            print(f"    {san}")
    except Exception as e:
        print(colorize(f"SSL error: {e}", "red"))
        sys.exit(1)


def cmd_cert(args):
    """Inspect a local certificate file."""
    path = args.path
    if not os.path.exists(path):
        print(colorize(f"Certificate file not found: {path}", "red"))
        sys.exit(1)
    try:
        info = cert_info_from_file(path)
        print(colorize(f"\nCertificate: {path}", "blue", bold=True))
        print(colorize(f"  Subject:      ", "cyan"), info.get("subject", {}))
        print(colorize(f"  Issuer:       ", "cyan"), info.get("issuer", {}))
        print(colorize(f"  Serial:       ", "cyan"), info.get("serialNumber", ""))
        print(colorize(f"  Version:      ", "cyan"), info.get("version", ""))
        print(colorize(f"  Signature:    ", "cyan"), info.get("signatureAlgorithm", ""))
        print(colorize(f"  Valid From:   ", "cyan"), info.get("notBefore", ""))
        print(colorize(f"  Valid Until:  ", "cyan"), info.get("notAfter", ""))
        days = info.get("daysRemaining")
        if days is not None:
            color = "green" if days > 30 else "yellow" if days > 0 else "red"
            label = "EXPIRED" if info.get("isExpired") else f"{days} days remaining"
            print(colorize(f"  Status:       ", "cyan"), colorize(label, color, bold=True))
    except Exception as e:
        print(colorize(f"Cert error: {e}", "red"))
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="crypto-box",
        description="All-in-one security toolkit (zero external dependencies)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  crypto-box encrypt secret.txt -p mypassword
  crypto-box decrypt secret.txt.enc -p mypassword
  crypto-box password "P@ssw0rd!"
  crypto-box totp --generate
  crypto-box hash file.txt --algo sha256
  crypto-box hash dir/ --algo sha512
  crypto-box checksum SHA256SUMS --algo sha256
  crypto-box ssl example.com
  crypto-box cert cert.pem
""",
    )
    parser.add_argument("--version", action="version", version=f"crypto-box {__version__}")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # encrypt
    p_enc = sub.add_parser("encrypt", help="Encrypt a file")
    p_enc.add_argument("input", help="Input file path")
    p_enc.add_argument("-o", "--output", help="Output file path (default: input.enc)")
    p_enc.add_argument("-p", "--password", required=True, help="Encryption password")

    # decrypt
    p_dec = sub.add_parser("decrypt", help="Decrypt a file")
    p_dec.add_argument("input", help="Encrypted file path")
    p_dec.add_argument("-o", "--output", help="Output file path (default: input.dec)")
    p_dec.add_argument("-p", "--password", required=True, help="Decryption password")

    # password
    p_pw = sub.add_parser("password", help="Check password strength")
    p_pw.add_argument("password", nargs="?", default="", help="Password to check")
    p_pw.add_argument("--stdin", action="store_true", help="Read password from stdin")

    # totp
    p_totp = sub.add_parser("totp", help="Generate TOTP codes")
    p_totp.add_argument("-s", "--secret", help="Base32 TOTP secret")
    p_totp.add_argument("-d", "--digits", type=int, default=6, help="Number of digits (default: 6)")
    p_totp.add_argument("-i", "--interval", type=int, default=30, help="Time interval in seconds (default: 30)")
    p_totp.add_argument("-g", "--generate", action="store_true", help="Generate a new TOTP secret")

    # hash
    p_hash = sub.add_parser("hash", help="Hash files or directories")
    p_hash.add_argument("paths", nargs="+", help="Files/directories to hash")
    p_hash.add_argument("-a", "--algo", default="sha256",
                        choices=["md5", "sha1", "sha256", "sha512"], help="Hash algorithm")

    # checksum
    p_csum = sub.add_parser("checksum", help="Verify files against a checksum file")
    p_csum.add_argument("checksum_file", help="Checksum file path")
    p_csum.add_argument("-a", "--algo", default="sha256",
                        choices=["md5", "sha1", "sha256", "sha512"], help="Hash algorithm")

    # ssl
    p_ssl = sub.add_parser("ssl", help="Check SSL certificate of a remote host")
    p_ssl.add_argument("host", help="Hostname to check")
    p_ssl.add_argument("-p", "--port", type=int, default=443, help="Port (default: 443)")
    p_ssl.add_argument("-t", "--timeout", type=float, default=10.0, help="Connection timeout")

    # cert
    p_cert = sub.add_parser("cert", help="Inspect a local PEM certificate file")
    p_cert.add_argument("path", help="Path to PEM certificate file")

    return parser


def cli_main(argv: list | None = None) -> None:
    """Main CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print_banner()
        build_parser().print_help()
        return

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "encrypt":
        cmd_encrypt(args)
    elif args.command == "decrypt":
        cmd_decrypt(args)
    elif args.command == "password":
        cmd_password(args)
    elif args.command == "totp":
        cmd_totp(args)
    elif args.command == "hash":
        cmd_hash(args)
    elif args.command == "checksum":
        cmd_checksum(args)
    elif args.command == "ssl":
        cmd_ssl(args)
    elif args.command == "cert":
        cmd_cert(args)
    else:
        parser.print_help()
