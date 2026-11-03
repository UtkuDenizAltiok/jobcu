# Working on Jobcu (for AI coding agents and new developers)

Jobcu is a local job-search app: a Python (FastAPI) server with a plain browser UI. It collects job ads from many
sources, removes duplicates, filters them by the person's conditions (places, travel time, dates), scores the rest
against their CV with the AI provider they chose, and shows cards with links to apply. Everything private stays on
the person's computer.

## Read first
1. [README](README.md): what Jobcu does for its user.
2. [CONTRIBUTING](CONTRIBUTING.md): setup, checks, private-data boundary.
3. [ENGINEERING](docs/ENGINEERING.md): architecture, search pipeline, module map, tools.
4. [SOURCES](docs/SOURCES.md): every job source, its terms, robots rules and measured behaviour.
5. [ROADMAP](docs/ROADMAP.md): planned work in priority order.

If you work for Jobcu's owner on their computer, their private notes are in Jobcu's data folder
(`~/Library/Application Support/Jobcu/assistant-reviews/`): start at its README.md. Nothing from there goes into
this repository.

## Checks before every commit
```bash
uv run ruff check .
uv run pytest -q
uv run python tools/check_no_secrets.py --all
git diff --check
```
Tests use fictional data, scripted AI providers and mocked HTTP, and need no keys. `tests/test_docs.py` fails when
a document links to a missing file or section, or when the module map in ENGINEERING doesn't list a module or tool.

## Rules that are part of the product
- **Privacy.** The repository is public. No keys, settings, CVs, saved searches, logs or anything about a real user
  in code, tests, commit messages or PR text: use fictional examples. Private data lives outside the checkout
  (`paths.ensure_data_dir()`).
- **Respect every source.** Follow robots.txt and terms; never bypass logins, human checks or blocks, never imitate
  a browser to get past a refusal, and never request an address a site disallows. Sites whose terms forbid reading
  (LinkedIn, Indeed and others in `applylink.NEVER_READ`) are never read. [SOURCES](docs/SOURCES.md) records each
  decision.
- **No automatic visits to application links.** Many links are paid per click. Jobcu reads a middleman page only
  when the person clicks it (`applylink.py`), never during a search.
- **Keep a job unless its removal is certain.** A job leaves the list only for a route that can't take the person's
  application at all (CV-Library, which accepts UK residents only) or a link the person marks unusable. A page that
  is gone or refuses the person's country is explained on click, and the job stays; for good jobs, the employer's own
  posting is looked up online (`livepostings.py`).
- **Every AI provider must work well.** All AI calls go through `ai/client.py`. Fix a provider's problem generically
  (streaming, declined answers, missing reasoning), never by tuning prompts to one model. A model's claim needs
  grounding: quotes are checked against the ad text, and addresses must appear in the provider's own web sources.
- **Quality and coverage come first**, then cost, then speed. Never lower coverage silently. Paid services are never
  capped by Jobcu: limits only tell the person. Free allowances are shared over the searches the person plans.
- **Jobcu finds and judges jobs itself.** Features that need the person to paste ads or do Jobcu's work aren't
  wanted.

## Conventions
- Match the surrounding code: comments explain why, in plain English; names say what things are.
- User-facing text is plain and short (the person isn't technical). No jargon in the UI.
- Tests are named as sentences about behaviour (`test_an_answer_from_memory_finds_nothing_and_is_asked_again_next_time`).
- Update docs in the same PR as the code: the module map in ENGINEERING, a source's record in SOURCES, the
  roadmap when an item is done. Database changes are new entries at the end of `db.MIGRATIONS`.
- One topic per branch and PR. Describe the evidence (what was measured, on which data) in the PR. The repository
  merges with merge commits; GitHub runs the tests on macOS and Windows and the privacy guard.
