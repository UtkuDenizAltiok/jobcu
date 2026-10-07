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

**CV-Library behind opaque redirects remains unfinished.** Known direct/exposed destinations
are protected by merged PR #63; an opaque redirect is not a proven alternate route to a known
blocked site. An unknown final host cannot yet be classified, and another platform does not
prove universal registration access. Do not claim that all hidden CV-Library routes are removed.

No unmerged product implementation remains. This final handover is on
`codex/session-closeout`; if interrupted on that branch, check its PR/CI and complete publication.
Exact next engineering action: establish permitted final-destination evidence for the existing
saved sample, retaining the exact vacancy identity. Do not probe blocked Adzuna pages, guess
application URLs, or discard unrelated UK jobs because their destination is unknown. If source
metadata cannot establish the route, add a private in-app way to identify an unusable destination;
never request private jobs/links in chat. Verify with fictional regressions before a quality claim.

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
