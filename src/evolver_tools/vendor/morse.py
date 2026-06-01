#!/usr/bin/env python3
"""morse — Text to Morse code converter.

Usage: morse "SOS"
       echo "hello world" | morse [--reverse] [--audio]
       morse --reverse ".... . .-.. .-.. ---"

Converts text to Morse code and vice versa.
Supports audible output via terminal bell.
Zero-dependency (stdlib only).
"""

import sys, time

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
    '$': '...-..-', '@': '.--.-.', ' ': '/',
}

# Build reverse map
TEXT_FROM_MORSE = {v: k for k, v in MORSE_CODE.items()}

def text_to_morse(text):
    words = text.upper().split(' ')
    morse_words = []
    for word in words:
        chars = []
        for c in word:
            if c in MORSE_CODE:
                chars.append(MORSE_CODE[c])
            else:
                chars.append(c)
        morse_words.append(' '.join(chars))
    return '   '.join(morse_words)

def morse_to_text(morse):
    words = morse.split('   ')
    text_words = []
    for word in words:
        chars = word.split(' ')
        text_chars = []
        for c in chars:
            c = c.strip()
            if c in TEXT_FROM_MORSE:
                text_chars.append(TEXT_FROM_MORSE[c])
            elif c == '/':
                text_chars.append(' ')
            elif c:
                text_chars.append(c)
        text_words.append(''.join(text_chars))
    return ' '.join(text_words)

def play_morse(morse, wpm=20):
    """Play Morse code using terminal bell."""
    dot_duration = 1.2 / wpm
    for symbol in morse:
        if symbol == '.':
            sys.stdout.write('\a')
            sys.stdout.flush()
            time.sleep(dot_duration)
        elif symbol == '-':
            sys.stdout.write('\a')
            sys.stdout.flush()
            time.sleep(dot_duration * 3)
        elif symbol == ' ':
            time.sleep(dot_duration * 2)
        elif symbol == '/':
            time.sleep(dot_duration * 4)
        time.sleep(dot_duration)

def main():
    args = sys.argv[1:]
    reverse = False
    audio = False

    for a in args:
        if a == '--reverse' or a == '-r':
            reverse = True
        elif a == '--audio' or a == '-a':
            audio = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    text_args = [a for a in args if not a.startswith('-')]

    if text_args:
        text = ' '.join(text_args)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Usage: morse <text> or morse --reverse <morse_code>")
        return

    if reverse:
        result = morse_to_text(text)
        print(f"  Morse: {text}")
        print(f"  Text:  {result}")
    else:
        result = text_to_morse(text)
        print(f"  Text:  {text}")
        print(f"  Morse: {result}")
        if audio:
            print(f"  Playing... (Ctrl+C to stop)")
            try:
                play_morse(result)
            except KeyboardInterrupt:
                pass


# === Auto-registration metadata ===
TOOL_META = {
    "name": "morse",
    "func": "main",
    "desc": 'Text-Morse code converter with audio',
}

if __name__ == '__main__':
    main()
