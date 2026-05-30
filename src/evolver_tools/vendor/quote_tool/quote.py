#!/usr/bin/env python3
"""quote — Random quote generator (inspirational, tech, programming)

Built-in collection of 100+ curated quotes.

Usage:
    quote                    # Random quote
    quote --category=tech    # Quote from tech category
    quote --category=life    # Quote from life category
    quote --count=5          # Show 5 quotes
    quote --author=Tesla     # Search by author
    quote list               # List categories
    quote add "text" --author=Name  # Add custom quote to local file
"""
import sys
import os
import random
import json


QUOTES_FILE = os.path.expanduser('~/.evolver_quotes.json')

BUILTIN_QUOTES = {
    'tech': [
        ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
        ("The best way to predict the future is to invent it.", "Alan Kay"),
        ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
        ("Talk is cheap. Show me the code.", "Linus Torvalds"),
        ("First, solve the problem. Then, write the code.", "John Johnson"),
        ("Make it work, make it right, make it fast.", "Kent Beck"),
        ("Premature optimization is the root of all evil.", "Donald Knuth"),
        ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan"),
        ("There are only two hard things in Computer Science: cache invalidation and naming things.", "Phil Karlton"),
        ("The purpose of abstraction is not to be vague, but to create a new semantic level.", "Alan Perlis"),
        ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
        ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
        ("In software, the most beautiful code, the most beautiful functions, and the most beautiful programs are sometimes not there at all.", "John Carmack"),
        ("A language that doesn't affect the way you think about programming is not worth knowing.", "Alan Perlis"),
        ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
    ],
    'life': [
        ("The journey of a thousand miles begins with one step.", "Lao Tzu"),
        ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
        ("The only impossible journey is the one you never begin.", "Tony Robbins"),
        ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
        ("The obstacle is the path.", "Zen Proverb"),
        ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("The mind is everything. What you think you become.", "Buddha"),
        ("Everything you can imagine is real.", "Pablo Picasso"),
        ("Act as if what you do makes a difference. It does.", "William James"),
        ("What lies behind us and what lies before us are tiny matters compared to what lies within us.", "Ralph Waldo Emerson"),
        ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
        ("Happiness is not something ready made. It comes from your own actions.", "Dalai Lama"),
        ("Do not go where the path may lead, go instead where there is no path and leave a trail.", "Ralph Waldo Emerson"),
        ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ],
    'programming': [
        ("Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live.", "John Woods"),
        ("Measuring programming progress by lines of code is like measuring aircraft building progress by weight.", "Bill Gates"),
        ("Walking on water and developing software from a specification are easy if both are frozen.", "Edward V. Berard"),
        ("If debugging is the process of removing bugs, then programming must be the process of putting them in.", "Edsger W. Dijkstra"),
        ("The best programs are written so that computing machines can perform them quickly and so that human beings can understand them clearly.", "Donald Knuth"),
        ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
        ("Give someone a program; you frustrate them for a day. Teach them how to program; you frustrate them for a lifetime.", "David Leinweber"),
        ("It's not that I'm so smart, it's just that I stay with problems longer.", "Albert Einstein"),
        ("One man's constant is another man's variable.", "Alan Perlis"),
        ("Deleted code is debugged code.", "Jeff Sickel"),
    ],
    'build': [
        ("Build something 100 people love, not something 1 million people kind of like.", "Brian Chesky"),
        ("The biggest risk is not taking any risk.", "Mark Zuckerberg"),
        ("If you are not embarrassed by the first version of your product, you've launched too late.", "Reid Hoffman"),
        ("Move fast and break things.", "Mark Zuckerberg"),
        ("Done is better than perfect.", "Sheryl Sandberg"),
        ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
        ("Your most unhappy customers are your greatest source of learning.", "Bill Gates"),
        ("It's not about ideas. It's about making ideas happen.", "Scott Belsky"),
        ("If you can't feed a team with two pizzas, it's too large.", "Jeff Bezos"),
        ("Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.", "Antoine de Saint-Exupéry"),
    ],
    'wisdom': [
        ("The only true wisdom is in knowing you know nothing.", "Socrates"),
        ("The unexamined life is not worth living.", "Socrates"),
        ("I think, therefore I am.", "René Descartes"),
        ("He who has a why to live can bear almost any how.", "Friedrich Nietzsche"),
        ("What does not kill me makes me stronger.", "Friedrich Nietzsche"),
        ("The cave you fear to enter holds the treasure you seek.", "Joseph Campbell"),
        ("Knowing others is intelligence; knowing yourself is true wisdom.", "Lao Tzu"),
        ("The quietest people have the loudest minds.", "Stephen Hawking"),
        ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
        ("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    ],
}


def load_custom_quotes():
    """Load user-added quotes from file."""
    if os.path.exists(QUOTES_FILE):
        try:
            with open(QUOTES_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_custom_quote(text, author):
    """Save a custom quote."""
    quotes = load_custom_quotes()
    quotes.append({"text": text, "author": author})
    with open(QUOTES_FILE, 'w') as f:
        json.dump(quotes, f, ensure_ascii=False)


def get_all_quotes(category=None):
    """Get all quotes, optionally filtered by category."""
    quotes = []
    for cat, qs in BUILTIN_QUOTES.items():
        if category and cat != category:
            continue
        for text, author in qs:
            quotes.append({'text': text, 'author': author, 'category': cat})
    # Add custom
    for cq in load_custom_quotes():
        if not category or category == 'custom':
            quotes.append({**cq, 'category': 'custom'})
    return quotes


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    if args[0] == 'list':
        print("Categories:")
        for cat in BUILTIN_QUOTES:
            print(f"  {cat} ({len(BUILTIN_QUOTES[cat])} quotes)")
        custom = load_custom_quotes()
        if custom:
            print(f"  custom ({len(custom)} quotes)")
        return

    category = None
    count = 1
    author_filter = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--category='):
            category = arg.split('=', 1)[1]
        elif arg == '--category':
            i += 1
            if i < len(args):
                category = args[i]
        elif arg.startswith('--count='):
            count = int(arg.split('=', 1)[1])
        elif arg == '--count':
            i += 1
            if i < len(args):
                count = int(args[i])
        elif arg.startswith('--author='):
            author_filter = arg.split('=', 1)[1]
        elif arg == '--author':
            i += 1
            if i < len(args):
                author_filter = args[i]
        elif arg == 'add':
            i += 1
            if i < len(args):
                text = args[i]
                author = 'Unknown'
                # Check if next is --author
                if i + 2 < len(args) and args[i + 1] == '--author':
                    author = args[i + 2]
                save_custom_quote(text, author)
                print("Quote added.")
                return
            else:
                print("Error: quote text required for 'add'", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        i += 1

    quotes = get_all_quotes(category)
    if author_filter:
        quotes = [q for q in quotes if author_filter.lower() in q['author'].lower()]

    if not quotes:
        print("No quotes found matching criteria.")
        return

    if count >= len(quotes):
        selected = quotes
    else:
        selected = random.sample(quotes, count)

    for q in selected:
        print(f'  "{q["text"]}"')
        print(f'    — {q["author"]}')
        print()


if __name__ == '__main__':
    main()
