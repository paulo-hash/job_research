from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from db import init_db, insert_jobs
from linkedin import LinkedInJob
from score_engine import Profile, score, score_job


def _job(**overrides: object) -> LinkedInJob:
    base = dict(
        id="1",
        company="Acme",
        title="Senior Backend Software Engineer",
        location="New York, NY",
        url="https://example.com/job",
        posted="2 hours ago",
        visa="sponsors",
        visa_snippet="we offer visa sponsorship",
        description=(
            "We need 4+ years of Python, TypeScript and SQL. "
            "Fintech infrastructure team. Distributed systems experience required."
        ),
    )
    base.update(overrides)
    return LinkedInJob(**base)  # type: ignore[arg-type]


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = Profile.load()

    def test_strong_match_scores_high(self) -> None:
        ranked = score_job(_job(), self.profile)
        self.assertGreaterEqual(ranked.score, 80)
        self.assertIn("python", ranked.matched_skills)

    def test_weak_match_scores_low(self) -> None:
        ranked = score_job(
            _job(
                title="Junior Marketing Intern",
                description="Excel and PowerPoint. 10+ years in sales.",
            ),
            self.profile,
        )
        self.assertLess(ranked.score, 30)
        self.assertEqual(ranked.matched_skills, ())

    def test_score_sorts_descending(self) -> None:
        ranked = score(
            [
                _job(id="weak", title="Junior Marketing Intern", description="sales"),
                _job(id="strong"),
            ],
            self.profile,
        )
        self.assertEqual([item.id for item in ranked], ["strong", "weak"])
        self.assertGreater(ranked[0].score, ranked[1].score)


class DbTests(unittest.TestCase):
    def test_insert_ignores_duplicate_job_id(self) -> None:
        profile = Profile.load()
        job = score_job(_job(id="unique-1"), profile)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.db"
            init_db(path)
            self.assertEqual(insert_jobs([job], path), 1)
            self.assertEqual(insert_jobs([job], path), 0)
            with sqlite3.connect(path) as connection:
                count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
