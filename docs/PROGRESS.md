# Jobcu progress

Current work only. Follow [AGENTS](../AGENTS.md); use [PROMPTS](PROMPTS.md) across sessions.
Completed details live in Git and PRs. Product reasons: [DECISIONS](DECISIONS.md).

## Right now

*Updated 2026-10-07. Session closing; Maps fix is locally tested, publication is unfinished.*

### State

- The result-save fix is **implemented, tested, pushed and merged** in
  [PR #54](https://github.com/UtkuDenizAltiok/jobcu/pull/54). Main's subsequent Mac/Windows/privacy
  CI passed; its closing handover was merged in PR #55.
- Maps changes are **implemented and locally tested**: a named-station access probe with
  public-transport wording, city-edge/centre comparison, per-element quota counting, fractional
  duration/error handling and old-answer refresh. A visible note explains sampling limits.
  Durable behavior/reasons, service facts and guides are in ARCHITECTURE, DECISIONS and SOURCES.
- **638 local tests**, Ruff, privacy and whitespace passed; **87 targeted checks** passed.
  An isolated Mac startup self-test passed on port 8799, stopped and deleted its empty data.
  Closing checks were rerun: **638 passed**, Ruff/privacy/whitespace passed. The existing
  dependency deprecation warning remains; no failed local product checks remain.
- The implementation is **pushed, not merged** in
  [PR #56](https://github.com/UtkuDenizAltiok/jobcu/pull/56), remote head `6d667bc`.
  Local branch `codex/maps-route-probe` also has later handover commits. Repeated real pushes
  returned GitHub Internal Server Error; run `37642326144` is queued with no jobs started.
  Maps Mac/Windows/privacy CI and merge remain **unverified/pending**.
- Closing diagnosis: local Git integrity and an authenticated push dry-run passed, the remote
  URL/hooks are correct, and no local cause was identified. HTTPS writes still failed at GitHub.
  The strict SSH fallback lacks a trusted host entry; no SSH/account configuration was changed.
- The owner's Jobcu app on port 8765 remains running; preserve the owner's chosen state.
  Its existing process needs an on-demand restart to load the local changes. Port 8799 is stopped.
- Only public app health/build and public routing inputs were inspected. No private keys,
  documents, queries, results or logs were read; no Maps/provider calls or full searches ran.
  No private scratch copies or assistant-started instances remain; PR-body temporary files
  were removed. Existing user data and unrelated work were preserved.

### In progress

Scope is **session closeout and publication only**; start no new product work. Maps implementation,
local review/tests and documentation are complete. GitHub publication is unfinished.

The recoverable checkpoint was committed before closing checks; those checks passed.
One final normal HTTPS push is the remaining closeout attempt. Merge PR #56 only if its
final-head Mac/Windows/privacy CI actually passes. If writes/CI remain unavailable, leave this
clean committed branch, preserve the pending checks and do not claim a merge.

Exact next action in the next chat: follow the start/resume routine, retry the branch push,
verify PR #56's final head and checks, merge with a merge commit when they pass, and synchronize
main. Recover publication before new engineering work. No new private access, paid development
calls or full searches are authorized by start/end prompts.

### Verify before relying on

- New Maps station probe and actual journey accuracy: mocked regressions pass; no real-key
  recheck was made by the assistant. The earlier probe's walking/waiting breakdown is unknown.
- First restored-Mac search: provider/research access, document parsing, interpretation, sources,
  progress/results and usage still need a completed search and authorized review.
- Quality/freshness: independent top-10 evidence and a balanced 30–50-ad sample remain unmeasured.
- Coverage: a date-verified 15–25-job benchmark in AGENTS.md's country order remains open.
- Efficiency: whole-search step/wait timings, tokens and web usage lack a current baseline.
- Beginner install walkthrough and a fresh Windows install/upload/search remain untested.

### Waiting on the owner

1. The owner plans to start Jobcu and run the first search in the **next session**, then use
   [Review a search](PROMPTS.md#review-a-search) here. Maps access was confirmed by the owner;
   other private setup was not inspected.
2. Next session, close any old Jobcu text window (Terminate on Mac if asked), then double-click
   **Start Jobcu.command** to load the latest local code. Keep keys/documents/query inside Jobcu,
   choose job types and the posting window, and answer any limit prompt there.

### Next tasks

1. Complete the Maps fix's pending push, final-head platform/privacy CI and merge.
2. Review completed results under [REVIEW](REVIEW.md) with the review prompt's explicit scope.
3. Fix confirmed freshness, coverage and matching gaps in AGENTS.md's country order.
4. Compare recall/ranking before reducing repeated research, cost or time.
5. Address observed usability issues; ZIP-update notices and fresh-Windows validation remain later.

### Known limitations

- A directory entry or blocked source is not a verified vacancy or measured recall.
- Summaries, unknown dates and unchecked conditions can affect ranking; scores are not hiring odds.
- Old quality samples can lack plans/timings; correction usage is cumulative.
- Provider research access and charges vary; token estimates can omit web fees and discounts.
- Failed final saving can lose the latest results on closing; earlier saved results remain intact.
- Maps samples an approximate edge and centre, consuming up to two elements per city within
  the existing cap. It can miss faster districts; town-centre origins are not exact workplaces.

Historical measurements predate the Mac reset. See [SOURCES](SOURCES.md) and
[the decision history](archive/DECISION-HISTORY.md) for dated background.
