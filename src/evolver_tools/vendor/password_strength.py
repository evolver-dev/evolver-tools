#!/usr/bin/env python3
"""password-strength — Evaluate password strength and entropy.

Usage: password-strength <password>
       cat passwords.txt | password-strength

Analyzes password strength (length, chars, entropy, patterns).
Returns score 0-100 and actionable recommendations.
Zero-dependency (stdlib only).
"""

import sys, re, math, string

def calculate_entropy(password):
    """Calculate Shannon entropy of a password."""
    if not password:
        return 0
    freq = {}
    for c in password:
        freq[c] = freq.get(c, 0) + 1
    entropy = 0
    length = len(password)
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def estimate_charset_size(password):
    """Estimate the character set size used."""
    size = 0
    if re.search(r'[a-z]', password):
        size += 26
    if re.search(r'[A-Z]', password):
        size += 26
    if re.search(r'[0-9]', password):
        size += 10
    if re.search(r'[^a-zA-Z0-9]', password):
        size += 33  # approx special chars
    return size

def check_common_patterns(password):
    """Check for common patterns and return warnings."""
    issues = []
    lower = password.lower()

    # Common passwords
    common = ['password', '123456', 'qwerty', 'letmein', 'admin', 'welcome',
              'monkey', 'dragon', 'master', 'passw0rd', 'login', 'abc123',
              'trustno1', 'iloveyou', 'sunshine', 'princess']
    if lower in common:
        issues.append("This is one of the most common passwords")

    # Keyboard patterns
    if re.search(r'(?:qwert|asdf|zxcv|uiop|hjkl|bnm)', lower):
        issues.append("Contains keyboard pattern (e.g., qwerty, asdf)")

    # Sequential chars
    if re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', lower):
        issues.append("Contains sequential characters (e.g., abc, xyz)")
    if re.search(r'(?:012|123|234|345|456|567|678|789|890)', password):
        issues.append("Contains sequential numbers (e.g., 123, 456)")

    # Repeated chars
    if re.search(r'(.)\1{2,}', password):
        issues.append("Contains repeated characters (e.g., aaa, 111)")

    # Leet speak check
    if re.search(r'[50@!]', password) and re.search(r'[a-zA-Z]{3,}', password):
        pass  # common, ignore

    # Date patterns
    if re.search(r'(?:19|20)\d{2}', password):
        issues.append("Contains a year (YYYY) — easily guessed")

    return issues

def rate_strength(password):
    """Rate password strength 0-100."""
    if not password:
        return 0, "Empty password"

    length = len(password)
    charset = estimate_charset_size(password)
    entropy = calculate_entropy(password)
    bits = math.log2(charset) * length if charset > 0 else 0

    score = 0

    # Length scoring (up to 40 points)
    if length >= 16:
        score += 40
    elif length >= 12:
        score += 30
    elif length >= 10:
        score += 20
    elif length >= 8:
        score += 10
    else:
        score += 0

    # Character variety (up to 30 points)
    types = 0
    if re.search(r'[a-z]', password): types += 1
    if re.search(r'[A-Z]', password): types += 1
    if re.search(r'[0-9]', password): types += 1
    if re.search(r'[^a-zA-Z0-9]', password): types += 1
    score += types * 7.5

    # Entropy bonus (up to 30 points)
    if entropy >= 4:
        score += min(30, entropy * 5)

    # Penalty for common patterns
    issues = check_common_patterns(password)
    score -= len(issues) * 10

    return max(0, min(100, int(score)))

def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    if args:
        passwords = [' '.join(args)]
    elif not sys.stdin.isatty():
        passwords = [line.strip() for line in sys.stdin if line.strip()]
    else:
        print("Usage: password-strength <password>")
        return

    for pw in passwords:
        length = len(pw)
        charset = estimate_charset_size(pw)
        entropy = calculate_entropy(pw)
        bits = math.log2(charset) * length if charset > 0 else 0
        score = rate_strength(pw)
        issues = check_common_patterns(pw)

        # Determine strength label
        if score >= 80:
            label, color = "Very Strong", '\033[1;32m'
        elif score >= 60:
            label, color = "Strong", '\033[0;32m'
        elif score >= 40:
            label, color = "Fair", '\033[1;33m'
        elif score >= 20:
            label, color = "Weak", '\033[0;31m'
        else:
            label, color = "Very Weak", '\033[1;31m'
        reset = '\033[0m'

        print()
        print(f"  Password: {'*' * max(2, length-4)}{pw[-4:] if length>4 else pw}")
        print(f"  Length:   {length} chars")
        print(f"  Charset:  {charset} possible characters")
        print(f"  Entropy:  {entropy:.2f} (bits per char)")
        print(f"  Bits:     {bits:.0f} (total)")
        print(f"  Score:    {color}{score}/100 — {label}{reset}")
        if issues:
            print(f"  Issues:")
            for issue in issues:
                print(f"    ⚠ {issue}")
        print()

if __name__ == '__main__':
    main()
