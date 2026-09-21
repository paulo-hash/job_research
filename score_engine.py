from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from linkedin import LinkedInJob

PROFILE_PATH = Path(__file__).resolve().parent / "data" / "profile.yaml"

SKILL_WEIGHT = 0.50
TITLE_WEIGHT = 0.20
SENIORITY_WEIGHT = 0.20
DOMAIN_WEIGHT = 0.10

SENIORITY_RANK = {
    "junior": 1,
    "intern": 1,
    "entry": 1,
    "mid": 2,
    "mid-level": 2,
    "intermediate": 2,
    "senior": 3,
    "staff": 4,
    "principal": 5,
}

YEARS_RE = re.compile(
    r"(\d+)\s*(?:\+|plus)?\s*[\-+]?\s*(?:to\s*)?(\d+)?\s*\+?\s*years?",
    re.I,
)


def _as_tuple(values: object) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(str(item).strip().lower() for item in values if str(item).strip())


def _contains(haystack: str, needle: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack, re.I))


@dataclass(frozen=True)
class Profile:
    seniority: str
    years: int
    skills: tuple[str, ...]
    titles: tuple[str, ...]
    domains: tuple[str, ...]

    @classmethod
    def load(cls, path: Path | None = None) -> Profile:
        data = yaml.safe_load((path or PROFILE_PATH).read_text(encoding="utf-8")) or {}
        return cls(
            seniority=str(data.get("seniority") or "").strip().lower(),
            years=int(data.get("years") or 0),
            skills=_as_tuple(data.get("skills")),
            titles=_as_tuple(data.get("titles")),
            domains=_as_tuple(data.get("domains")),
        )


@dataclass(frozen=True)
class ScoredMatch(LinkedInJob):
    score: int
    matched_skills: tuple[str, ...] = ()


def _overlap(needles: tuple[str, ...], text: str) -> tuple[float, tuple[str, ...]]:
    if not needles:
        return 0.0, ()
    matched = tuple(item for item in needles if _contains(text, item))
    return len(matched) / len(needles), matched


def _title_score(profile: Profile, title: str) -> float:
    title_l = title.lower()
    if any(item in title_l for item in profile.titles):
        return 1.0
    ratio, _ = _overlap(profile.titles, title_l)
    return ratio


def _job_years(text: str) -> int | None:
    match = YEARS_RE.search(text)
    if not match:
        return None
    low = int(match.group(1))
    high = int(match.group(2)) if match.group(2) else low
    return (low + high) // 2


def _job_seniority_rank(text: str) -> int | None:
    found: list[int] = []
    for label, rank in SENIORITY_RANK.items():
        if _contains(text, label):
            found.append(rank)
    return max(found) if found else None


def _seniority_score(profile: Profile, text: str) -> float:
    scores: list[float] = []
    yours = SENIORITY_RANK.get(profile.seniority, 3)
    theirs = _job_seniority_rank(text)
    if theirs is not None:
        gap = abs(yours - theirs)
        scores.append(1.0 if gap == 0 else 0.6 if gap == 1 else 0.25)

    required = _job_years(text)
    if required is not None and required > 0:
        scores.append(min(1.0, profile.years / required))

    return sum(scores) / len(scores) if scores else 0.5


def score_job(job: LinkedInJob, profile: Profile) -> ScoredMatch:
    blob = f"{job.title}\n{job.description}".lower()
    skills_ratio, matched = _overlap(profile.skills, blob)
    title_ratio = _title_score(profile, job.title)
    seniority_ratio = _seniority_score(profile, blob)
    domain_ratio, _ = _overlap(profile.domains, blob)
    total = round(
        100
        * (
            SKILL_WEIGHT * skills_ratio
            + TITLE_WEIGHT * title_ratio
            + SENIORITY_WEIGHT * seniority_ratio
            + DOMAIN_WEIGHT * domain_ratio
        )
    )
    return ScoredMatch(**asdict(job), score=total, matched_skills=matched)


def score(matches: list[LinkedInJob], profile: Profile) -> list[ScoredMatch]:
    ranked = [score_job(job, profile) for job in matches]
    ranked.sort(key=lambda item: (-item.score, item.company.casefold(), item.title.casefold()))
    return ranked
