# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Documentation work is complete; personal setup/search awaits confirmation.*

### State

- Documentation organization, beginner guides and richer query examples are **implemented,
  tested, pushed and merged** in [PR #50](https://github.com/UtkuDenizAltiok/jobcu/pull/50),
  [PR #51](https://github.com/UtkuDenizAltiok/jobcu/pull/51) and
  [PR #52](https://github.com/UtkuDenizAltiok/jobcu/pull/52). Mac/GitHub main were synchronized
  before this closing checkpoint; latest merged-main Mac/Windows/privacy CI passed.
- README is the entry point; [How to use Jobcu](guides/first-search.md) explains everyday steps
  and richer examples. PROMPTS holds all three project prompts; dated background is in `archive/`.
  Beginner wording and preserving richer examples are recorded in DECISIONS.md.
- Jobcu and the preview are stopped (ports 8765/8799). Preserve on-demand launcher use.
- This session inspected no private inputs/results and made no live searches or paid requests.
  No private scratch copies were created; temporary PR-body files were removed.

### In progress

Only session closure remains. Branch: `codex/session-handover`; no PR yet. This checkpoint
records verified completed work and owner inputs before final checks. No implementation files
are unfinished; no new development, private-data access or paid work is authorized.

Earlier **617 tests**, Ruff/privacy and latest merged-main CI passed. Closing checks on this
checkpoint are not run yet. Exact next action: run Ruff/full tests/privacy, review and publish
the handover, wait for Mac/Windows/privacy CI, merge with a merge commit and leave clean main.

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

1. Review those results with [REVIEW.md](REVIEW.md) before tuning.
2. Fix confirmed freshness, coverage and matching gaps in the country order from AGENTS.md.
3. Reduce summary dependence and repeated research; compare recall/ranking before optimizing cost/time.
4. Fix confusion observed during use. ZIP-update notices and a full fresh-Windows check remain later work.

### Known limitations

- Blocked sources stay blocked; a directory entry is not a verified vacancy or measured recall.
- Summaries, unknown dates and unchecked conditions can affect ranking; scores are not hiring probabilities.
- The quality set holds 50 ads and 40 titles. Older samples may lack location plans; missing timings
  and unlabelled quality remain unknown. Correction usage is cumulative.
- Provider/model research support varies; token estimates can omit web fees and discounts.

Historical measurements predate the Mac reset and are not a current baseline. See the
[decision history](archive/DECISION-HISTORY.md) and [source evidence](SOURCES.md) when relevant.
