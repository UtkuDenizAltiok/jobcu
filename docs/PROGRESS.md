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
- ZIP copies now show manual update steps on startup; the reminder makes no update request.
  [PR #75](https://github.com/UtkuDenizAltiok/jobcu/pull/75) is implemented, tested, pushed
  and merged with a merge commit. Implementation head: `cb234f1`; merge: `4ecf8ce`.
  The Mac checkout was synchronized after merging. Final-head PR and merged-main
  Mac/Windows/privacy CI passed.
- Local checks passed: **747 tests**, Ruff, privacy, Bash syntax and whitespace. The six new
  launcher cases cover ZIP copies, Git directories/worktree files and self-tests with local
  helpers. The installation guide explains the reminder. AI instructions and JavaScript
  are unchanged; live search quality remains unverified.
  Existing dependency deprecation warning remains.
- Saved-evidence review remains dependent on permitted original full ads or later saved
  early-title decisions. Standing authority and the private checkpoint were rechecked;
  detailed evidence and review status remain private. No new search, paid call or job-site
  request started. Disposable private scratch was deleted and ratings were preserved.
- Both app ports are stopped. Owner data, ratings and private authority are preserved;
  only the assistant's private review checkpoint was refreshed.

### In progress

Active goal: honor job-source cooldowns across parallel readers while keeping Stop responsive.
Branch `codex/source-cooldowns`, base `bafc21b`. Startup main/PR/CI and app state are verified;
the local startup suite passed **747 tests**. The saved private review dependency remains
checkpointed; no private investigation or paid work is needed for this goal.

Research shortlist, ranked by confirmed benefit and verification needs:
1. Source cooldowns: confirmed ignored HTTP dates, shortened delays and uncoordinated readers;
   moderate effort/risk, verified with fake clocks, concurrency and Stop tests. Selected.
2. Full-ad fallback: one eligible copy is tried even when another matched copy could supply
   full text; moderate effort, needs identity/budget/cache failure regressions.
3. Unknown local places: unresolved names are rejected despite the documented keep-unknown
   rule; low effort, needs fictional engineering/non-engineering collection regressions.
4. Source/vocabulary expansion: potential recall benefit, but permission and independent
   date-verified coverage evidence are still dependencies. No recall gain is established.

Protocol evidence is recorded in SOURCES. Mocked baseline requests reproduced a 600-second
delay shortened to 120 seconds and four CAPTCHA attempts. Shared host deadlines, integer/date
Retry-After parsing, cancellable waits, first-refusal blocking and progress notes are implemented.
Targeted checks passed **100 tests**, Ruff and whitespace. Independent-host, cache, terminal
failure, extended-deadline and engineering/nursing/hospitality retention checks are included.

Full local checks passed **774 tests**, Ruff, privacy and whitespace. Final diff review is in
progress. Exact next action: finish the review, commit/push and open a PR; verify final-head
Mac/Windows/privacy CI before a merge commit and synchronize main. No provider calls or live
vacancy traffic are planned; no live quality claim is made.

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

1. Independently judge full evidence and early title outcomes within applicable private authority.
2. Measure fresh-job misses, separating source coverage, title screening, duplicates and criteria.
3. Compare the next authorized search's interpretation, ranking and original elapsed time.
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
