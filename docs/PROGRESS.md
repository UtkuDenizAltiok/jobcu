# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions and implementation: [ENGINEERING](ENGINEERING.md).
Completed details live in Git and PRs. Private evaluation follows
[CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).

## Right now

*Updated 2026-10-08. Engineering checks use fictional data.*

### State

- Title-screen recovery, vacancy identity, local matching and location-confidence changes
  are merged. Behavior, reasons and measured local limits live in [ENGINEERING](ENGINEERING.md).
  Live recall, accuracy, speed and cost remain unverified.
- [PR #77](https://github.com/UtkuDenizAltiok/jobcu/pull/77) is implemented, tested, pushed
  and merged with a merge commit. Implementation head: `bfafe1e`; merge: `c7a49eb`.
  Source readers share rate-limit/service cooldowns, honor integer/date Retry-After, stop
  waiting on cancellation and recognize blocked hosts before retrying. Progress explains waits.
  Final-head PR and merged-main Mac/Windows/privacy CI passed.
  The Mac checkout was synchronized after merging.
- Local checks passed: **774 tests**, Ruff, privacy and whitespace. The 27 new mocked cases
  compare request ordering, full/cached evidence, concurrent/extended waits, blocked responses
  and retained engineering/nursing/hospitality ads. Dated protocol evidence and measured local
  limits live in [SOURCES](SOURCES.md#job-source-cooldown-protocol) and
  [ENGINEERING](ENGINEERING.md#source-reliability). AI effort/scoring and JavaScript are unchanged.
  Live recall, accuracy, speed and cost remain unverified. Existing deprecation warning remains.
- ZIP copies show manual update steps on startup, with no update request. The installation
  guide remains detailed; the search guide now explains source waits and Stop.
- Saved-evidence review remains dependent on permitted original full ads or later saved
  early-title decisions. Standing authority and the private checkpoint were rechecked;
  detailed evidence and review status remain private. No new search, paid call or job-site
  request started. Disposable private scratch was deleted and ratings were preserved.
- Both app ports are stopped. Owner data, ratings and private authority are preserved;
  only the assistant's private review checkpoint was refreshed.

### In progress

Active goal: recover complete evidence from already-matched ad copies on
`codex/full-ad-recovery`, base `76f405f`. Main and PR/CI/app state are verified; startup checks
passed **774 tests**. The saved private review still needs missing original ads/new title
decisions; recovery inspection used a read-only scratch copy, now deleted. No new search or
paid/provider/job-site call started, and owner data/ratings/authority are preserved.

Shortlist by benefit, evidence, effort and risk:
1. Full-ad recovery: confirmed first-copy-only behavior; high evidence benefit, moderate effort
   and identity/concurrency/budget risk. Select it; verify cache-first and failure fallback
   with fictional electronics, nursing and hospitality searches.
2. Unresolved places: confirmed mismatch with keep-unknown intent; potentially high recall
   benefit, low effort, needs geographic exclusion/matching regressions before implementation.
3. Retry accounting: budget charges precede internal HTTP retries; needs a focused limit audit
   before any claim of correct attempt accounting. No live budget experiment is authorized.

Steps: recheck full-evidence and existing API documentation/permissions; reproduce missed full
ads; reuse valid cached text across copies; try permitted copies in sequence until full text
is found, preserving source serialization, identity, source limits and Stop; document behavior;
run full checks and review; publish, verify final-head Mac/Windows/privacy CI, merge and sync.
Implemented locally: cache-first across matched copies, employer-first fallback, identity and
mutation guards, retained summaries, Stop/source serialization, correction-reader budgets and
pre-scoring objective-fact checks. The original loader failed 18 focused cases. Final local
checks passed **819 tests**, Ruff, privacy, whitespace and an isolated startup self-test; the
diff was reviewed. Self-test stopped and its disposable data was deleted.
Dated public evidence and fictional before/after reader counts are recorded in SOURCES and
ENGINEERING; no live benefit is claimed. Implementation and records are ready for publication;
no merge is claimed by this checkpoint. Recover actual HEAD/PR from Git and GitHub.
Exact next action: push/open the branch PR if absent; verify its exact-head Mac/Windows/privacy
CI, merge with a merge commit, synchronize main, then refresh this handover against actual state.

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

1. Reproduce and improve full-ad fallback among already-matched copies, preserving identity,
   budgets and cached evidence. [Research leads](ENGINEERING.md#research-leads-requiring-their-own-verified-goal)
   also cover unresolved-place rejection, retry accounting and remaining protocol scopes.
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
