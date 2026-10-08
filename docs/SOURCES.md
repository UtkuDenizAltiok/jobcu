# Source and service index

This indexes the adapters in the current code and the dated access evidence behind them.
It does **not** confirm today's availability, vacancies or recall. Read [AGENTS](../AGENTS.md)
and recheck current terms/robots rules before adding or changing collection.

Detailed formats, rate limits, site quirks and past measurements live in
[dated source research](archive/SOURCE-RESEARCH.md). Its checks span 2026-09-17 to 2026-10-06;
follow each section's date. Add newly verified facts here with a date and primary source link.

## Implemented job sources

The registry is `src/jobcu/sources/__init__.py`; requests go through `sources/http.py` and budgets
through `sources/budget.py`. A failed source reports its own status and does not stop others.
Countries below describe the adapter's scope, not complete market coverage.

| Source | Scope and method | Evidence and caveats |
|---|---|---|
| Adzuna | Ten supported countries; official API, app ID/key | [Record](archive/SOURCE-RESEARCH.md#adzuna). No Ireland; descriptions are summaries. Blocked ad pages are not fetched. |
| Reed | UK; official API/key, job details | [Record](archive/SOURCE-RESEARCH.md#reed). List dates have day precision; full details are separate. |
| Bundesagentur | Germany; public endpoint used by Jobsuche | [Record](archive/SOURCE-RESEARCH.md#bundesagentur). Unofficial API contract; may change without notice. |
| JobsIreland | Ireland; public list and job pages | [Record](archive/SOURCE-RESEARCH.md#jobsireland). Match titles locally; an empty first page may be a service failure. |
| Arbeitnow | Germany/UK feeds; public API | [Record](archive/SOURCE-RESEARCH.md#arbeitnow). Free-text locations need interpretation. |
| jobs.ac.uk | UK/Ireland; search pages and JobPosting data | [Record](archive/SOURCE-RESEARCH.md#jobsacuk). Academic/research/technical jobs; personal-use terms. |
| EURAXESS | Supported countries; research-job pages | [Record](archive/SOURCE-RESEARCH.md#euraxess). Throttling and per-search request limits apply. |
| JobTech | Sweden; public JobSearch API | [Record](archive/SOURCE-RESEARCH.md#jobtech). Full text; local timestamps and paging limits need handling. |
| service.bund.de | Germany; RSS and job pages | [Record](archive/SOURCE-RESEARCH.md#servicebund). Feed has a bounded recent window. |
| Teaching Vacancies | England; API and job pages | [Record](archive/SOURCE-RESEARCH.md#teachingvacancies). OGL attribution applies; page text adds requirements. |
| NHS Jobs | England/Wales; XML search and job pages | [Record](archive/SOURCE-RESEARCH.md#nhsjobs). Full person specifications need page parsing. |
| Le Forem | Belgium; open structured dataset | [Record](archive/SOURCE-RESEARCH.md#leforem). CC BY-SA attribution; summary evidence, blocked job pages. |
| Werken voor Nederland | Netherlands; sitemap and job pages | [Record](archive/SOURCE-RESEARCH.md#werkenvoornederland). Sitemap lastmod is not a posting date. |
| NAV | Norway; public experimental feed token | [Record](archive/SOURCE-RESEARCH.md#nav). Production-token permission is a separate owner/account decision. |
| Employer career systems | Directory plus discovered employers; public lists, feeds or sitemaps | [System records](archive/SOURCE-RESEARCH.md#career-systems). Check each employer host's permission and full-ad evidence. |

Career adapters: Ashby, d.vinci, Eightfold, Greenhouse, Lever, Oracle, Personio, Prospective,
Recruitee, generic job sitemaps, Softgarden, SuccessFactors, Teamtailor, Workable and Workday.
`src/jobcu/data/employers.json` is the directory; `tools/check_employers.py` is its maintenance tool.
The [2026-10-06 country matrix](archive/SOURCE-RESEARCH.md#engineering) measures listed employers
only, not reachable vacancies or engineering recall. All seven priority countries are represented.

## Recorded restrictions and candidates

These are retained decisions from dated checks; no new access was tested during this cleanup.

- [Held boards](archive/SOURCE-RESEARCH.md#held-boards): StepStone, Totaljobs, IrishJobs and Jobs.ie
  lack established permission for direct automated collection. Do not infer permission from robots alone.
- [Unused sources](archive/SOURCE-RESEARCH.md#unused-sources): EURES extraction requires a partner
  route; publicjobs.ie, UK Civil Service Jobs and DWP Find a Job blocked automated access.
- [LinkedIn/StepStone](archive/SOURCE-RESEARCH.md#linkedin-stepstone): no established direct
  vacancy-reading API for Jobcu. AI-found links need permitted original evidence and date checks.
- Employer restrictions also apply: Hays/Rise Technical terms and SmartRecruiters API robots
  restrictions are in the [research record](archive/SOURCE-RESEARCH.md).
- [Country candidates](archive/SOURCE-RESEARCH.md#candidates) are research leads, not adapters.
  The later [2026-10-06 update](archive/SOURCE-RESEARCH.md#engineering) takes precedence:
  Engineers Ireland is a manual benchmark candidate pending collection checks; VDAB requires a
  partnership; Job-Room's employer-management API is not a public vacancy-search feed.

## Identity and freshness evidence

**Checked 2026-10-07:** [Google's job-posting reference](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
defines `identifier` as the hiring organization's unique job reference and `datePosted` as
the employer's original posting date. [Schema.org](https://schema.org/JobPosting) distinguishes
an identifier from a title/description. These are data definitions, not collection permission.
Jobcu applies them conservatively: an employer source's different listing IDs cannot be
collapsed by matching names or templates; an exact ID still supports repost detection.
This is an engineering inference from the adapter contract, not proof that every system uses
only one listing ID per real vacancy. Cross-site names and unknown legacy metadata remain
imperfect identity evidence; old merged history is preserved rather than guessed apart.

[SQLite's limits](https://www.sqlite.org/limits.html) allow device-specific parameter limits.
`jobidentity.rows` uses [Python 3.13's connection limit](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.getlimit)
to bound batched reads; fictional regression checks lower the limit to 64.
[SQLite's transaction reference](https://www.sqlite.org/lang_transaction.html) explains that
`BEGIN IMMEDIATE` starts a write transaction before later reads/writes. Jobcu uses it to
serialize identity allocation; fictional simultaneous-save and rollback checks verify behavior.

## Full-ad evidence and existing detail APIs

**Rechecked 2026-10-08:** [Google's job-posting reference](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
requires a full description including duties, qualifications, skills, hours, education and
experience; `datePosted` means the employer's original posting date. These are data definitions,
not collection permission or proof that a particular site's text includes every condition.

[Greenhouse's Job Board API](https://docs.greenhouse.io/job-board.html) documents public GET
endpoints without authentication. Its job-list response omits content by default (the optional
`content=true` includes it); the individual job endpoint returns the full content. This supports
the existing separate list/detail reader, not unrestricted employer crawling or applications.
[Reed's jobseeker API](https://www.reed.co.uk/developers/jobseeker) likewise documents separate
search and job-ID detail endpoints: details include description and expiration, and a missing
job returns a blank response. It requires an API key via HTTP Basic authentication. Recruiter
API limits must not be assumed to apply to these jobseeker endpoints.

Inference for Jobcu: a list summary or failed detail read does not establish that the vacancy's
requirements are unavailable everywhere. Read another already-matched copy through its
existing permitted adapter; prefer the original employer when live reading is necessary.
Existing endpoints, terms/robots checks, source limits and access decisions are retained;
no source or collection permission is added by this coordinator change. Full text still needs
identity, completeness and bounded-age checks. Live recall/fit benefits need independent review.

## Job-source cooldown protocol

**Checked 2026-10-08:** [RFC 9110 section 10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after)
defines Retry-After as either non-negative integer seconds or an HTTP date. It gives a minimum
delay before a follow-up request. [RFC 6585 section 4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4)
defines 429 rate limiting, allows Retry-After and forbids caching a 429 response. It does not
prescribe whether a service applies limits per resource, host or account.

Jobcu conservatively shares a 429/5xx cooldown across readers of that host within one search,
including the last failed attempt. This is an engineering choice to avoid parallel readers
undercutting a delay, not proof that every provider has host-wide limits. Other hosts continue.
Valid delays are not shortened to Jobcu's ordinary backoff bound; zero and past dates remain
zero, while invalid headers use ordinary backoff. The established bot-protection test now
stops that host on its first recognized refusal, without retries or later network reads in
the same client. Already-running requests may finish; saved evidence remains usable.

[Python 3.13 date parsing](https://docs.python.org/3.13/library/email.utils.html#email.utils.parsedate_to_datetime)
supports HTTP-date forms, including legacy representations; invalid dates can raise ValueError.
[Timed lock acquisition](https://docs.python.org/3.13/library/threading.html#lock-objects)
allows queued readers to check Stop instead of waiting behind a long cooldown. Search and
condition-correction clients check Stop during waits. Fake-clock tests establish request
ordering and cancellation; they do not measure live source availability or job recall.

This changes retry coordination only: adapters, endpoints, minimum intervals, source limits
and robots/terms permissions are unchanged. No new vacancy collection permission is inferred.

## AI and Maps

**Classification/error guidance checked 2026-10-08:**
[Google's structured-output guide](https://ai.google.dev/gemini-api/docs/structured-output)
distinguishes valid JSON from correct values and recommends application validation/error
handling. This is capability guidance, not a provider recommendation or proof of classifier
accuracy. Jobcu accepts unrelated-title decisions only for IDs in that batch; an unexamined
title is never a rejection. [Python 3.13 futures](https://docs.python.org/3.13/library/concurrent.futures.html)
raise a task's exception when its result is retrieved; cancelling cannot stop an already-running
task. Jobcu handles recoverable title failures within that independent batch, while critical
errors and Stop propagate through its existing cancellation helper.

Provider support is in `src/jobcu/ai/`; users choose their provider and model. Research access
varies by account/model/tier. A connection test checks generation, not web research. See the
[2026-10-06 capability check](archive/SOURCE-RESEARCH.md#web-research) and [current key guide](guides/getting-your-keys.md).
Archived price comparisons are historical; do not use them as current cost or model advice.

**Application-link metadata checked 2026-10-07:** Adzuna's
[API schema](https://developer.adzuna.com/swagger/spec/test2.json) supplies a `redirect_url`
and describes it as the advertiser route required for API compliance. It does not supply the
final application host. Existing blocked-site rules still prohibit probing Adzuna pages.
Known CV-Library destinations are excluded by owner instruction; no CV-Library collection
or application-form traffic was added. Opaque redirects remain an unverified destination.

**Rechecked 2026-10-07 for the guides:**

- [Gemini API standard pricing](https://ai.google.dev/gemini-api/docs/pricing):
  `gemini-3.8-flash` lists USD 0.75 input and USD 3.75 output per million tokens, including
  thinking tokens, through 2026-12-31; USD 1.50/7.50 begins 2027-01-01. This is a dated
  pricing fact, not a model recommendation. Jobcu's token estimate omits grounding fees and
  cached-token discounts; provider billing remains the reference for actual charges.
- [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key) are managed in AI Studio;
  follow its current project/key instructions rather than assume a fixed key format.
- [Google Cloud alerts-only budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)
  notify about spending; they do not automatically cap it.
- [Routes API quotas](https://developers.google.com/maps/documentation/routes/usage-and-billing)
  limit request volume. Select limits against current billing terms; a quota is not a promise of
  free use. Jobcu also has its configured monthly route limit.
- [Maps storage constraints](archive/SOURCE-RESEARCH.md#maps) are retained dated evidence;
  the app stores AI travel estimates, not Google route times.
- [Transit routes](https://developers.google.com/maps/documentation/routes/transit-route)
  can combine trains, buses, subways and walking. General TRANSIT is not train-only time.
- [Route waypoints](https://developers.google.com/maps/documentation/routes/reference/rest/v2/Waypoint)
  accept coordinates, place IDs or addresses; named public stations can be used for a key probe.
- [Route-matrix durations](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix)
  are seconds and can be fractional; each element's status is independent of route-found condition.
  [Billing counts origins times destinations](https://developers.google.com/maps/documentation/routes/usage-and-billing),
  rather than HTTP requests; two sampled destinations use two elements for one origin.

Source/data credits remain in [README](../README.md#ownership-and-data-credits).
