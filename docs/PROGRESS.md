# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Checking the Maps probe before the owner's first search.*

### State

- [PR #53](https://github.com/UtkuDenizAltiok/jobcu/pull/53) recovery is complete; its final
  PR and merged-main Mac/Windows/privacy checks passed. Startup found clean current main.
- The result-save race is **implemented, tested, pushed and merged** in
  [PR #54](https://github.com/UtkuDenizAltiok/jobcu/pull/54), using a merge commit.
  Its final Mac/Windows/privacy checks passed; the Mac checkout was synchronized afterward.
  Searches/corrections now stay active until final results/status commit together. Overlapping
  work is blocked during saving; storage failures keep available results visible with a warning.
- A controlled fictional correction reproduced finished-before-save on the old code and passed
  with the fix. Ten new regression cases cover final statuses, optional results, correction
  restore, overlap, storage failure and rollback. **627 local tests**, Ruff, privacy and diff
  whitespace passed; no failed local checks remain. Usage/troubleshooting guides are updated.
- The Maps probe's train-only label and town-centre-to-edge inputs were reproduced with mocked
  requests. A fictional slow-edge/fast-centre case also reproduced a false rejection. The fixes
  are implemented: named station probe, public-transport wording, access-only explanation,
  edge/centre comparison, exact element counting, stale-answer refresh and a visible sampling
  limit. **87 targeted tests**, the closing **638 tests**, Ruff, privacy and diff whitespace
  passed. Publication and platform CI are pending.
- README is the entry point; [How to use Jobcu](guides/first-search.md) explains everyday steps
  and richer examples. PROMPTS holds all three project prompts; dated background is in `archive/`.
  Beginner wording and preserving richer examples are recorded in DECISIONS.md.
- The owner started Jobcu on port 8765 and confirmed a successful Maps key test. The running
  build matched clean current main; port 8799 is stopped. Preserve the owner's running app.
- Only the running app's public health/build and public routing inputs were inspected; no
  private keys/documents/queries/results/logs were read and no provider/Maps calls or searches ran.
  No private scratch copies or app/preview instances were created. No managed worktrees or
  attached artifacts were present at startup.

### In progress

Goal on `codex/maps-route-probe`: check the misleading Maps connection-test duration before
the owner starts a search. Startup Git/PR/CI checks passed; the baseline **627 tests** passed.

1. Inspect only app health/build and public routing inputs; do not read private keys,
   documents, queries, results or logs. Keep the owner's app running.
2. Make the connection test use explicit station endpoints and call its result public
   transport, rather than train-only time. Check arbitrary edge-point routing in searches.
3. Add fictional route/filter regressions, record verified service facts and limits, run
   Ruff/tests/privacy, review/push/PR, wait for Mac/Windows/privacy CI and merge.
4. Synchronize clean main; tell the owner how to restart on demand before searching.

Confirmed: the old test sends town-centre-to-calculated-city-edge coordinates with TRANSIT,
then labels the returned whole-journey duration "by train". The particular walking/waiting
breakdown of the owner's reported duration is unknown; no new Maps/provider calls were made.
Both controlled regressions failed against the old code and pass with the fix. Targeted checks
also cover fractional durations, missing routes, quota limits, old answers, explicit city-centre
requests and fictional hardware/library profiles. Reviewed, fully tested and **pushed** in
[PR #56](https://github.com/UtkuDenizAltiok/jobcu/pull/56); not yet merged. Exact next action:
wait for final Mac/Windows/privacy CI, merge with a merge commit and synchronize clean main.
Then publish the closing handover and tell the owner to restart before searching.
No paid development test or full search is authorized.

### Verify before relying on

- Beginner guides: a first-time user's install/setup/search walkthrough remains untested.
- First restored-Mac search: provider/model access, document parsing, criteria interpretation,
  source availability, progress, results and usage. A connection test does not prove research access.
- Freshness: original posting/closing dates, old reposts and distinct requisitions.
- Quality: independent top-10 full evidence plus a balanced 30–50-ad sample; summary exposure and
  borderline score stability remain unmeasured after the reset.
- Coverage: a date-verified 15–25-job benchmark in country order from AGENTS.md.
- Efficiency: complete original-search timings, answer-wait time, tokens and web usage on that sample.
- Windows: automated CI passes; a full human install/upload/search on a fresh Windows machine is open.

### Waiting on the owner

1. Personal setup/search is awaiting confirmation; private app data was not inspected. If
   still needed, open Jobcu on demand, enter keys/documents/query **inside the app**, choose
   job types and the 72-hour posting window, and complete the search and any limit prompt.
2. Once a search is complete, use [Review a search](PROMPTS.md#review-a-search) in the local
   project chat. Start the next chat with [Start a session](PROMPTS.md#start-a-session).

### Next tasks

1. Review completed search results with [REVIEW.md](REVIEW.md) before tuning.
2. Fix confirmed freshness, coverage and matching gaps in the country order from AGENTS.md.
3. Reduce summary dependence and repeated research; compare recall/ranking before optimizing cost/time.
4. Fix confusion observed during use. ZIP-update notices and a full fresh-Windows check remain later work.

### Known limitations

- Blocked sources stay blocked; a directory entry is not a verified vacancy or measured recall.
- Summaries, unknown dates and unchecked conditions can affect ranking; scores are not hiring probabilities.
- The quality set holds 50 ads and 40 titles. Older samples may lack location plans; missing timings
  and unlabelled quality remain unknown. Correction usage is cumulative.
- Provider/model research support varies; token estimates can omit web fees and discounts.
- If final saving fails, the latest results may not survive closing Jobcu; any earlier saved results
  remain available. Follow the warning before closing the app.

Historical measurements predate the Mac reset and are not a current baseline. See the
[decision history](archive/DECISION-HISTORY.md) and [source evidence](SOURCES.md) when relevant.
