# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Documentation cleanup is active before the first restored-Mac search.*

### State

- The session started on clean main `feb760f`, matching origin; PR #49 and main Mac/Windows/privacy
  CI passed. Locked dependencies synced; the local baseline passed **614 tests**.
- Jobcu and the preview are stopped (ports 8765/8799). Preserve on-demand launcher use.
- No private inputs/results were inspected and no live search or paid request was made.

### In progress

**Documentation cleanup, `codex/documentation-cleanup`, from `feb760f`.** Establish one home per
kind of information, combine the three reusable prompts, simplify guides and current records,
and move dated history into `docs/archive/`. Preserve source evidence, license, private data
and runtime paths. All edits are implemented; **22 document checks**, Ruff and the privacy
guard passed. Full verification/publication remain pending. Historical records are preserved;
current documents were reduced from 3,306 to about 830 lines outside the archive.

Exact next action: finish the diff review, stage every new/moved file, run the full suite and
privacy guard, commit/push a PR, wait for
Mac/Windows/privacy CI, then merge with a merge commit and return to clean main.

### Verify before relying on

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
