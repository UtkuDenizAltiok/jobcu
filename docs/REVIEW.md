# Review a completed search

Use the [review prompt](PROMPTS.md#review-a-search) after Jobcu finishes. It grants bounded
private access and re-scoring permission; a normal development prompt does not. Follow
[AGENTS.md](../AGENTS.md), preserve owner ratings, and keep detailed evidence outside Git.

## 1. Measure

Run `uv run python tools/review_search.py`. It opens the latest saved results in read-only
SQLite mode, with no provider or job-site requests and allowlisted aggregate output only.
Keep even aggregates local until the owner approves a public summary.

Inspect source messages, unchecked conditions, unknown dates, scoring limits, summary shares,
top-10 blockers, step times and token/web usage privately. Separate answer-wait time from work.
The report flags a newer attempt without saved results. Correction timings cover only the
latest correction, while usage includes the original search and all corrections; compare
complete original searches for performance. Missing timings or run kinds remain unknown.

## 2. Judge independently

On an authorized private scratch copy, read the full evidence against the documents and actual
criteria **before seeing scores**. Include every top-10 card and build a balanced 30–50-ad set:
good fits, near fits and blockers across the priority countries. Open originals for summaries;
unseen requirements are not satisfied requirements.

The Score check screen hides scores until rated. Add missing top cards with `quality.add`,
preserving evidence completeness and the location plan; the 50-ad limit still applies. Save
approved labels with `quality.rate(..., by="assistant")` in the real private folder.
Never overwrite owner ratings automatically.
`quality.rate(..., by="assistant")` preserves existing owner and legacy labels, including
concurrent edits. Review uncertain evidence without inventing a label to fill the sample.

## 3. Check ranking and stability

Report top-10 good/okay/poor counts and precision only when every top card is independently
labelled. Check field, seniority, languages, permits and other requirements separately.
Use `tools/score_check.py --rescore --aggregate` only for an authorized focused repeat, with
current documents and the saved location plan. Older plan-less samples cannot validate
preferences. Compare single/batch runs and repeat borderline cases; broad score-band agreement
is a diagnostic, not accuracy. Do not tune to one ad.

## 4. Measure misses

Find an independent 15–25-job benchmark in country order from AGENTS.md. Verify original
posting/closing dates and requisition identity; search snippets alone are insufficient.
Keep its CSV outside Git and run `tools/coverage_test.py` on the private copy. Classify misses
as source coverage, search words, duplicates, criteria, relevance or scoring limits.
Report recall for that sample and its size, never for the whole job market.

## 5. Improve and compare

Fix the biggest confirmed issue with fictional regressions. Change one collection/scoring
factor at a time. Compare recall, ranking, requests, cost and elapsed time on the same sample
at medium effort. Token estimates may omit provider fees and discounts; corrections have
cumulative usage. Delete disposable scratch data, update anonymous records, test, push, wait
for CI and merge with a merge commit.
