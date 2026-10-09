# Source and service index

This indexes the adapters in the current code and the dated access evidence behind them.
It does **not** confirm today's availability, vacancies or recall. Read [AGENTS](../AGENTS.md)
and recheck current terms/robots rules before adding or changing collection.

Detailed formats, rate limits, site quirks and past measurements live in
[dated source research](archive/SOURCE-RESEARCH.md). Its checks span 2026-09-17 to 2026-10-06;
follow each section's date. Add newly verified facts here with a date and primary source link.

## Local deletion evidence

**Checked 2026-10-09.** SQLite's [secure_delete documentation](https://www.sqlite.org/pragma.html#pragma_secure_delete)
says ordinary deleted content is overwritten when enabled; virtual/shadow tables have caveats.
[VACUUM](https://www.sqlite.org/lang_vacuum.html) rebuilds the database, removes deleted content
and needs temporary disk space; active transactions/readers can prevent completion.
[Journal modes](https://www.sqlite.org/pragma.html#pragma_journal_mode) distinguish DELETE
(journal removed at commit), PERSIST (header cleared, file retained) and persistent WAL mode.
Jobcu restores DELETE mode before resetting rows and compacts afterwards, with fictional tests
for all three starting modes. This verifies app-file behavior, not SSD/OS-snapshot erasure.

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

### Greenhouse temporal evidence

**Rechecked 2026-10-09:** the [Job Board contract](https://docs.greenhouse.io/job-board.html)
separates `first_published`, `updated_at` and detail `application_deadline`; GET data is public.
The [API overview](https://support.greenhouse.io/hc/en-us/articles/10568627186203-Greenhouse-API-overview)
describes exporting public posts. The [legal portal](https://www.greenhouse.com/legal) links
subscription/privacy agreements; this is not a new license or permission for private APIs.
An actual public robots.txt read on boards-api.greenhouse.io returned HTTP 200 and disallowed
only `/embed/`. No vacancies were fetched for this research; existing budgets/blocked-host
rules remain. Only fields in the already-used list/detail response change interpretation.

Inference: modification does not establish first publication; missing/invalid original dates
stay unknown. A post date also cannot prove the underlying requisition is new: the contract
distinguishes post `id` from `internal_job_id`. Bulk `content=true` is a research lead requiring
latency/coverage measurements, not an adopted collection change. The same API overview says
Harvest endpoints require authentication; no private API access is introduced.

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

### OpenCode Go and AI credit eligibility

**Checked 2026-10-09:** [Go](https://opencode.ai/en/go) advertises USD10/month, not a verified EUR10
checkout total. Its [service documentation](https://opencode.ai/docs/go/) describes coding-agent
traffic, an honest client user agent and stable `x-opencode-session`; the
[terms](https://opencode.ai/legal/terms-of-service) restrict unintended uses. Marketing says
any agent, but permission for Jobcu's non-coding matching workload is unresolved. Seek service
confirmation; do not disguise Jobcu as a coding client. No subscription/account action occurred.

Go's documented single-model equivalents, prices per million tokens and recommended protocols:

| Model | Input / output, USD | Monthly usage value, USD | Protocol |
|---|---:|---:|---|
| GPT-6 Luna | 0.10 / 0.50 | 15 | Responses |
| Claude Haiku 5.5 | 0.10 / 0.50 | 15 | Messages |
| MiMo-V2.6-Pro | 0.435 / 0.87 | 15 | Chat Completions |
| Kimi K2.6 | 0.95 / 4.00 | 60 | Chat Completions |
| GLM-5.2 | 1.40 / 4.40 | 60 | Chat Completions |

GPT rates above assume prompts at most 272K; Haiku at most 100K. Five-hour/weekly limits are
20%/50% of the monthly equivalent. Advertised request counts assume cached coding conversations;
they are estimates, not limits for full-ad scoring. Optional **Use balance** allows paid Zen
overage. Native upstream tool support does not establish Go entitlement. Go reports no training
for these five; GPT/Haiku retention is 30 days, the other three zero. These are service claims.

**Second pass, 2026-10-09:** the public [Go model list](https://opencode.ai/zen/go/v1/models)
responded without a key and includes the five candidates. Its IDs do not prove tool or effort
support. The [published Responses helper](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/provider/openai.ts#L14)
passes a native Responses body onward; cross-format conversion is a separate path. Inference:
use the model's documented native format to preserve explicit reasoning/schema parameters,
then verify behavior; source code alone does not prove the live service.

The [coding client's web-search tool](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/opencode/src/tool/websearch.ts#L60)
invokes a separate MCP search service, with Parallel/Exa paths. A web-search button in OpenCode
does not establish standalone Go model API research, applicable entitlement or included fees
for Jobcu. No such endpoint was called. Current client-use guidance still requests coding
traffic; no primary permission for this non-coding app was found. This is unresolved permission,
not proof that the models are poor or a claim that every non-coding request is explicitly banned.

The [published handler at `388406238b`](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/handler.ts#L1191)
adds cost multiplied by a model factor into the same user's five-hour, weekly and monthly
counters. Inference: model allowances are weighted equivalents, not additive pools; mixed
models consume shared capacity. Published code is not proof of the owner's deployed account
state. It also gates DeepSeek Go models on permitted processing regions; check actual region
availability/consent before choosing them. No private account, usage endpoint or key was read.

Primary capability evidence, not proof of Jobcu accuracy or proxy compatibility:

- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) documents medium-default
  reasoning, a 1,050,000-token context, structured output and Responses web search. Those are
  upstream features; Go-hosted search access/pricing remains unverified. Its direct API lists
  the same USD0.10/0.50 uncached input/output rates for requests at most 272K; no Go subscription
  is required for direct API use. [OpenAI tool pricing](https://developers.openai.com/api/docs/pricing)
  separately charges web-search calls/content; token-only comparisons omit that work.
- [Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort) documents Haiku
  5.5's medium default; [structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
  lists Haiku 5.5 support and refusal/truncation exceptions.
- [MiMo-V2.6-Pro](https://mimo.mi.com/models/en-US/mimo-v2.6-pro) lists thinking, structured output
  and a 1M context. Its Go effort mapping and matching quality are unverified.
- [Kimi K2.6's own model card](https://huggingface.co/moonshotai/Kimi-K2.6/raw/main/README.md)
  reports reasoning/knowledge evaluations and thinking/instant modes. Differing effort/harness
  settings prevent treating its benchmark comparisons as Jobcu ranking evidence.
- [GLM-5.2](https://docs.z.ai/guides/llm/glm-5.2) documents thinking, JSON and a 1M context.
  [GLM-5.3](https://docs.z.ai/guides/llm/glm-5.3) shares its base with coding-focused post-training,
  supports low/high/max rather than medium, and defaults to max. Its stronger coding scores
  do not establish a matching benefit or justify quietly changing Jobcu's effort.

[Gemini 3.8 Flash guidance](https://ai.google.dev/gemini-api/docs/latest-model) documents
medium thinking and built-in tools. Current prices and charge units live in
[Gemini running costs](#gemini-running-costs). Different model tokenizers, reasoning and
request patterns prevent inferring equal workload cost.
[Gemini billing](https://ai.google.dev/gemini-api/docs/billing#prepay) explicitly limits AI Studio
prepaid credit to Gemini API usage, not other Cloud services. It is not a Maps balance.
Separately issued promotional Cloud credits have their own eligible SKUs/expiry; inspect the
actual grant before relying on one. No balance type, amount, refund or transfer was verified.

The [conditional ranking and arithmetic](ENGINEERING.md#ai-subscription-decision--2026-10-09)
preserve these uncertainties. No model calls, paid benchmark or private review were performed.

### Requirement evidence and independent review

**Checked 2026-10-09:** [Google's structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output)
distinguishes schema-valid JSON from semantically correct values and recommends application
validation. Inference for Jobcu: a numerical rubric part cannot substitute for evidence that
a mandatory requirement is met, unmet or unknown. Check short quotes against the supplied
ad/profile text, scope research quotes to the identified vacancy and keep unsupported
comparisons unknown. Quote presence cannot prove the interpretation or the original ad's truth.

[Zheng et al., 2023](https://arxiv.org/abs/2306.05685) study position, verbosity and
self-enhancement bias in model evaluation. This is chatbot-evaluation research, not evidence
of Jobcu accuracy. It supports blinded, independently recorded assessments as a useful
precaution; saved scores and assistant labels are not ground truth or market recall.

[UKSV's vetting explanation](https://www.gov.uk/government/publications/vetting-explained-and-our-vetting-charter/vetting-explained)
describes nationality/residence as factors considered and notes that few posts are reserved
to UK nationals. [Clearance-level guidance](https://www.gov.uk/government/publications/united-kingdom-security-vetting-clearance-levels/national-security-vetting-clearance-levels)
says the departmental authority sets the vetting requirement for the post. Inference: a
clearance acronym alone does not establish a particular applicant's ineligibility. Require
explicit excluding rules and relevant stated facts; otherwise retain uncertainty. These
pages do not prove eligibility for a particular vacancy; no personal vetting decision is made.

### Gemini running costs

**Rechecked 2026-10-09:** [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
lists Gemini 3.8 Flash standard input/output at USD0.75/3.75 per million through 2026-12-31,
then USD1.50/7.50 from 2027-01-01. Output includes thinking. Google Search grounding has
5,000 free monthly requests shared across Gemini 3 and newer models, then USD14/1,000;
the page's footnote says each performed search query is charged. One model request can
produce multiple queries. Grounding with Google Maps is a separate Gemini tool; it is not
Jobcu's directly called Routes matrix or its allowance.

Inference: count available grounding queries, other account work and thinking before forecasting;
do not add reasoning tokens twice or present a token-only estimate as an invoice. These are
public rates, not verified owner billing, tax, currency or remaining allowance.

### Maps request limits and recovery

**Per-route outcomes rechecked 2026-10-09:** Google's [matrix reference](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix)
separates each element's error status from its route-found condition; the
[matrix guide](https://developers.google.com/maps/documentation/routes/compute_route_matrix)
allows errors in individual elements of an otherwise successful response. `ROUTE_NOT_FOUND`
is an explicit outcome; an error, missing element or unusable duration does not establish it.
The [field-mask guide](https://developers.google.com/maps/documentation/routes/choose_fields)
says default protobuf values can be omitted, so a missing zero index/code is different from
an invalid index/code. Inference: preserve valid partial durations and leave unchecked
alternatives unknown; attribute any AI fallback separately, without storing Maps times as AI.
Google's [canonical error codes](https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto)
identify permission/authentication refusals (7/16) and exhausted resources (8). Jobcu stops
later network attempts after known access refusals or persistent per-element quota scope,
while preserving valid results from the same response. Raw status messages remain private.

[Policies](https://developers.google.com/maps/documentation/routes/policies),
[usage limits](https://developers.google.com/maps/documentation/routes/usage-and-billing) and
[global pricing](https://developers.google.com/maps/billing-and-pricing/pricing) were rechecked
the same day. Matrix limits/free caps/first-tier prices below remain listed; eligibility and
SKU depend on the account/features. Existing request dimensions, billing controls, attribution
and caching rules remain. No live route, key, billing or account change was used for research.

**Rechecked 2026-10-08:** [Routes usage and billing](https://developers.google.com/maps/documentation/routes/usage-and-billing)
counts matrix elements as origins × destinations; its documented standard rate is 3,000
elements/minute and transit matrices allow at most 100 elements. An owner's project can have
different configured quotas. Jobcu keeps its existing request dimensions and route cap.
[Current global pricing](https://developers.google.com/maps/billing-and-pricing/pricing) lists
10,000 free monthly Matrix Essentials elements, then USD5/1,000 in the first paid tier;
Matrix Pro lists 5,000 then USD10/1,000. Features determine the SKU. These are dated price facts,
not a guarantee of free requests, account eligibility or a recommendation to increase limits.

[Google's error design](https://google.aip.dev/193) identifies causes through ErrorInfo and
QuotaFailure details; raw messages can contain account/resource identifiers.
[Google's retry guidance](https://google.aip.dev/194) treats RESOURCE_EXHAUSTED as generally
non-retryable when replenishment may take hours or retries have billing implications.
[Maps web-service guidance](https://developers.google.com/maps/documentation/routes/web-service-best-practices)
supports increasing delays for recoverable failures. Inference: known daily/monthly/zero
quotas should stop immediately; temporary or unidentified throttling may recover through
bounded retries. Metadata availability is not promised for every response. Jobcu parses known
units/names when present, falls back to prose and labels an unidentified quota honestly.

[Routes policies](https://developers.google.com/maps/documentation/routes/policies) retain
content caching restrictions and Google Maps attribution; EEA terms depend on billing address.
No cross-search duration cache or new access is introduced. Attempted elements are counted
conservatively before every network attempt, including errors; this ledger is not a Google
invoice and cannot track usage from other apps. No live call or account/billing change was
made for this check. Measured fictional limits live in [ENGINEERING](ENGINEERING.md#maps-recovery).

#### Maps spending and alternatives

**Checked 2026-10-09:** the [SKU definitions](https://developers.google.com/maps/billing-and-pricing/sku-details)
list traffic-aware routing and location modifiers as Matrix Pro triggers, and two-wheel/toll
features as Enterprise triggers. Ordinary TRANSIT plus departure time is not listed as either.
Inference from the current `travel.GoogleMaps._matrix` request: Jobcu uses Matrix Essentials;
this is a code/contract assessment, not verification of the owner's actual billing line item.
The global Matrix prices above apply to that SKU, not a subscription or a price per collected ad.

The [pricing overview](https://developers.google.com/maps/billing-and-pricing/overview) aggregates
usage across projects linked to the billing account; free usage resets at midnight Pacific US
time on the first day of the month. A separate project does not establish a separate allowance.
[Cost controls](https://developers.google.com/maps/billing-and-pricing/manage-costs) distinguish
quota metrics from billing, which can lag up to 48 hours. Alerts-only budgets do not cap spending;
quotas can cap usage, but Google warns about quota/billing discrepancies. Inference: include
other account usage, the reset boundary, currency/tax and a margin before enlarging Jobcu's
attempt allowance. A local element counter cannot enforce an account-wide euro ceiling.

[Transit documentation](https://developers.google.com/maps/documentation/routes/transit-route)
supports arrival/departure times, station/line details and alternative routes in Compute Routes.
Transit can include walking, waiting, buses and trains; forecasts depend on changing schedules.
Inference: a higher billing tier is not evidence of better transit coverage; current sampling
and timetable gaps need route-specific checks. Compute Routes and Matrix have separate billing
events/allowances; adding detailed verification must account for both.

Alternative leads, not adopted sources or owner account instructions:

- [HERE Public Transit v8](https://docs.here.com/transit/reference/public-transit-api-v8-getroutes)
  documents dated journeys, alternatives, transit-mode and walking controls. The official
  pricing and limited-plan pages returned HTTP 403 in this research; current production price,
  terms and relevant country/timetable coverage remain unverified. No blocked page was bypassed.
- [TravelTime pricing](https://traveltime.com/pricing) offers development/evaluation access and
  a quoted fixed annual production plan based on throughput/service level. Its page restricts
  free access to development/evaluation, and says low-volume pay-as-you-go can be cheaper.
  A production quote and applicable use rights are dependencies; no account or contact was made.
- [OpenTripPlanner](https://www.opentripplanner.org/) describes routing built from GTFS and
  OpenStreetMap data. Inference: local routing would need licensed current feeds and ongoing
  coverage/maintenance across supported countries. It is not an established drop-in transit
  replacement, a zero-maintenance saving or permission to host Jobcu.

No private search evidence, live route call, paid test or account change was used for these
comparisons. The bounded spending recommendation and illustrative arithmetic live in
[ENGINEERING](ENGINEERING.md#maps-spending-proposal--2026-10-09).

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

## Search-method research leads — 2026-10-09

The official [Ashby posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)
returns full descriptions and secondary locations; its documented secondary address exposes
country/locality directly, while the primary address has `postalAddress`. `publishedAt` means
last publication, not proof of a new underlying requisition. Jobcu currently expects nested
secondary country metadata: vague location names could therefore lose evidence. This is a
code/contract research lead needing a reproduction, terms check and country/identity review,
not a measured recall claim or new collection permission.

[Lever's official posting API](https://github.com/lever/postings-api) already supplies public
published-post lists and description data; it is an existing adapter, not a new coverage
source. Structured employer APIs may improve evidence/reliability, but their value depends on
employer coverage, original dates and unique jobs. No adapter was added/removed or vacancy
queried for this comparison; existing restrictions and request budgets remain.
