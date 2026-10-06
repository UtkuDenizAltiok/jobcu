# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Documentation is organized; personal setup and the first search are next.*

### State

- Cleanup is implemented and published in [PR #50](https://github.com/UtkuDenizAltiok/jobcu/pull/50).
  README is the entry point; PROMPTS holds all three prompts. Dated background is in `archive/`.
  **617 tests**, Ruff and the privacy guard passed locally. The PR/CI record establishes merge state.
- Jobcu and the preview are stopped (ports 8765/8799). Preserve on-demand launcher use.
- No private inputs/results were inspected and no live search or paid request was made.

### In progress

Goal: make everyday instructions clear enough for first-time users with little technical
experience. Branch: `codex/plain-usage-guides`; no PR yet. No new paid work is authorized.

1. Check the actual setup, search, result and launcher labels/behavior against the guides.
2. Rewrite README's usage section and guides as explained steps, keeping optional setup separate.
3. Check document links, run Ruff/tests/privacy checks, review, publish and merge after CI.

Implemented: explained README usage steps; installation, AI/key setup, first search, results,
stopping/reopening and troubleshooting guides. Corrected document formats and separate key/model
saves from code; simplified Settings copy and removed stale free-use promises. No AI/source
behavior changed. OS instructions cite verified Apple/Microsoft guidance.
Checks: final **617 tests**, Ruff and privacy passed after correcting the app's external-URL
check; guide navigation stays in README. Jobcu/preview remain stopped.
Exact next action: push the validated branch, open a PR and wait for Mac/Windows/privacy CI.

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
