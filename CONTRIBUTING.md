# Contributing to Jobcu

Jobcu's source is **publicly readable** and **not open source**; the owner's proprietary
license remains in place. User data stays private on each person's computer. By contributing,
you agree that
your changes become part of Jobcu under its [LICENSE](LICENSE). Everyday users need only the
[README](README.md).

Everything about how Jobcu is built and worked on is in **[AGENTS.md](AGENTS.md)**, the one
rulebook for people and AI assistants alike. This page only gets you started.

## Continuing development with ChatGPT (2026-10-06)

The owner (Utku) now develops Jobcu directly with **ChatGPT/Codex on his restored Mac**.
The assistant makes product and technical decisions and carries tested changes through review
and merge; account changes, spending and licensing remain the owner's decisions. Where things stand
is in [docs/PROGRESS.md](docs/PROGRESS.md) ("Right now": state, what to verify, what waits on
the owner, next tasks in order); why things are as they are is in
[docs/DECISIONS.md](docs/DECISIONS.md); facts about every source and service are in
[docs/SOURCES.md](docs/SOURCES.md). To start:

1. Clone the public repository. Contributors fork it and open a pull request; only authorized
   maintainers need write access. Never upload any personal Jobcu data (AGENTS.md, hard rule 5).
2. Set up your computer as below, and run `uv run pytest` once: all tests must pass.
3. Open the repository in an assistant that can read and edit files and run commands (ChatGPT's
   coding agent Codex, or any of those listed below). Such assistants read `AGENTS.md` by
   themselves; `CLAUDE.md` only points to it. A chat-only assistant needs AGENTS.md and
   docs/PROGRESS.md pasted in.
4. Paste the start prompt below. For real tests, put your own AI key in your own Jobcu's
   Settings (never in a chat); the owner's CV and data stay on his Mac.

## Set up

Mac: `brew install git uv gh` · Windows: `winget install --id Git.Git -e`,
`winget install --id astral-sh.uv -e`, `winget install --id GitHub.cli -e`

```bash
gh auth login
gh repo clone UtkuDenizAltiok/jobcu          # with write access (or: gh repo fork … --clone)
cd jobcu
uv sync
git config core.hooksPath .githooks          # safety check before every commit
uv run pytest && uv run ruff check .
uv run jobcu
```

## Cloud sessions with Claude Code (optional, claude.ai/code)

Only for Claude Code's cloud. One-time setup; how sessions work there is in AGENTS.md, "Working
in a cloud session". Other assistants' cloud agents follow the same rules with their own setup.

1. At claude.ai, **Settings → Usage**: check your credit balance. If paid **Usage credits** are on,
   set the monthly spend limit to the lowest amount, so nothing beyond a credit is charged.
2. At claude.ai/code, connect GitHub, and install the **Claude GitHub App** on this repository
   only ("Only select repositories").
3. In the environment menu, open **Default**'s settings (the icon next to it), set **Network
   access** to **Full**, and save.
4. Recommended: in the same dialog, **API credentials → Add credential** with a separate key of
   your AI provider, so sessions can test with a real AI without seeing the key. For Gemini:
   **Allowed websites** `generativelanguage.googleapis.com`, header **Name** `x-goog-api-key`,
   **Prefix** empty, the key as **Value**, then **Connect**. Never paste a key into a chat.

Each session: pick this repository and branch **main**, the model and effort you want, the mode
**Auto** (or **Accept edits**), and paste the start prompt below. Run one session at a time.

Optional, to test with your own CV (DECISIONS.md, 2026-09-24 night): attach your CV and cover
letter with the **+** and add this paragraph to the start prompt:

```text
Attached are my real CV and cover letter, for testing only. Save them only in a scratch folder
outside the repository and delete it when you finish. Never put them, or any personal detail from
them, in the repository, a commit, a branch name, a pull request, an issue, a comment, a test or
CI output: friends and others with access to the repository must never see them. Use them as the
main test person with the AI credential, next to made-up people from other fields: check how Jobcu
reads them, which jobs it finds for me in my priority countries and how it scores them, and
improve what falls short.
```

## Working with an AI assistant

Any capable AI coding assistant works: Claude Code (on your computer, or in a cloud session at
claude.ai/code), Codex, Gemini CLI, Cursor, GitHub Copilot, Aider, or a chat assistant such as
ChatGPT, Gemini, Grok or Kimi. Open the project in your assistant and paste these prompts as
they are. Cloud sessions need a one-time setup: see AGENTS.md, "Working in a cloud session".

**At the start of every session:**

```text
You are joining Jobcu, a local job search app with public code and private user data. Read
AGENTS.md in full and follow it: it is the
project's rulebook. Then do what its section "Starting, or resuming after any interruption" says:
read "Right now" in docs/PROGRESS.md and check the repository's real state. Tell me in plain words
where the project stands, anything unfinished or needing a check, and what is waiting on me.
Then carry on with the mission and the next tasks in PROGRESS.md: decide the technical details
yourself, research where needed, and work carefully in small, tested, recorded steps. Ask me only
about decisions that are mine (AGENTS.md). You may merge your own pull requests with a merge
commit once GitHub's tests pass. If you can't open files yourself, ask me to paste AGENTS.md and
docs/PROGRESS.md.
```

**Before you stop, or when the conversation is getting full:**

```text
Wrap up for a fresh session: follow the section "Ending a session" in AGENTS.md. Stop at a safe
point, make sure everything important from this session is recorded in the repository (not only
in this chat), check the tests, commit and push. Merge your pull request with a merge commit once
GitHub's tests pass. Then tell me in a few lines what was done, what comes
next, what is waiting on me, and whether it's safe to start a new session.
```

**Check my latest search (only on your own computer, never in a cloud session):**

```text
Check my latest search: this session runs on my own computer. First follow "Starting, or
resuming after any interruption" in AGENTS.md. With my permission, work on a scratch copy of my
Jobcu data folder (JOBCU_DATA_DIR), and do three things:
1. Study my latest search: the results, the scores and their limits, the places and conditions,
   the notes and the sources, against "Verify before relying on" and the plan in PROGRESS.md.
2. The quality set, on my behalf: rate the ads Jobcu kept for the score check (good, okay or
   poor, with blockers), until 30-50 are rated over time. Judge each full ad against my CV and
   cover letter as a careful recruiter would, before looking at Jobcu's score. Save the ratings
   in my real data folder with quality.rate(..., by="assistant"), then run
   tools/score_check.py --rescore (the stored scores are from when each ad was collected).
3. The coverage list, on my behalf: search the web for 15-25 fresh, real jobs that fit my CV in
   my priority countries (employers' own sites and job boards, including LinkedIn and StepStone
   pages as search engines show them), and run tools/coverage_test.py with them. Before counting
   a job as missed, check its date on the employer's own site: LinkedIn shows reposts as new.
Record what you find, with examples, in docs/PROGRESS.md (decisions in DECISIONS.md, source facts
in SOURCES.md), never my CV or other personal details. Delete the scratch copy, check the tests,
commit and push. Then fix what you found, most important first, in small tested steps, and tell
me in plain words what you found, what you fixed and what comes next.
```

**When a cloud credit is nearly used, before going back to local sessions:**

```text
Final handover: my cloud credit is nearly used, and I'll continue in a local session on my
computer. Stop new work at a safe point and follow "Budget and the final handover" in AGENTS.md
(section "Working in a cloud session") and "Ending a session": a complete check-up, everything
merged with merge commits, and "Right now" in docs/PROGRESS.md rewritten for a local session.
Then tell me in plain words what was done, what's next, what is waiting on me, and that it's
safe to continue locally.
```

## Changes

Work on a branch, keep every change tested (`uv run ruff check . && uv run pytest`), and open a
pull request (`gh pr create`). GitHub runs the tests on macOS and Windows; the owner approves
merges, always as a merge commit (never squash or rebase). Never force-push or rewrite history.
