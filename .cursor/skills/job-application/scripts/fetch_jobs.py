#!/usr/bin/env python3
"""Print jobs from data/jobs.db as JSON. Usage: fetch_jobs.py ID [ID ...]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "db" / "store.py").exists()
)
sys.path.insert(0, str(ROOT))

from db import get_jobs  # noqa: E402


def main(argv: list[str]) -> int:
    ids = [item.strip() for item in argv if item.strip()]
    if not ids:
        print("usage: fetch_jobs.py JOB_ID [JOB_ID ...]", file=sys.stderr)
        return 2
    found = get_jobs(ids)
    missing = [job_id for job_id in ids if job_id not in {str(row["id"]) for row in found}]
    json.dump({"jobs": found, "missing": missing}, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 1 if missing and not found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
