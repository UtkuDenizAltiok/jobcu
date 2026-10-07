# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Free aggregate review and search-usability fixes are merged; restart on demand.*

### State

- Main was clean and synchronized at start; no earlier implementation needed recovery.
  PR #58's final-head Mac/Windows/privacy CI passed; its merge is synchronized locally.
  Subsequent main Mac/Windows/privacy CI also passed; dependencies were synchronized.
- Implemented, locally tested, pushed and merged with a merge commit in
  [PR #58](https://github.com/UtkuDenizAltiok/jobcu/pull/58): sought-role progress,
  explicit history label, optional document-understanding reset, cumulative online-check
  progress, original vacancy URL, combined medium-effort location interpretation with a format
  fallback, separate travel usage, and a 24-hour new-install posting window.
- **648 tests**, Ruff, privacy, JS syntax and whitespace passed. A fictional reset-screen check
  passed with no browser errors; isolated Mac startup self-test passed on port 8799 and stopped.
  The existing dependency deprecation warning remains; no failed product checks remain.
- The authorized latest-search aggregate review is saved in the private data folder. Additional
  balanced evidence was saved for Score check; existing owner ratings were preserved. No keys,
  provider calls, paid re-score, source requests or another full search were used in this review.
  No personal profile, query, documents, jobs or ratings were published.
- The owner's requested next-search posting choice was saved as 24 hours. His app on port 8765
  remains running in its original process; it needs an on-demand restart to load these changes.
  Port 8799 is stopped. Disposable review/preview data and the temporary browser tab are deleted.

### In progress

Finished-search evidence/ranking audit on `codex/finished-search-audit`.
- Completed free evidence checks on the balanced private sample. A conservative supported
  assistant label is saved privately; ambiguous evidence remains unrated and owner labels are
  preserved. Candidate experience discrepancies are hypotheses, not confirmed extraction bugs.
- Confirmed code defect: a full-ad answer with no minimum years retained the summary's old
  years requirement and score limit. Corrected the replacement rule; other blockers remain.
  Original saved results were not overwritten and live ranking impact is not claimed.
- Implemented atomic ownership protection for assistant ratings, including legacy labels and
  an owner edit between the review's read/write. No paid calls, source traffic or full search.
- Checks: 655 tests, Ruff, privacy and whitespace passed; original PR #58/#59 and main CI passed.
  New audit changes are implemented, locally tested and pushed in
  [PR #60](https://github.com/UtkuDenizAltiok/jobcu/pull/60); CI/merge remain. Private audit
  evidence/aggregates are retained locally; disposable scratch is deleted.
Exact next action: wait for final-head Mac/Windows/privacy CI on PR #60, merge with a merge
commit, synchronize main and close the handover. Disposable scratch is already removed.

### Verify before relying on

- Combined location interpretation: fictional country, commute, nursing and failure checks pass;
  no live provider comparison was made. Fewer normal calls does not establish live speed or
  equal interpretation quality. Confirm on the next authorized on-demand search.
- Ranking: independent full-evidence/criteria judgement remains unfinished. Some sample ads
  need original full text. No top-10 precision, score stability or benchmark recall is claimed.
- Efficiency: an original-search timing baseline exists privately. Older travel estimates share
  the location usage bucket; new runs separate them. Repeated-search savings remain unmeasured.
- Maps: mocked station/edge/centre/quota checks pass; actual journeys still need live validation.
- Coverage: independent date-verified 15–25-job benchmark in AGENTS.md's country order remains.
- Beginner install walkthrough and a fresh Windows install/upload/search remain untested.

### Waiting on the owner

1. To unlock a bounded medium-effort re-score of the existing sample, configure current prices
   inside Jobcu. Prices are absent, so this review's conditional EUR1 permission was not used.
   Keep all private inputs in Jobcu. A running app is not required for free saved-result review.
2. Summary-based cards still need permitted original full-ad evidence for a complete ranking
   assessment. The next on-demand daily search remains set to 24 hours; none was started here.

### Next tasks

1. Finish independent full-ad judgement and top-10 evidence checks under [REVIEW](REVIEW.md).
2. Measure fresh-job misses in the priority country order before changing collection/scoring.
3. Compare next-search interpretation, recall/ranking and elapsed time before further reductions.
4. ZIP-update notices and fresh-Windows walkthrough remain later.

### Known limitations

- Source/card counts do not measure market recall; scores are not hiring odds.
- Summaries, unknown dates and unchecked conditions can affect ranking.
- Corrections measure only the latest correction's time but accumulate original/correction usage.
- Provider fees/discounts can be missing from token cost estimates.
- Maps compares approximate edge/centre samples and can miss faster districts.
- A failed final save can lose the latest visible results on closing; earlier saved results remain.

Historical measurements predate the Mac reset. See [SOURCES](SOURCES.md) and
[the decision history](archive/DECISION-HISTORY.md) for dated background.
