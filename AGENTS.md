# Jobcu: working instructions

Jobcu is a local job search app for macOS and Windows, with public source and private user data.
The owner develops it with ChatGPT/Codex. These instructions apply to every contributor and
assistant. Current decisions supersede the original historical concept.

## Mission and priorities

Find relevant fresh jobs, explain their fit accurately, and make the app simple to use. The first
validation focus is technical engineering, especially electronics, hardware and power electronics.
Work on countries in this order: **Germany, Ireland, UK, Switzerland, Netherlands, Belgium, Italy**
(owner, 2026-10-06). Other supported countries and professions remain supported; improvements must
be general rather than hard-coded to a person's CV or query. Include fictional non-engineering
profiles in matching changes. The 30 supported countries are in `countries.py`.

Coverage and freshness come first, then filtering and scoring, ease of use, cost, and speed.
Reduce repeated work without dropping relevant jobs or weakening scores. Every AI step defaults
to **medium** effort. The owner's service budget is up to EUR25/month; paid development tests
need authorization and a bounded budget. Existing user-set limits stay respected.

## Decision authority and communication

- The assistant owns product and engineering decisions, implementation, cleanup, review and tested
  merges. The human retains ownership, copyright and licensing decisions. Account changes,
  spending and messages sent in the owner's name need his instructions.
- Take authorized work to completion. Resolve routine details yourself and record decisions.
- Assume no programming experience. Explain outcomes plainly and finish **every response with
  simple, direct next steps** for the owner. Do not ask him to run technical work you can do.
- Never ask for a key, password, CV, cover letter or query in chat. Keys and documents are entered
  in Jobcu itself. The owner's next personal setup and 72-hour search are planned for Wednesday,
  2026-10-07; the 72 hours is a posting-date lookback, not the search's running time.

## Hard rules

1. **No job-site logins or bypasses.** Respect robots.txt, terms, request budgets and Retry-After.
   No account cookies, CAPTCHA solving or bot-protection evasion. A blocked source stays blocked;
   find a permitted alternative. Verify current terms before adding or changing a source.
2. **Device-local app.** No hosting, user accounts, telemetry, analytics or cloud storage. It
   connects to job sources, the user's selected AI provider, and optional Google Maps. Be clear
   that text needed by the chosen AI is sent to that provider; local storage does not mean offline.
3. **Private data never enters Git or public output.** Keys, documents, queries, profiles, results,
   ratings, logs and account identifiers stay outside every Git checkout. No real user details in
   fixtures, documentation, issues, PRs, screenshots or CI logs. Public findings use approved
   aggregate measurements and fictional examples. `paths.ensure_data_dir()` enforces the folder
   boundary; the commit guard adds protection but is not proof that prose contains no private data.
4. **Preserve shared history and proprietary licensing.** Keep LICENSE and the owner's copyright.
   No force push, shared-history rewrite, squash or rebase merge. Use merge commits. Public source
   does not change reuse permissions. Cleanup removes obsolete current files, not Git history.
5. **Support macOS and Windows.** Use Python 3.13, uv, pathlib and explicit UTF-8. CI verifies both.
6. **Provider neutral and English UI.** Users choose their provider and model; no built-in model
   names or preferred provider. All AI requests go through `ai/client.py`. The dated keys guide may
   recommend a provider only from a current verified source, with limitations explained.

## Where to read and record things

| Information | Home |
|---|---|
| Working rules and authority | this file |
| Current state, interrupted work, pending checks, priorities | [docs/PROGRESS.md](docs/PROGRESS.md) |
| Product and technical decisions, including superseded ones | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Verified source/service facts and terms | [docs/SOURCES.md](docs/SOURCES.md) |
| Architecture, module map and lessons | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Two canonical start/end prompts | [docs/SESSION-PROMPTS.md](docs/SESSION-PROMPTS.md) |
| Codex setup and local search-review protocol | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Everyday usage | [README.md](README.md) and [docs/guides/](docs/guides/) |
| Original concept, retained as historical reference | [docs/HANDOVER.md](docs/HANDOVER.md) |
| Detailed change history | Git commits and pull requests |

Keep non-private durable knowledge in its one repository home; link instead of duplicating.
Private investigation files and detailed real-result findings belong only in the private data
folder or a disposable scratch copy. Do not load every historical document for an unrelated edit.
Code/tests establish current behavior; the latest decision on a topic establishes intent.

## Sessions: start, work, stop

### Starting, or resuming after any interruption

1. `git status` and read any uncommitted diff before editing. Read **Right now** in PROGRESS.md.
2. On clean main, `git pull --ff-only`, then `uv sync --locked`. Never discard unexplained work.
3. Check recent Git history and GitHub checks. Complete or clearly recover **In progress** first.
4. Read architecture and decision sections relevant to the task; read SOURCES.md before source work.
   Run the local test suite once for a substantive new development session, then targeted checks
   as changes require. Tests use disposable fictional data and need no API key or approval.
5. Check for abandoned previews or private scratch copies; preserve the user's actual app and data.

### While working

- Before a task with several steps, record its goal, steps and verification under **In progress**.
- Checkpoint meaningful progress before long checks or a likely interruption. Distinguish
  implemented, tested, pushed and merged; preserve the active goal and exact next action.
- Work on a branch in small complete steps. Update the appropriate records with implementation.
- When reversing a decision, add the new reason and mark the old row superseded.
- Test meaningful behavior and failure paths. No network, real documents or provider calls in tests.
- Review the diff, run Ruff and the privacy guard, push, open a PR and wait for macOS, Windows and
  privacy checks. The assistant may merge its own tested PR with a **merge commit**.
- Do not claim search quality, coverage, cost or speed is validated without measured evidence.
  Use CONTRIBUTING.md's local review protocol for real results.

### Ending a session

1. Save a recoverable checkpoint before lengthy checks. Under **In progress**, record the active
   goal, branch/PR state, unfinished files or steps, passed/failed/unrun checks and exact next action;
   clear it when complete. Separate confirmed problems from hypotheses and future risks.
2. Update Right now, pending live checks, Waiting on the owner and Next tasks. Keep it short;
   completed history belongs in Git, not a growing diary.
3. Run `uv run ruff check . && uv run pytest`, and `uv run python tools/check_no_secrets.py --all`.
   Commit, push, wait for CI, merge finished work, and leave an updated clean main when possible.
   If context, usage or access prevents finishing, preserve known safe work on its branch and
   record the remaining checks/publication steps. Never discard work or label unverified work done.
4. Delete disposable private scratch copies and stop previews; preserve the user's Jobcu service.
5. Read back the handover against the actual repository and running services. Tell the owner what
   was saved, verified or left unfinished, and direct next steps. Canonical prompts live in
   [SESSION-PROMPTS.md](docs/SESSION-PROMPTS.md); link them instead of making conflicting copies.

## Commands

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
uv run jobcu
uv run python tools/review_search.py
```

`JOBCU_DATA_DIR` selects a private folder outside Git; `JOBCU_NO_BROWSER=1` suppresses browser
opening; `JOBCU_SELFTEST=1` starts the app, checks health and stops. Preview on 127.0.0.1:8799;
the user's app uses 127.0.0.1:8765. Never expose either on the network.

## Implementation conventions

- Plain HTML/CSS/JS, system fonts, no CDN, external scripts or build tools. Preserve CSP protections.
- State-changing API requests require `X-Jobcu: 1` from the local page. Keys use `keystore.KeyStore`,
  remain masked and are never logged. Logs themselves remain private.
- Database changes are new numbered migrations; never edit a pushed migration.
- Use Ruff (100 characters), test useful behavior, and check JS syntax after edits. Locked
  dependencies are installed with uv; dependency changes update `uv.lock`.
- Isolate each source behind `JobSource`; failure must not stop other sources. Prefer original
  employer ads and full evidence, keeping summaries and unchecked conditions labelled.
- Changes to user-facing behavior update the corresponding guide in the same commit.
- Real tests use the saved keys only through Jobcu code and an authorized private scratch copy.
  Never print, log, copy into source, or pass keys through shell arguments. Delete scratch data.
- Retain lessons in ARCHITECTURE.md. Shared source code contains fictional data only.
