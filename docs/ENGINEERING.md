# Jobcu engineering

Current decisions, implementation and tools in one reference. Read the section needed for the
work. Rules: [AGENTS](../AGENTS.md); current work: [PROGRESS](PROGRESS.md); source permissions
and dated evidence: [SOURCES](SOURCES.md); development and private evaluation:
[CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).
Historical reasons remain in the [decision history](archive/DECISION-HISTORY.md).
Code/tests establish behavior; the latest current decision establishes intent.

## Current decisions

### API replacement decision refreshed — 2026-10-19

The [dated market refresh](SOURCES.md#api-market-refresh--2026-10-19) retains direct MiMo Pro
as the first comparison hypothesis, with the documented rights/controls and quality gates.
Readable privacy terms improve the assessment but do not settle third-party-use wording or
matching accuracy. Cheaper Haiku/Luna rates, newer aliases and promotional Mistral pricing do
not justify a silent downgrade. Preserve the selected provider/models and medium defaults.

Prioritise verified duplicate-work and usage/connection repairs while comparison dependencies
remain. Evaluate cited research separately and count actual tools, retrieved text and token
demand; another developer's benchmark cannot establish Jobcu quality or a complete bill.
No new account, provider switch, subscription or private-data transfer is implied by research.

### Responses completion, receipts and research bounds — 2026-10-19

Native OpenAI research sends its existing search allowance as the documented Responses
`max_tool_calls` ceiling. It limits total built-in tool calls; it is not an output-token or
currency ceiling. No larger allowance, model choice or hosted-tool entitlement is introduced.
Custom Responses endpoints retain their research-disabled policy until separately supported.

Both structured and research answers require `completed` status and no refusal. Truncation,
failed execution and unconfirmed/nonterminal states cannot supply facts or a match judgement.
Retain the available token/tool receipt on errors; successful answers without complete token
counts stay usable with explicitly incomplete usage. Output already contains reasoning tokens.
Known research activity followed by a failed incomplete bill reaches the shared cost guard.
Structured truncation retains both bills when the existing larger-output repair succeeds.

Eighteen locked-SDK regressions first reproduce omitted bounds, accepted partial research,
lost failure receipts and missing-usage crashes. Four additional cases protect partial counts
and once-only repair accounting. The native and custom structured paths share these checks;
medium effort, schema validation, source links and existing retry limits remain unchanged.
No paid provider request or live quality/cost claim was needed for this repair.

### Research failure with an incomplete bill — 2026-10-19

When research reports observed search-tool use and incomplete usage before a temporary
service/rate failure, stop automatic research on that provider/model path for this client.
Record the available lower bound once and explain the financial uncertainty without calling
it a proven connection failure. A queued later request receives the same stop before dispatch;
already running requests can still finish. Structured generation remains independent.

This supersedes automatic retry for that narrow failure case. Early temporary failures with
no observed searches and failed requests with complete receipts retain bounded recovery.
Successful answers and medium effort are unchanged. Six fictional client regressions first
reproduce repeated dispatch; locked native event-stream cases exercise failed status and
service-error endings after tool activity. Separate boundary cases protect transient recovery.
These checks establish the software path, not historical invoice allocation or measured savings.

### Employer-original matching evidence — 2026-10-19

For an already matched vacancy group, prefer usable complete text from an employer source
over longer complete board/aggregator text. Extra secondary boilerplate must not displace
an original experience, registration or language requirement. This supersedes longest-text
selection between all complete copies. Keep longer text within equal provenance; an empty
or incomplete employer description still yields to usable complete secondary text. A supplied
employer application link does not turn an aggregator description into employer-original text.

Eighteen fictional hardware/nursing/teaching cases first reproduce losing the original
requirement, across secondary source types and both copy orders. Four boundary cases protect
fallback and equal-provenance reuse. Both copies, identities and links remain available;
scores are calculated fresh from the chosen evidence. This changes selection inside an
already matched group, not vacancy-identity thresholds or any stored owner score/mark.

### Source workplace metadata before AI lookup — 2026-10-19

Complete supplied ad text does not establish a complete workplace. Detail readers can declare
that they supply missing town/country fields; JSearch does so. The normal full-ad stage checks
those fields even when usable text already exists, within the same source allowance and
failure controls. Lookup locale alone still cannot establish workplace country.

Reuse a cached country/town for the same workplace while preserving fresh complete text.
An explicitly changed town or country prevents copying the conflicting cached location;
resolve it through the detail reader instead. JSearch details that shrink earlier complete
text retain the richer text while adding independently supplied metadata and links. This
supersedes the assumption that any non-ellipsis detail description outranks complete list text.

Nine fictional regressions first reproduce skipped metadata, unsafe replacement and cache
loss across hardware, nursing and teaching. Existing date readers, source caps and admission
checks remain in force. More complete source evidence can avoid an AI lookup; live net cost,
coverage and original-ad completeness require the private comparison procedure.

### Silent AI stream termination — 2026-10-19

A Gemini event or content stream that reaches EOF without its required completion frame is
an interrupted, potentially billed request. Route it through the shared sent-request guard,
retain any receipt once, close the response and stop automatic repetition on that request
path. A plausible partial JSON answer or research passage cannot establish completion.
This extends the interruption handling in PR #150; an EOF was previously a generic outage,
so the shared client could repeat it and obtain a second billed answer.

Eight locked-SDK regressions first reproduce the repetition: both transports, structured
generation and research, with empty and plausible partial answers. The repaired paths send
one request, do not wait/retry, record one incomplete receipt and block a later repeat on
that path. Medium effort and recovery for known transient responses remain unchanged.
This establishes a software defect and its fixture behavior, not the upstream cause of a
historical connection loss or an invoice saving.

### Optional JSearch integration — 2026-10-18

The owner requested combining JSearch discovery with Jobcu's complete pipeline. The dated
[contract, terms and pricing](SOURCES.md#jsearch-assessment--2026-10-18) govern the isolated
`sources/jsearch.py` adapter. This supersedes its assessment-only status, without claiming
live coverage or savings. Existing sources, matching, medium effort and service limits stay.

`source_opt_ins` defaults empty for both new and legacy settings. A saved key is insufficient;
the Sources UI sends an explicit positive choice. Older clients preserve that choice rather
than silently enabling a new source. Full-ad recovery rechecks the switch. Before vacancy
requests a current direct Free quota receipt is mandatory; paid/unknown plans fail closed.
Atomic calendar-month reservations, provider-period remaining quota and an adaptive per-run
share all apply. Reserve each attempt before sending, including account checks; one-page
discovery and one-ID details avoid unknown batch charges. No automatic retry or credential
redirect is allowed. A failed source keeps collected jobs while other sources continue.

Reuse generated local-language/English role terms, interleave countries before cursor pages,
and retain older copies as date evidence. Existing full-text reuse runs before selective
details, under the same source cap. `FoundJob.source_context` preserves lookup locale without
inventing workplace country. Nullable/derived fields cannot establish precision, sponsorship,
salary or expiry. In particular, source coordinates do not establish a workplace address.
`application_options` survives pools and the existing short ad cache; links retain permitted
alternatives and existing blocked/reported-route controls. No redirect probing is added.
New dataclass defaults keep old saved records readable without a migration or mark rewrite.

Fictional hardware, nursing and teaching cases cover field handling, grouping, text reuse,
failure isolation and ceilings. There is no new AI stage. More unique jobs may add ordinary
matching/travel work; only an authorised equal-coverage comparison can establish net savings.

### Search behavior

| Decision | Reason and date |
|---|---|
| Reject career titles only when explicitly classified as clearly unrelated. Keep unreviewed titles for normal matching; preserve independent batch decisions and stop on critical account/quota/monthly-limit errors. Retain raw source counts and private rejection evidence. | Fictional searches reproduced unseen late titles disappearing, a bad batch erasing healthy decisions, and matching continuing after a limit error. Supersedes dropping all titles beyond the 3,000-pair early-screen bound or after a failed screen. The request bound remains; later matching of unknowns may use more AI, subject to existing limits (2026-10-08). |
| Read documents into a structured profile; reuse it only while documents, prompt and model are unchanged. Never reuse job scores. | Save repeated document work while keeping each search's judgement fresh (2026-09-17). |
| Show sought roles in profile progress; label the most recent role as history. Offer **Reset document understanding** to forget cached profiles and read again on the next search. | Completed study or placement work must not look like a requested role. Reset costs no AI calls itself, keeps documents/results, and preserves default reuse (2026-10-07). |
| Interpret changed queries afresh. The original every-search interpretation is **superseded** by exact-input setup reuse below. Conditions can name places, population, travel limits or researched facts; label estimates and unchecked conditions. | People's wording and intentions differ; no personal query is hard-coded (2026-09-17 to 2026-09-24). |
| Reuse successful location readings and search-word groups for up to 30 days when request inputs, prompts, schemas, provider/model/host and reasoning controls match. Rebuild conditions from current local data and fresh web research; never cache plans, scores or journeys here. | Repeated setup adds unnecessary requests and failure exposure. Migration 16 stores only validated setup answers privately; failed/partial groups remain retryable, and clear-search reset deletes them. Legacy snapshots lack request identity and cannot seed this cache (2026-10-14). |
| Interpret countries, places and condition types together in one medium-effort request; apply the existing population, travel and research checks afterwards. | Avoid asking the AI to read and classify the same request twice. Fictional country/commute/nursing checks verify preserved conditions; live speed and interpretation still need measurement (2026-10-07). |
| **Edit** reapplies corrected conditions to the same job pool and reuses earlier evidence. | Correct interpretation without collecting every ad again (2026-09-17; implemented 2026-09-21). |
| Report completion only after final results and status are saved together. If saving fails, keep available results visible and explain that closing Jobcu may lose them. | A finished heading must mean the latest results can be restored; a controlled fictional test reproduced completion preceding persistence after the Windows CI restore failure (2026-10-07). |
| Measure travel to the nearest edge of a reference place unless the user asks for its centre. | The person could live anywhere in the place (2026-09-24). |
| For Maps journeys into a reference city, compare the calculated edge point and city centre, keeping the faster available journey. Explicit centre requests still measure the centre alone; explain that sampling can miss faster districts. | A geometric edge can have a worse connection than the centre. Fictional regressions reproduce a reachable job rejected by an edge-only journey. This clarifies the anywhere-in-the-place intent above without claiming an exact fastest commute (2026-10-07). |
| Preserve confidence in facts about reference places separately from journey confidence. Keep usable partial rules, but explain missing facts and label estimates on each card. | A fictional city-library condition reproduced a measured journey upgrading unverified library access to verified. Distance, limit edits and Maps cannot prove that fact; scores and filtering remain unchanged (2026-10-08). |
| Explain incomplete reference-place facts in initial and edited search details. A condition's usable distance rule does not establish all its facts. Retire only resolved condition warnings on an explicit edit. | The outer near status can be estimate while reference research failed; counting it as checked omitted the shared failure explanation. Fictional full-search/library cases preserve usable jobs and unrelated source notes (2026-10-12). |
| Charge attempted Maps elements before each network attempt, preserve cached/earlier measurements and stop known persistent quotas. Keep transient recovery bounded and uncertainty visible. | A single budget charge before HTTP retries can exceed the owner's route allowance; quota scope and retry waits must not be guessed (2026-10-08). |
| Prefer original employer ads and full descriptions. Keep summary evidence and missing conditions labelled. | Missing text must not appear to be complete evidence (2026-09-17; clarified 2026-10-06). |
| Reuse bounded-age full text across matched copies before live reads; then prefer employer originals and try other permitted matched copies if needed. Recheck revealed objective facts before scoring. | A first-copy failure does not prove full evidence is unavailable; scores remain fresh per search (2026-10-08). |
| Exclude known CV-Library application destinations. Keep the same vacancy with another already-matched link, preferably the employer; otherwise exclude it with a counted reason. Preserve saved/applied history and original snapshots. | The owner reports that the application form rejects contact details from outside the UK. This is an explicit destination exclusion, not proof that every alternate platform accepts every applicant. Opaque redirect destinations still need verification (owner, 2026-10-07). |
| Let the person exclude an exact saved application link and undo that choice locally. Reuse an already-matched alternative or count the vacancy as left out before further matching. Keep other links on that site available. | Opaque redirects cannot establish their final host. A local report handles an observed unusable link without probing blocked pages, guessing URLs or classifying unrelated vacancies. No automatic final-host verification is claimed (2026-10-07). |
| Full-ad requirements replace earlier summary requirements, including an unstated experience minimum. Keep other blockers intact. | A fictional regression confirms that retaining the summary's years when the full ad says none leaves an obsolete score limit (2026-10-07). |
| Use original posting/closing dates and job memory to suppress expired ads and old reposts. Keep distinct requisitions distinct. | A board's refreshed date is not a new vacancy (2026-09-24; fixes 2026-10-03). |
| Greenhouse modification timestamps are never posting-date fallbacks. Read original publication/deadline from existing details and invalidate caches parsed under the old reader policy. | Missing originals stay unknown, and cached full text must not restore an invalid date. Supersedes the Greenhouse updated_at fallback; saved results are not rewritten (2026-10-09). |
| Prefer exact source IDs in job memory. Distinct IDs on the same employer source stay separate, including through other copies. Require similar text when both matching ads are complete. Keep ambiguous name matches as separate jobs; preserve all historical keys, marks and snapshots. | Fictional electronics, nursing and hospitality openings reproduced a fresh vacancy inheriting an old date or Not interested mark. Titles and templates do not establish a unique vacancy. Previously merged history cannot be automatically split without evidence (2026-10-07). |
| Groups kept separate by duplicate checks cannot rejoin solely through remembered names in the same batch. Exact copy evidence still wins; known countries can disambiguate. | The former one-card heuristic for two vague agency summaries could silently share Save/Not interested state without vacancy evidence. Supersedes that title-only assumption while retaining one card for proven copies (2026-10-08). |
| Explain scores with rubric parts and deterministic blocker limits; retain low-score jobs. | Users can see why a job ranks where it does; a score is not hiring probability (2026-09-23 to 2026-09-30). |
| The 28–35 role/skills band has a total maximum of 80; 18–27 → 60, 8–17 → 45, 0–7 → 30 stay unchanged. Only the 36–40 core-work band is uncapped by field fit. | Supersedes allowing neighbouring specialisations/gaps to reach an excellent total through level, language and country points. Judge actual daily deliverables and required domain, not employer/industry/graduate labels or shared tools (owner-directed scoring improvement, 2026-10-14). |
| Bound clearly mismatched experience/responsibility levels as well as role mismatch. The initial 0–5 → 50 and 6–11 → 65 caps are **superseded by the owner adjustment below**. | Strong skill overlap must not compensate for a level the rubric already calls clearly unsuitable; applies to all professions, including overqualification. This extends the earlier total-limit policy (2026-10-12). |
| Owner maximums: seniority 0–5 → 65, 6–11 → 80; required-language gap of exactly two CEFR levels → 80, three or more → 75. Keep point deductions, small/optional/implied-language treatment, exact-years rules and other limits. | The owner explicitly chose more forgiving totals with a separate threshold for larger language gaps. Lowest applicable limit still wins; saved scores are not rewritten. This supersedes the earlier experience caps and uniform language maximum of 65 (owner follow-up, 2026-10-13). |
| Ordinary mandatory-requirement points follow grounded met/unmet/unknown comparisons. Preserve known blockers when incomplete research omits them; explicit resolutions recompute points. | Supersedes accepting contradictory raw hard-requirement points in new scoring. Fictional comparisons reproduce an unmet eligibility condition retaining 14 points, and unsupported comparisons imposing definite limits. Existing band/limit values and separate policies remain (2026-10-09). |
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
| Retry incomplete employer discovery by country on a later search. Preserve completed countries and independently checked employers; account/allowance errors stop pending discovery. | Supersedes marking generic failures and blank answers as successful two-week refreshes. Legacy timestamps lack completion evidence and are rechecked once during normal use (2026-10-10; extends 2026-10-06). |
| Keep guides provider-neutral and link to current provider instructions/prices. Remove fixed model recommendations and unmeasured cost/runtime promises. | Capabilities and charges change; the restored Mac has no measured search baseline yet (2026-10-07). This supersedes the guide's 2026-10-03 provider recommendation. |
| Write everyday guides for first-time users: explain terms, give one clear action per step, name the actual controls and say how to confirm success. Put optional setup after the basic route; keep owner/Codex review instructions in their project documents. | Friends using Jobcu may have little technical experience. Plain language needs enough explanation to complete a task, rather than the shortest possible text (owner, 2026-10-07). |
| Keep concrete examples of richer place requests in README and the usage guide, including election vote shares, Turkish supermarkets, Sunday opening, student populations and combined commute conditions. Define thresholds and label research limits. | The examples help users understand the range of requests they can make; simplifying the guides should preserve them without claiming unmeasured accuracy (owner, 2026-10-07). |

### Evaluation

| Decision | Reason and date |
|---|---|
| During Review, Deep improvement or another authorized development task, assess the whole pipeline and choose improvements proactively, including independent judgement of saved evidence where authorized. Complete one verified improvement at a time. | The owner expects initiative beyond examples or the backlog (2026-10-08). The 2026-10-09 session decision supersedes any interpretation that Start should choose a new goal: initiative belongs within the requested task, without extra private access, paid-test budget or background searches. |
| Assess the incremental coverage and evidence from existing and potential job sources/search methods. Add or improve useful permitted methods; replace/remove methods demonstrated to add no useful value or harm results, accounting for unique relevant jobs, better evidence and backup value first. | The owner wants source decisions in both Review and Deep improvement (2026-10-09). Counts, duplicates and temporary failures alone cannot establish value; preserve recall and distinguish measured contribution from missing evidence. Evaluation method: [CONTRIBUTING](../CONTRIBUTING.md#4-measure-misses); terms: [SOURCES](SOURCES.md). |
| Sample full ads and labelled summaries across score bands; keep final scores, evidence completeness and the original location plan. | Avoid bias from summary omissions, duplicate-first selection or pre-research scores (2026-10-06). |
| Judge every top card independently before reporting precision; use a date-verified independent list before reporting coverage recall. | Counts and broad score bands do not prove search quality (2026-10-06). Procedure: [private review](../CONTRIBUTING.md#review-a-completed-search). |
| Focused paid reviews follow the owner's existing monthly budget and configured service limits, with current verified prices. No fixed EUR1 review allowance or per-search money cap is imposed. | The earlier review prompt's EUR1 permission applied only to development review, never ordinary searches. The owner removed that restriction; a session-ending instruction still stops new paid work (2026-10-07). |
| Assistant ratings may fill empty labels or revise prior assistant labels; owner and legacy labels are protected atomically. | A concurrent owner edit must not be overwritten by a review. Fictional controlled-order tests cover the read/write gap (2026-10-07). |
| Record step time and answer-wait time; label correction timings separately from cumulative usage. | Corrections and full searches cannot be compared as equivalent performance runs (2026-10-06). |
| Warn when scoring reads only an excerpt of a lengthy ad. | Unseen requirements must not be assumed satisfied (2026-10-06). |

## Receipt admission and bounded spending — 2026-10-17

Successful generation/research usage is recorded while its request slot is occupied.
Research allowance accounting also happens there: atomically convert the held reservation
to used searches before writing its receipt, so a sibling cannot count both or be falsely
deferred. Release each reservation once on success/failure; keep the receipt inside the slot
before queued monthly checks. Error receipts already follow this rule. Preserve exactly one ledger entry
per actual attempt, including format repairs, truncation and Stop after a complete answer.
Paused-ledger regressions first reproduce queued dispatches against stale token/money totals,
then prove those same owner limits prevent them for structured and research requests.

This does not bound a provider's internal hosted-search loop. A request allowance is not a
server-enforced query maximum, and a token maximum does not bound search fees. No bounded
paid research experiment is safe merely because the previous call was cheap: verify an
enforceable bound before offering a monetary ceiling. Keep raw research storage/display
constraints and the owner-selected model/effort; do not adopt an unverified cheaper path or
silently reduce candidates/evidence to manufacture a savings claim. The UI/guide explain that
in-flight provider searches and missing receipts can exceed local estimates.

## Coordinated connection recovery — 2026-10-17

After a transport interruption, `AIClient` admits only one real queued request at a time
on that provider/model/request-kind path until a successful answer restores ordinary
parallel work. It sends no separate probe, drops no jobs and changes no evidence, reasoning,
per-request retry bound or owner limit. Research and structured paths remain independent;
a successful structured answer cannot release an interrupted research queue. Requests already
in flight finish normally. Stop and account refusals still prevent queued dispatches.

Recovery queue waits are logged separately from attempt time and retry sleeps, without
payloads. Waits can overlap other work. Fictional concurrent-outage regressions preserve every
answer and usage receipt, prevent other paid attempts while the recovery request is pending,
and prove parallel work resumes. This prevents a particular source of repeated failure costs;
it does not guarantee a live provider recovery, a lower invoice or a fixed cost per search.

## Chat and Messages completion receipts — 2026-10-19

Compatible Chat and native/custom Messages retain reported input/output/cache/tool counts on
truncation, refusals and invalid completion states before raising a typed error. Missing primary
counts remain unknown, preserving available counts rather than claiming a complete zero bill.
A completed usable answer survives missing usage, with the existing incomplete-estimate notice.
The bounded structured truncation repair records both attempts once and preserves medium.

Unfinished tool turns, unconfirmed stop reasons and unsupported message bodies cannot become
completed facts. Messages context-window exhaustion is terminal: increasing output room cannot
repair that input/context limit. Completed stop sequences still pass normal schema validation.
Research retains sources and its existing web-use ceiling; no host, model, reasoning or schema
negotiation changes. These are response/accounting contracts, not a live provider-quality test
or a guarantee that configured tariffs include every provider-specific fee. Dated protocol
references are in [SOURCES](SOURCES.md#completion-state-contracts--2026-10-19).

## City evidence and connection dispatch — 2026-10-18

`reference_sources.py` reads explicitly reviewed public references before hosted research.
Private settings retain exact-condition identities, source addresses, country/city scopes,
reviewed aliases/geographic identifiers, dated permissions and optional whole PDF pages. They retain no verdict or
source text. Every new check reads the pages again, respecting robots, access refusals and
request budgets. Comparisons are grouped by country, with up to 16 relevant reference pages
per city batch and the unchanged total-text bound. Additional references or an overloaded
batch cannot disable independent countries. Missing, oversized, redirected or unreadable
references cannot establish a
fact. The chosen model compares supplied evidence at medium effort without a hosted search
tool; unresolved cities remain eligible for ordinary research. A failed paid comparison stops
that recovery path instead of buying a second research operation.

Reviewed CSV references can optionally select exact columns and row values before the
400,000-character comparison bound. `EvidenceCSV` records the delimiter, ordered columns and
AND filters with exact allowed values; it never infers a city from a name fragment. The whole
fresh UTF-8 table must fit the unchanged 8 MB download bound. Duplicate/missing headers,
malformed records (including discarded rows), missing filter columns and empty selections
reject that reference before any paid comparison. All matching rows and selected cells,
including zeroes and quoted multiline values, survive. An oversized projection is rejected
whole; no first-rows truncation. Geographic labels and citations are checked against the fresh
projection, with the original source address retained. Selecting rows does not establish that
their geographic units cover a whole city, or that omitted columns are irrelevant; both belong
in the source/scope review. Existing HTML/PDF references and unselected CSVs keep their path.

An optional `CSVCalculation` groups explicitly reviewed columns and adds strict integer
measures locally. Every remaining selected column must be constant, except declared row
identity fields; a varying undeclared qualifier rejects the view. Explicit `separate_values`
keep reviewed collective labels as separate records rather than one shared member. Missing/noninteger cells,
malformed rows and unknown columns produce no partial result. Blank grouping values keep
separate source-row identities even when their names repeat. The convenience unlabelled
subtotal does not make those records one member. All rows contribute to exact group/grand
totals and record counts. The compact view keeps constant geographic/event context in every
row; a dropped reviewed geographic identity prevents paid comparison.

The original projected rows remain available for quotation validation within the unchanged
8 MB download bound. AI input uses the calculated view within the same per-source/combined
400,000-character budget. `Quote.kind=calculation` validates only against current local output;
`source` still validates against source text. Invented totals, disguised publisher quotations
and unavailable calculation views cannot pass. Accepted calculated evidence is labelled as
local arithmetic, with the original URL retained. This removes AI row addition without caching
facts or choosing categories; comparable units, classification and semantic review still matter.

`must_cite_for_towns` records sources a review found indispensable for a particular condition's
comparison. An unavailable required source, or a missing required city identifier, prevents
buying that city's supplied-reference comparison; other cities remain available. Each city's
prompt names its required source IDs. A known answer must cite exact current text from every
dependency, with city-specific identity in each required city source. A geography/context
citation cannot stand in for an omitted measurement, nor can another city's row borrow identity
from a separate source. Country context can be a dependency without claiming city scope.
This opt-in dependency review complements quotation checks; it does not prove the semantic
correctness of figures or category reasoning. Unsupported findings remain unknown.

Answers require unique city IDs, explanations and exact supporting quotes. Country-only
evidence cannot establish a city fact; shared-table evidence must name the requested city or
a reviewed alias. When a source supplies a reviewed geographic label/code, the page must
contain it before buying a comparison, and the city citation must include it. A same-named
county cannot substitute for that city. Missing IDs, unsupported quotes and unresolved
comparisons retain their specific unchecked explanation without becoming accepted facts.
Preserve complete table headers and all rows needed for the whole city;
constituencies and counties are not interchangeable with cities. Comparisons require the same
event, geographic unit and category, or rigorous conservative bounds. Every unclassified
named member must remain in those bounds as well as the Other row. Shared members must have
the same category membership in both units. `ai/instructions.py` supplies this rule to fresh
reference comparisons and hosted research: bound the city-minus-national difference jointly
instead of combining incompatible separate extrema. Unknown members' positive differences
raise its maximum; negative differences lower its minimum. Apply the requested operator and
strict/inclusive boundary. For an at-or-below request, a maximum at zero qualifies, a minimum
above zero contradicts it, and a remaining overlap stays unknown. Distinct independent
candidates cannot be merged into one member. Separate share intervals can overlap while the
joint difference proves the comparison; this does not resolve missing geographic data or
invent category assignments. For a proven city subset, the national count of a shared member
cannot be below its city count. That lower count bound can bound the difference when a fuller
national figure is absent; it is never an invented exact national count. Quote validation proves
provenance, not the correctness of the model's interpretation. Source selection and live
semantic verification remain necessary. Population rules, candidate coverage, journey
admission and fresh job scoring are unchanged. Whole-city comparisons receive 20,000 answer
tokens plus the existing medium thinking room: 32,000 tokens on the first attempt. The shared
client still owns bounded truncation recovery. A smaller
allowance could end before the final city answers; this reserves space without lowering effort.
Actual billed tokens still need receipts; the larger allowance is not a cost ceiling.

Supported native models now use a stateless event stream for generation and research:
`store=False`, `background=False`, no previous conversation ID, the selected model/effort and
no SDK retries. Lifecycle events let the HTTP response begin before a long answer finishes.
Only terminal success is accepted. Final output replaces streamed fragments; citation offsets
are UTF-8 bytes. A complete usage receipt needs explicit input/output/thought/cache counts;
partial receipts remain unknown. Documented refusals, invalid requests, quotas and outages
retain distinct handling. Unknown future model IDs retain the legacy endpoint; an account
refusal never triggers a different endpoint or model.

Across providers, a connection failure proven to precede dispatch can retry. A lost reply
after possible dispatch records unknown usage and suspends further automatic requests on
that provider/model/request-kind path for the current client, including queued work. Explicit
saved-evidence recovery creates a fresh client. This supersedes automatically repeating an
ambiguous paid request: the provider may already have charged for it. Other request kinds and
completed evidence remain usable. This bounds duplicate attempts; it does not identify the
external component that closed an earlier connection or prove invoice savings.

## Native event transport candidate — 2026-10-16 (superseded)

Before the 2026-10-18 protocol and dispatch repairs above, the stateless native event-stream
candidate in draft PR #137 was not adopted: offline contract tests alone did not establish
live availability or complete recovery. The earlier checkpoint required bounded verification
of complete answers, citations, usage and dispatch behavior before replacing the old endpoint.
Those earlier paid packets are closed; their private receipts remain available. An account
refusal must never be retried through another endpoint or bypassed by raising a limit.

## Job types and online research — 2026-10-16

The broad `full_time_permanent`/`fixed_term` pair can describe a source's unspecified
full-time contract. It does not contradict an ad's student/placement classification:
student work may be full-time. `pipeline.job_types_of` accepts that refinement while
preserving a source's single explicit type and other conflicting readings. An `unclear`
answer never becomes an excluding job type when source evidence is absent.

`search._ad_exclusion` supplies the same job-type and fully-remote decisions before extra
online checks and when building final cards. Keep candidates for final counts and saved
evidence, but omit proven exclusions from research requests. Unscored/unknown jobs remain
eligible. Fictional electronics, nursing and teaching searches exercise wanted/unwanted
student roles, excluded remote work and unknown types without provider traffic. This proves
request admission and output behavior; it does not measure a live invoice saving.

## Location admission and UK sponsorship — 2026-10-16

### Reference conversion efficiency and recovery — 2026-10-16

`reference_places.py` keeps full research notes in the conversion prompt, but replaces repeated
grounding excerpts and opaque URLs with city-specific source IDs. Actual links/passages remain
available to the same source validator. Missing model IDs can be recovered only from provider
links covering the entire decisive excerpt inside that one city block. Explicit wrong IDs,
cross-city excerpts, signs/negations and incomplete evidence retain their safeguards. If an
available provider map supplies no usable city links, no conversion call can pass validation;
skip that paid conversion and retain unknowns. Providers without passage maps keep their
existing source format and validation.

A complete searched answer with usable sources/complete usage can survive a later conversion
failure in transient search memory. Reapplying that same search in the same app process can
reuse the exact request's answer for up to one hour, within a 32-entry bound. Identity includes
search ID, route/model/effort controls, fact, ordered city identities and research prompt/limits.
An app restart, new search, changed identity or expiry needs fresh research. Nothing enters
saved snapshots, preparation storage or a cross-search answer cache. Journeys and scores are
not reused by this mechanism; monthly/Stop checks still govern new conversion requests.
Completed conversion retires its raw answer, even when the judgement remains unknown, so
genuinely missing facts can be researched afresh instead of repeatedly converting old notes.

Fictional tests cover same-search recovery, omitted IDs, empty/foreign links, prompt retention,
route/fact/scope/age invalidation and snapshot privacy. Medium effort, candidate coverage,
research freshness and scoring rules stay unchanged. Input reduction and avoided calls can
be measured; a shorter prompt does not establish a live latency improvement, invoice saving
or the cause of an external disconnect. Private diagnostics and native receipts stay private.

Private logs also record each AI attempt's ID, step, elapsed request time and outcome, plus
actual AI retry/source wait duration separately from the requested duration (including Stop).
No prompt, key, response or account identifier is added to these timing events. Existing
answer-wait timing remains separate. Concurrent request durations overlap and must not be
summed as elapsed search time. These events prepare observation of the next owner-started run;
they do not start monitoring or provider work by themselves.

### UK sponsorship deduction and admission guards

The owner requested a five-point deduction on every UK vacancy without an explicit offer of
visa sponsorship for that vacancy. `scoring.py` retains the vacancy country and proposed offer
with its exact clause. An offer needs the positive model classification, a literal supported
quote and an explicit positive offer; negative, conditional and company-wide licensing wording
does not qualify. Ground online research within the individual job paragraph. A person's visa
eligibility cannot establish an employer offer. Apply the deduction after the existing lowest
maximum, floor at zero, retain the rubric parts and show the deduction separately on cards and
score tooltips. Rejudging or recovering requirements cannot compound the deduction. New
scoring uses the rule; historical saved scores are preserved. Use the score before this
deduction for the existing incomplete-ad research gate, so the missing offer cannot prevent
its own verification. No additional request stage is added.

`travel.py` no longer treats the population-derived city radius as proof that a workplace in
another/unknown town is inside that city. This supersedes the old automatic zero-minute radius
shortcut; named reference-city workplaces still qualify, while a requested city centre requires
a journey from an address away from that centre. Old geometric zeros and journeys retained for
different workplace coordinates cannot establish a pass. Measuring only the nearest two cities
cannot establish a failure while other eligible cities remain in possible reach. Preserve those
jobs as unknown and name the unmeasured alternatives; keep a demonstrated passing journey.
The nearest-city sample count and retry policy stay unchanged. Workplaces previously given a
geometric zero now use the existing journey checks and service limits. A sampled city edge
remains approximate; it is not a surveyed municipal boundary.

Nationality/security uncertainty has a separate explicit score note containing the retained
wording. A conditional screening clause does not establish personal ineligibility; explicit
excluding nationality rules retain the existing 30-point maximum. Do not turn alliance membership
or a clearance acronym into an invented eligibility decision. Relevant official guidance and
application-route permissions remain in [SOURCES](SOURCES.md).
Fictional engineering, nursing, teaching and hospitality regressions cover the scoring rule;
finite fictional cities cover stale origins, geometric zeros and unmeasured alternatives.
Offline regressions do not verify a real journey or repair previously missing reference facts.

## Saved evidence recovery — 2026-10-16

**Retry incomplete checks** operates on the latest retained pool and location plan. It does
not call job collection or change the owner's form, provider, model, reasoning or limits.
It can read permitted missing details during ordinary reevaluation. Its preview performs
local validation only; pressing Retry is the point that can use AI.

An unchanged finite reference-city condition retains its interpreted scope. Population/name
rules rebuild the complete candidate set; only sourced, supported, timestamped city facts
checked within one hour are reused. Legacy, invalid or expired timestamps require fresh
research. Missing facts use the existing groups of eight; an exhausted connection failure
stops remaining groups. A changed eligible destination set invalidates prior travel outcomes.
This narrow same-search recovery does not create a cross-search research cache.

Research replies can retain provider-linked note passages separately from a page list.
Gemini streaming accumulates grounding chunks in arrival order, resolves support indices
against that complete list, and retains only unique literal non-thought passages. Reference
extraction receives the passage-to-source-ID map; when that map is available, a citation must
be linked inside the same city's paragraph. Ambiguous/repeated text, missing links and another
city's source remain unknown. Opaque redirect URLs and identical domain titles alone cannot
reconstruct those associations. This preserves provenance without another AI request; it does
not verify the source's factual accuracy or the model's complete interpretation. Current
comparisons must use the latest comparable published facts or explain the specified event.
See [provider contract](SOURCES.md#grounding-passage-links--2026-10-16).

Ordinary requirement grounding now retains the proposed verdict and local validation failures
in private evidence, including results extracted from online notes. Legacy unknowns have no
retained proposal: valid quotes or high points cannot reconstruct a lost verdict. Free
revalidation can recover a retained proposal only from the actual complete scoring text.
Remaining explicit unknowns in full ads use focused, numbered comparisons against the saved
profile. Missing/duplicate IDs cannot erase evidence, confirmed blockers are untargetable,
and unsupported quotes remain unknown. Only the ordinary-requirement judgement changes;
other score components and independent warnings remain. Summary-only jobs require their
original evidence instead. Standalone list bullets can move between lines without invalidating
the same adjacent quoted sentences; words and negations are still required. AI explanations
describe uncertainty but are not verified facts.

Recovery honors the existing scoring continuation question and monthly controls. A failed
comparison stops queued work; already running requests can finish. Completed pool work and
usage survive Stop or a later failure. Cards rebuild on completed reevaluation. Reopened
clients restore reported web usage for the same search ID across providers, excluding employer
discovery's separate allowance, so a correction cannot silently obtain a fresh allowance.
Missing usage remains unreported; local
estimates and planned native-search reservations cannot guarantee the provider invoice.
Fictional tests cover the API/CSRF boundary, no new collection, limits, failed/ambiguous
answers, preservation and quote recovery. They do not establish live provider availability
or resolve missing external facts in historical results.

## Reasoning-preserving request recovery — 2026-10-15

Native adapters previously treated every bad request as a possible unsupported reasoning
control. An unrelated schema, input-size or tool error could trigger a second request without
the chosen effort and remember that omission for later requests/searches. Research remembered
it even before the fallback succeeded. Six fictional generation/research controls reproduced
the unrelated-error behavior before this repair; this is not evidence of a real-run HTTP 400.

Adapters now classify a separate `AIReasoningUnsupported` only from an explicit whole-control
refusal in the provider's error message, or an OpenAI unsupported-parameter code naming that
control. Classification does not scan diagnostic envelopes, quoted schema fields or private
request content. Unsupported effort values, conditional thinking/tool errors and unrecognized
wording remain bad requests. Custom protocols retain their strict reasoning contract.
The [current native contracts](SOURCES.md#native-reasoning-refusals--2026-10-15) distinguish
control support from supported levels and provider defaults; they do not establish error
wording for every model or host.

| Fictional behavior | Before | After |
|---|---|---|
| Unrelated native bad request | Retry without effort; later requests can inherit the omission | One dispatch; preserve medium on later requests and fresh clients |
| Explicit whole-control refusal | Compatibility retry | One compatibility retry; a second refusal stops |
| Failed research fallback | Unsupported-control cache written before success | No new cache entry |
| Invalid JSON or blank research fallback | Could establish unsupported-control cache | Generation must validate; research needs nonblank text |

Available usage from malformed and failed replies is still recorded. Successful genuine native
compatibility recovery remains; complete answers, bounded outage/format retries, medium defaults
and independent work are preserved. The request comparison proves avoidance of an inappropriate
retry, not measured live savings, matching quality or provider/network availability. Saved
pre-header disconnects lack the transport evidence needed to identify their cause. No paid
call, new search, service limit, provider/account/network change or owner-app restart was used.

### Subsequent bounded connection diagnostic — 2026-10-15

An authorized isolated native-generation pair used one fixed fictional six-ad profile,
medium effort and one physical dispatch per request, with hosted tools disabled. Both JSON
answers completed without retries, reported usage and retained all six decisions. Headers
arrived in 6.84/3.48 seconds and completion took 8.01/7.46 seconds. The second request enabled
rolling thought summaries; this single sequential pair cannot separate that setting from
ordinary variation, request order or provider caching. It does not justify changing production
controls or establish equal matching quality. Unstated secondary qualifications still need
unknown treatment even when a decisive mandatory mismatch supports the overall classification.

The diagnostic stopped after this pair. Complete answers, phases, known usage and limits stay
in the private checkpoint; actual test usage was added to the monthly ledger without changing
saved searches or ratings, and the disposable key/settings/database copy was removed.
No job search, hosted research, provider switch, app restart or network change was made.
These short successes do not reproduce the saved longer hosted-research pre-header failure.
Further short passing requests would not resolve that missing evidence. A research-path
reproduction first needs its permitted display/retention contract and a bounded test scope;
credit balance and basic host reachability alone cannot identify a transport failure.

## Original-ad section recovery — 2026-10-15

The common JobPosting reader now retains separately supplied responsibilities, skills,
qualifications, education/experience and work/applicant eligibility text. Known credential,
DefinedTerm and experience-month forms become readable evidence; unknown objects, absent
values and linked-only credentials do not become facts. Requirement wording, preferences,
operators and experience-instead-of-education flags survive. Duplicate handling keeps field
context and distinct skill names. Fields without an actual ad body remain partial evidence.

SuccessFactors previously kept only the first `itemprop="description"` block; it now reads
all sections belonging to the job, separate marked requirements and JSON-LD originals.
Nested descriptions are read once, unrelated employer/other-vacancy blocks are excluded,
and a short visible fragment cannot hide a fuller structured body. Feed dating uses the
already downloaded page's job text too, including when its date is missing; the date stays
unknown. Longer Dutch government page extraction also retains separate structured fields.
Six affected readers use cache version 2, including direct sitemap/feed cache calls. Old
incomplete caches are refreshed within existing limits; corrected warm caches avoid requests.

Fictional hardware, nursing and teaching regressions reproduce seven original section-loss
failures and compare recovered evidence in the scoring prompt. They also check mixed markup,
negations, partial originals, metadata isolation, cache refresh/reuse and no extra page calls.
This establishes evidence retention, not live matching accuracy, market recall or net savings;
longer complete evidence can itself require more scoring tokens. No score rubric, AI effort,
provider, source budget, private history or application link is changed. Existing saved cards
are not automatically rescored. New requests still need their normal authorization.

The [current source/access evidence](SOURCES.md#original-ad-sections-and-access-boundaries--2026-10-15)
also establishes a scoped hold for SAP-owned websites. Entry points reject these before robot
or budget work; the HTTP destination guard prevents a redirect from contacting them. Other
employers continue independently. This does not broaden source permissions or authorize
research through a restricted site.

## Workplace-scoped city checks and complete journey rounds — 2026-10-18

Initial searches and saved-condition recovery now schedule finite reference-city research
after source collection, quick relevance and full-ad reading. `Anchor.reference_deferred`
represents scheduled work, not a failed check. `reference_places.resolve_for_jobs` unions
the population/name candidates within the collected workplaces' existing geographic travel
bounds for each shared interpreted fact. It sends only unresolved relevant cities, then the
normal source/citation checks establish eligible destinations before timed journeys or scoring.
Standalone/open-ended conditions retain their existing path. No model, effort or limit changes.

Completed sourced facts belong to the unchanged condition of that saved search; recovery does
not buy them again just because the one-hour transient research-note memory expired. New
searches still research fresh facts. Unneeded unknown placeholders are omitted from the result,
while `unchecked_reference_towns` recalculates absent candidates when another workplace needs
them: omission cannot become a pass or a negative decision. Missing workplaces remain blocked.
Country/municipal identity, comparable event and category-source requirements remain intact.

`travel.NEAREST` is now destinations per round, superseding the earlier two-candidate total.
Failed nearest journeys automatically advance to the next geographically reachable eligible
cities, stopping at the first pass or after all candidates are measured. A failed/incomplete
round stops that origin without repeatedly dispatching other alternatives. Every completed
round is retained before the next request. Identical workplaces share validated measurements;
completed cells are not repurchased, and Maps readings take priority over older AI estimates.
The configured Maps/AI limits and labelled estimate fallback still apply. These samples retain
the city-edge/centre limitation; testing all cities does not test every possible city district.
An oversized matrix does not block a later smaller matrix that fits the remaining allowance;
only the normal atomic budget can admit either request. Limit notes describe a batch that
does not fit, rather than incorrectly declaring the entire allowance exhausted.

Population cutoffs now round fractional people upward in both workplace and reference-city
rules: a place below the requested country share cannot pass through rounding down. This
corrects arithmetic, not the observation dates or precision of the shipped population dataset.
Fictional engineering/nursing/teaching flows verify full-ad workplace correction before facts,
shared work, third-city admission, complete negatives, interruptions, failure stops and reuse.
Request counts establish those cases, not live invoice savings or universal source availability.

## Finite reference evidence and source recovery — 2026-10-15

For a travel condition with a known population or named-place rule, `reference_places.py`
selects candidate cities locally before researching the remaining fact. This supersedes asking
for a complete minority/complement list across whole countries for that bounded case. The
existing open-ended method remains for standalone country/town conditions, unknown named places
and scopes larger than 400 cities; no candidate list is silently truncated. Multiple travel
conditions about one fact share the union of their candidates and one research request.

Fresh notes use a separate city ID for each candidate. Structured outcomes must have one unique
row/paragraph, a literal excerpt in that city's paragraph and a citation from the returned
sources. No searches, no citations, missing/duplicate IDs, foreign-city excerpts and estimated
answers remain unknown. A positive answer requires the whole stated condition, while one
supported contradiction can establish a negative. The AI still reads the source evidence;
local population/name selection and travel decisions do not require another AI judgement.
Citation membership and an excerpt establish provenance, not independently measured source
accuracy; live comparability, interpretation and coverage still require verification.

Each city keeps its own outcome and cited excerpt. Supported answers survive missing rows;
no omitted city is implicitly acceptable. Only confirmed suitable cities can trigger journeys.
A supported journey can prove a pass despite an unknown alternative; a negative decision stays
unknown if an unchecked candidate could still be in reach. Local size edits preserve old facts
without inventing evidence for newly eligible cities. Old journey entries cannot qualify through
an ineligible reference city. Complete notes remain available in flight if organizing them
fails, but are excluded from saved/API serialization. The initial proposal to retain raw notes
in saved results is superseded by the checked provider retention restrictions below. Individual
outcomes and cited excerpts remain in the end-user result. The optional condition
editor exposes city outcomes and permits rechecking partial results. Its labels distinguish
missing city facts, unfinished journeys, AI estimates, Maps and local calculations.

The source HTTP client's DNS check now caches absence only for definite name/no-address errors.
Temporary DNS and generic resolver failures keep normal bounded retries and do not poison the
per-search hostname cache. This does not bypass blocking, change an endpoint, increase request
limits or remove Retry-After/Stop checks. Fictional failures reproduced a lost source response
before the fix and successful recovery afterwards; genuinely nonexistent hosts still stop early.

Fictional before/after checks cover smaller workplaces near acceptable reference cities,
confirmed negatives, unknown alternatives, all 30 countries, engineering/nursing/teaching,
missing citations, duplicates, edits, in-flight notes without hidden retention and shared scope.
The bounded-city case uses the same research/formatting requests, medium controls and allowance;
an empty local candidate set needs no research. No paid call, new search, provider/account/network
change or owner-state reset was needed. Actual research latency, net savings and live matching/
market recall are unmeasured; this repair does not guarantee external service availability.

**Retention correction, 2026-10-15:** [checked service restrictions](SOURCES.md#long-ai-answers-and-streaming)
supersede unrestricted raw-note retention. Excluding these new fields from serialization avoids
introducing a hidden archive; no real research call or stored owner result used the new fields.
Existing owner history is preserved. Durable raw-answer recovery needs a verified display,
retention/expiry and reuse policy before enabling it. This correction does not certify every
existing hosted-tool use; verify its exact end-user refinement/display contract before paid
hosted-research experiments or transferring/reusing grounded output elsewhere.

## Duplicate boundaries and reference eligibility — 2026-10-15

### Confirmed copy history and date readers — 2026-10-17

Recruitment prefixes and a title's own employer/place suffix are comparison context, not new
roles. Removing them requires strong matching ad evidence. Recruiter parent/division labels
also require matching role, workplace and text. Levels, specialist words, reference numbers,
country differences, contradictory full ads and distinct native employer requisitions remain
guards; a shared name, boilerplate or neighbouring town alone does not establish a copy.

Migration 17 links historical IDs only when currently available copies pass duplicate checks.
It keeps every job, key, snapshot, rating and raw mark. Linked copies use the earliest first
showing and combine current marks; an explicit later mark change applies to the whole linked
vacancy. A recycled board copy cannot bridge two remembered native employer requisitions.
Unproved name ambiguities remain separate. Saved-result responses combine confirmed copies
and remove proven old reposts without rewriting the saved search. Disagreeing old assessments
stay recorded but do not become a chosen higher match score; a new assessment is needed.

Complete text does not establish that every relevant date reader succeeded. Try remaining
matched metadata readers after another fails or supplies cached full text, within existing
source budgets. Cache checks are tracked per copy and progress counts groups once. A permitted
original can then establish an older date or deadline before paid scoring; failed/missing
metadata stays unknown. The [BA source hold](SOURCES.md#bundesagentur-access-hold--2026-10-17)
is independent of this recovery and cannot be bypassed with a fallback reader.

Unicode dash punctuation separates words before ASCII accent folding. Previously a nonbreaking
dash could join tokens, so otherwise matching copies became separate scoring units. Fictional
power-supply, patient-care and early-years titles now form one group and one assessment while
keeping original text, links and earliest posting evidence. Different countries/workplaces,
seniority, employer requisitions, conflicting full ads and staffing-agency guards remain.
Remembered identity also tries the exact older normalization spelling; existing source keys,
marks and history are not rewritten. Ambiguous names still cannot establish identity.

Reference-city facts must be applied before either distance/travel can decide a condition or
the travel meter requests Maps/AI durations. Missing, estimated and legacy-unproven facts keep
the job unknown and available, without presenting a population-only destination as eligible.
Previously recorded routes remain intact but cannot prove another city fact. Verified facts
resume normal measurement; sufficient partial journey evidence and existing per-search reuse
remain. An explicit owner replacement of eligible/excluded places is their rule; editing only
minutes or population does not confirm a missing fact. This supersedes measuring population-only
fallback destinations after reference research fails. Avoided route requests are verified in
fictional tests; net live savings and provider/network recovery are not measured. More unknown
candidates can remain for scoring, so avoided routes alone do not prove a lower total bill.

Cards group distinct uncertain/estimated explanations under a visible, keyboard-accessible
**Needs checks** disclosure instead of repeated question marks. Verified facts, failures and
completed-evidence information remain visible. Details and historical snapshots are preserved.
**Maximum** describes a score ceiling even when the parts total is lower; every reason retains
its own ceiling. Scoring policy and medium effort are unchanged.

Native Gemini response cleanup now preserves a successful terminal answer and its citations
when closing the HTTP body raises a transport error. It also preserves a refusal/truncation
error and received usage instead of replacing them with a raw cleanup exception. Cleanup still
attempts each thread-owned resource and clears thread-local tracking; uncertain trailing usage
stays explicit. Three real-SDK fictional streaming regressions failed before the fix and pass
after it, including one completed assessment without another request. This reproduces a related
failure path, not the cause of pre-answer disconnects in a saved run. Native medium, retry limits,
token/tool accounting and incomplete-answer rejection remain.

The authorized saved review/checkpoint, original run-boundary measurements, failure/request
limits, billing scenarios and independent judgements remain private. Missing originals and an
eligible independent benchmark prevent whole-results accuracy or recall claims. A connection
break is not evidence of exhausted credit. Current public prices remain in [SOURCES](SOURCES.md#gemini-running-costs);
incomplete failed-request usage, tool allowances, other account work and direct Routes billing
must be separated from the token-only estimate. No source/provider switch, paid test, new
search or owner-state change was made. Automatic Adzuna destination replacement retains its
explicit-permission/interface dependency; independently collected originals remain usable.

## Task focus and scoring confidence — 2026-10-14

The scorer first compares the occupation, main deliverables and specialist knowledge. Related
tools or a shared sector cannot establish a direct target-role match. Existing role bands now
bound every non-core total: 28–35 points → maximum 80, then 27/17/7 → 60/45/30. Lower
experience/language/eligibility limits still win. A fictional neighbouring role with 31 role
points and 20/15/10/15 other points changes from 91 to 80; a direct 40-point role stays at 100.
Jobs remain available; this changes ranking, not collection or filtering. Model band selection
still needs accurate interpretation; the pure rules comparison is not a live quality claim.

Mandatory evidence includes specific technology/domain/practical skill prerequisites even when
phrased as experience, while duration/overall seniority use their own fields. A degree alone
cannot replace the required-skills checklist; absent expertise stays unknown. Document reading
preserves stated basic/introductory proficiency instead of flattening it to an unqualified skill.
These prompt changes reuse the existing schemas, batches, calls and medium default; actual token
or outcome changes remain unmeasured. Original-ad completeness is not proof of checklist accuracy.

**Superseded for scoring admission by the 2026-10-17 rule below.** Filtering retains uncertain
locations. Scoring surfaces unchecked reference-city facts and
bounds location/preferences points to 8 where the job's evidence is uncertain or estimated.
Keep the proposed points separately, refresh confidence before research/ranking and on final
or corrected cards, and restore them when the condition resolves or is disabled. Evidence
research uses the priority before this uncertainty deduction, with all other fit limits intact:
missing facts cannot push their own useful check below the existing research threshold. A real trip
cannot prove a missing destination fact; an attempted lookup cannot create an online-evidence
note. Excerpt warnings survive confidence updates. Historical snapshots are not rewritten.
Reference-city population remains distinct from workplace population: a small workplace town
may qualify through a large enough city within the stated journey limit.

### Location eligibility before scoring — 2026-10-17

The owner requires hard location conditions to pass before paid scoring. The gate consumes
each person's parsed conditions: population percentage, named/ranked reference cities, travel
limits and researched facts remain general inputs. It does not reject villages by their own
size or hard-code one person's percentage. A proved failing condition excludes the job before
scoring. An unknown or unread hard condition retains the job in the pool and a separate
**Location not verified — not scored** list; it sends no scoring or later fit-research request
for that job. Optional preferences and explicitly disabled conditions do not block admission.
Original-ad metadata can change a workplace; only changed journey origins are measured again
before admission. Resolving or disabling the condition lets retained candidates proceed.

This supersedes paying for a score with reduced location points while a hard condition is
unknown. Stored historical assessments and owner marks are preserved; the current-search
response reclassifies explicitly unchecked historical matches without provider requests or
database rewrites. This does not establish a missing city fact or journey, and does not claim
a measured invoice saving. Pending locations have separate counts from a scoring allowance.

### Specialist work and conflicting workplaces — 2026-10-17

An existing online ad check now reassesses role/skills against the same rubric as initial
scoring. The replacement needs sources and a short task quote from that job's own research
paragraph; missing/cross-job quotes leave the earlier part unchanged. Both higher and lower
supported points replace the summary judgement, while other blockers still apply. No separate
research or scoring call is added. A grounded mandatory central skill marked unclear cannot
support the core-match band; proposed points survive for later supported resolution. Degrees,
years, incidental tools and unsupported ad quotes do not trigger this restriction.

The existing quick pass may report an explicit workplace contradicting the feed even when
the feed names a known town. It must quote that workplace within the supplied title/opening;
unchanged towns, head offices and training/customer destinations are not requested. Known-place
text remains bounded to the same opening length. Contradictory distant ad/feed towns or
coordinates have no approved journey origin. They stay pending without scoring, routes or a
futile town lookup; the card identifies the conflict. Corrected original metadata can resolve
it. Multiple distant workplaces need disambiguation, rather than picking a convenient copy.
This does not prove that every workplace mention will be extracted correctly, or replace
missing original ads, city facts or journeys. Invoice savings have not been measured.

### Explicit saved-evidence recovery and original facts — 2026-10-17

An online attempt is not a complete evidence check. Retain `read_online` to prevent automatic
repetition within normal condition edits, and record whether the result was complete,
incomplete or not found. Explicit **Retry incomplete checks** reopens incomplete/legacy summary
checks and failed empty workplace lookups once. Complete evidence and existing assessments
survive; service/scoring allowances and persistent-failure stops still apply. The dialog counts
these ad/workplace checks. Ordinary comparisons run after current location/travel admission,
so an explicit retry cannot spend comparison requests on a failed or unresolved hard condition.
Focused comparisons also retain a previously grounded central-skill flag when a reply omits it;
an inconclusive retry cannot release the core-match restriction.
Both focused comparisons and online-ad updates use the same replacement policy: an unsupported
ad/profile quote cannot overwrite an earlier grounded clause. Retain the latest failed proposal
separately, show its verification failure, and keep the earlier uncertainty and score restriction.
Supported later evidence can still resolve the requirement and restore the proposed points;
failed replies neither establish a blocker nor accumulate retry history or extra requests.

`vacancy_evidence.py` and migration 18 retain independently verified original closure or a
conservative latest-possible publication bound for the exact saved vacancy. This is separate
from source dates, first-seen history, scores and owner marks. A loading/error page, unrelated
requisition or company statement cannot establish closure or original age. Reviewers/readers
must verify identity and supporting facts before recording them; this module makes no network
or provider requests. Confirmed alias families share evidence; distinct requisitions do not.
Old/closed evidence excludes the job before paid work and filters a copy of restored results.
Saved/Applied history survives; confirmed closed links are disabled there. **Excluded jobs and
links** shows the evidence, source and undo control. Undo removes only that evidence and starts
no search; all other search rules remain applicable. No owner reset was performed.

Application reports now recognize the same numeric Adzuna advertisement across its known
details/land route forms and changed `utm_*`, `se` or `v` tracking fields. The original advertiser
URL is preserved. Unknown query fields, other identifiers/hosts/ports and unrecognized paths
do not establish equivalence. No redirect is fetched. Reports remain reversible; independent
matched employer/board alternatives and Saved/Applied/history survive. This extends the exact
URL report policy above without guessing destinations for other jobs. Current public policy
evidence and limits are in [SOURCES](SOURCES.md#ai-and-maps).

Fictional electronics, nursing, teaching and hospitality regressions cover core/adjacent ranking,
lower limits, partial reference facts, per-job route evidence, later resolution, legacy recovery,
warning retention and reversible application identity. Frozen saved decisions may be replayed
privately as deterministic-rule diagnostics; they are not new independent model judgements,
precision measurements or market recall. Complete invoices, unavailable originals and an
eligible independent coverage benchmark remain separate dependencies.

Equal totals favor the stronger weakest rubric area (points divided by that area's maximum),
then newer posting evidence. This prevents a capped but clearly wrong seniority level from
winning a tie with a suitable adjacent role purely because it is newer. Backend and browser
use the same scoring maxima. Equal breakdowns and incomplete legacy breakdowns retain the
posting-date tie-break; **Newest** remains date-first. This supersedes date-only Best match ties.

## Search preparation reuse and connection clarity — 2026-10-14

`preparation.py` and migration 16 keep successful setup answers outside Git. Location reuse
stores only the structured interpretation of the text, including a successful legacy-format
fallback; each search rebuilds local rules and rechecks web-dependent facts and citations.
Search-word groups are keyed to the exact profile excerpt, requested languages and request
contract. Missing languages or either requested word kind cannot become a reusable group.
Completed groups survive another group's failure. Both kinds expire after 30 days without
extending their age on a hit, are schema-validated on read and are bounded to 20 entries each.
Provider/model/host, native reasoning controls, thinking/output policy, prompts, schemas and
reader versions participate in the identity; account limits remain enforced before new calls.
Legacy result snapshots do not prove that identity and are not imported as setup judgements.

**Exact-edit clarification (owner, 2026-10-14):** the earlier whitespace-normalized box
identity is superseded. Profile/location cache identity retains raw text before prompt trimming,
so a letter, space or line break triggers the affected reading. Word identity also includes
an exact digest of both documents and both boxes, alongside its derived profile/language
request: equal interpretations of edited inputs cannot accidentally reuse words. Location
edits do not invalidate the independent document reading. The profile key now includes the
actual provider/host/native reasoning contract too. Old keys lack this proof and re-prime once;
history and owner settings are preserved. Fictional electronics/nursing/teaching regressions
cover unchanged answers, edited inputs with identical model output, fresh collection/scoring
and safe reuse after the new version of the text has succeeded. This verifies cache behavior,
not provider interpretation accuracy or measured live savings.

The progress labels identify saved location understanding and saved search words. Fictional
unchanged electronics/nursing/teaching setups produce equal answers with four fresh setup
requests versus two when reused over two searches; subsequent unchanged setup needs none.
This is an offline request comparison, not a measured total bill, live coverage or quality
claim. A complete fictional search also recollects sources and accepts a new score on the
second run, proving that job collection and judgement were not cached. All countries remain
supported. Failure, fallback, partial-language, expiry, corruption, route-control and migration/
reset regressions protect recovery and historical data.

Transport failures now have a separate provider-neutral connection error and retry note;
HTTP service responses retain their service classification, and credit refusals remain
terminal. Complete successful answers, partial usage and unknown charges retain the existing
recovery/accounting rules. No timeout, retry count, effort, spending limit or provider choice
is changed. [Current primary recovery guidance](SOURCES.md#ai-and-maps) does not establish
which end of a particular connection failed. Detailed diagnosis stays private; no paid probe,
owner settings change, restart, Stop, reset or new search is performed by development.

## Bounded reference research and priced usage — 2026-10-15

Reference-city research now uses groups of at most eight, retaining every candidate, independent
city evidence/citations and all completed groups. The bound applies to request scope, not recall:
missing answers remain unknown. Progress identifies the group and each retry number. An
exhausted connection budget stops dispatching the remaining groups for that reference fact,
preserving earlier answers and explicitly retaining unchecked candidates. An
in-memory fingerprint prevents restarting the retry budget for an identical exhausted research
request within one client/search. Independent country/fact requests, normal generation and job
sources remain available; a new search starts fresh. A broad research outage hold was rejected
because a failed request does not establish that independent requests cannot recover.

Private SDK diagnostics record elapsed time, response-header/chunk/completion/usage receipt and
transport error class, without request text or identifiers. No timeout, retry count, chosen model
or medium effort is reduced. Fictional electronics/nursing/teaching tests verify complete
candidate retention, failure isolation, evidence identity and independent recovery. Offline
checks do not establish a live latency, billing or matching improvement, nor the remote cause.

An explicit reached monthly spending cap is a terminal account refusal, including when reported
as HTTP 403 or 429: do not retry it or misclassify it as missing hosted-search capability.
An otherwise ambiguous Gemini 403 mentions both key permissions and billing/spending status;
the status alone cannot identify which failed. Invalid keys keep their separate diagnosis.
Fictional refusal tests verify that later requests do not restart the refused account within
the same search. Its reason is surfaced once even when a discovery/ad check retains partial
results and catches the refusal. A fresh search/client can recheck after the owner restores service.

User-entered prices now include optional cached-input and per-thousand web-search rates.
Thinking remains part of output, counted once. Missing applicable rates/usage keep estimates
incomplete; mixed currencies have no combined money total. A configured estimated spending
limit requires applicable model/search tariffs in one currency before dispatch. Gemini counts
unique nonempty grounding queries per request (older Gemini 2.x uses grounded prompts);
cumulative duplicate metadata is not another charge. Estimates precede allowances/tax/other
fees and cannot cap unreported charges or already running requests.
[Current service evidence](SOURCES.md#priced-grounding-and-spend-controls--2026-10-15).

Requirement quote validation now accepts comma-joined complete scalar values from the structured
profile and ignores leading Unicode list bullets in ad formatting. A supplied skill/degree list
must not become unsupported solely because Python/JSON punctuation separates its values. The
fallback accepts only complete stated values, preserving missing facts, changed negation and
numeric comparison signs as unknown. Scoring and online requirement extraction share the same
validator. Existing verdicts/scores are not rewritten, and the check still validates quotes,
not the AI's interpretation or complete fit. Fictional nursing, teaching and electronics cases
cover positive evidence and false-confirmation failures; no paid rescore was performed.

## Original evidence and repeated requests — 2026-10-12

The saved-review procedure remains independent judgement before score reveal, including every
top card and a balanced sample. Missing originals, unverified conditions and an incomplete
independent benchmark limit live claims; details and real-result aggregates stay private.
New owner messages extend the active task; finish or checkpoint its dependency before moving on.

| Candidate, in benefit order | Evidence, effort and risk | Decision / verification |
|---|---|---|
| Original Greenhouse text at collection | High evidence benefit; small change, larger list payload. The public API already offers full content. Missing dates must still reach the detail reader. | Implement `content=true`; preserve originals through matching, with date fallback and current list text ahead of cached text. Fictional hardware/nursing/teaching cases verify request reduction on a cold board and unchanged original-date rules. |
| Research grounding and explanations | A bold job heading could erase per-job evidence; completed-research information was drawn with an uncertainty marker. Small change; accepting another job's evidence is the main risk. | Accept ordinary Markdown headings, reject duplicate/missing IDs, preserve quote grounding. Informational notes have no question mark; missing requirements retain it, including legacy cards. No score rubric or certainty is relaxed. |
| Identical Maps elements within a search | Overlapping matrices repeat successful elements; whole-response caching can trap failed cells. Moderate change; identity mistakes can reuse the wrong journey. | Cache only validated elements for the same origin, destination, mode and departure. Retry unknown cells; preserve known cells alongside service/budget failures. Fictional overlapping queries use three elements instead of five. New dates/modes/origins/search instances require new evidence. No cross-search Google duration reuse. |
| Verified employer references | Official public career feeds offer original electronics/hardware evidence and backup coverage. Small change; dates and relevance remain separate. | Add independently verified ARX Robotics and STARK Greenhouse references. Preserve discovered employers and country retry provenance. Directory membership is not proof of whole-market recall or an in-window miss. |
| Cheaper main model | Large possible bill reduction, but no paired fit/research outcomes yet; a cheap output rate cannot establish equal quality. | Keep current medium configuration. Direct MiMo Pro remains the selected challenger; native enabled thinking is explicitly different from a literal medium control. Retain fresh cited research until its replacement passes separately. See the dated [market update](SOURCES.md#api-market-and-reuse-update--2026-10-12). |

Bulk full-content collection was previously a research lead (2026-10-09), now superseded for
Greenhouse by its current documented public API and offline evidence-preservation regressions.
The larger response is a bandwidth tradeoff, not a measured live latency or AI-bill saving.
List text also participates in existing word matching, so some titles may enter normal
matching through their description rather than the extra-title screen. This can improve evidence
and recall, but does not prove fewer AI requests or a lower bill; measure the complete pipeline.
On a fictional cold board with ten relevant ads supplying full text, publication and deadlines,
list plus ten detail requests becomes one list request. Missing temporal metadata still gets
the necessary detail check;
valid bounded-age metadata attempts are reused without replacing current original text.
Other adapters keep their existing contracts. No source is removed on low counts or outages.
The existing search reset deletes reusable profile/employer/ad evidence and AI journey memory;
its confirmation now explains that the next search may repeat paid AI work. Reset behavior and
preserved data are unchanged; no owner reset is performed as part of development.
When another matched board supplies a recent date, it must not suppress a missing original
employer date check. A fictional complete-ad/future-deadline case recovers an older original
and excludes the stale requisition rather than accepting the secondary board's recent date.

Cross-search route-duration storage remains held by the current Google contract. The earlier
Tuesday 08:00 timing is superseded by Wednesday 10:30 local, chosen by the owner on 2026-10-12;
car journeys use traffic-unaware routing. Each search keeps one departure reference across
midnight. This single representative time is not a measured daily average or a fee discount.
Matching only a city name would also lose origin/district, mode and departure identity.
AI estimates retain their
existing labelled 30-day memory, keyed to the current timing so old morning estimates are not
reused. Saved condition readings likewise retain timing identity; historical snapshots stay
unchanged. Google values do not enter AI memory. A different routing service
requires verified retention rights, transit coverage, freshness, quality and complete cost.

The existing custom Chat adapter already supports enabled thinking, strict-schema negotiation,
completed-answer checks, failed usage and separate research routing. Fictional adapter checks
establish this contract, not live MiMo quality or hosted-search integration. The prepared paired
packet and demand sensitivity stay private; the next paid action needs a separately bounded
comparison budget and an account key entered only in Jobcu. Any observed recall, scoring,
grounding or research regression blocks adoption; an unknown outcome cannot pass.

### Local reset and optional review — 2026-10-09

- Keep everyday navigation to Search and Settings. **Settings → Review results** replaces the
  main Score check tab; old `#/score-check` links still open the review. Independent ratings
  remain useful evidence, not automatic model training. Assistant development reviews remain
  proactive within standing authority and never require the owner to complete the sample.
- Offer confirmed Search, Review and full data resets. Search clears query/note, results,
  job memory/marks/excluded links and search caches, keeping documents and review samples.
  Review clears only samples/ratings/notes. Full reset clears both plus all other private-folder
  files, including uploaded copies, logs and assistant review evidence/checkpoints.
- Keep saved settings/filter choices, keys, assistant authorization and real usage/request
  counters. Detach deleted searches from AI usage so reused search IDs cannot inherit spending.
  Usage counters cannot be reset through these controls; that would restore spent allowances.
- `reset.py` owns scopes, deletion and the API mutation gate. Reset refuses active searches,
  corrections and competing uploads/provider checks; starts and corrections share the manager
  lock. Successful database deletion forgets the in-memory run even if later file deletion or
  compaction is incomplete. A failed reset reports partial deletion and can be retried.
- Database deletion first restores DELETE journal mode, then uses secure_delete and compaction
  so earlier text is not retained in a persistent journal/WAL. Full reset closes/recreates the
  owned log handler for Windows. Symlink targets/external originals are not traversed. This is
  local deletion, not secure erasure of SSDs, snapshots or separate backups. The page reloads
  after success and broadcasts a transient reload signal to other Jobcu tabs, without storing
  private content in the browser. No owner reset is performed during development.

### Project organization — 2026-10-08

- Keep current decisions and implementation/tool knowledge in this engineering reference.
  Keep the private review procedure with developer instructions in CONTRIBUTING. This
  supersedes separate DECISIONS, ARCHITECTURE and REVIEW files: the owner wants fewer places
  to look, without losing the setup, usage, contribution or evaluation detail.
- Keep one complete prompt per task in PROMPTS. The short loader introduced on 2026-10-08
  saved copying but added a choice and indirection; the owner prefers a single pasteable block.
- **Session scope, updated 2026-10-09:** Start/resume prepares a fresh chat, finishes only an
  already authorized recorded goal and then waits. Review uses the latest completed search;
  Deep improvement needs no new search and may use older authorized evidence. Both own
  substantive investigation and implementation. End safely finishes or parks the current step
  and saves a concise handover. This supersedes automatic backlog selection in Start and full
  startup in every work prompt. The procedure lives in [AGENTS](../AGENTS.md#sessions).
  Reuse valid recorded checks when their inputs are unchanged, retain exact-head CI, and avoid
  an extra handover commit just to chase its own hash. No running owner app is required for
  development; preserve its chosen state. These workflow changes add no private/paid authority.
- PROGRESS holds current state, one active goal, pending checks and next actions. Completed
  details belong in Git/PRs; dated source permissions belong in SOURCES. Standing rules stay
  in AGENTS. Link to the relevant section rather than repeat the same procedure.
- Preserve detailed human guides, licensing and historical records in the archive. Keep the
  established runtime/test/tool layout; consolidate only where responsibilities actually overlap.
  Retire merged branches after checking PRs/worktrees; preserve unmerged or active work.

## Employer discovery recovery and service choices — 2026-10-10

Dated external facts live in
[SOURCES](SOURCES.md#employer-feeds-and-remote-candidates--2026-10-10).

| Ranked goal | Benefit and evidence | Effort / risk / verification |
|---|---|---|
| 1. Recover incomplete employer discovery | Confirmed code turns AI failures into empty successes and suppresses country discovery for two weeks. Fix a known path to missed employers before adding feeds. | Small / low; fictional per-country recovery, fatal errors, parallel results, migration, all countries and nursing/teaching/hardware. Selected. |
| 2. Assess Jobicy remote feed | Explicit app/AI integration permission; a distinct remote-work route with a three-hour delay. | Medium / moderate; current host rules, original dates/full ads, eligibility and unique useful jobs versus existing methods. Hardware/on-site benefit unknown. No adapter yet. |
| 3. Compare direct AI challengers | Several direct APIs have lower token prices and some documented hosted search. Potential savings without a fixed subscription. | Medium / moderate; bounded paid authority/key through Jobcu, exact native reasoning and tool accounting, blind fit outcomes and fresh cited evidence. No quality-equivalent winner measured. |
| 4. Broader portal discovery and bulk full ads | Portals may add unique jobs; existing employer feeds offer original evidence. | Permission/partner access for held portals; unique relevant coverage and payload/request comparison before expansion/removal. Reachability or a temporary zero is insufficient. |

`employers.find` now keeps country outcomes independently. Provider failures, refusals,
truncation, invalid or blank answers remain due. A completed answer needs supplied source
evidence and either employer lines for the requested country or explicit `NONE`; useful named
employers are still verified/kept when research completeness is unknown. This does not prove
exhaustive employer discovery. The prompt requests the explicit empty form instead of silence.
Unknown tool accounting is not converted into a measured cost or a quality claim.

`in_parallel` cancels pending work on fatal account/model/feature/allowance errors. The finder
also stops queued requests before they call AI, waits for running work and persists all available
country outcomes in the caller thread, even beside a fatal error. Successful countries retain
the fourteen-day reuse interval; existing employers remain available to normal source readers.
Search details expose incomplete countries and explain retry on the next normal search.

Migration **14** adds completion provenance to discovery timestamps. Old timestamps were
written after both genuine results and failures, so they cannot reliably prove completion.
They remain stored but trigger one recheck on normal use. Employers, jobs, ratings, marks,
settings and original snapshots are preserved. No migration was applied to owner data during
development. Existing ten-lookups-per-due-country allowance, monthly controls, source rules
and medium AI defaults remain; repairing missing discovery can require necessary additional
work, so this is not advertised as a cost or speed reduction.

Fictional before/after comparison with two countries: both versions make two initial requests
and retain one checked employer. Previously the following search makes zero discovery calls
after the other country fails; now it makes one call for that country and does not repeat the
successful country. Tests also cover simultaneous completed work beside account failure,
empty/uncited/malformed answers, another country's names and preserved legacy state.
No live recall, new-job count, speed or accuracy improvement is measured.

**Superseded candidate ordering:** the earlier Luna → GLM Flash → MiMo Pro → DeepSeek Flash →
MiniMax order ranked inexpensive experiments, not intelligence. It overemphasized price and
covered too little of the public market. The owner reaffirmed that no quality/coverage loss is
acceptable; the [broader decision below](#quality-first-api-and-electronics-coverage-decision--2026-10-10)
replaces that order and earlier Go-first trial recommendations. Dated capability/cost facts
remain evidence, not comparative matching outcomes.

## AI billing refusals, Stop and incomplete usage — 2026-10-12

An authorized saved-data review selected failure recovery as the strongest reproducible
cost improvement. Detailed judgements, billing evidence, source contributions and run
measurements remain private; no paid test, new search or vacancy request was made.

The shortlist compared request recovery/accounting, same-model discounted processing,
permitted originals and a replacement API. Preserve the configured provider and medium:
prices and generic benchmarks cannot establish matching equivalence. The existing
[market assessment](SOURCES.md#public-api-market-and-quality-evidence--2026-10-10) remains a
dated comparison, including stronger models; no subscription is adopted from model count.
[Updated service evidence](SOURCES.md#billing-refusals-and-processing-evidence--2026-10-12)
keeps MiMo as a capability candidate but identifies a concrete third-party-use/rights
dependency. This supersedes treating its previously unread terms as the only access gap.
Go's shared windows alone are not a rejection, but use permission, current hosted-tool
fees and an independent fit comparison remain adoption gates. Private half/equal/double
daily, weekly and monthly scenarios include fixed fees, thinking, tools and missing charges.

Every AI dispatch, including repair/truncation retries, now checks Stop and recorded monthly
limits. Retry sleeps check Stop at most one second apart; queued request-slot waits check
within 250 ms. Definite depleted-credit refusals are remembered for the provider/model in
that search, so a step that catches an account error cannot dispatch it again. Existing
transient retries, parallelism and necessary evidence checks are preserved. A request
already sent can finish first and incur a charge; Stop is not a provider-side refund.
Quick connection probes do not repeat outage requests. The current step shows retry waits,
while the permanent note describes retries in the past tense after completion.

Gemini HTTP 402 or explicit depleted-credit responses are terminal billing refusals,
not temporary throttling. SDK attempts are explicitly one; Jobcu controls the retries.
The locked SDK previously made one attempt when retry options were absent, so this is
not a claim that hidden SDK retries caused an observed bill.

Only a received successful `STOP` finish permits reuse after a later HTTP transport failure.
Schema validation still follows; truncation, refusal and pre-completion disconnects cannot
become judgements. Normal streams still collect late citations and cumulative usage. Known
usage/search queries from a failed frame are retained before retrying; the failed answer and
its citations cannot support a judgement. Generation that ends without complete usage is
marked `unreported_requests`, including zero-known-token failures, rather than a free receipt.
Migration 15 preserves old records and adds this marker; old missing charges are unrecoverable.
The local cost estimate becomes incomplete and the UI/report exposes missing request usage.
Fees, discounts, taxes, currency, parallel in-flight work and provider reporting delays still
prevent the local monthly limit from being a guaranteed bill cap.

Controlled fictional regressions first reproduced the old behavior:

| Failure | Before | After |
|---|---|---|
| Depleted-credit HTTP 402 | Temporary throttling/retry path | Terminal billing refusal; later dispatch blocked |
| Stop during an AI retry | Whole wait and another request could run | Wait cancelled within a one-second check; one request sent |
| Successful terminal answer followed by a disconnect | Second request replaces the completed answer | One request; completed evidence retained, usage uncertainty marked |
| Failed/truncated generation with known usage | Available receipt discarded | Known tokens/thinking/queries counted once before limits/retry |
| Failure with no usage receipt | Could look like zero spending | Missing usage shown even with zero known tokens |

The transport comparison covers fictional electronics, nursing and teaching and preserves
medium. Search-manager Stop, concurrent slots, shared research allowance, migration, monthly
guards and existing all-country matching regressions verify the app contract. These are
offline behavior/request comparisons, not measured live savings, provider latency or fit/
coverage improvements. Missing originals, researched conditions and a date-verified independent
benchmark remain evidence gaps; do not tune scores or remove sources on counts or temporary
failures. Clearing search data removes reusable caches/history and does not repair billing.

## Quality-first API and electronics coverage decision — 2026-10-10

The owner asks for a practical best judgement across public APIs, without buying/testing every
model. [Current service evidence](SOURCES.md#public-api-market-and-quality-evidence--2026-10-10)
separates general benchmarks, native controls, hosted retrieval and Jobcu integration.

**Decision:** keep the working Gemini 3.8 Flash at medium for normal searches now. This is a
deployment-confidence decision, not a claim that Gemini is universally more intelligent.
Choose **direct MiMo-V2.6-Pro as the first replacement hypothesis**: credible general reasoning/
long-context results, documented structured answers and cited hosted search, and materially
lower published output prices. Its weaker factual-reliability/document results in the same
benchmark are real counterevidence. Do not switch from a composite score or price alone.
Jobcu's custom Chat adapter can request thinking but cannot yet use MiMo's hosted research;
its exact search/citation/usage contract needs implementation and offline failure tests before
one bounded comparison. No provider setting, account, key, allowance or AI effort was changed.

The five replacement candidates worth focused consideration are MiMo Pro, Claude Sonnet 5.5,
Qwen3.8-Max-0902, Grok 4.7 and GPT-6.1 Sol. After MiMo, this is a set of alternatives, not a
measured quality ranking or a request to purchase five accounts. Sonnet provides a
professional-reasoning reference; Qwen broadens multilingual/document comparison; Grok offers native
research/medium; Sol provides another professional-reasoning reference. Their bills and fit
outcomes may disqualify adoption, but higher prices do not establish lower quality. Haiku,
Luna, GLM, DeepSeek, Kimi, MiniMax, Mistral and Nova remain in the wider survey. Kimi's current
official warning against production web search makes it a weaker simple one-provider choice.
Go remains an alternative host, subject to its own intended-use/tools/shared-window evidence.

Use CONTRIBUTING's [provider comparison procedure](../CONTRIBUTING.md#compare-a-provider-without-lowering-quality).
Any observed requirement, exclusion, uncertainty, citation or coverage regression blocks
adoption; an average score gain cannot pay for a missed suitable job. A finite sample cannot
prove universal equality. Missing comparative evidence means preserve the working baseline,
not assert equivalence or ask the owner to choose models. The EUR30 ceiling is not paid-test
authority or a forecast; a necessary bounded trial is proposed only after the integration and
review packet are concrete. Prefer one complete provider and avoid unnecessary subscriptions.

| Ranked opportunity | Expected benefit / evidence | Effort, risk and verification |
|---|---|---|
| 1. Original employer coverage in electronics | Sector references identify specialist employers beyond familiar large brands; some major companies use currently unread systems. Better originals can improve both discovery and judgements. | Medium; check each host/terms, actual readable board and country, unique date-verified jobs/evidence and backup overlap. No speculative directory entries. |
| 2. One strong API challenger | MiMo's native research contract and independent general results justify a focused hypothesis, not guaranteed savings/equality. | Medium; offline contract/recovery work, separately authorized paired evaluation and complete bill; preserve fresh research. |
| 3. Specialist engineering boards / Avature | Potentially useful sector/country coverage; existing Siemens RSS research is a lead. | Medium/high; current permissions, layout, original dates/places, ordering/paging and unique contribution. Existing aggregator backup does not prove completeness. |
| 4. Remote-only feeds | Explicit feed permission can add backup value, but benefit to priority on-site sectors is unmeasured. | Lower priority under latest owner decision; freshness, eligibility and original evidence still required. Do not remove existing remote coverage. |

The selected coherent step is to correct decisions, comparison gates and reusable guidance.
It does not add a reader or claim new live coverage. [Sector evidence and access dependencies](SOURCES.md#electronics-employer-and-specialist-coverage--2026-10-10)
replace the earlier remote-feed-first expansion idea. The directory already includes PULS,
Infineon, Murata, Rohde & Schwarz, Analog Devices, NXP, onsemi and Texas Instruments; public
reference names are leads for missing employers, not proof of active relevant jobs. Unlisted
Siemens/Bosch/ABB/Keysight illustrate reader/access gaps, not proven whole-search misses.
Check permitted employer originals before introducing broad-board duplication. Retain useful
existing methods until unique jobs, original evidence and backup contribution are assessed.

## Structured employer workplace evidence — 2026-10-10

Prepared-session Deep improvement reused completed private reviews and read-only saved usage;
no new search or provider call. Source/service evidence is in
[SOURCES](SOURCES.md#broad-boards-and-web-discovery--2026-10-10); personal findings remain private.

| Priority | Benefit and evidence | Effort / risk / verification dependency |
|---|---|---|
| 1. Recover structured employer workplaces | Confirmed Ashby schema mismatch: locality was discarded and secondary country expected the wrong nesting. Known source facts can prevent false country/place exclusions and unnecessary research. | Small / low; offline parser → collection → workplace/check-selection cases across countries and professions. Selected and implemented. |
| 2. Expand permitted original-ad discovery | High potential coverage/accuracy value across broad boards and professions; snippets and current counts cannot measure it. | Medium to large / medium; reliable vacancy IDs, original dates, permissions and an independent benchmark. No new method on unverified value. |
| 3. Compare lower-cost model APIs | Potential large savings at native medium; current integration or price is not a quality verdict. | Medium / high; independently labelled cases, bounded paid-test authority, full tool bills and Go's intended-use clarification. No provider switch. |
| 4. Discounted processing of the same model | Flex/Batch have verified token discounts without selecting a different model. | Large integration/recovery work / medium; longer variable waits, missing capacity, durable recovery and tool accounting. Retain normal interactive processing. |

The Ashby parser now retains the free-text name plus stated locality and country from
primary postal and documented direct secondary addresses. Legacy nested secondary addresses
still work; malformed optional data cannot erase usable text. It keeps location alternatives,
original IDs, full descriptions and publication metadata. Ashby cache reader version 2 prevents
old parsed workplace metadata from replacing corrected source fields; corrected warm caches
remain usable. Structured regions are not appended as town evidence: a county/province can
share a city name or override the actual locality in free-text lookup. Original location names
stay intact; missing towns remain unknown. No employer, endpoint, request budget or
matching/scoring policy was added or removed. The general unresolved-place matching helper remains a separate lead;
this correction only recovers available Ashby evidence.

Fictional before/after: the original parser failed 69 of 72 new cases. After correction, these
and an additional mocked source-search regression pass. Primary and secondary workplaces reach
country/city selection in all 30 supported countries. Nursing, teaching and hardware cases
keep mandatory requirement text and avoid location-only research when a known town is stated.
The mocked global employer lists a USA primary/Irish secondary vacancy: previously no Irish
job survived; now it does, with full evidence, the same one list request, and no pending
location/summary research. Unlisted ads remain excluded. Cache-recovery regressions preserve
corrected location fields and reuse new full evidence. Region-only data stays unknown even
when the region shares a city name; a region cannot override a stated locality. These measure
fictional correctness/request selection, not live recall or money saved.
Previously saved snapshots/scores are preserved; future scoring remains fresh at medium.

Cost decision: avoid redundant evidence work and transport failures first. Do not shorten ads,
lower effort, reuse scores, discard uncertainty or narrow sources to meet a price target.
Explicit input caching alone cannot reduce output/thinking charges. Equal-token provider
comparisons are sensitivity scenarios; models may use different reasoning/token amounts.
No app price table, provider, service allowance, quota, account or billing setting changed.

An independently fictional daily workload of 100,000 input and 50,000 total output tokens,
with no cache discounts, illustrates the [dated prices](SOURCES.md#processing-tiers-and-complete-cost-comparisons--2026-10-10):

| Route | 30-day arithmetic, USD | Evidence limits |
|---|---:|---|
| Gemini 3.8 Flash Standard | 7.88 tokens | Search fees depend on queries and remaining shared allowance; Maps/tax/FX excluded. |
| Gemini same-model Flex | 3.94 tokens | Best-effort latency/capacity; not current Jobcu support or measured reliability. |
| Direct GPT-6 Luna Standard | 1.05 tokens + 6.00 search calls + 0.48 retrieved content = 7.53 | Assumes 20 calls/day, 8,000 retrieved input tokens/call; not converted from Gemini queries or a quality/capacity result. |
| Go | 10.00 fixed subscription, plus any uncovered tools/overage | Hosted charges/intended use remain unverified. Same-volume Luna consumes 7% of monthly weighted allowance; MiMo Pro 17.4%, before any separately metered tools. |

The numbers deliberately describe no owner search. More tool calls, longer reasoning or shared
usage can reverse the comparison. Private saved-demand scenarios cover the complete Go price
table and half/equal/double demand in five-hour, weekly and monthly windows; shared limits alone
do not reject it. The next justified cost decision is a bounded labelled Gemini/Luna/MiMo
comparison after required call/account authority, not buying or switching on this table.
Go service permission/tool-fee clarification stays checkpointed. Coverage needs an independent
date-verified benchmark; temporary failures/zero contributions do not justify removing a source.

## Complete AI answers and online-check recovery — 2026-10-10

Decision: keep medium effort, request content, models, source coverage and configured limits.
Improve transport/recovery before buying capacity or removing evidence checks. Generic code
inspection and primary documentation support the following shortlist; private review findings
and real-result measurements remain outside Git.

| Priority | Expected benefit and evidence | Effort, risk and verification |
|---|---|---|
| 1. Receive long answers incrementally and require completion | Existing Gemini calls buffered the whole answer; documented streaming offers another transport for the same request. Incomplete research must not become a judgement. | Moderate; fragments, terminal errors, late grounding/usage and parallel cleanup need real-SDK offline regressions. Live reliability/latency remain unmeasured. |
| 2. Recover missing original and condition evidence | High potential accuracy benefit; a summary or unchecked place fact cannot establish eligibility. | Originals and independent labels/benchmark are dependencies; preserve unknowns and do not invent precision or recall. |
| 3. Reconsider concurrency after rate limits | A single 429 currently serializes the rest of the run; later recovery could reduce elapsed time. | Actual quota scope and safe request rate are unverified. Preserve existing backoff and conservative concurrency in this step. |
| 4. Change source coverage | Potential unique fresh jobs or richer evidence. | Needs independent contribution/date checks and current permissions; raw totals and temporary failures do not justify removal. |

Implemented: Gemini's documented `generate_content_stream` transports both schema-constrained
generation and web research. The adapter assembles all answer text, excludes thought text,
retains grounding sources/query multiplicity and merges cumulative usage counts without adding
them repeatedly. Usage arriving after the text remains included. Only a successful terminal
answer is usable; silent EOF, disconnection, refusal and token truncation cannot supply a partial
judgement. JSON retains its existing format validation and bounded retry behavior. Research
truncation now remains an incomplete check instead of passing clipped notes to extraction.

The shared SDK client remains alive. Public HTTPX response hooks track request-local responses
per thread so an interrupted/refused stream closes its own body without interrupting another
answer or abandoning the connection pool. No SDK private API is called. Connection-retry notes
explain that completed work is kept; the rate-limit note distinguishes provider throttling from
an exhausted monthly allowance. Failed online batches explicitly leave missing details unchecked.

Before/after comparison used a fictional offline gateway that disconnects an idle response at
60 seconds and permits six streamed chunks over 120 seconds. The previous adapter exhausted
five attempts plus backoff (375 logical seconds); the new adapter completed in one attempt
(120 logical seconds), preserving the identical request body and an unknown registration fact.
These are simulated transport measurements, not live speed, billing, matching or recall claims.
Real-SDK tests cover nursing, teaching and electronics, UTF-8, medium/schema payloads, late and
repeated metadata, refusals, server errors, truncated/valid-looking incomplete answers, fresh
recovery and parallel cleanup. Provider interruptions can still occur before or during streaming; its live
benefit needs evidence from a later ordinary search or a separately bounded authorized test.
The usage ledger contains reported completed answers; interrupted paid work can be missing.
Transport tests and ledger estimates cannot establish the provider's complete invoice.

## Go feasibility and interruption continuity — 2026-10-09

**Operational update, 2026-10-10:** preserve the existing one-model Gemini medium setup and
Maps for the owner's next on-demand 24-hour search. Do not buy or switch to Go solely for
Jobcu yet. This is a readiness decision, not a finding that Gemini matches jobs better.
The owner authorized generic questions; a dedicated Discord forum question and an independent
Reddit question are delivered. The earlier Zen question was replaced with a forum redirect;
there are two active questions, with no Discord reference in the Reddit post. Delivery proof
and reply status stay in the private checkpoint. No provider clarification was received at
the decision checkpoint; a community reply alone cannot establish service permission.

The next evaluation remains GPT-6 Luna at medium, comparing its direct API with Go's complete
service cost; MiMo Pro is the first challenger. Include hosted search charges and retrieved
content tokens, not only generation prices. A low token bill can favor direct usage; included
hosted tools could favor a subscription. Neither outcome is established by advertised model
counts or one workload forecast. The [dated technical lead and prices](SOURCES.md#opencode-go-and-ai-credit-eligibility)
support investigating hosted research rather than ruling it out. Adoption still needs service
confirmation, compatible cited research and a separately authorized bounded matching comparison.

Readiness was checked on a disposable private copy without network calls: saved configuration,
required inputs and database integrity, followed by an isolated fictional startup health check.
Owner state was preserved; scratch data was removed and the preview stopped. This checks local
readiness, not credit balance, provider availability, live Maps outcomes or matching accuracy.
The owner starts the search; review its saved evidence afterward under CONTRIBUTING.

Current decision: **keep Go as a viable evaluation candidate**, with GPT-6 Luna first and
MiMo Pro as the first interpretation challenger. Preserve the working one-model Gemini setup
while resolving Go's intended-use fit, hosted research/fees and independent matching quality.
This supersedes reading the earlier do-not-buy-now wording as a permanent exclusion. Shared
allowances and coding-oriented client guidance alone do not establish inadequate capacity or
model inability. Dated capability/tool evidence lives in [SOURCES](SOURCES.md#opencode-go-and-ai-credit-eligibility);
private workload calculations and continuity details stay outside Git.

| Question | Evidence / decision |
|---|---|
| Can the models understand documents and return structured matching answers? | Several upstream specifications explicitly support those capabilities and non-coding work. Gemini is not uniquely capable; actual matching quality still needs independent cases. |
| Does Go expose cited research through the chosen endpoint? | Native Responses passthrough and an original hosted-search report provide a positive lead. Check current tool behavior, citations and fees for the chosen model rather than claim all 32 lack research. |
| Does Jobcu currently enable that custom-host research? | Custom Responses/Messages deliberately set `can_search_the_web=False`; generation already supports the three formats. This is a fixable integration guard, not a permanent provider/model limitation. A separate native research provider works today. |
| Is this workload appropriate for the subscription? | Published guidance requests coding-agent traffic; obtain clarification for this personal non-coding workload. Use honest client/session identity and do not infer rights from a successful request. |

For a once-daily search, forecast token work including thinking once, with all work assumed in
one five-hour window, seven runs per week and 30 per month. Use current uncached rates and
context/peak tiers; add retries, variance and other model use. The
[fictional examples](#complete-catalogue-and-universal-api-decision--2026-10-09) demonstrate
plausible headroom for several candidates, while larger MiMo demand can exceed the monthly
allowance. Private saved usage was evaluated separately, not copied into the examples.
One saved search cannot establish future variance or an equivalent reasoning/token workload
on another model. Shared capacity is not inherently a blocker; decide from measured workload,
quality and necessary tools. A 24-hour posting window determines ad age, not token consumption.

Continuity verification after the reported short network loss: main matched GitHub at `07006ea`,
PR #97 was merged, and exact-main Mac/Windows/privacy CI `37985687468` passed. Git's full object
check found no missing/corrupt objects; ordinary unreachable blobs were retained. Authorized
read-only private database/checkpoint checks passed; disposable SQLite scratch was deleted.
No pending development write needed recovery, no owner data/settings/key changed, and no
provider call or search was made. A temporary network outage does not by itself prove either
corruption or uninterrupted provider work; report only the verified saved state.

Exact adoption dependency at the 2026-10-09 checkpoint: the prepared generic support question
asks whether Go permits personal non-coding document/JSON matching and whether the chosen Responses model includes
hosted cited web search, with its applicable charges/allowance. Sending it in the owner's name
needed explicit instructions under AGENTS; no support message had been sent then. The
2026-10-10 update above supersedes that delivery state. A subsequent bounded
fictional paired comparison through Jobcu must preserve medium effort and necessary evidence.
No new subscription, provider switch, research toggle or paid experiment is introduced here.

## Simple AI setup and buying decision — 2026-10-09

Current operational decision: **one Gemini 3.8 Flash model at medium plus Google Maps**.
Gemini supports structured output, medium thinking and native cited research; one AI key/model
can perform all Jobcu AI tasks. This is the simplest working setup, not a claim that Gemini
beats MiMo, DeepSeek, GLM or GPT on matching. The earlier replacement shortlist remains an
evaluation order, not a purchase instruction or an active paid comparison. Go remains a viable
candidate as clarified above; defer a Jobcu-only purchase/switch until its intended-use fit,
necessary tools and matching quality are established. The complete allowance, policy and credit
facts live in [SOURCES](SOURCES.md#opencode-go-and-ai-credit-eligibility). Model count supplies
choice, not an accuracy improvement or independent allowances.

The owner's EUR30/month total remains a ceiling, not a guaranteed bill. Preserve current
settings, credit, keys and limits; no top-up, subscription, provider switch, paid test or further
quota change is part of this decision. Maps uses separate Cloud billing and has per-SKU free
usage; buying more AI credit cannot fix a Routes quota. The existing targeted quota correction
is complete, and its live outcome can be reviewed after the next ordinary on-demand search.

Ranked improvement shortlist for the owner's simplicity/subscription follow-up:

| Goal | Benefit / evidence | Effort, risk and verification |
|---|---|---|
| 1. Make the one-model setup clear | Reproduced confusion from three prominent advanced sections; no extra model is required | Small change; hidden saved overrides must stay visible in the summary and persist; fictional browser save/reload and API regressions |
| 2. Settle shared capacity and intended use | Public billing code confirms weighted shared counters; public client guidance resolves the immediate buying recommendation | Free research; deployed limits and permission cannot be invented; primary code/documents, dated arithmetic and exact dependency |
| 3. Switch models immediately | Potential savings; no independently labelled Jobcu comparison | Quality/permission risk; requires separately bounded paid comparison, not a purchase based on model count |

**Implemented:** native setups show one optional **Advanced AI settings** section instead of
three separate advanced prompts. **Other API** names all three custom formats honestly and
opens **API format and advanced settings** because custom protocol selection is part of setup.
A live visible summary identifies interpretation/research overrides even while collapsed;
changing fields updates it and Save retains those choices. The interpretation override already
serves documents, location understanding, estimates and same-provider research; the label now
reflects that scope instead of suggesting only document reading needs careful AI. Both effort
defaults stay medium; no routing, matching or provider-call behavior changes. Separate research
remains useful for custom APIs without supported web tools, and is unnecessary for the normal
one-model Gemini setup. Never remove supported alternatives just to shorten the screen.

Before: three advanced entry points and no visible summary of closed overrides. After: one
entry point, native setup closed by default, custom format open, and actual selected routing
explained outside it. Fictional browser checks passed: collapsed legacy/separate-provider choices survived Save and
reload; clearing overrides restored one model; custom Messages plus separate research survived
reload with format controls expanded; medium defaults persisted; console warnings/errors were
absent. Preview request logs contained local reads and Settings writes, no provider probes or
search. The 1,125-test full suite and affected API/format/document checks passed.
No live ranking, capacity, cost or latency improvement is claimed from this interface change.

## Complete catalogue and universal API decision — 2026-10-09

Technical implementation and comparison record after the owner's full-catalogue/API/reuse
request. The simple setup decision above now governs operational buying guidance; the candidate
order below remains an evaluation priority. The catalogue facts and
terms have one home in [SOURCES](SOURCES.md#opencode-go-and-ai-credit-eligibility). The landing
page's 31 and documentation's 32 disagree; assess all 32 documented models rather than omit
one or count alternate pricing rows as models. This supersedes the older five-model order
below; it does not turn an evaluation priority into measured superiority over Gemini.

Ranked improvement shortlist:

| Goal | Expected benefit / evidence | Effort / risk / verification |
|---|---|---|
| 1. Universal custom formats plus independent online research | Removes a reproduced integration barrier while preserving current evidence collection; native protocol specifications and code establish the gap | Moderate effort; wrong host/key, reasoning and lost research are material risks; real SDK serialization, mixed-provider caps/usage and failure tests |
| 2. Reuse route judgements across days | Potential saving, not a measured gain; identical requests already share responses within a search | Storage rights and stale schedules make indefinite location-only duration reuse unjustified; verify contract and route identity before any persistent cache |
| 3. Replace the working model immediately | Potential price/quality improvement | No independently labelled comparison or Go non-coding permission; shipping an unmeasured switch would not satisfy the quality requirement |

**Implemented goal 1:** Other accepts Chat Completions, Responses and Messages. Each uses the
owner's custom address/key; native provider keys stay on native adapters. Messages accepts an
unversioned or `/v1` base without duplicating `/v1`. Custom Responses/Messages preserve native
medium/schema requests; Chat supports explicit effort, enabled thinking, or a disclosed
provider default. An explicit high/max mapping for logical medium is available for hosts
without medium; never silently map to low/off or call it measured equivalent effort. Legacy
custom configurations preserve their previously unsent effort and disclose the uncertainty.
Custom reasoning rejections stop; only explicit Chat format refusals negotiate schema/JSON/
prompt format, retaining the selected thinking control and validating the answer afterwards.
Fictional before/after SDK-transport comparison at base `92df256` reproduced an unrelated
custom 400 causing **six attempts before, one after**. Both report `AIBadRequest`; the new
request retains medium rather than retry without it. This is measured request behavior, not
a live latency/cost or accuracy claim. Mocked Responses/Messages serialization also confirms
correct paths, key headers, schemas and usage; the three formats were previously unavailable
at custom addresses except Chat without explicit effort.

An optional native **online research provider/model** routes only `research` calls. Main
generation still performs document reading, criteria, screening, scoring and structured
extraction after research. Both share the logical client's parallel gate, monthly ledger and
per-search web allowance; usage is attributed to the actual provider/model. Refused research
stays unknown and stops repeated research for this search without switching providers; main
generation remains available. Separate connection probes check generation, not web access,
and do not change saved configuration or make hidden calls when saving/loading settings.
Custom proxies do not automatically inherit upstream web-tool entitlement. Custom clients
identify themselves as Jobcu; Go-address requests include an opaque per-client/search session
header. Technical compatibility does not resolve Go's permitted-use dependency.

Five candidates to evaluate, in order:

| Candidate | Why it earns a comparison place | Adoption gate |
|---|---|---|
| 1. GPT-6 Luna | Best first operational candidate: documented medium/schema and inexpensive direct main-token work | Independently labelled requirements, unknowns, quotes and rankings against Gemini; host/tool behavior |
| 2. MiMo-V2.6-Pro | First quality challenger alongside GPT: flagship reasoning and economical output | Explicit enabled thinking is not a literal medium scale; labelled comparison, proxy behavior and allowance reserve |
| 3. DeepSeek V4.1 Flash | Strong value challenger with substantial Go capacity and native reasoning | Host-specific high/max mapping, allowed processing region, renewed privacy terms and independent multilingual fit |
| 4. Claude Haiku 5.5 | Alternative family with documented medium/schema, useful for detecting shared mistakes | Compare complex/borderline fit, retained-data policy, long-prompt pricing and custom Messages behavior |
| 5. GLM-5.3-Flash | New primary evidence supports document work/JSON/reasoning; promising additional challenge beyond the older GLM shortlist | Vendor's intelligence claim is not Jobcu evidence; disclose native high/max and compare independently |

GPT remains the first replacement **candidate**, preferably direct API for Jobcu-only use
when its complete bill is below Go's fixed fee. Keep Gemini as the operational baseline and
available cited-research provider until quality is measured. No API purchase, private model
switch or fit-quality victory is implied. MiMo/DeepSeek/GLM are not shown to be worse.

Complete individual disposition, based on fit to this investigation, not intrinsic intelligence:

| Model | Decision / reason |
|---|---|
| GPT-6 Luna | First comparison; explicit controls and useful direct-price alternative |
| GPT-5.6 Luna | Reserve comparator; establish an advantage before choosing an older, dearer option |
| Claude Haiku 5.5 | Top five; independent model family and explicit controls |
| MiMo-V2.6-Pro | Top five; test flagship interpretation with enabled thinking |
| MiMo-V2.6-Flash | Next value comparison; cheapness alone cannot replace the Pro quality check |
| MiMo-V2.5-Pro | Reserve; compare if newer Pro regresses, rather than assume version superiority |
| MiMo-V2.5 | Reserve value comparator; no established matching advantage |
| DeepSeek V4.1 Flash | Top five, conditional on region/privacy and host controls |
| DeepSeek V4 Pro | Focused quality comparator if labelled failures justify its tighter capacity |
| DeepSeek V4 Flash | Reserve; newer Flash has more allowance, but quality still needs comparison |
| DeepSeek V4 Flash Vision Exp | Defer experimental vision; current pipeline supplies text, not images |
| GLM-5.3-Flash | Top five after current document/reasoning evidence; native mapping required |
| GLM-5.3 | Focused comparator; coding gains do not justify its tighter capacity for daily matching |
| GLM-5.2 | Reserve; useful capacity if it matches or beats newer variants on independent cases |
| Kimi K3 | Focused quality challenger; expensive output/tight capacity prevents an unsupported daily-main recommendation |
| Kimi K2.7 Code | Reserve; test whether code specialization helps this document workload |
| Kimi K2.6 | Strong next comparator; displaced from the first five by the new GLM Flash evidence, not proved inferior |
| MiniMax M3 | Next comparator; reported agent/context gains warrant testing, not an automatic switch |
| MiniMax M2.7 | Reserve; compare if M3 fails specific cases or availability |
| Qwen3.8 Max | Focused quality challenger; establish incremental accuracy before tighter-capacity daily use |
| Qwen3.8 Flash | Next value comparator; independently validate multilingual requirements |
| Qwen3.7 Plus | Reserve; can earn a place through stable independently measured fit |
| LongCat-2.0 | Reserve; validate evidence fidelity before interpreting cheap capacity as quality |
| LongCat 2.5 Preview Free | Fictional experiments only when permitted; temporary access is not a production fallback |
| Step 5 Preview Free | Same temporary-access caution; no silent downgrade when another allowance ends |
| Muse Spark 1.3 Contributor | Exclude automatic private-document adoption because training permission changes the privacy bargain |
| Muse Spark 1.2 Contributor | Same privacy gate; low price cannot decide consent |
| Hy4 preview | Defer primary use until stability and interpretation evidence justify preview risk |
| Hy3 | Reserve value comparator; matching evidence missing |
| Space Bunny | Defer until identity, controls and task evidence are sufficiently clear |
| Grok 4.7 | Focused challenger; high token cost/tight capacity needs measured incremental quality |
| Grok 4.6 | Reserve; no assumed superiority or need to test both before stronger candidates |

Fictional capacity planning extends the earlier smaller/larger scenarios (500K/100K and
1M/250K fresh input/output daily for 30 days, thinking included once, no cache/retries):

| Candidate | Smaller monthly equivalent share | Larger share |
|---|---:|---:|
| GPT-6 Luna | 20% | 45% |
| MiMo-V2.6-Pro | 60.9% | 130.5% |
| DeepSeek V4.1 Flash, off-peak / peak | 6.75% / 13.5% | 15% / 30% |
| Claude Haiku 5.5, prompts within 100K | 20% | 45% |
| GLM-5.3-Flash | 6.25% | 13.75% |

These calculations do not establish equal tokenization, reasoning, accuracy or billed demand.
Apply shared weighted consumption and five-hour/weekly windows, not 32 independent pools.
Do not create prompt padding, stale-score reuse, reduced evidence or lower effort to fit limits.
A bounded paid paired comparison and independent labels remain the exact quality dependency;
no new full search is needed. Use CONTRIBUTING's method and preserve owner/private records.

**Maps decision:** distinguish a day's headroom from the app's monthly allowance. A fictional
9,000 elements over 30 days averages **300/day**; 450/day permits 13,500, so it cannot enforce
that monthly total. A higher daily quota can accommodate a busy search while the separate
monthly app guard remains; it does not guarantee every day's search is fully Maps-checked.
One ad is not one element. Sampled destinations and every actual retry consume the guard.
Jobcu already coalesces identical coordinates within each condition and identical HTTP bodies
within the same search, before spending another attempt. That identity includes destination
coordinates, mode and transit departure, not just the workplace. New searches refresh routing;
changing destinations/mode/departure must not share a stale result. Independently sourced town
coordinates can be reused; an unrestricted stored Google duration cannot. No route-cap change,
duration cache, paid route call or measured billing/recall improvement is introduced here.

## Practical service choice — 2026-10-09

**Implementation/shortlist update:** the complete catalogue decision above supersedes the
older shortlist order and the future-only hybrid/custom-protocol statements in this section.
Its no-unmeasured-switch rule and spending authority remain current. The simple setup decision
above supersedes any suggestion that a paid comparison is already active or a subscription is
the current purchase recommendation.

The owner delegates technical service/model decisions and explicitly approves **EUR30/month
total** (superseding EUR25), with cheaper service preferred when quality is preserved. Keep the
working Gemini 3.8 Flash medium setup during evaluation; the chosen first replacement candidate
is **GPT-6 Luna at medium**. Compare its direct API first for Jobcu-only use, and Go after
non-coding use is clarified. This supersedes treating either the earlier Go shortlist or the
initial Gemini-first spending proposal as a proven best setup. No preferred app default or
provider/account/limit change is introduced; no candidate's matching superiority is established.

Go's models are **not shown to be worse**, and its low price can be good value. Its model caps
must be compared using tokens, including reasoning, rather than advertising's cached coding
request counts. Price/capacity, fit quality, permission and integration are separate questions.
Do not reject it because Jobcu currently lacks an adapter: that technical gap is fixable.
Do not buy it solely for Jobcu before the contractual and necessary-research gaps are resolved.
The five-model shortlist below remains the evaluation order; it is not an intelligence ranking.

Choose setup using total work, not subscription advertising: count output including thinking
once; distinguish original searches from corrections and non-search usage; include grounding,
shared allowances, route elements/retries, currency and tax. Gemini's current grounding
allowance is separate from Routes API usage; see [SOURCES](SOURCES.md#gemini-running-costs).
Private saved observations and forecasts belong only in the private review record, never in
these documents. Sparse history cannot establish a fixed daily bill or future workload.

The earlier EUR10 Maps / EUR15 AI allocation and larger proposed total are superseded as the
budget plan; the current ceiling is in AGENTS. No allocation or euro cap has been implemented.
Do not change configured limits or reduce medium effort, necessary evidence or coverage to fit
it. Diagnose Maps first and forecast combined costs against EUR30, including tax/currency and
other account use. Report insufficient headroom without silently raising the ceiling.

Ranked integration approaches:

| Approach | Benefit / effort / risk | Acceptance gates |
|---|---|---|
| 1. Direct GPT-6 Luna main + existing Gemini research | Low main-token price, explicit medium/schema support, no Go client-policy dependency; medium engineering effort | Add optional research-provider routing through `ai/client.py`, truthful usage/limits and failure handling; independently labelled comparison against Gemini |
| 2. Go GPT-6 Luna main + existing Gemini research | Predictable USD10 subscription with multi-model options; higher integration effort; permission dependency | Confirm non-coding app use, correct Responses/medium/schema and honest session/client identity; same quality comparison and shared allowance checks |
| 3. Go-only, including research | One subscription would simplify billing if complete; entitlement/cost and evidence-preservation unknown | Explicit hosted research/API rights and citations; preserve employer/place/requirement checks rather than replace live evidence with recollection |
| 4. Keep all work on Gemini | Already functioning medium/research pipeline, little integration effort; variable cost | Actual daily workload and account bill must fit the ceiling; operation does not prove best matching quality |

For the same chosen model, Go's fixed subscription is not automatically cheaper than its
direct API. Compare direct **main-token** expense with USD10 before adding research/Maps,
which both approaches still need. In the earlier fictional scenarios, direct GPT main-token
expense is USD3.00/6.75 per month. These are not real usage or a complete bill. Go becomes
financially useful if the permitted comparable workload and other useful model work justify
its subscription without exhausting the weighted/windows limits. A different model's larger
equivalent cap is useful only if its independently checked job understanding is good enough.

An optional **separate research provider** was proposed here and is now implemented as recorded
above. Retain Gemini's fresh cited research while evaluating a different
main model for extraction, criteria, screening and scoring; do not move every `job_places` or
`location` call merely by step name, as those steps also contain structured extraction.
Preserve one logical client's search web budget, monthly ledger, per-provider keys, cancellation,
medium defaults and correct usage attribution. Never silently switch providers or lower effort
on a refusal. Native direct GPT has a Responses adapter; the custom Responses path is now
implemented above. A coding agent wrapper is not a workaround for permitted-use rules.

Before a purchase/switch, a bounded Jobcu-only fictional comparison must assess explicit
requirements, multilingual title/criteria interpretation, evidence quotes, unknowns and ranking,
including engineering/non-engineering and all-country cases. Repeat borderline cases and
judge against independent labels; JSON validity and cheaper output alone are insufficient.
No paid comparison or migration occurred in that decision step; the later hybrid implementation
is recorded above.

For Maps, inspect saved error/quota evidence first. Older generic 429 warnings do not identify
which quota failed. The account dependency is the actual Routes project billing state,
**Compute Route Matrix** quota/usage and billed SKU/shared allowance. The owner can open the
relevant Cloud page using the [setup guide](guides/getting-your-keys.md#recommended-setup-now).
Do not reset data, repeat a whole search, raise a local counter or buy credit as a diagnostic.
Any live diagnostic still needs a bounded paid-test authorization through Jobcu. Keep the
estimate/sample negative-evidence safeguard as a separate development goal, not a completed fix.

### Additional model assessment — 2026-10-09

There is **no measured evidence that Gemini 3.8 Flash matches jobs better** than MiMo-V2.6-Pro,
DeepSeek V4.1 Flash or GLM-5.3. The initial shortlist favored documented effort, integration and
allowance headroom, not intrinsic intelligence. Its position must not be described as a model
quality verdict. [Dated native and Go facts](SOURCES.md#additional-reasoning-model-candidates)
support the following evaluation decision:

| Candidate | Product judgement | Gate before adoption |
|---|---|---|
| MiMo-V2.6-Pro | Put alongside GPT-6 Luna in the first quality comparison: flagship reasoning/structured-output capability and comparatively low output rate justify testing | Explicit enabled thinking/effort behavior on the chosen host; labelled multilingual requirements/unknowns/scoring comparison and research preservation |
| DeepSeek V4.1 Flash | Serious value candidate; Go's larger equivalent allowance warrants including it after the first pair | Region/privacy permission, host-specific reasoning controls, schema/quotes and multilingual fit measured on the same independent cases |
| GLM-5.3 | Include in a focused quality comparison; stronger coding post-training is neither evidence of better job matching nor a reason to call it poor | Control the native max default, validate allowance headroom; its Go equivalent is smaller than GLM-5.2 despite the same token rate |
| Gemini 3.8 Flash | Keep as the working baseline, with native research; familiarity is not evidence it wins | Independently labelled fit/exclusion quality remains necessary even without changing provider |

Jobcu's default remains **medium**. Vendors' effort labels are not a common computation or
accuracy scale. Absence of a literal medium is a solvable adapter/calibration question, not
automatic model rejection. A future mapping must explicitly preserve enabled reasoning,
disclose the actual native control and measure quality/cost; do not silently choose low/off,
pretend native max is medium, or claim equal effort merely because a request succeeded.
That assessment introduced no mapping, switch or quality claim. The later custom controls above
allow explicit enabled/native-effort requests; host calibration and model quality remain unverified.

## AI subscription decision — 2026-10-09

**Superseded as the current setup recommendation by the practical service choice above.**
The model shortlist and migration gates remain evaluation evidence, not a selected replacement.

The owner intends to replace Gemini 3.8 Flash with OpenCode Go for daily searches and considers
using Google credit for Maps. [Current service/model facts](SOURCES.md#opencode-go-and-ai-credit-eligibility)
establish two dependencies: Go's coding-client policy does not clearly permit Jobcu's non-coding
workload, and AI Studio prepaid credit cannot pay for Maps. Preserve the owner's running app,
keys and settings; no subscription, account or provider change was made in this investigation.

Recommendation: **GPT-6 Luna is the first main-model candidate to evaluate at medium effort**.
This is a suitability hypothesis, not a measured claim that it beats Gemini or the other models
on job fit. Consider its direct API before buying Go solely for Jobcu: the listed token rates
match, the native Responses adapter already exists, and general app use does not need Go's
coding-client clarification. Direct use needs its own owner-chosen key/account, actual limits
and a complete token/tool cost forecast. Keep the functioning provider until a bounded paired
comparison supports a switch. The owner can still choose Go after the dependencies are resolved.
No preferred model/provider is added to Jobcu defaults.

Ranked evaluation shortlist for the requested Go plan, based on documented capability and
integration/headroom, not a ranking of intrinsic intelligence:

| Rank / candidate | Why evaluate it | What remains unknown |
|---|---|---|
| 1. GPT-6 Luna | Explicit medium reasoning, strict output, long context and native Responses fit; strong calculated allowance margin | Jobcu extraction/fit accuracy versus Gemini; Go hosted-tool access, permitted use and proxy behavior |
| 2. Claude Haiku 5.5 | Explicit medium default and schema support; same favorable short-prompt allowance calculation | Complex matching quality and Go Messages/tool behavior; prompts over 100K change its rate |
| 3. MiMo-V2.6-Pro | Flagship thinking/structured-output capabilities and long context justify a quality comparison | Go effort mapping, schema behavior and quality; the larger fictional workload below exceeds its equivalent cap |
| 4. Kimi K2.6 | Own reasoning/knowledge evaluation and thinking support; larger equivalent allowance | No medium mapping established through Go; JSON reliability, matching and little reserve in the larger scenario |
| 5. GLM-5.2 | Thinking/JSON/long context, with a larger allowance than GLM-5.3 | Go effort mapping and general matching benefit; larger scenario exceeds its cap |

GLM-5.3's stronger coding results do not prove better matching than its shared-base predecessor;
its max default and absent medium option need explicit handling. Kimi K3/Qwen3.8 Max/Grok's
expensive token rates and smaller equivalents need workload proof before daily-main use.
DeepSeek is a further candidate after actual permitted processing regions and its dated ZDR
agreement are checked; published Go code has region gating. Muse Contributor's training bargain
needs an explicit privacy decision; do not choose it automatically for private documents.
Temporary unlimited previews are not a stable capacity/quality guarantee or automatic fallback.
None of these exclusions establishes that a model is inaccurate.

One search with a **24-hour posting window** is not one AI call or a fixed token load. Its fresh
ads, title screening, profile/criteria interpretation, matching, scoring, repairs, reasoning,
employer discovery and web research all consume work. The marketing estimates use long cached
coding conversations with short outputs; do not apply their advertised request counts to Jobcu.

Fictional single-model planning examples below use 30 searches, no cache discount, no retries,
and output totals including thinking. The smaller daily workload is 500K uncached input/100K
output; the larger is 1M/250K. Each individual GPT prompt is at most 272K and Haiku at most 100K.
These are arithmetic, not measured owner demand or an accuracy/performance benchmark:

| Candidate | Smaller 30-day usage value, USD / equivalent share | Larger value, USD / share |
|---|---:|---:|
| GPT-6 Luna | 3.00 / 20% | 6.75 / 45% |
| Claude Haiku 5.5 | 3.00 / 20% | 6.75 / 45% |
| MiMo-V2.6-Pro | 9.135 / 60.9% | 19.575 / 130.5% |
| Kimi K2.6 | 26.25 / 43.75% | 58.50 / 97.5% |
| GLM-5.2 | 34.20 / 57% | 75.00 / 125% |

The subscription fee is separate from these token-value equivalents; Go does not bill these
values on top merely for included usage. Mixed models share weighted capacity: half of one
model's equivalent plus half of another consumes the whole allowance, not two separate pools.
Check five-hour and weekly windows as well as the subscription month and other coding use.
Actual tokenization, cache writes, repairs, reasoning, thresholds, concurrency and changing
prices/caps can alter the forecast. Do not enable Zen **Use balance** or automatic top-ups to
hide a limit. Keep unknown cases and fresh scoring; do not lower effort or drop ads for savings.

Direct GPT's corresponding token-only examples are USD3.00/6.75 per 30 days rather than a fixed
Go fee. However, direct web search adds USD10/1,000 calls plus retrieved-content tokens: 500
calls add USD5; 2,000 add USD20 before those tokens. Thus direct use is an integration/cost
candidate, not a promised cheaper complete search. Inspect authorized saved token/tool usage
before forecasting the combined AI/Maps total; retain needed research, not an arbitrary cap.

Migration acceptance gates, refreshed after the implementation above:

1. For Go, confirm permission for on-demand personal job matching with document interpretation
   and JSON scoring. Identify the client honestly as Jobcu and use opaque stable session IDs;
   do not impersonate a validated coding agent or route private tasks through another client.
2. Custom formats, explicit controls and honest identity/session headers are now implemented
   with fictional SDK regressions. Live host/model behavior still needs verification. Native
   OpenAI/Anthropic keys go to native addresses; a Go key belongs only under Other.
3. Separate native online research is now implemented/tested. Go's own hosted-search
   entitlement/fees remain unverified. A main-model switch must preserve employer/place/
   requirement research; existing Gemini credit can cover its Gemini work, not Maps.
4. Before switching, run a separately authorized bounded fictional comparison through Jobcu:
   profile extraction, multilingual criteria, unrelated-title decisions, requirement quotes,
   permits/languages, unknowns and borderline scoring, including non-engineering/all-country
   cases. Compare against independent labels, current Gemini and repeated borderline outputs;
   record errors, schema repairs, reasoning/tool tokens and time. No fresh real search is needed.
   Real accuracy/coverage claims still require CONTRIBUTING's private procedure and originals.
5. Diagnose Maps independently from AI billing. Verify the actual quota, Maps SKU, credit grant
   eligibility and usage; preserve uncertain journeys. The earlier
   [Maps allocation proposal](#maps-spending-proposal--2026-10-09) remains pending. No credit
   transfer/refund or billing change is implied. Keep the current EUR30 total, taxes/currency and room
   for the existing workload; report insufficient budget without changing matching quality.

The useful free step completed here is the researched decision, numerical planning and corrected
setup guidance. No model API call, private review, key/account inspection, new search or live
quality measurement was performed. Go permission/tool support, actual account allowance and a
bounded comparison are exact dependencies; no migration implementation is currently active.

## Search pipeline

`search.py` runs a background thread; the page polls progress once a second.
Searches and condition corrections stay running until `jobstore.finish_search` commits the
final result snapshot and search status in one transaction. Only then does the manager publish
finished, stopped or failed. A save failure reports failed, keeps results visible in the current
app session and warns that the latest results may not survive closing Jobcu; the prior saved
snapshot remains intact if the transaction rolls back. Controlled-save tests cover polling,
overlapping starts/corrections, immediate restore and storage failures without timing guesses.

1. Read documents into a profile, interpret the query into a location plan, and generate
   multilingual search words, reusing successful unchanged setup within its bounds. Refresh
   discovered employers when due (two-week interval).
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
   title-only optional review sample. Search details separates this gate from duplicate removal.
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
4. Score evidence through `ai/client.py`; `requirements.py` grounds ordinary mandatory
   comparisons in the supplied ad/profile text and `scoring.py` applies deterministic limits.
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

`location.py` reuses exact-input readings for at most 30 days, then builds explicit conditions
with current data and fresh research. `places.py` supplies
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
One `TravelMeter` serves both measurement rounds of a decision, so confirmed daily/monthly/
zero quotas and key refusals do not trigger fresh attempts later in that same decision.
Temporary/unidentified failures can still recover in later rounds. Historical result messages
remain unchanged. [Maps recovery](#maps-recovery) defines request accounting and measured limits.
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

### Mandatory requirements — 2026-10-09

`requirements.py` owns ordinary eligibility comparisons, including enrolment, professional
registration/licences, qualifications and work permission. Each AI check supplies a short
requirement name, exact ad/profile quotes and a met/not-met/unclear verdict. Unsupported or
conflicting comparisons become unclear. Quote validation uses the actual scoring excerpt;
it cannot support a clause beyond the 12,000-character bound or establish semantic truth.
Requirements and applicant facts still need accurate model interpretation and original evidence.

Supported unmet requirements force the existing 0–10 hard-requirement band and named 55 limit.
Unknown, missing checks or incomplete text use the existing 11–14 band, without a definite
ordinary blocker. Complete checked evidence with no missing ordinary requirement uses 15.
Language, doctorate, citizenship/clearance and experience retain their separate policies.
The citizenship prompt explicitly rejects inference from clearance names, foreign nationality
or absent history alone; live extraction and vacancy-specific exclusions remain unverified.

Online research collects these additional requirement facts in the existing requests. The
structuring step receives the profile needed for comparisons. Quotes must appear in that job's
identified research paragraph; missing/ambiguous multi-job headings do not support a blocker.
Notes never become full-ad text. Omission or an unclear later comparison cannot erase an
earlier known ordinary blocker; explicit supported resolution can replace its comparison.
Keep the original proposed points so a resolved limit does not leave a sticky points penalty.
Legacy evidence retains its original behaviour and ordinary limits until fresh scoring;
historical snapshots are not rewritten. Medium effort, batch sizes and service limits remain.
Output room is increased for the additional structured evidence, with no extra AI step.

A no-network comparison using a fictional ward applicant, identical other rubric parts and
scripted evidence (not a live model accuracy measurement):

| Evidence | Before | After | Preserved limit |
|---|---|---|---|
| Explicit unmet registration, contradictory 14 points | 94, no ordinary limit | 55, named eligibility limit | Job remains available |
| Unsupported negative comparison, proposed 0 points | 55, definite generic limit | Unknown, 11 points, no definite ordinary limit | Missing evidence stays visible |
| Explicit met registration, contradictory 2 points | 55, generic limit | 95, 15 requirement points | Established rubric bands |

Regression coverage includes all 30 countries, fictional engineering/nursing/teaching/
hospitality facts, quotes, conflicts, clipping, missing answers, research boundaries, later
resolution and legacy preservation. One initial scripted request per job remains one;
no live ranking, recall, latency or cost gain is claimed. Primary evidence:
[SOURCES](SOURCES.md#requirement-evidence-and-independent-review).
Seven warmed 100-call rounds on this Mac measured median local `finish` time of
0.0073–0.0078 ms before and 0.0203–0.0214 ms after for those three cases. Grounding adds
local validation work; these short fictional texts do not represent whole-search latency.

## Project layout

The root keeps launchers, README, CONTRIBUTING, AGENTS, LICENSE and Python/tool configuration.
`src/`, `tests/` and `tools/` keep their established paths; no extra build step is required.

| Area | Modules and purpose |
|---|---|
| Startup/server | `launcher.py`, `__main__.py`, `app.py`; local server/browser and request safety. `build.py` fingerprints code to replace an older running version. |
| Local persistence | `paths.py` locates private data; `keystore.py` stores masked keys; `settings.py`/`settings_api.py` handle settings; `db.py` owns SQLite migrations; `logs.py` masks keys in private logs; `reset.py` owns deliberate deletion and competing-write protection. |
| Documents/profile | `documents.py`, `documents_api.py`, `profile.py`; uploads, text and cached structured profiles. |
| Search preparation | `preparation.py`; bounded private reuse of exact-input location readings and search-word groups, excluding research, scores and journeys. |
| Search coordination | `search.py`, `search_api.py`, `pipeline.py`, `pool.py`; progress, collection, decisions, cards and condition reapplication. |
| Places/criteria | `countries.py`, `location.py`, `reference_places.py`, `reference_sources.py`, `reference_tables.py`, `places.py`, `placenames.py`, `travel.py`; supported geography, query interpretation, finite reference-city evidence, exact table calculations and measurements. |
| Discovery | `keywords.py`, `employers.py`; multilingual words and periodically discovered employers. |
| Evidence/matching | `text.py`, `jobposting.py`, `dedupe.py`, `filters.py`, `freshness.py`, `relevance.py`, `jobplace.py`, `requirements.py`, `recheck.py`, `scoring.py`; text extraction, filtering, research, grounded requirements, saved-ad recovery and fit. |
| Results/evaluation | `applications.py`, `vacancy_evidence.py`, `jobidentity.py`, `jobstore.py`, `quality.py`, `quality_api.py`; application routes, verified original facts, remembered jobs, saved results and independent score checks. |
| `ai/` | `client.py` is the sole AI entry point; provider adapters, schemas, errors and token/web usage. |
| `sources/` | Isolated adapters and the registry. `base.py` defines `JobSource`; `http.py` applies polite requests/robots; `budget.py` tracks limits; `matching.py` matches lists; `careers.py` uses the directory; `careerlinks.py` recognizes career hosts. See [SOURCES](SOURCES.md). |
| `data/` | Public reference assets: `employers.json`, `places.csv.gz`, `regions.csv.gz`, `postcodes.csv.gz`. User data never belongs here. |
| `web/` | `index.html`, `app.js`, `style.css`, `favicon.svg`; plain UI, system fonts, no external scripts. |
| `tests/` | Scripted providers and mocked HTTP; `conftest.py` gives disposable fictional data. `test_imports.py` checks import order; `test_docs.py` checks navigation and recovery sections. |
| `docs/` | PROMPTS, PROGRESS, ENGINEERING, SOURCES; `guides/` for users and `archive/` for dated background. |
| `.githooks/`, `.github/` | Commit privacy guard, issue/PR templates, Mac/Windows/privacy CI. |

## Source reliability

### Greenhouse original temporal evidence — 2026-10-09

The [dated public contract and access check](SOURCES.md#greenhouse-temporal-evidence) separate
first publication from modification. The reader keeps missing/invalid originals unknown,
uses day precision for a date without a time, and recovers original publication and application
deadline from its existing full-detail response even when text is empty. Search's existing
post-detail rules exclude proven old/closed ads before scoring; unknowns remain visible.

`JobSource.detail_cache_version` defaults to 1. `jobstore` records/checks the reader version in
full-ad JSON; legacy unversioned entries are version 1. Greenhouse uses 2, so an old cache
cannot restore a modification timestamp as original publication. Old caches/snapshots are not
rewritten; incompatible cached details are refreshed within the existing source budgets, or
the job stays with incomplete/unknown evidence if unavailable. Corrected warm caches still
reuse full evidence, and scores are always new. The three-day text expiry remains unchanged.

A controlled no-network comparison against `4a640b8` used fictional teaching/nursing ads:

| Temporal evidence | Before | After | Detail stub reads per version |
|---|---|---|---|
| Only a recent edit date | Fresh | Unknown, retained | 0 |
| Only an old edit date | Too old | Unknown, retained | 0 |
| Existing details reveal old first publication | Fresh | Too old | 1 |
| Existing details reveal a passed deadline | Fresh/open | Closed | 1 |
| Original day overlaps the 24-hour boundary | Too old at invented midnight | Retained with day precision | 0 |

The cache regression proves a legacy cache needs one corrected detail read, then zero new
reads on warm reuse. End-to-end fictional searches prove old/closed cases make no scoring
call and the unknown case is scored/displayed. All 30 countries and non-engineering cases
are covered. These are behavior/request comparisons, not market freshness, recall, live speed
or paid-cost measurements. More unknowns can require more matching work within existing limits.

Original dates in other adapters still need independent source-specific audits. First post
publication does not prove a new underlying requisition. Post-vs-job IDs, bulk full-content
lists and private/internal API permission are separate evidence/measurement dependencies.
When another copy already supplies full text, the existing reader-selection gate can skip a
detail-only temporal check; dates/deadlines may also change within the unchanged cache window.
This correction does not claim complete original-date/deadline verification for every result.

### Maps recovery

**2026-10-08:** [Dated primary evidence](SOURCES.md#maps-request-limits-and-recovery) distinguishes
quota exhaustion from recoverable throttling. `GoogleMaps` reads supported ErrorInfo/QuotaFailure
hints before falling back to the full message; missing scope remains unknown. Known daily,
monthly or zero quotas stop after one attempt and remain unavailable within that meter.
Key/access refusals also stop; other hosts continue. No account quota is raised automatically.
The same meter is reused when online research reveals additional workplace locations.

`PoliteClient` has optional per-attempt preflight/charge and response-retry hooks. A preflight
checks allowance before waits; committed spending rechecks just before sending. Cache hits
bypass both, and Stop during a wait spends nothing for the unsent attempt. Retry-After remains
shared with other readers even when a caller declines a retry. Terminal responses keep the
cooldown but do not announce a retry that will not happen. Other source retry budgets remain a
separate audit; this change meters Maps, including its key test, without inferring extra access.
`RequestBudget` serializes committed check-and-spend in SQLite across independent instances;
preflight checks cannot reserve allowance or override a later failed check.

Maps wait details update the active step without restarting its timer; one stable note replaces
repeated different-delay warnings. Sanitized logs retain HTTP code/quota scope, without raw
provider messages that can name private accounts. Successful in-search cached responses remain
usable after a later quota failure or exhausted allowance. After request-level failures,
remaining jobs retain labelled AI estimates or unchecked routes within existing AI limits;
no scoring effort or criteria changed.
The source count now explicitly describes collected ads before matching/duplicate removal.

A no-network comparison against `97713bb` used two sampled destinations and a fake clock:

| Fictional case | Before | After | Evidence/limit |
|---|---|---|---|
| Structured daily quota | 4 attempts, 35 s simulated waits; 8 elements attempted, 2 recorded | 1 attempt, 0 s waits; 2 elements attempted/recorded | Same unavailable routes; jobs use labelled estimates/unknowns |
| 503 then success, allowance 4 | 2 attempts, 7 s wait; 4 elements attempted, 2 recorded | Same attempts/wait; 4 recorded | Same 19-minute measured journey |
| Same retry with allowance 2 | 4 elements attempted despite limit 2 | 1 attempt/2 elements, no unfunded wait | Unavailable measurement is labelled; no unauthorized extra attempt |
| Identical successful matrix read twice | 1 network attempt, 4 elements recorded | Same attempt, 2 recorded | Same measured journey; cache reuse spends nothing |

These are controlled retry/ledger measurements, not live end-to-end latency, charges or recall.
The ledger conservatively counts attempted elements, including refusals; Google decides actual
billing and other apps' requests are outside this counter. Missing originals/independent
ratings still limit live quality claims. Step timings include the activities of that stage;
filtering includes initial journey work, and online checking can include later journey work.
Answer waiting is recorded separately; compare original runs, not correction totals.

#### Maps spending proposal — 2026-10-09

**Follow-up:** the relevant account quota/billing dependency was inspected privately and a
targeted daily-quota correction was visibly verified. Exact account observations, limits and
proof remain outside Git. The app's monthly attempt allowance and total budget were preserved;
no paid route test or new search was run. The daily restriction is consistent with the saved
refusal pattern, but a successful post-change route/search is not yet measured. The current
owner-approved total is EUR30; the earlier EUR25 allocation proposal below is historical.

General lesson: distinguish daily project caps, per-minute throttling and the app's monthly
allowance before recommending extra credit. A daily cap can interrupt one run while monthly
headroom remains. Fix that specific restriction without automatically expanding monthly use,
enabling another API operation or buying a subscription. Keeping the monthly allowance still
means later work can reach it; do not promise measured journeys for every daily search or
solved fit quality from a quota edit. The estimate/sample-negative safeguard remains separate.

The owner asked whether reasonable paid Maps use would solve recurring errors without losing
good jobs or harming scores. This request authorizes a proposal; it does not choose a paid
allowance, change Google billing/quotas or authorize a paid diagnostic. The existing total
service budget remains EUR25/month. [Dated facts](SOURCES.md#maps-spending-and-alternatives) are
separate from the following engineering recommendation and unmeasured hypotheses.

Recommendation: retain Google Routes on pay-as-you-go for now, diagnose the exact refusal and
protect uncertain travel evidence before increasing usage. Propose a **maximum EUR10/month
Maps allocation within the EUR25 total**, pending an explicit owner decision and verified room
for the existing AI workload. Do not lower AI effort, drop jobs or remove evidence to fit that
allocation. If the combined workload cannot fit, report that dependency rather than silently
change quality or the total budget. A Maps euro target is not yet an implemented spending cap.

| Priority / action | Expected benefit and evidence | Effort / risk | Verification / dependency |
|---|---|---|---|
| 1. Identify the refused quota or access setup | High if it explains repeat failures; current generic warnings cover 429 and 5xx, not just a need to pay | Low / low for authorized saved inspection | Recheck private authority/checkpoint; prefer saved HTTP/quota scope and usage, then actual project quota, billing SKU and shared allowance. No new search needed |
| 2. Prevent uncertain negative travel evidence from rejecting a job | High recall protection: code still turns explicit long/null AI estimates and complete long/no-route city samples into a failed condition | Medium / medium; more uncertain results must not become false passes | Fictional engineering/non-engineering/all-country cases; independent workplace/route evidence before live accuracy claims. Recommended next free code improvement, not implemented by this proposal |
| 3. Add bounded paid headroom when needed | Helpful for an exhausted allowance, not missing schedules, wrong sample points or transient outages | Low account effort / spending risk | Approved allocation; actual SKU/free allowance, currency/tax, reset/ledger alignment and peak-use quotas. Preserve unknown results at limits |
| 4. Add or replace the route provider | Potential backup/coverage gain, currently unmeasured | High integration/maintenance / unknown price and coverage | HERE current price/terms/coverage, TravelTime production quote/rights or maintained licensed local feeds; compare the same independently verified journeys first |

The current matrix sends one workplace origin and up to two reference cities, each with an
edge and centre sample (centre-only requests have one sample per city). Identical coordinates
are coalesced within the measurement work; jobs in a qualifying city or outside the conservative
distance reach may need no Maps call. Multiple conditions, corrected/new locations, retries and
the key test can add elements. Therefore raw ad totals cannot be multiplied into the bill.

Fictional planning scenarios assume one travel condition, 30 daily searches, four elements per
distinct workplace that actually needs routing, no retries, the full corresponding free cap
available, and global first-tier pricing. These are calculations, not observed owner usage:

| Routed workplaces per search | Monthly elements | Matrix Essentials, USD | Matrix Pro, USD |
|---|---:|---:|---:|
| 50 | 6,000 | 0 | 10 |
| 75 | 9,000 | 0 | 40 |
| 100 | 12,000 | 10 | 70 |
| 150 | 18,000 | 40 | 130 |

The present request format appears to use Essentials, including TRANSIT plus departure time;
verify the actual billing SKU before promising a price. An illustrative small first paid
allowance of **11,000 monthly elements** would be USD5 before tax with the full Essentials free
cap, but USD55 if that cap were already consumed elsewhere. This is a candidate, not a changed
owner setting or an enforceable EUR10 cap. Currency/tax are not converted or assumed here.

Current `maps_monthly_routes` defaults to 9,000 attempted elements, not 9,000 jobs; existing saved
settings may differ. Attempts, including retries/errors, are metered conservatively before
sending; cached responses add none. `RequestBudget` currently groups the default UTC day/month,
while Google's free-usage month resets in Pacific time. Before a cap is presented as billing
protection, align the accounting window without rewriting historical counters, verify shared
account use and reserve a margin. Cloud budget alerts alone are not a hard stop. Choose Cloud
quotas from verified peaks and the monetary ceiling; an arbitrary tight daily quota can cause
the same false outage despite unused monthly allowance. Do not raise quotas blindly.

The required quality safeguard extends the already merged per-element correction: lack of a
confirmed journey must remain unknown. An AI estimate cannot prove that no acceptable route
exists, and two nearest cities/edge-centre samples cannot prove no district or farther city has
a faster connection. Prefer an actual workplace coordinate/address from the ad; a headquarters
elsewhere is not a substitute. Any future policy must distinguish an explicit requested
destination from a broad "any part of a qualifying city" condition, keep useful positive
measurements, and label confidence separately from job fit. Unknown travel must not be a
confirmed preference conflict or eligibility blocker. Today those estimate/sample negative
paths still exist; this proposal makes no claim that all false exclusions or scoring errors
have been solved. Historical search snapshots retain their original evidence.

No new routing provider, price-dependent feature, source, AI default or filtering behavior was
implemented here. No private result review, Google Cloud access, live route/provider call or
new search was used. Exact current account refusal, remaining allowance, relevant live route
accuracy and the combined AI/Maps spending forecast remain dependencies. If a live diagnostic
becomes necessary, request a separate bounded Jobcu-only test (for example, at most 8 elements
and EUR0.10) after scope/price/account checks; a full search or repeated key tests are unnecessary.

#### Partial route outcomes — 2026-10-09

The Deep improvement investigation ranked these alternatives before implementing one:

| Rank / candidate | Expected benefit and evidence | Effort / risk | Verification |
|---|---|---|---|
| 1. Maps per-route uncertainty | High: documented errors became failed conditions; 9 fictional baseline failures | Medium / medium | Partial data, no-route, fallback attribution, limits, persistence and scoring; implemented below |
| 2. Unresolved source-place filtering | High potential: the helper contradicts its keep-unknown contract | Small / medium | Regions/multiple locations, affected source permissions and independent coverage evidence |
| 3. Ashby secondary-country metadata | Potential country misses: parser/contract mismatch recorded in SOURCES | Medium / medium | API shapes, country/identity handling, terms and coverage sample |
| 4. Bulk full-content career lists | Possible fewer detail requests; documented capability already exists | Medium / medium | Payload/latency/evidence comparison; no assumed recall or cost saving |

Maps had a direct false-exclusion path and free reproducible evidence. Source additions/removals
were not justified by counts or documentation alone. These other candidates remain separate
leads; [SOURCES](SOURCES.md#search-method-research-leads--2026-10-09) records public contracts.

The empty-duration interpretation is superseded: a per-element service error, missing/invalid
answer or failed alternative is not a confirmed no-route outcome. `TravelReading` keeps usable
durations, unchecked towns and per-town attribution. A successful journey within the limit can
establish a pass; a longer partial journey cannot prove the unchecked alternative fails.
Only successful explicit no-route elements supply a known null. Raw response text is not shown
or logged; known access refusals or persistent per-element quota scopes stop later attempts.

The existing fallback estimates only unresolved towns without a usable Maps time. It preserves
Maps evidence and labels each town separately; only AI values reach `travel_memory`. Omitted,
unrequested or conflicting AI answers stay unknown. A passing known route needs no extra cache
read or estimate just to complete alternatives. Corrected limits reuse sufficient evidence;
changed reference towns need their own evidence. Routing version 3 refreshes old Maps readings
whose nulls did not distinguish errors; original saved result snapshots remain unchanged.

Fictional comparison with `786ccf2` (`tests/test_maps_elements.py`; no live calls):

| Case | Before | After | Meaningful check |
|---|---|---|---|
| Two service errors / missing or invalid answer | Failing travel condition; job excluded | Unknown condition; job retained for scoring | One matrix / two attempted elements; no raw account text |
| 60-minute valid sample, other sample fails; limit 35 | Excluded | Retained with 60-minute partial evidence and unchecked alternative | Valid duration retained, no invented fast journey |
| 19-minute valid sample, other sample fails | Pass | Same measured pass | No unnecessary fallback call; truthful Maps attribution |
| All samples explicitly no route | Fail | Same fail | No fallback call; distinct no-route wording |
| Failed town plus another town measured at 60 min | Null treated as no route | Existing 60 min retained; missing town can get labelled 22 min estimate | Only estimated town enters AI memory; card stays an estimate |
| Omitted AI alternative | Implicit null could reject a job | Unknown until supplied | No fabricated route or cached judgement |
| Known persistent quota in a partial response | Two attempts/four elements/1 s simulated host wait | One attempt/two elements/0 s wait; valid partial route retained | Same two fictional workplaces; remaining journey stays unknown |

A direct replay of baseline/current readers confirmed the service-error and long-partial
cases change from no to unknown with the same one attempt/two elements/zero waits. The short
19-minute partial route remains a pass with the same request count. The quota row above uses
a fake clock and identical response data; it does not measure actual latency or Google billing.

The initial 12-case reproduction had 9 failures on the baseline; these now pass. Broader
regressions cover all 30 countries, fictional engineering/teaching/nursing and two end-to-end
engineering/library searches where uncertain jobs reach scoring while confirmed no-route
jobs do not. They establish application behavior, not live route accuracy, market recall,
provider fit quality, cost or latency. Live review still needs the private procedure/evidence.

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
internal retries need a separate attempt-accounting audit outside Maps. The per-element Maps
empty-duration outcome is superseded by [partial route outcomes](#partial-route-outcomes--2026-10-09).
The Greenhouse modification fallback is superseded by the original-date correction above.
Original-date provenance in other adapters still needs a source-specific audit.
Provider retry/date handling and
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


### Independently saved application links — 2026-10-14

When a restored card has an opaque Adzuna primary link and an allowed, independently saved
**Employer's site** alternative, `applications.clean_card` promotes the employer link on the
response copy and retains the exact Adzuna route under alternatives. Current collection already
prefers `employer_url`; restored and marked cards now agree. Scores, marks and historical
snapshots remain intact, and repeated display is stable. Other-board links cannot establish
an employer original; blocked/reported destinations remain excluded. UI copy explains the
forwarding route plainly. No redirect is resolved, unwrapped or fetched. Adzuna route
replacement remains blocked by its current compliance requirement and absent final-host field;
see [dated contract evidence](SOURCES.md). Fictional regressions
cover electronics, nursing, teaching, hospitality, blocked/opaque alternatives and history.
