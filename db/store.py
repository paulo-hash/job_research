from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from score_engine import ScoredMatch

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("JOBS_DB", ROOT / "data" / "jobs.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    url TEXT NOT NULL,
    posted TEXT,
    visa TEXT,
    visa_snippet TEXT,
    description TEXT,
    score INTEGER NOT NULL,
    matched_skills TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

INSERT_SQL = """
INSERT OR IGNORE INTO jobs (
    id, company, title, location, url, posted, visa, visa_snippet,
    description, score, matched_skills
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def init_db(path: Path | None = None) -> Path:
    db_path = path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(SCHEMA)
        connection.commit()
    return db_path


def insert_jobs(matches: list[ScoredMatch], path: Path | None = None) -> int:
    db_path = init_db(path)
    rows = [
        (
            job.id,
            job.company,
            job.title,
            job.location,
            job.url,
            job.posted,
            job.visa,
            job.visa_snippet,
            job.description,
            job.score,
            ",".join(job.matched_skills),
        )
        for job in matches
    ]
    with sqlite3.connect(db_path) as connection:
        before = connection.total_changes
        connection.executemany(INSERT_SQL, rows)
        connection.commit()
        return connection.total_changes - before
