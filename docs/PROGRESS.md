# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Session closeout; no new search or paid test is running.*

### State

- Mac main was clean and synchronized at `2581b30` before this handover branch.
  Product changes are implemented, locally tested, pushed and merged with merge commits:
  [PR #58](https://github.com/UtkuDenizAltiok/jobcu/pull/58) fixes profile/history progress,
  optional document reset, cumulative online-check progress and location interpretation;
  [PR #60](https://github.com/UtkuDenizAltiok/jobcu/pull/60) fixes full-ad experience replacement
  and atomic protection of owner ratings.
- [PR #62](https://github.com/UtkuDenizAltiok/jobcu/pull/62) removes default scoring/web-check
  caps and the fixed review allowance. Saved optional controls remain supported. The owner's
  per-search caps are cleared privately; verified current token prices are saved locally.
  Monthly choices, Maps control and medium effort are preserved. Prices are optional for
  ordinary searches; dated pricing facts live in [SOURCES](SOURCES.md#ai-and-maps).
- [PR #63](https://github.com/UtkuDenizAltiok/jobcu/pull/63) excludes known CV-Library routes,
  uses another already-matched link where available, and filters restored recommendations
  without rewriting original snapshots. Saved/applied history retains its state with excluded
  links disabled. Opaque application destinations are labelled unverified.
- **673 tests**, Ruff, privacy, JS syntax and whitespace passed. Final-head Mac/Windows/privacy
  CI and subsequent main CI passed for all product PRs, including PR #63.
  Dependencies were synchronized. The existing dependency deprecation warning remains.
- The completed-search aggregate and evidence audit are saved privately. Owner ratings and
  original results are preserved; ambiguous sample cases remain unrated. No full top-10
  precision, score stability, market recall or live speed improvement is claimed.
- No provider calls, paid re-score, job-source requests or new full search ran in this review.
  Private investigations used disposable copies outside Git; all are deleted. Detailed evidence
  remains in the private data folder. No private profile/query/documents/jobs/ratings/keys
  were published.
- The next-search choice is saved as **24 hours**. The owner's original app on port 8765 is
  preserved; port 8799 is stopped and no assistant instance remains. Earlier fictional reset
  UI and isolated Mac startup checks passed and their preview stopped. The new application
  labels have syntax/API coverage, but no new visual walkthrough was run during closeout.

### In progress

**Recover hidden application-route handling**, branch `codex/unusable-application-links`.
The earlier handover PR #64 is merged; clean main at `ab00ee3` and its Mac/Windows/privacy
CI passed. Dependencies are synchronized. Baseline: 673 tests, Ruff and privacy passed.
Both app ports are stopped; no abandoned Jobcu scratch directories were found.

This session authorizes free fictional checks only: no private saved evidence, provider calls,
job-site traffic or full search. An opaque redirect cannot establish its final host. Use the
recorded fallback: a local, reversible way for the person to mark an unusable application link.

1. Add exact-link persistence and route selection/filtering without suppressing unrelated jobs,
   changing scores, owner ratings or original snapshots.
2. Add clear reporting/undo controls, update the guide and decision/architecture records.
3. Verify fictional engineering and non-engineering routes, alternatives, restart, undo and
   guarded API failures; inspect an isolated fictional preview and stop it.
4. Review; run Ruff, full tests, privacy and JS checks; push a PR; wait for Mac/Windows/privacy
   CI; merge with a merge commit and synchronize clean main.

Migration, guarded local APIs, route handling and report/undo controls are implemented.
Targeted regressions, Ruff, JS syntax and whitespace passed. The isolated fictional Mac UI
walkthrough passed: employer alternative, removal without an alternative, reload persistence,
Saved history and undo; no browser console warnings/errors. Preview stopped and its tab closed.
Review added monotonic report IDs to stop stale undo buttons deleting a newer report.
Full checks and publication are pending. Exact next action: run the full local suite/privacy
and isolated launcher self-test, then push/open a PR and wait for CI before merging.
Automatic final-host identification and real ranking/coverage/speed claims remain unverified;
do not probe blocked pages or guess application URLs.

### Verify before relying on

- Ranking: independent full-evidence judgement and every top-10 label remain unfinished;
  summary cards need permitted original full ads. A balanced saved sample is not accuracy.
- Location/speed: combined medium-effort interpretation has fictional country, commute,
  nursing and failure checks; live quality, latency and repeated-search savings are unmeasured.
  Older travel estimates share location usage; new searches separate travel usage.
- Maps: mocked station/edge/centre/quota checks pass; actual journeys need live validation.
- Coverage: independent date-verified 15–25-job benchmark in priority country order remains.
- Beginner install walkthrough and fresh Windows install/upload/search remain untested.

### Waiting on the owner

- No keys, documents or price entry are needed for this closeout. Keep private inputs in Jobcu.
- The owner plans the next 24-hour on-demand search on **2026-10-08**. Start the next local
  project chat with [Start a session](PROMPTS.md#start-a-session), recovering the application-route
  task first. Restart with **Start Jobcu.command** when ready to load merged code. After a
  completed search, use [Review a search](PROMPTS.md#review-a-search).
- The finished product should complete on-demand searches without assistant supervision;
  development review and decisions remain the assistant's responsibility. No scheduling or
  background app operation was added.

### Next tasks

1. Finish hidden application-route handling, then independent full-ad/top-10 checks under
   [REVIEW](REVIEW.md). No new full search is needed to inspect saved evidence.
2. Measure fresh-job misses in priority country order before changing collection/scoring.
3. Compare the next authorized search's interpretation, ranking and elapsed time.
4. ZIP-update notices and the fresh-Windows walkthrough remain later.

### Known limitations

- Source/card counts do not measure market recall; scores are not hiring odds.
- Summaries, unknown dates, unchecked conditions and unknown application sites affect decisions.
- Correction timings cover only the latest correction; usage accumulates across corrections.
- Token cost estimates can omit provider fees and discounts; they are not invoices.
- Maps samples approximate city edges/centres and can miss faster districts.
- A failed final save can lose visible results on closing; earlier saved searches remain.

Historical measurements predate the Mac reset. See [SOURCES](SOURCES.md) and
[the decision history](archive/DECISION-HISTORY.md) for dated background.
