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

### Gemini running costs

**Rechecked 2026-10-10:** [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
lists Gemini 3.8 Flash standard input/output at USD0.75/3.75 per million through 2026-12-31,
then USD1.50/7.50 from 2027-01-01. Output includes thinking. Google Search grounding has
5,000 free monthly requests shared across Gemini 3 and newer models, then USD14/1,000;
the page's footnote says each performed search query is charged. One model request can
produce multiple queries. Grounding with Google Maps is a separate Gemini tool; it is not
Jobcu's directly called Routes matrix or its allowance.

Inference: count available grounding queries, other account work and thinking before forecasting;
do not add reasoning tokens twice or present a token-only estimate as an invoice. These are
public rates, not verified owner billing, tax, currency or remaining allowance.

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

### Long AI answers and streaming

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
