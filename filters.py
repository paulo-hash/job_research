"""Shared NYC / engineering / visa filters."""

from __future__ import annotations

import re

NYC_RE = re.compile(
    r"(?:"
    r"\b(?:new york city|nyc|brooklyn|manhattan|queens|bronx|"
    r"staten island|long island city|greater new york)\b|"
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

VISA_POSITIVE_RE = re.compile(
    r"(?:"
    r"visa\s+sponsor(?:ship)?|"
    r"sponsor(?:s|ship|ing)?\s+(?:a\s+|an\s+|your\s+)?(?:work\s+)?visas?|"
    r"h-?1-?b(?:\s+visa)?(?:\s+sponsor(?:ship)?)?|"
    r"(?:eligible|available|provided|offer(?:s|ed)?|open)\s+"
    r"(?:for\s+)?(?:visa\s+)?sponsor(?:ship)?|"
    r"(?:we|will|willing\s+to)\s+(?:do\s+)?sponsor(?:s|ship|ing)?"
    r"(?:\s+\w+){0,4}\s+visas?|"
    r"immigration\s+sponsor(?:ship)?|"
    r"work\s+(?:visa|authorization)\s+sponsor(?:ship)?"
    r")",
    re.I,
)

VISA_NEGATIVE_RE = re.compile(
    r"(?:"
    r"(?:unable|not\s+able|cannot|can\s+not|will\s+not|do(?:es)?\s+not|"
    r"don'?t|won'?t|no\s+longer)\s+(?:to\s+)?"
    r"(?:offer|provide|support|give|consider|pursue)?\s*(?:any\s+)?"
    r"(?:visa\s+|immigration\s+)?sponsor|"
    r"(?:unable|not\s+able|cannot|will\s+not|do(?:es)?\s+not|don'?t)\s+"
    r"(?:to\s+)?(?:consider|pursue).{0,100}(?:visa\s+|immigration\s+)?sponsor|"
    r"(?:not|no)\s+(?:currently\s+)?(?:accepting|considering).{0,80}(?:visa\s+)?sponsor|"
    r"candidates?\s+who\s+require\s+(?:visa\s+)?sponsor|"
    r"(?:no|without|not\s+available)\s+(?:visa\s+|immigration\s+)?sponsor|"
    r"without.{0,50}(?:visa|immigration)\s+sponsor|"
    r"no\s+immigration\s+sponsor|"
    r"not\s+(?:eligible|available)\s+for\s+(?:visa\s+)?sponsor|"
    r"sponsor(?:ship)?\s+is\s+not|"
    r"must\s+(?:already\s+)?be\s+(?:legally\s+)?"
    r"authorized\s+to\s+work.{0,80}without.{0,40}sponsor"
    r")",
    re.I,
)


def is_nyc_location(location: str) -> bool:
    return bool(NYC_RE.search(location.strip()))


def is_engineering_role(title: str) -> bool:
    if NON_IC_TITLE_RE.search(title) and not ENGINEERING_TITLE_RE.search(title):
        return False
    return bool(ENGINEERING_TITLE_RE.search(title))


def visa_snippet(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 70)
    end = min(len(text), match.end() + 90)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def visa_status(text: str) -> tuple[str, str | None]:
    negative = VISA_NEGATIVE_RE.search(text)
    if negative:
        return "no", visa_snippet(text, negative)
    positive = VISA_POSITIVE_RE.search(text)
    if positive:
        return "sponsors", visa_snippet(text, positive)
    return "unmentioned", None


OLDER_THAN_DAY_RE = re.compile(r"\b(?:\d+\s+)?(?:days?|weeks?|months?|years?)\b", re.I)
OLDER_THAN_WEEK_RE = re.compile(r"\b(?:\d+\s+)?(?:weeks?|months?|years?)\b", re.I)
OLDER_THAN_MONTH_RE = re.compile(r"\b(?:\d+\s+)?(?:months?|years?)\b", re.I)


def is_recent_linkedin_post(posted_text: str, posted: str) -> bool:
    if posted == "any":
        return True
    text = posted_text.strip()
    if not text:
        return True
    if posted == "24h":
        return not OLDER_THAN_DAY_RE.search(text)
    if posted == "week":
        return not OLDER_THAN_WEEK_RE.search(text)
    if posted == "month":
        return not OLDER_THAN_MONTH_RE.search(text)
    return True
