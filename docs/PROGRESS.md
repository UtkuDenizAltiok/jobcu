# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Result-save fix awaits publication; personal setup/search awaits confirmation.*

### State

- [PR #53](https://github.com/UtkuDenizAltiok/jobcu/pull/53) recovery is complete: merged,
  final PR/merged-main Mac/Windows/privacy checks passed, and clean main was synchronized.
  Dependencies were synced and the starting **617 tests** passed.
- A controlled fictional correction reproduced the recorded Windows restore race: the app
  reported finished while its save was paused. The fix keeps the run active until final
  results/status commit together, blocks overlapping work and explains storage failures.
  Code, regression checks and the usage/troubleshooting guides are **implemented**;
  **72 targeted tests**, Ruff, privacy and diff whitespace passed. Full suite/publication pending.
- README is the entry point; [How to use Jobcu](guides/first-search.md) explains everyday steps
  and richer examples. PROMPTS holds all three project prompts; dated background is in `archive/`.
  Beginner wording and preserving richer examples are recorded in DECISIONS.md.
- Jobcu and the preview are stopped (ports 8765/8799). Preserve on-demand launcher use.
- This session inspected no private inputs/results and made no live searches or paid requests.
  No private scratch copies or app/preview instances were created. No managed worktrees or
  attached artifacts were present at startup.

### In progress

Goal: investigate and fix the recorded Windows restore failure on
`codex/save-before-finished`, using only fictional data. PR #53 recovery is complete.

Reproduction, implementation, targeted checks and diff review are complete. The controlled
regression failed against the old completion order and passes with the fix. Ten new cases
cover final statuses, optional results, correction restore, overlap, storage failure and rollback.

Not yet pushed/merged. Exact next action: run closing Ruff/full tests/privacy checks, update
this checkpoint with results, commit/push and open a PR. Then wait for Mac/Windows/privacy CI,
merge with a merge commit, synchronize clean main and clear this checkpoint.
No private inputs/results, live searches or paid requests are authorized for this work.

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

1. Finish publishing the result-save fix described above.
2. Review completed search results with [REVIEW.md](REVIEW.md) before tuning.
3. Fix confirmed freshness, coverage and matching gaps in the country order from AGENTS.md.
4. Reduce summary dependence and repeated research; compare recall/ranking before optimizing cost/time.
5. Fix confusion observed during use. ZIP-update notices and a full fresh-Windows check remain later work.

### Known limitations

- Blocked sources stay blocked; a directory entry is not a verified vacancy or measured recall.
- Summaries, unknown dates and unchecked conditions can affect ranking; scores are not hiring probabilities.
- The quality set holds 50 ads and 40 titles. Older samples may lack location plans; missing timings
  and unlabelled quality remain unknown. Correction usage is cumulative.
- Provider/model research support varies; token estimates can omit web fees and discounts.

Historical measurements predate the Mac reset and are not a current baseline. See the
[decision history](archive/DECISION-HISTORY.md) and [source evidence](SOURCES.md) when relevant.
