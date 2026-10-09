# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions/implementation: [ENGINEERING](ENGINEERING.md); dated
contracts/access facts: [SOURCES](SOURCES.md). Detailed history lives in Git and PRs.

## Right now

*Updated 2026-10-09. Engineering checks use fictional data.*

### State

- The Maps correction is merged in [PR #90](https://github.com/UtkuDenizAltiok/jobcu/pull/90)
  at `3d8cb30`; exact main Mac/Windows/privacy CI `37914682388` passed.
  Per-route service errors, missing/invalid answers and unchecked alternatives stay uncertain
  rather than proving a travel failure. Valid partial Maps times remain; fallback estimates
  have per-town attribution and only AI values enter AI memory. Explicit no-route results
  remain distinct. Known access/persistent quota refusals stop later requests; limits stay intact.
- Existing condition edits reuse sufficient readings; routing version 3 refreshes old Maps
  entries that could not distinguish errors from no route. Historical result snapshots and
  scoring criteria are preserved. Every AI step still defaults to medium.
- The owner's Maps spending question has a documented
  [recommendation](ENGINEERING.md#maps-spending-proposal--2026-10-09), public price/SKU/control
  evidence and fictional cost scenarios. Retain Google for now; diagnose actual quota/access
  and protect uncertain negative travel evidence before enlarging usage. A proposed EUR10
  Maps allocation inside the existing EUR25 total is pending the owner's decision and account/
  combined-workload checks. No billing, quota, setting, provider or filtering change was made.
  Exact live refusal/account allowance and route/fit quality remain unverified.
- Local checks passed: **1,098 tests**, Ruff, privacy, whitespace, document links and complete
  diff review, plus an isolated startup self-test that stopped and removed its disposable data.
  Fictional cases cover all 30 countries, engineering/teaching/nursing, partial/malformed data,
  Maps/AI attribution, persistence, limits and two full engineering/library search pipelines.
  [Before/after evidence and limits](ENGINEERING.md#partial-route-outcomes--2026-10-09) distinguish
  application correctness from unmeasured live route/fit quality, coverage, cost and latency.
- Public Routes/Ashby/Lever documentation, Maps policy/limits/prices and source contribution
  alternatives were researched; dated facts and hypotheses live in SOURCES. No source was
  added/removed on insufficient evidence. No private review, paid call, new job search or live
  vacancy fetch occurred. Owner data, settings, limits, keys and authorization are untouched.
- [PR #89](https://github.com/UtkuDenizAltiok/jobcu/pull/89) is merged at `786ccf2`; exact main
  Mac/Windows/privacy CI `37907028979` passed. Its session workflow remains current: Start
  prepares/recovers and waits; Review/Deep improvement use the prepared chat; End parks safely.
- Prior app changes are merged: [PR #86](https://github.com/UtkuDenizAltiok/jobcu/pull/86)
  added confirmed resets and optional Settings → Review results; [PR #87](https://github.com/UtkuDenizAltiok/jobcu/pull/87)
  corrected Greenhouse original-date evidence and reader-version cache recovery. Historical
  snapshots keep their original scores/date labels. Reset preserves settings, keys, assistant
  authorization and real usage counters; full reset deletes review evidence/checkpoints.
- App/preview ports had no listeners at recovery and after the isolated self-test. Preserve
  the owner's chosen state. No owner app was started/stopped or private scratch copy created.

### In progress

The **Maps reliability and bounded spending proposal** is complete; only publication remains.
Branch `codex/maps-spending-proposal`, base/known head `3d8cb30`. Recommendations/cost scenarios
are in ENGINEERING; dated contracts/prices are in SOURCES; guides/prompts are updated.
No runtime, billing, quota, owner-setting or account change is included. The proposed EUR10
allocation remains pending; actual account refusal/allowance and combined-workload checks
are dependencies, not a new implementation goal.

Checkpoint before commit: 20 document checks, Ruff, privacy, whitespace, fictional price
arithmetic and complete diff review passed. Code/tests/dependencies are unchanged; prior
1,098-test code verification remains valid. No private result review, cloud access, live
route/provider call, paid test or new search occurred. No app or scratch copy was started.

Exact next action: commit/push these six document files and create/recover the PR
(`gh pr list --state all --head codex/maps-spending-proposal`). Require Mac/Windows/privacy CI
on its exact head, merge with a merge commit, synchronize main and verify its exact-head CI.
If pushed, finish only outstanding publication. If verified merged, this proposal is complete
and **no active goal remains**; Start prepares and waits. No extra PR is needed to insert its
own merge hash. Budget/diagnostic dependencies do not authorize account changes during Start.

### Verify before relying on

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
  account SKU, refused quota, shared allowance, reset alignment and combined AI/Maps forecast.
- Live timing/ranking comparisons need bounded authority/current prices. Spare assistant usage
  grants no private APIs, spending, site logins or new/background searches.
- A fresh Windows installation/upload/search walkthrough remains untested; launcher CI is narrower.

### Waiting on the owner

- Maps proposal: choose whether to allocate up to EUR10/month within the existing EUR25 total.
  This is not an implemented cap or permission to change billing. Diagnose the account issue
  first; a live diagnostic, if necessary, needs separately bounded authority. No new search,
  keys in chat, reset or optional rating homework is required.
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
