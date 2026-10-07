# Jobcu architecture

Use this for code navigation and implementation detail. Rules: [AGENTS](../AGENTS.md).
Current tasks: [PROGRESS](PROGRESS.md). Private evaluation: [REVIEW](REVIEW.md).
Older code comments mentioning HANDOVER refer to [the archived concept](archive/HANDOVER.md).

## Search pipeline

`search.py` runs a background thread; the page polls progress once a second.
Searches and condition corrections stay running until `jobstore.finish_search` commits the
final result snapshot and search status in one transaction. Only then does the manager publish
finished, stopped or failed. A save failure reports failed, keeps results visible in the current
app session and warns that the latest results may not survive closing Jobcu; the prior saved
snapshot remains intact if the transaction rolls back. Controlled-save tests cover polling,
overlapping starts/corrections, immediate restore and storage failures without timing guesses.

1. Read documents into a profile, interpret the query into a location plan, and generate
   multilingual search words. Refresh discovered employers when due (two-week interval).
   `LocationInterpretation` reads geography and classified conditions in one medium-effort
   request. Initial interpretation and edited conditions share the same checking function;
   population rules stay local and researched facts still use the provider. Journey estimates
   record usage under `travel`, separately from `location` interpretation (older runs mix them).
2. Collect sources in parallel. Screen career titles missed by the search words, merge copies,
   and apply fixed date/type/remote/country/dismissal rules.
3. In `search._decide`, apply location conditions, quick relevance and travel limits; load full
   ads for candidates still in the running.
4. Score evidence through `ai/client.py`; `scoring.py` applies deterministic blocker limits.
5. Research candidate towns and summary requirements where supported, then reapply conditions
   and limits. Preserve uncertainty and evidence-completeness labels.
   Research includes the preferred original URL so title/company matches cannot silently
   substitute another requisition. Quota-deferred batches do not advance progress; retries and
   owner-approved continuation use the completed count from earlier rounds.
6. Build ranked cards and job memory. **Edit** reuses the saved `pool.py` jobs and earlier answers
   to apply corrected conditions without collecting sources again.

## Location and evidence

`profile.py` distinguishes completed study/placement history from sought work. Progress uses
target roles, with a clearly labelled fallback field. The guarded `DELETE /api/profile/cache`
forgets interpretations without deleting uploads/results or making AI calls; it refuses while
a search is running. The next read rebuilds the cache and normal reuse resumes.

`location.py` interprets each query afresh into explicit conditions. `places.py` supplies
coordinates, population, local names and regions as measurement data, not interpretation rules.
Population constraints are computed; other facts may need provider web research. Estimates
and unchecked conditions remain visible with sources and can be corrected through **Edit**.

Travel constraints use job-ad coordinates when available, otherwise the named town's centre.
Reference-city edges are approximated from population. `travel.route_targets` compares that
edge point and the city centre in the same Maps matrix, keeping the faster available journey;
an explicit centre request has one destination per city. These samples do not establish the
fastest journey into every district. A visible note explains that limit. The route budget counts
every destination element, including both samples. Prior single-edge Maps answers are rechecked
using a routing version; current answers still survive condition-limit edits without new calls.
`travel.py` uses Google Maps when configured, otherwise labelled AI estimates. AI estimates may
be remembered for 30 days; Google route times are not stored in the cross-search travel cache.
The key test uses named public stations rather than city-edge coordinates, makes one matrix
element within the configured limit and describes public transport/access rather than train time.

`dedupe.py` combines copies, prefers employer links and retains possible-duplicate warnings.
`freshness.py`/`jobstore.py` use original dates, closing dates and first-seen memory to identify
old reposts. Distinct requisitions must stay distinct. Summaries and clipped excerpts remain
incomplete evidence even when online research supplements their requirements.

## Project layout

The root keeps launchers, README, CONTRIBUTING, AGENTS, LICENSE and Python/tool configuration.
`src/`, `tests/` and `tools/` keep their established paths; no extra build step is required.

| Area | Modules and purpose |
|---|---|
| Startup/server | `launcher.py`, `__main__.py`, `app.py`; local server/browser and request safety. `build.py` fingerprints code to replace an older running version. |
| Local persistence | `paths.py` locates private data; `keystore.py` stores masked keys; `settings.py`/`settings_api.py` handle settings; `db.py` owns SQLite migrations; `logs.py` masks keys in private logs. |
| Documents/profile | `documents.py`, `documents_api.py`, `profile.py`; uploads, text and cached structured profiles. |
| Search coordination | `search.py`, `search_api.py`, `pipeline.py`, `pool.py`; progress, collection, decisions, cards and condition reapplication. |
| Places/criteria | `countries.py`, `location.py`, `places.py`, `placenames.py`, `travel.py`; supported geography, query interpretation and measurements. |
| Discovery | `keywords.py`, `employers.py`; multilingual words and periodically discovered employers. |
| Evidence/matching | `text.py`, `jobposting.py`, `dedupe.py`, `filters.py`, `freshness.py`, `relevance.py`, `jobplace.py`, `scoring.py`; text extraction, filtering, research and fit. |
| Results/evaluation | `jobstore.py`, `quality.py`, `quality_api.py`; remembered jobs, saved results and independent score checks. |
| `ai/` | `client.py` is the sole AI entry point; provider adapters, schemas, errors and token/web usage. |
| `sources/` | Isolated adapters and the registry. `base.py` defines `JobSource`; `http.py` applies polite requests/robots; `budget.py` tracks limits; `matching.py` matches lists; `careers.py` uses the directory; `careerlinks.py` recognizes career hosts. See [SOURCES](SOURCES.md). |
| `data/` | Public reference assets: `employers.json`, `places.csv.gz`, `regions.csv.gz`, `postcodes.csv.gz`. User data never belongs here. |
| `web/` | `index.html`, `app.js`, `style.css`, `favicon.svg`; plain UI, system fonts, no external scripts. |
| `tests/` | Scripted providers and mocked HTTP; `conftest.py` gives disposable fictional data. `test_imports.py` checks import order; `test_docs.py` checks navigation and recovery sections. |
| `docs/` | PROMPTS, PROGRESS, DECISIONS, ARCHITECTURE, SOURCES, REVIEW; `guides/` for users and `archive/` for dated background. |
| `.githooks/`, `.github/` | Commit privacy guard, issue/PR templates, Mac/Windows/privacy CI. |

## Tools

Run these from the repository root with `uv run python tools/<name>.py`.
Real-data tools require the specific authorization described in REVIEW.md.

| Tool | Purpose |
|---|---|
| `tools/check_no_secrets.py` | Privacy guard for commits and CI; `--all` scans tracked files. |
| `tools/review_search.py` | Read-only, allowlisted aggregate review of saved results; no network/AI. |
| `tools/score_check.py` | Compare scores with independent labels; focused authorized re-scoring and prompt variants. |
| `tools/coverage_test.py` | Trace a private independent benchmark through collection/filtering/scoring. |
| `tools/universality_check.py` | Fictional professions through profile, words, relevance and scoring; ESCO vocabulary checks. |
| `tools/made_up_search.py` | A full fictional search in its own data folder. Live/paid runs still need authorization. |
| `tools/check_employers.py` | Inspect directory entries and candidate career systems; live source checks need current terms. |
| `tools/update_places.py` | Rebuild public GeoNames town/region/postcode assets. |

## Evaluation data and timing

Step timers use a monotonic clock and continue across repeated progress updates. Answer-wait
is recorded separately but also included in step elapsed time. A correction has new timers
and cumulative token/web usage for its search ID. Review output labels those scopes; legacy
missing kinds/times remain unknown.

The quality set holds up to 50 scored ads and 40 excluded titles, adding at most eight of each
per search. Existing items are removed before selecting fresh ones. Samples span score bands,
full ads and summaries, retain final post-research scores and store the original location plan.
Re-scoring uses current documents and that plan. Plan-less old samples fall back to Anywhere
and cannot validate location preferences. Online requirements notes do not become full-ad text.

## Lessons

- Check terms and every host's robots rules, including API hosts. A readable page does not imply
  a permitted API. Blocked sites stay blocked; record evidence in SOURCES.
- Career systems often sit behind a separate careers link/host. Job-board employer links seldom
  identify them reliably; keep the directory and career-link recognition.
- Job memory is freshness evidence. Check original dates and requisitions before treating a
  board repost or search snippet as a new job.
- Measure whole-search coverage, not isolated adapter success. Validate words before spending
  request budgets; broad words can exhaust a source without useful ads.
- Scripted AI tests cannot establish live interpretation. Authorized real checks use a private
  scratch copy and must include other professions/wordings as well as borderline cases.
- Tell the model explicitly when it must search; memory answers are guesses. Check web-search
  usage. Reasoning consumes output allowance, so the client reserves room for it.
- Stored scores age when prompts/limits change. Use authorized re-scoring and inspect rubric
  parts; broad score bands can hide field blockers.
- Keep important explanations visible; hover-only details are easy to miss. Show incomplete
  evidence, estimates and refused research in the UI.
- Cache only what provider terms allow. Service-day quotas may reset in another timezone;
  token estimates may omit tool fees/discounts.
- Use `sources.http.RobotsRules`: longest matching rule wins (RFC 9309), unlike the standard
  library's first-rule behavior. Respect Retry-After and per-source budgets.
- Verify test exit codes; piping output through tail/grep can hide failure. CI on both systems
  catches platform/timing bugs. Check independent imports to expose cycles.
- Implement a behavior decision in the same change as its record. The guard can flag public
  IDs; allow one only when clearly non-secret, with an explanatory `jobcu-guard: allow` comment.
