"""LinkedIn guest Jobs API — see https://gist.github.com/Diegiwg/51c22fa7ec9d92ed9b5d1f537b9e1107"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from filters import is_engineering_role, is_nyc_location, is_recent_linkedin_post, visa_status

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
NYC_GEO_ID = "102571732"
NYC_LOCATION = "New York, New York, United States"
PAGE_SIZE = 10
REQUEST_GAP_SECONDS = 1.5
CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "linkedin"
_request_lock = threading.Lock()
_next_request_at = 0.0
POSTED_TPR = {
    "any": None,
    "24h": "r86400",
    "week": "r604800",
    "month": "r2592000",
}

DEFAULT_KEYWORDS = [
    "software engineer",
    "data engineer",
    "machine learning engineer",
    "data scientist",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "platform engineer",
    "site reliability engineer",
    "forward deployment engineer", 
     "forward deployed engineer"
]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
)


def _wait_for_slot() -> None:
    global _next_request_at
    with _request_lock:
        now = time.monotonic()
        wait = _next_request_at - now
        if wait > 0:
            time.sleep(wait)
        _next_request_at = time.monotonic() + REQUEST_GAP_SECONDS


def _retry_after(response: requests.Response, attempt: int) -> float:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return max(5.0, float(header))
        except ValueError:
            pass
    return 15.0 * (attempt + 1)


def _get(url: str, params: dict | None = None, retries: int = 5) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(retries):
        _wait_for_slot()
        try:
            response = SESSION.get(url, params=params, timeout=30)
            if response.status_code == 429:
                delay = _retry_after(response, attempt)
                last_error = requests.HTTPError(
                    f"LinkedIn limite le débit (429). Pause {delay:.0f}s…"
                )
                print(f"! {last_error}", file=sys.stderr)
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2**attempt)
    raise last_error or RuntimeError(f"GET failed: {url}")


def _search_cache_path(keywords: str, start: int, posted: str) -> Path:
    key = quote(f"{keywords}_{posted}_{start}", safe="")
    return CACHE_DIR / "search" / f"{key}.json"


def _detail_cache_path(job_id: str) -> Path:
    return CACHE_DIR / "jobs" / f"{job_id}.json"


def parse_job_id(url: str, urn: str = "") -> str:
    if urn and ":" in urn:
        return urn.rsplit(":", 1)[-1]
    path = url.split("?", 1)[0].rstrip("/")
    return path.rsplit("-", 1)[-1]


def parse_search_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []
    for card in soup.select("div.base-card"):
        link = card.select_one("a.base-card__full-link, [class*=_full-link]")
        href = (link.get("href") if link else "") or ""
        url = href.split("?", 1)[0]
        title_el = card.select_one("[class*=_title]")
        company_el = card.select_one("[class*=_subtitle]")
        location_el = card.select_one("[class*=_location]")
        posted_el = card.select_one("time, [class*=listdate]")
        job_id = parse_job_id(url, card.get("data-entity-urn") or "")
        if not job_id or not job_id.isdigit():
            continue
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        posted_at = posted_el.get("datetime") if posted_el else None
        jobs.append(
            {
                "id": job_id,
                "title": title_el.get_text(strip=True) if title_el else "",
                "company": company_el.get_text(strip=True) if company_el else "",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": url or f"https://www.linkedin.com/jobs/view/{job_id}",
                "posted": posted_text,
                "posted_at": posted_at,
            }
        )
    return jobs


def parse_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    node = (
        soup.select_one("[class*=description] > section > div")
        or soup.select_one(".show-more-less-html__markup")
        or soup.select_one(".description__text")
    )
    return node.get_text(" ", strip=True) if node else ""


def search_page(
    keywords: str, start: int, posted: str = "24h", refresh: bool = False
) -> list[dict]:
    path = _search_cache_path(keywords, start, posted)
    if not refresh and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    params = {
        "keywords": keywords,
        "location": NYC_LOCATION,
        "geoId": NYC_GEO_ID,
        "start": start,
        "f_JT": "F",
    }
    tpr = POSTED_TPR.get(posted)
    if tpr:
        params["f_TPR"] = tpr

    response = _get(SEARCH_URL, params=params)
    jobs = parse_search_cards(response.text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs), encoding="utf-8")
    return jobs


def fetch_description(job_id: str, refresh: bool = False) -> str:
    path = _detail_cache_path(job_id)
    if not refresh and path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("description") or ""

    response = _get(DETAIL_URL.format(job_id=job_id))
    description = parse_description(response.text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"description": description}), encoding="utf-8")
    return description


def collect_listings(
    keywords: list[str], pages: int, posted: str = "24h", refresh: bool = False
) -> list[dict]:
    seen: set[str] = set()
    listings: list[dict] = []
    for keyword in keywords:
        for page in range(pages):
            start = page * PAGE_SIZE
            try:
                batch = search_page(keyword, start, posted=posted, refresh=refresh)
            except requests.RequestException as exc:
                print(f"! linkedin search {keyword!r} start={start}: {exc}", file=sys.stderr)
                break
            if not batch:
                break
            for job in batch:
                if job["id"] in seen:
                    continue
                seen.add(job["id"])
                listings.append(job)
            if len(batch) < PAGE_SIZE:
                break
    return listings


def search_linkedin(
    visa_filter: str,
    pages: int = 8,
    keywords: list[str] | None = None,
    posted: str = "24h",
    refresh: bool = False,
) -> tuple[list[dict], dict[str, int]]:
    keywords = keywords or DEFAULT_KEYWORDS
    listings = collect_listings(keywords, pages=pages, posted=posted, refresh=refresh)
    stats = {"jobs": len(listings), "details": 0, "errors": 0}

    candidates = [
        job
        for job in listings
        if is_engineering_role(job.get("title") or "")
        and is_nyc_location(job.get("location") or "")
        and is_recent_linkedin_post(job.get("posted") or "", posted)
    ]

    descriptions: dict[str, str] = {}
    for job in candidates:
        try:
            descriptions[job["id"]] = fetch_description(job["id"], refresh=refresh)
            stats["details"] += 1
        except (requests.RequestException, RuntimeError) as exc:
            stats["errors"] += 1
            print(f"! description {job['id']} ignorée: {exc}", file=sys.stderr)

    matches: list[dict] = []
    for job in candidates:
        description = descriptions.get(job["id"])
        if description is None:
            continue
        status, snippet = visa_status(f"{job.get('title') or ''}\n{description}")
        if visa_filter == "sponsors" and status != "sponsors":
            continue
        if visa_filter == "none" and status != "no":
            continue
        location = job.get("location") or ""
        matches.append(
            {
                "company": job.get("company") or "",
                "title": job.get("title") or "",
                "location": location,
                "url": job.get("url"),
                "posted": job.get("posted"),
                "visa": status,
                "visa_snippet": snippet,
            }
        )

    matches.sort(key=lambda item: (item["company"].casefold(), item["title"].casefold()))
    return matches, stats
