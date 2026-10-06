# Develop Jobcu with Codex

The source is publicly readable under the owner's proprietary [LICENSE](LICENSE). User data is
private. [AGENTS.md](AGENTS.md) contains the working rules and decision authority; development
continues locally with ChatGPT/Codex. Everyday users start with [README.md](README.md).

## Open a local Codex project

Use the existing `jobcu` folder containing `AGENTS.md`, `pyproject.toml`, `src` and the two launchers.
In Codex, add a **local project**, name it **Jobcu**, and select that folder as its primary folder.
Start a new chat inside that project in **Local** mode. The code folder is the project context;
you do not need to upload the source, previous chats, CV or keys as project sources.

Codex discovers `AGENTS.md` in the primary folder. The checked-in state and instructions carry
between chats, so paste only the start prompt below. Reference: [official project documentation,
checked 2026-10-06](https://learn.chatgpt.com/docs/projects).

The restored Mac already has Git, uv, GitHub CLI and the locked Python environment. For another
computer, install Git and uv, clone the public repository, then let Codex run:

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
```

For convenient project actions, these commands can be added in Codex's local environment settings:
**Start Jobcu** `uv run jobcu`, **Tests** `uv run pytest`, **Review latest search**
`uv run python tools/review_search.py`. They need no provider keys themselves; only an actual
search needs your personal setup. [Official local-environment documentation](https://learn.chatgpt.com/docs/environments/local-environment).

## Start a fresh session

```text
Continue Jobcu from this local project. Follow AGENTS.md and its "Starting, or resuming after any
interruption" routine. Read Right now in docs/PROGRESS.md and check reality. Make the product and
engineering decisions, research relevant official sources, implement and verify useful changes,
and merge tested PRs with merge commits. Preserve my ownership and private data. Focus first on
electronics and technical engineering, in the recorded country order. Keep the repository ready
for another session and end every response with simple next steps. My documents and keys go only
in Jobcu; don't ask for them in chat. Until I complete a search, continue useful offline work
without inventing results or starting paid tests.
```

## Tomorrow's first search

The planned day is **Wednesday, 2026-10-07**. In Jobcu itself:

1. Set up the AI provider, model and key; test the connection. Optional job-source keys improve
   coverage; Jobcu explains which sources need them.
2. Upload the CV and cover letter, then enter the private query and any additional background.
3. Choose **Posted within: 72 hours**, check the job types, and select **Find matching jobs**.
   This means ads posted in the previous three days, not a three-day running time. New installs
   default to this window; existing saved choices are preserved. Read and answer any limit prompt.
4. Once the search finishes, start a new Local chat in the Jobcu project with the review prompt.

Your actual query decides which countries and roles are searched. The development priority order
is not silently inserted into anyone's query. Keys and documents live outside the source folder.

## Review the latest search locally

```text
Analyse my latest Jobcu search on this Mac. Follow AGENTS.md's start routine, then the local review
protocol in CONTRIBUTING.md. You may read my local Jobcu documents, query and results privately,
and rate the saved quality sample on my behalf. Start with the read-only aggregate review; never
print or publish my profile, query, documents, keys, job list or ratings. Decide which findings
matter, fix confirmed defects with fictional regressions, verify and merge the changes. Use my
saved keys only through Jobcu code for a focused re-score at medium effort, within my existing
limits and at most EUR1 for this review if prices are configured; otherwise finish the free
analysis first and give me one clear next step. Don't start another full search. Public project
records get anonymous aggregate findings and fictional examples only. End with simple next steps.
```

The reviewer follows this order:

1. **Measure first.** `uv run python tools/review_search.py` reads the latest saved results in
   read-only SQLite mode. It makes no provider or job-site requests. Inspect all source messages,
   skipped/unchecked conditions, unknown dates, scoring limits, summary shares, top-10 blockers,
   per-step times and token/web usage. Separate time waiting for answers from app work. Corrections
   have new timings but cumulative usage; compare complete original searches for performance.
2. **Judge independently.** On a private scratch copy outside Git, judge full ads against the
   CV, cover letter and actual criteria **before seeing their scores**. Include the top 10 and a
   balanced 30–50-ad sample over time: good fits, near fits and blockers, across the priority
   countries. Open original pages for summaries; do not treat missing requirements as satisfied.
   The quality screen hides scores until rated. Add missing top-10 cards to the private sample
   with `quality.add`, preserving their evidence and location plan; its 50-ad limit still applies.
   Save approved labels with `quality.rate(...,
   by="assistant")` in the real private folder; never overwrite owner ratings automatically.
3. **Check ranking and stability.** Measure top-10 good/okay/poor counts and precision only when
   all 10 have independent labels. Check role, seniority, languages, permits and requirements
   separately. Use `tools/score_check.py --rescore` for a focused authorized repeat with current
   documents and the stored location plan; old plan-less samples cannot validate preferences.
   Use `--aggregate` to keep profile and job names out of tool output. Compare single versus
   batch scoring and run twice on borderline specialisations. Broad
   overlapping score bands are a diagnostic, not an accuracy claim. Where enough fully labelled
   data exists, compare ranking quality as well as absolute scores. Don't tune to a single ad.
4. **Measure misses.** Independently find 15–25 relevant, date-verified jobs, starting with Germany,
   Ireland and the UK, then the other priority countries. Store the CSV outside Git and run
   `tools/coverage_test.py` on the private copy. Verify original posting and closing dates and
   requisition identity; search-engine snippets alone cannot establish freshness. Classify each
   miss as source coverage, search words, deduplication, criteria, relevance or scoring limit.
   Report recall of this sample with its size; never call it recall of the whole job market.
5. **Improve and compare.** Fix the biggest measured issue with fictional regression cases.
   Change one scoring/collection factor at a time. Keep recall and ranking quality while reducing
   repeated requests, cost and time. Delete disposable private scratch data, update the records
   with anonymous findings, test, push and wait for CI before a merge commit.

## Wrap up a session

```text
Follow "Ending a session" in AGENTS.md. Finish at a safe point, preserve any unfinished work in
PROGRESS.md, verify and merge completed changes, remove temporary private copies and previews,
and leave the project ready for a fresh local session. Tell me what changed, what is still
unverified, and my simple next steps.
```

Contributors work on a branch and propose a PR. The assistant may merge its own tested changes
under the owner's authorization; other contributors' changes require review. Preserve Git history.
