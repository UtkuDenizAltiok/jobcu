# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-08. Current engineering checks use fictional data.*

### State

- [PR #65](https://github.com/UtkuDenizAltiok/jobcu/pull/65) (application-link reports),
  [PR #67](https://github.com/UtkuDenizAltiok/jobcu/pull/67) (vacancy identity/local matching) and
  [PR #68](https://github.com/UtkuDenizAltiok/jobcu/pull/68) (location
  evidence and session prompts) are tested and merged with merge commits. The Mac checkout
  was synchronized at `5106dc1`; dependencies/hooks are current. Final-head
  Mac/Windows/privacy CI passed.
- Distinct fresh employer references and ambiguous groups keep separate dates/marks. Proven
  copies share one identity; historical keys/states/results are preserved. Local matching
  measurements and limits are in
  [ARCHITECTURE](ARCHITECTURE.md#fictional-local-comparison--2026-10-08).
  Live ranking/recall/speed remain unverified.
- A measured journey cannot verify a missing reference-city fact. New/rebuilt cards explain
  partial research and estimates per job, preserving scores/filtering and saved-plan edits.
- [Start/review/end prompts](PROMPTS.md) recover one active goal and prepare a fresh chat.
  End completes a coherent step where safe, checkpoints remaining work, and opens no new goals.
- 728 tests, Ruff, privacy, JS syntax, whitespace and fictional Mac UI/reload passed. Existing
  dependency deprecation warning remains. Both app/preview ports are stopped; disposable test
  state is removed. Owner data/ratings are preserved; private records stay outside Git.

### In progress

**Recall under incomplete career-title screening**, branch `codex/preserve-unreviewed-titles`,
based on clean synchronized main `02cc673`. No PR yet. Baseline 728 tests/Ruff/privacy passed;
main Mac/Windows/privacy CI passed, no open PR, and app/preview ports were stopped.

Goal: never classify unexamined career titles as irrelevant, and retain useful batch decisions
when an independent title-screen batch fails. Account/quota/spending failures must still stop
new paid work. These are code-path findings, not measured market recall.

1. Review the saved-evidence checkpoint privately and inspect the collection/title/filter path;
   check primary guidance on structured answers and independent task failures.
2. Reproduce cap, partial failure and invalid-answer cases with fictional engineering and
   non-engineering roles. Preserve unknown jobs for normal matching; expose checked/unknown
   outcomes without changing scores or increasing the title-screen request bound.
3. Verify matching continuity, per-source counts, cancellation, critical errors and histories;
   update decisions, architecture and the affected guide. Keep real evidence outside Git.
4. Run full Ruff/tests/privacy and relevant UI checks; review/publish, wait for final-head
   Mac/Windows/privacy CI, merge and synchronize main. Save needed private notes and delete
   disposable scratch; preserve the owner's stopped app state.

All three failures were reproduced by full mocked searches before the correction. Implemented
explicit-negative screening, per-batch recovery, unknown-tail retention, critical-error/Stop
propagation and raw source counts. Saved early rejections feed the existing bounded Score check
sample; Search details and the read-only review separate title screening from later matching.
Fictional engineering/nursing/hospitality checks pass, including 3,001 pairs with exactly 20
screen calls, parallel partial failures, unchanged scored-card results, cancellation, all four
critical errors, ID allowlisting, row injection and aggregate-output privacy.
Full local checks passed: **743 tests**, Ruff, privacy, JS syntax and whitespace. The final
wording adjustment passed targeted checks. Fictional Mac UI/reload shows the retained RF job,
raw/filtered counts, unreviewed explanations and expandable early rejections; no console errors/
warnings. Preview/tab are stopped/closed and disposable fictional data was deleted.
Final wording passed the refreshed full suite: **743 tests**, Ruff, privacy, JS syntax and
whitespace. Diff review is complete. Exact next action: commit/push/open PR, wait for final-head
Mac/Windows/privacy CI, merge and synchronize main. Private review notes are saved; delete
the disposable private scratch before ending.
The independent live coverage benchmark and full-evidence ranking remain unfinished; no live
improvement is claimed. No new search or paid development test has started.

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
- Search on demand: double-click **Start Jobcu.command**, choose **24 hours**, then search
  when ready. After completion, use [Review a search](PROMPTS.md#review-a-search); existing
  permissions apply within their scope and no keys/documents need to be shared in chat.
- Before closing a chat, use [End](PROMPTS.md#end-a-session) and wait for the saved-state
  confirmation. Open a fresh local project chat and use [Start](PROMPTS.md#start-a-session).
- When a link leads to an unusable application site, use **Application link problem** in
  Jobcu; **Excluded links** can undo it. This uses no AI allowance.
- Jobcu completes on-demand searches without assistant supervision. No scheduling or
  background app operation was added.

### Next tasks

1. Independently judge every top-10 job from full evidence under [REVIEW](REVIEW.md), within
   applicable authorization. Keep observed hidden-route failures local; do not guess final hosts.
2. Measure fresh-job misses in Germany, Ireland, UK, Switzerland, Netherlands, Belgium, Italy
   before changing collection/scoring; all 30 countries and other professions remain supported.
3. Compare the next authorized search's interpretation, ranking and elapsed time.
4. ZIP-update notices and the fresh-Windows walkthrough remain later free engineering work.

### Known limitations

- Source/card counts do not measure market recall; scores are not hiring odds.
- Historical cards keep their original check labels. New searches or rebuilt conditions apply
  the reference-place confidence correction; original snapshots are not rewritten.
- Summaries, unknown dates, unchecked conditions and unknown application sites affect decisions.
- A changed redirect URL needs a new report. Undo restores a link where original results retain
  it; a later search that already omitted the vacancy needs the next on-demand search.
- Correction timings cover only the latest correction; usage accumulates across corrections.
- Token cost estimates can omit provider fees and discounts; they are not invoices.
- Maps samples approximate city edges/centres and can miss faster districts.
- A failed final save can lose visible results on closing; earlier saved searches remain.

Archived historical measurements predate the Mac reset. See [SOURCES](SOURCES.md) and
[the decision history](archive/DECISION-HISTORY.md) for dated background.
