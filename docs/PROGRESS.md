# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Closing the session; no new search or paid review is running.*

### State

- Main was clean and synchronized at start; no earlier implementation needed recovery.
  PR #58's final-head Mac/Windows/privacy CI passed; its merge is synchronized locally.
  Subsequent main Mac/Windows/privacy CI also passed; dependencies were synchronized.
  PR #60's final-head and subsequent main Mac/Windows/privacy CI also passed.
- Implemented, locally tested, pushed and merged with a merge commit in
  [PR #58](https://github.com/UtkuDenizAltiok/jobcu/pull/58): sought-role progress,
  explicit history label, optional document-understanding reset, cumulative online-check
  progress, original vacancy URL, combined medium-effort location interpretation with a format
  fallback, separate travel usage, and a 24-hour new-install posting window.
- Earlier merged work: **655 tests**, Ruff, privacy, JS syntax and whitespace passed. A fictional reset-screen check
  passed with no browser errors; isolated Mac startup self-test passed on port 8799 and stopped.
  The existing dependency deprecation warning remains; no failed product checks remain.
- The authorized latest-search aggregate review is saved in the private data folder. Additional
  balanced evidence was saved for Score check and a supported assistant label was added;
  existing owner ratings were preserved. No keys,
  provider calls, paid re-score, source requests or another full search were used in this review.
  No personal profile, query, documents, jobs or ratings were published.
- The owner's requested next-search posting choice was saved as 24 hours. His app on port 8765
  remains running in its original process; it needs an on-demand restart to load these changes.
  Port 8799 is stopped. Disposable review/preview data and the temporary browser tab are deleted.
- Closeout corrections are implemented: no default scoring/web-check cap, preserved saved
  optional limits, corrected review prompt and independent on-demand product intent.
  The owner's per-search caps are cleared locally; verified current token prices are saved
  privately. Monthly choices, Maps control, documents, results and ratings are preserved.

### In progress

Session closeout only, on `codex/review-budget-closeout` from synchronized main `65add76`.
Default/settings/guidance corrections are implemented; the private settings save was read back
and verified. Current branch checks, push, PR/CI and merge are pending. Earlier changes remain
implemented, tested, pushed and merged in PRs #58 and #60.
Exact next action: run Ruff, pytest and privacy checks; review and push the complete change,
wait for Mac/Windows/privacy CI, merge with a merge commit, and read back the final handover.
No new quality investigation, paid re-score, source requests or full search during closeout.

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

### Owner inputs and next session

- No keys, documents or price entry are needed for this closeout. Current prices are saved
  locally; dated public pricing evidence is in [SOURCES](SOURCES.md#ai-and-maps).
- The owner plans the next 24-hour on-demand search on 2026-10-08. Restart through
  **Start Jobcu.command** when ready to load merged code, then use
  [Review a search](PROMPTS.md#review-a-search) in the next local project chat.
- Summary-based cards still need permitted original full-ad evidence for complete independent
  judgement. Ambiguous sample cases remain unrated; owner labels/results are preserved.

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
