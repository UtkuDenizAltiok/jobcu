# Jobcu prompts

Copy one whole block into a **new local chat in the Jobcu project**. These three prompts form
one routine. Current priorities and unfinished work live in [PROGRESS.md](PROGRESS.md), so the
next chat does not need the previous conversation. After an interruption, use Start directly.

| When | Prompt |
|---|---|
| Begin a fresh chat or recover after a cutoff | [Start a session](#start-a-session) |
| Analyse a completed search privately | [Review a search](#review-a-search) |
| Finish the current chat and prepare a fresh one | [End a session](#end-a-session) |

Start/end grant no new private access, spending or searches. Existing owner instructions still
apply; consult any private authorization record as directed by AGENTS. Never put its contents
in this file. The review prompt grants the scope it states when the owner uses it. Enter keys,
documents and queries in Jobcu, not in chat.

## Start a session

```text
Resume Jobcu in this local project as a fresh chat with no prior conversation context. Follow
AGENTS.md's "Starting, or resuming after any interruption" routine. Read Right now in
docs/PROGRESS.md; inspect all uncommitted work, Git, relevant PR/CI and app/preview state.
Preserve existing work. Recover In progress and its exact next action before choosing new work.
Verify the handover against actual state; do not assume a pushed change was tested or merged.

Continue the highest-priority authorized goal under the latest decisions. Keep one active goal;
finish or clearly checkpoint its blocking dependency before choosing another. Make complete,
reviewable improvements, test meaningful behavior, merge ready changes with merge commits and
synchronize the Mac checkout and GitHub. Read only relevant files. Checkpoint before long work.

This prompt grants no new private access, paid calls or searches. Check any existing private
authorization and review checkpoint before authorized private work; prefer saved evidence.
Respect on-demand app use and existing limits. If evidence or authority is missing, do useful
free work and identify the exact dependency. End with a verified handover and simple next steps.
```

## Review a search

Use this after Jobcu finishes. The procedure is in [REVIEW.md](REVIEW.md). Existing private
instructions may already authorize review; there is no need to repeat an approved permission.

```text
Analyse my latest completed Jobcu search on this Mac. Follow AGENTS.md's start routine and
recover any active work before beginning the review in docs/REVIEW.md. You may read my Jobcu
documents, query and saved evidence privately and add assistant ratings without overwriting
owner or legacy ratings. Check existing private authorization for any further scope or limits.
Never echo keys or publish any personal information, including real-result aggregates. Public
changes use general lessons and fictional examples; save detailed evidence privately.

Begin with the read-only saved review, flag a newer unfinished attempt, and distinguish original
search timings from correction timings and cumulative usage. On a private scratch copy outside
Git, judge full evidence against the actual documents and criteria before seeing scores.
Include every top-10 job; keep incomplete or ambiguous cases unknown rather than inventing
labels. Counts and scores do not prove accuracy or coverage.

Fix the biggest confirmed defect with general fictional regressions, verify and merge before
opening another improvement. Prefer saved evidence to another search. Use saved keys only
through Jobcu code; any focused re-score must be authorized, at medium effort, within existing
monthly/service limits and verified current prices. No fixed per-review ceiling is introduced.
Do not start a full search unless existing instructions explicitly authorize it; obey their
window and limits. Finish useful free analysis when inputs are missing. Save the private review
checkpoint before deleting scratch, preserve owner data/app state, and give simple next steps.
```

## End a session

Use this while the chat can still respond. Wait for its saved-state confirmation, then open a
**fresh local Jobcu project chat** and use Start. Ending a chat does not mean stopping an
owner-initiated Jobcu search; it can complete independently.

```text
I'm ending this Jobcu chat and will start a new chat with a fresh context window. Follow
AGENTS.md's "Ending a session" routine. Stop opening goals, investigations, searches and paid
calls. Checkpoint immediately before lengthy checks. Finish the current coherent step safely,
including necessary verification/publication/CI where practical; do not stop midway through a
write or expand scope into another feature. Preserve unrelated work and my chosen app state.

Update Right now in docs/PROGRESS.md from verified facts: active goal/scope, branch and head,
PR/CI state, implemented/tested/pushed/merged status, failed or unrun checks, unfinished work,
dependencies and one exact next action. Put durable decisions/lessons in their proper homes.
Save needed private evidence and review status outside Git before deleting disposable scratch;
keep private authorization records intact. The new chat must not need this conversation.

Run the required final checks and publish/merge completed work when possible. If access,
context, usage or a failing check prevents completion, preserve safe work on its branch and
record exactly how to resume; never force a merge or call unverified work done. Stop only
instances you started and clean up disposable state. Read back the handover against Git, CI
and running services. Report what is saved, verified or unfinished, link to docs/PROMPTS.md,
and give simple steps for the fresh chat. Do not begin another task after the handover.
```
