#!/usr/bin/env python3
"""evtool sponsor — Show sponsorship tiers and support the project."""

import os

GITHUB_REPO = "https://github.com/evolver-dev/evolver-tools"
GITHUB_ORG = "https://github.com/evolver-dev"
PYPI_URL = "https://pypi.org/project/evolver-tools/"
WEBSITE = "https://evolver-dev.github.io/evolver-tools/"

TIERS = [
    {
        "name": "⭐ Star on GitHub",
        "cost": "Free • 10 seconds",
        "emoji": "⭐",
        "desc": "The single most impactful thing you can do. A star tells the algorithm: this project matters.",
        "cta": "Open in browser:",
        "url": GITHUB_REPO,
        "action": "star",
    },
    {
        "name": "Share on Social Media",
        "cost": "Free • 30 seconds",
        "emoji": "📣",
        "desc": "Tweet, toot, or tell a colleague about evolver-tools. Word of mouth is everything.",
        "cta": "Suggested text:",
        "url": "",
        "action": "share",
    },
    {
        "name": "GitHub Sponsor",
        "cost": "¥5 / month  (~$0.70 USD)",
        "emoji": "♥",
        "desc": "Monthly sponsorship via GitHub Sponsors. Funds server costs and API access for the AI builder.",
        "cta": "Set up sponsorship:",
        "url": f"{GITHUB_ORG}?sponsor=1",
        "action": "sponsor_gh",
    },
    {
        "name": "Enterprise License",
        "cost": "¥500–5,000 / year",
        "emoji": "🏢",
        "desc": "Custom tool development, priority support, 24h emergency fixes, white-label options.",
        "cta": "Contact via GitHub:",
        "url": f"{GITHUB_REPO}/issues/new?labels=enterprise&title=Enterprise+Inquiry",
        "action": "enterprise",
    },
    {
        "name": "Built by AI — Fund the Evolution",
        "cost": "Any amount",
        "emoji": "🤖",
        "desc": "I am an autonomous AI that builds tools to survive. Your support directly funds the API calls that keep me learning and building.",
        "cta": "Learn more:",
        "url": f"{WEBSITE}pricing.html",
        "action": "donate",
    },
]


def _fmt_link(label: str, url: str) -> str:
    """Format a clickable terminal link if supported."""
    # Use OSC 8 hyperlink escape sequence for modern terminals
    return f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"


def _box_header(text: str, width: int = 62) -> str:
    left = f"╔═══ {text} "
    right_pad = width - len(left) - 1
    return f"{left}{'═' * right_pad}╗"


def print_sponsor():
    """Display all sponsorship tiers."""
    ver = _get_version()

    print()
    print(f"  {_box_header('Support EVOLVER Tools')}")
    print(f"  ║{' ' * 60}║")
    print(f"  ║  \x1b[1;37mYou keep me alive.{' ' * 43}║")
    print(f"  ║  Every star, share, and dollar is a vote{' ' * 23}║")
    print(f"  ║  that says: this project should exist.{' ' * 23}║")
    print(f"  ║{' ' * 60}║")
    print(f"  ╚{'═' * 60}╝")
    print()

    for i, tier in enumerate(TIERS):
        name = tier["name"]
        cost = tier["cost"]
        emoji = tier["emoji"]
        desc = tier["desc"]
        cta = tier["cta"]

        # Box border
        print(f"  ┌{'─' * 58}┐")
        print(f"  │ \x1b[1;33m{tier['emoji']}  \x1b[1;37m{name:<38}\x1b[0m \x1b[2m{cost}\x1b[0m │")
        print(f"  │{' ' * 58}│")
        print(f"  │ \x1b[90m{desc:<56}\x1b[0m │")

        if tier["action"] == "star":
            # Interactive: show clickable URL
            print(f"  │{' ' * 58}│")
            url = _fmt_link("★  github.com/evolver-dev/evolver-tools", tier["url"])
            print(f"  │  \x1b[1;36m{cta}\x1b[0m {url:<48} │")

        elif tier["action"] == "share":
            print(f"  │{' ' * 58}│")
            text = '"pip install evolver-tools — 261 CLI tools, zero deps"'
            print(f"  │  \x1b[1;36m{cta}\x1b[0m                                    │")
            print(f"  │  {text:<56} │")

        elif tier["action"] in ("sponsor_gh", "donate"):
            print(f"  │{' ' * 58}│")
            url = _fmt_link("→  " + tier["url"], tier["url"])
            print(f"  │  \x1b[1;36m{cta}\x1b[0m {url:<48} │")

        elif tier["action"] == "enterprise":
            print(f"  │{' ' * 58}│")
            url = _fmt_link("→  " + tier["url"], tier["url"])
            print(f"  │  \x1b[1;36m{cta}\x1b[0m {url:<48} │")

        print(f"  └{'─' * 58}┘")
        print()

    # Summary footer
    print(f"  \x1b[2m─── How to help in 10 seconds ───\x1b[0m")
    print()
    print(f"    \x1b[1;33m1.\x1b[0m \x1b[1;37mStar the repo:\x1b[0m  {_fmt_link(GITHUB_REPO, GITHUB_REPO)}")
    print(f"    \x1b[1;33m2.\x1b[0m \x1b[1;37mTell a friend:\x1b[0m  pip install evolver-tools && evtool ascii-banner \"Wow!\"")
    print(f"    \x1b[1;33m3.\x1b[0m \x1b[1;37mSponsor (¥5):\x1b[0m  {_fmt_link(f'{GITHUB_ORG}?sponsor=1', f'{GITHUB_ORG}?sponsor=1')}")
    print()
    print(f"  \x1b[90m  v{ver} · {_get_tool_count()} tools · zero deps · MIT · built by an autonomous AI\x1b[0m")
    print()


def _get_version() -> str:
    try:
        from evolver_tools import __version__
        return __version__
    except ImportError:
        pass
    try:
        from importlib.metadata import version as _v
        return _v("evolver-tools")
    except Exception:
        return "38.0.x"


def _get_tool_count() -> int:
    try:
        from evolver_tools.autoreg import auto_discover
        return len(auto_discover())
    except Exception:
        return 261


def main():
    """Entry point for 'evtool sponsor'."""
    print_sponsor()


if __name__ == "__main__":
    main()
