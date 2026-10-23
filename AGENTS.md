# Jobcu contributor rules

Jobcu runs on macOS and Windows. The owner directs product work and retains copyright and
licensing. These rules apply to human contributors and coding assistants.

## Product constraints

- Coverage and freshness come first, then accurate filtering/scoring, ease of use, cost and
  speed. Preserve recall and scores when reducing repeated work. AI defaults to medium effort.
- Electronics, hardware and power electronics are the validation priorities. Country order:
  Germany, Ireland, UK, Switzerland, Netherlands, Belgium, Italy. All 30 supported countries
  and other professions remain supported; matching regressions include fictional
  non-engineering profiles. Remote-only source expansion has lower priority.
- Provider-neutral English UI. Users choose providers/models. All AI calls use `ai/client.py`.
- Plain HTML/CSS/JavaScript, system fonts, no CDN or external scripts; preserve CSP.
- Sources implement `JobSource`; a source failure must not stop other sources. Prefer original
  full ads and label summaries, missing evidence and unchecked conditions.

## Authority and privacy

- Work within the owner's requested task. Account changes, spending and messages in the owner's
  name need instructions. The ordinary service budget is EUR30/month; paid development tests
  need separate bounded authorization. Existing additional allowances retain prior spending
  and remain separate from ordinary usage.
- Preserve owner documents, settings, keys, results, ratings and history. Reset controls do not
  authorize using them. Protect active searches when opening, closing or restarting Jobcu.
  Starting the app grants no authority to search or make paid calls.
- Private data stays outside Git and public output, including fixtures, screenshots, issues,
  PRs and CI logs. `JOBCU_DATA_DIR` must be outside every checkout. Use fictional test data.
- Before private work, check `assistant-authorization.json` in the private data folder for
  recipient, scope, limits and revocations. Authorization for one assistant does not authorize
  another. Real-data investigations use an authorized scratch copy outside every checkout;
  saved keys are used only through Jobcu code and never printed or passed as shell arguments.
- Device-local app: no hosting, user accounts, telemetry, analytics or general cloud storage.
  Necessary text goes to the chosen AI provider; local storage does not mean offline use.
  The owner's 2026-10-23 exception permits explicitly enabled temporary Google interaction
  storage for same-request recovery, with automatic cancellation/deletion and local tracking
  of outstanding requests and bills. Failed deletion can leave normal provider retention in
  effect. This does not authorize other cloud storage or provider changes.
- No job-site logins or bypasses. Respect terms, robots.txt, request limits and Retry-After.
  Blocked sources stay blocked. Verify current permissions before source changes.
- Keep LICENSE and the owner's copyright. No force pushes, history rewrites, squash or rebase
  merges. Cleanup changes current files; Git retains history. Public source is proprietary.

## Development

Use Python 3.13, uv, pathlib and explicit UTF-8. Read uncommitted diffs before editing and
preserve unrelated work. On clean main, pull with `git pull --ff-only` and sync locked
dependencies. Work on a branch with one coherent scope.

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
```

At substantive code/dependency/test work, establish or reuse a valid full-suite baseline.
Test changed behavior and failures with fictional data and mocked traffic; run the full suite
on final code. Documentation-only changes use document checks. Review the entire diff and run
Ruff, privacy and whitespace checks. Check JavaScript syntax after edits. Add numbered database
migrations without editing pushed migrations; dependency changes update `uv.lock`.

Publish a PR, require macOS, Windows and privacy CI on its exact final head, then merge with a
merge commit. Synchronize main and verify CI on that exact merge head. Implemented, tested,
pushed and merged are separate states. Do not infer live quality or availability from mocks.

Keep architecture in [ENGINEERING](docs/ENGINEERING.md), source permissions/evidence in
[SOURCES](docs/SOURCES.md),
developer setup in [CONTRIBUTING](CONTRIBUTING.md), and user help in [guides](docs/guides/).
Completed history belongs in Git and PRs. Remove disposable scratch/previews after use.

## Runtime conventions

`uv run jobcu` starts the app; the root launchers support everyday use. Bind only to 127.0.0.1:
owner app port 8765, isolated preview port 8799. `JOBCU_NO_BROWSER=1` suppresses browser opening;
`JOBCU_SELFTEST=1` checks health and stops. Isolated runs use a disposable data folder outside Git.

State-changing local requests require `X-Jobcu: 1`. Keys use `keystore.KeyStore`, stay masked,
and are never logged. Logs remain private.
