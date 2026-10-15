# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); implementation/decisions: [ENGINEERING](ENGINEERING.md);
source permissions and dated facts: [SOURCES](SOURCES.md). Completed change history is in Git/PRs.

## Right now

*Updated 2026-10-15. Engineering checks use fictional data.*

### State

- All product repairs from this session are merged. Application code/tests/dependencies are
  unchanged from `d988466` ([PR #128](https://github.com/UtkuDenizAltiok/jobcu/pull/128)); its
  exact-main CI `38715862731` passed Mac, Windows and privacy. The final local source baseline
  is **1,732 passing tests**, with one existing dependency deprecation warning. Current
  documentation-only session-close cleanup is merged in
  [PR #129](https://github.com/UtkuDenizAltiok/jobcu/pull/129), with exact-main CI
  `38718653775` passing Mac, Windows and privacy on `f074f7c`. Do not run another local full
  suite for unchanged code merely to prepare a chat.
- Owner app **8765** and assistant preview **8799** were both closed at session close; preserve
  the owner's subsequent choice. No service is left running by the assistant. The next normal
  owner launch loads the repairs. No reset, new key or model choice is required.
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
| Original ads and discovery | [Separate ad sections](ENGINEERING.md#original-ad-section-recovery--2026-10-15) reach matching/scoring; [discovery recovery](ENGINEERING.md#employer-discovery-recovery-and-service-choices--2026-10-10) preserves successful countries/employers and retries incomplete ones. Scoped source holds remain. |
| Reference cities and travel | [Finite city evidence](ENGINEERING.md#finite-reference-evidence-and-source-recovery--2026-10-15) gates eligible living/reference cities before travel. [Wednesday timing and reuse](ENGINEERING.md#original-evidence-and-repeated-requests--2026-10-12) retain evidence identity and service-specific storage limits. |
| Scores, duplicates and links | [Task focus/confidence](ENGINEERING.md#task-focus-and-scoring-confidence--2026-10-14) and [duplicate/reference boundaries](ENGINEERING.md#duplicate-boundaries-and-reference-eligibility--2026-10-15) preserve owner score limits, independent vacancy identity and supported originals. Required aggregator routes remain available. |
| Unchanged setup | [Exact setup reuse](ENGINEERING.md#search-preparation-reuse-and-connection-clarity--2026-10-14) covers documents, raw box text, model/host/controls and prompt identity; editing even one letter invalidates relevant reuse. Fresh facts, jobs and scores remain separate. |

### In progress

**No active goal or unfinished product implementation, local checks or session-close
housekeeping.** The previous handover, private pointer reconciliation and disposable
validation-cache cleanup are complete; publication is verified above. Do not reopen completed
repairs or start backlog work during Start.

The earlier whole-pipeline review has only these **parked dependencies**:

1. **Long research-request interruptions.** Saved failures ended before response headers;
   their provider/network cause is unproved. The short generation diagnostic is complete.
   Exact next action if this diagnostic is resumed: verify hosted-search display/suggestions,
   retention/reuse and bounded full token/query charges, then freeze a fictional reproduction
   of that request class through `AIClient` on isolated scratch. Respect the existing private
   authority and remaining monthly/request limits; no new call is scheduled by this handover.
2. **Provider comparison.** A direct challenger key entered only in Jobcu and a bounded
   paired-comparison budget remain dependencies of the separate proposal, not of ordinary
   use. [Current decision and counterevidence](ENGINEERING.md#quality-first-api-and-electronics-coverage-decision--2026-10-10)
   select one comparison hypothesis; the coding Token Plan excludes this app. Exact next
   action once its account/budget/rights gates are met: refresh the frozen fictional packet
   against current scoring policy, then run the first paired five-ad batch with complete
   answers and full usage. Any observed regression blocks adoption; missing evidence is
   not equivalence. Keep the working configuration meanwhile.
3. **Opaque Adzuna destinations.** Independently collected matching employer originals are
   already preferred. Automatic replacement/probing of the supplied advertiser route needs
   Adzuna's explicit permission and a permitted interface. Exact next action only after that
   permission: verify destination, retention/attribution and request rules before implementing
   bounded handling. No login, blocked-host probe or bypass is authorized.
4. **Go hosted use/tools.** Previously authorized support questions are already sent; retain
   their private receipts and await clarification. No duplicate message, purchase or provider
   switch is pending. Intended use, complete fees, native controls and independent fit outcomes
   must be verified before adoption; shared limits alone do not reject a provider.

### Waiting on the owner

Run the next search on demand with **24 hours** and existing frequency/service limits when
ready, then bring its completed results to the next chat. No reset or replacement key is
needed. The assistant has no scheduled search, reminder or further paid work from this End.

1. Open a fresh **local chat in this repository's project** and use
   [Start](PROMPTS.md#start-a-session). It verifies/reconciles this handover and waits;
   it does not begin a private review, new search, paid call or backlog task.
2. After the owner's next search finishes, use [Review](PROMPTS.md#review-a-search).
   Follow [CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search) on authorized isolated
   evidence: find the latest completed attempt, flag a newer unfinished attempt and reuse
   only unchanged saved judgements. Do not repeat the previous completed review as preparation.
3. Check full ads/documents/criteria independently before scores, including every top card
   and the balanced 30–50-ad sample. Investigate new warnings, missing evidence, duplicate
   identity, exclusions, travel, ranking and explanations across the pipeline. Use recorded
   run boundaries and separate corrections, retries, answer waits and cumulative usage.
4. Select and finish the strongest supported improvement with fictional regressions and
   required publication checks. Counts alone prove neither accuracy nor coverage; leave
   missing evidence unknown and keep detailed real evidence outside Git. No extra search or
   paid experiment is granted by Start, End or the ordinary Review prompt.

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
