# Jobcu session prompts

These are the two canonical defaults. Copy the whole relevant text block into the Jobcu chat;
no dates, branch names or priorities need editing. Current facts belong in PROGRESS.md, so the
prompts keep working as the project changes. They replace the earlier start/wrap-up prompts.

Use the ending prompt while the session can still respond, before closing the chat or exhausting
usage. Wait for its handover confirmation. Then start a new **Local** chat in the same Jobcu
project and paste the starting prompt. After an unexpected cutoff, use the starting prompt
directly; it recovers from the saved files and Git rather than assuming a completed handover.

## End a session

```text
I'm ending this Jobcu session. Follow AGENTS.md's "Ending a session" routine. Stop starting new
work and save a recoverable checkpoint before lengthy checks.

Update Right now in docs/PROGRESS.md from verified facts: the active objective and latest scope,
what changed, what remains unfinished, branch/commit and PR state, checks passed/failed/not run,
known problems and uncertainties, owner input still needed, and the exact next action with
relevant files or commands. Distinguish implemented, tested, pushed and merged. Keep it concise;
completed detail belongs in Git. Record durable decisions, source facts and architecture lessons
in their existing homes. Keep private evidence outside Git and public output; reference it safely.

Review the diff and preserve unrelated work. Verify and merge completed changes under the existing
rules when time allows. If context, usage, checks or access prevent completion, save known safe
work on its branch, clearly label any unverified checkpoint, and record the remaining verification,
publication or merge steps. Never discard work or claim success to create a clean-looking ending.

Stop previews and app instances you started, and remove disposable scratch copies. Respect the
owner's chosen running/stopped app state and preserve user data.
Read back the handover and confirm it matches the actual repository, checks and running services.
End with a short saved-state report, anything incomplete, and simple steps for opening the next chat.
```

## Start a session

```text
Resume Jobcu from this local project. Follow AGENTS.md's "Starting, or resuming after any
interruption" routine. Read Right now in docs/PROGRESS.md, then verify the actual Git status,
uncommitted diff, branch, recent commits, relevant PR/CI state and running app or previews.
Preserve existing work. Update from origin only when safe; resolve recorded work before choosing
a new task. A new chat does not mean a fresh checkout or a completed previous session.

Use the latest user instructions and recorded decisions to establish the current objective,
constraints, completed work, unfinished work, known problems and next action. Treat stale claims
and unverified results as uncertain. Read only the architecture, decisions, sources and code
needed for that action; don't reload the entire history or repeat completed work without reason.

Then continue the highest-priority authorized work. Lead product and engineering decisions,
implement and verify useful improvements, and merge ready PRs under the project rules. Preserve
my ownership, license and private data. Respect recorded permissions and spending limits; this
prompt adds no new paid calls or full searches. If personal setup or real results are missing,
continue useful free work and clearly identify what needs those inputs. Ask only for a decision
or authorization that the existing context cannot resolve.

Checkpoint meaningful progress as you work, keep the project ready for another handover, and
finish every response with simple, direct next steps.
```

The result-review prompt remains in [CONTRIBUTING.md](../CONTRIBUTING.md#review-the-latest-search-locally);
it adds the specific private-data and bounded re-score authorization for that task. The default
starting prompt preserves existing authorization without granting that access automatically.

The workflow uses repository instructions and selective context. References checked 2026-10-06:
[official OpenAI instructions documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [official prompting guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
