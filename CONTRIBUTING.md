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

Use Start once in a local project chat, then send Review, Deep improvement or another task.
Before closing the chat, use End. All reusable prompts live in [PROMPTS.md](docs/PROMPTS.md):

- [Start a session](docs/PROMPTS.md#start-a-session) prepares the chat and can finish an already
  authorized interrupted goal. It waits for your task instead of choosing work from the backlog.
- [Review a completed search](docs/PROMPTS.md#review-a-search) independently evaluates the latest
  completed search and implements an evidence-backed improvement, within its private scope.
- [Deep improvement](docs/PROMPTS.md#deep-improvement) researches and implements improvements
  across the project; it does not require a new search. Older evidence needs existing authority.
- [End a session](docs/PROMPTS.md#end-a-session) finishes the smallest safe coherent step or
  parks it with an exact next action and verified handover for a fresh chat.

Review and Deep improvement reuse the prepared session. Both assess source coverage and can
add, improve, replace or remove search methods using evidence and verified permissions.
Recovery, check reuse and publication rules live in [AGENTS](AGENTS.md#sessions); no-work
readiness/ending needs no full test run or ceremonial commit. Development still requires
meaningful tests and exact-head Mac/Windows/privacy CI before merging.
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
For employer discovery, `tests/test_employer_recovery.py` verifies incomplete countries retry
while completed countries are reused, account/allowance errors preserve parallel completed
work, explicit empty answers need evidence, and migration retains history/ratings/employers.
`tests/test_employers.py` checks actual mock career-list verification; `tests/test_reset.py`
also populates completion provenance so reset controls clear the new state. No live discovery
or provider traffic is needed to exercise these paths.
For full-ad evidence changes, use `tests/test_full_ad_recovery.py`, `tests/test_search.py` and
`tests/test_careers.py`: verify recovered requirements reach matching, objective facts are
checked before scoring, cache reuse makes fresh judgements and failed reads retain labelled
evidence. Mock readers and HTTP transports exercise source limits without vacancy traffic.
For Maps reliability, `tests/test_maps_recovery.py` covers persistent/transient quotas,
attempted-element accounting, cached evidence, Stop, concurrent allowance checks and truthful
wait progress. Fake clocks establish protocol waits; they do not measure live search speed.
`tests/test_maps_elements.py` distinguishes service errors, incomplete samples and confirmed
no-route outcomes, preserves mixed Maps/AI attribution and memory boundaries, and exercises
retention/scoring across fictional professions and all supported countries.
For scoring evidence, `tests/test_requirements.py` checks ad/profile quote support, met/unmet/
unknown rubric consistency, clipped text, per-job research boundaries, late resolution and
legacy blockers. `tests/test_search.py` verifies the notes reach results. These scripted checks
prove application behavior, not live extraction or matching accuracy; use the private procedure
below for those claims. Keep fictional non-engineering cases and all countries supported.
For custom APIs, `tests/test_custom_ai.py` sends fictional requests through SDK mock transports
to check the actual host/path/key, schema, thinking and token payloads. Mixed-provider research
must keep one web allowance/monthly ledger and record the real provider; tests also cover
refusals, explicit probes and legacy configuration. `tests/test_ai_parallel.py` verifies shared
concurrent web reservations. Changing API formats must not imply hosted search entitlement or
silently remove reasoning. A connection probe is generation, not matching-quality validation.
Work on a branch, review the diff, open a PR and wait for Mac, Windows and privacy CI.
Merge with a merge commit; preserve shared history. Other contributors' PRs require review.

## Review a completed search

Use the [review prompt](docs/PROMPTS.md#review-a-search) after Jobcu finishes, or follow an existing
owner authorization recorded privately as described in [AGENTS.md](AGENTS.md). Check its
recipient, scope, search window, spending limits and any revocation before using it. A normal
development prompt grants no private access or paid testing permission. Follow
[AGENTS.md](AGENTS.md), preserve owner ratings, and keep detailed evidence outside Git.
The saved search can be reviewed whether Jobcu is running or stopped. Checking app state in
Start preserves the owner's session; it is not a prerequisite for result analysis. In a
prepared chat, inspect only relevant state changes rather than repeat startup. No newly
completed search is needed for [Deep improvement](docs/PROMPTS.md#deep-improvement).
Use the stages below for the claims being investigated; they do not grant additional source
traffic or paid calls. Reuse unchanged saved evidence and completed review work. If original
ads, labels, a benchmark or live-test authority are missing, record the exact dependency and
continue useful free investigation and reproducible fixes without claiming live accuracy.

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

Shuffle the review packet and record each judgement before revealing scores. A known blocker
can establish poor fit despite missing text; an incomplete promising ad remains unknown.
Save unknown cases and their exact missing evidence in the private review record without
inventing ratings to complete precision. Assistant judgement is an independent comparison
with Jobcu's output, not a replacement for original evidence or owner judgement.

Settings → Review results (formerly Score check) hides scores until rated. The owner does not
need to fill in this optional tool for assistant development reviews. Add missing top cards with
`quality.add`, preserving evidence completeness and the location plan; the 50-ad limit still
applies. Save
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

Compare existing and potential search methods for unique fresh relevant jobs and original
evidence across countries/professions, alongside reliability, requests and cost. Total ads,
duplicate shares or a temporary outage alone do not establish a method's value. Trace the
unique useful jobs, better evidence, backup value and gaps before replacing/removing a source;
validate additions against the same benchmark where evidence and authority allow. Consult
[SOURCES](docs/SOURCES.md) and verify current permissions before source work. A missing
independent benchmark limits coverage claims; it need not block a general fix reproduced
with fictional tests.

### 5. Improve and compare

Fix the biggest confirmed issue with fictional regressions. Change one collection/scoring
factor at a time. Compare recall, ranking, requests, cost and elapsed time on the same sample
at medium effort. Token estimates may omit provider fees and discounts; corrections have
cumulative usage. Delete disposable scratch data, record general lessons with fictional
examples only (public real-result summaries require separate approval), test, push, wait
for CI and merge with a merge commit.
