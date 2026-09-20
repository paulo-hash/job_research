#!/usr/bin/env python3
"""Search Lever public postings for NYC engineering jobs that mention visa sponsorship."""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests

API_URL = "https://api.lever.co/v0/postings/{company}"
PAGE_SIZE = 100
CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "lever"
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})

NYC_RE = re.compile(
    r"(?:"
    r"\b(?:new york city|nyc|brooklyn|manhattan|queens|bronx|"
    r"staten island|long island city)\b|"
    r"\bnew york,\s*(?:ny|new york)\b|"
    r"^new york\b"
    r")",
    re.I,
)

ENGINEERING_TITLE_RE = re.compile(
    r"(?:"
    r"software(?:\s+development)?\s+engineer|software\s+developer|"
    r"\bswe\b|full[-\s]?stack|front[-\s]?end|back[-\s]?end|"
    r"data\s+engineer|data\s+scientist|analytics\s+engineer|"
    r"machine\s+learning|ml\s+engineer|ai\s+engineer|"
    r"platform\s+engineer|infrastructure\s+engineer|"
    r"devops|site\s+reliability|\bsre\b|"
    r"applied\s+scientist|research\s+(?:engineer|scientist)|"
    r"systems?\s+engineer|security\s+engineer|"
    r"forward\s+deployed.{0,24}engineer|quantitative\s+(?:developer|engineer)|"
    r"staff\s+engineer|principal\s+engineer|"
    r"new\s+grad.{0,40}engineer|engineering\s+intern"
    r")",
    re.I,
)

NON_IC_TITLE_RE = re.compile(
    r"\b(?:sales|account\s+executive|recruiter|recruiting|"
    r"customer\s+success|business\s+development|account\s+manager|"
    r"solutions\s+engineer|sales\s+engineer)\b",
    re.I,
)

# Positive: the posting says they sponsor (or that sponsorship is available).
VISA_POSITIVE_RE = re.compile(
    r"(?:"
    r"visa\s+sponsor(?:ship)?|"
    r"sponsor(?:s|ship|ing)?\s+(?:a\s+|an\s+|your\s+)?(?:work\s+)?visas?|"
    r"h-?1-?b(?:\s+visa)?(?:\s+sponsor(?:ship)?)?|"
    r"(?:eligible|available|provided|offer(?:s|ed)?|open)\s+"
    r"(?:for\s+)?(?:visa\s+)?sponsor(?:ship)?|"
    r"(?:we|will|willing\s+to)\s+sponsor|"
    r"immigration\s+sponsor(?:ship)?|"
    r"work\s+(?:visa|authorization)\s+sponsor(?:ship)?"
    r")",
    re.I,
)

# Negative: they mention visas only to say they do not sponsor.
VISA_NEGATIVE_RE = re.compile(
    r"(?:"
    r"(?:unable|not\s+able|cannot|can\s+not|will\s+not|do(?:es)?\s+not|"
    r"don'?t|won'?t|no\s+longer)\s+(?:to\s+)?"
    r"(?:offer|provide|support|give|consider)?\s*(?:any\s+)?"
    r"(?:visa\s+)?sponsor|"
    r"(?:unable|not\s+able|cannot|will\s+not|do(?:es)?\s+not|don'?t)\s+"
    r"(?:to\s+)?consider.{0,100}(?:visa\s+)?sponsor|"
    r"(?:not|no)\s+(?:currently\s+)?(?:accepting|considering).{0,80}(?:visa\s+)?sponsor|"
    r"candidates?\s+who\s+require\s+(?:visa\s+)?sponsor|"
    r"(?:no|without|not\s+available)\s+(?:visa\s+)?sponsor|"
    r"not\s+(?:eligible|available)\s+for\s+(?:visa\s+)?sponsor|"
    r"sponsor(?:ship)?\s+is\s+not|"
    r"must\s+(?:already\s+)?be\s+(?:legally\s+)?"
    r"authorized\s+to\s+work.{0,80}without.{0,40}sponsor"
    r")",
    re.I,
)


def load_companies(path: Path) -> list[str]:
    companies: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        companies.append(line)
    return companies


def posting_text(job: dict) -> str:
    parts = [
        job.get("text") or "",
        job.get("descriptionPlain") or "",
        job.get("openingPlain") or "",
        job.get("descriptionBodyPlain") or "",
        job.get("additionalPlain") or "",
        job.get("salaryDescriptionPlain") or "",
    ]
    for item in job.get("lists") or []:
        parts.append(item.get("text") or "")
        html = item.get("content") or ""
        parts.append(re.sub(r"<[^>]+>", " ", html))
    return "\n".join(parts)


def locations(job: dict) -> list[str]:
    categories = job.get("categories") or {}
    values = [categories.get("location") or ""]
    values.extend(categories.get("allLocations") or [])
    return [value for value in values if value]


def is_nyc(job: dict) -> bool:
    return any(NYC_RE.search(location.strip()) for location in locations(job))


def is_engineering_role(title: str) -> bool:
    if NON_IC_TITLE_RE.search(title) and not ENGINEERING_TITLE_RE.search(title):
        return False
    return bool(ENGINEERING_TITLE_RE.search(title))


def visa_snippet(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 70)
    end = min(len(text), match.end() + 90)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def cache_path(company: str) -> Path:
    return CACHE_DIR / f"{quote(company, safe='')}.json"


def fetch_company_jobs(company: str, refresh: bool = False) -> list[dict]:
    path = cache_path(company)
    if not refresh and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    jobs: list[dict] = []
    skip = 0
    while True:
        response = SESSION.get(
            API_URL.format(company=company),
            params={"mode": "json", "limit": PAGE_SIZE, "skip": skip},
            timeout=30,
        )
        if response.status_code == 404:
            jobs = []
            break
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            jobs = []
            break
        jobs.extend(payload)
        if len(payload) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs), encoding="utf-8")
    return jobs


def fetch_one(company: str, refresh: bool = False) -> tuple[str, list[dict] | None, str | None]:
    try:
        return company, fetch_company_jobs(company, refresh=refresh), None
    except requests.RequestException as exc:
        return company, None, str(exc)


def visa_status(text: str) -> tuple[str, str | None]:
    negative = VISA_NEGATIVE_RE.search(text)
    if negative:
        return "no", visa_snippet(text, negative)
    positive = VISA_POSITIVE_RE.search(text)
    if positive:
        return "sponsors", visa_snippet(text, positive)
    return "unmentioned", None


def search(
    companies: list[str], workers: int, visa_filter: str, refresh: bool = False
) -> tuple[list[dict], dict[str, int]]:
    matches: list[dict] = []
    stats = {"companies_ok": 0, "companies_missing": 0, "companies_error": 0, "jobs": 0}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_one, company, refresh) for company in companies]
        for future in as_completed(futures):
            company, jobs, error = future.result()
            if error:
                stats["companies_error"] += 1
                print(f"! {company}: {error}", file=sys.stderr)
                continue
            if jobs is None:
                continue
            if not jobs:
                stats["companies_missing"] += 1
                continue
            stats["companies_ok"] += 1
            stats["jobs"] += len(jobs)
            for job in jobs:
                title = job.get("text") or ""
                if not is_engineering_role(title) or not is_nyc(job):
                    continue
                status, snippet = visa_status(posting_text(job))
                if visa_filter == "sponsors" and status != "sponsors":
                    continue
                if visa_filter == "none" and status != "no":
                    continue
                categories = job.get("categories") or {}
                matches.append(
                    {
                        "company": company,
                        "title": title,
                        "location": categories.get("location"),
                        "all_locations": categories.get("allLocations") or [],
                        "team": categories.get("team"),
                        "workplace": job.get("workplaceType"),
                        "url": job.get("hostedUrl") or job.get("applyUrl"),
                        "visa": status,
                        "visa_snippet": snippet,
                    }
                )

    matches.sort(key=lambda item: (item["company"].casefold(), item["title"].casefold()))
    return matches, stats


def print_matches(matches: list[dict]) -> None:
    if not matches:
        print("Aucun job NYC d'ingénierie ne mentionne un sponsoring de visa.")
        return
    for item in matches:
        print(f"[{item['company']}] {item['title']}")
        print(f"  Lieu: {item['location']} ({item['workplace'] or 'unspecified'})")
        if item["team"]:
            print(f"  Équipe: {item['team']}")
        if item["visa_snippet"]:
            print(f"  Visa ({item['visa']}): {item['visa_snippet']}")
        else:
            print(f"  Visa: {item['visa']}")
        print(f"  {item['url']}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Trouve des jobs Lever à New York (software/data engineer, etc.) "
            "dont la description mentionne un sponsoring de visa."
        )
    )
    parser.add_argument(
        "--companies",
        help="Slugs Lever séparés par des virgules (sinon companies.txt)",
    )
    parser.add_argument(
        "--companies-file",
        type=Path,
        default=Path(__file__).with_name("companies.txt"),
        help="Fichier de slugs (défaut: companies.txt)",
    )
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    parser.add_argument(
        "--visa",
        choices=("sponsors", "none", "all"),
        default="sponsors",
        help="sponsors: mention positive (défaut). none: refus. all: tous les jobs NYC d'ingénierie",
    )
    parser.add_argument("--workers", type=int, default=16, help="Requêtes en parallèle")
    parser.add_argument("--refresh", action="store_true", help="Ignore le cache local")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.companies:
        companies = [item.strip() for item in args.companies.split(",") if item.strip()]
    else:
        if not args.companies_file.exists():
            print(f"Fichier introuvable: {args.companies_file}", file=sys.stderr)
            return 1
        companies = load_companies(args.companies_file)

    if not companies:
        print("Aucune entreprise à interroger.", file=sys.stderr)
        return 1

    matches, stats = search(
        companies,
        workers=max(1, args.workers),
        visa_filter=args.visa,
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
            f"{stats['companies_ok']} boards Lever · "
            f"{stats['companies_missing']} slugs vides/inconnus · "
            f"{stats['companies_error']} erreurs",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
