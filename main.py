#!/usr/bin/env python3
"""Search LinkedIn for NYC engineering jobs that mention visa sponsorship."""

from __future__ import annotations

import argparse
import json
import sys

from linkedin import search_linkedin


def print_matches(matches: list[dict]) -> None:
    if not matches:
        print("Aucun job NYC d'ingénierie ne mentionne un sponsoring de visa.")
        return
    for item in matches:
        print(f"[{item['company']}] {item['title']}")
        print(f"  Lieu: {item['location']}")
        if item.get("posted"):
            print(f"  Publié: {item['posted']}")
        if item["visa_snippet"]:
            print(f"  Visa ({item['visa']}): {item['visa_snippet']}")
        else:
            print(f"  Visa: {item['visa']}")
        print(f"  {item['url']}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Trouve des jobs LinkedIn à New York (software/data engineer, etc.) "
            "dont la description mentionne un sponsoring de visa."
        )
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=8,
        help="Pages par mot-clé (10 offres/page, défaut: 8)",
    )
    parser.add_argument(
        "--keywords",
        help="Mots-clés séparés par des virgules",
    )
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    parser.add_argument(
        "--posted",
        choices=("24h", "week", "month", "any"),
        default="24h",
        help="Ancienneté de l'offre (défaut: 24h, f_TPR LinkedIn)",
    )
    parser.add_argument(
        "--visa",
        choices=("sponsors", "none", "all"),
        default="sponsors",
        help="sponsors: mention positive (défaut). none: refus. all: tous les jobs NYC d'ingénierie",
    )
    parser.add_argument("--refresh", action="store_true", help="Ignore le cache local")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    keywords = None
    if args.keywords:
        keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]

    matches, stats = search_linkedin(
        visa_filter=args.visa,
        pages=max(1, args.pages),
        keywords=keywords,
        posted=args.posted,
        refresh=args.refresh,
    )

    if args.json:
        json.dump(matches, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        print_matches(matches)

    print(
        f"{len(matches)} résultat(s) · "
        f"{stats['jobs']} offres · "
        f"{stats['details']} descriptions · "
        f"{stats['errors']} erreurs",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
