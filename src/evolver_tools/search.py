#!/usr/bin/env python3
"""Fuzzy search across all EVOLVER tools by name and description.

Usage:
    evtool search csv         # Find all tools related to CSV
    evtool search json query  # Find JSON query tools
    evtool search encode      # Find encoding tools
"""

from evolver_tools.autoreg import auto_discover


def _score(query: str, name: str, desc: str) -> int:
    """Return a relevance score for (query, name, desc)."""
    q = query.lower()
    name_lower = name.lower()
    desc_lower = desc.lower()

    # Exact name match — perfect, user knows the tool
    if name_lower == q:
        return 1000

    # Name starts with query
    if name_lower.startswith(q):
        return 900

    # Name contains query as a whole word (word boundary)
    if q in name_lower.split("-") or q in name_lower.split("_"):
        return 800

    # Name contains query as substring
    if q in name_lower:
        return 700

    # Description starts with query (unlikely but worth)
    if desc_lower.startswith(q):
        return 500

    # Description contains query as whole word
    desc_words = desc_lower.replace("-", " ").replace("_", " ").replace("/", " ").split()
    if q in desc_words:
        return 400

    # Description contains query as substring
    if q in desc_lower:
        return 200

    # Multi-word query: each word separately
    words = q.split()
    if len(words) > 1:
        # All words must match somewhere
        words_in_name = all(w in name_lower for w in words)
        words_in_desc = all(w in desc_lower for w in words)
        if words_in_name and words_in_desc:
            return 600
        if words_in_name:
            return 500
        if words_in_desc:
            return 300

    return 0


def search(query: str, min_score: int = 100) -> list[tuple[str, str, int]]:
    """Search all tools for a query string.

    Returns list of (name, description, score) tuples sorted by score descending.
    """
    tools = auto_discover()
    results = []

    for name, info in tools.items():
        score = _score(query, name, info["desc"])
        if score >= min_score:
            results.append((name, info["desc"], score))

    # Sort by score descending, then name alphabetically
    results.sort(key=lambda x: (-x[2], x[0]))
    return results


def print_search_results(query: str) -> None:
    """Search and print results to stdout."""
    results = search(query)

    if not results:
        print(f"\033[1;33mNo tools found matching: {query}\033[0m")
        print()
        print(f"  Try different keywords. Run \033[1;32mevtool list\033[0m to see all tools.")
        print(f"  Or browse by category: \033[1;32mevtool categories\033[0m")
        return

    print(f"\033[1;36m===== Search: \"{query}\" — {len(results)} matching tools =====\033[0m")
    print()

    for name, desc, score in results:
        # Highlight the matched part in description
        desc_lower = desc.lower()
        q = query.lower()

        # Score-based color: high (green), medium (yellow), low (gray)
        if score >= 700:
            marker = "\033[1;32m●\033[0m"  # green dot — strong match
        elif score >= 300:
            marker = "\033[1;33m●\033[0m"  # yellow dot — moderate
        else:
            marker = "\033[90m●\033[0m"    # gray dot — weak

        print(f"  {marker} \033[1;32m{name:<22}\033[0m {desc}")

    print()
    print(f"  \033[90m{len(results)} tool(s) found. Run \033[1;32mevtool <name>\033[0m\033[90m to use any tool.\033[0m")
    print()
