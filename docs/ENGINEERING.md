# Jobcu engineering

Current decisions, implementation and tools in one reference. Read the section needed for the
work. Rules: [AGENTS](../AGENTS.md); current work: [PROGRESS](PROGRESS.md); source permissions
and dated evidence: [SOURCES](SOURCES.md); development and private evaluation:
[CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).
Historical reasons remain in the [decision history](archive/DECISION-HISTORY.md).
Code/tests establish behavior; the latest current decision establishes intent.

## Current decisions

### Search behavior

| Decision | Reason and date |
|---|---|
| Reject career titles only when explicitly classified as clearly unrelated. Keep unreviewed titles for normal matching; preserve independent batch decisions and stop on critical account/quota/monthly-limit errors. Retain raw source counts and private rejection evidence. | Fictional searches reproduced unseen late titles disappearing, a bad batch erasing healthy decisions, and matching continuing after a limit error. Supersedes dropping all titles beyond the 3,000-pair early-screen bound or after a failed screen. The request bound remains; later matching of unknowns may use more AI, subject to existing limits (2026-10-08). |
| Read documents into a structured profile; reuse it only while documents, prompt and model are unchanged. Never reuse job scores. | Save repeated document work while keeping each search's judgement fresh (2026-09-17). |
| Show sought roles in profile progress; label the most recent role as history. Offer **Reset document understanding** to forget cached profiles and read again on the next search. | Completed study or placement work must not look like a requested role. Reset costs no AI calls itself, keeps documents/results, and preserves default reuse (2026-10-07). |
| Interpret each new query afresh. Conditions can name places, population, travel limits or researched facts; label estimates and unchecked conditions. | People's wording and intentions differ; no personal query is hard-coded (2026-09-17 to 2026-09-24). |
| Interpret countries, places and condition types together in one medium-effort request; apply the existing population, travel and research checks afterwards. | Avoid asking the AI to read and classify the same request twice. Fictional country/commute/nursing checks verify preserved conditions; live speed and interpretation still need measurement (2026-10-07). |
| **Edit** reapplies corrected conditions to the same job pool and reuses earlier evidence. | Correct interpretation without collecting every ad again (2026-09-17; implemented 2026-09-21). |
| Report completion only after final results and status are saved together. If saving fails, keep available results visible and explain that closing Jobcu may lose them. | A finished heading must mean the latest results can be restored; a controlled fictional test reproduced completion preceding persistence after the Windows CI restore failure (2026-10-07). |
| Measure travel to the nearest edge of a reference place unless the user asks for its centre. | The person could live anywhere in the place (2026-09-24). |
| For Maps journeys into a reference city, compare the calculated edge point and city centre, keeping the faster available journey. Explicit centre requests still measure the centre alone; explain that sampling can miss faster districts. | A geometric edge can have a worse connection than the centre. Fictional regressions reproduce a reachable job rejected by an edge-only journey. This clarifies the anywhere-in-the-place intent above without claiming an exact fastest commute (2026-10-07). |
| Preserve confidence in facts about reference places separately from journey confidence. Keep usable partial rules, but explain missing facts and label estimates on each card. | A fictional city-library condition reproduced a measured journey upgrading unverified library access to verified. Distance, limit edits and Maps cannot prove that fact; scores and filtering remain unchanged (2026-10-08). |
| Prefer original employer ads and full descriptions. Keep summary evidence and missing conditions labelled. | Missing text must not appear to be complete evidence (2026-09-17; clarified 2026-10-06). |
| Reuse bounded-age full text across matched copies before live reads; then prefer employer originals and try other permitted matched copies if needed. Recheck revealed objective facts before scoring. | A first-copy failure does not prove full evidence is unavailable; scores remain fresh per search (2026-10-08). |
| Exclude known CV-Library application destinations. Keep the same vacancy with another already-matched link, preferably the employer; otherwise exclude it with a counted reason. Preserve saved/applied history and original snapshots. | The owner reports that the application form rejects contact details from outside the UK. This is an explicit destination exclusion, not proof that every alternate platform accepts every applicant. Opaque redirect destinations still need verification (owner, 2026-10-07). |
| Let the person exclude an exact saved application link and undo that choice locally. Reuse an already-matched alternative or count the vacancy as left out before further matching. Keep other links on that site available. | Opaque redirects cannot establish their final host. A local report handles an observed unusable link without probing blocked pages, guessing URLs or classifying unrelated vacancies. No automatic final-host verification is claimed (2026-10-07). |
| Full-ad requirements replace earlier summary requirements, including an unstated experience minimum. Keep other blockers intact. | A fictional regression confirms that retaining the summary's years when the full ad says none leaves an obsolete score limit (2026-10-07). |
| Use original posting/closing dates and job memory to suppress expired ads and old reposts. Keep distinct requisitions distinct. | A board's refreshed date is not a new vacancy (2026-09-24; fixes 2026-10-03). |
| Prefer exact source IDs in job memory. Distinct IDs on the same employer source stay separate, including through other copies. Require similar text when both matching ads are complete. Keep ambiguous name matches as separate jobs; preserve all historical keys, marks and snapshots. | Fictional electronics, nursing and hospitality openings reproduced a fresh vacancy inheriting an old date or Not interested mark. Titles and templates do not establish a unique vacancy. Previously merged history cannot be automatically split without evidence (2026-10-07). |
| Groups kept separate by duplicate checks cannot rejoin solely through remembered names in the same batch. Exact copy evidence still wins; known countries can disambiguate. | The former one-card heuristic for two vague agency summaries could silently share Save/Not interested state without vacancy evidence. Supersedes that title-only assumption while retaining one card for proven copies (2026-10-08). |
| Explain scores with rubric parts and deterministic blocker limits; retain low-score jobs. | Users can see why a job ranks where it does; a score is not hiring probability (2026-09-23 to 2026-09-30). |
| Default to no per-search scoring or AI web-check cap. Preserve explicitly saved caps; if selected, ask before exceeding them and let **Always** remove them. Monthly controls and source/provider request rules still apply. | A normal on-demand search should complete its work without arbitrary pauses. Optional user controls remain available; supersedes the 200-score/50-web-check defaults (owner, 2026-10-07). |
| Count attempted online checks cumulatively; deferred jobs remain pending when a limit is reached. Supply the original URL to research the same vacancy. | Fictional regressions reproduce the counter moving backwards on continuation. Titles alone can identify different requisitions (2026-10-07). |
| New installs use a **24-hour posting lookback**; preserve existing saved choices. The owner chooses daily 24-hour searches. | Support earlier applications with daily on-demand use (owner, 2026-10-07). Supersedes the 72-hour first-evaluation default of 2026-10-06; wider windows remain available. |

### Setup and provider behavior

| Decision | Reason and date |
|---|---|
| Search requires AI configuration, CV and cover letter; first-run guidance links to each. | Make the route to a first search complete (2026-10-06). |
| The finished app completes each on-demand search without assistant supervision. During development, the assistant owns implementation, review and measured improvements; the owner chooses when to search. | Development oversight must not become a requirement for everyday use or automatic background operation (owner, 2026-10-07). |
| When a launcher has no Git metadata, show manual ZIP-update steps before preparing Jobcu. Skip the reminder during self-tests. | ZIP copies otherwise start silently without explaining how to receive fixes. The reminder uses no network and does not claim a newer version exists; Git-copy updates stay unchanged (2026-10-08). |
| Share job-source rate-limit/service cooldowns per host within a search; honor integer and HTTP-date Retry-After values without shortening them. Keep waiting readers cancellable and recognized blocked hosts stopped for that client. | Fictional requests reproduced a 600-second delay shortened to 120 seconds and four attempts at a CAPTCHA response. Independent hosts and collected ads are preserved; no live availability/recall gain is established. Protocol evidence is in SOURCES (2026-10-08). |
| The Maps key test uses named stations, says public transport, shows the weekday-morning departure assumption and explains that it checks access. Count it against the local route limit. | General TRANSIT includes walking and other modes; a successful sample must not be presented as a train-only timetable or overall accuracy check (2026-10-07). |
| A successful connection test checks ordinary generation, not web-research access. Definite research refusals explain once and skip that research for one search. | Account/model capability can differ from basic generation; preserve collection/scoring and show uncertainty (2026-10-06). |
| Retry research on a later search; never mark a refused employer lookup as a successful refresh. | A temporary restriction must not suppress future employer discovery (2026-10-06). |
| Keep guides provider-neutral and link to current provider instructions/prices. Remove fixed model recommendations and unmeasured cost/runtime promises. | Capabilities and charges change; the restored Mac has no measured search baseline yet (2026-10-07). This supersedes the guide's 2026-10-03 provider recommendation. |
| Write everyday guides for first-time users: explain terms, give one clear action per step, name the actual controls and say how to confirm success. Put optional setup after the basic route; keep owner/Codex review instructions in their project documents. | Friends using Jobcu may have little technical experience. Plain language needs enough explanation to complete a task, rather than the shortest possible text (owner, 2026-10-07). |
| Keep concrete examples of richer place requests in README and the usage guide, including election vote shares, Turkish supermarkets, Sunday opening, student populations and combined commute conditions. Define thresholds and label research limits. | The examples help users understand the range of requests they can make; simplifying the guides should preserve them without claiming unmeasured accuracy (owner, 2026-10-07). |

### Evaluation

| Decision | Reason and date |
|---|---|
| Sample full ads and labelled summaries across score bands; keep final scores, evidence completeness and the original location plan. | Avoid bias from summary omissions, duplicate-first selection or pre-research scores (2026-10-06). |
| Judge every top card independently before reporting precision; use a date-verified independent list before reporting coverage recall. | Counts and broad score bands do not prove search quality (2026-10-06). Procedure: [private review](../CONTRIBUTING.md#review-a-completed-search). |
| Focused paid reviews follow the owner's existing monthly budget and configured service limits, with current verified prices. No fixed EUR1 review allowance or per-search money cap is imposed. | The earlier review prompt's EUR1 permission applied only to development review, never ordinary searches. The owner removed that restriction; a session-ending instruction still stops new paid work (2026-10-07). |
| Assistant ratings may fill empty labels or revise prior assistant labels; owner and legacy labels are protected atomically. | A concurrent owner edit must not be overwritten by a review. Fictional controlled-order tests cover the read/write gap (2026-10-07). |
| Record step time and answer-wait time; label correction timings separately from cumulative usage. | Corrections and full searches cannot be compared as equivalent performance runs (2026-10-06). |
| Warn when scoring reads only an excerpt of a lengthy ad. | Unseen requirements must not be assumed satisfied (2026-10-06). |

### Project organization — 2026-10-08

- Keep current decisions and implementation/tool knowledge in this engineering reference.
  Keep the private review procedure with developer instructions in CONTRIBUTING. This
  supersedes separate DECISIONS, ARCHITECTURE and REVIEW files: the owner wants fewer places
  to look, without losing the setup, usage, contribution or evaluation detail.
- Keep one complete prompt per task in PROMPTS. The short loader introduced on 2026-10-08
  saved copying but added a choice and indirection; the owner prefers a single pasteable block.
- PROGRESS holds current state, one active goal, pending checks and next actions. Completed
  details belong in Git/PRs; dated source permissions belong in SOURCES. Standing rules stay
  in AGENTS. Link to the relevant section rather than repeat the same procedure.
- Preserve detailed human guides, licensing and historical records in the archive. Keep the
  established runtime/test/tool layout; consolidate only where responsibilities actually overlap.
  Retire merged branches after checking PRs/worktrees; preserve unmerged or active work.

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
   An unusable combined answer falls back to the simpler geography/classification route.
   Authentication, quota and spending-limit failures propagate without fallback calls.
2. Collect sources in parallel. Screen career titles missed by the search words, merge copies,
   and apply fixed date/type/remote/country/dismissal rules.
   Title screening returns only explicitly unrelated IDs. Its 3,000-pair preliminary bound
   limits requests, not recall: unseen titles and independent failed batches remain for normal
   matching. Successful batch decisions survive recoverable errors; critical account/model/
   quota/spending errors and Stop propagate without later matching calls. Batch callbacks
   check Stop before starting a request; already-running requests may finish.
   Source Ads found counts stay as collected. `result.career_titles` records reviewed,
   unreviewed and rejected outcomes; rejected ads remain in the private snapshot and bounded
   title-only Score check sample. Search details separates this gate from duplicate removal.
   Legacy snapshots retain their original post-screen counts and lack rejected-title evidence;
   do not infer retrospective rejection counts or compare them as raw collection measurements.
3. In `search._decide`, apply location conditions, quick relevance and travel limits; load full
   ads for candidates still in the running. Check every matched copy's existing three-day text
   cache first; if no complete nonempty text is available, prefer the employer and try available
   adapters in rounds until one supplies it. Keep each source serial while independent sources
   run together. No unrelated vacancy or new endpoint is fetched. Reject mismatched identities,
   preserve richer summaries after incomplete responses, and isolate failed adapter mutations.
   Cache failures cannot discard successfully recovered text. Stop prevents later rounds.
   A career reader created for corrections without `search()` also retains the normal request
   budget, carrying forward that saved search's reported requests; reaching it is reported as
   partial. Internal HTTP retry accounting is a separate lead.
   Recheck original/closing dates, stated countries, job types, remote status and application
   routes before scoring. Conflicting copies still follow the existing conservative free rules.
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
Reference-place research confidence is saved separately in `Anchor.research_status` and
survives route measurement and limit edits. A passing journey cannot verify an unchecked city
fact. Cards retain usable partial rules, explain the uncertainty and label estimated journeys
per job; a checked route is not downgraded merely because another job used an estimate.
Older plans with research notes but no saved confidence are treated conservatively on rebuild;
historical result snapshots are preserved.

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
Different IDs from one employer source cannot share a group, even through a board copy.
Complete descriptions across a proposed merged group must be similar; a summary cannot
bridge conflicting full ads. An exact source ID can identify a revised ad despite changed
text. Empty source IDs establish no exact match.
Text comparison prepares each distinct description once in a per-call cache, shared with
agency-repeat checks. The cache is discarded after grouping; scores are never cached.
`applications.py` removes known CV-Library destinations, including exposed redirect targets,
and selects another already-matched copy. With no alternative, the free filter excludes the
vacancy before scoring. Restored recommendations are filtered on a response copy; saved/applied
history retains its state with blocked links disabled. Original snapshots remain unchanged.
Opaque aggregator IDs do not reveal the final application host. Migration 12 stores exact
saved links the person marks unusable, with guarded reporting and undo APIs in `search_api.py`.
The page's **Application link problem** control offers only that vacancy's saved links;
**Excluded links** keeps undo available after a card disappears or a later search finishes.
Reports never fetch links, change scores/ratings/marks or rewrite original snapshots. Matching
reads the report set once per filter/build stage, rather than opening SQLite for every vacancy.
Only an identical URL is remembered: a changed tracking URL requires a new report. Other links
on the same site stay available. An opaque alternate is not proof of another final destination.
Automatic destination verification remains unfinished, and a different allowed link does not
prove universal registration access.
`freshness.py`/`jobstore.py` use original dates, closing dates and first-seen memory to identify
old reposts. An older copy with the exact same source ID still dates a redated copy on that
site; another employer requisition stays separate. `jobidentity.py` gives exact source IDs
priority over name matches and rejects conflicting employer IDs or known country conflicts.
Migration 13 preserves `job_keys` and copies legacy name keys to a non-unique candidate index;
names can refer to several vacancies. An ambiguous name match cannot inherit old marks/dates.
Separate current groups sharing a name/location cannot silently rejoin through job memory;
known countries can disambiguate, and an exact copy still takes priority. Name preparation is
reused within that transaction; a known-copy-only lookup needs no name processing.
Known copies use bounded batch lookups; states and first-seen reads use the device's SQLite
parameter limit too. Within one save, new aliases are registered for subsequent groups and
allocation is serialized and all writes commit atomically. Historical merged identities
and snapshots remain unchanged;
unknown legacy country metadata cannot prove a conflict. Summaries and clipped excerpts remain
incomplete evidence even when online research supplements their requirements.

Online requirements replace the summary's languages and minimum years, including null when
the full ad states no minimum. Retaining an earlier years value would leave a stale experience
limit in the total. Other confirmed blockers survive this replacement; rubric parts are not
retuned. Fictional engineering and hospitality checks cover clearing the limit and retaining
an unrelated doctorate blocker.

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
| Results/evaluation | `applications.py`, `jobidentity.py`, `jobstore.py`, `quality.py`, `quality_api.py`; application routes, remembered jobs, saved results and independent score checks. |
| `ai/` | `client.py` is the sole AI entry point; provider adapters, schemas, errors and token/web usage. |
| `sources/` | Isolated adapters and the registry. `base.py` defines `JobSource`; `http.py` applies polite requests/robots; `budget.py` tracks limits; `matching.py` matches lists; `careers.py` uses the directory; `careerlinks.py` recognizes career hosts. See [SOURCES](SOURCES.md). |
| `data/` | Public reference assets: `employers.json`, `places.csv.gz`, `regions.csv.gz`, `postcodes.csv.gz`. User data never belongs here. |
| `web/` | `index.html`, `app.js`, `style.css`, `favicon.svg`; plain UI, system fonts, no external scripts. |
| `tests/` | Scripted providers and mocked HTTP; `conftest.py` gives disposable fictional data. `test_imports.py` checks import order; `test_docs.py` checks navigation and recovery sections. |
| `docs/` | PROMPTS, PROGRESS, ENGINEERING, SOURCES; `guides/` for users and `archive/` for dated background. |
| `.githooks/`, `.github/` | Commit privacy guard, issue/PR templates, Mac/Windows/privacy CI. |

## Source reliability

### Fictional full-ad recovery comparison — 2026-10-08

Public API/evidence findings live in [SOURCES](SOURCES.md#full-ad-evidence-and-existing-detail-apis).
The first-eligible-copy rule is superseded: it could stop at a summary or failure although a
second matched copy supplied full evidence. A no-network comparison against `76f405f` used
fictional ads, stub readers and separate disposable databases:

| Two matched copies | Before | After | Evidence retained |
|---|---|---|---|
| First stays a summary, second has full requirements | 1 reader call; summary only | 2 calls; full text | Same vacancy/copy identities |
| Second already has a valid full-text cache entry | 1 unnecessary live-reader call | 0 reader calls | Same full requirements |
| Neither can supply full text | 1 call; summary | 2 calls; summary | Job retained with incomplete label |

These count stub reader invocations, not HTTP retry attempts or live latency. Additional reads
deliberately seek missing evidence within existing limits. A slow source can delay later rounds;
these results do not promise an end-to-end speed or recall gain. Existing text expiry is unchanged
and cannot prove an ad has not been revised within that window; no previous score is reused.
Fictional power-electronics and nursing searches verify that recovered eight-year requirements
reach scoring and its explanation, and a second search uses cached text with a fresh judgement.
Cached/live detail cases verify that known old/closed/wrong-country/unticked-type/remote jobs
do not reach scoring. Failure, Stop, budget, identity/marks, expiry and serialization checks use
no owner inputs, real sources or providers. Independent live quality remains unverified.

### Fictional cooldown comparison — 2026-10-08

`tests/test_source_cooldowns.py` uses mocked HTTP and controlled clocks/events. It preserves
successful full-ad responses and cached answers while exercising 429/503 recovery, parallel
readers, later deadline extensions, terminal failures, malformed/date headers and Stop.

| Fictional failure | Before | After |
|---|---|---|
| Source asks for 600 seconds | Retry after 120 seconds | Retry after the full 600 seconds |
| 429 asks for a future HTTP date | Date ignored; ordinary 5-second backoff | Date-derived delay honored |
| 429 contains a recognized CAPTCHA | Four requests before blocking | One request; later readers blocked in that client |
| Stop during a 600-second delay | Sleep cannot observe Stop | Waiting reader stops after one 0.2-second simulated polling step; no retry |

These are protocol/request-order measurements, not live latency or market recall. Longer
source delays deliberately make that source take longer; independent hosts continue and
already collected ads survive cancellation. An active network request may finish before Stop
completes. Cooldown/block state is scoped to the current HTTP client; it does not establish
account-wide or cross-process enforcement. Normal retry counts and source budgets are unchanged.

### Research leads requiring their own verified goal

The 2026-10-08 pipeline inspection found that local place matching returns false for unresolved
named places despite its keep-unknown contract. This needs a focused fictional reproduction
and review before implementation. Full-ad fallback is resolved above; location checks made
before full text arrives still need a focused audit of newly revealed place evidence.
Request budgets are charged by adapters before the HTTP client, whose
internal retries need a separate attempt-accounting audit. Provider retry/date handling and
redirect-specific delays also need their own scope; the source change above does not validate
them. New permitted sources and multilingual vocabulary still require date-verified coverage
evidence; neither public documentation nor counts establish a recall gain.

## Tools

Run these from the repository root with `uv run python tools/<name>.py`.
Real-data tools follow [CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).

| Tool | Purpose |
|---|---|
| `tools/check_no_secrets.py` | Privacy guard for commits and CI; `--all` scans tracked files. |
| `tools/benchmark_local_matching.py` | Fictional local identity/deduplication comparison against a Git baseline; no saved user data, network or provider calls. |
| `tools/review_search.py` | Read-only, allowlisted aggregate review of saved results; no network/AI. |
| `tools/score_check.py` | Compare scores with independent labels; focused authorized re-scoring and prompt variants. |
| `tools/coverage_test.py` | Trace a private independent benchmark through collection/filtering/scoring. |
| `tools/universality_check.py` | Fictional professions through profile, words, relevance and scoring; ESCO vocabulary checks. |
| `tools/made_up_search.py` | A full fictional search in its own data folder. Live/paid runs still need authorization. |
| `tools/check_employers.py` | Inspect directory entries and candidate career systems; live source checks need current terms. |
| `tools/update_places.py` | Rebuild public GeoNames town/region/postcode assets. |

### Fictional local comparison — 2026-10-08

Run `uv run python tools/benchmark_local_matching.py --baseline 61b133d` from a Git checkout.
The tool uses a disposable database outside Git and prints aggregate counts/times only.
It checks identical identities/group membership before timing; it never reads configured user
data or calls sources/providers. Privacy regressions cover normal completion and failure.

On the Mac, five warmed rounds produced these medians:

| Fictional work | Before | After | Preserved output |
|---|---|---|---|
| Look up 1,000 known job copies | 10.370 ms; 1,000 identity SELECTs | 2.983 ms; 2 identity SELECTs | Every job ID, including order |
| Compare 40 distinct full recruitment ads | 368.320 ms; 1,560 text preparations | 16.020 ms; 40 preparations | 40 distinct groups |

The ad fixture uses disjoint repeated text to exercise repeated comparison. Timings depend on
the device and fixture. Live end-to-end speed, ranking quality and market recall still require
the authorized real evaluation in [private review](../CONTRIBUTING.md#review-a-completed-search); this comparison makes no claims about them.

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

`quality.rate(..., by="assistant")` updates only unrated items or prior assistant labels. Its
ownership condition is in the SQL UPDATE, so owner and legacy labels survive even an edit
between the assistant's read and write. The owner can still revise any label through Jobcu.

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
