# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions/implementation: [ENGINEERING](ENGINEERING.md); dated
contracts/access facts: [SOURCES](SOURCES.md). Detailed history lives in Git and PRs.

## Right now

*Updated 2026-10-10. Engineering checks use fictional data.*

### State

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
- The [current Go reassessment](ENGINEERING.md#go-feasibility-and-interruption-continuity--2026-10-09)
  keeps Go as a viable candidate, with GPT-6 Luna first and MiMo Pro as an interpretation
  challenger. Preserve working Gemini medium meanwhile. Several candidates support documents,
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
- Last observed owner app state at the final check: closed (8765); it was running earlier in
  the task. Neither state was changed by the assistant. The isolated fictional preview at
  8799 is stopped, its tab closed and disposable data removed. Authorized saved evidence and
  checkpoints stay private; owner data/settings are preserved. Recheck actual app state once
  on resume and preserve the owner's choice.

### In progress

**No remaining implementation.** The completed-search review and online-check improvement are
implemented and locally verified. Private judgements preceded score reveal, including every top
card; uncertain cases remain unknown. Judgements stay in the private packet; the bounded in-app
sample had no matching entries for supported new labels, so existing ratings remain unchanged.
No newer unfinished attempt was found. No provider/source call, paid test,
new search, account, model or app-limit change was made. Disposable private scratch was removed;
needed evidence/checkpoint stay private. The owner app's observed closed state was preserved.

Local verification: **1,145 tests**, Ruff/privacy/whitespace, document links, complete diff review
and isolated startup passed; its preview/data were removed. The existing dependency warning
remains. Fictional before/after transport results are in ENGINEERING, not live speed/quality proof.

Publication checkpoint: [PR #101](https://github.com/UtkuDenizAltiok/jobcu/pull/101), branch
`codex/review-online-checks`, base `9d27d7a`. On interruption, the exact next action is to check
the PR's actual final head and required Mac/Windows/privacy CI, finish merge-commit publication
if outstanding, synchronize main and verify its exact-head CI. Once those pass, this goal is
complete; Start waits for the owner. Missing originals, researched conditions, independent
coverage evidence and live transport outcomes are checkpointed dependencies for a later task;
do not restart a search or provider comparison to fill them without its required authority.

### Verify before relying on

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
5. Reproduce Ashby secondary-country metadata handling, then compare new/existing methods and
   structured public APIs for unique useful jobs, evidence, country/profession gaps and
   reliability. Improve/add/replace/remove based on
   verified terms and contribution. Private/internal APIs need documented authority.
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
