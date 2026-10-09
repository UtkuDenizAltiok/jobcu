# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions/implementation: [ENGINEERING](ENGINEERING.md); dated
contracts/access facts: [SOURCES](SOURCES.md). Detailed history lives in Git and PRs.

## Right now

*Updated 2026-10-09. Engineering checks use fictional data.*

### State

- Custom APIs now have Chat Completions, Responses and Messages configuration, explicit
  thinking controls, and an optional separate native online-research provider in
  [PR #95](https://github.com/UtkuDenizAltiok/jobcu/pull/95). Local checks pass; verify its actual
  final head and merged-main CI before relying on publication. The [complete current catalogue assessment](ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09)
  prioritizes GPT-6 Luna, MiMo-V2.6-Pro, DeepSeek V4.1 Flash, Haiku 5.5 and GLM-5.3-Flash.
  The documented catalogue has 32 models despite the landing page's 31. This replaces the
  older shortlist order, not the requirement for independent quality evidence before a switch.
- The owner delegates technical service decisions and is willing to pay for useful APIs.
  The [current recommendation](ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09) is keep
  Gemini medium during a cheaper-main-model comparison, with GPT-6 Luna medium first.
  Compare direct API plus Gemini research before Go-only or Go plus research; Routes quota
  correction is already verified, while post-change live success remains unmeasured.
  This supersedes treating the earlier five-model evaluation shortlist as a selected upgrade
  or asking the owner to choose a model/integration. No matching superiority is claimed.
  Current provider, keys and settings are preserved. The owner explicitly raised the monthly
  total ceiling to EUR30; EUR25 and the initial larger-budget proposal are superseded.
  The earlier EUR10 Maps / EUR15 AI split is not a verified forecast or implemented allocation.
- Go's permitted non-coding use, hosted research entitlement/fees and correct medium/schema/
  protocol behavior need verification. Model equivalents share weighted capacity; advertised
  cached coding-request counts do not establish daily-search capacity. AI Studio prepaid credit
  cannot pay for Maps; actual credit type/expiry remains unchecked. Dated facts are in SOURCES.
  Relevant Maps quota/billing was inspected privately; a targeted daily-quota correction was
  visibly verified. Exact account values/proof stay outside Git. No key, paid/provider test or
  new search was used; the app's monthly allowance, owner settings and EUR30 total stay intact.
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
- Local checks passed: **1,125 tests**, Ruff, privacy, whitespace, document links and complete
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
- The owner app 8765 stays closed. The assistant's isolated fictional Settings preview at 8799
  is stopped, its tab closed and disposable data removed. Authorized saved service evidence/
  forecast and its recovery checkpoint stay
  private; the disposable diagnostic copy is removed. Owner search data/settings are preserved.

### In progress

No unfinished implementation remains for **universal AI configuration/service decision**.
Publication recovery only if [PR #95](https://github.com/UtkuDenizAltiok/jobcu/pull/95) is unmerged
or exact merged-main CI is missing. Branch `codex/universal-ai-service-choice`, base `92df256`;
implementation head `c962116` is committed/pushed, this final handover is a docs-only follow-up.
The complete catalogue, custom formats/controls and separate online research are implemented;
no model switch, paid comparison, purchase, new search or Maps-cap/cache change was performed.

Verified locally: **1,125 tests**, Ruff/privacy/whitespace, JS syntax, complete diff review,
and fictional Settings Save/reload with no console errors. Preview/tab/scratch are cleaned up;
owner app/data/settings remain preserved. Reuse unchanged runtime checks for this handover.
Exact next action if unmerged: commit/push the handover, recover PR #95's actual final head,
require Mac/Windows/privacy CI on that head, merge commit, synchronize main and verify its
exact-head CI. If already merged and verified, this goal is complete and no active goal remains;
clear this conditional entry when updating progress for the next owner task. Do not repeat
private account edits, start a paid comparison or choose backlog work during Start.
Adoption dependencies: Go non-coding permission, independent matching labels and a separately
bounded paid comparison through Jobcu. Main/research format compatibility is now implemented;
no extra full search or owner ratings are needed to prepare that comparison.

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

- Keep the working Gemini medium setup; no Go purchase, replacement key or model choice is
  needed. The relevant Maps account investigation and targeted daily-quota correction are
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
