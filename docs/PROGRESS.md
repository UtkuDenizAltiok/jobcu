# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); implementation/decisions: [ENGINEERING](ENGINEERING.md);
source permissions and dated facts: [SOURCES](SOURCES.md). Completed change history is in Git/PRs.

## Right now

*Updated 2026-10-18. Engineering checks use fictional data.*

### State

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
  CI `38944559503`. The separate native transport candidate is not adopted; cost-safe complete recovery
  remains unverified.
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

**City/journey and provider connection/cost recovery: final publication/application.**

Branch `codex/location-connection-recovery`, PR #150. Baseline: **1,978 tests** at `bebbf64`,
exact PR/main CI `39064042453` / `39064322926` passed Mac/Windows/privacy. Final local source:
**2,088 tests pass**, plus Ruff/privacy/docs/JS/whitespace; one existing dependency warning.
The earlier source head `401c6be` passed all platforms; the final geographic-scope/diagnostic
head still needs its own exact CI. Do not substitute that earlier pass.

Implemented: stateless native event decoding/receipts, terminal error classification,
provider-neutral suspension after ambiguously charged connection failures, and fresh reviewed
source comparisons before hosted city research. City geographic IDs are checked before paid
comparison and in citations. Complete groups survive later failures; unverified explanations
stay labelled. Medium-effort whole-city comparisons have sufficient initial output space.
The prepared owner update preserves raw assessments, marks, identities, other settings and
history. Real source/arithmetic and Maps receipts, backup and exact application checks are
private. Do not adopt a model-only answer where independent evidence remains inconclusive.

**Exact next action:** require exact final PR Mac/Windows/privacy CI; confirm no active search,
apply the prepared private evidence/card update with its backup and integrity guards, then
merge with a merge commit, synchronize main/locked dependencies, restart the updated app and
verify exact-main CI/health. No more paid calls or new search: all verification packets closed.
Private `checkpoint.json` contains paths and exact commands; never rerun a used packet.

Remaining evidence must stay specific: some category comparisons overlap; other-country city
facts and unmeasured journeys remain unchecked. The exact component closing the original
connection and exact original-run invoice allocation are still unproven. Later successful
connections and daily billing totals do not prove those historical causes. Current account
caps and complete cost reconciliation are recorded privately; no account/limit change is made.
PR #149 is complete; earlier original-ad facts must not be reapplied. The older native PR #137
candidate is superseded only by the tested parts adopted in PR #150.

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

No account change, new search or provider/model switch is pending. All bounded development
verification packets are closed; receipts and specific unresolved evidence are in the private
checkpoint. Preserve existing local/provider limits. A local estimate is not an invoice or
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
