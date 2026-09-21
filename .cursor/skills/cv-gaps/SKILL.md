---
name: cv-gaps
description: >-
  Compares data/experience.txt to jobs in data/jobs.db and writes data/gaps.md
  with skill gaps, what to learn, and personal-project ideas to strengthen the
  CV. Use when the user asks for gaps, CV improvements, skills to learn, or
  projects versus saved job offers.
---

# CV gaps

Compare the user's experience to saved LinkedIn jobs. Write `data/gaps.md`: what is missing, what to learn, which personal projects would create CV evidence.

## Workflow

1. Read [guidelines.md](guidelines.md) and [report-template.md](report-template.md).
2. Run:

```bash
PYTHONPATH=. python .cursor/skills/cv-gaps/scripts/compare_gaps.py
```

3. Exit `1`: `experience.txt` is empty → stop, ask them to fill it.
   Exit `2`: no rows in `data/jobs.db` → stop, ask them to run `python main.py`.
4. Write `data/gaps.md` from the JSON using the report template. Every skill in the file must come from `have`, `thin`, or `missing`.
5. Recap in chat: top 5 gaps, 3 project ideas, path to the file.

## Hard rules

- Do not invent tools or job requirements that are not in the JSON.
- Do not use `data/profile.yaml`.
- Project ideas are suggestions, not experience. Never add them to `experience.txt` or a CV.
