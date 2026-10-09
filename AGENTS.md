# Jobcu: working instructions

These rules apply to contributors and assistants. Current decisions supersede the archived
concept. Jobcu runs on macOS and Windows; public source and handovers live on GitHub.

## Mission and priorities

Find relevant fresh jobs, explain fit accurately and keep the app simple. Coverage and freshness
come first, then filtering/scoring, ease of use, cost and speed. Preserve recall and scores when
reducing repeated work. Every AI step defaults to **medium** effort.

Validate electronics, hardware and power electronics first. Country work order: **Germany,
Ireland, UK, Switzerland, Netherlands, Belgium, Italy** (owner, 2026-10-06). All 30 countries in
`src/jobcu/countries.py` and other professions remain supported. Changes must be general;
include fictional non-engineering profiles in matching regressions.

## Authority and communication

- The assistant owns product/engineering decisions, implementation, cleanup, review and tested
  merges. The human retains ownership, copyright and licensing. Account changes, spending and
  messages in the owner's name need his instructions. The service budget is up to EUR30/month
  (owner, 2026-10-09; supersedes EUR25);
  paid development tests need authorization and a bounded budget. Respect existing user limits.
- Complete authorized work and record routine decisions. Keep the Mac checkout and GitHub current
  through the session routine. Local means execution on the Mac; Git publication is versioned.
- Explain plainly, assume no programming experience, and finish **every response with simple,
  direct next steps**. Do technical work yourself. Never request keys, passwords, documents or
  private queries in chat; the owner enters them in Jobcu.
- Jobcu runs on demand: double-click **Start Jobcu.command**, then close the terminal and choose
  **Terminate** if asked. Do not automatically start or leave it running. Use self-tests or
  isolated previews; stop instances you started and respect the owner's chosen app state.
- Preserve owner data. Adding or testing reset controls does not authorize using them on it;
  perform an owner-data reset only when explicitly asked to do that deletion.

## Hard rules

1. **No job-site logins or bypasses.** Respect robots.txt, terms, request budgets and Retry-After.
   No account cookies, CAPTCHA solving or bot-protection evasion. A blocked source stays blocked;
   find a permitted alternative. Verify current terms before adding or changing a source.
2. **Device-local app.** No hosting, user accounts, telemetry, analytics or cloud storage.
   Connections are to job sources, the chosen AI provider and optional Google Maps. Explain
   that necessary text goes to that provider; local storage does not mean offline use.
3. **Private data stays outside Git and public output.** Keys, documents, queries, profiles,
   results, ratings, logs and account identifiers never enter fixtures, docs, PRs, issues,
   screenshots or CI logs. Use fictional examples and approved aggregate findings.
   `paths.ensure_data_dir()` enforces the folder boundary; the commit guard cannot prove prose
   is private. Private investigations use an authorized scratch copy outside every checkout.
   Check `assistant-authorization.json` in the private data folder for any standing owner
   instructions before private work. Keep that record outside Git and public output; its
   recipient, scope, limits and later revocations control access. Absence grants no access.
4. **Preserve history and proprietary licensing.** Keep LICENSE and the owner's copyright.
   No force pushes, shared-history rewrite, squash or rebase merge. Use merge commits. Public
   source does not grant reuse permission. Cleanup changes current files, not Git history.
5. **Support Mac and Windows.** Use Python 3.13, uv, pathlib and explicit UTF-8. CI checks both.
6. **Provider-neutral, English UI.** Users choose the provider/model. No built-in preferred
   provider or model names. All AI calls go through `ai/client.py`. Any guide recommendation
   requires dated, current verified evidence and an explanation of its limits.

## Information homes

| Information | Home |
|---|---|
| Current state, interrupted work, pending checks and priorities | [PROGRESS](docs/PROGRESS.md) |
| Current decisions, architecture, module/tool map and lessons | [ENGINEERING](docs/ENGINEERING.md) |
| Source/service facts, terms and dated evidence | [SOURCES](docs/SOURCES.md) |
| All reusable prompts | [PROMPTS](docs/PROMPTS.md) |
| Developer setup and private-results procedure | [CONTRIBUTING](CONTRIBUTING.md) |
| Everyday use and navigation | [README](README.md) and [guides](docs/guides/) |
| Historical concept, decisions and research | [archive](docs/archive/) |
| Detailed change history | Git commits and PRs |

Keep each fact in its home and link to it. Read only relevant material; archives are background.
Code/tests establish behavior; the latest current decision establishes intent.

## Sessions

Start prepares the chat; Review, Deep improvement or another owner task directs development;
End finishes or parks it. Use [Start, a task, then End](docs/PROMPTS.md). Product initiative
belongs inside the task the owner requested. A backlog item is not an instruction to start it.

### Starting, or resuming after any interruption

1. In a fresh chat, assume no previous conversation. Check `git status` and all uncommitted
   diffs; read **Right now** in PROGRESS.md. Preserve unexplained work.
2. On clean main, `git pull --ff-only`, then `uv sync --locked`. Check recent commits and the
   relevant PR/CI at their actual heads; pushed, tested and merged are different states.
3. Recover **In progress** before anything else. If its already authorized goal is genuinely
   unfinished, resume only its recorded remaining scope and exact next action. Finish what is
   safe and practical; checkpoint a blocking dependency instead of choosing a replacement.
   If Git/CI show it is complete, clear the stale entry. Never select new work from Next tasks.
4. Read only the decisions/code needed for that recovery. Defer wider code investigation,
   source research, private review and test baselines until the relevant task needs them.
   Before any authorized private work, recheck authorization/revocations and its private
   checkpoint. Start/resume grants no new private access, spending or job searches.
5. Check app/preview state and recorded assistant-owned scratch once, to preserve the owner's
   state and recover or clean up your own abandoned work. Open or closed Jobcu is no obstacle
   to development or saved-result review. Do not ask the owner to close it as a routine step.
6. Report readiness, any recovered work and exact blocking dependency, then wait for the owner's
   task. Do not open a new goal. After a brief interruption in a prepared chat, refresh only
   state that could have changed; rerun the full recovery only if context or state was lost.

### While working

- Review and Deep improvement normally follow Start in the same chat. Reuse verified session
  state; refresh relevant Git/CI or saved evidence if it changed. If sent without preparation,
  do the minimum missing recovery, then execute the requested task; do not duplicate Start.
- Record a multi-step goal, authorized scope, steps and verification under **In progress**
  before starting it. Choose improvements proactively within a development task, considering
  the whole pipeline and the owner's priorities; Start and End do not select new improvements.
- Keep one active goal. Finish or explicitly checkpoint its blocking dependency before choosing
  another; do not accumulate unrelated unfinished changes. Checkpoint before lengthy work.
- Work on a branch in small complete steps. Checkpoint before long checks or interruptions;
  distinguish implemented, tested, pushed and merged, with the exact next action.
- Update the relevant record with the change. When reversing a decision, retain its reason and
  mark the old entry superseded. User-facing changes update the corresponding guide.
- Test meaningful behavior and failures without real documents, provider calls or job-site
  traffic. At the first substantive code/dependency/test work, establish a local full-suite
  baseline; run affected tests after changes and the full suite on the final code. Reuse a
  recorded passing check only when its relevant code, tests, dependencies and environment are
  unchanged. Readiness alone needs no test run; documentation-only work uses document checks.
- Review the complete diff and run Ruff/privacy and whitespace checks after changes. Push/open
  a PR; require Mac, Windows and privacy CI on its exact final head, then merge with a **merge
  commit**, synchronize main and verify its exact-head CI. Never infer a pass from another head.
- Claims about quality, coverage, cost and speed need measurements. Use CONTRIBUTING.md's
  private review procedure for real results.

### Ending a session

An end request prepares a **fresh chat**, not a continuation that can rely on this context.
Stop opening goals, searches, research and paid calls. Finish the current coherent step where
safe and practical (including checks, publication and CI); do not abandon a write midway or
expand scope to fix unrelated issues. If a dependency, context or usage prevents completion,
leave a recoverable branch and exact next action instead of forcing a merge.

1. Checkpoint first, before long checks: active goal and remaining authorized scope, branch/PR
   and known head, implemented/tested/pushed/merged status, failed or unrun checks, dependency
   and one exact next action. Clear **In progress** when complete; separate facts from hypotheses.
2. Update changed facts in Right now. Put durable decisions, source evidence and guide changes
   in their existing homes; save detailed private evidence only in the private data folder.
   Keep the handover short and actionable, not a transcript or duplicate change history.
3. Complete the checks/publication required above for the current step. Reuse valid recorded
   checks; do not repeat a full suite merely because the chat is ending or only the handover
   changed. Commit/push changed files, wait for exact-head CI and merge completed work when
   practical; leave synchronized clean main when possible. Preserve a recoverable branch and
   exact next action if blocked or running low. No changes means no ceremonial commit or PR;
   do not create another commit solely to record its own hash. Never label unverified work done.
4. Delete disposable private scratch copies and stop instances you started. Preserve user data
   and the owner's chosen service state. Save needed private evidence and review status in the
   private data folder before deleting scratch; keep authorization records private and intact.
   Read back the handover against Git and running services. A fresh chat must be able to find
   the files, recover preserved work and run the exact next action without this conversation.
5. Report what was saved, verified or unfinished and give direct next steps. Link to PROMPTS.md.

## Commands and conventions

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
```

`uv run jobcu` starts the app. `JOBCU_DATA_DIR` must be outside Git;
`JOBCU_NO_BROWSER=1` suppresses browser opening; `JOBCU_SELFTEST=1` checks health and stops.
Bind only to 127.0.0.1: preview port **8799**, owner app **8765**.

- Plain HTML/CSS/JS, system fonts, no CDN or external scripts/build tools; preserve CSP.
- State changes require `X-Jobcu: 1` from the local page. Keys use `keystore.KeyStore`, stay masked
  and are never logged. Logs stay private.
- Add numbered database migrations; never edit a pushed migration. Use Ruff's 100-character
  limit, check JS syntax after edits, and update `uv.lock` for dependency changes.
- Isolate sources behind `JobSource`; one failure must not stop others. Prefer original full ads;
  label summaries and unchecked conditions.
- Real tests use saved keys only through Jobcu code on an authorized private scratch copy.
  Never print/log keys or pass them as shell arguments. Delete scratch data; retain lessons in
  ENGINEERING.md. Shared code and fixtures contain fictional data only.
