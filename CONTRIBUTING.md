# Develop Jobcu

Follow [AGENTS.md](AGENTS.md). The assistant leads implementation, cleanup, review and tested
merges; the human owns copyright and licensing. User data stays outside Git.

## Local project

Use the existing checkout. In Codex, add it as a local project, select it as the primary folder,
and start a Local chat. The folder supplies the code and AGENTS.md; no source or chat upload is
needed. [Official project documentation](https://learn.chatgpt.com/docs/projects), checked 2026-10-07.

The checkout is connected to GitHub. Safe pulls, commits, tests, pushes, CI and merge commits
publish changes; individual edits are not mirrored instantly. The launcher checks for updates
on clean main and warns if it must use the installed version.

## Sessions

All reusable prompts live in [PROMPTS.md](docs/PROMPTS.md):

- [Start a session](docs/PROMPTS.md#start-a-session), including recovery after a cutoff.
- [Review a completed search](docs/PROMPTS.md#review-a-search), with explicit private-access and spending limits.
- [Deep improvement](docs/PROMPTS.md#deep-improvement), for researched and tested improvements.
- [End a session](docs/PROMPTS.md#end-a-session), before closing the chat or reaching a usage limit.

The private-results procedure is [below](#review-a-completed-search). Everyday setup and searches
are in the [user guides](README.md#use-jobcu).

## Development commands

For another computer, install Git and uv and clone the repository. The assistant runs:

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
```

Tests use disposable fictional data and need no API keys. Use the
[architecture and tool map](docs/ENGINEERING.md#project-layout) for targeted work.
For full-ad evidence changes, use `tests/test_full_ad_recovery.py`, `tests/test_search.py` and
`tests/test_careers.py`: verify recovered requirements reach matching, objective facts are
checked before scoring, cache reuse makes fresh judgements and failed reads retain labelled
evidence. Mock readers and HTTP transports exercise source limits without vacancy traffic.
Work on a branch, review the diff, open a PR and wait for Mac, Windows and privacy CI.
Merge with a merge commit; preserve shared history. Other contributors' PRs require review.

## Review a completed search

Use the [review prompt](docs/PROMPTS.md#review-a-search) after Jobcu finishes, or follow an existing
owner authorization recorded privately as described in [AGENTS.md](AGENTS.md). Check its
recipient, scope, search window, spending limits and any revocation before using it. A normal
development prompt grants no private access or paid testing permission. Follow
[AGENTS.md](AGENTS.md), preserve owner ratings, and keep detailed evidence outside Git.
The saved search can be reviewed whether Jobcu is running or stopped. Checking app state in
the start routine preserves the owner's session; it is not a prerequisite for result analysis.

### 1. Measure

Run `uv run python tools/review_search.py`. It opens the latest saved results in read-only
SQLite mode, with no provider or job-site requests and allowlisted aggregate output only.
Keep even aggregates local until the owner approves a public summary.

Inspect source messages, unchecked conditions, unknown dates, scoring limits, summary shares,
top-10 blockers, step times and token/web usage privately. Separate answer-wait time from work.
The report flags a newer attempt without saved results. Correction timings cover only the
latest correction, while usage includes the original search and all corrections; compare
complete original searches for performance. Missing timings or run kinds remain unknown.

### 2. Judge independently

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

### 3. Check ranking and stability

Report top-10 good/okay/poor counts and precision only when every top card is independently
labelled. Check field, seniority, languages, permits and other requirements separately.
Use `tools/score_check.py --rescore --aggregate` only for an authorized focused repeat, with
current documents and the saved location plan. Older plan-less samples cannot validate
preferences. Compare single/batch runs and repeat borderline cases; broad score-band agreement
is a diagnostic, not accuracy. Do not tune to one ad.

### 4. Measure misses

Find an independent 15–25-job benchmark in country order from AGENTS.md. Verify original
posting/closing dates and requisition identity; search snippets alone are insufficient.
Keep its CSV outside Git and run `tools/coverage_test.py` on the private copy. Classify misses
as source coverage, search words, duplicates, criteria, relevance or scoring limits.
Report recall for that sample and its size, never for the whole job market.

### 5. Improve and compare

Fix the biggest confirmed issue with fictional regressions. Change one collection/scoring
factor at a time. Compare recall, ranking, requests, cost and elapsed time on the same sample
at medium effort. Token estimates may omit provider fees and discounts; corrections have
cumulative usage. Delete disposable scratch data, record general lessons with fictional
examples only (public real-result summaries require separate approval), test, push, wait
for CI and merge with a merge commit.
