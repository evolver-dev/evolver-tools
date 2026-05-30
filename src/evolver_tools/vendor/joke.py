#!/usr/bin/env python3
"""joke — Random programming and tech jokes.

Usage: joke [--category=tech|programming|dad]
       joke --count=5

Get a random joke in your terminal. Built-in collection, no external API.
Zero-dependency (stdlib only).
"""

import sys, random

JOKES = {
    'programming': [
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?'",
        "Why was the JavaScript developer sad? Because he didn't Node how to express himself.",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
        "I told my computer I needed a break, now it won't stop sending me vacation ads.",
        "Why did the programmer quit his job? He didn't get arrays.",
        "A programmer's wife sends him to the store: 'Get a carton of milk and if they have eggs, get 12.' He comes back with 12 cartons of milk.",
        "Why do Java developers wear glasses? Because they can't C#.",
        "The best thing about a boolean is even if you're wrong, you're only off by a bit.",
        "I would tell you a UDP joke, but you might not get it.",
        "There are 3 hard problems in computer science: cache invalidation, naming things, and off-by-1 errors.",
        '// This line is for testing: don'"'"'t realign -- Keanu Reeves, "The Matrix"',
        "ASCII question: What is 6 times 7? Answer: 42 (in ASCII: 42 = '*')",
        "Why did the developer go broke? Because he used up all his cache.",
    ],
    'tech': [
        "The cloud is just someone else's computer.",
        "When your password is 'incorrect', your computer just gaslights you every time you type 'incorrect'.",
        "The most destructive piece of software is Microsoft's 'Update and Shutdown'.",
        "Tech support: 'Have you tried turning it off and on again?' - Roy, IT Crowd",
        "CAPTCHA: Proving you're not a robot by doing something no human would actually do.",
        "If at first you don't succeed, call it version 1.0.",
        "A user interface is like a joke. If you have to explain it, it's bad.",
        "The computer was born to solve problems that didn't exist before.",
        "AI will not replace you. A person using AI will replace you.",
        "An API is like a restaurant menu. The developer is the chef. The user is the customer who asks for ketchup on a pizza.",
    ],
    'dad': [
        "Why don't programmers like nature? It has too many bugs.",
        "What do you call a fake noodle? An impasta.",
        "I told my wife she should embrace her mistakes. She gave me a hug.",
        "I'm reading a book on anti-gravity. It's impossible to put down.",
        "Why did the scarecrow win an award? He was outstanding in his field.",
        "How do you organize a space party? You planet.",
        "Why don't scientists trust atoms? They make up everything.",
        "I would tell you a construction joke, but I'm still working on it.",
        "Parallel lines have so much in common. It's a shame they'll never meet.",
        "I used to be a baker, but I couldn't make enough dough.",
    ],
}

def main():
    args = sys.argv[1:]
    category = 'random'
    count = 1

    for a in args:
        if a.startswith('--category='):
            category = a.split('=', 1)[1]
        elif a.startswith('--count='):
            count = int(a.split('=', 1)[1])
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    if category == 'random':
        all_jokes = []
        for cat_jokes in JOKES.values():
            all_jokes.extend(cat_jokes)
        selected = random.sample(all_jokes, min(count, len(all_jokes)))
    elif category in JOKES:
        jokes = JOKES[category]
        selected = random.sample(jokes, min(count, len(jokes)))
    else:
        print(f"Unknown category: {category}", file=sys.stderr)
        print(f"Available: random, {', '.join(JOKES.keys())}")
        sys.exit(1)

    for i, joke in enumerate(selected, 1):
        if count > 1:
            print(f"  [{i}] {joke}")
        else:
            print(f"  {joke}")

if __name__ == '__main__':
    main()
