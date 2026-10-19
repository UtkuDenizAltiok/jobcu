# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); implementation/decisions: [ENGINEERING](ENGINEERING.md);
source permissions and dated facts: [SOURCES](SOURCES.md). Completed change history is in Git/PRs.

## Right now

*Updated 2026-10-19. Engineering checks use fictional data.*

### State

- Silent incomplete AI streams now use the possibly-billed request guard in
  [PR #156](https://github.com/UtkuDenizAltiok/jobcu/pull/156). All **2,199 offline tests**
  pass; eight regressions reproduce the earlier automatic repetition. Exact PR head
  `5910dfd` passed Mac/Windows/privacy CI `39166290234` and merged as `a0f8161`.
  Exact-main CI `39166844812` passed at that merge. The integrated review below
  continues. This establishes the software path, not a historical upstream outage cause.

- Source workplace metadata and richer-description preservation are merged in
  [PR #157](https://github.com/UtkuDenizAltiok/jobcu/pull/157), with **2,208 offline tests**
  passing. Exact head `9eed2ba` passed Mac/Windows/privacy CI `39167102066`; merge `7fae5ed`
  passed exact-main CI `39167726713`. Saved evidence replay and actual usage receipts
  stay private. Source and monthly limits are unchanged.

- Optional JSearch integration is merged in
  [PR #155](https://github.com/UtkuDenizAltiok/jobcu/pull/155): **2,191 offline tests**
  pass, extending the 2,115-test baseline. Exact PR head `6dd60fa` passed Mac/Windows/privacy
  CI `39158878068`. The
  [dated assessment and controls](SOURCES.md#jsearch-assessment--2026-10-18) govern the direct
  Free adapter, explicit opt-in and shared page/detail ceilings. Existing feeds, scores,
  provider/model/effort, owner data and limits are preserved. No account, purchase, live API
  comparison or new job search was started in that initial implementation; useful added
  coverage and net savings remain unmeasured. Its initial deployment receipt is indexed
  privately. Current configuration can have changed since then; do not restore historical
  settings from an adoption receipt. Verify exact merge/main CI rather than inferring it from PR
  checks. Research PR #154 is merged as `511aa02`; its main CI `39154798101` passed.

- Workplace-scoped city research and complete journey alternatives are implemented in
  [PR #152](https://github.com/UtkuDenizAltiok/jobcu/pull/152): **2,115 offline tests** pass.
  Facts follow fuller workplace evidence, shared completed checks survive saved recovery,
  further eligible cities are measured when nearer ones fail, and smaller batches can use
  remaining route allowance. Decimal population cutoffs preserve exact boundaries. Exact
  PR head `0a5c3b1` and main merge `94f5152` passed Mac/Windows/privacy CI `39113149122` and
  `39113542857`. Guarded saved application and deployed-build readback are complete; their
  receipts are indexed privately. No limit/model/effort changes.

- Prepared reference evidence is isolated by country and page budget in
  [PR #151](https://github.com/UtkuDenizAltiok/jobcu/pull/151): **2,091 offline tests** pass.
  Three regressions first reproduce otherwise usable references being discarded. Actual
  PR/main CI and deployment receipts are indexed privately; inspect their exact heads.


- City-source verification and connection/cost safeguards are completed in
  [PR #150](https://github.com/UtkuDenizAltiok/jobcu/pull/150): **2,088 offline tests** pass.
  Reviewed geographic identifiers prevent city/county substitution before paid comparisons;
  complete groups and receipts survive later failures. Stateless event streams retain the
  selected model/effort; ambiguously charged requests stop automatic repetition. Real bounded
  source/journey checks and preserved-data application are recorded privately. These establish
  the tested paths, not universal availability, full city coverage or historical invoice causes.
  Exact main CI and deployment receipts are in the private index; verify their actual heads.


- Shared requirement-evidence replacement is repaired in
  [PR #149](https://github.com/UtkuDenizAltiok/jobcu/pull/149): **1,978 offline tests** pass.
  Eighteen regressions first reproduced unsupported replies overwriting grounded requirements
  in both focused recovery and online-ad updates. Failed replacements retain the earlier
  clause and score restriction, with the latest verification failure visible; supported later
  evidence still resolves it. Final publication state is the PR's actual head and CI, with
  exact receipts retained in the private recovery index.
- Explicit saved-evidence recovery and verified exact-original facts are merged in
  [PR #148](https://github.com/UtkuDenizAltiok/jobcu/pull/148): **1,960 offline tests** pass.
  Complete checks are reused; incomplete attempts are retryable only through explicit recovery.
  Requirement comparisons obey the location gate and preserve central-skill uncertainty.
  Verified old/closed facts have separate storage, source/undo controls and no paid admission.
  Original records, owner marks and snapshots survive. Exact source CI receipts are below.
- Location eligibility before paid scoring is merged in
  [PR #144](https://github.com/UtkuDenizAltiok/jobcu/pull/144): **1,889 offline tests** pass.
  PR head `aa4103c` and main `d37bd0f` passed exact Mac/Windows/privacy CI `39042964831` and
  `39043329386`; main/locked dependencies are synchronized. Pending jobs stay available
  without scoring; missing-workplace findings are reused and saved assessments stay intact.
- Duplicate/history, matched date-reader recovery and the dated BA source-permission hold are
  merged in [PR #145](https://github.com/UtkuDenizAltiok/jobcu/pull/145):
  **1,913 offline tests** pass. PR head `58c8b90` and main `e2f40a5` passed exact
  Mac/Windows/privacy CI `39045657826` and `39046632701`; main/locked dependencies synchronized.
  Ten targeted regressions reproduce the old duplicate/missed-date behavior before the repairs.
  Confirmed historical copy links preserve keys, rows, snapshots and raw marks; distinct native
  employer requisitions remain separate. Confirmed saved-evidence alias repair is applied;
  original tables, marks, keys and snapshots were verified unchanged, with recovery outside Git.
  Specialist-role reassessment and workplace-conflict handling are merged in
  [PR #146](https://github.com/UtkuDenizAltiok/jobcu/pull/146): **1,938 offline tests** pass,
  plus Ruff/privacy/docs/JS/whitespace checks. Exact PR/main CI receipts are recorded below.
  Six regressions reproduce the earlier overly strong core-match rating or unwanted scoring
  on conflicting workplaces. These offline checks do not prove a correct live assessment or
  invoice savings. No new search, paid AI/Maps test, model change or limit change was made.

- Atomic web-reservation accounting is merged in
  [PR #141](https://github.com/UtkuDenizAltiok/jobcu/pull/141): **1,878 offline tests** pass.
  Its regression first reproduced false deferral during receipt writing, then verified all
  allowed work finishes. PR head `f479f39` and main merge `25e89b6` passed exact-head
  Mac/Windows/privacy CI `38969270061` and `38969989627`; main/locked dependencies are
  synchronized. Publication is complete; do not repeat unchanged checks.
- Successful receipt admission and spending-limit clarity are merged in
  [PR #140](https://github.com/UtkuDenizAltiok/jobcu/pull/140), with **1,877 offline tests**
  passing. PR head `d22b4b7` and main merge `66256fd` passed exact-head Mac/Windows/privacy
  CI `38968135336` and `38968706265`; primary main/locked dependencies are synchronized.
- Coordinated connection recovery is merged in
  [PR #139](https://github.com/UtkuDenizAltiok/jobcu/pull/139), with **1,873 offline tests**
  passing. PR head `5666c13` and main merge `973e8d8` passed exact-head Mac/Windows/privacy
  CI `38966766470` and `38967197096`; main/locked dependencies are synchronized.
- Exact-run review's safe job-type/research-admission fixes and request-kind diagnostics are
  merged in [PR #138](https://github.com/UtkuDenizAltiok/jobcu/pull/138), with **1,864 local
  tests passing**. PR head `66a2d4e` and main merge `4b71cdc` passed exact-head Mac/Windows/privacy
  CI `38965550282` and `38966116991`; main/locked dependencies are synchronized. PR #136's
  unchanged baseline was 1,857 tests; its merged head `7a708a6` passed Mac/Windows/privacy
  CI `38944559503`. The native transport is superseded by PR #150 below; broader recovery
  remains limited by the specific evidence dependencies recorded there.
- Location admission, explicit screening uncertainty and the UK sponsorship deduction are
  tracked in [PR #135](https://github.com/UtkuDenizAltiok/jobcu/pull/135). Final local suite:
  **1,833 passing tests**. These checks use fictional data; real missing place evidence stays
  unresolved. Read the PR and private checkpoint for exact publication heads and CI receipts.
- Saved-evidence recovery, citation provenance, requirement-quote and allowance repairs are in
  merged [PR #133](https://github.com/UtkuDenizAltiok/jobcu/pull/133), extending
  [PR #131](https://github.com/UtkuDenizAltiok/jobcu/pull/131). Final PR head `40f5d02` passed
  CI `38852360275`; source merge `e082122` passed exact-main CI `38852830982`, on Mac,
  Windows and privacy. Final local suite: **1,805 passing tests**, with one existing dependency
  deprecation warning. Main and locked dependencies are synchronized. The current source checks are listed above;
  these older receipts establish only their own source heads.
- Disposable private scratch and fictional preview data are removed. The prior capture is
  complete; the exact-run observer has finished and keeps evidence outside Git. No reset,
  new key or model choice is required.
- Saved documents, queries, searches, ratings, marks, settings, keys and authorization are
  preserved. Detailed reviews, complete diagnostic answers, usage and exact publication
  receipts stay outside Git. Private `assistant-review-checkpoint.json` is the recovery index;
  read standing authorization/revocations before following it. Historical evidence remains
  available, but stale completed work must not become a new active goal.
- Two authorized fictional native-generation requests completed without retries. Their usage
  is in the monthly ledger; disposable key/settings/database scratch is removed. This small
  pair did **not** reproduce the saved longer research-path interruption or justify a provider,
  reasoning or network change. Existing API authority is recorded privately; do not ask for
  the same authorization again or repeat unchanged short passing requests.
- This handover replaces the accumulated completed-work ledger and conflicting historical
  app-state notes. Durable decisions, source evidence, guides, licence and Git history remain.

### Current behavior to preserve

| Area | Current record |
|---|---|
| AI errors, reasoning and complete answers | [Narrow reasoning recovery](ENGINEERING.md#reasoning-preserving-request-recovery--2026-10-15) preserves chosen effort on unrelated errors; [billing/Stop recovery](ENGINEERING.md#ai-billing-refusals-stop-and-incomplete-usage--2026-10-12) distinguishes refusals, waits and unknown usage. |
| Bounded research, quotes and money estimates | [Current repairs](ENGINEERING.md#bounded-reference-research-and-priced-usage--2026-10-15) retain candidates/completed groups, bound repeated failures, validate ordinary list quotes and price cache/search usage. These offline checks do not prove live recovery or a complete bill. |
| Original ads and discovery | [Separate ad sections](ENGINEERING.md#original-ad-section-recovery--2026-10-15) reach matching/scoring; [discovery recovery](ENGINEERING.md#employer-discovery-recovery-and-service-choices--2026-10-10) preserves successful countries/employers and retries incomplete ones. Scoped source holds remain. |
| Reference cities and travel | [Finite city evidence](ENGINEERING.md#finite-reference-evidence-and-source-recovery--2026-10-15) gates eligible living/reference cities before travel. [Wednesday timing and reuse](ENGINEERING.md#original-evidence-and-repeated-requests--2026-10-12) retain evidence identity and service-specific storage limits. |
| Scores, duplicates and links | [Task focus/confidence](ENGINEERING.md#task-focus-and-scoring-confidence--2026-10-14) and [duplicate/reference boundaries](ENGINEERING.md#duplicate-boundaries-and-reference-eligibility--2026-10-15) preserve owner score limits, independent vacancy identity and supported originals. Required aggregator routes remain available. |
| Unchanged setup | [Exact setup reuse](ENGINEERING.md#search-preparation-reuse-and-connection-clarity--2026-10-14) covers documents, raw box text, model/host/controls and prompt identity; editing even one letter invalidates relevant reuse. Fresh facts, jobs and scores remain separate. |

### In progress

**Active: integrated search quality, reliability and cost review — 2026-10-18.**

The owner authorised one continuing task in this chat for eight hours, ending
2026-10-19 07:50 Europe/Istanbul or on his return/stop. Analyse the actual intended workflow
and current saved evidence; research JSearch's current contract and the wider AI API market;
integrate confirmed improvements across collection, originals/freshness, deduplication,
location evidence/admission, scoring, explanations, connection recovery and speed. Preserve
recall, medium effort, data, marks, history, licensing and all existing service/monthly limits.
Choose and prepare a justified cheaper provider without claiming unmeasured equivalence.

Branch: `codex/reference-csv-scope`, base `eda1c6e`. The previous JSearch step and its
exact-main Mac/Windows/privacy CI `39159332622` are complete. No unexplained local work.
One same-chat heartbeat continues this authorised scope; no separate chat or project task.
Across all continuations together, ceilings are EUR1.20 total estimated paid API usage,
200 Google Maps route elements and 20 JSearch reserved credits, further constrained by lower
existing limits. The private packet ledger owns dispatch reservations and receipts; never
restart that allowance on a new turn. No new account, purchase, message in the owner's name,
unbounded hosted-search experiment or broad paid job search is authorised. A service failure,
missing usage or unenforceable cost bound closes paid dispatch; continue useful offline and
public-source work without hiding missing evidence. Necessary private review stays outside Git.

Steps: recover private evidence/authorisation and freeze the review packet; establish the
offline baseline and current source/provider contracts; prioritise confirmed root causes;
implement and verify coherent general repairs; perform only bounded useful live checks;
publish with exact-head Mac/Windows/privacy CI and merge commits. Record exact remaining
dependencies and a fresh-chat handover before the deadline. The 2,191-test baseline passes.
Private evidence, the
working copy, aggregate budget and source-check script are indexed under private
`assistant-reviews/2026-10-18-integrated-review/`; check that ledger before every continuation.
A bounded JSearch-only comparison is captured privately; no AI or Maps dispatch has been made.
The first three coherent repairs are merged in PRs #156/#157/#158. PR #158 head `5512a40`
passed Mac/Windows/privacy CI `39168267567`; merge `e3d49a4` passed exact-main CI
`39168641212`. All 2,230 offline tests pass. Usable complete employer-original text now wins
over longer secondary copies; incomplete/empty originals still yield to complete evidence.

PR #159 head `4d02448` passed exact Mac/Windows/privacy CI `39172214147`, then merged as
`1478fa2`. Exact-main CI `39172539288` passed all three checks.
All 2,240 local offline tests pass. Research failures with observed tools and incomplete usage
now stop automatic repetition on that research path, retaining one lower-bound receipt.

PR #160 head `10582c0` passed exact Mac/Windows/privacy CI `39172881920`, then merged as
`cecf409`. Exact-main CI `39173362803` passed all three checks. All 2,262 local offline tests pass.
Responses research now sends the documented tool ceiling and rejects unfinished/refused
answers; native/custom structured errors retain receipts, including truncation repairs.

PR #161 records the dated market refresh, readable provider terms and independent official
reference-data leads. Exact PR head `6f3b2f3` passed CI `39173723994` and merged as `eda1c6e`;
exact-main CI `39189394698` passed all three checks. No paired provider
quality result or new city verdict is established.

The current step repairs complete CSV reference tables being discarded by the AI input bound.
Explicit reviewed row/column selection keeps every matching row, validates the whole table
and preserves existing download/context/geographic/quote limits. Four regressions first
reproduced the failure; all **2,289 offline tests** now pass, including invalid/freshness and
fictional engineering/nursing/teaching cases. Ruff/privacy/whitespace and the complete diff
review pass. Exact next action: publish, require exact-head Mac/Windows/privacy CI, merge
commit, sync main and verify its exact-head CI. The private checkpoint names the final
municipal table, unresolved classification and independent permitted UK data route. Recheck
access/geography and validate counts before adopting facts; do not bypass a blocked download
or treat constituency totals as city totals. Preserve the shared budget and current medium
configuration until no-regression gates are met.

**Parked: comparable city-election evidence within the retained owner review.**

The automatic flow repair in PR #152 is complete in this merge. Full-ad workplaces now select
the finite living-city research scope. Shared sourced facts and completed routes survive
recovery, alternative cities continue in small rounds, and an oversized matrix cannot block
a later smaller matrix within the same allowance. Fractional population cutoffs round upward
without binary-float boundary errors. The final local suite has **2,115 passing tests**,
plus Ruff/privacy/whitespace and the existing documentation checks; one existing dependency
warning. Exact PR head `0a5c3b1` and main merge `94f5152` passed Mac/Windows/privacy CI
`39113149122` and `39113542857`. The bounded real verification, confirmed saved-result
application and deployed-build readback are complete. All paid packets are closed; preserve
their private receipts and never rerun their scripts. Raw assessments, marks, history, other
saved results and settings were independently checked unchanged.

**Exact next action:** read authorization and `assistant-review-checkpoint.json` before private
recovery. No route packet, application or deployment remains open. Follow the retained source
dependency below: obtain independent party-classification evidence for the overlapping
comparison or comparable whole-city election results for the unresolved countries. Validate
those facts before further journeys or admission; reuse completed evidence. The repaired
automation does not establish those factual comparisons. Shipped population observation dates
are unchanged. No new search, account change, larger monthly limit or reset is authorized.

The preceding coherent step is complete; its receipts and remaining evidence dependency follow.

The country-source integration in PR #151 is complete in this merge. Three fictional
regressions first reproduced the global page-limit and mixed-country failures. The final
local suite has **2,091 passing tests**, plus Ruff/privacy/docs/JS/whitespace; one existing
dependency warning. Exact PR head `873e97f` passed Mac/Windows/privacy CI `39073928526`.
Reference comparisons now group by country with up to 16 relevant pages per batch and the
unchanged total-text bound. Additional sources or an overloaded batch do not discard healthy
countries. No paid request or new search was used for this integration repair. Deployment,
source-selection readback and actual main CI receipts are in the private recovery index.

The coherent software/data step in PR #150 is complete in this merge: **2,088 offline tests**
pass, plus Ruff/privacy/docs/JS/whitespace; one existing dependency warning. Exact PR head
`dd23de4` passed Mac/Windows/privacy CI `39072837766`; its merge `46bb731` passed
exact-main CI `39073187583`. The source selection, event-stream,
ambiguous-charge, complete-receipt and precise-uncertainty repairs are adopted. Independently
reviewed city evidence and bounded Maps checks are applied to the same saved search, with
free geometry settled and cards refreshed without additional paid scoring. Raw assessments,
marks, identities, other settings and history were verified preserved. The rollback copy and
exact private receipts are indexed by `assistant-review-checkpoint.json`.

No implementation, paid packet or new search remains open for this coherent step. Verify
actual merge/main CI and app build from Git/private receipts; a PR pass alone is not main CI.
The older PR #137 candidate is superseded by the tested portions in PR #150. PR #149 and
previous original-ad applications are complete and must not be repeated.

**Dependency:** a close category comparison still overlaps because the available classification
evidence does not yet settle every small/named party; other countries still need comparable
whole-city election evidence. Unmeasured/unchecked alternatives also remain explicit. Neither
a county result nor an AfD-only shortcut can settle the broader requested comparison.
The exact historical disconnecting component and original-run invoice allocation remain
unproven; successful later packets and daily totals do not identify those causes.

**Exact next action within the retained review scope:** after reading authorization and the
private checkpoint, obtain independent classification evidence for its explicitly listed
unresolved comparisons, or exact comparable city results for the still-unchecked countries.
Validate that evidence before using it for journeys or admission. Reuse completed facts/routes;
do not repeat paid requests, rescore blocked jobs or select an unrelated backlog task. Further
paid verification requires a new bounded packet; all previous packets are closed. Current
account caps, source evidence and usage reconciliation remain private.

The earlier whole-pipeline review also has these **parked dependencies**; do not resume them
without evidence and authority relevant to the active task:

1. **Provider comparison.** A direct challenger key entered only in Jobcu and a bounded
   paired-comparison budget remain dependencies of the separate proposal, not of ordinary
   use. [Current decision and counterevidence](ENGINEERING.md#quality-first-api-and-electronics-coverage-decision--2026-10-10)
   select one comparison hypothesis; the coding Token Plan excludes this app. Exact next
   action once its account/budget/rights gates are met: refresh the frozen fictional packet
   against current scoring policy, then run the first paired five-ad batch with complete
   answers and full usage. Any observed regression blocks adoption; missing evidence is
   not equivalence. Keep the working configuration meanwhile.
2. **Opaque Adzuna destinations.** Independently collected matching employer originals are
   already preferred. Automatic replacement/probing of the supplied advertiser route needs
   Adzuna's explicit permission and a permitted interface. Exact next action only after that
   permission: verify destination, retention/attribution and request rules before implementing
   bounded handling. No login, blocked-host probe or bypass is authorized.
3. **Go hosted use/tools.** Previously authorized support questions are already sent; retain
   their private receipts and await clarification. No duplicate message, purchase or provider
   switch is pending. Intended use, complete fees, native controls and independent fit outcomes
   must be verified before adoption; shared limits alone do not reject a provider.

### Waiting on the owner

No owner response is required during the integrated review. Its current bounded allowance
is recorded above and in the private shared ledger; older verification packets remain closed
and must not be replayed. No account change, new job search or provider/model switch is pending.
Preserve existing local/provider limits. A local estimate is not an invoice or
provider cap. Service restoration does not retroactively complete missing search checks.
A fresh chat follows [Start](PROMPTS.md#start-a-session) and recovers In progress before new work.

### Verify before relying on

- Live provider availability, route accuracy, matching quality, net savings and whole-market
  recall are not established by offline tests or a few successful native-generation requests.
- Missing original ads/reference facts, incomplete billed usage and an independent dated
  benchmark limit historical quality/coverage and invoice claims. Optional ratings do not
  automatically train AI. Retain owner/legacy ratings and the prior blinded review.
- Routes use sampled city-edge/centre destinations. Unchecked alternatives and service errors
  must not become proven travel failures. Never persist Google route durations as unrestricted
  cross-search memory; AI estimates have their separate identity/expiry rules.
- Posting-date audits, region/multiple-location exclusions and uncertain negative travel
  decisions still need targeted evidence in an authorized development task. The remaining
  freshness concern includes metadata skipped when another copy already supplies full text.
- When feed and ad workplaces disagree, the exact vacancy's permitted original is needed
  before choosing a location. Reconciliation must preserve multiple-site alternatives and
  recheck filters/travel; do not treat an arbitrary mentioned town as the workplace.

### Known limitations

- Stop interrupts retry/queued waits; an already running synchronous provider request can
  still take time to return. Do not describe this as complete in-flight cancellation.
- Opaque final destinations and registration/access eligibility remain unknown without
  permitted original evidence. A failed final save can lose the unsaved visible results;
  previously saved searches remain. Token estimates may omit fees/discounts and are not invoices.
- A fresh Windows beginner install/upload/search walkthrough remains untested; launcher CI
  covers a narrower behavior. No setup or owner-app restart is needed merely to review data.

### Next tasks

Candidates only for a new owner-directed development task; not instructions during Start/End:

1. Reproduce uncertain negative travel decisions and region/multiple-location exclusions,
   preserving unknowns and source permissions before filtering changes.
2. Audit original posting dates and skipped metadata; recover permitted missing originals,
   independent top-card/title-screen judgements and a dated coverage benchmark.
3. Measure unique relevant jobs, better evidence and backup value of permitted sources in
   AGENTS' country/profession order before adding/removing methods. Prioritize electronics
   employer originals; remote-only expansion remains low priority. [Source leads](SOURCES.md#electronics-employer-and-specialist-coverage--2026-10-10)
   and [Jobicy](SOURCES.md#employer-feeds-and-remote-candidates--2026-10-10) require current rights,
   freshness and contribution evidence; reachable/internal endpoints grant no collection right.
4. Investigate repeated/slow work from saved phases and failures; any different paid test
   needs a bounded scope within existing authority and limits. Complete the Windows walkthrough
   when a task calls for it.
