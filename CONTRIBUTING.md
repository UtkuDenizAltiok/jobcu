# Develop Jobcu

Follow [AGENTS.md](AGENTS.md). The assistant leads implementation, cleanup, review and tested
merges; the human owns copyright and licensing. User data stays outside Git.

## Local project

Use the existing checkout. In Codex, add it as a local project, select it as the primary folder,
and start a Local chat. The folder supplies the code and AGENTS.md; no source or chat upload is
needed. [Official project documentation](https://learn.chatgpt.com/docs/projects), checked 2026-10-07.

The checkout is connected to GitHub. Safe pulls, commits, tests, pushes, CI and merge commits
publish changes; individual edits are not mirrored instantly. The launcher checks for updates
on clean main and warns if it must use the installed version.

## Sessions

All reusable prompts live in [PROMPTS.md](docs/PROMPTS.md):

- [Start a session](docs/PROMPTS.md#start-a-session), including recovery after a cutoff.
- [Review a completed search](docs/PROMPTS.md#review-a-search), with explicit private-access and spending limits.
- [End a session](docs/PROMPTS.md#end-a-session), before closing the chat or reaching a usage limit.

The private-results procedure is in [REVIEW.md](docs/REVIEW.md). Everyday setup and searches
are in the [user guides](README.md#use-jobcu).

## Development commands

For another computer, install Git and uv and clone the repository. The assistant runs:

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
```

Tests use disposable fictional data and need no API keys. Use the
[architecture and tool map](docs/ARCHITECTURE.md#project-layout) for targeted work.
Work on a branch, review the diff, open a PR and wait for Mac, Windows and privacy CI.
Merge with a merge commit; preserve shared history. Other contributors' PRs require review.
