# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Beginner usage guides are ready; personal setup and the first search are next.*

### State

- Explained usage guides are published in [PR #51](https://github.com/UtkuDenizAltiok/jobcu/pull/51).
  README is the entry point; [How to use Jobcu](guides/first-search.md) covers everyday steps.
  **617 tests**, Ruff and privacy passed locally; the PR/CI record establishes merge state.
  PROMPTS holds all three project prompts; dated background stays in `archive/`.
- Jobcu and the preview are stopped (ports 8765/8799). Preserve on-demand launcher use.
- No private inputs/results were inspected and no live search or paid request was made.

### In progress

Goal: restore clear examples of research-based place conditions, including election vote
shares and Turkish markets, in README and the usage guide. Branch:
`codex/restore-query-examples`; no PR yet. No paid calls or private-data access are authorized.

1. Recover the public examples and check interpretation/research behavior against code.
2. Add plain examples and a combined query; explain estimates, unchecked facts and correction.
3. Review, run Ruff/tests/privacy, publish and merge after Mac/Windows/privacy CI.

Implemented: restored the public example range and added a combined query; clarified the
same-election national vote-share comparison, shop counts and unchecked/estimated facts.
Checked against the location/research instructions and existing fictional tests. No code changed.
Checks: **617 tests**, 22 document/link checks, Ruff, privacy and diff whitespace passed.
Jobcu/preview remain stopped. Exact next action: commit/push, open a PR and finish CI/merge.

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

1. After cleanup, open Jobcu, enter keys/documents/query **inside the app**, choose job types
   and the 72-hour posting window, and complete the first search and any limit prompt.
2. Use [Review a search](PROMPTS.md#review-a-search) in the local project chat.

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
