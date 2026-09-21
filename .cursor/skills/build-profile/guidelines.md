# Profile from experience

- Source: `data/experience.txt` only. Never `data/profile.yaml`.
- Layout: `data/profile_demo.md`.
- Copy facts; do not paraphrase into new claims.
- Omit a heading when that section has no facts.
- **Seniority:** highest rank present in titles (`intern`/`junior`/`mid`/`senior`/`staff`/`principal`). If none of those words appear, omit seniority. Do not default to `senior`.
- **Years:** use the integer from the fetch script (`derived_years`) when dates exist. Otherwise omit. Do not copy `years: 4` from `profile.yaml`.
- **Domains:** a word or phrase already in `experience.txt` (company, title, or bullets). Do not infer "fintech" from a bank name unless the file says fintech.
- **Skills:** the `skills` lists, plus tokens that already appear as written tools/languages in bullets. No synonyms.
- Do not invent a headline. Use `headline` only if filled.
