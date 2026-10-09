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
| Retry research on a later search; never mark a refused employer lookup as a successful refresh. | A temporary restriction must not suppress future employer discovery (2026-10-06). |
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

## Practical service choice — 2026-10-09

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

An optional **separate research provider** is a promising quality-preserving architecture,
not an implemented feature. Retain Gemini's fresh cited research while evaluating a different
main model for extraction, criteria, screening and scoring; do not move every `job_places` or
`location` call merely by step name, as those steps also contain structured extraction.
Preserve one logical client's search web budget, monthly ledger, per-provider keys, cancellation,
medium defaults and correct usage attribution. Never silently switch providers or lower effort
on a refusal. Native direct GPT already has a Responses adapter; custom Go needs an explicit
compatible Responses path. A coding agent wrapper is not a workaround for permitted-use rules.

Before a purchase/switch, a bounded Jobcu-only fictional comparison must assess explicit
requirements, multilingual title/criteria interpretation, evidence quotes, unknowns and ranking,
including engineering/non-engineering and all-country cases. Repeat borderline cases and
judge against independent labels; JSON validity and cheaper output alone are insufficient.
No paid comparison, hybrid implementation or migration is included in this decision step.

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
No mapping, model switch or quality claim was implemented in this assessment.

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

Migration acceptance gates, all still pending:

1. For Go, confirm permission for on-demand personal job matching with document interpretation
   and JSON scoring. Identify the client honestly as Jobcu and use opaque stable session IDs;
   do not impersonate a validated coding agent or route private tasks through another client.
2. Preserve medium, structured answers and necessary web research through a correctly routed
   adapter. `CompatibleAdapter` currently sends Chat Completions, no explicit effort or custom
   Go identity/session headers, and advertises no web research. Native OpenAI/Anthropic adapters
   use their own provider addresses; a Go key must not be entered under those native providers.
   Go's protocol translation may accept extra formats, but that is not a tested migration.
3. Verify Go hosted-search entitlement and fees, or deliberately implement/test a separately
   chosen research provider. Current settings have one provider; the optional reasoning model
   is another model of that provider, not a second research account. A silent loss of employer,
   place or requirement research is a quality regression. Existing Gemini credit may be useful
   for Gemini work, but a split-provider workflow is not implemented or assumed here.
4. Before switching, run a separately authorized bounded fictional comparison through Jobcu:
   profile extraction, multilingual criteria, unrelated-title decisions, requirement quotes,
   permits/languages, unknowns and borderline scoring, including non-engineering/all-country
   cases. Compare against independent labels, current Gemini and repeated borderline outputs;
   record errors, schema repairs, reasoning/tool tokens and time. No fresh real search is needed.
   Real accuracy/coverage claims still require CONTRIBUTING's private procedure and originals.
5. Diagnose Maps independently from AI billing. Verify the actual quota, Maps SKU, credit grant
   eligibility and usage; preserve uncertain journeys. The earlier
   [Maps allocation proposal](#maps-spending-proposal--2026-10-09) remains pending. No credit
   transfer/refund or billing change is implied. Keep the EUR25 total, taxes/currency and room
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
| Search coordination | `search.py`, `search_api.py`, `pipeline.py`, `pool.py`; progress, collection, decisions, cards and condition reapplication. |
| Places/criteria | `countries.py`, `location.py`, `places.py`, `placenames.py`, `travel.py`; supported geography, query interpretation and measurements. |
| Discovery | `keywords.py`, `employers.py`; multilingual words and periodically discovered employers. |
| Evidence/matching | `text.py`, `jobposting.py`, `dedupe.py`, `filters.py`, `freshness.py`, `relevance.py`, `jobplace.py`, `requirements.py`, `scoring.py`; text extraction, filtering, research, grounded requirements and fit. |
| Results/evaluation | `applications.py`, `jobidentity.py`, `jobstore.py`, `quality.py`, `quality_api.py`; application routes, remembered jobs, saved results and independent score checks. |
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
