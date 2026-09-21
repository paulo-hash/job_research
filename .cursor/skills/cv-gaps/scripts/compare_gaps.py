#!/usr/bin/env python3
"""Compare data/experience.txt to jobs in SQLite. Prints JSON gaps."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "db" / "store.py").exists()
)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import list_jobs  # noqa: E402
from phrases import ALIASES, GENERIC, PHRASES, SENIORITY, TITLE_LIKE  # noqa: E402

EXPERIENCE_PATH = ROOT / "data" / "experience.txt"


def _contains(haystack: str, needle: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack, re.I))


def _mentions(text: str, needle: str) -> int:
    return len(re.findall(rf"(?<!\w){re.escape(needle)}(?!\w)", text, re.I))


def _canonical(phrase: str) -> str:
    return ALIASES.get(phrase.lower(), phrase.lower())


def compare() -> dict:
    experience = EXPERIENCE_PATH.read_text(encoding="utf-8") if EXPERIENCE_PATH.exists() else ""
    jobs = list_jobs()
    by_skill: dict[str, list[dict[str, str]]] = defaultdict(list)
    seniority_jobs: dict[str, int] = defaultdict(int)

    for job in jobs:
        blob = f"{job.get('title') or ''}\n{job.get('description') or ''}"
        seen: set[str] = set()
        for phrase in PHRASES:
            if not _contains(blob, phrase):
                continue
            key = _canonical(phrase)
            if key in seen:
                continue
            seen.add(key)
            by_skill[key].append(
                {
                    "id": str(job.get("id") or ""),
                    "company": str(job.get("company") or ""),
                    "title": str(job.get("title") or ""),
                    "score": job.get("score"),
                }
            )
        title = str(job.get("title") or "")
        for label in SENIORITY:
            if _contains(title, label):
                seniority_jobs[label] += 1
                break

    have: list[dict] = []
    thin: list[dict] = []
    missing: list[dict] = []
    for skill, hits in sorted(by_skill.items(), key=lambda item: (-len(item[1]), item[0])):
        count = _mentions(experience, skill)
        row = {
            "skill": skill,
            "kind": "title" if skill in TITLE_LIKE else "generic" if skill in GENERIC else "skill",
            "jobs": len(hits),
            "experience_mentions": count,
            "examples": hits[:5],
        }
        if row["kind"] != "skill":
            have.append(row)
        elif count == 0:
            missing.append(row)
        elif count == 1:
            thin.append(row)
        else:
            have.append(row)

    return {
        "empty_experience": not experience.strip(),
        "job_count": len(jobs),
        "have": have,
        "thin": thin,
        "missing": missing,
        "seniority_in_titles": dict(seniority_jobs),
        "seniority_in_experience": {
            label: _mentions(experience, label) for label in SENIORITY if _mentions(experience, label)
        },
    }


def main() -> int:
    payload = compare()
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    print()
    if payload["empty_experience"]:
        return 1
    if payload["job_count"] == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
