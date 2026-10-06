# Jobcu architecture

Read this when changing the search pipeline or looking for a module. The working rules are in
[AGENTS.md](../AGENTS.md); current tasks are in [PROGRESS.md](PROGRESS.md).

## How a search works

`search.py` runs these steps in a background thread; the screen asks for progress once a second:

documents → profile (`profile.py`) → location plan (`location.py`) → search words (`keywords.py`)
→ employers the person's AI finds for their kind of work, every two weeks (`employers.py`) →
sources in parallel (`pipeline.collect`, `sources/*`) → a look by the AI at the career sites'
titles the search words missed (`relevance.screen_titles`) → duplicates (`dedupe.py`) → fixed rules
(`filters.py`) → the location conditions that need no measuring → quick relevance check
(`relevance.py`; it also reads the town from the ad text when the job sites give only a country,
and the conditions are then applied to those jobs) → travel limits (`travel.py`) → full ads
(`load_details`) → scoring (`scoring.py`: the AI reads the evidence, code applies the limits for
blockers) → the best jobs looked up online (`jobplace.py`: the town of those without one, and the
full ad's languages and years for those scored from a summary), then the conditions and limits
again for them → cards and job memory (`pipeline.build_card`, `jobstore.py`).

Everything after the rules runs in `search._decide`. **Edit** (next to "Understood as") runs it
again on the same jobs with corrected conditions, reusing every earlier answer (`pool.py`).

## The location box

People write a sentence, not a filter: *"Dublin or Cork"*, *"at most 50 minutes by public
transport to a city with at least 0.3% of the country's people"*, *"no cities where far-right
parties are strong"*, *"a top-10 country for work-life balance"*, *"a Turkish supermarket nearby"*.

- **Every search is different.** Nothing about anyone's wording is hard-coded or carried over:
  the person's AI reads the text fresh each time and splits it into conditions.
- **The AI analyses any fact itself.** Sizes are computed from the shipped figures; everything
  else is looked up on the web through the person's own AI provider, answered as towns that fit,
  towns to avoid, a size rule or countries (which also narrow the countries searched), with
  sources. When nothing lists every place, the AI reasons to a rule and labels it an estimate.
- **Limits to reference places are one condition** ("near"): a time or distance, measured to
  places defined by size, name or any looked-up fact, from where the job ad says the job is to
  the nearest edge of each place (the person could live anywhere in it), or to its centre only
  when the person says so.
- **Show the working.** "Understood as" lists every condition, how it was checked and its
  sources; estimates are labelled; the person can correct everything with Edit.
- **Shipped data is only a ruler.** The town list (coordinates, population, local names) measures
  what the AI decided to measure; it never decides what someone meant.

## Project layout

```
Start Jobcu.command / .bat   double-click launchers (macOS / Windows)
src/jobcu/
  launcher.py                starts the local server and opens the browser (__main__.py: python -m jobcu)
  app.py                     FastAPI app: screen, internal API, local-only safety checks
  paths.py                   the per-user data folder (never inside the code folder)
  keystore.py                API keys, saved in the data folder, readable only by the user
  settings.py                all other settings (settings.json in the data folder)
  settings_api.py            internal API behind the Settings screen
  documents.py               CV and cover letter: saving uploads and reading their text
  documents_api.py           internal API for documents and the profile preview
  profile.py                 the AI prompt that reads documents into a profile
  countries.py               supported countries, their job-ad languages and populations
  location.py                understands "Where do you want to work?": conditions, web research,
                             size rules, country answers, corrections from Edit
  travel.py                  travel limits to reference places: Google Maps with the user's key,
                             otherwise AI estimates (remembered 30 days)
  places.py                  the shipped town list: finding towns, populations, distances
  placenames.py              which country a free-text job location is in
  quality.py                 the score check: ads kept from real searches and the owner's answers
  quality_api.py             internal API behind the Score check screen
  keywords.py                the hidden multilingual search words
  employers.py               employers the person's AI finds for their kind of work: their
                             career systems recognised, checked and remembered in the data folder
  search.py                  runs a search (or a correction) step by step, with progress
  pipeline.py                collecting from sources, full ads, result cards
  dedupe.py                  duplicates, main link, "possible duplicate"
  filters.py                 the fixed rules (dates, types, remote, country, dismissed) and
                             conditions
  relevance.py               the quick AI relevance check
  jobplace.py                the best jobs looked up online by the person's AI: their town, and
                             their full ad's languages and years when only a summary was read
  scoring.py                 the scoring rubric and prompt
  freshness.py               posting dates and "Posted within"
  jobstore.py                jobs remembered between searches, job states, saved results
  pool.py                    the latest search's jobs, so Edit can apply corrected conditions
  text.py                    job ad HTML to plain text
  jobposting.py              reads schema.org JobPosting data from job pages
  search_api.py              internal API for starting and following a search
  build.py                   code fingerprint, so a new Jobcu replaces an older running one
  db.py                      SQLite database with numbered migrations
  logs.py                    log file in the data folder, with keys hidden
  ai/                        the AI layer: client.py is the ONLY way to call an AI;
                             one adapter per provider; providers.py lists them
  sources/                   job sources: base.py (common interface), http.py (polite
                             requests), budget.py (usage limits), matching.py (titles and
                             places matched on Jobcu's side), careers.py (company career systems
                             and the employer directory), careerlinks.py (which career system an
                             address or page belongs to), one module per source
  data/                      shipped reference data: employers.json, places.csv.gz,
                             regions.csv.gz, postcodes.csv.gz
  web/                       the screen: plain HTML, CSS, JS (no build step)
tests/                       pytest; conftest.py gives every test a throwaway data folder
tools/check_no_secrets.py    safety check against keys and personal data (Git hook and CI)
tools/check_employers.py     checks the employer directory and adds new candidates
tools/update_places.py       rebuilds the shipped town, region and postcode lists from GeoNames
tools/coverage_test.py       how many jobs a person found by hand did Jobcu find, and at which
                             step it lost the others
tools/universality_check.py  made-up people from other fields through profile, search words,
                             quick check and scoring, with the search words checked against ESCO
tools/made_up_search.py      one complete search for a made-up person (by default a graduate
                             power-electronics engineer), in its own data folder
tools/score_check.py         scores against independent ratings, and prompt variants
tools/review_search.py       read-only aggregate review of the latest saved search
.githooks/pre-commit         runs the safety check before every commit
.github/workflows/tests.yml  CI: safety check, then tests on macOS and Windows
docs/                        PROGRESS, DECISIONS, SOURCES, HANDOVER, guides/
```

`tests/test_docs.py` keeps this module map, document links and recovery sections usable.

## Reviewing quality and performance

Search steps measure elapsed time with a monotonic clock. Repeated progress updates keep the
same timer. Time spent waiting for a user's answer is recorded separately, and is included in
that step's elapsed time. Old saved searches have no timings; never invent them. A correction
has its own step timings, while its token ledger includes the original search's usage too.
The aggregate review allowlists the saved run kind and labels both scopes: original searches
have matching timing/usage scopes; reapplications have latest-correction timings and usage from
the search plus all corrections. Missing or unknown kinds remain unknown and trigger a warning.

The quality sample keeps up to 50 scored ads and 40 excluded titles. Each search adds up to eight
new items per kind, after removing already collected items. Scored samples span the score bands
and include both full ads and short summaries where available. They keep the final score after
online requirements checks, an explicit completeness flag and the original location plan.
Rescoring uses that plan and the current documents; old samples without a plan use Anywhere
and must not be treated as a faithful check of location preferences. Summary text remains
summary evidence, even if requirements were checked online; research notes are not a saved full ad.

`tools/review_search.py` opens SQLite in read-only mode, makes no network or AI requests, and
prints allowlisted aggregate fields only. It measures summary exposure, unknown dates, location
uncertainty, source availability, limits, timings, usage and independent top-10 ratings. It reports
precision only when every top card has a rating; coverage recall stays unknown until a separate,
date-verified coverage list exists. Counts and broad score-band agreement do not establish quality.

## Lessons to retain


- **Check a site's terms, not only its robots.txt.** Hays' robots.txt welcomes every crawler
  and publishes a job sitemap, but its terms forbid "Sammeln oder Auslesen von Informationen";
  Rise Technical forbids downloading. Record what the terms say in SOURCES.md before reading.
- **A corporate careers page rarely shows its career system.** The job site is one link deeper
  or on its own host (`jobs.`, `careers.`, `job.`): a sweep found 35 readable employers that
  way (Rohde & Schwarz, Hensoldt, Fraunhofer…) after the pages themselves showed 11.
- **Jobcu's own memory is evidence.** A job Jobcu showed before the window began is old,
  whatever date a job board gives it now (search 11: 45 of 349 cards were such reposts).

- **Check the test result before committing.** Piping pytest output through `tail` or `grep`
  hides failures. Use `uv run pytest && git commit …` or `set -o pipefail`.
- **Wait for GitHub's tests after every push** (`gh run list`, `gh run view <id> --log-failed`).
  Windows exposes timing and path bugs that macOS doesn't.
- **Never contact real sites in tests.** Use `httpx.MockTransport` with
  `PoliteClient(min_intervals={}, sleep=…, transport=…)`, and the scripted AI adapters in the tests.
- **An owner's decision only counts once the code applies it.** "Dominant election result" was
  decided on 2026-09-17 but missing from the AI's instructions until 2026-09-22. When recording a
  decision that changes behaviour, change the code or prompt in the same commit.
- **Check a service's terms before storing its answers.** Google's Routes API terms allow keeping
  coordinates for 30 days, not travel times.
- **Try new AI instructions with a real provider**, on a copy of someone's data (see Commands):
  scripted tests can't show whether a model reads a sentence the way people mean it.
- **A model answers from memory unless told to search.** "Find where this job ad is" came back
  with company head offices and no web search at all until the instructions said to search for
  every job and called an answer from memory a guess. Check `usage.web_searches` to see which it
  did.
- **Measure a search word before spending a budget on it.** Adzuna's `count` (one request) showed
  that two general words made one query match 6,459 ads instead of 337, which had been eating the
  whole request budget on ads nobody wants.
- **A daily limit belongs to the service's day, not the user's.** Google's Routes quota resets at
  midnight Pacific, so an evening search and one after midnight in Europe share it.
- **What only a tooltip shows doesn't exist.** The owner asked how a one-point score difference
  arises; the breakdown was there, but only on hover.
- **Import loops can hide behind a lucky import order.** `tests/test_imports.py` loads key modules
  on their own; import heavy modules inside a function when two modules need each other.
- **Try AI instructions with someone else's words too.** One made-up person's sentence
  (Netherlands, trains, a technical university, no rain) found two general faults the owner's
  own sentence never showed: a cut-off answer and "fit" swapped with "avoid".
- **Thinking counts as output with every provider.** Raising the reasoning effort cut off a
  2,000-token answer; `ai/client.py` now adds room for thinking to every request.
- **A site that blocks Jobcu stays blocked.** Find the data another way (the same job elsewhere,
  the person's AI reading it online) instead of trying again each search.
- **Python's robots.txt reader gets the standard wrong.** `urllib.robotparser` takes the first
  matching rule, so "Disallow: /" followed by "Allow: /careers" refused allowed pages. Use
  `sources.http.RobotsRules` (RFC 9309: the longest rule wins).
- **Measure coverage with a whole search, not a source on its own.** Each new source looked fine
  alone; only `tools/made_up_search.py` showed that the directory's career sites gave nothing
  for a hardware engineer around Munich or in Dublin.
- **LinkedIn shows reposts as new.** A coverage-list job "posted 2 days ago" on LinkedIn was 24
  days old on the employer's own site; check the original's date before counting a miss.
- **A score stored with an ad ages.** The score check's stored scores predate later limits; judge
  scoring with `tools/score_check.py --rescore`, never with the stored numbers.
- **Parts of a score can hide a whole.** Jobs in other fields reached 62–75 because the rubric's
  other 60 points come to any job without a blocker; look at the parts, not only the total.
- **An API can be closed while its pages are open.** SmartRecruiters' job API allows only
  LinkedIn's crawler in robots.txt; read every host's robots.txt, API hosts included.
- The secrets check can flag public identifiers. Only if a value is clearly not a secret, add
  `# jobcu-guard: allow` with a comment explaining why.
