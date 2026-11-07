# Jobcu architecture

Current implementation reference. Source permissions and dated protocol evidence are in
[SOURCES](SOURCES.md); setup and checks are in [CONTRIBUTING](../CONTRIBUTING.md).
Code and tests define behavior. Historical discussions and completed changes remain in Git.

## Runtime and persistence

`launcher.py` runs a FastAPI server on 127.0.0.1 and opens the plain HTML/CSS/JavaScript UI.
`build.py` binds the loaded build fingerprint at import, so an old process cannot identify
itself as a newly edited checkout. State-changing routes require `X-Jobcu: 1`; CSP and local
binding constrain browser access.

`paths.py` locates private data outside every checkout. SQLite migrations are additive and
numbered; `db.py` currently includes migration 22. Keys, settings, uploaded documents, logs,
reviews and capture files stay private. Reset actions are explicit, scoped and protect usage
counters, settings and keys. Secure deletion/compaction is app-file behavior, not a promise
about SSD snapshots or external backups.

## Search pipeline

`search.py` coordinates background work; the UI polls progress. Budget/capture admission
happens before a new search is created or source collection begins, including with cached setup.

1. Parse documents into a profile, interpret geography/conditions, generate multilingual
   search words, and refresh discovered employers when due.
2. Collect independent sources in parallel. Career-title screening rejects only explicitly
   unrelated titles; unseen titles survive its preliminary request bound. Merge proven copies
   and apply date, type, remote, country and dismissal rules before full-ad loading. A job
   leaves for its type only when the employer's own career system or the ad text says so (a
   job site's tag alone can keep a job, never remove it), and as remote only when no copy
   names an office among its places (`filters.leaves_for_job_type`, `filters.fully_remote`).
3. Apply location conditions and quick relevance. Recover full ads from matched copies, using
   the bounded-age text cache first, preferring permitted employer originals and retaining
   richer summaries after failed/incomplete reads. Recheck newly revealed objective facts.
4. Check fit, workplaces, requirements and travel; use sourced research where supported.
   `requirements.py` validates ad/profile evidence; `scoring.py` applies deterministic limits.
   The profile states work rights per country once (now, and whether they last); scoring only
   reads an ad's right-to-work clause and code compares the two (`scoring.work_right`).
   Validated batch outcomes survive failures in later batches.
5. Build ranked cards and job memory. `jobstore.finish_search` commits status and the final
   snapshot together. Failed/stopped attempts retain available raw candidates and reports even
   before ranked cards exist. A save failure remains visible and preserves prior saved data.
   The result lists of the last 90 searches are kept; older ones are deleted only when a new
   search starts (`jobstore.make_room_for_a_new_search`), so the latest list stays until then.
   Job memory, saved cards and the person's marks are never deleted this way.

The duplicate-removal, full-ad, location, scoring and online-check stages have distinct progress
states. An interrupted stage differs from an unstarted stage. Source retries are summarized
per host while private diagnostics retain individual waits. A source's final report determines
whether its collection was partial.

**Edit** reapplies corrected conditions to a saved pool without collecting all sources again.
Explicit continuation retains an interrupted search's identity, window, inputs and completed
work. Missing details can still need permitted source reads; incomplete AI work uses current
settings/limits. An uncaptured search does not gain a retroactive capture. Continuation timings
cover that continuation, while usage is cumulative.

## Evidence, identity and scoring

- Original full ads are preferred. Summaries, clipped text, unknown dates and unchecked
  requirements remain labelled; absence of a requirement is not evidence it is satisfied.
- Duplicate identity uses source/requisition identifiers and supporting evidence. Distinct
  requisitions remain separate despite similar names/templates. Ambiguous copies cannot share
  saved/applied/dismissed state solely through title similarity.
- Original publication/closing dates and job memory distinguish fresh jobs from reposts. A job an
  earlier search showed with its score and a checked place is left out ("Shown in an earlier
  search already"), whatever its date: a date later than that showing is the same job dated
  again, and daily searches started at different times share part of their windows. A job listed
  only while its place was still being checked, or without a score, is judged again when it
  comes back (`jobstore.first_assessed`), so an unfinished check never hides a job for good. "Posted within" is strict: an ad dated before the window is
  too old, also from sites that list ads days late (they look further back only to find
  reposts). A job Jobcu showed at least a week before and really posted again inside the window
  is assessed again like a new job (today's ad, places, links and score) and listed with a
  "Reposted" label, when its earlier score was at least 55 and the person hasn't applied or
  marked it Not interested (`search._reposts_to_assess`). Saved results follow the same rules when
  opened.
  Modification timestamps and sitemap lastmod do not establish an original posting date.
- Full-ad facts replace unsupported summary assumptions. Grounded mandatory requirements and
  known blockers constrain scores; unknowns remain explicit. A years-of-experience limit needs
  the ad's own words stating an amount (`scoring.years_stated`): "strong experience" is none;
  a number from an online look-up needs such words in its own notes (`scoring.years_grounded`). Low-scoring jobs are retained.
  Scores express fit under the rubric, not hiring probability.
- The role part grades closeness to the person's own specialist field (their technical areas),
  not only to their discipline: application or test work in that field is the same kind of role
  with a gap, the same work for another specialisation is a related job. An entry route (an ad
  that explicitly hires juniors or recent graduates, or a structured graduate or trainee
  programme) counts the discipline instead for an early-career person, since the employer
  teaches the specialisation; sales, other professions, technician, field-service and
  apprenticeship or internship roles are not lifted (`scoring.ROLE_RULES`).
- Matched employer-original application links are preferred. Explicit unusable-link exclusions
  can use another verified copy; opaque redirect destinations are not guessed or bypassed.
- Direct links: the employer's own page (an employer source's page, a supplied employer address, a
  page of an employer's application system, or the employer's posting found online) is marked
  `direct` and opens as it is. A good job (60 or more) whose links all lead through job sites gets
  the employer's page of that vacancy looked up online during the search (`livepostings.py`;
  never another job site or a careers index; no job link is visited).
- A click on another site's link reads that one page and sends the browser straight to its single,
  clear apply link on another site, skipping sites that only repeat an ad. Searches never do this:
  those links can be paid per click. Sites that forbid reading or refuse it keep their link, and
  so does anything unclear: a way on into another ad-repeating site, or a same-site address with
  a query (it can carry a token made for Jobcu's visit; trabajo.org's opened a blank page)
  (`applylink.py`). A page that plainly can't take the application (gone, 404/410; taking
  applications only from people elsewhere; or only through CV-Library) is explained instead, with
  a web search for the job. Only a CV-Library route leaves the list (marked unusable like one the
  person reports): a job is never dropped unless it is certainly dead or CV-Library.
- CV-Library links never count as a job's link. Pages that take applications only from visitors
  in the UK (Learn4Good's UK pages: a limit of the site, not the job) come last; for a good job
  with nothing better, the person's AI looks for the employer's own posting online, kept only when
  the provider's web sources list it and it isn't a site that only repeats other sites' ads
  (`livepostings.py`), and the card adds a web search for it.
- The job memory knows a job by its source IDs, then by employer, title and town (the town its
  location names, whatever the wording). When several remembered jobs share that name, none is
  chosen and no saved state is shared, but the job counts as shown before if one of them was
  shown with its score.
- Saved owner/legacy ratings are protected from automatic replacement. Optional review results
  are stored separately from production scores.

## Locations and travel

`location.py` interprets geography and classifies conditions. `places.py`, `placenames.py` and
public GeoNames assets resolve places/postcodes. Districts and similarly named towns are not
interchangeable. Villages (`villages.csv.gz`) count only when a piece of a job's location is their
whole name, are never reference places, and a name several far-apart places share is left out.
Job-specific workplace evidence can contain multiple alternatives.

Reference-place facts and journey confidence remain separate. Research requires relevant
sources, supported quotes, the correct geographic scope and comparable units. Local CSV
calculation preserves original rows/provenance. Missing or inconsistent facts stay unchecked.
Reviewed reference sets match the exact interpreted fact, or the unchanged request they were
reviewed for when it holds exactly one looked-up reference fact, so a different provider's
wording keeps them; edited plans use exact matching only. A table row printed in the indented
block under a city's reviewed label (such as a city total after its constituency rows) counts as
that city's only when the quoted row appears nowhere else on the page.

Screening sees the person's education, seniority and unticked job types: clearly
lower-qualification roles and titles that are only an unwanted job type are left out before
scoring. Seniority differences within a profession still reach careful scoring.

Travel can use Maps or labelled AI estimates. Unless a city centre is explicitly requested,
public transport asks for the main station nearest the job (`data/stations.csv`; the centre where
none is listed), then, within twice the limit, the calculated edge and next main station, then,
within 1.5 times the limit, the best two of those at two later departures. Other modes sample the
edge and centre. The fastest usable route counts; this is not the fastest possible journey from
every district. Google's transit duration holds no wait for the first vehicle, but it is the
journey arriving first after the time asked, so a slow one can hide a fast one. Failed/incomplete
samples are not proven no-route results. Attempted matrix elements count before each request, including
retries. Cached/earlier routes survive later failures; persistent quotas stop the affected path.

## AI providers, usage and recovery

`ai/client.py` is the sole AI entry point. Native adapters support Anthropic, Google, OpenAI
and Xiaomi. Custom endpoints support Chat Completions, Responses and Messages with explicit
reasoning controls; hosted research is separately configured. OpenRouter is its own choice: the
Chat Completions adapter at OpenRouter's address with the selected effort, sent as its documented
`reasoning` object, so it needs only a key and model. Requests through a router (OpenRouter) ask only for hosts that neither keep nor train on request data and that honour
every requested parameter; without a schema-capable host they fall back to plain JSON, never
to a looser data policy. Some hosts serve a JSON format with reasoning off while accepting the
request: a router answer that reports no reasoning is asked again with the format in the prompt
only, which is kept for that model if it reasons there. `model@host` pins one serving host without fallback. Defaults remain medium. A provider without a literal medium control
exposes its mapping/uncertainty rather than silently disabling thinking. Native keys stay on
their native host.

Google Flex is an explicit choice for the same Gemini model at half the token price.
A request Google refuses for capacity before accepting work (a 503 "high demand", or in background
mode an interaction that fails at once without generating anything) is retried with backoff (30 s,
then 60 s) and then sent at the normal tier. Flex work Google accepts and then stops without an
answer (cancelled, failed after part of the work, e.g. a web look-up after some searches, or
"not found") goes once at the normal tier, and what the stopped part used is recorded as of unknown
cost; otherwise one stopped look-up would read as an outage after paid searches and stop every
later online check of the search. Other failures around accepted Flex work (a lost connection while
waiting) follow the normal retry rules. Repeated Flex failures end Flex for that search.
Usage records the served tier as `<model> (flex)`, priced at half the normal row unless a Flex
row exists. Connection tests use the normal tier. Flex runs only with request recovery: a
preempted Flex stream is otherwise an ambiguous dropped connection.

An optional monthly free-search allowance (`limits.free_web_searches`) gives each search a
share of the research provider's free searches left in its billing month (Pacific time for
Google), spread over the remaining days at the person's searches per day; past the share Jobcu
asks before more look-ups, like the per-search limit, and the smaller of the two applies.

Native Anthropic requests stream and use only the final message: a streamed answer starts at
once, where a silent plain request was cut by a network idle limit at 60 s. A broken stream keeps
its reported usage as a lower bound; an error event inside a started stream is classified by its
error type, and an unreadable stream is invalid output, not a bad request. OpenAI (Responses)
and OpenRouter (Chat Completions) requests stream the same way; their usage arrives with the
final event, so a stream that breaks after it began is recorded as work with an unknown bill.
Other API addresses keep plain requests: a service's streams are not assumed to report usage.

Structured answers require completion/refusal checks and schema validation. Research additionally
retains provider source annotations and validates required evidence. Generated URLs are not
provider citations. Missing passage mappings do not become invented quote provenance. A research
answer without any usable source (`AIUnsourcedAnswer`: the provider's searches brought back no
pages) is asked once more, both attempts billed; a second one leaves that check unchecked.

`ai/usage.py` retains available token/tool receipts on successful and failed calls. Unknown
usage is not zero; local prices omit some provider fees/discounts and are not invoices.
Ordinary monthly usage excludes explicitly tagged extra-allowance receipts while the combined
view remains available. `ai/budgets.py` reads private explicit allowance records, preserving
opening spend, currency/multiplier, historical uncertainty and a receipt cutoff. New charges
increase the same allowance across restarts, month changes and search deletion. Exact prepared
inputs select an automatic allowance; explicit client scope supports authorized isolated work.

One ad must never fail a search. A batch over job ads that is refused, cut off or malformed
(`ai.base.ONE_ANSWER_PROBLEMS`) is asked again in smaller parts: scoring job by job, the quick
check in halves. A job that fails alone stays in the search, unscored or unchecked, never
dropped; online look-ups, title screening, travel estimates and re-checks lose only that answer.

Retry behavior distinguishes transport/rate-limit failures from authentication, account and
spending refusals. Retry-After and bounded waits apply. Ambiguous generation failures do not
trigger automatic paid repetition. Stop cancels queued work/waits; an already dispatched
synchronous request can finish first. Completed answers and receipts are retained.

Optional Google background recovery creates one provider operation and retrieves that same ID.
`ai/request_recovery.py` journals attribution locally. A request still being polled refreshes its
heartbeat; another Jobcu process (a tool, a second window, a restart) cleans up only requests that
are finished or nobody polled for 10 minutes, never a running search's. Cancellation/deletion is attempted on
Stop/completion, with startup cleanup for outstanding operations. Unknown cancellation blocks
new generation. Cumulative receipts update the original usage row instead of double charging.
This option uses temporary provider storage and requires explicit consent; default requests
remain stateless. Failed deletion can leave normal provider retention in effect.

## Reuse and capture

Profiles are cached against document/prompt/model identity. `preparation.py` reuses successful
location readings and search-word groups for up to 30 days only when exact inputs, prompts,
schemas, provider/model/host and reasoning settings match. A city's verified comparison over
reviewed reference pages (`reference_sources.py`) is reused the same way while that city's own
evidence reads exactly the same. Any verified, sourced city fact (`reference_places.py`) is
also kept by the person's request (or, after an edit, the fact itself) and the city, whichever
AI and wording established it: used for 90 days without another look-up, and after that still
used for up to a year when a new check can't establish the city. A reviewed place-evidence set
can decide a fact for all cities of a country (`country_decisions`). Unknown verdicts are never
kept; completed research that left a city unknown is not bought again by ordinary searches for
30 days through the same AI route, while an explicit retry or edit looks again at once. The AI's
travel estimates are remembered for 90 days per place, destination and way of travelling.
Google's travel times are kept only when the person chooses (`maps_memory_days`; the owner: 90)
for exactly the same origin and destination points; Settings says that Google's Routes terms
allow keeping only coordinates. Free monthly allowances (Adzuna, JSearch, free web searches, the
Maps route limit) are divided equally over the planned search days still to come
(`budget.share`; a 72-hour search counts as three days). Paid limits (monthly AI cost and
tokens, web searches past the free ones, Maps past its limit) stop by default or only tell
(`paid_limits`, the owner's choice). A search's share of the free web searches holds either way:
past it the search asks before more look-ups, with their price, and goes on without them when
nobody answers (`search.free_web_search_share`). With limits that stop, a web look-up that fails after its
searches without a full bill pauses automatic research for the rest of the search, because the
missing bill could pass the limit. With limits that only tell, it is an ordinary outage
(bounded retries), its searches count against the allowance, and the incomplete bill is noted.
Plans, other
web research, journeys and new-search scores are not reused as setup. Full-ad caching has its
own bounded age and parser versions. Changed inputs invalidate the relevant cache.

`review_capture.py` provides explicit one-search private capture, off by default. It records
inputs, candidates, decisions, ad evidence, AI attempts, responses and usage outside Git,
excluding keys, HTTP headers and hidden reasoning. Capture starts no search, paid replay or
scheduled monitoring. A capture-required allowance checks both the arm and successful claim
before requests. A capture error remains explicit; missing evidence cannot be reconstructed
from an older run.

## Source reliability

Adapters use `sources/http.py` for robots rules, polite request timing, bounded retries and
Retry-After. Each source reports status independently. `sources/budget.py` counts source usage;
collection/detail budgets and hosted AI tool allowances are distinct.

Blocked access remains blocked. The Bundesagentur portal is paused under its recorded terms.
Employer feeds and original pages can change; their directory and permitted interfaces are
recorded in [SOURCES](SOURCES.md). Offline source tests validate parsing and failure handling,
not current availability or complete market coverage.

## Project layout

The root keeps launchers, README, CONTRIBUTING, AGENTS (rules and conventions for AI coding agents;
CLAUDE.md imports it), LICENSE and Python/tool configuration.
`src/`, `tests/` and `tools/` keep their established paths; no extra build step is required.

| Area | Modules and purpose |
|---|---|
| Startup/server | `launcher.py`, `__main__.py`, `app.py`; local server/browser and request safety. `build.py` fingerprints code to replace an older running version. |
| Local persistence | `paths.py` locates private data; `keystore.py` stores masked keys; `settings.py`/`settings_api.py` handle settings; `db.py` owns SQLite migrations; `logs.py` masks keys in private logs; `reset.py` owns deliberate deletion and competing-write protection. |
| Documents/profile | `documents.py`, `documents_api.py`, `profile.py`; uploads, text and cached structured profiles. |
| Search preparation | `preparation.py`; bounded private reuse of exact-input location readings, search-word groups and verified reference-city facts, excluding other research, scores and journeys. |
| Search coordination | `search.py`, `search_api.py`, `pipeline.py`, `pool.py`; progress, collection, decisions, cards and condition reapplication. |
| Places/criteria | `countries.py`, `location.py`, `reference_places.py`, `reference_sources.py`, `reference_tables.py`, `places.py`, `placenames.py`, `travel.py`; supported geography, query interpretation, finite reference-city evidence, exact table calculations and measurements. |
| Discovery | `keywords.py`, `employers.py`; multilingual words and periodically discovered employers. |
| Evidence/matching | `text.py`, `jobposting.py`, `dedupe.py`, `filters.py`, `freshness.py`, `relevance.py`, `jobplace.py`, `requirements.py`, `recheck.py`, `scoring.py`; text extraction, filtering, research, grounded requirements, saved-ad recovery and fit. |
| Results/evaluation | `applications.py`, `applylink.py`, `livepostings.py`, `vacancy_evidence.py`, `jobidentity.py`, `jobstore.py`, `quality.py`, `quality_api.py`; application routes, apply links found on a click, verified original facts, remembered jobs, saved results and independent score checks. |
| Private comparison capture | `review_capture.py`; explicitly armed one-run document/candidate/request/response evidence outside Git, without searches, timers or paid replay. |
| `ai/` | `client.py` is the sole AI entry point; provider adapters, schemas, errors and token/web usage. |
| `sources/` | Isolated adapters and the registry. `base.py` defines `JobSource`; `http.py` applies polite requests/robots; `budget.py` tracks limits; `matching.py` matches lists; `careers.py` uses the directory; `careerlinks.py` recognizes career hosts. See [SOURCES](SOURCES.md). |
| `data/` | Public reference assets: `employers.json`, `places.csv.gz`, `villages.csv.gz`, `regions.csv.gz`, `postcodes.csv.gz`, `stations.csv`. User data never belongs here. |
| `web/` | `index.html`, `app.js`, `style.css`, `favicon.svg`; plain UI, system fonts, no external scripts. |
| `tests/` | Scripted providers and mocked HTTP; `conftest.py` gives disposable fictional data. `test_imports.py` checks import order; `test_docs.py` checks documentation links and the module/tool map. |
| `docs/` | ENGINEERING, SOURCES and ROADMAP; `guides/` for users. |
| `.githooks/`, `.github/` | Commit privacy guard, issue/PR templates, Mac/Windows/privacy CI. |

## Tools

Run these from the repository root with `uv run python tools/<name>.py`.
Private-data boundaries are described in [CONTRIBUTING](../CONTRIBUTING.md#private-data).

| Tool | Purpose |
|---|---|
| `tools/check_no_secrets.py` | Privacy guard for commits and CI; `--all` scans tracked files. |
| `tools/benchmark_local_matching.py` | Fictional local identity/deduplication comparison against a Git baseline; no saved user data, network or provider calls. |
| `tools/review_search.py` | Read-only, allowlisted aggregate review of saved results; no network/AI. |
| `tools/score_check.py` | Compare scores with independent labels; focused authorized re-scoring and prompt variants. |
| `tools/compare_providers.py` | Replay one private capture's AI requests on another provider/model and compare each step with Jobcu's own rules; `--setup` compares fresh profile, location and search-word readings; `--saved-ads` scores the Score check's or a frozen private ad set against judged ranges and blockers, with each run's reasoning tokens. Paid. |
| `tools/coverage_test.py` | Trace a private independent benchmark through collection/filtering/scoring. |
| `tools/universality_check.py` | Fictional professions through profile, words, relevance and scoring; ESCO vocabulary checks. |
| `tools/made_up_search.py` | A full fictional search in its own data folder. Live/paid runs still need authorization. |
| `tools/check_employers.py` | Inspect directory entries and candidate career systems; live source checks need current terms. |
| `tools/update_places.py` | Rebuild public GeoNames town/village/region/postcode assets. |
| `tools/update_stations.py` | Rebuild the main railway stations of the biggest towns from GeoNames. |
