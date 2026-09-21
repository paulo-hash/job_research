---
name: job-application
description: >-
  Fetches LinkedIn jobs from data/jobs.db by job id, then writes a tailored CV
  as .docx (layout of data/resume_example.docx / data/cv_demo.md) and a cover
  letter using only facts from data/experience.txt and resume_example.docx.
  Never invents experience. Use when the user gives one or more job IDs and
  asks for a CV, resume, cover letter, or lettre de motivation.
---

# Job application

Given one or more LinkedIn **job ids**, load each row from SQLite, then write a CV and cover letter.

Visual layout is `data/resume_example.docx`. Markdown skeleton is `data/cv_demo.md`. Convert with the script below so the Word file matches the example (Calibri, section rules, right-aligned dates, en-dash bullets).

## Workflow

1. Parse job ids from the user message (digits, comma/space separated). If none, ask.
2. Fetch jobs (run this, do not hand-write SQL):

```bash
PYTHONPATH=. python .cursor/skills/job-application/scripts/fetch_jobs.py ID [ID ...]
```

3. If `missing` is non-empty, tell the user those ids are not in `data/jobs.db`. Continue with the jobs that were found. If none were found, stop.
4. Read `data/experience.txt`, `data/cv_demo.md`, and [guidelines.md](guidelines.md). Skim `data/resume_example.docx` (header, EDUCATION, SKILLS row labels).
5. If `experience.txt` has no filled roles, **stop**. Ask the user to fill it. Do not invent a career. Do not use `data/profile.yaml`.
6. For each job, write `data/applications/<job_id>/cv.md` in the `cv_demo.md` shape, then:

```bash
python .cursor/skills/job-application/scripts/md_to_cv_docx.py \
  data/applications/<job_id>/cv.md \
  data/applications/<job_id>/cv.docx
```

Also write `data/applications/<job_id>/cover_letter.md`.

7. Recap: company, title, url, visa, which bullets were used, which job requirements had **no** matching fact (list them; do not fill the gap). Confirm `cv.docx` exists.

## Hard rules

- Do not invent. Role bullets come from `data/experience.txt`. Name, email, LinkedIn, tagline, EDUCATION, and SKILLS row labels come from `data/resume_example.docx` when they are already there.
- Do not add a tool, metric, or degree that is in neither `experience.txt` nor `resume_example.docx`.
- Section order: SUMMARY, EXPERIENCE, SKILLS, EDUCATION. Headings in ALL CAPS.
- English output (NYC jobs).
- Cover letter mentions visa only when `work_authorization` is set in `experience.txt` **and** the job `visa` is `sponsors`.
