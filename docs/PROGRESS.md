# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Free engineering session; no new search or paid test ran.*

### State

- The previous handover, PR #64, is merged. The Mac checkout was clean at `ab00ee3` on
  resumption; main was synchronized at `729db41` after PR #65. Dependencies and hooks are
  synchronized. Both app ports were already stopped.
- [PR #65](https://github.com/UtkuDenizAltiok/jobcu/pull/65) implements the recorded fallback
  for hidden application destinations (implemented, tested, pushed and merged).
  **Application link problem** excludes an exact saved link locally; **Excluded links**
  offers undo even after the card disappears. Another
  already-matched link is retained, or the vacancy is left out with a counted reason.
- Reports preserve scores, owner ratings, Saved/Applied marks and original snapshots. They
  never fetch destinations or block unrelated links on the same site. Matching reads the
  report set once per filter/build stage. Changed tracking URLs need another report.
- **684 tests**, Ruff, privacy, JS syntax, whitespace and isolated Mac startup passed.
  Migration preservation, guarded APIs, restart, undo, storage failure and stale undo are
  covered with fictional engineering, nursing and hospitality jobs. Existing dependency
  deprecation warning remains. Final-head Mac/Windows/privacy PR CI passed for #65.
  No real accuracy, coverage, cost or speed gain is claimed.
- Fictional Mac UI walkthrough passed: employer fallback, exclusion without an alternative,
  reload, Saved history and undo; no console warnings/errors. Preview stopped and tab closed.
- No private-data access, provider calls, job-source requests or full search ran. Disposable
  fictional preview/self-test data was deleted. The owner's app remains stopped; no assistant
  instance remains. Start it on demand to load the merged changes.
- Earlier private search aggregates/evidence and original owner ratings remain preserved;
  none was read this session. Ambiguous review cases and independent top-10 labels remain
  unfinished; no new full search is needed to inspect saved evidence after authorization.

### In progress

**Proactive freshness/identity review**, branch `codex/job-memory-identity`, started from
clean synchronized main `61b133d`. PR #66 and final main Mac/Windows/privacy CI passed;
no open PR or running app/preview remains. Private data and paid work remain unauthorized.

Goal: prevent distinct fresh vacancies inheriting old jobs' dates/marks, and remove repeated
identity work while preserving proven copies. These are hypotheses until reproduced.

1. Research primary identifier/date guidance; inspect grouping and remembered-job identity.
2. Reproduce failures with fictional employer requisitions and non-engineering examples;
   choose the smallest general correction, preserving existing state and history.
3. Measure any optimization locally with fictional inputs; verify recall, reposts, marks,
   alternatives, ambiguity and failures. Update the relevant records and guide.
4. Review; run full Ruff/tests/privacy; publish a PR; wait for Mac/Windows/privacy CI;
   merge with a merge commit and synchronize clean main. Stop/delete assistant test state.

Reproduced in fictional electronics and nursing cases: two employer references became one
group, and a fresh reference inherited an old Not interested mark. Implemented grouping guards,
exact-ID memory precedence, a non-unique name index (migration 13), country/ambiguity checks,
atomic saves, bounded reads and per-grouping-call text reuse. Historical keys/marks remain.

Baseline: 684 tests/Ruff/privacy passed. New targeted regressions pass, including full mocked
electronics/nursing searches, transitive matches, empty IDs, conflicting full ads, legacy
state, low SQLite limits, rollback and exact-ID reposts. First fictional component benchmark
preserves 1,000 IDs and 40 groups: identity reads 1,000 -> 2; text preparation 1,560 -> 40.
Timing is preliminary and does not establish live search speed. A reusable fictional benchmark
is implemented; its privacy isolation/failure regression and document checks passed.
Review also closed concurrent-allocation and summary-bridge gaps, with regressions passing.
Full suite and publication remain pending. Exact next action: run all required checks and the
reproducible benchmark, record final measurements, then publish. Real ranking/coverage/speed
remain unverified.
The prior hidden-route fallback is complete; automatic hidden-host detection remains unverified.
Do not probe blocked pages, guess application URLs, or request private jobs/links in chat.

### Verify before relying on

- Hidden destinations: exact-link reports cover observed failures; automatic final-host
  identification and application access at alternate sites remain unverified.
- Ranking: independent full-evidence judgement and every top-10 label remain unfinished;
  summary cards need permitted original full ads. A balanced saved sample is not accuracy.
- Location/speed: combined medium-effort interpretation has fictional geography, commute,
  nursing and failure checks; live quality, latency and repeated-search savings are unmeasured.
- Maps: mocked station/edge/centre/quota checks pass; actual journeys need live validation.
- Coverage: independent date-verified 15–25-job benchmark in priority country order remains.
- Beginner install walkthrough and fresh Windows install/upload/search remain untested.

### Waiting on the owner

- No new keys, documents or settings are needed for these changes. Keep private inputs in Jobcu.
- The next planned on-demand search is **2026-10-08**, using the saved **24-hour** choice.
  Double-click **Start Jobcu.command** when ready. After a completed search, use
  [Review a search](PROMPTS.md#review-a-search) with explicit access/spending choices.
- When a link leads to an unusable application site, use **Application link problem** in
  Jobcu; **Excluded links** can undo it. This uses no AI allowance.
- Jobcu completes on-demand searches without assistant supervision. No scheduling or
  background app operation was added.

### Next tasks

1. Independently judge every top-10 job from full evidence under [REVIEW](REVIEW.md) after
   authorization. Keep observed hidden-route failures local; do not guess final hosts.
2. Measure fresh-job misses in Germany, Ireland, UK, Switzerland, Netherlands, Belgium, Italy
   before changing collection/scoring; all 30 countries and other professions remain supported.
3. Compare the next authorized search's interpretation, ranking and elapsed time.
4. ZIP-update notices and the fresh-Windows walkthrough remain later free engineering work.

### Known limitations

- Source/card counts do not measure market recall; scores are not hiring odds.
- Summaries, unknown dates, unchecked conditions and unknown application sites affect decisions.
- A changed redirect URL needs a new report. Undo restores a link where original results retain
  it; a later search that already omitted the vacancy needs the next on-demand search.
- Correction timings cover only the latest correction; usage accumulates across corrections.
- Token cost estimates can omit provider fees and discounts; they are not invoices.
- Maps samples approximate city edges/centres and can miss faster districts.
- A failed final save can lose visible results on closing; earlier saved searches remain.

Historical measurements predate the Mac reset. See [SOURCES](SOURCES.md) and
[the decision history](archive/DECISION-HISTORY.md) for dated background.
