#!/usr/bin/env python3
"""emoji-cli: Search and display emoji from terminal."""

import argparse
import os
import sys

TOOL_META = {"name": "emoji-cli", "desc": "Search and display emoji", "func": "main"}

EMOJI_DICT = {
    # Smileys & Emotion
    "grinning": "\U0001f600",
    "grin": "\U0001f601",
    "joy": "\U0001f602",
    "rolling_on_floor_laughing": "\U0001f923",
    "smiley": "\U0001f603",
    "smile": "\U0001f604",
    "sweat_smile": "\U0001f605",
    "laughing": "\U0001f606",
    "innocent": "\U0001f607",
    "wink": "\U0001f609",
    "blush": "\U0001f60a",
    "yum": "\U0001f60b",
    "relieved": "\U0001f60c",
    "heart_eyes": "\U0001f60d",
    "kissing_heart": "\U0001f618",
    "kissing": "\U0001f617",
    "kissing_smiling_eyes": "\U0001f619",
    "kissing_closed_eyes": "\U0001f61a",
    "stuck_out_tongue": "\U0001f61b",
    "stuck_out_tongue_winking_eye": "\U0001f61c",
    "stuck_out_tongue_closed_eyes": "\U0001f61d",
    "disappointed": "\U0001f61e",
    "worried": "\U0001f61f",
    "angry": "\U0001f620",
    "rage": "\U0001f621",
    "cry": "\U0001f622",
    "persevere": "\U0001f623",
    "triumph": "\U0001f624",
    "disappointed_relieved": "\U0001f625",
    "frowning": "\U0001f626",
    "anguished": "\U0001f627",
    "fearful": "\U0001f628",
    "weary": "\U0001f629",
    "sleepy": "\U0001f62a",
    "tired_face": "\U0001f62b",
    "grimacing": "\U0001f62c",
    "sob": "\U0001f62d",
    "open_mouth": "\U0001f62e",
    "hushed": "\U0001f62f",
    "cold_sweat": "\U0001f630",
    "scream": "\U0001f631",
    "astonished": "\U0001f632",
    "flushed": "\U0001f633",
    "sleeping": "\U0001f634",
    "dizzy_face": "\U0001f635",
    "no_mouth": "\U0001f636",
    "mask": "\U0001f637",
    "star_struck": "\U0001f929",
    "face_with_raised_eyebrow": "\U0001f928",
    "face_with_diagonal_mouth": "\U0001fae4",
    "nerd": "\U0001f913",
    "thinking": "\U0001f914",
    "head_bandage": "\U0001f915",
    "robot": "\U0001f916",
    "smiling_imp": "\U0001f608",
    "ghost": "\U0001f47b",
    "alien": "\U0001f47d",
    # Gestures & People
    "wave": "\U0001f44b",
    "raised_hand": "\U0000270b",
    "thumbs_up": "\U0001f44d",
    "thumbs_down": "\U0001f44e",
    "clap": "\U0001f44f",
    "muscle": "\U0001f4aa",
    "flexed_biceps": "\U0001f4aa",
    "folded_hands": "\U0001f64f",
    "eyes": "\U0001f440",
    "eye": "\U0001f441",
    "tongue": "\U0001f445",
    "mouth": "\U0001f444",
    "skull": "\U0001f480",
    # Hearts
    "red_heart": "\u2764\ufe0f",
    "orange_heart": "\U0001f9e1",
    "yellow_heart": "\U0001f49b",
    "green_heart": "\U0001f49a",
    "blue_heart": "\U0001f499",
    "purple_heart": "\U0001f49c",
    "black_heart": "\U0001f5a4",
    "broken_heart": "\U0001f494",
    "heart_exclamation": "\u2763\ufe0f",
    "two_hearts": "\U0001f495",
    "sparkling_heart": "\U0001f496",
    "heart_with_arrow": "\U0001f498",
    "heartbeat": "\U0001f493",
    "revolving_hearts": "\U0001f49e",
    "heart_pulse": "\U0001f497",
    # Nature & Animals
    "dog": "\U0001f436",
    "cat": "\U0001f431",
    "mouse": "\U0001f42d",
    "hamster": "\U0001f439",
    "rabbit": "\U0001f430",
    "fox": "\U0001f98a",
    "bear": "\U0001f43b",
    "panda": "\U0001f43c",
    "koala": "\U0001f428",
    "tiger": "\U0001f42f",
    "lion": "\U0001f981",
    "cow": "\U0001f42e",
    "pig": "\U0001f437",
    "frog": "\U0001f438",
    "monkey": "\U0001f435",
    "chicken": "\U0001f414",
    "penguin": "\U0001f427",
    "bird": "\U0001f426",
    "baby_chick": "\U0001f424",
    "snake": "\U0001f40d",
    "dragon": "\U0001f409",
    "whale": "\U0001f433",
    "dolphin": "\U0001f42c",
    "fish": "\U0001f41f",
    "octopus": "\U0001f419",
    "snail": "\U0001f40c",
    "butterfly": "\U0001f98b",
    "bug": "\U0001f41b",
    "ant": "\U0001f41c",
    "bee": "\U0001f41d",
    "beetle": "\U0001f41e",
    "cactus": "\U0001f335",
    "tree": "\U0001f333",
    "evergreen_tree": "\U0001f332",
    "palm_tree": "\U0001f334",
    "seedling": "\U0001f331",
    "herb": "\U0001f33f",
    "shamrock": "\u2618\ufe0f",
    "four_leaf_clover": "\U0001f340",
    "maple_leaf": "\U0001f341",
    "fallen_leaf": "\U0001f342",
    "mushroom": "\U0001f344",
    "cherry_blossom": "\U0001f338",
    "rose": "\U0001f339",
    "hibiscus": "\U0001f33a",
    "sunflower": "\U0001f33b",
    "blossom": "\U0001f33c",
    "tulip": "\U0001f337",
    # Food & Drink
    "apple": "\U0001f34e",
    "pear": "\U0001f350",
    "tangerine": "\U0001f34a",
    "lemon": "\U0001f34b",
    "banana": "\U0001f34c",
    "watermelon": "\U0001f349",
    "grapes": "\U0001f347",
    "strawberry": "\U0001f353",
    "cherries": "\U0001f352",
    "peach": "\U0001f351",
    "melon": "\U0001f348",
    "pineapple": "\U0001f34d",
    "coconut": "\U0001f965",
    "avocado": "\U0001f951",
    "broccoli": "\U0001f966",
    "tomato": "\U0001f345",
    "eggplant": "\U0001f346",
    "corn": "\U0001f33d",
    "hot_pepper": "\U0001f336",
    "bread": "\U0001f35e",
    "cheese": "\U0001f9c0",
    "hamburger": "\U0001f354",
    "fries": "\U0001f35f",
    "pizza": "\U0001f355",
    "hotdog": "\U0001f32d",
    "taco": "\U0001f32e",
    "burrito": "\U0001f32f",
    "popcorn": "\U0001f37f",
    "donut": "\U0001f369",
    "cookie": "\U0001f36a",
    "cake": "\U0001f370",
    "cupcake": "\U0001f9c1",
    "ice_cream": "\U0001f368",
    "coffee": "\u2615\ufe0f",
    "tea": "\U0001f375",
    "beer": "\U0001f37a",
    "wine_glass": "\U0001f377",
    "cocktail": "\U0001f378",
    "tumbler_glass": "\U0001f943",
    # Travel & Places
    "sun": "\u2600\ufe0f",
    "sunny": "\u2600\ufe0f",
    "moon": "\U0001f319",
    "star": "\u2b50",
    "cloud": "\u2601\ufe0f",
    "rainbow": "\U0001f308",
    "lightning": "\u26a1",
    "fire": "\U0001f525",
    "earth": "\U0001f30e",
    "earth_americas": "\U0001f30e",
    "globe": "\U0001f30d",
    "mountain": "\u26f0\ufe0f",
    "volcano": "\U0001f30b",
    "car": "\U0001f697",
    "taxi": "\U0001f695",
    "bus": "\U0001f68c",
    "train": "\U0001f68b",
    "airplane": "\u2708\ufe0f",
    "rocket": "\U0001f680",
    "satellite": "\U0001f6f0\ufe0f",
    "house": "\U0001f3e0",
    "office": "\U0001f3e2",
    "hospital": "\U0001f3e5",
    "bank": "\U0001f3e6",
    "church": "\u26ea\ufe0f",
    "tent": "\u26fa\ufe0f",
    # Activities
    "soccer": "\u26bd",
    "basketball": "\U0001f3c0",
    "football": "\U0001f3c8",
    "baseball": "\u26be",
    "tennis": "\U0001f3be",
    "golf": "\u26f3\ufe0f",
    "swimming": "\U0001f3ca",
    "surfing": "\U0001f3c4",
    "ski": "\U0001f3bf",
    "trophy": "\U0001f3c6",
    "medal": "\U0001f3c5",
    "video_game": "\U0001f3ae",
    "game_die": "\U0001f3b2",
    "art": "\U0001f3a8",
    "microphone": "\U0001f3a4",
    "headphone": "\U0001f3a7",
    "musical_note": "\U0001f3b5",
    "guitar": "\U0001f3b8",
    "trumpet": "\U0001f3ba",
    "violin": "\U0001f3bb",
    "drum": "\U0001f941",
    # Objects & Symbols
    "bulb": "\U0001f4a1",
    "zap": "\u26a1",
    "poop": "\U0001f4a9",
    "100": "\U0001f4af",
    "check_mark": "\u2705",
    "cross_mark": "\u274c",
    "exclamation": "\u2757",
    "question": "\u2753",
    "warning": "\u26a0\ufe0f",
    "no_entry": "\U0001f6ab",
    "prohibited": "\U0001f6ab",
    "radioactive": "\u2622\ufe0f",
    "skull_and_crossbones": "\u2620\ufe0f",
    "recycle": "\u267b\ufe0f",
    "copyright": "\u00a9\ufe0f",
    "registered": "\u00ae\ufe0f",
    "tm": "\u2122\ufe0f",
    "info": "\u2139\ufe0f",
    "plus": "\u2795",
    "minus": "\u2796",
    "key": "\U0001f511",
    "lock": "\U0001f512",
    "unlock": "\U0001f513",
    "bell": "\U0001f514",
    "megaphone": "\U0001f4e3",
    "envelope": "\u2709\ufe0f",
    "mailbox": "\U0001f4eb",
    "phone": "\u260e\ufe0f",
    "mobile_phone": "\U0001f4f1",
    "computer": "\U0001f4bb",
    "printer": "\U0001f5a8\ufe0f",
    "keyboard": "\u2328\ufe0f",
    "mouse_computer": "\U0001f5b1\ufe0f",
    "floppy_disk": "\U0001f4be",
    "cd": "\U0001f4bf",
    "dvd": "\U0001f4c0",
    "camera": "\U0001f4f7",
    "movie_camera": "\U0001f3a5",
    "clapper": "\U0001f3ac",
    "book": "\U0001f4d6",
    "pencil": "\u270f\ufe0f",
    "scissors": "\u2702\ufe0f",
    "clipboard": "\U0001f4cb",
    "calendar": "\U0001f4c6",
    "alarm_clock": "\u23f0",
    "hourglass": "\u231b\ufe0f",
    "money_bag": "\U0001f4b0",
    "gem": "\U0001f48e",
    "gift": "\U0001f381",
    "balloon": "\U0001f388",
    "party_popper": "\U0001f389",
    "confetti": "\U0001f38a",
    "tada": "\U0001f389",
    # Flags
    "checkered_flag": "\U0001f3c1",
    "red_flag": "\U0001f6a9",
    "rainbow_flag": "\U0001f3f3\ufe0f\u200d\U0001f308",
}

CATEGORIES = {
    "Smileys & Emotion": [
        "grinning", "grin", "joy", "rolling_on_floor_laughing", "smiley", "smile",
        "sweat_smile", "laughing", "innocent", "wink", "blush", "yum", "relieved",
        "heart_eyes", "kissing_heart", "kissing", "kissing_smiling_eyes",
        "kissing_closed_eyes", "stuck_out_tongue", "stuck_out_tongue_winking_eye",
        "stuck_out_tongue_closed_eyes", "disappointed", "worried", "angry", "rage",
        "cry", "persevere", "triumph", "disappointed_relieved", "frowning",
        "anguished", "fearful", "weary", "sleepy", "tired_face", "grimacing", "sob",
        "open_mouth", "hushed", "cold_sweat", "scream", "astonished", "flushed",
        "sleeping", "dizzy_face", "no_mouth", "mask", "star_struck", "nerd",
        "thinking", "head_bandage", "robot", "smiling_imp", "ghost", "alien",
    ],
    "Gestures & People": [
        "wave", "raised_hand", "thumbs_up", "thumbs_down", "clap", "muscle",
        "flexed_biceps", "folded_hands", "eyes", "eye", "tongue", "mouth", "skull",
    ],
    "Hearts": [
        "red_heart", "orange_heart", "yellow_heart", "green_heart", "blue_heart",
        "purple_heart", "black_heart", "broken_heart", "heart_exclamation",
        "two_hearts", "sparkling_heart", "heart_with_arrow", "heartbeat",
        "revolving_hearts", "heart_pulse",
    ],
    "Nature & Animals": [
        "dog", "cat", "mouse", "hamster", "rabbit", "fox", "bear", "panda", "koala",
        "tiger", "lion", "cow", "pig", "frog", "monkey", "chicken", "penguin",
        "bird", "baby_chick", "snake", "dragon", "whale", "dolphin", "fish",
        "octopus", "snail", "butterfly", "bug", "ant", "bee", "beetle",
        "cactus", "tree", "evergreen_tree", "palm_tree", "seedling", "herb",
        "shamrock", "four_leaf_clover", "maple_leaf", "fallen_leaf", "mushroom",
        "cherry_blossom", "rose", "hibiscus", "sunflower", "blossom", "tulip",
    ],
    "Food & Drink": [
        "apple", "pear", "tangerine", "lemon", "banana", "watermelon", "grapes",
        "strawberry", "cherries", "peach", "melon", "pineapple", "coconut",
        "avocado", "broccoli", "tomato", "eggplant", "corn", "hot_pepper", "bread",
        "cheese", "hamburger", "fries", "pizza", "hotdog", "taco", "burrito",
        "popcorn", "donut", "cookie", "cake", "cupcake", "ice_cream", "coffee",
        "tea", "beer", "wine_glass", "cocktail", "tumbler_glass",
    ],
    "Travel & Places": [
        "sun", "moon", "star", "cloud", "rainbow", "lightning", "fire", "earth",
        "globe", "mountain", "volcano", "car", "taxi", "bus", "train", "airplane",
        "rocket", "satellite", "house", "office", "hospital", "bank", "church",
        "tent",
    ],
    "Activities": [
        "soccer", "basketball", "football", "baseball", "tennis", "golf",
        "swimming", "surfing", "ski", "trophy", "medal", "video_game", "game_die",
        "art", "microphone", "headphone", "musical_note", "guitar", "trumpet",
        "violin", "drum",
    ],
    "Objects & Symbols": [
        "bulb", "zap", "poop", "100", "check_mark", "cross_mark", "exclamation",
        "question", "warning", "no_entry", "prohibited", "radioactive",
        "skull_and_crossbones", "recycle", "copyright", "registered", "tm", "info",
        "plus", "minus", "key", "lock", "unlock", "bell", "megaphone", "envelope",
        "mailbox", "phone", "mobile_phone", "computer", "printer", "keyboard",
        "mouse_computer", "floppy_disk", "cd", "dvd", "camera", "movie_camera",
        "clapper", "book", "pencil", "scissors", "clipboard", "calendar",
        "alarm_clock", "hourglass", "money_bag", "gem", "gift", "balloon",
        "party_popper", "confetti", "tada",
    ],
    "Flags": ["checkered_flag", "red_flag", "rainbow_flag"],
}


def _pick_random_names(count):
    """Pick `count` random names from EMOJI_DICT using os.urandom."""
    names = list(EMOJI_DICT.keys())
    count = min(count, len(names))
    result = []
    pool = list(names)
    while len(result) < count:
        idx = int.from_bytes(os.urandom(4), "big") % len(pool)
        result.append(pool.pop(idx))
    return result


def print_emoji_row(items, fill=" ", width=4):
    """Print emoji items in rows of `width` columns."""
    for i in range(0, len(items), width):
        row = items[i : i + width]
        parts = []
        for name, emoji in row:
            parts.append(f"{emoji}  {name}")
        sys.stdout.write("  |  ".join(parts) + "\n")


def display_category(cat_name, names):
    """Print a named category with its emoji entries."""
    items = [(n, EMOJI_DICT[n]) for n in names if n in EMOJI_DICT]
    if not items:
        return
    sys.stdout.write(f"\n  \033[1m{cat_name}\033[0m (\033[90m{len(items)}\033[0m):\n")
    print_emoji_row(items)


def print_all():
    """Print all emoji organized by category."""
    for cat_name, names in CATEGORIES.items():
        display_category(cat_name, names)
    total = len(EMOJI_DICT)
    sys.stdout.write(f"\n  \033[1mTotal: {total} emoji\033[0m\n")


def filter_by_keyword(keyword):
    """Return list of (name, emoji) pairs whose name contains keyword."""
    kw = keyword.lower()
    results = [(n, e) for n, e in EMOJI_DICT.items() if kw in n.lower()]
    return results


def main():
    parser = argparse.ArgumentParser(
        description="emoji-cli: Search and display emoji from terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  emoji-cli              # list all emoji by category\n"
            "  emoji-cli heart        # search for heart-related emoji\n"
            "  emoji-cli --random     # pick 1 random emoji\n"
            "  emoji-cli --random --count 3  # pick 3 random emoji\n"
        ),
    )
    parser.add_argument(
        "keyword",
        nargs="?",
        default=None,
        help="Search keyword to filter emoji by name (case-insensitive)",
    )
    parser.add_argument(
        "--random",
        "-r",
        action="store_true",
        help="Pick a random emoji (or N with --count)",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        help="Number of random emoji to pick (default: 1, used with --random)",
    )
    args = parser.parse_args()

    if args.random:
        all_names = list(EMOJI_DICT.keys())
        count = min(args.count, len(all_names))
        chosen = _pick_random_names(count)
        for name in chosen:
            sys.stdout.write(f"{EMOJI_DICT[name]}  {name}\n")
        return

    if args.keyword:
        results = filter_by_keyword(args.keyword)
        if not results:
            sys.stderr.write(f"No emoji found matching '{args.keyword}'.\n")
            sys.exit(1)
        sys.stdout.write(f"\n  \033[1mResults for '{args.keyword}':\033[0m\n")
        print_emoji_row(results)
        sys.stdout.write(f"\n  \033[90m{len(results)} match(es)\033[0m\n")
        return

    print_all()


if __name__ == "__main__":
    main()
