# Jobcu prompts

Copy the appropriate whole block into the local Jobcu project chat. These are the only reusable
prompts; dates, priorities and unfinished work live in [PROGRESS.md](PROGRESS.md).

| When | Prompt |
|---|---|
| Begin a chat or recover after a cutoff | [Start a session](#start-a-session) |
| Analyse a completed search privately | [Review a search](#review-a-search) |
| Finish before closing the chat or reaching a limit | [End a session](#end-a-session) |

Start/end prompts grant no new private-data access, paid calls or full searches. The review
prompt grants its stated permission only when you use it. Enter keys and documents in Jobcu.

## Start a session

```text
Resume Jobcu from this local project. Follow AGENTS.md's "Starting, or resuming after any
interruption" routine. Read Right now in docs/PROGRESS.md, verify Git, PR/CI and app/preview
state, preserve existing work, and recover In progress before choosing new work.

Continue the highest-priority authorized work under the latest decisions. Implement, verify
and merge ready changes; keep the Mac checkout and GitHub synchronized. Read only relevant
files. This prompt grants no new private-data access, paid calls or full searches. Respect
on-demand app use. If real results are missing, do useful free work and identify the needed
inputs. Checkpoint progress and finish with simple, direct next steps.
```

## Review a search

Use this after Jobcu finishes. The procedure is in [REVIEW.md](REVIEW.md).

```text
Analyse my latest completed Jobcu search on this Mac. Follow AGENTS.md's start routine and
then docs/REVIEW.md. You may read my local documents, query and results privately and rate
the saved quality sample on my behalf. Begin with the read-only aggregate review. Never
print or publish my profile, query, documents, keys, job list or ratings; public records use
anonymous aggregate findings and fictional examples only.

Fix confirmed defects with fictional regressions, verify and merge. Use saved keys only
through Jobcu code for a focused re-score at medium effort, within my existing monthly budget
and configured service limits, using verified current prices. There is no fixed per-review
or per-search money ceiling. If prices are missing, finish the free analysis first and give
me one clear next step. Do not start another full search or overwrite my
ratings automatically. Delete disposable private scratch data and end with simple next steps.
```

## End a session

Use this while the chat can still respond. Wait for its saved-state confirmation; begin the
next Local project chat with Start a session. After a cutoff, use Start a session directly.

```text
I'm ending this Jobcu session. Follow AGENTS.md's "Ending a session" routine. Stop starting
new work and save a recoverable checkpoint before lengthy checks.

Update Right now in docs/PROGRESS.md from verified facts: active goal and scope, changes,
unfinished work, branch/PR state, checks, owner inputs and exact next action. Distinguish
implemented, tested, pushed and merged. Keep durable knowledge in its proper home and
private evidence outside Git/public output. Preserve unrelated work.

Verify and publish completed work when possible. Otherwise save safe work on its branch
and record remaining checks/publication steps; do not label unverified work done. Stop
instances you started, delete disposable scratch data, and preserve my data and chosen
app state. Read back the handover against Git and services. Report what is saved or
unfinished and give simple steps for the next chat.
```
