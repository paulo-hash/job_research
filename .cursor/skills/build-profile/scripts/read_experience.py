#!/usr/bin/env python3
"""Load data/experience.txt and print filled facts as JSON. Exit 1 if empty."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "data" / "experience.txt").exists()
)
EXPERIENCE_PATH = ROOT / "data" / "experience.txt"

SENIORITY_RANK = {
    "intern": 1,
    "junior": 1,
    "entry": 1,
    "mid": 2,
    "mid-level": 2,
    "intermediate": 2,
    "senior": 3,
    "staff": 4,
    "principal": 5,
}

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip().strip("-"):
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def _clean(value: object) -> object:
    if isinstance(value, str):
        text = value.strip()
        return text if text and text != "-" else ""
    if isinstance(value, list):
        return [item for item in (_clean(item) for item in value) if item not in ("", None, [])]
    if isinstance(value, dict):
        return {key: item for key, item in ((k, _clean(v)) for k, v in value.items()) if not _blank(item)}
    return value


def _parse_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    if re.fullmatch(r"(?i)present|current|now|aujourd['’]?hui", text):
        return date.today()
    iso = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?", text)
    if iso:
        year = int(iso.group(1))
        month = int(iso.group(2) or 1)
        return date(year, month, 1)
    named = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", text)
    if named and named.group(1).lower() in MONTHS:
        return date(int(named.group(2)), MONTHS[named.group(1).lower()], 1)
    year_only = re.fullmatch(r"(\d{4})", text)
    if year_only:
        return date(int(year_only.group(1)), 1, 1)
    return None


def _derived_years(roles: list[dict]) -> int | None:
    starts: list[date] = []
    ends: list[date] = []
    for role in roles:
        start = _parse_date(role.get("start"))
        end = _parse_date(role.get("end")) or (date.today() if start else None)
        if start:
            starts.append(start)
            ends.append(end or date.today())
    if not starts:
        return None
    days = (max(ends) - min(starts)).days
    return max(0, round(days / 365.25))


def _seniority(titles: list[str]) -> str:
    found: list[tuple[int, str]] = []
    blob = " ".join(titles).lower()
    for label, rank in SENIORITY_RANK.items():
        if re.search(rf"(?<!\w){re.escape(label)}(?!\w)", blob):
            found.append((rank, label))
    if not found:
        return ""
    return max(found)[1]


def _filled_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    filled: list[dict] = []
    for row in rows:
        if isinstance(row, dict) and not _blank(row):
            filled.append(row)
    return filled


BLOCK_RE = re.compile(
    r"^={10,}\s*\n"
    r"(?P<title>[^\n]+)\s*\n"
    r"(?P<meta>[^\n]+)\s*\n"
    r"={10,}\s*\n"
    r"(?P<body>.*?)(?=^={10,}|\Z)",
    re.M | re.S,
)
META_RE = re.compile(
    r"^(?P<company>.+?)\s*·\s*(?:(?P<location>.+?)\s*·\s*)?(?P<start>.+?)\s*[-–—]\s*(?P<end>.+)$"
)
NAME_RE = re.compile(r"^([A-Z][A-Z\s.'-]+?)\s*-\s*EXPERIENCE", re.I)


def _parse_prose(text: str) -> dict[str, object]:
    name_match = NAME_RE.search(text)
    name = name_match.group(1).strip().title() if name_match else ""
    roles: list[dict] = []
    projects: list[dict] = []
    for match in BLOCK_RE.finditer(text):
        title = match.group("title").strip()
        if title.lower() in {"projects", "education", "experience professionnelle"}:
            continue
        meta = META_RE.match(match.group("meta").strip())
        if not meta:
            continue
        bullets = [
            line[1:].strip()
            for line in match.group("body").splitlines()
            if line.strip().startswith("- ")
        ]
        row = {
            "company": meta.group("company").strip(),
            "title": title,
            "location": (meta.group("location") or "").strip(),
            "start": meta.group("start").strip(),
            "end": meta.group("end").strip(),
            "bullets": bullets,
        }
        company = row["company"].lower()
        if "personal project" in company:
            projects.append(row)
        else:
            roles.append(row)
    return {"name": name, "experience": roles, "projects": projects, "education": [], "skills": {}}


def _load_raw(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        loaded = None
    if isinstance(loaded, dict) and loaded:
        data = _clean(loaded)
        return data if isinstance(data, dict) else {}
    return _parse_prose(text)


def load_experience(path: Path = EXPERIENCE_PATH) -> dict[str, object]:
    data = _load_raw(path)
    if not isinstance(data, dict):
        data = {}
    roles = _filled_rows(data.get("experience"))
    education = _filled_rows(data.get("education"))
    projects = _filled_rows(data.get("projects"))
    skills = data.get("skills") if isinstance(data.get("skills"), dict) else {}
    titles = [
        str(role["title"])
        for role in [*roles, *projects]
        if role.get("title")
    ]
    payload = {
        "name": data.get("name") or "",
        "email": data.get("email") or "",
        "phone": data.get("phone") or "",
        "location": data.get("location") or "",
        "linkedin": data.get("linkedin") or "",
        "github": data.get("github") or "",
        "website": data.get("website") or "",
        "headline": data.get("headline") or "",
        "work_authorization": data.get("work_authorization") or "",
        "skills": skills,
        "experience": roles,
        "education": education,
        "projects": projects,
        "titles": list(dict.fromkeys(titles)),
        "seniority": _seniority(titles),
        "derived_years": _derived_years([*roles, *projects]),
    }
    has_facts = bool(
        payload["name"]
        or payload["headline"]
        or payload["titles"]
        or roles
        or education
        or projects
        or skills
    )
    payload["empty"] = not has_facts
    return payload


def main() -> int:
    payload = load_experience()
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False, default=str)
    print()
    return 1 if payload["empty"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
