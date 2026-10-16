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

### Broad boards and web discovery — 2026-10-10

**Rechecked:** [LinkedIn's agreement](https://www.linkedin.com/legal/user-agreement) restricts
scraping/copying and unauthorized automation. [Indeed's terms](https://www.indeed.com/legal)
require written permission for automated access, with a conditional robots.txt exception;
its [Job Sync API terms](https://docs.indeed.com/legal-terms/job-sync) concern partner integrations,
not a general personal-app search entitlement. Neither establishes Jobcu collection permission.

StepStone's [current applicant-terms portal](https://www.stepstone.de/e-recruiting/rechtliches/nutzungsbedingungen-bewerber/)
embeds its terms, and the [official integration catalogue](https://api.stepstone.com/)
documents job feeds, applications and recruitment integrations. No permitted personal-app
vacancy-reading route was established. This preserves the held decision; it does not claim
that no StepStone API exists. Permission/partner scope remains the dependency for direct reading.

[Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview) is
closed to new customers; existing customers must transition by 2027-01-01. It is not a new
self-service discovery route for Jobcu. [Gemini Search grounding](https://ai.google.dev/gemini-api/docs/google-search/)
already supports cited research. Adding discovery still needs reliable exact vacancy URLs,
permitted originals and original dates; search snippets do not establish freshness or recall.
No search-engine scraping, board adapter, partner account or vacancy traffic was introduced.

### Employer feeds and remote candidates — 2026-10-10

**Primary checks:** [Greenhouse's Job Board API](https://developers.greenhouse.io/job-board.html)
documents public unauthenticated GETs and optional full content; this differs from its private
recruiting-management APIs. [Lever's own posting documentation](https://github.com/lever/postings-api)
describes published employer listings. [Personio's recruiting overview](https://support.personio.de/hc/en-us/articles/360000314338-Overview-of-the-Personio-Recruiting-API)
distinguishes its employer XML feed from account integrations. These existing methods depend
on discovering actual employers, permitted hosts and original evidence; an endpoint catalogue
or directory size does not establish unique fresh relevant coverage.

[Jobicy's API/RSS documentation](https://jobicy.com/jobs-rss-feed), updated 2026-10-01,
explicitly permits ordinary apps and AI integrations with attribution and canonical Jobicy URLs.
The public paginated feed covers seven days with a three-hour publication delay; direct ATS
links require separate paid access. RSS polling must not exceed hourly. Candidate for remote
work, pending robots/terms checks at implementation and comparison of country eligibility,
original dates/descriptions and unique contribution. No paid feed, adapter or vacancy call here.

[Remotive's original API terms](https://github.com/remotive-com/remote-jobs-api) require attribution
and links, and delay public jobs by 24 hours. **Inference:** weak as the primary route for a
daily 24-hour fresh-job search; possible remote backup value is not disproved. Neither feed
establishes broad on-site hardware, nursing or teaching coverage. Broad-board restrictions
above remain: a reachable/internal endpoint is not app permission or a guarantee against bans.

### Ashby workplace fields — 2026-10-10

**Rechecked:** the [public posting contract](https://developers.ashbyhq.com/docs/public-job-posting-api)
documents primary `address.postalAddress`, direct secondary `address`, and their locality,
region and country fields. Missing upstream data remains missing; `publishedAt` is last
publication. [Customer terms](https://www.ashbyhq.com/resources/terms) govern contracted service
use, not a new blanket crawling licence. A metadata-only robots.txt request to api.ashbyhq.com
returned 401; this neither grants crawling permission nor changes the documented public API
contract. Blocked pages stay blocked.

The parser correction consumes fields in the existing documented list response, preserving
free text and legacy nested secondary addresses. No endpoint, employer directory, scope,
request budget, robots policy, page access or permission is expanded. It does not infer an
unknown town, employer head office or first posting date. Fictional evidence and limits:
[ENGINEERING](ENGINEERING.md#structured-employer-workplace-evidence--2026-10-10).

## Identity and freshness evidence

### Original-ad sections and access boundaries — 2026-10-15

**Checked:** [Schema.org's JobPosting definition](https://schema.org/JobPosting) supplies
separate responsibilities, qualifications, skills, education, experience and eligibility
properties as well as `description`. [Experience](https://schema.org/experienceRequirements)
can be text or an object with months; [education](https://schema.org/educationRequirements)
can be a credential and explicitly allow experience instead. These definitions do not say
every skill is mandatory, or that a missing property means no requirement. Its
[terms](https://schema.org/docs/terms.html) cover the vocabulary, not permission to collect
an employer's pages. The correction consumes already requested markup, preserves wording and
alternatives, and adds no endpoint, page scope or request allowance.

[SAP's website terms](https://www.sap.com/about/legal/terms-of-use.html), revised 2026-02-26,
restrict automated extraction, persistent copying and passing site content to AI providers
without specific permission. Search-engine indexing exceptions do not grant Jobcu permission.
SAP-owned `sap.com` career pages are held before requests, including redirect destinations;
other employers' SuccessFactors sites remain subject to their own terms and robots rules.
This supersedes the older robots-only assumption for SAP's own directory entry. It is an
access restriction, not evidence that SAP jobs lack value or that the whole career system
should be removed. A permitted independent original/feed or explicit permission is needed
to reopen that direct collection. Existing private history is preserved.

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
distinguishes post `id` from `internal_job_id`. Bulk `content=true` was a research lead here;
the dated implementation below supersedes that status. The same API overview says
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

### Greenhouse original lists and references — 2026-10-12

The [public Job Board contract](https://docs.greenhouse.io/job-board.html) was rechecked:
`content=true` includes full descriptions, departments and offices in the existing GET list;
individual GET details can still supply first publication and application deadlines.
The API host's robots.txt again returned 200 with only `/embed/` disallowed. Existing request
limits, blocked-host rules and public GET access remain; no Harvest access or application
submission is introduced. Larger list payloads trade bandwidth for earlier original evidence.

Official career references independently verify [ARX Robotics](https://www.arx-robotics.com/careers)
and [STARK's public career board](https://job-boards.eu.greenhouse.io/skdse) as Greenhouse feeds.
The directory records their individual check dates. Its other historic observations were not
re-certified. Source dates, underlying requisition identity, fit and current-window eligibility
are separate checks; a vendor's New label is not original publication evidence.

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

**Checked 2026-10-14:** Google's [Gemini troubleshooting guide](https://ai.google.dev/gemini-api/docs/troubleshooting)
distinguishes transient network/service failures from client/billing refusals. It recommends
bounded retries with increasing waits for transient failures and no retry for HTTP 402.
This is generic recovery guidance, not evidence of a current outage or a particular account's
balance. Jobcu owns its bounded retry loop and disables extra SDK retries; a disconnected
connection without a provider response cannot establish credit exhaustion or actual charges.

### OpenCode Go and AI credit eligibility

**Rechecked 2026-10-10:** the [Go documentation](https://opencode.ai/docs/go/) still lists
32 distinct models, USD10/month for Go, weighted shared windows and coding-agent client
guidance. The [terms](https://opencode.ai/legal/terms-of-service) list `help@anoma.ly` for
service/terms questions. The repository's [official support routing](https://github.com/anomalyco/opencode/blob/dev/.github/ISSUE_TEMPLATE/config.yml)
directs support and how-to questions to Discord; a subscription compatibility question is
not a reproducible software bug. No current provider clarification of this workload was found.

An additional primary integration lead is the maintainer's
[pi-web-search README](https://github.com/ttttmr/pi-web-search): it documents native hosted
search through Go/Zen Responses, with Go model examples and client/session requirements.
It distinguishes Chat Completions from Responses and marks Messages support unverified.
This is evidence from another integration, not an official entitlement, fee guarantee or
Jobcu quality measurement. No third-party extension was installed or run, and no disguised
client identity was used.

For a complete direct-versus-subscription comparison, [GPT-6 Luna's specification](https://developers.openai.com/api/docs/models/gpt-6-luna)
lists USD0.10/0.50 per million fresh input/output tokens through 272K context, medium as the
default and Responses tool support. [Native OpenAI tool pricing](https://developers.openai.com/api/docs/pricing)
lists USD10 per 1,000 web-search calls plus retrieved-content tokens. These native charges
do not establish Go's hosted-search charges. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
still lists Gemini 3.8 Flash at USD0.75/3.75 through 2026-12-31, then USD1.50/7.50;
thinking is included in output. Google Search grounding has 5,000 free queries/month shared
across Gemini 3 models, then USD14/1,000; one request can issue multiple queries. Rates are
not a euro invoice or matching-quality comparison. Verify taxes, currency conversion, tool
fees, long-context tiers and actual service allowance before purchasing or projecting savings.

**Checked 2026-10-09:** [Go](https://opencode.ai/en/go) advertises USD10/month, not a verified EUR10
checkout total. Its [service documentation](https://opencode.ai/docs/go/) describes coding-agent
traffic, an honest client user agent and stable `x-opencode-session`; the
[terms](https://opencode.ai/legal/terms-of-service) restrict unintended uses. Marketing says
any agent, but permission for Jobcu's non-coding matching workload is unresolved. Seek service
confirmation; do not disguise Jobcu as a coding client. No subscription/account action occurred.

Go's complete documented catalogue, fresh input/output prices per million tokens and protocols:
the landing page says **31**, while the checked documentation lists **32 distinct models**.
Version/context/peak price rows are not additional models. Use the current documented IDs;
extra IDs returned by the public models endpoint do not establish plan entitlement.

| Model | Input / output, USD | Monthly usage value, USD | Protocol |
|---|---:|---:|---|
| GLM-5.3-Flash | 0.15 / 0.50 | 60 | Chat Completions |
| GLM-5.3 | 1.40 / 4.40 | 15 | Chat Completions |
| GLM-5.2 | 1.40 / 4.40 | 60 | Chat Completions |
| Kimi K3 | 3.00 / 15.00 | 15 | Chat Completions |
| Kimi K2.7 Code | 0.95 / 4.00 | 60 | Chat Completions |
| Kimi K2.6 | 0.95 / 4.00 | 60 | Chat Completions |
| LongCat-2.0 | 0.30 / 1.20 | 60 | Chat Completions |
| LongCat 2.5 Preview Free | Free, temporary | Unlimited, temporary | Chat Completions |
| Step 5 Preview Free | Free, temporary | Unlimited, temporary | Chat Completions |
| MiMo-V2.6-Flash | 0.14 / 0.28 | 60 | Chat Completions |
| MiMo-V2.6-Pro | 0.435 / 0.87 | 15 | Chat Completions |
| MiMo-V2.5 | 0.14 / 0.28 | 60 | Chat Completions |
| MiMo-V2.5-Pro | 0.435 / 0.87 | 15 | Chat Completions |
| MiniMax M3 | 0.30 / 1.20 | 60 | Messages |
| MiniMax M2.7 | 0.30 / 1.20 | 60 | Messages |
| Muse Spark 1.3 Contributor | 0.10 / 0.20 | 60 | Responses |
| Muse Spark 1.2 Contributor | 0.10 / 0.20 | 60 | Responses |
| Qwen3.8 Max | 2.00 / 6.00 | 15 | Messages |
| Qwen3.8 Flash | 0.15 / 0.47 | 30 | Messages |
| Qwen3.7 Plus | 0.40 / 1.60 | 60 | Messages |
| DeepSeek V4.1 Flash | 0.15 / 0.60 off-peak; double at peak | 60 | Chat Completions |
| DeepSeek V4 Pro | 0.66 / 1.98 off-peak; double at peak | 15 | Chat Completions |
| DeepSeek V4 Flash | 0.15 / 0.60 off-peak; double at peak | 30 | Chat Completions |
| DeepSeek V4 Flash Vision Exp | 0.15 / 0.60 off-peak; double at peak | 15 | Chat Completions |
| Hy4 preview | 0.834 / 2.501 | 30 | Chat Completions |
| Hy3 | 0.14 / 0.58 | 60 | Chat Completions |
| Space Bunny | 0.15 / 0.60 | 30 | Chat Completions |
| Grok 4.7 | 2.00 / 6.00 | 15 | Responses |
| Grok 4.6 | 2.00 / 6.00 | 15 | Responses |
| GPT-6 Luna | 0.10 / 0.50 | 15 | Responses |
| GPT-5.6 Luna | 0.20 / 1.20 | 15 | Responses |
| Claude Haiku 5.5 | 0.10 / 0.50 | 15 | Messages |

GPT/Haiku rates above assume prompts at most 272K/100K. Larger contexts respectively cost
0.20/0.75 (GPT-6), 0.40/1.80 (GPT-5.6), and 0.50/2.50 (Haiku). Grok rates double above 200K;
Qwen Plus rates triple above 256K. Cached read/write discounts are in the primary table; do
not assume a fresh job-ad workload earns its cached-conversation discounts. Five-hour/weekly limits are
20%/50% of the monthly equivalent. Advertised request counts assume cached coding conversations;
they are estimates, not limits for full-ad scoring. Optional **Use balance** allows paid Zen
overage. Native upstream tool support does not establish Go entitlement. Retention/training
differences are recorded below; these are service claims, not independently audited guarantees.

**Capability versus service recheck, 2026-10-09:** the upstream
[GPT-6 Luna reference](https://developers.openai.com/api/docs/models/gpt-6-luna) lists structured
output and Responses web search; [MiMo Pro's specification](https://mimo.mi.com/models/en-US/mimo-v2.6-pro)
lists structured output, thinking and web search; [GLM-5.3-Flash's guide](https://docs.z.ai/guides/vlm/glm-5.3-flash)
explicitly describes professional document/research work beyond coding. These models are not
limited to generating code. Their Go-hosted controls/tool access and Jobcu matching accuracy
are separate questions. No evidence supports saying that all 32 models cannot perform the AI
work. An API supplies a transport/protocol; its host still chooses models, tools and allowance.

Go's client guidance says clients should send typical coding-agent traffic. That describes the
service's expected workload, not a technical model restriction. The landing page's any-agent
wording does not settle this specific use, and the checked terms restrict unintended purposes.
Neither establishes a precise all-non-coding-request ban. Confirm the intended-use fit rather
than turn ambiguity into a model-capability verdict or disguise requests. The repository's
[contact configuration](https://github.com/anomalyco/opencode/blob/dev/.github/ISSUE_TEMPLATE/config.yml)
directs support/how-to questions to its Discord community; no message was sent.

**Hosted research evidence, 2026-10-09:** an
[original test report dated 2026-08-13](https://github.com/lidge-jun/opencodex/issues/1616)
describes DeepSeek V4 Flash on Go's Responses endpoint performing hosted web searches and
returning source URLs. This is a useful positive lead, not current official entitlement,
quality or fee verification. Its reported zero cost is not a promise of free tool use.
Go's [published native Responses helper](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/provider/openai.ts#L14)
preserves the native body; its [request passthrough](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/requestBody.ts#L1)
rewrites the model while preserving the rest. These support investigating native hosted tools,
not assuming all models/formats share them. A separate
[upstream conversion report](https://github.com/anomalyco/opencode/issues/42090) describes
non-function tool rejection in converted Responses requests; native format and current model
routing matter. No paid probe was made, and reports were not treated as provider permission.

The current [OpenCode client search documentation](https://opencode.ai/v2/docs/websearch)
lists separate search providers. That is another research path, not proof that hosted Go
research is impossible or that external search fees are included in a Go subscription.
Distinguish client tools, model-native tools, gateway passthrough and actual plan entitlement.

**One-model capability recheck, 2026-10-09:** Google's
[Gemini 3.8 Flash model reference](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
lists medium thinking, structured output and Search grounding. Its
[Search guide](https://ai.google.dev/gemini-api/docs/google-search) documents cited current
information using that same model. These capabilities support a one-key/model setup; they do
not establish independent matching superiority or success on every fact. The
[billing guide](https://ai.google.dev/gemini-api/docs/billing#prepay) explicitly restricts prepaid
credit to Gemini API usage; other Cloud services remain separately billed. No owner balance,
account identifier or expiry is recorded here.

**Maps-tool distinction, 2026-10-09:** Gemini also offers
[Maps grounding](https://ai.google.dev/gemini-api/docs/maps-grounding), documented as a textual
search tool for places, reviews, addresses and opening hours, returning cited model text.
Its [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash) lists 5,000
free monthly Maps-grounding requests shared across Gemini 3/newer models, then USD14 per
1,000 search queries, plus model tokens. This is Gemini API work, distinct from Cloud Routes
billing. Jobcu currently uses Routes for structured origin/destination journey measurements,
not Gemini Maps grounding. The checked grounding guide does not establish an equivalent
transit-departure matrix contract. Inference: retain Routes for measured travel; do not replace
it with generated location answers or promise the existing Gemini balance pays Routes.
Maps grounding is a possible future place-evidence method, not an implemented feature or a
permission/price comparison proving it is a better route source. No tool call was made.

**Shared allowance and reset verification, 2026-10-09:** the published
[billing handler](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/handler.ts#L1191)
adds `round(cost * model.costMultiplier)` to the same subscriber/workspace monthly, weekly
and five-hour counters. The row is not keyed by model. Switching models does not reset it.
The [subscription checks](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/app/src/routes/zen/util/handler.ts#L897)
check those counters before balance fallback. The
[model configuration loader](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/core/src/model.ts#L85)
and [limits loader](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/core/src/subscription.ts#L44)
read deployed resource configuration; exact live multipliers/limits are not public in these
files. Do not claim this code inspects the owner's account or guarantees deployed behavior.

A normalized example derived from the published Go table: USD1.50 of GPT-6 Luna usage value
out of its USD15 monthly equivalent is **10%**. USD6 of DeepSeek V4.1 Flash usage value out of
USD60 is another **10%**. Mixed consumption is **20% of the shared monthly allowance**, and
would consume the published five-hour allowance if performed in one window. The percentages
also count toward the weekly 50% ceiling. These dollar usage values describe token work at
the listed rates, not additional cash invoices on top of the subscription. A weekly dashboard
percentage may use the weekly ceiling as its denominator, rather than the monthly equivalent.
This arithmetic is a planning interpretation of the published table and shared-counter code,
not a live capacity measurement. Model rotation cannot multiply the monthly allowance.

The published [date helpers](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/core/src/util/date.ts#L1)
anchor weeks at Monday 00:00 UTC and months to the subscription's UTC creation date/time,
clamping the day for shorter months. The
[five-hour check](https://github.com/anomalyco/opencode/blob/388406238bd5ca15564a762840a2362c3a45bd9c/packages/console/core/src/subscription.ts#L53)
uses the stored window-start timestamp; the handler preserves it within a window and starts
another after expiry. It is not an automatic daily refresh or a new allowance for each model.
Use the actual console's reset notice for an account-specific wait. **Use balance** must stay
off to avoid optional pay-as-you-go fallback when a shared ceiling is reached.

**Buying decision evidence, 2026-10-09:** repeated public searches did not find an official
permission statement for this non-coding workload. Go's current client instructions explicitly
request typical coding traffic; its API protocols do not override that guidance. The later
capability recheck above supersedes interpreting this as blanket Go rejection.
This leaves intended-use confirmation before paid adoption, without declaring its models
inferior or claiming every non-coding request is forbidden. Written provider confirmation is
the exact remaining permission dependency. No support message, payment or disguised request was made.

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

Go's privacy table reports training for both **Muse Contributor** models; exclude these from
automatic private-document adoption. GPT, Grok and Haiku list 30-day retention; the others list
zero days, with DeepSeek's renewable agreement valid only through **2026-10-31**. Recheck at
adoption. These are provider declarations, not an independent audit.

The [complete assessment and arithmetic](ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09)
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

### Additional reasoning-model candidates

**Checked 2026-10-09:** [MiMo-V2.6-Pro's own specification](https://mimo.mi.com/models/en-US/mimo-v2.6-pro)
lists deep thinking, tool calls, web search, structured output and a 1M context. Direct uncached
input/output is USD0.435/0.87 per million. These advertised capabilities and benchmark claims
are not Jobcu accuracy measurements; Go tool entitlement and effort mapping remain separate.

[DeepSeek's model metadata guide](https://api-docs.deepseek.com/api/list-models/)
illustrates V4.1 Flash as `deepseek-flash`, 1M context, native low/high/max efforts and high
default. Its [original model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/README.md)
describes a continuous 1–100 model-level reasoning control. Inference: serving interfaces can
expose different controls; inspect the chosen host rather than transferring a parameter from
another host or assuming a literal medium exists. Neither source proves job-fit quality.

[GLM-5.3's specification](https://docs.z.ai/guides/llm/glm-5.3) documents always-on reasoning,
low/high/max controls with max default, 1M context, and the same base as GLM-5.2 with coding/agent
post-training improvements. A coding benchmark gain does not establish a job-matching gain.

The [Go table](https://opencode.ai/docs/go/) currently gives MiMo Pro and GLM-5.3 USD15 monthly
equivalents, versus USD60 for DeepSeek V4.1 Flash and GLM-5.2. MiMo rates match the direct rates
above; GLM-5.3 is USD1.40/4.40 per million. DeepSeek is USD0.15/0.60 off-peak and USD0.30/1.20
peak; peak is weekdays 01:00–04:00 and 06:00–10:00 UTC. Limits/regions and shared weighted
capacity still apply. These are allowance units, not subscription surcharges or intelligence
rankings. The [model assessment](ENGINEERING.md#additional-model-assessment--2026-10-09)
keeps quality hypotheses separate from these facts. No model API request or paid comparison.

**Further primary checks, 2026-10-09:** [MiMo's thinking guide](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/other/deep-thinking)
states that V2.6 Pro/Flash enable thinking by default and documents `thinking.type`. This is
enabled reasoning, not a numeric medium guarantee; proxy behavior still needs verification.
[GLM-5.3-Flash](https://docs.z.ai/guides/vlm/glm-5.3-flash) documents 1M context, JSON, document
work and always-enabled thinking, recommending native max. Its claim of stronger intelligence
than GLM-5.2 is vendor evidence, not measured job-fit superiority. Its separate Go allowance
makes it a worthwhile new challenger. [Kimi K3's original card](https://huggingface.co/moonshotai/Kimi-K3/raw/main/README.md)
documents always-enabled thinking, low/high/max (default max) and preserved thinking for
multi-turn tool use. [MiniMax M3's research report](https://www.minimax.io/blog/minimax-m3)
focuses on coding, agent and long-context tasks; its gains do not independently validate job
matching. [Qwen's official catalogue](https://www.alibabacloud.com/help/en/model-studio/models)
describes native multimodal models; that is not Go research entitlement. None of these checks
called a model or established comparative matching accuracy.

### Direct-provider challengers — 2026-10-10

These are **direct pay-as-you-go APIs**, separate from coding subscriptions and Go proxy
entitlements. Prices below are USD per million uncached input/output tokens; context tiers,
reasoning output, retrieved text, tool fees, taxes and actual token demand still matter.
No call, account change or comparative fit test was made.

| Candidate | Input / output | Native reasoning and hosted research evidence |
|---|---|---|
| GPT-6 Luna | 0.10 / 0.50 through 272K context | Native medium and Responses web research; [current model/pricing check](#processing-tiers-and-complete-cost-comparisons--2026-10-10). Search USD0.01/call plus retrieved input. |
| GLM-5.3-Flash | 0.15 / 0.50 | [Price/tool table](https://docs.z.ai/guides/overview/pricing): search USD0.01/use. [Native API reference](https://docs.z.ai/api-reference/llm/chat-completion) gives low/high/max, always-on thinking, max default. |
| DeepSeek V4.1 Flash (`deepseek-flash`) | 0.15 / 0.60 off-peak; 0.30 / 1.20 peak | [Current pricing](https://api-docs.deepseek.com/quick_start/pricing/), [thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/): enabled/high default; requested medium maps to high. JSON/tool calling/Responses support does not establish hosted search. |
| MiMo-V2.6-Pro | 0.435 / 0.87 | [Original specification](https://mimo.mi.com/models/en-US/mimo-v2.6-pro) documents structured output and thinking. The [later native-contract check](#public-api-market-and-quality-evidence--2026-10-10) establishes published search/fee/citation fields; live behavior and Jobcu integration remain untested. |
| MiniMax-M3 | 0.30 / 1.20 through 512K input | [Current standard pricing](https://platform.minimax.io/docs/pricing/overview) lists beta hosted search at USD0.01/request. [Server Tools](https://platform.minimax.io/docs/guides/server-tools) documents Messages/Responses search and result URLs/citations; this is not Chat Completions function calling. |

For GLM, [search documentation](https://docs.z.ai/guides/tools/web-search) describes retrieval
and web search in Chat, with returned source records. The API reference has inconsistent tool
wording; exact GLM-5.3-Flash response/account support needs a bounded check before integration.
The [model guide](https://docs.z.ai/guides/vlm/glm-5.3-flash) recommends max; that recommendation
and coding/office claims are not Jobcu matching evidence. A deliberate high mapping for
Jobcu's medium setting is a native configuration, not a claim of equivalent thinking depth.

MiniMax's [invocation guide](https://platform.minimax.io/docs/guides/text-generation) now
highlights **M3.1-Flash-Preview**, with native medium among its efforts; the price table and
hosted-tool example above name **M3**. Do not transfer that control, price or availability
between model versions without verification. No Jobcu adapter change was made.

**Comparison rule:** a token-price scenario is `input × rate + output × rate`; a complete bill
also includes each actual hosted tool and retrieved-content charge, any retained research
provider, fixed subscription fees and Maps. For a USD0.01 tool, 10/30/50 uses per search over
30 searches add USD3/9/15 before content tokens. Those are fictional sensitivities, not a
prediction or transfer of Gemini query counts to another provider. Compare half/equal/double
token demand, identical evidence and independent labels. Private demand arithmetic stays private.
The earlier price-led candidate ordering is superseded; selection and acceptance gates:
[ENGINEERING](ENGINEERING.md#quality-first-api-and-electronics-coverage-decision--2026-10-10).

### Public API market and quality evidence — 2026-10-10

Scope: current general-purpose text/reasoning families from eleven developers, plus hosting/
research alternatives. This expands beyond Go's 32-model catalogue and the earlier inexpensive
direct-API subset. It is not an exhaustive census of every legacy, specialist, regional or
private-preview model. Model developers, API hosts and subscriptions are different choices;
hosted tools, reasoning controls, prices and terms cannot be transferred between them.
No model request, paid test, private-data processing or account change was made.

| Developer / current families considered | Primary evidence relevant to Jobcu |
|---|---|
| Google: 3.8 Flash; catalogue's Pro/Flash/Lite variants | [Current catalogue](https://ai.google.dev/gemini-api/docs/models) distinguishes text models from image/audio and previews. [Prices](https://ai.google.dev/gemini-api/docs/pricing) include thinking; Google Search grounding content is not charged as input, unlike URL Context/File Search content. |
| Anthropic: Fable 5.1, Opus/Sonnet/Haiku 5.5 | [Catalogue](https://platform.claude.com/docs/en/models/overview), [price table](https://platform.claude.com/docs/en/about-claude/pricing): input/output USD10/50, 4/20, 2/10, and Haiku 0.10/0.50 up to 100K prompt tokens (0.50/2.50 above). Search adds USD0.01/use and retrieved input. [Haiku overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview) documents adaptive effort and a newer tokenizer; not equivalent demand or matching quality. |
| OpenAI: Astra, Sol 6.1, Luna; current text catalogue | [Catalogue](https://developers.openai.com/api/docs/models), [Standard prices](https://developers.openai.com/api/docs/pricing): short-context input/output USD10/50, 2/10, 0.10/0.50; long-context/cache/tool charges differ. [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) documents native medium and Responses tools. Stronger models are included; Luna's lower price is not a quality verdict. |
| Xiaomi: MiMo-V2.6-Pro / Flash | [Model](https://mimo.mi.com/models/en-US/mimo-v2.6-pro), [overseas price table](https://mimo.mi.com/docs/pricing): Pro USD0.435/0.87; Flash USD0.14/0.28. [Thinking](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/text-generation/deep-thinking) uses enabled/disabled, enabled by default; no literal medium control documented. |
| Alibaba: Qwen3.8-Max / Max-0902, 3.7-Plus, 3.8-Flash | [Catalogue](https://www.alibabacloud.com/help/en/model-studio/models), [Max capabilities](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max), [prices](https://www.alibabacloud.com/help/en/model-studio/model-pricing). Global Max/0902 USD1.65/4.951 per million, including thinking output. Base Max lacks search in several regions where 0902 lists support; do not interchange snapshots/regions. Exact search controls/fees need checking for the selected deployment. |
| Moonshot: Kimi K3 / K2.6; coding variants separately | [K3 guide](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart): 1M context, strict JSON, always-on low/high/max reasoning. [Public platform](https://platform.kimi.ai/) lists USD3/15; [billing](https://platform.kimi.ai/docs/pricing/chat) is separate from subscriptions. The guide explicitly advises against production web-search use while it is updated; Formula needs a client tool loop. |
| DeepSeek: V4.1 Flash / V4 Pro-0813 | [Current pricing](https://api-docs.deepseek.com/quick_start/pricing/), [release](https://api-docs.deepseek.com/news/news260813/): Pro USD0.66/1.98 off-peak, 1.32/3.96 peak; low/high/max reasoning and structured/tool support. Current Flash identity/rates are recorded above; no hosted-search entitlement inferred. |
| Z AI: GLM-5.3 / 5.3-Flash | [Model](https://docs.z.ai/guides/llm/glm-5.3), [Flash](https://docs.z.ai/guides/vlm/glm-5.3-flash), [prices/tools](https://docs.z.ai/guides/overview/pricing). Native thinking/search evidence and reference inconsistencies are recorded above; neither small-model pricing nor coding gains establish job-fit quality. |
| MiniMax: M3 / M3.1-Flash-Preview | [Invocation](https://platform.minimax.io/docs/guides/text-generation), [pricing](https://platform.minimax.io/docs/pricing/overview), [server tools](https://platform.minimax.io/docs/guides/server-tools). Version-specific pricing/effort and beta research remain distinct, as above. |
| Mistral: Medium 3.5 / Large 3 / Small 4 | [Medium capabilities](https://docs.mistral.ai/models/mistral-medium-3-5-26-04), [prices](https://docs.mistral.ai/inference/pricing): USD1.50/7.50, 0.50/1.50, 0.15/0.60. [Hosted web search](https://docs.mistral.ai/studio/agents/agent-tools/websearch) belongs to Agents/Conversations, not ordinary compatible Chat. Model naming does not specify reasoning effort. |
| SpaceXAI/xAI: Grok 4.7 / earlier 4.6 | [Current 4.7 guide](https://docs.x.ai/developers/grok-4-7) (updated 2026-10-05) documents USD2/6, native medium and Responses research. [Tool pricing](https://docs.x.ai/developers/pricing): web search USD0.005/use plus tokens. Older catalogue/price text still highlights 4.6; use the exact version's contract/account rates. Fast 4.7 is not public-API access. |

Additional route: [Cohere Command A Reasoning](https://docs.cohere.com/docs/command-a-reasoning)
has multilingual, structured/citation/tool capabilities, but its production Model Vault route
is not an established small pay-as-you-go Jobcu plan. [Nova 2 Lite's guide](https://docs.aws.amazon.com/nova/latest/nova2-userguide/)
and [reasoning documentation](https://docs.aws.amazon.com/nova/latest/nova2-userguide/reasoning-capabilities.html)
describe multilingual/document reasoning with charged redacted thinking; native Bedrock
integration and a complete deployment quote are separate dependencies. Neither is rejected
as incapable; neither is ready as the simplest one-provider replacement here.

**MiMo contract resolved from primary documentation:** [native web search](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/text-generation/tool-calling/web-search)
requires activating the plugin. Chat requests use `tools: [{type: "web_search", ...}]`,
`force_search`, `max_keyword` and `limit`; other protocols are not supported for this tool.
The response documents `message.annotations` URL citations and
`usage.web_search_usage.tool_usage/page_usage`. Overseas search is USD5/1,000 uses plus
retrieved input tokens. A search round can make several billable keyword uses. The general
FAQ spells a force parameter differently; the dedicated contract is the integration reference,
with actual behavior still to verify. Thinking remains enabled; do not copy the disabled
thinking from the search example. This resolves the earlier missing published mechanism/price,
not live search quality, account eligibility or current Jobcu hosted-tool support. The service
agreement link did not expose readable text in this check; account/data terms must be inspected
before transferring private records. Direct API documentation does not confer Go entitlement.

[OpenRouter's server tool](https://openrouter.ai/tool/web-search/) documents native search or
an external engine with standard model token charges. Its current product page lists Exa at
USD0.007/use while the [beta guide](https://openrouter.ai/docs/guides/features/server-tools/web-search)
still lists USD0.005 plus extra-result charges: verify the selected engine's actual tariff.
[Credit fees](https://openrouter.ai/business) add 5.5% Standard purchase fees; model count does
not prove quality or net savings. Gateways and hosts such as Together/Fireworks require their
own routing, data-use, exact-model and tool checks; do not assume the native developer's terms.

**Independent general evidence, not a Jobcu verdict:** Artificial Analysis' [original comparison](https://artificialanalysis.ai/models/comparisons/mimo-v2-6-pro-vs-gemini-3-8-flash)
reports MiMo Pro 46 versus Gemini 3.8 Flash **High** 41 on its Intelligence Index, with
long-context reasoning 86%/81%, but factual-reliability AA-Omniscience 8/30 and GDP.pdf 19%/21%.
These counterexamples prevent treating a higher composite as universally better. Its
[methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking) describes a
primarily English suite, separate multilingual evaluation and model-judged components. High
Gemini is not Jobcu's medium configuration. None measures fresh-job recall, electronics fit,
unsupported requirements or route evidence. Selection remains a hypothesis until paired
Jobcu evidence meets [the quality gates](../CONTRIBUTING.md#compare-a-provider-without-lowering-quality).

### Electronics employer and specialist coverage — 2026-10-10

These primary references identify employer leads, **not collection licences, current jobs or
proof of missed vacancies**. Do not bulk-harvest member lists or use job-site accounts. Check
each employer's current terms/robots, actual career system and original-ad evidence before
adding it. Industry membership may include agencies, suppliers with no local hiring and
outdated acquired companies; independently verify identity and country.

| Country / route | Evidence and contribution hypothesis |
|---|---|
| Germany: sector employers | [ZVEI's sector board](https://www.zvei.org/verband/ueber-uns/vorstand) identifies power supplies, capacitors, semiconductors, PCB and automation employers, including inpotron and BLOCK. Hypothesis: specialist manufacturers can broaden coverage beyond familiar large brands; no vacancy benchmark established. |
| Ireland: microelectronics ecosystem | [MIDAS industry members](https://www.midasireland.ie/about-us/midas-company-members/) identifies design/research/manufacturing firms such as Emdalo, Icergi, Farran and Firecomms. A stronger sector-discovery reference than relying only on a general national board; no current relevant-job count inferred. |
| UK: electronics supply chain | [TechWorks member search](https://techworks.org.uk/members-searchable/) covers semiconductors, electronic systems and power electronics as well as other sectors/agencies. Candidate employer reference; no automatic collection right inferred. |
| Netherlands and Italy | [High Tech NL](https://www.hightechnl.nl/onzeleden/) separates semiconductor, energy and other clusters; [ANIE](https://anie.it/) represents electrotechnical/electronic industry. Candidate references, pending individual career-site checks and contribution evidence. Switzerland/Belgium need equally specific verified references, not guessed parity. |
| Original career-system gaps | [Bosch's FAQ](https://www.bosch.com/careers/faq/) confirms SmartRecruiters; its restrictions remain held. [ABB's application guide](https://careers.abb/global/en/how-to-apply) identifies Workday, but the exact permitted readable board is unverified. [Keysight's current career landing](https://jobs.keysight.com/external) is public; reachability does not establish an API/reader entitlement. Historical Avature/Siemens RSS observations remain dated leads, not a newly checked reader contract. |
| Specialist boards | [Engineers Ireland terms](https://www.engineersireland.ie/Terms-of-use) do not establish an automated vacancy licence. [Jobvector's legal page](https://www.jobvector.de/impressum.html) links separate terms; no permitted Jobcu feed established. IET's [platform terms](https://www.theiet.org/media/9621/iet-platform-general-terms.pdf) contain extraction restrictions; the applicable job-board terms/permission remain a dependency. Suitable public manual benchmarks need original dates and employer IDs. |
| Broader portals | [StepStone XML documentation](https://api.stepstone.com/knowledge-base/xml-guide-stepstone-de/) describes publishing ads, not a general vacancy-reading licence. [jobs.ch terms](https://www.jobs.ch/en/terms/) expressly restrict scraping and automation outside official tools. LinkedIn/Indeed and EURES dependencies above remain; no internal endpoint, cookies or blocked-host bypass is introduced. |

The shipped directory's existing electronics employers and unread systems were inspected
locally; its countries are historical observations, not verified today's coverage. A missing
directory entry does not prove a whole-search miss: an aggregator or discovered-employer
record may cover it. No list was fetched through Jobcu, source added/removed or private result
aggregate published. PULS/Agoria web research encountered robots restrictions; blocked pages
were not retried through another route. Rechecked permissions and a date-verified independent
sample are required before claiming additional recall. [Priority decision](ENGINEERING.md#quality-first-api-and-electronics-coverage-decision--2026-10-10).

### Gemini running costs

**Rechecked 2026-10-15:** [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
lists Gemini 3.8 Flash standard input/output at USD0.75/3.75 per million through 2026-12-31,
then USD1.50/7.50 from 2027-01-01. Output includes thinking. Google Search grounding has
5,000 free monthly requests shared across Gemini 3 and newer models, then USD14/1,000;
the page's footnote says each performed search query is charged. One model request can
produce multiple queries. Grounding with Google Maps is a separate Gemini tool; it is not
Jobcu's directly called Routes matrix or its allowance.

Inference: count available grounding queries, other account work and thinking before forecasting;
do not add reasoning tokens twice or present a token-only estimate as an invoice. These are
public rates, not verified owner billing, tax, currency or remaining allowance.

### Priced grounding and spend controls — 2026-10-15

**Rechecked 2026-10-15:** [Google's grounding guide](https://ai.google.dev/gemini-api/docs/google-search#pricing)
counts unique nonempty queries within each request for Gemini 3 and newer; Gemini 2.5 and
older bill per grounded prompt. Repeated streaming metadata must not
inflate that count; a separate request can incur the same query charge again. The
[pricing table](https://ai.google.dev/gemini-api/docs/pricing) separately lists cached-input
rates and grounding fees; thinking is already billed with output. Shared free allowances
cannot be inferred from one app's ledger. Rates, models and dates remain in the section above.

[Google's billing guide](https://ai.google.dev/gemini-api/docs/billing#spend-caps) documents
experimental project spend caps in AI Studio's Spend page, with roughly ten minutes of possible
enforcement delay and overages. Prepay balances and billing graphs have different processing
delays. These controls are distinct from an estimated local ceiling and alerts-only Cloud
budgets. No billing account was accessed or changed for this research.

### Processing tiers and complete cost comparisons — 2026-10-10

[Gemini Flex](https://ai.google.dev/gemini-api/docs/flex-inference) offers a 50% token-price
discount for supported models, including 3.8 Flash. It is preview, best-effort capacity with
variable latency (a 1–15-minute target), shares general limits and can be evicted. It has no
automatic Standard fallback; the guide shows Interactions API requests and recommends long
timeouts. This is an integration/recovery lead, not a setting already supported by Jobcu's
Generate Content adapter. Batch can take up to 24 hours. Neither is adopted for normal searches.

The [Go price table](https://opencode.ai/docs/go/) was fetched in full: 32 distinct models,
42 price rows including context/peak variants; prices/windows remain as recorded above.
Compare normalized shared-window fractions at half, equal and twice the observed token volume;
do not assume equal tokenization, thinking, cached usage or tool entitlement between models.

[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) supports native medium
reasoning, structured output and Responses web search. Direct Standard prices remain
USD0.10/0.50 per million short-context input/output tokens. [Tool pricing](https://developers.openai.com/api/docs/pricing)
adds USD10/1,000 search calls and retrieved-content tokens at model rates. A Gemini query count
is not an OpenAI tool-call count; Go hosted-tool fees/allowances are a separate unresolved fact.

[Chen et al., revised 2026-05-28](https://arxiv.org/abs/2603.23971) measure large differences
in reasoning tokens and interaction turns across models. Their tasks do not establish Jobcu
matching quality; the research supports measuring complete costs rather than ranking list prices.
Private demand/estimates stay private. Public fictional comparisons and decisions:
[ENGINEERING](ENGINEERING.md#structured-employer-workplace-evidence--2026-10-10).

### Billing refusals and processing evidence — 2026-10-12

**Rechecked:** Google's [billing documentation](https://ai.google.dev/gemini-api/docs/billing)
identifies exhausted prepay credit as HTTP 402 until replenishment. Delayed cut-off can create
a negative balance, deducted from the next purchase. Billing reports can lag; a balance
change alone cannot identify the charge for one run. This supports a terminal billing error,
not repeated minute-scale throttling waits or a diagnosis from a screenshot timestamp.

[Current pricing](https://ai.google.dev/gemini-api/docs/pricing) still lists 3.8 Flash standard
input/output USD0.75/3.75 per million through 2026-12-31, with thinking included in output.
Search queries have the documented shared free allowance and additional per-query fees.
Complete comparison includes failed work, retrieved content where charged, cache/storage,
tax/currency and separate Maps; local token estimates are not invoices.
The [Flex contract](https://ai.google.dev/gemini-api/docs/flex-inference) retains a 50% token
discount with variable 1–15-minute target latency, sheddable capacity, shared rate limits
and client-managed retries; there is no automatic Standard fallback. It uses Interactions
and is not implemented by Jobcu's Generate Content adapter. Batch can take up to 24 hours.
Equal-token half-price arithmetic does not measure actual latency/recovery or full savings.

MiMo's [rendered overseas prices](https://mimo.mi.com/docs/en-US/price/pay-as-you-go), updated
2026-10-08 and read on 2026-10-12, confirm V2.6 Pro USD0.435/0.87, cached read USD0.0036,
and overseas search USD5/1,000 uses separately. Retrieved input and multiple keyword uses
still matter. V2.6 Pro Ultraspeed is USD4.35/8.70, so an advertised faster variant is not
the same cheap API. The notice says native V2.5 aliases auto-route on October 14 and expire
October 21; this is not verified Go-hosted alias behavior. Existing thinking/search contracts
and quality counterevidence above remain; no private data was sent or plan purchased.

The [service agreement](https://mimo.mi.com/docs/quick-start/terms/user-agreement), dated
2026-07-07, is now readable. It describes an API platform and processor/controller roles,
with overseas storage in Europe/Singapore. Clauses 3.2.8–3.2.9 restrict unauthorized third-party
tools/systems; 5.2 requires rights to third-party copyrighted material. This resolves the
previous unreadable-page gap, not Jobcu-specific authorization. **Inference/adoption gate:**
reconcile those clauses with the documented API integration and source-content rights before
transferring records. Do not silently assume permission or claim a universal non-coding ban.

Go's current documentation could not be independently retrieved in this recheck; the complete
catalogue/token-window table above remains explicitly dated 2026-10-10. Search-indexed official
text is a lead, not proof that every current price, plan entitlement or hosted tool is unchanged.
No blocked access was bypassed. The broader eleven-developer comparison and stronger-model
counterevidence remain the comparison baseline; fresh rights/identity/fees and independent fit
outcomes are required for adoption. [Selected implementation](ENGINEERING.md#ai-billing-refusals-stop-and-incomplete-usage--2026-10-12).

### API market and reuse update — 2026-10-12

The [eleven-developer survey](#public-api-market-and-quality-evidence--2026-10-10) and
[complete 32-model Go table](#ai-and-maps) remain the baseline, including stronger models.
Fresh native checks confirm [DeepSeek's exact model/prices](https://api-docs.deepseek.com/quick_start/pricing/)
(browser read after the web reader timed out), [Z AI prices](https://docs.z.ai/guides/overview/pricing),
[MiniMax Standard/Priority/tool bills](https://platform.minimax.io/docs/pricing/overview),
[OpenAI Luna medium and prices](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Kimi K3 controls](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart),
[Mistral pricing](https://docs.mistral.ai/inference/pricing) and
[Alibaba regional/context prices](https://www.alibabacloud.com/help/en/model-studio/model-pricing).
DeepSeek Flash still has off-peak/peak token prices, not a native hosted-search entitlement.
GLM-5.3/Flash accept low/high/max; the [reference](https://docs.z.ai/api-reference/llm/chat-completion)
documents medium mapping for 5.2, not a verified literal-medium mapping for 5.3. MiniMax Priority
is 1.5 times Standard; Kimi K3 has always-on reasoning and advises against production web search
while its tool is updated. These distinctions do not rank matching quality.

Additional primary routes considered: [LongCat's API](https://longcat.chat/platform/docs/APIDocs.html)
and [current tariff](https://longcat.chat/platform/docs/zh/pricing/long-cat-2.0) offer Chat/Messages,
with temporary LongCat-2.0 USD0.30/1.20 uncached input/output instead of USD0.75/2.95;
[StepFun's public platform](https://platform.stepfun.ai/step-plan) lists Step 5 Preview and
3.7/3.5 Flash, but its rendered pricing/permission/tool contract is incomplete here;
[Tencent's Hy3 release](https://www.tencent.com/tencent-hunyuan-officially-releases-hy3-advancing-agent-capabilities-and-deeper-product-integration/)
announces TokenHub availability; [ByteDance's Seed2 report](https://arxiv.org/abs/2607.00248)
provides developer evaluations. Native regions, complete bills and Jobcu outcomes for these
routes remain unverified. They are not rejected as incapable; free previews, coding gains
or gateway availability cannot establish a sustainable equal-quality app replacement.

**Subscription versus direct API:** MiMo's [complete individual plan](https://mimo.mi.com/docs/en-US/tokenplan/Token%20Plan/subscription)
was read natively: Lite/Standard/Pro/Max cost USD6/16/50/100 monthly, with shared 4.1/11/38/82
billion Credits. The six lasting models comprise Pro, Flash, ASR and three TTS variants;
two old aliases expire October 21. Pro uses 300 Credits per uncached input token and 600 per
output token, cached input 2.5; Flash uses 100/200, cached 2. Off-peak uses 0.8 times Credits.
The package explicitly forbids non-coding automated scripts/custom application backends.
Therefore this plan is not a permitted Jobcu recommendation; this is an intended-use restriction,
not rejection from shared limits. Its distinct standard API remains a candidate.
Go's complete dated table/windows above remain useful, but current permission/hosted-tool
entitlement is unresolved; no new blocked-host attempt or purchase was made.

Fictional 100K input plus 100K output per search (including thinking) costs USD0.45 on Gemini
Standard, 0.225 on same-model Flex, 0.1305 on MiMo Pro, 0.065 on GLM Flash, 0.075–0.15 on
DeepSeek Flash, 0.15 on MiniMax M3 or 0.06 on Luna at the stated short-context tariffs.
Thirty identical searches multiply those token-only scenarios by 30; half/double demand
halves/doubles them. They exclude taxes/FX, failed usage, retrieved tokens, tools and Maps.
For 30 billable tool uses per search, MiMo adds USD4.50/month, GLM/MiniMax/OpenAI USD9/month
plus any charged retrieved input; equal use counts are not equal research quality/demand.
Gemini's query-based shared allowance is a different unit and may already be used elsewhere.
MiMo Pro's fictional workload uses 2.7 billion monthly Credits, half/double 1.35/5.4 billion;
its direct token bill is USD3.915 versus Lite USD6 or Standard USD16 before complete add-ons.
Quota arithmetic does not override the package's use restriction. Private measured-demand
daily/weekly/monthly sensitivity, retained-research scenarios and exact missing bills stay private.

**Best judgement with counterevidence:** keep MiMo Pro as the single challenger, while retaining
the working medium configuration until paired outcomes pass. Artificial Analysis' [current comparison](https://artificialanalysis.ai/models/comparisons/mimo-v2-6-pro-vs-gemini-3-8-flash)
still reports composite 46/41 and long-context 86%/81%, but factual reliability 8/30,
GDP.pdf 19%/21%, and longer end-to-end response time. Its v4.3.2 general suite compares Gemini
High, not Jobcu medium; no benchmark establishes job-fit or fresh-coverage equivalence.
[GLM Flash versus MiniMax](https://artificialanalysis.ai/models/comparisons/glm-5-3-flash-vs-minimax-m3)
also shows different strengths across long-context and document/factual tasks. Cheapest output,
integration ease and effort labels do not settle the choice.
[DeepSeek Flash](https://artificialanalysis.ai/models/releases/deepseek-v4-1-flash) reaches 39
at Max on that general index; its non-thinking result is not the required configuration.
[Haiku medium](https://artificialanalysis.ai/models/claude-haiku-5-5-medium) scores 34, while
[the publisher's release analysis](https://artificialanalysis.ai/articles/claude-haiku-5-5)
reports 43 at Max with heavy output use and an over-refusal issue. [Kimi K3 analysis](https://artificialanalysis.ai/articles/kimi-k3-achieves-3-in-the-artificial-analysis-intelligence-index-comparable-to-opus-4-8-and-gpt-5-5)
reports factual-reliability gains alongside higher direct rates. These are useful counterevidence
to price/composite rankings, not independently measured Jobcu exclusions or matching quality.
MiMo's [FAQ](https://mimo.mi.com/docs/en-US/quick-start/faq/api-integration) recommends disabling
thinking for some unstable tool outputs; Jobcu must instead preserve enabled thinking and
verify research separately. Its [agreement](https://mimo.mi.com/docs/quick-start/terms/user-agreement)
and source-content rights still need reconciliation before private transfer. Do not buy a coding
plan or switch private processing from this public evidence alone.

**Maps reuse:** the [general no-caching clause](https://cloud.google.com/maps-platform/terms)
permits only express exceptions. [Global Routes section 19.3](https://cloud.google.com/maps-platform/terms/maps-service-terms)
and [EEA Routes section 20.2](https://cloud.google.com/terms/maps-platform/eea/maps-service-terms)
allow latitude/longitude for up to 30 days; they do not authorize a cross-search journey-time
database. [Routes policies](https://developers.google.com/maps/documentation/routes/policies)
likewise distinguish place IDs and restricted content. Existing user history is preserved;
new validated-element reuse stays within one search, with exact request identity and retryable
unknowns. A different service needs both retention permission and verified transit coverage.

### Long AI answers and streaming

**Retention rechecked 2026-10-15:** [Gemini additional terms](https://ai.google.dev/gemini-api/terms)
restrict storage of grounded results to specified purposes, including displayed-result evaluation
and end-user history (up to two years), or temporary refinement with deletion/display conditions.
Associated suggestions/links and use restrictions still apply. This is not permission for an
unrestricted hidden archive or a reusable fact database. Jobcu's new raw reference notes are
in-flight only and excluded from serialization; existing owner history is preserved. Durable
recovery or paid hosted-research experiments require verifying the exact refinement/display,
retention/expiry and reuse contract first.

**Checked 2026-10-10:** Google's [Generate Content API reference](https://ai.google.dev/api/generate-content)
documents `streamGenerateContent` with the same generation request fields, including tools and
generation configuration. The [official Python SDK](https://github.com/googleapis/python-genai#generate-content-synchronous-streaming)
exposes `models.generate_content_stream`; its examples consume successive response chunks.
The response contract includes terminal finish reasons, prompt feedback, grounding metadata
and request-level token usage. Schema-valid partial JSON does not establish completed generation.

The locked SDK 2.24.0 was inspected locally: its synchronous streaming path does not guarantee
closing an interrupted HTTP response. [HTTPX's public response hooks](https://www.python-httpx.org/advanced/event-hooks/)
run before the body is consumed and provide that response object. Inference for Jobcu: close
each request's tracked responses in `finally`, without closing the shared SDK client or another
thread's body. Tests use the actual locked SDK and an offline HTTPX transport; no provider call.

An [original developer report](https://discuss.ai.google.dev/t/60s-timeout-from-python-sdk/83274)
describes long non-streaming requests disconnecting around 60 seconds and reports streaming as
a workaround. It is a lead, not proof of a universal server deadline, the cause of a particular
connection failure or guaranteed improvement with current models. Streaming can also fail.
Preserve medium thinking and necessary evidence; verify completed answers, metadata and live
behavior rather than claim savings from a different transport alone. Existing service terms,
pricing, allowance and endpoint identities still apply; this adds no job source or access right.

### Grounding passage links — 2026-10-16

**Checked 2026-10-16.** Google's [Generate Content grounding contract](https://ai.google.dev/api/generate-content#GroundingSupport)
links claim segments to grounding-chunk indices. For streaming, indices refer to chunks
accumulated across all responses in order. Segment offsets are bytes within provider parts;
the segment also supplies corresponding text. The locked official SDK exposes these fields.
Inference for Jobcu: retain unique literal note passages with their source URLs rather than
guess Python character offsets across chunks or infer associations from duplicate page titles.
A provider attribution establishes provenance, not independent verification or a complete
condition. Missing/ambiguous links remain unknown. This uses the existing Generate Content
contract and adds no service, endpoint, retention right or paid-call authority.

### Native reasoning refusals — 2026-10-15

**Checked 2026-10-15.** The official [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
distinguishes the requested reasoning effort, model defaults and billed reasoning tokens.
Omitting the setting is not a general proof of equal effort. Google's
[Generate Content thinking guide](https://ai.google.dev/gemini-api/docs/generate-content/thinking.md)
uses `thinking_config.thinking_level`, lists different supported levels and model defaults,
and distinguishes Gemini 2.5's budget control. This is the Generate Content contract Jobcu
uses; Interactions controls are not interchangeable.

Anthropic's [effort guide](https://platform.claude.com/docs/en/build-with-claude/effort) and
[thinking troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
distinguish whole-control support from rejected levels, thinking modes and per-turn effort.
A rejection of one value or combination does not mean the model lacks all effort controls.
These documents establish request distinctions, not every provider error's exact wording,
quality equivalence or live account availability. Jobcu's narrow refusal classifier is checked
with fictional SDK error payloads; unrecognized refusals preserve the requested setting.
See [implementation and limits](ENGINEERING.md#reasoning-preserving-request-recovery--2026-10-15).

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

**Storage/reuse rechecked 2026-10-09:** the [Routes-specific contract, section 19.3](https://cloud.google.com/maps-platform/terms/maps-service-terms)
permits temporary latitude/longitude caching for 30 days, not an unrestricted duration cache.
The policy's indefinite exception is for place IDs. Do not transfer another API's exceptions
to Routes durations, or claim that the coordinate exception authorizes stored travel decisions.
Code inspection confirms Jobcu's independently sourced town coordinates and exact-request
in-memory reuse; these differ from retaining yesterday's Google journey time. Current terms
and time-sensitive timetables rule out the proposed indefinite location-only route reuse.

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

**Adzuna direct-destination request rechecked 2026-10-14:** the current
[Job and Ad API schema](https://developer.adzuna.com/swagger/spec/test2.json) explicitly requires
using its supplied `redirect_url` to send the user to the advertiser for API compliance.
Neither response supplies a final-destination field. The
[API terms](https://developer.adzuna.com/docs/terms_of_service) require queries through Adzuna
and restrict third-party content-provider contact. Existing blocked-page rules also remain.
Do not resolve and replace this advertiser route without explicit Adzuna permission and a
permitted destination interface. Public documentation checks used no API key, ad request,
private redirect or destination traffic. Independently collected originals of the same job
can still be offered with their own provenance; an already saved employer link can be primary
while the exact Adzuna advertiser route remains an alternative. Unknown redirects are not
proof of a permitted direct link or an accessible application website.

**Application restrictions rechecked 2026-10-14:** the indexed official
[CV-Library FAQ](https://www.cv-library.co.uk/help/popular-questions) describes registration
requiring a UK address and access restricted to users located in the UK; temporary UK addresses
are accepted with a UK working visa. This describes address/location access, not a blanket
British-citizenship rule. Direct public retrieval returned 403; no account, application form or
bypass was used, so live eligibility was not tested. The existing owner-directed destination
exclusion remains. A reported numeric Adzuna ad may match its known details/land URL variants
with tracking-only query changes, while stored advertiser URLs stay intact. Other IDs/hosts or
unknown request fields cannot establish the same route. This changes local report matching,
not collection permission; no opaque advertiser redirect is fetched.

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
