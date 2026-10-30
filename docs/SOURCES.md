# Source and service index

This indexes the adapters in the current code and the dated access evidence behind them.
It does **not** confirm today's availability, vacancies, terms or recall.

Dates below describe recorded checks, not current availability. Historical investigations are
retained in Git. Adapter parsing and request details are in `src/jobcu/sources/`.

## Temporary provider recovery — 2026-10-23

Google's [background execution guide](https://ai.google.dev/gemini-api/docs/background-execution)
documents asynchronous execution for standard models, including Gemini 3.8 Flash. Normal HTTP
connections commonly close around 60 seconds; an immediately returned interaction ID supports
retrieval after a dropped connection. This is consistent with a long-request failure mode,
not proof of which component closed any particular connection. Background requests require
`store=true`; they cannot provide stateless recovery.

The [Interactions overview](https://ai.google.dev/gemini-api/docs/interactions-overview)
documents paid-tier stored-interaction retention of up to 55 days and early deletion. Stateless
`store=false` requests do not appear in interaction observability logs; waiting for a missing
stateless request to appear there cannot recover its bill. Jobcu's optional recovery setting
explicitly discloses temporary request/answer storage and automatic deletion, with retained local
IDs for failed cleanup. No account retention/logging setting is changed. Provider data terms and
billing attribution still apply; an operation ID does not itself prove complete usage or quality.

## Routes billing

**Routes pricing rechecked 2026-10-16:** Google's [global price list](https://developers.google.com/maps/billing-and-pricing/pricing)
lists Compute Route Matrix Essentials/Pro/Enterprise at USD5/10/15 per 1,000 events in the first
paid tier. [Routes billing guidance](https://developers.google.com/maps/documentation/routes/usage-and-billing)
describes matrix elements as origins multiplied by destinations and feature-dependent SKUs.
Free allowances and account-specific charges are separate; a conservative development estimate
does not establish an invoice. Count attempted elements and keep existing monthly controls.

**Transit timing measured 2026-10-30 (real requests, next Wednesday):** a route matrix `duration`
stays the same for departures 10:30-10:45 when the journey is the same, so it holds no wait for the
first vehicle, and `staticDuration` equals it. It can still hold waits between vehicles, overnight
in the worst case. It is the journey arriving first after the time asked, which can be slower than
the next one, so one departure can overstate by up to 25 minutes. An `arrivalTime` gave the same
kind of answer. The destination matters more: up to about 35 minutes between a city's centre and a
main station. Jobcu's `data/stations.csv` holds GeoNames points; Google's own geocoded points are
not stored.

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
| Adzuna | Ten supported countries; official API, app ID/key | No Ireland; descriptions are summaries. Blocked ad pages are not fetched. |
| Reed | UK; official API/key, job details | List dates have day precision; full details are separate. |
| Bundesagentur | Opt-in: off unless the person accepts its terms | [Access hold](#bundesagentur-access-hold--2026-10-17) and [owner's decision](#bundesagentur-opt-in--2026-10-30). |
| JobsIreland | Ireland; public list and job pages | Match titles locally; an empty first page may be a service failure. |
| Arbeitnow | Germany/UK feeds; public API | Free-text locations need interpretation. |
| jobs.ac.uk | UK/Ireland; search pages and JobPosting data | Academic/research/technical jobs; personal-use terms. |
| EURAXESS | Supported countries; research-job pages | Throttling and per-search request limits apply. |
| JobTech | Sweden; public JobSearch API | Full text; local timestamps and paging limits need handling. |
| service.bund.de | Germany; RSS and job pages | Feed has a bounded recent window. |
| Teaching Vacancies | England; API and job pages | OGL attribution applies; page text adds requirements. |
| NHS Jobs | England/Wales; XML search and job pages | Full person specifications need page parsing. |
| Le Forem | Belgium; open structured dataset | CC BY-SA attribution; summary evidence, blocked job pages. |
| Werken voor Nederland | Netherlands; sitemap and job pages | Sitemap lastmod is not a posting date. |
| NAV | Norway; public experimental feed token | Production-token permission is a separate owner/account decision. |
| Employer career systems | Directory plus discovered employers; public lists, feeds or sitemaps | Check each employer host's permission and full-ad evidence. |

Career adapters: Ashby, d.vinci, Eightfold, Greenhouse, Lever, Oracle, Personio, Prospective,
Recruitee, generic job sitemaps, Softgarden, SuccessFactors, Teamtailor, Workable and Workday.
`src/jobcu/data/employers.json` is the directory; `tools/check_employers.py` is its maintenance tool.
Directory membership does not establish reachable vacancies or engineering recall.

## Access and protocol records

### JSearch assessment — 2026-10-18

**Decision, updated after the owner's implementation request:** add JSearch as an optional
extra source through its direct Free API. It stays off until explicitly enabled and does not
replace existing feeds. The earlier assessment-only status is superseded by the implementation
below; its coverage, rights and metering qualifications still apply. No live vacancy/API test,
owner-data review, account change or purchase was made. Useful unique coverage and net cost
remain unmeasured.

#### Contract and evidence quality

OpenWeb Ninja's [product page](https://www.openwebninja.com/api/jsearch) describes a commercial
API over Google for Jobs results. This is a third-party service, not Google's own public job
search API or proof of separate direct partnerships with every named board. Its breadth is
a vendor claim. The [current OpenAPI](https://openwebninja.s3.us-east-1.amazonaws.com/portal/openapi/jsearch.yaml)
and [maintainer reference](https://github.com/OpenWeb-Ninja/openwebninja-skills/blob/main/openwebninja/apis/jsearch/README.md)
were read directly, rather than relying on cached search snippets or tutorial examples.

| Area | Current contract | Implication for Jobcu |
|---|---|---|
| Search | `/search-v2`, `data.jobs[]`, continuation in `data.cursor`; up to 10 jobs per page, 1–20 pages per call | Retain cursors and count page credits, not just HTTP requests. Search ranking is not exhaustive coverage. |
| Details | `/job-details` accepts up to 20 comma-separated IDs; each ID consumes a request credit | Batching reduces round trips, not credit use. Recover only additional evidence actually needed. |
| Descriptions | `job_description` is described as full text but is nullable | Potentially better than a snippet. A field name alone cannot establish complete employer requirements. |
| Links | Main apply URL, direct-link flags and alternative publisher apply options | Prefer a matching permitted employer/ATS vacancy when supplied; do not promise every link reaches an employer or remains live. |
| Locations | Nullable city, country and coordinates | A coordinate can describe a town rather than the actual workplace. Preserve provenance and ambiguity; it cannot establish commuting time. |
| Enrichment | Detail fields describe AI-extracted sponsorship, experience and skills | These are derived claims, not quoted requirements or independent scoring truth. Unknown sponsorship stays unknown. |

The downloaded schema contains `/search-v2`, details and two salary endpoints; `/search` is
absent. Older marketplace overview text and cached references still describe `/search`, and
an older cached reference mentions a deep-pagination multiplier not present in the current
contract. Integrations must use the current cursor contract and reconcile actual metering.
The schema mentions `enrich=true` in response-field descriptions without declaring that query
parameter or its fee. Do not enable it or assume the public sample's enriched fields are
ordinary guaranteed output. Marketing mentions expiration data, but the current schema does
not declare an expiration field. Neither discrepancy proves actual runtime behavior.

For reproducibility, the public schema retrieved on this date had SHA-256
`9f9ef1eec6cd97873211941c35b49c51b6ce8390fae803f2c2186b1127b7d03c`.
No provider example ad or third-party document text is copied into Jobcu's fixtures.

#### Countries, freshness and the existing pipeline

Google's [JobPosting guidance](https://developers.google.com/search/docs/appearance/structured-data/job-posting#region-availability)
lists Germany, UK, Switzerland, Netherlands, Belgium and Italy; Ireland is absent. That does
not prove JSearch returns no Irish jobs. It leaves Irish contribution and support across all
30 Jobcu countries unestablished. Google also documents expired results and incorrect
locations despite its publication rules. Search-index presence cannot prove vacancy validity.

The API accepts country/language inputs and relative date filters (`today`, `3days`, `week`,
`month`), without a documented exact rolling 24-hour parameter. Its timestamps are nullable;
ISO formatting alone cannot prove time precision or the employer's original publication date.
**Inference:** compare a conservative wider discovery window with Jobcu's exact saved window,
historical identity and permitted original dates. Do not widen the user's accepted age or
translate a refreshed board/index date into a new vacancy. Test boundary behavior first.

**Boundary check — 2026-10-24.** `3days` is looser than its name: two live queries returned
ads stamped 40-88 hours old and, for one German query, 160 and 184 hours old, all at day
precision. A 72-hour search that asked for `week` kept only 47 of 109 results; 62 were older
than its window. Searches up to 72 hours therefore ask for `3days` and 168-hour searches for
`week`: the tightest filter that covers the window, so no fresh ad is lost and more of each
paid page is usable.

**Lag check — 2026-10-29.** Two 24-hour searches counted no JSearch ad for 10 credits; in the
second, all 23 ads returned were dated before the window. A direct check of "Hardwareentwickler in Germany"
returned nothing for `today` and ten ads dated 68-92 hours earlier for `3days`. Jobcu had shown
three of them in earlier searches (one 15 days before its JSearch date: the date is the
index's, not the vacancy's); seven were jobs Jobcu had never shown. So JSearch lists ads about
two to three days late, and a 24-hour search could never count a job only JSearch found. Its
ads therefore count up to 72 hours before the window (`date_lag_hours`) when no other copy
dates the job earlier and Jobcu never showed it before the window began. A job already shown
stays a repost, and the card keeps the date JSearch gives.

JSearch does not provide the evidence needed to decide population shares, city-election
comparisons, sampled journeys or personal fit. Its radius filter is not a travel-time filter.
More structured full text could reduce some online-ad research, but additional unique jobs
can also add downstream work. A net saving requires measured total AI/source/Maps usage on
equal coverage and quality. It is not established by API prices or a short response time.

The integration is one isolated `JobSource`, using the existing local
key store, request accounting, Stop handling, deduplication and freshness/location gates.
There is no need to install the vendor's agent skill/MCP server or change the chosen AI.
Use vacancy/requisition identity across providers; a JSearch ID alone does not deduplicate
Adzuna, a recruiter and the employer. Retain current employer feeds for originals and backup.
Never pay to score a job whose location gate is still unresolved or fails.

#### Price and spending controls

The [direct price list](https://www.openwebninja.com/api/jsearch) currently advertises:

| Direct plan | USD price | Included allowance | Extra usage |
|---|---:|---:|---:|
| Free | $0/month | 200 credits/month | Hard limit |
| Pay as you go | $0.005 per unit | No monthly fee | Usage billed |
| Pro | $25/month | 10,000 credits/month | $0.003 per extra |

The [marketplace pricing page](https://rapidapi.com/letscrape-6bRBa3qguO5/api/jsearch/pricing)
likewise lists 200 free units and Pro at $25 for 10,000. It additionally displays a bandwidth
platform fee: 10,240 MB/month included, then
$0.001/MB. The direct provider advertises no credit card for its free tier and no RapidAPI
transfer limit. Marketplace onboarding rules differ; do not assume a generic platform FAQ
overrides this API's actual plan/checkout. No checkout was inspected or accepted.

For ordinary requests, budget search pages plus requested detail IDs, with separate allowances
for any other opted-in endpoints and attempted retries. Reserve the maximum requested pages
before dispatch; release only reconciled unused capacity. Do not assume an empty response,
error, timeout or same-query retry is free. The current published error-charging treatment is
not sufficiently explicit to make that claim. Paid overages are not a spending ceiling.

#### Rights and privacy

The provider's current [terms](https://www.openwebninja.com/terms), sections 2, 3 and 8, expressly
allow official API integration and use of API output in applications, including commercial
products. They limit that grant to the provider's own rights and leave original-source terms,
third-party rights and lawful storage/reuse with the customer. They exclude a competing
standalone data/API resale product. This is permission to use their API under its plan, not
blanket proof that every upstream board's full text can be stored and forwarded for matching.
Clarify the intended local history, display, AI processing and provenance before activation;
do not use an intermediary to bypass a held host or infer a board partnership from its logo.
No support message was sent and no legal agreement accepted during this research.

The [privacy policy](https://www.openwebninja.com/privacy) describes US hosting and one-year API
request-log/IP retention. The adapter sends only generated role/skill terms and search country;
it has no reason to upload a CV, cover letter or private preference narrative. Jobcu remains
local, but enabling it adds another external recipient for those search terms. The policy does
not establish that query bodies are never retained. Provider log retention is not a licence
for Jobcu to keep third-party ad text indefinitely.

#### Implemented controls

`sources/jsearch.py` uses direct `x-api-key` authentication and `/search-v2` cursor pages.
Saving a key does not enable collection, including when upgrading an existing installation.
Before vacancies, `/usage?api_id=jsearch` must report an active direct Free plan and a complete,
current request allowance no greater than 200. Paid, unknown and incomplete accounts stop this
source. Calendar-month reservations are atomic and capped at 200, including account checks;
provider-period remaining quota can further reduce the allowance. The provider's advertised
Free hard limit is also required: local accounting alone cannot cap other clients' usage.

Each search receives an adaptive share, at most 40 credits including account checks and full-ad
details. Countries and native/English queries take turns; cursor pages follow initial queries,
with at most three pages per query. Two units are kept for selective missing full ads when the
allowance permits. Small allowances rotate the starting country. Exhaustion is reported as
partial coverage, while other feeds continue. One page or one detail ID is requested per call;
reserved attempts are never assumed free or refunded after errors. Automatic HTTP and transport
retries are disabled for this adapter, and credentials never follow redirects. No enrichment,
salary-estimate, marketplace, storefront or wallet route is used.

Supplied descriptions and application alternatives enter existing reuse, deduplication and
admission checks. Earlier dates and complete text survive weaker detail replies. Missing dates
stay unknown, midnight dates are day precision, and a wider source date filter does not widen
the user's accepted age. Lookup country is stored separately from workplace evidence. Source
coordinates are not promoted to an address; derived sponsorship/skill fields are not requirements.
Employer links require both the supplied direct flag and a matching employer/known ATS host;
original board routes remain available. Jobcu makes no request to those destinations merely to
resolve a redirect. Fictional tests cover hardware, nursing and teaching, failures and ceilings.

### Bundesagentur access hold — 2026-10-17

The current [portal terms](https://www.arbeitsagentur.de/nutzungsbedingungen), section 2a(3),
prohibit robots/webspiders and automated data collection contrary to the intended interface use.
This supersedes the earlier assumption that the public website endpoint was sufficient
permission. Pause automated search/details and deny these destinations in the HTTP client,
including redirects, until an explicitly permitted interface or permission is established.
Keep the historical parser, source identifiers, saved ads and manual links; no login, alternate
host or blocked-page workaround is authorized. Other permitted sources continue independently.
The hold has a coverage cost; no complete replacement is claimed.

A portal copy's first-publication date is not proof of an employer vacancy's original date.
Identity, earlier matching copies and permitted original posting/closing metadata are still
needed to distinguish a fresh opening from a refreshed advertisement.

These are retained decisions from dated checks; no new access was tested during this cleanup.

### Source checks — 2026-10-30

- **EURES** has a public search interface (`POST
  https://europa.eu/eures/api/jv-searchengine/public/jv-search/search`, the portal's own; JSON
  body with keywords, `publicationPeriod` such as `LAST_DAY`, `locationCodes` such as `de`). It
  returns full descriptions, first-publication time, employer, NUTS regions and contract codes.
  The [legal notice](https://eures.europa.eu/legal-notice_en) authorises re-use with the
  European Labour Authority credited and says nothing against automated access; robots.txt
  does not exclude the search, and europa.eu asks for `Crawl-delay: 10`. For Germany it carries
  the Bundesagentur's vacancies (same titles and wording); for Ireland it held 5 jobs of the
  last day, all German-posted. A candidate for the other EU countries' public employment
  services and for people who keep the Bundesagentur off; not built yet.
- **JobsIreland.ie** answered 403 to every address (robots.txt included) from the owner's
  connection, to an ordinary browser there and to an outside fetcher, from 2026-10-29 evening.
  Jobcu sends it 1-4 requests a day, so this is the site's refusal, now reported as one.
- **SmartRecruiters** (Bosch, ETAS, Delta Electronics): `api.smartrecruiters.com/robots.txt`
  allows only LinkedInBot; Jobcu stays out (see the access boundaries below).

### Bundesagentur opt-in — 2026-10-30

The owner asked the agency for permission on 2026-10-25. On 2026-10-29 its technical support
replied only that the owner should call their local Agentur für Arbeit; it neither gave nor
refused permission. The terms (Stand 08.07.2026, section 2a(3)) still say robots, web spiders
and using existing interfaces contrary to the agency's intended purpose are not allowed. The
owner decided to read it again for their own job search and accepts that. The source is
therefore an opt-in like JSearch: off for everyone until switched on in Settings, which shows
the terms note; only then does the HTTP client let requests reach arbeitsagentur.de hosts
(`sources.accepted_terms`, `http.terms_denial`). Nothing works around a block, the agency's
own public client ID is used as before, and requests keep their pause (0.7 s) and per-search
ceiling. Evidence for the decision: searches 1-5 (before the hold) had 11-47 German cards
each from it, almost all found by no other source; on 2026-10-29 one query found six
hardware-developer ads of the last day, five of which Jobcu had not found elsewhere.

- Held boards: StepStone, Totaljobs, IrishJobs and Jobs.ie
  lack established permission for direct automated collection. Do not infer permission from robots alone.
- Unused sources: EURES (see the 2026-10-30 check below); publicjobs.ie, UK Civil Service Jobs
  and DWP Find a Job blocked automated access.
- LinkedIn/StepStone: no established direct
  vacancy-reading API for Jobcu. AI-found links need permitted original evidence and date checks.
- Employer restrictions also apply; see the [additional access boundaries](#additional-access-boundaries).
- Country candidates are research leads, not adapters.
  The later 2026-10-06 update takes precedence:
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
[ENGINEERING](ENGINEERING.md#evidence-identity-and-scoring).

## Identity and freshness evidence

### Workday detail workplaces — 2026-10-23

A bounded check through the existing Workday reader's terms, robots and polite-request gates
confirmed `jobPostingInfo.location` and string-list `additionalLocations` alongside the full
ad. The reader now consumes these fields in the response it already requests, without another
endpoint, query, country or source allowance. Named locations remain source evidence; absent
or malformed fields retain known metadata. This is an existing-response parser correction,
not permission for new collection or evidence that every employer fills those fields.

### Employer-board moves — 2026-10-23

[Amplitude's careers page](https://amplitude.com/careers) now links to its
[Ashby board](https://jobs.ashbyhq.com/amplitude). [Wayve's official join page](https://wayve.ai/careers/join-us/)
redirects to its [Ashby board](https://jobs.ashbyhq.com/wayve). Move Amplitude's directory
entry to Ashby and remove only Wayve's obsolete Greenhouse entry; its existing Ashby entry
and country coverage remain. Do not remove an employer merely because an old board fails.

Rechecked the [documented public posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)
and [customer terms](https://www.ashbyhq.com/resources/terms). Two bounded posting-API reads
returned listed jobs with full descriptions. The API host's robots file returned 401 again;
no HTML crawling permission is inferred. Existing documented posting-API use, access decisions
and request budgets remain. This verifies board identity, not market coverage or fresh-job recall.

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
sample are required before claiming additional recall. [Priority decision](ENGINEERING.md#source-reliability).

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
cannot be inferred from one app's ledger. The date of each price record limits its applicability.

[Google's billing guide](https://ai.google.dev/gemini-api/docs/billing#spend-caps) documents
experimental project spend caps in AI Studio's Spend page, with roughly ten minutes of possible
enforcement delay and overages. Prepay balances and billing graphs have different processing
delays. These controls are distinct from an estimated local ceiling and alerts-only Cloud
budgets. No billing account was accessed or changed for this research.

**Query controls rechecked 2026-10-17:** Google's [grounding guide](https://ai.google.dev/gemini-api/docs/google-search/)
prices each query selected by newer native models. The locked SDK's `GoogleSearch`/`ToolConfig`
and [Interactions generation configuration](https://ai.google.dev/api/interactions-api) expose
no documented hard query-count ceiling for built-in Google Search. Jobcu's request allowance
cannot enforce one inside the provider; prompt instructions or earlier observed counts are
not spending guarantees. Token maxima do not cap these query fees. Keep local estimates and
provider controls distinct, local token ceilings do not include every possible provider charge.

### Billing refusals and processing evidence — 2026-10-12

**Rechecked 2026-10-16:** Google's [billing documentation](https://ai.google.dev/gemini-api/docs/billing)
and [Interactions error reference](https://ai.google.dev/gemini-api/docs/api-errors) identify
exhausted prepay credit as HTTP 402 until replenishment. An active monthly spending cap is
separate from available prepaid credit; do not infer a particular account's balance from
this general contract. Delayed cut-off can create
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

### Transport diagnosis limits — 2026-10-16

**Checked 2026-10-16.** In [SDK issue #1356](https://github.com/googleapis/python-genai/issues/1356),
a reporter described a disconnect after a minute despite longer timeouts, then attributed their
own case to an unstable client network. The maintainer could not reproduce it. In
[issue #2705](https://github.com/googleapis/python-genai/issues/2705), a maintainer confirmed
TCP keepalive prevented a reported NAT idle-eviction case. That report concerns longer silent
calls and a different failure mode; it does not identify every pre-header disconnect.

These are competing diagnostic leads, not proof of Jobcu's network path or a reason to change
reasoning/model settings. The locked SDK passes the configured timeout to HTTPX and its server
timeout header. A controlled reproduction and private transport evidence are needed before
claiming an increased deadline, keepalive or another network policy fixes a particular failure.

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
See [implementation and limits](ENGINEERING.md#ai-providers-usage-and-recovery).

### Router reasoning and JSON formats — 2026-10-25

**Checked 2026-10-25.** OpenRouter's [reasoning tokens guide](https://openrouter.ai/docs/use-cases/reasoning-tokens)
documents the unified `reasoning` object (`effort` or `max_tokens`) and says Anthropic models
are enabled only through it; a top-level `reasoning_effort` is not documented there, although
its model list still accepts it. Small paid probes on zero-retention hosts with the same
calculation: two models on one host reasoned and answered correctly without a
`response_format`, but with a JSON schema or JSON object answered in about 20 tokens with no
reasoning and wrong values; `require_parameters` did not refuse those requests. Other tested
models reasoned with a JSON schema; one of them occasionally did not. Claude Sonnet 5.5 used
no reasoning on the probe with either control, also directly on Anthropic's API at medium and
high effort: its adaptive thinking decides per request, so zero reasoning there is the model's
choice, not a dropped control.

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
made for this check. Measured fictional limits live in [ENGINEERING](ENGINEERING.md#locations-and-travel).

**Storage/reuse rechecked 2026-10-09:** the [Routes-specific contract, section 19.3](https://cloud.google.com/maps-platform/terms/maps-service-terms)
permits temporary latitude/longitude caching for 30 days, not an unrestricted duration cache.
The policy's indefinite exception is for place IDs. Do not transfer another API's exceptions
to Routes durations, or claim that the coordinate exception authorizes stored travel decisions.
Code inspection confirms Jobcu's independently sourced town coordinates and exact-request
in-memory reuse; these differ from retaining yesterday's Google journey time. Current terms
and time-sensitive timetables do not authorize indefinite location-only route reuse.

## Native streams and selected reference pages — 2026-10-18

**Responses control check, 2026-10-19:** OpenAI's current
[Responses reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
documents `max_tool_calls` as a total ceiling across built-in tools: further attempts are
ignored. Jobcu sends the already allowed research count through that field. This controls
tool calls, while token/retrieved-content charges and account limits remain separate.
The same reference distinguishes completed, failed and incomplete responses and provides
usage separately from output. Error outcomes must retain received usage rather than erase it.
The [current Gemini Interactions schema](https://ai.google.dev/api/interactions-api) does not
document a corresponding per-request hosted-query ceiling. A prompt instruction cannot create
that guarantee. These are dated protocol facts, not comparative matching results or a reason
to switch a configured provider automatically.

Google's [Interactions API](https://ai.google.dev/api/interactions-api) supports streaming,
structured response schemas, medium thinking and `store=false` without a previous interaction.
The [streaming guide](https://ai.google.dev/gemini-api/docs/streaming) documents early lifecycle
events and final completion. The [error guide](https://ai.google.dev/gemini-api/docs/api-errors)
distinguishes invalid requests, refusals, quotas and retryable server failures. A partial
usage object is not a complete receipt. SDK automatic retries are disabled; Jobcu owns attempts.

[Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search) bills unique
queries for the relevant model generation, rather than one fixed fee per API request. The
current Google Search tool schema has no per-request query ceiling. An instruction asking for
four searches is not an enforced four-query limit. Directly supplied source text needs no
hosted search tool; input and output tokens still cost money. No invoice saving is established
by this contract alone.

The federal election authority's [official city/district tables](https://www.bundeswahlleiterin.de/dam/jcr/903d2260-fbd1-457f-a7d5-2580db9b0580/btw25_wbztabs_gesamt.pdf)
permit reproduction/distribution with attribution (PDF page 2). City rows can be split across
constituencies and multiple pages; counties and city states need their correct geographic
aggregation. Review the full geographic identifier rather than matching only the name
before a comma; an identically named surrounding county can occupy different table pages.
The [national results](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/bund-99.html)
provide the corresponding election baseline. A dated election file alone cannot establish
that a later election has not occurred.

[The PopuList](https://popu-list.org/) publishes classifications for public use with citation;
its [methodology](https://popu-list.org/elementor-page-1041/) explains coverage and expert review.
Version 4.0 covers national elections through May 2026; parties below its inclusion threshold
may be absent. Its vote-share graph is explicitly approximate and is not an official result.
Do not equate every unlisted party with a known negative category. Use official election
figures and explicit category coverage, or rigorous bounds for remaining unclassified votes.
Robots/access checks and the dated permission review remain required for each selected source.
Source selections, actual questions, evidence and verification receipts stay private.

**UK reference-data lead, checked 2026-10-19:** the [Commons Library data index](https://commonslibrary.parliament.uk/data/)
encourages re-use under the [Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright/open-parliament-licence/),
with its required attribution and no implied endorsement. Its independent
[election-results service](https://electionresults.parliament.uk/) publishes verified results,
CSV downloads, a public SQLite export and a [data dictionary](https://electionresults.parliament.uk/meta/data-dictionary).
The [election index](https://electionresults.parliament.uk/elections) separates general elections,
by-elections and notional boundary-adjusted results. These cannot be interchanged in a city/
national comparison. A constituency/region is still not automatically a whole city; verify
the population/election geographic units, complete counts and category definition first.
Recheck robots/access for the chosen independent host; a blocked download does not authorise
another route to that blocked host. No city verdict follows from finding the dataset.


The federal civic-education agency's [dated election profiles](https://www.bpb.de/themen/parteien/wer-steht-zur-wahl/bundestagswahl-2025/)
identify expert authors and distinguish programme descriptions from quoted party claims. Its
[current publisher notice](https://www.bpb.de/die-bpb/ueber-uns/service/impressum/) was checked
on 2026-10-18. Review the selected article's date, author, applicable rights and robots before
reading it automatically; retain attribution and do not redistribute complete articles. An
ideological inference from an expert description must be labelled as an inference, rather than
misquoted as an explicit binary classification. These references can address gaps in another
dataset's coverage; a short programme summary alone does not prove every category comparison.

## Completion-state contracts — 2026-10-19

The [Chat completion object](https://developers.openai.com/api/reference/resources/chat)
defines natural stops, length limits, filters and tool/function calls; usage is optional in the
response schema. A compatible host must confirm completion rather than merely supply parseable
JSON. Missing primary counts cannot establish a complete zero-cost receipt.

Anthropic's [stop-reason guide](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
distinguishes finished turns/stop sequences, output limits, refusals, pending tools, paused
server-tool loops and context-window exhaustion. Continuing a paused turn is an additional
operation; Jobcu does not silently buy it or switch models. Installed-SDK fictional fixtures
verify parsing, receipts and retained controls. They do not establish another host's tariff,
cache premium, access rights or real matching/grounding quality.

## Additional access boundaries

These retained access observations were recorded in September–October 2026. Adapter parsing
and request budgets are defined in `src/jobcu/sources/`; public accessibility alone does not
establish collection permission.

Recorded access boundaries also cover SmartRecruiters' API and iCIMS hosts whose robots rules
refused Jobcu, Hays/Rise Technical terms that restricted collection, EURES' partner route,
and blocked publicjobs.ie, UK Civil Service Jobs and DWP Find a Job interfaces. These were not
implemented as bypasses. Historical employer/board counts are not current vacancy coverage.

## Native Xiaomi interface — recorded 2026-10-22

The [Chat API](https://mimo.mi.com/docs/en-US/api/chat/openai-api) documents the native endpoint,
enabled thinking, JSON-object output and completion tokens including thinking. It does not
promise a literal medium control. The [Web Search guide](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/text-generation/tool-calling/web-search)
describes the separately activated plugin. Keyword/result limits do not bound total search
rounds or cost. Returned flat annotations do not establish passage-level citation mappings.

The [ordinary API agreement](https://mimo.mi.com/docs/quick-start/terms/user-agreement) and
[Token Plan terms](https://mimo.mi.com/docs/en-US/tokenplan/Token%20Plan/subscription) describe
different products/use restrictions. The [payment FAQ](https://mimo.mi.com/docs/en-US/quick-start/faq/payment)
describes delayed billing and possible negative balances. Alerts/prepayment do not establish
an exact currency ceiling. These are recorded interface/terms facts, not a provider recommendation.
