# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions/implementation: [ENGINEERING](ENGINEERING.md); dated
contracts/access facts: [SOURCES](SOURCES.md). Detailed history lives in Git and PRs.

## Right now

*Updated 2026-10-15. Engineering checks use fictional data.*

### State

- [Independently saved application links](ENGINEERING.md#independently-saved-application-links--2026-10-14)
  are implemented in [PR #118](https://github.com/UtkuDenizAltiok/jobcu/pull/118), source
  `9b017d0` on `codex/direct-application-links`, based on `1468a30`. Restored and marked cards
  use an allowed, independently collected employer link directly when already saved for the
  same job, retaining the exact Adzuna route under alternatives. Opaque-only cards explain
  forwarding and missing destination evidence. History, scores, marks and source rules remain.
  The 133 affected and final 1,578-test checks pass, with one existing dependency warning;
  Ruff/privacy, 20 documents, JS syntax and complete diff/whitespace checks pass. Publication
  is complete: final head `336fbc6`, merge `90a72e3`, exact PR CI `38533873149` and main CI
  `38534533490` passed Mac/Windows/privacy. No private redirect or destination was fetched.
  Automatic replacement of the Adzuna advertiser route needs explicit Adzuna permission and a
  permitted interface; [dated evidence](SOURCES.md) separates this dependency from independent
  originals that Jobcu already collected. No account change, paid call or new search was made.
- [Task focus and scoring confidence](ENGINEERING.md#task-focus-and-scoring-confidence--2026-10-14)
  is implemented in [PR #117](https://github.com/UtkuDenizAltiok/jobcu/pull/117), source
  `3fe11f4` on `codex/task-focus-scoring`. Neighbouring/gapped main work has an 80 maximum;
  tied totals favor the stronger weakest fit area, then freshness. Technical prerequisites
  and proficiency remain distinct from general seniority. Uncertain location conditions limit
  preference points without suppressing useful evidence checks; resolved conditions restore
  points. Recognized tracking-only variants retain unusable-link reports, preserving independent
  alternatives and history. Original reference-city semantics and owner scoring limits remain.
  The 263 affected and final 1,570-test checks pass, with one existing dependency warning;
  Ruff/privacy, 20 documents, JS syntax/ordering and complete diff/whitespace checks pass.
  Publication is complete: final head `bd7f1a7`, merge `1468a30`, exact PR CI `38531858561`
  and main CI `38532483632` passed Mac/Windows/privacy; main was synchronized cleanly.
  Detailed balanced saved judgements, timing/billing limits and reported application identities
  remain private. Offline verification does not establish live model accuracy or market recall.
- Exact setup edits are published in [PR #116](https://github.com/UtkuDenizAltiok/jobcu/pull/116),
  head `398a40f`, merge `41e3cb8`. Exact PR CI `38527412545` and main CI `38527892757`
  passed Mac/Windows/privacy; the 1,519-test final local suite remains the unchanged baseline.
  Raw box text and original document/box word identity prevent accidental reuse after edits;
  actual profile host/reasoning controls participate too. Jobs and scores remain fresh.
  Detailed saved review, uncertainty, billing and application-route dependencies remain private.
- [Search preparation reuse and connection clarity](ENGINEERING.md#search-preparation-reuse-and-connection-clarity--2026-10-14)
  is in [PR #115](https://github.com/UtkuDenizAltiok/jobcu/pull/115), source commit `f504f69`
  on `codex/search-preparation-reuse`: successful unchanged location readings
  and word groups can be reused for 30 days; fresh research, jobs, scores and travel rules
  remain. Migration 16 preserves history and adds only private setup storage. Final local
  1,490-test, Ruff/privacy, 20-document and whitespace/full-diff checks pass. Publication is
  complete: final head `6dbf72d`, merge `8f730ba`, exact PR CI `38472126047` and main CI
  `38472857093` passed Mac/Windows/privacy. This verifies offline behavior, not a live bill
  or connection repair.
- The continuing review's scoring, Wednesday 10:30 transit timing and incomplete-reference
  explanations are published in [PR #113](https://github.com/UtkuDenizAltiok/jobcu/pull/113),
  final head `b23e953`, merge `3075b9a`. Exact PR CI `38304883132` and exact main CI
  `38305333288` passed Mac/Windows/privacy. Its 1,420-test local final check remains the
  baseline. The owner's more forgiving experience/language maximums are in
  [PR #114](https://github.com/UtkuDenizAltiok/jobcu/pull/114), source commit `64282ef` on
  `codex/owner-score-limits`; 174 affected and 1,431 full-suite tests pass (one existing
  dependency warning), with Ruff/privacy, 20 document checks and whitespace/full-diff review.
  PR #114 publication is complete: final head `2c5a9d2`, merge `b1b0f6f`, exact PR CI
  `38308967181` and exact main CI `38309537820` passed Mac/Windows/privacy.
  No paid call, new search or owner-state change is made.
- [Original evidence and repeated requests](ENGINEERING.md#original-evidence-and-repeated-requests--2026-10-12)
  is published in [PR #111](https://github.com/UtkuDenizAltiok/jobcu/pull/111), head
  `e869a58`, merged at `71dd6fc`. Exact PR-head CI `38295942407` and merged-main CI
  `38296731440` passed on Mac, Windows and privacy. Original-text collection, Markdown
  grounding, honest information/uncertainty markers, per-search Maps element reuse and reset
  cost clarity are implemented. Public employer references were independently verified.
  [PR #112](https://github.com/UtkuDenizAltiok/jobcu/pull/112) completes the mixed-copy freshness
  regression, merged at `397d932`; exact PR CI `38299591582` and exact main CI `38299970712`
  passed Mac/Windows/privacy. No live accuracy, recall or savings is inferred; private evidence
  stays outside Git.
- [AI billing refusals, Stop and usage recovery](ENGINEERING.md#ai-billing-refusals-stop-and-incomplete-usage--2026-10-12)
  is published in [PR #109](https://github.com/UtkuDenizAltiok/jobcu/pull/109), merged
  at `a698ea6`. Exact PR-head CI `38287331688` and merged-main CI `38287834077` passed
  on Mac, Windows and privacy. The local final suite passed 1,333 tests (one existing
  dependency warning); Ruff/privacy, JS syntax, 20 document checks, whitespace and full
  diff review passed. Fictional before/after tests verify terminal credit refusals,
  cancellable retry/queued waits, completed-answer retention and incomplete usage markers.
  Migration 15 preserves old receipts and ratings. Existing provider, medium effort,
  evidence checks and owner limits are preserved; no live savings or matching gain is claimed.
- The authorized saved review used a shuffled balanced packet including every top card;
  available evidence was judged before score reveal. Detailed billing, source contributions,
  judgements and exact missing-evidence dependencies are saved privately in the directory
  referenced by `assistant-review-checkpoint.json`. Owner/legacy ratings were preserved;
  unknowns were retained. No paid test, new search, job-site request, source/provider switch,
  account change or reset was made. Disposable review and fictional startup data are removed.
  Owner app 8765 remains running and was preserved; assistant preview 8799 is stopped.
  The next normal launch loads the repair. Exact historical billing attribution, missing
  originals/conditions and an independent date-verified benchmark remain evidence limits.
- Start recovery verified the final session handover in
  [PR #107](https://github.com/UtkuDenizAltiok/jobcu/pull/107), merged at `c75cbd9`.
  Exact PR-head CI `38043089148` and merged-main CI `38043353599` passed on Mac,
  Windows and privacy. Clean main was synchronized and `uv sync --locked` passed.
  Owner app 8765 and preview 8799 were both stopped; that state was preserved.
  The completed publication checkpoint below was cleared. No private review, paid call,
  job search or new development goal was started.
- [Quality-first API and electronics coverage decision](ENGINEERING.md#quality-first-api-and-electronics-coverage-decision--2026-10-10)
  replaces earlier price-led/Go-centred trial ordering. The broader public survey includes
  stronger models and native research contracts; direct MiMo Pro is the first replacement
  hypothesis, with counterevidence and explicit no-regression gates. Keep working Gemini
  medium pending a focused comparison. Electronics employer originals outrank remote-only
  expansion. Source references, permissions and precise integration dependencies are in
  [SOURCES](SOURCES.md#public-api-market-and-quality-evidence--2026-10-10). No provider switch,
  new source, paid call, search, account edit or private-results review was made in this step.
  [PR #105](https://github.com/UtkuDenizAltiok/jobcu/pull/105) is merged at `d7bee16`;
  exact PR-head Mac/Windows/privacy CI `38034813256` and merged-main CI `38035224672`
  passed. Local document/Ruff/privacy/whitespace checks and full diff review passed.
  The completion handover in [PR #106](https://github.com/UtkuDenizAltiok/jobcu/pull/106)
  is merged at `23b8da6`; exact PR-head CI `38035535171` and merged-main CI `38035793937`
  passed on Mac, Windows and privacy. No remaining implementation or publication from that
  task is pending. End observed owner app 8765 and preview 8799 both stopped; preserve this
  on-demand state. Private evidence/authorization remain intact; disposable task files are gone.
- [Employer discovery recovery](ENGINEERING.md#employer-discovery-recovery-and-service-choices--2026-10-10)
  retries incomplete countries on the next normal search, keeps successful countries/employers
  and explains missing discovery. Migration 14 preserves history while rechecking ambiguous
  legacy timestamps once. Existing medium effort, source permissions and limits remain.
  Published in [PR #103](https://github.com/UtkuDenizAltiok/jobcu/pull/103), merge `ff61bcb`.
  Exact PR-head Mac/Windows/privacy CI `38032271821` and merged-main CI `38032481853` passed.
  Local 1,312-test suite, Ruff/privacy/whitespace, 20 document checks and isolated startup pass.
  The preview stopped and disposable data was removed; owner app/data/settings were preserved.
- [Additional source and direct-provider research](SOURCES.md#employer-feeds-and-remote-candidates--2026-10-10)
  identified Jobicy as a remote-feed candidate with freshness/evidence checks still
  needed; remote-only expansion is now low priority. Its inexpensive direct-API subset is
  superseded by the broader quality-first survey above. Keep the working configuration; no purchase,
  provider switch, paid test or search was made. Detailed saved-demand scenarios stay private.
- The [structured Ashby workplace correction](ENGINEERING.md#structured-employer-workplace-evidence--2026-10-10)
  recovers towns/countries from primary and secondary addresses and preserves original ads.
  Legacy caches cannot restore discarded metadata. Fictional collection/check-selection cases
  cover all countries, nursing/teaching/hardware and unknowns without more source requests.
  [PR #102](https://github.com/UtkuDenizAltiok/jobcu/pull/102) is verified merged at `d7017e5`;
  exact-main Mac/Windows/privacy CI `38030324705` passed. No provider, source, effort,
  allowance, account or owner-data change was made.
- [Current source and complete-cost research](SOURCES.md#broad-boards-and-web-discovery--2026-10-10)
  rechecked broad boards, Google discovery, Go's entire table and direct/discounted processing.
  No permitted new broad-board reader was established. Go remains a candidate; shared limits
  alone do not reject it. Live quality/coverage and model-dependent bills remain unmeasured.
  Private saved-demand/timing evidence stays private; no paid call or new search occurred.

- [Complete AI answers and online-check recovery](ENGINEERING.md#complete-ai-answers-and-online-check-recovery--2026-10-10)
  is in [PR #101](https://github.com/UtkuDenizAltiok/jobcu/pull/101): Gemini receives answers
  incrementally, requires successful completion
  and retains late grounding/usage metadata. Broken or clipped answers cannot become judgements.
  Parallel cleanup preserves other requests. Notes now distinguish throttling, connection retries
  and unfinished online checks. Medium effort, request content and existing limits are preserved.
- The completed-search review followed the private procedure with shuffled judgements before
  score reveal, including every top card. Detailed evidence and supported assistant labels stay
  private; owner/legacy ratings were preserved. Missing originals, original dates, researched
  conditions and an independent coverage benchmark prevent broad accuracy/recall claims.
  Source contribution was inspected; no method was removed on counts or temporary failures.
- The [Go decision and readiness update](ENGINEERING.md#go-feasibility-and-interruption-continuity--2026-10-09)
  preserves one Gemini model at medium plus Maps for the owner's next on-demand 24-hour search.
  Dedicated Discord forum and independent Reddit questions were delivered with explicit owner
  instructions; the old Zen question became a redirect. Two active questions, no cross-reference
  in Reddit. Replies and proof stay in the private checkpoint; no provider clarification was
  received at this checkpoint. Go remains a candidate, not an established quality improvement.
  Compare its full subscription/tool cost with direct APIs before adoption.
- Read-only saved-setup checks and isolated fictional startup passed without provider calls,
  purchases, searches or owner-state changes. Disposable scratch was removed and the preview
  stopped. Local readiness does not prove live service availability, balance or result quality.
- AI Settings now has one optional advanced section, a visible summary of active model/
  research overrides and an honest **Other API** label. Custom formats open their required
  setup controls. Existing choices, keys, routing and medium defaults are preserved.
  [PR #96](https://github.com/UtkuDenizAltiok/jobcu/pull/96) is verified merged at `61e6d9c`;
  exact merged-main Mac/Windows/privacy CI `37984746346` passed.
- The [earlier Go reassessment](ENGINEERING.md#go-feasibility-and-interruption-continuity--2026-10-09)
  keeps Go as a viable host candidate; its trial ordering is superseded by the broader decision
  above. Preserve working Gemini medium meanwhile. Several candidates support documents,
  structured output and research features; shared limits alone do not reject one daily search.
  This supersedes interpreting the earlier do-not-buy-now wording as permanent exclusion or
  claiming all 32 models are unable to do Jobcu's work. No candidate's matching superiority is
  measured. Intended-use fit, hosted research/fees and labelled quality remain adoption checks.
  [PR #98](https://github.com/UtkuDenizAltiok/jobcu/pull/98) is verified merged at `fae35e2`;
  exact merged-main Mac/Windows/privacy CI `37989205909` passed. Git object and read-only
  saved-search integrity checks found no interruption damage or newer unfinished search.
- The owner delegates technical decisions and explicitly raised the total ceiling to EUR30/
  month, superseding EUR25 and the larger proposal. Preserve working settings/keys and limits.
  No new purchase, top-up, provider switch, paid test, new search or further account edit was
  made. The earlier EUR10 Maps / EUR15 AI split is not an implemented allocation or invoice.
- Go's public billing code confirms weighted shared subscriber counters across models, not
  independent pools. Dated reset rules/arithmetic, complete 32-model assessment, terms and
  exact permission/quality dependencies live in [SOURCES](SOURCES.md#opencode-go-and-ai-credit-eligibility).
  Model count and cached coding-request estimates do not prove daily Jobcu capacity or accuracy.
  Gemini prepaid credit cannot pay for Maps. The targeted Maps daily-quota correction is already
  verified privately; live post-change route/fit quality is not yet measured.
- [PR #95](https://github.com/UtkuDenizAltiok/jobcu/pull/95) is verified merged at `d4ac53c`;
  exact merged-main Mac/Windows/privacy CI `37979826008` passed. Custom Chat Completions,
  Responses/Messages, explicit thinking controls and separate research are available. See
  the [complete assessment](ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09).
- [PR #93](https://github.com/UtkuDenizAltiok/jobcu/pull/93) is verified merged at `597701d`;
  exact merged-main Mac/Windows/privacy CI `37969222262` passed. Integration ease and vendor
  effort labels are not quality verdicts. The [additional model assessment](ENGINEERING.md#additional-model-assessment--2026-10-09)
  puts MiMo Pro alongside GPT-6 Luna in the first comparison, with DeepSeek V4.1 Flash and
  GLM-5.3 also serious candidates. No evidence establishes Gemini's matching superiority.
- [PR #92](https://github.com/UtkuDenizAltiok/jobcu/pull/92) is verified merged at `8a5b132`;
  exact merged-main Mac/Windows/privacy CI `37963987419` passed. Its publication is complete.
- The Maps correction is merged in [PR #90](https://github.com/UtkuDenizAltiok/jobcu/pull/90)
  at `3d8cb30`; exact main Mac/Windows/privacy CI `37914682388` passed.
  Per-route service errors, missing/invalid answers and unchecked alternatives stay uncertain
  rather than proving a travel failure. Valid partial Maps times remain; fallback estimates
  have per-town attribution and only AI values enter AI memory. Explicit no-route results
  remain distinct. Known access/persistent quota refusals stop later requests; limits stay intact.
- Existing condition edits reuse sufficient readings; routing version 3 refreshes old Maps
  entries that could not distinguish errors from no route. Historical result snapshots and
  scoring criteria are preserved. Every AI step still defaults to medium.
- [PR #91](https://github.com/UtkuDenizAltiok/jobcu/pull/91) is merged at `d5a1a1d`;
  exact main Mac/Windows/privacy CI `37923012101` passed. The Maps spending question has a documented
  [recommendation](ENGINEERING.md#maps-spending-proposal--2026-10-09), public price/SKU/control
  evidence and fictional cost scenarios. Retain Google for now; diagnose actual quota/access
  and protect uncertain negative travel evidence before enlarging usage. A proposed EUR10
  Maps allocation proposed under the earlier EUR25 total remains provisional pending account/
  combined-workload checks; willingness to pay does not establish sufficient headroom.
  No billing, quota, setting, provider or filtering change was made.
  That account dependency was subsequently inspected and a targeted correction verified;
  post-change live route/search success and fit quality remain unmeasured.
- Earlier route checks passed: **1,125 tests**, Ruff, privacy, whitespace, document links and complete
  diff review, plus an isolated startup self-test that stopped and removed its disposable data.
  Fictional cases cover all 30 countries, engineering/teaching/nursing, partial/malformed data,
  Maps/AI attribution, persistence, limits and two full engineering/library search pipelines.
  [Before/after evidence and limits](ENGINEERING.md#partial-route-outcomes--2026-10-09) distinguish
  application correctness from unmeasured live route/fit quality, coverage, cost and latency.
- Public Routes/Ashby/Lever documentation, Maps policy/limits/prices and source contribution
  alternatives were researched; dated facts and hypotheses live in SOURCES. No source was
  added/removed on insufficient evidence. No new job search, paid call or live vacancy fetch
  occurred. Owner search data, settings, limits, keys and authorization are untouched.
- [PR #89](https://github.com/UtkuDenizAltiok/jobcu/pull/89) is merged at `786ccf2`; exact main
  Mac/Windows/privacy CI `37907028979` passed. Its session workflow remains current: Start
  prepares/recovers and waits; Review/Deep improvement use the prepared chat; End parks safely.
- Prior app changes are merged: [PR #86](https://github.com/UtkuDenizAltiok/jobcu/pull/86)
  added confirmed resets and optional Settings → Review results; [PR #87](https://github.com/UtkuDenizAltiok/jobcu/pull/87)
  corrected Greenhouse original-date evidence and reader-version cache recovery. Historical
  snapshots keep their original scores/date labels. Reset preserves settings, keys, assistant
  authorization and real usage counters; full reset deletes review evidence/checkpoints.
- Last observed owner app state in this Deep improvement: running (8765). The owner opened it;
  the assistant preserved it. The read-only saved run/usage is unchanged, with no newer unfinished
  attempt. The isolated fictional preview at
  8799 is stopped, its tab closed and disposable data removed. Authorized saved evidence and
  checkpoints stay private; owner data/settings are preserved. Recheck actual app state once
  on resume and preserve the owner's choice.

### In progress

**Latest saved review and evidence recovery — owner task, 2026-10-15:**
On `codex/evidence-recovery`, base `90a72e3`; previous free work is complete, unchanged
1,578-test baseline may be reused if code/tests/dependencies/environment remain identical.
Authorized scope: privately review the latest finished run against actual documents/criteria,
reuse unchanged sealed judgements and inspect initial delay, provider/source failures,
freshness/coverage/duplicates/exclusions, requirements/travel and uncertainty throughout the
pipeline. Use read-only reporting and a private isolated snapshot; preserve owner state and
ratings. No new search, paid test/call, account/network/settings change or blocked-site bypass.
Steps: save a balanced blinded review including all top cards, distinguish run boundaries and
usage uncertainty, rank a small evidence-backed shortlist, implement the strongest reproducible
free improvement with fictional multi-profession/failure regressions, update its guides/records,
run affected/final tests and Ruff/privacy/JS/docs/diff checks, publish with exact PR/main-head
Mac/Windows/privacy CI and merge commits. Detailed evidence/checkpoints stay private.
Read-only reporting, isolated snapshot and balanced sealed evidence judgements are complete;
no newer unfinished attempt was found. Details, shortlist, original timing/failure separation
and evidence limits are private. Chosen coherent step: preserve Unicode dash word boundaries
before duplicate matching, retain legacy remembered identities, gate route decisions/requests
on checked reference-place facts, and make missing checks and nonbinding score ceilings clear.
Keep unknown jobs available; do not invent verification, weaken matching guards, change source
permissions or remove evidence checks. Connection failures have no demonstrated balance cause.
Implementation is complete, including native Gemini cleanup resilience: a transport error
while closing a response cannot discard a completed answer/citations or replace a meaningful
failure and its usage. Three real-SDK fictional reproductions fail before and pass after;
this is not established as the cause of saved pre-answer disconnects. Final 1,620 tests pass
(one existing dependency warning); 294 matching/travel/search and 103 provider checks pass.
Ruff/privacy, 11 current non-archive documents, JS syntax/fictional card DOM and complete
diff/whitespace checks pass. Detailed supported labels/unknowns and before/after diagnostics
are saved privately; owner history/marks/settings/authorization and owner/legacy labels remain.
Exact next action: commit/push the completed step, create/attach its PR, verify Mac/Windows/privacy
CI on its exact final head, merge with a merge commit, synchronize main and verify exact-main CI.

**Whole-pipeline quality, coverage and complete-cost improvement — 2026-10-12.**
Prior free work, including PR #114's owner scoring adjustment, is fully published and verified;
receipts are in Right now. The bounded provider comparison remains blocked below. Do not
reopen completed work or rerun unchanged checks.

**Direct-destination dependency — owner continuation, 2026-10-14:**
The justified free improvement in PR #118 is fully published and verified (Right now).
Its stale publication checkpoint is cleared; the permission dependency remains parked.
Automatically resolving and replacing Adzuna's supplied advertiser route remains blocked:
its schema requires that route and does not supply the final host; blocked pages cannot be
probed. Exact next action only if that scope is reopened with Adzuna's explicit permission:
verify its permitted destination interface, retention/attribution/request rules, then implement
bounded redirect handling with fictional failure/privacy regressions. Preserve the required
route meanwhile. No private redirect, new search, paid call or owner-state change is authorized.

Private `assistant-review-checkpoint.json` points to `active_completed_review`: the latest
finished attempt has a balanced blinded review including every top card, original run-boundary
measurements, detailed cost components and supported assistant labels. Owner/legacy ratings,
settings, marks and historical results were preserved. Owner-identified unusable
application routes were reported with the owner's authorization; no opaque destination was fetched.
Missing original evidence, unresolved reference facts, incomplete billed usage and an eligible
independent benchmark prevent broader quality, recall or invoice claims. No newer unfinished
attempt was found at review. Publication receipts are saved privately and disposable scratch is
removed; preserve owner app 8765 and private authorization/evidence.

**Dependency after publication:** a direct API key entered only in Jobcu and owner authorization
for a **EUR5 total** fictional paired comparison within the existing EUR30 monthly ceiling.
[Market/rights/fees](SOURCES.md#api-market-and-reuse-update--2026-10-12) selects direct MiMo Pro
as the one challenger, with factual/document/latency counterevidence. Keep working medium settings
and fresh cited research. Its coding Token Plan explicitly excludes this app; do not buy it.
The assistant owns execution/judgement; no model-shopping, owner ratings or new search is needed.

Remaining authorized scope is conditional preparation only: recheck standing authorization,
revocations and the private checkpoint, exact model/API/use/rights/fees and remaining total
headroom before any call. The packet has 30 balanced fictional cases, six ambiguous repeats
and separately gated hosted research. Unknown charges/outcomes or any quality/coverage regression
stop the comparison and block adoption. Protected source evidence must not move before its
rights are resolved. Exact next paid action, only when those dependencies are satisfied: verify
the frozen packet against the current task-focus policy and run the first paired five-ad
fictional batch through `AIClient` on an isolated copy, saving complete answers and token/tool/failed usage before continuing inside the
ceiling. No calls are authorized yet. Otherwise retain this dependency and wait for owner input.

### Verify before relying on

- Discovery: completion/retry behavior is verified offline, not live recall. The next normal
  launch loads the change and may recheck ambiguous legacy timestamps once within existing
  limits. No additional job search or owner-data reset is required for development.
- Direct API challengers: [broader catalogue, native controls and hosted research](SOURCES.md#public-api-market-and-quality-evidence--2026-10-10)
  do not establish fit equivalence or total bills. Exact model/version/tool response support,
  independent outcomes and half/equal/double demand comparisons are adoption gates. A bounded
  paid-test budget and an account key entered only in Jobcu remain required before paid work.
- Provider change: current Go permission/tool/protocol/medium support, real token/tool workload,
  shared limits and bounded labelled comparison remain unverified. Existing Gemini credit is
  not a Maps allowance. Do not promise accuracy, savings or full daily capacity from the tables.
- Before a private review, recheck authorization/revocations and the private review checkpoint.
  The earlier `score_review_resume` is a dated review, not a current quality judgement. Verify
  saved evidence still exists, especially after an owner reset. No data reset is authorized here.
- Freshness: other adapters still need original-date audits. A first post date is not proof of
  a new underlying requisition; the three-day cache and full-text reader-selection gate can
  leave temporal metadata unchecked. Unknown/secondary-board dates remain incomplete proof.
- Ranking/title screening: incomplete originals and independent top-card/early-title labels
  limit accuracy claims. Scores/counts are not hiring odds or recall measurements.
- Coverage: an independent date-verified 15–25-job benchmark remains, in AGENTS' country order.
  Source value includes unique jobs, better evidence and backup coverage, not total ad counts.
- Maps: per-element uncertainty is covered by fictional regressions; live route accuracy
  remains unmeasured. AI negative estimates and complete negative city samples can still
  reject jobs. City-edge/centre sampling is approximate. Price/cap changes need the actual
  account controls, reset alignment and forecast before changing any further allowance. Daily
  quota/SKU/billing were verified privately; post-change live success/accuracy remains untested.
- Live timing/ranking comparisons need bounded authority/current prices. Spare assistant usage
  grants no private APIs, spending, site logins or new/background searches.
- A fresh Windows installation/upload/search walkthrough remains untested; launcher CI is narrower.

### Waiting on the owner

- Go adoption is deferred, not rejected. The [generic support question](guides/getting-your-keys.md)
  was sent with explicit instructions in two independent places; no further post is needed.
  Await provider clarification of intended-use fit and hosted tools/fees. Subsequent adoption
  needs a key entered only in Jobcu and an explicitly bounded fictional matching comparison.
  Hosted custom research is currently disabled by an
  integration guard; positive reports justify verification. Do not infer new paid-test authority
  or start another search for this investigation.
- Keep one working Gemini model at medium; no Go purchase, replacement key or model choice is
  needed for the working setup. Go remains a candidate. The relevant Maps account investigation
  and targeted daily-quota correction are
  complete; no further payment/quota homework is needed for that correction. The next normal
  on-demand search can provide post-change evidence. Its monthly attempt allowance still
  applies; this is not a promise of measured journeys on every daily search.
- The owner approved EUR30/month total; no larger ceiling or particular allocation is approved.
  No paid test or app-limit change has been performed; a focused live diagnostic or model
  comparison needs a separately bounded paid-test budget. No extra provider key is needed
  until its integration path and trial scope are ready.
  The assistant chooses technical options; the owner need only decide actual spending and
  perform required account steps. No rating homework or reset is required.
- In a fresh local chat use [Start](PROMPTS.md#start-a-session), then send
  [Review](PROMPTS.md#review-a-search) after a completed search or
  [Deep improvement](PROMPTS.md#deep-improvement) without needing a new search. Use
  [End](PROMPTS.md#end-a-session) before closing the chat. Neither work prompt repeats startup.
- No new keys/settings or rating homework is required; Jobcu may be open or closed during
  development. New backend changes load on the next owner-initiated launch. When ready to
  search, use **24 hours** on demand within existing limits; no new search is required here.
- [Reset scopes](guides/first-search.md#clear-data-and-start-fresh) explain deletion/preservation.
  Only reset deliberately; a full reset requires uploading documents again. Optional
  **Settings → Review results** remains available for your own feedback.

### Next tasks

Candidates for an owner-requested development task, not automatic work during Start:

1. In an owner-requested Maps development task, reproduce estimated/sampled negative travel
   exclusions and keep incomplete evidence unknown through filtering/scoring. Then inspect
   authorized saved diagnostics before any proposed quota increase. The next free reproduction
   belongs in `travel.answer`, its filter callers and scoring background; use fictional jobs.
2. Reproduce unresolved source-place exclusions, including regions and multiple locations;
   verify affected permissions and preserve unknowns before changing the helper.
3. Continue original-date audits in other adapters, including future timestamps and metadata
   skipped when another copy provides full text. Keep unknowns rather than cut counts.
4. Recover originals/independent labels, review unknown top cards and title rejections, then
   trace an independent date-verified coverage sample. Do not tune to one ad or score distribution.
5. Compare new/existing methods and structured public APIs for unique useful jobs, original
   evidence, country/profession gaps and reliability. Ashby metadata recovery is complete.
   Prioritize [electronics employer references and unread systems](SOURCES.md#electronics-employer-and-specialist-coverage--2026-10-10)
   in country order; remote-only expansion has low priority. Reference names do not prove
   active jobs, collection permission or misses through other sources.
   [Jobicy](SOURCES.md#employer-feeds-and-remote-candidates--2026-10-10) is a remote-feed
   candidate; verify host rules, eligibility/original dates and contribution before adding it.
   Improve/add/replace/remove based on terms and evidence; private/internal endpoints need
   documented authority. Held portals need permission before automated collection.
6. Review repeated/slow work on saved evidence; paired live tests need bounded authorization.
   A fresh Windows beginner walkthrough remains later free work.

### Known limitations

- Historical snapshots retain old evidence; summaries, unknown posting dates and unchecked
  conditions remain incomplete proof. Optional ratings do not automatically train AI.
- Opaque application destinations and final-host checks remain unverified. A changed redirect
  needs a new report; undo restores retained links, while an omitted vacancy may need the next
  on-demand search. An alternative link does not prove registration access.
- Maps edge/centre samples are approximate. Correction timings cover the latest correction;
  usage accumulates. Token cost estimates can omit fees/discounts and are not invoices.
- A failed final save can lose visible results on closing; earlier saved searches remain.
