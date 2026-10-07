# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-08. Current engineering checks use fictional data.*

### State

- [PR #65](https://github.com/UtkuDenizAltiok/jobcu/pull/65) (application-link reporting) and
  [PR #67](https://github.com/UtkuDenizAltiok/jobcu/pull/67) (vacancy identity and local matching
  work) are tested and merged with merge commits. Main was synchronized at `75cc83e`;
  dependencies/hooks are current. Final-head Mac/Windows/privacy PR CI passed.
- Fresh employer references and ambiguous current groups retain separate dates/marks.
  Proven copies share one identity. Migration 13 preserves historical keys, states and results;
  previously merged history is not guessed apart. No scoring cache or collection change.
- **718 tests**, Ruff, privacy, whitespace, isolated Mac startup and direct import passed.
  Component measurements and their limits are in
  [ARCHITECTURE](ARCHITECTURE.md#fictional-local-comparison--2026-10-08).
  Live ranking/recall/end-to-end speed remain unverified. Existing dependency warning remains.
- Both app/preview ports are stopped. Owner data and ratings are preserved. No private
  material or real-result measurements belong in this handover; consult [REVIEW](REVIEW.md)
  and applicable private records for authorized investigations.

### In progress

**Location evidence and session handover**, branch `codex/location-check-confidence`, based on
synchronized main `75cc83e`. No PR yet; implementation not started.

Goal: prevent a checked journey from presenting an unchecked reference-place fact as verified,
and make start/review/end prompts recover work reliably in a fresh chat.

1. Reproduce confidence loss with fictional engineering and non-engineering examples.
2. Preserve reference-place research confidence through travel measurement, saved plans,
   corrections and cards. Explain partial checks clearly without changing scores or recall.
3. Refine the three prompts and AGENTS routine: one active goal, checkpoint before long work,
   end drains the current coherent step without new scope, next chat needs no prior context.
4. Run targeted/full checks, privacy and fictional UI verification; review, push, open PR,
   wait for Mac/Windows/privacy CI, merge and synchronize main; clean up assistant state.

Exact next action: add fictional failure regressions, implement confidence preservation and
update the handover prompts. Preserve original private evidence and owner ratings outside Git.

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
