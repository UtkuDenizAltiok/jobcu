# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions and implementation: [ENGINEERING](ENGINEERING.md).
Completed details live in Git and PRs. Private evaluation follows
[CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).

## Right now

*Updated 2026-10-08. Engineering checks use fictional data.*

### State

- [PR #79](https://github.com/UtkuDenizAltiok/jobcu/pull/79) is implemented, tested, pushed
  and merged with a merge commit. Implementation head: `7726a51`; merge: `f078539`.
  Final-head PR Mac/Windows/privacy CI passed. The Mac checkout was synchronized after merging.
  Merged-main run `37790261867` also passed Mac/Windows/privacy checks.
- Full-ad loading reuses valid recent text across matched copies, prefers original employer
  readers when live reading is necessary and falls back after incomplete/failed reads.
  Known dates, countries, types, remote status and application routes are checked again before
  scoring. Corrections carry forward reported source requests into the normal reader budget.
  Source serialization, Stop, identities/marks and incomplete-evidence labels are preserved.
- Local checks passed: **819 tests**, Ruff, privacy, whitespace and isolated startup self-test.
  The 45 added fictional cases cover recovered requirements and fresh matching, cache reuse/
  expiry, objective-fact checks, source limits, concurrency and failures. Dated primary evidence
  lives in [SOURCES](SOURCES.md#full-ad-evidence-and-existing-detail-apis); before/after reader
  counts and practical limits live in [ENGINEERING](ENGINEERING.md#fictional-full-ad-recovery-comparison--2026-10-08).
  No live recall, fit, cost or latency improvement is claimed. Existing deprecation warning remains.
- Earlier title-screen recovery, vacancy identity, local matching/location confidence, source
  cooldowns and manual ZIP startup guidance remain merged. AI medium/provider choice,
  scoring rules and JavaScript are unchanged by this goal. Guides remain detailed.
- Saved-evidence review still needs permitted original full ads or later saved early-title
  decisions. Authority and the private checkpoint were rechecked; detailed findings remain
  private. No new search, paid/provider call or vacancy request started. Disposable private
  review data was deleted; only the assistant's private engineering checkpoint was updated.
- Both app ports are stopped. Owner data, ratings, private authority and app state are preserved.

### In progress

Active goal: make Maps quota recovery respect request limits and explain failures accurately,
on `codex/maps-recovery-limits`, base `97713bb`. Startup verified clean main, merged PRs and
final-main Mac/Windows/privacy CI; locked sync and **819 tests** passed. The owner subsequently
closed Jobcu; preserve that choice. Preview 8799 is stopped. Development works with either
owner app state and does not require closing it.

The owner requested review after an on-demand search. Standing private authority/checkpoint
were checked; saved results/logs were inspected on a private SQLite backup outside Git.
Detailed counts, criteria, timings and quota diagnostics remain private. No new search or
provider/Maps/vacancy request was made. Independent top-card labels/original posting-date
provenance still limit quality claims; newly saved early-title evidence is now available.

Shortlist ranked by benefit, evidence, effort, risk and verification:
1. Maps recovery/accounting: confirmed retry loop and budget charged once before multiple
   transport attempts; high reliability/limit benefit, medium effort and retry/evidence risk.
   Select this goal; verify recoverable throttling, persistent quotas, cancellation, budget
   exhaustion and measured/estimated labels without live calls.
2. Original-date provenance: high freshness benefit; some adapters fall back to modification
   dates. Needs source-by-source primary evidence, independent original dates and fictional
   regressions before changing collection. Saved dates alone cannot prove posting freshness.
3. Unresolved-place rejection: high potential recall benefit, low/moderate effort; retain
   proven geographic exclusions and include fictional non-engineering matching cases.

Steps: check primary quota/error/terms guidance; reproduce failures and retry accounting;
distinguish persistent from transient limits; count each attempted matrix's elements; preserve
successful measurements and avoid retrying a confirmed persistent quota again in the same search;
provide clear bounded diagnostics; compare fictional behavior/requests/waits; update guides
and records; review, run full checks, publish, verify exact-head Mac/Windows/privacy CI, merge
with merge commits and synchronize main. Do not lower AI effort, omit candidates or cache
Google travel times across searches. No account/billing changes or paid tests are authorized.

Implemented locally: persistent quota classification, per-attempt element accounting with
atomic spending, allowance preflight, preserved cached measurements, shared measurement-round
state, single wait notice/current-step timing and explicit collected-ad wording. The original
implementation failed 12 focused cases. Final local checks passed **855 tests**, Ruff, privacy,
whitespace and an isolated startup self-test. The full diff was reviewed; no failed check remains.
Fictional before/after comparisons and primary evidence are recorded in ENGINEERING/SOURCES.
No live quality, cost or end-to-end speed gain is claimed. Implementation is ready for publication;
no merge is claimed by this checkpoint. Recover actual branch HEAD/PR from Git and GitHub.
Exact next action: push/open the branch PR if absent, verify exact-head Mac/Windows/privacy CI,
merge with a merge commit, synchronize main and verify merged-main CI before final handover.
Private review evidence and updated status were saved outside Git; its scratch copy was deleted.
Owner data, ratings and private authority are preserved. Both app ports are stopped as chosen
by the owner. No paid test, provider/Maps/vacancy call or new search was made by this session.

### Verify before relying on

- Ranking/title screening: independent full-ad judgement, every top-10 label and new early
  rejection/unknown evidence remain unfinished; old counts cannot reconstruct discarded titles.
- Coverage: an independent date-verified 15–25-job benchmark remains, in AGENTS' country order.
- Interpretation/location: live quality, timing and repeated-search savings remain unmeasured;
  Maps journeys and faster districts need live validation.
- Beginner installation and fresh Windows install/upload/search walkthroughs remain untested.

### Waiting on the owner

- No new keys, documents or settings are required; enter private inputs only in Jobcu.
- Search on demand: double-click **Start Jobcu.command**, choose **24 hours**, then search
  when ready. After completion, use [Review](PROMPTS.md#review-a-search).
- With spare assistant usage/time, copy [Deep improvement](PROMPTS.md#deep-improvement).
  Before closing a chat, use [End](PROMPTS.md#end-a-session), wait for the saved confirmation,
  then use [Start](PROMPTS.md#start-a-session) in a fresh local chat.
- Report an unusable route with **Application link problem**; **Excluded links** can undo it.
  This uses no AI allowance. Searches run on demand without assistant supervision.

### Next tasks

1. Reproduce unresolved-place rejection and compare it with the keep-unknown intent; retain
   proven geographic exclusions, all countries/professions and source limits. This is the next
   free lead, not an implemented fix. [Research leads](ENGINEERING.md#research-leads-requiring-their-own-verified-goal)
   also cover place evidence revealed after full-ad reading, retry accounting and protocol scopes.
2. Independently judge full evidence/early titles and trace a date-verified coverage sample
   within private authority. Missing originals/new saved decisions remain dependencies.
3. Compare the next authorized search's interpretation, ranking and original elapsed time;
   source expansion/vocabulary changes need independent recall evidence and current permission.
4. Fresh Windows installation/upload/search walkthrough remains later free engineering work;
   launcher CI is not a beginner's installation or a live search validation.

### Known limitations

- Counts do not measure market recall; scores are not hiring odds. Summaries, unknown dates
  and unchecked conditions are incomplete evidence. Historical snapshots keep original labels.
- Opaque application destinations and automatic final-host checks are unverified. A changed
  redirect needs a new report; undo restores retained links, while an omitted vacancy may need
  the next on-demand search. An alternative link does not prove registration access.
- Maps edge/centre samples are approximate. Correction timings cover the latest correction;
  usage accumulates. Token estimates can omit fees/discounts and are not invoices.
- A failed final save can lose visible results on closing; earlier saved searches remain.
