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
  messages in the owner's name need his instructions. The service budget is up to EUR25/month;
  paid development tests need authorization and a bounded budget. Respect existing user limits.
- Complete authorized work and record routine decisions. Keep the Mac checkout and GitHub current
  through the session routine. Local means execution on the Mac; Git publication is versioned.
- Explain plainly, assume no programming experience, and finish **every response with simple,
  direct next steps**. Do technical work yourself. Never request keys, passwords, documents or
  private queries in chat; the owner enters them in Jobcu.
- Jobcu runs on demand: double-click **Start Jobcu.command**, then close the terminal and choose
  **Terminate** if asked. Do not automatically start or leave it running. Use self-tests or
  isolated previews; stop instances you started and respect the owner's chosen app state.

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

### Starting, or resuming after any interruption

1. Check `git status` and all uncommitted diffs; read **Right now** in PROGRESS.md. Preserve work.
2. On clean main, `git pull --ff-only`, then `uv sync --locked`. Never discard unexplained changes.
3. Check recent commits, relevant PR/CI state and app/preview state. Recover **In progress** first.
4. Read relevant architecture/decisions; read SOURCES before source work. Run the local suite once
   for a substantive session, then targeted checks as needed. Tests use fictional data and no network.
5. Check abandoned previews/scratch copies; preserve user data and the owner's chosen app state.
6. Treat a new chat as having no prior conversation context. Recover one active goal from the
   handover and actual Git/CI state; do not start several replacements. Before authorized
   private review, consult the private authorization and review checkpoint without publishing
   their contents. Recheck scope and revocations; resuming or ending grants no extra authority.

### While working

- Record a multi-step goal, steps and verification under **In progress** before starting it.
- Keep one active goal. Finish or explicitly checkpoint its blocking dependency before choosing
  another; do not accumulate unrelated unfinished changes. Checkpoint before lengthy work.
- Work on a branch in small complete steps. Checkpoint before long checks or interruptions;
  distinguish implemented, tested, pushed and merged, with the exact next action.
- Update the relevant record with the change. When reversing a decision, retain its reason and
  mark the old entry superseded. User-facing changes update the corresponding guide.
- Test meaningful behavior and failures without real documents, provider calls or job-site traffic.
- Review the diff; run Ruff/privacy checks; push/open a PR; wait for Mac, Windows and privacy CI.
  The assistant may merge its own tested PR with a **merge commit**.
- Claims about quality, coverage, cost and speed need measurements. Use CONTRIBUTING.md's
  private review procedure for real results.

### Ending a session

An end request prepares a **fresh chat**, not a continuation that can rely on this context.
Stop opening goals, searches, research and paid calls. Finish the current coherent step where
safe and practical (including checks, publication and CI); do not abandon a write midway or
expand scope to fix unrelated issues. If a dependency, context or usage prevents completion,
leave a recoverable branch and exact next action instead of forcing a merge.

1. Checkpoint first. Record the active goal, branch/PR and head, unfinished work,
   passed/failed/unrun checks
   and exact next action under **In progress**. Clear it when complete; separate facts from hypotheses.
2. Refresh Right now, live checks, owner inputs and next tasks. Keep it short; history belongs in Git.
3. Run `uv run ruff check . && uv run pytest` and `uv run python tools/check_no_secrets.py --all`.
   Commit, push, wait for CI and merge completed work. Leave updated clean main when possible.
   If access/context/usage prevents completion, preserve safe work on its branch and record what
   remains. Never discard work or label unverified work done.
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
