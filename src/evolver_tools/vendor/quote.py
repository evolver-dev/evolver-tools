#!/usr/bin/env python3
"""quote — Display random inspirational/tech quotes."""

import sys
import random

TOOL_META = {
    "name": "quote",
    "func": "main",
    "desc": "Display random inspirational/tech quotes",
}

QUOTES = [
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
    ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("It's not at all important to get it right the first time. It's vitally important to get it right the last time.", "Andrew Hunt"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("The most disastrous thing that you can ever learn is your first programming language.", "Alan Kay"),
    ("Measuring programming progress by lines of code is like measuring aircraft building progress by weight.", "Bill Gates"),
    ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan"),
    ("If you automate a mess, you get an automated mess.", "Unknown"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("The purpose of abstraction is not to be vague, but to create a new semantic level.", "Edsger W. Dijkstra"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Before software can be reusable it first has to be usable.", "Ralph Johnson"),
    ("The most dangerous phrase in the language is: 'We've always done it this way.'", "Grace Hopper"),
    ("It works on my machine.", "Every Developer Ever"),
]


def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print("Usage: evolver quote          # Random quote")
        print("       evolver quote --list    # List all quotes")
        return

    if args and args[0] == "--list":
        print(f"=== {len(QUOTES)} Quotes ===\n")
        for i, (text, author) in enumerate(QUOTES, 1):
            print(f"  {i:2d}. \"{text}\"")
            print(f"      \u2014 {author}\n")
        return

    text, author = random.choice(QUOTES)
    print(f"  \"{text}\"")
    print(f"      \u2014 {author}")


if __name__ == "__main__":
    main()
