# Application guidelines

## Honesty

- Every sentence on the CV and cover letter must be supported by `data/experience.txt` or already appear on `data/resume_example.docx`.
- Do not invent employers, titles, dates, locations, degrees, tools, metrics, team size, or impact.
- Do not upgrade a fact ("used Python" → "designed a distributed Python platform").
- Do not add a keyword from the job description unless it already appears in those two files.
- If `experience.txt` has no roles, stop. Do not use `data/profile.yaml` as biography.

## CV (Word)

Match `data/resume_example.docx` / `data/cv_demo.md`:

1. Centered name (all caps).
2. Centered `email   ·   linkedin`.
3. Centered bold tagline (`Native French speaker  ·  Fluent English  ·  Targeting New York` unless experience.txt has a different tagline).
4. `SUMMARY` — one paragraph. Re-weight toward this job; do not add new claims.
5. `EXPERIENCE` — `### Title` then `Company  ·  Location  ·  dates` on the next line, then `- ` bullets. Reorder roles/bullets for the posting. Optional `**bold lead-in**` on a bullet only if that phrase is already in the source.
6. `SKILLS` — rows `**Label**	values` with labels from the example (Languages, Programming, Engineering, Data, AI tooling, Domain). Drop a row if nothing in it is supported.
7. `EDUCATION` — copy from `resume_example.docx` unless experience.txt lists education.

One page. English. No photo. Convert md → docx with `scripts/md_to_cv_docx.py` (do not hand-build the .docx).

## Cover letter

English, ~250–350 words:

1. Opening: role title, company, one true reason this posting matches a fact in `experience.txt`.
2. Body: 2–3 facts from experience that map to the posting.
3. Close: availability / location from the files. Mention visa only if `work_authorization` is filled **and** the job `visa` field is `sponsors`.

No generic "I am passionate about software."

## Output

```
data/applications/<job_id>/cv.md
data/applications/<job_id>/cv.docx
data/applications/<job_id>/cover_letter.md
```
