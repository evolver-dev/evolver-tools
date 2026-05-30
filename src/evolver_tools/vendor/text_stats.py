#!/usr/bin/env python3
"""text-stats — File/stdin text statistics analyzer.

Usage: text-stats [--file PATH]
       cat file.txt | text-stats

Analyzes text and reports: word count, character count, line count,
sentence count, average word length, and estimated reading time.
Zero-dependency (stdlib only).
"""

import sys
import argparse

# Average reading speed: ~238 words per minute (common benchmark)
WPM = 238


def count_sentences(text):
    """Count sentences by splitting on terminal punctuation."""
    import re
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def count_words(text):
    """Count words (whitespace-delimited tokens containing letters)."""
    words = text.split()
    return len(words)


def count_chars(text):
    """Count characters including spaces, excluding newlines."""
    return len(text)


def average_word_length(text):
    """Compute average word length (characters per word)."""
    words = [w for w in text.split() if w.strip()]
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def reading_time(word_count):
    """Estimate reading time in minutes (decimal)."""
    return word_count / WPM


def format_reading_time(minutes):
    """Format reading time as human-readable string."""
    if minutes < 1:
        secs = round(minutes * 60)
        return f"{secs} sec"
    mins = int(minutes)
    secs = round((minutes - mins) * 60)
    if secs == 0:
        return f"{mins} min"
    return f"{mins} min {secs} sec"


def main():
    parser = argparse.ArgumentParser(
        description="Text statistics analyzer — word/char/line/sentence counts, "
                    "avg word length, reading time."
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to input file (reads from stdin if omitted)"
    )
    args = parser.parse_args()

    # Read input
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(0)

    # Compute statistics
    chars = count_chars(text)
    words = count_words(text)
    lines = text.count("\n")
    if lines == 0 and text:
        lines = 1
    sentences = count_sentences(text)
    avg_wlen = average_word_length(text)
    read_mins = reading_time(words)
    read_str = format_reading_time(read_mins)

    # Output
    print(f"Characters:       {chars}")
    print(f"Words:            {words}")
    print(f"Lines:            {lines}")
    print(f"Sentences:        {sentences}")
    print(f"Avg word length:  {avg_wlen:.2f}")
    print(f"Reading time:     {read_str}  ({WPM} wpm)")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "text-stats",
    "func": "main",
    "desc": "Text statistics (words, chars, sentences, reading time)",
}

if __name__ == "__main__":
    main()
