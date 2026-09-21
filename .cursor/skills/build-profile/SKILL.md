---
name: build-profile
description: >-
  Builds data/profile.md from data/experience.txt using the layout of
  data/profile_demo.md. Never invents facts. Use when the user asks to create,
  update, or regenerate profile.md from experience.
---

# Build profile.md

Write `data/profile.md` from `data/experience.txt` only. Follow `data/profile_demo.md`.

## Workflow

1. Read [guidelines.md](guidelines.md) and `data/profile_demo.md`.
2. Load facts (do not hand-parse if the script runs):

```bash
python .cursor/skills/build-profile/scripts/read_experience.py
```

3. If `"empty": true`, **stop**. Ask the user to fill `data/experience.txt`. Do not use `data/profile.yaml`. Do not invent a biography.
4. Write `data/profile.md` with the demo headings, dropping any section that has no facts.
5. Recap: which fields were filled, which were omitted for lack of data.

## Hard rules

- Do not invent. If it is not in `experience.txt`, it is not in `profile.md`.
- Do not copy seniority, years, skills, titles, or domains from `data/profile.yaml`.
- Keep original wording for bullets, titles, and school names.
