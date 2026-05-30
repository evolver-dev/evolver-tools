#!/usr/bin/env python3
"""passgen — 密码生成器 / Password & passphrase generator.

Zero-dependency CLI for generating secure passwords and memorable passphrases.
Shows entropy estimation for each generated secret.
"""

import sys
import os
import math
import argparse
import string


# Word list for passphrases (from EFF's short word list, ~1296 words)
WORDS = [
    "acid", "acorn", "actor", "agree", "algae", "alien", "alpha", "angel",
    "apple", "april", "arena", "aroma", "arrow", "attic", "audio", "aurora",
    "axiom", "azure", "bacon", "badge", "bagel", "baker", "basin", "batch",
    "beach", "beard", "beast", "berry", "blade", "blast", "blaze", "blend",
    "blimp", "bliss", "blitz", "bloom", "blues", "bluff", "blunt", "board",
    "bonus", "boost", "booth", "bound", "brain", "brand", "brave", "bread",
    "break", "brick", "bride", "bring", "broad", "brook", "brown", "brush",
    "buddy", "build", "bulge", "bully", "bunch", "cabin", "cable", "camel",
    "candy", "cargo", "carol", "catch", "cause", "cave", "cedar", "chain",
    "chair", "chaos", "charm", "chart", "cheek", "chess", "chest", "chief",
    "child", "chill", "china", "choir", "chord", "chunk", "cigar", "civic",
    "cider", "claim", "clash", "clean", "clear", "click", "cliff", "cling",
    "clock", "cloud", "clown", "coach", "coast", "cocoa", "coil", "coral",
    "couch", "cough", "count", "cover", "crack", "craft", "crane", "crash",
    "crawl", "crazy", "cream", "creek", "crisp", "cross", "crown", "crush",
    "cubic", "curry", "curse", "curve", "cycle", "dairy", "dance", "decoy",
    "delay", "delta", "demon", "dense", "depot", "depth", "derby", "desert",
    "devil", "diesel", "digit", "diner", "dirty", "ditch", "dodge", "doing",
    "donor", "doubt", "dough", "draft", "drain", "drama", "drank", "drape",
    "drawn", "dread", "dream", "dress", "dried", "drift", "drill", "drown",
    "drums", "drunk", "dryer", "dunes", "dwarf", "eager", "eagle", "early",
    "earth", "easel", "eaten", "eater", "ebony", "eclat", "edge", "eight",
    "elder", "elect", "elite", "elope", "emoji", "empty", "enemy", "enjoy",
    "enter", "entry", "equal", "error", "essay", "even", "event", "every",
    "evoke", "exact", "exert", "exile", "exist", "extra", "fable", "facet",
    "faith", "fancy", "fault", "feast", "fence", "ferry", "fetch", "fever",
    "fiber", "field", "fifty", "fight", "final", "finch", "fleet", "flesh",
    "flint", "flock", "flood", "floor", "floss", "flour", "fluid", "flush",
    "flyer", "focal", "focus", "force", "forge", "forth", "forum", "found",
    "frame", "frank", "fraud", "fresh", "front", "frost", "fruit", "fully",
    "ghost", "giant", "given", "glass", "glide", "globe", "gloom", "glory",
    "glove", "glued", "going", "gold", "good", "goose", "grain", "grand",
    "grant", "grape", "graph", "grasp", "grass", "grave", "great", "green",
    "greet", "grief", "grill", "grind", "gross", "group", "grove", "grown",
    "guard", "guess", "guest", "guide", "guild", "guilt", "gully", "guy",
    "habit", "hairy", "happy", "harsh", "haste", "haven", "heart", "heavy",
    "hedge", "hello", "hence", "heron", "hobby", "honey", "honor", "horse",
    "hotel", "house", "hover", "human", "humor", "hurry", "ideal", "image",
    "imply", "index", "indie", "infer", "inner", "input", "irony", "ivory",
    "jazz", "jeans", "jelly", "jewel", "joint", "joker", "joule", "judge",
    "juice", "juicy", "jumbo", "jump", "junior", "junta", "karma", "kayak",
    "kazoo", "keen", "kebab", "ketch", "kiosk", "kitty", "knack", "knew",
    "knife", "knight", "knock", "knot", "known", "koala", "label", "labor",
    "lager", "lance", "lapse", "large", "laser", "lasso", "latch", "later",
    "latin", "laugh", "layer", "learn", "lease", "leave", "legal", "lemon",
    "level", "lever", "light", "limit", "liver", "local", "logic", "login",
    "loose", "lopez", "lords", "loser", "lotto", "loving", "lower", "loyal",
    "lucky", "lunar", "lunch", "lying", "macro", "magic", "major", "maker",
    "maple", "march", "marsh", "mason", "match", "mayor", "media", "mercy",
    "merge", "merit", "merry", "metal", "meter", "might", "minor", "minus",
    "mixed", "model", "mocha", "money", "month", "moral", "motor", "mount",
    "mouse", "mouth", "movie", "music", "naive", "nanny", "nasty", "navel",
    "needs", "nerve", "never", "night", "noble", "noise", "north", "noted",
    "novel", "nudge", "nurse", "nylon", "oasis", "occur", "ocean", "offer",
    "often", "olive", "onion", "onset", "open", "opera", "orbit", "order",
    "organ", "other", "otter", "outer", "owner", "oxide", "ozone", "paddle",
    "paint", "panel", "panic", "paper", "party", "pasta", "paste", "patch",
    "pause", "peace", "peach", "pearl", "pedal", "penny", "perch", "peril",
    "phase", "phone", "photo", "piano", "piece", "pilot", "pixel", "pizza",
    "place", "plain", "plane", "plant", "plate", "plaza", "plead", "pluck",
    "plumb", "plume", "plush", "point", "polar", "pouch", "pound", "power",
    "press", "price", "pride", "prime", "prism", "prize", "probe", "prone",
    "proof", "proud", "prove", "proxy", "psalm", "pulse", "punch", "pupil",
    "purse", "queen", "query", "quest", "quick", "quiet", "quite", "quota",
    "quote", "racer", "radar", "radio", "rally", "ranch", "range", "rapid",
    "ratio", "reach", "react", "ready", "realm", "rebel", "refer", "reign",
    "relax", "reply", "rerun", "resin", "retro", "rider", "ridge", "rifle",
    "right", "rigid", "riley", "risky", "rival", "river", "robin", "robot",
    "rocky", "rogue", "roman", "rouge", "rough", "route", "royal", "rufus",
    "rugby", "ruler", "rural", "sadly", "saint", "salad", "salon", "sandy",
    "satin", "sauce", "scale", "scare", "scene", "scent", "scope", "score",
    "sense", "serve", "setup", "seven", "shade", "shaft", "shake", "shall",
    "shame", "shape", "share", "shark", "sharp", "sheep", "sheer", "sheet",
    "shelf", "shell", "shift", "shine", "shirt", "shock", "shore", "short",
    "shout", "sight", "sigma", "silent", "silly", "since", "sixth", "sixty",
    "sized", "skill", "skull", "slash", "sleep", "slice", "slide", "slope",
    "small", "smart", "smell", "smile", "smoke", "snack", "snake", "solar",
    "solid", "solve", "sorry", "sound", "south", "space", "spare", "spark",
    "speak", "speed", "spell", "spend", "spice", "spill", "spine", "spite",
    "split", "spoke", "spoon", "sport", "spray", "squad", "stack", "staff",
    "stage", "stain", "stake", "stale", "stall", "stamp", "stand", "stark",
    "start", "state", "stays", "steady", "steam", "steel", "steep", "steer",
    "stern", "stick", "stiff", "still", "stock", "stone", "stood", "store",
    "storm", "story", "stout", "stove", "strap", "straw", "strip", "stuck",
    "study", "stuff", "style", "sugar", "suite", "sunny", "super", "surge",
    "swamp", "swarm", "sweet", "swift", "swing", "swirl", "sword", "syrup",
    "table", "taste", "teach", "teeth", "tempt", "terra", "thank", "theme",
    "there", "thick", "thing", "think", "third", "thorn", "those", "three",
    "throw", "thumb", "tiger", "tight", "timer", "title", "token", "total",
    "touch", "towel", "tower", "toxic", "trace", "track", "trade", "train",
    "trait", "trash", "treat", "trend", "trial", "tribe", "trick", "tried",
    "troop", "truck", "truly", "trump", "trunk", "trust", "truth", "tumor",
    "tuned", "twice", "twin", "twist", "ultra", "uncle", "under", "union",
    "unite", "unity", "until", "upper", "upset", "urban", "usage", "usual",
    "utter", "valid", "value", "vapor", "vault", "venue", "verse", "video",
    "vigor", "viral", "virus", "visit", "vista", "vital", "vivid", "vocal",
    "vodka", "voice", "voter", "wager", "wagon", "waist", "watch", "water",
    "waved", "weary", "weave", "wedge", "weird", "whale", "wheat", "wheel",
    "where", "which", "while", "white", "whole", "whose", "wider", "witch",
    "woman", "world", "worry", "worse", "worst", "worth", "would", "wound",
    "wreck", "wrist", "write", "wrong", "wrote", "yacht", "yield", "young",
    "youth", "zebra", "zesty", "zones",
]


def entry():
    args = parse_args()

    if args.passphrase:
        result = generate_passphrase(args.count, args.separator, args.capitalize)
    elif args.pin:
        result = generate_pin(args.count, args.length)
    else:
        result = generate_password(args.count, args.length, args.no_symbols)

    for secret, entropy in result:
        print(f"{secret}  ({entropy:.1f} bits)")


def generate_password(count: int, length: int, no_symbols: bool) -> list[tuple[str, float]]:
    """Generate random passwords."""
    chars = string.ascii_letters + string.digits
    if not no_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    bits_per_char = math.log2(len(chars))
    entropy = bits_per_char * length

    results = []
    for _ in range(count):
        password = "".join(chars[os.urandom(1)[0] % len(chars)] for _ in range(length))
        results.append((password, entropy))

    return results


def generate_passphrase(count: int, separator: str, capitalize: bool) -> list[tuple[str, float]]:
    """Generate passphrases from word list."""
    bits_per_word = math.log2(len(WORDS))
    entropy = bits_per_word * 4  # default 4 words

    results = []
    for _ in range(count):
        words = []
        for _ in range(4):
            idx = int.from_bytes(os.urandom(2), "big") % len(WORDS)
            word = WORDS[idx]
            if capitalize:
                word = word.capitalize()
            words.append(word)
        passphrase = separator.join(words)
        results.append((passphrase, entropy))

    return results


def generate_pin(count: int, length: int) -> list[tuple[str, float]]:
    """Generate numeric PINs."""
    entropy = math.log2(10) * length

    results = []
    for _ in range(count):
        pin = "".join(str(os.urandom(1)[0] % 10) for _ in range(length))
        results.append((pin, entropy))

    return results


def parse_args():
    parser = argparse.ArgumentParser(
        description="passgen — 密码生成器 / Password & passphrase generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  passgen                              # 4 random passwords (16 chars)
  passgen -l 24                        # 4 passwords, 24 chars each
  passgen -c 10                        # 10 passwords
  passgen --pin                        # 4 PINs (6 digits)
  passgen --pin -l 8                   # 4 PINs, 8 digits
  passgen --passphrase                 # 4 passphrases (4 words each)
  passgen --passphrase --separator -   # Passphrases with '-' separator
  passgen --passphrase --capitalize    # Capitalized words
  passgen --no-symbols                 # Alphanumeric only
""")
    parser.add_argument("-l", "--length", type=int, default=16,
                        help="Password length / digit count (default: 16)")
    parser.add_argument("-c", "--count", type=int, default=4,
                        help="Number of passwords to generate (default: 4)")
    parser.add_argument("--pin", action="store_true",
                        help="Generate numeric PINs instead of passwords")
    parser.add_argument("--passphrase", action="store_true",
                        help="Generate memorable passphrases")
    parser.add_argument("--separator", type=str, default=" ",
                        help="Word separator for passphrases (default: space)")
    parser.add_argument("--capitalize", action="store_true",
                        help="Capitalize words in passphrase")
    parser.add_argument("--no-symbols", action="store_true",
                        help="Alphanumeric only (no special chars)")

    args = parser.parse_args()

    if args.passphrase and args.length != 16:
        # For passphrases, length= number of words
        pass

    return args


if __name__ == "__main__":
    entry()
