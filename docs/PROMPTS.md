# Jobcu prompts

Copy one whole block into a **local chat in the Jobcu project**. Start, Review and End form
the session routine; Deep improvement adds a research and implementation session when you
have spare assistant usage and time. Start and Deep improvement also work in a fresh chat.
Current priorities and unfinished work live in [PROGRESS.md](PROGRESS.md), so the next chat
does not need the previous conversation. After an interruption, recover with Start.

| When | Prompt |
|---|---|
| Begin a fresh chat or recover after a cutoff | [Start a session](#start-a-session) |
| Analyse a completed search privately | [Review a search](#review-a-search) |
| Use spare assistant usage for research and complete improvements | [Deep improvement](#deep-improvement) |
| Finish the current chat and prepare a fresh one | [End a session](#end-a-session) |

Start, Deep improvement and End grant no new private access, spending or job searches.
Deep improvement authorizes public web research and engineering work. Spare assistant usage
is separate from Jobcu's API/provider allowance and service budget. Existing owner instructions
still apply; consult any private authorization record as directed by AGENTS. Never put its
contents in this file. Review grants the scope it states when the owner uses it. Enter keys,
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
Assess the whole pipeline proactively in active development sessions. Optional Settings →
Review results is not homework for the owner. Do not reset owner data unless explicitly asked
to perform that deletion; adding or testing reset controls is not permission to use them on it.
```

## Review a search

Use this after Jobcu finishes. Follow the
[private review procedure](../CONTRIBUTING.md#review-a-completed-search).
Existing private instructions may already authorize review; do not repeat an approved permission.

```text
Analyse my latest completed Jobcu search on this Mac. Follow AGENTS.md's start routine and
recover active work before using CONTRIBUTING.md's "Review a completed search" procedure.
You may read my Jobcu documents, query and saved evidence privately and add assistant ratings
without overwriting
owner or legacy ratings. Check existing private authorization for any further scope or limits.
Never echo keys or publish any personal information, including real-result aggregates. Public
changes use general lessons and fictional examples; save detailed evidence privately.

Begin with the read-only saved review, flag a newer unfinished attempt, and distinguish original
search timings from correction timings and cumulative usage. On a private scratch copy outside
Git, judge full evidence against the actual documents and criteria before seeing scores.
Include every top-10 job; keep incomplete or ambiguous cases unknown rather than inventing
labels. Counts and scores do not prove accuracy or coverage.
Use your own independent judgement; do not require me to fill in Settings → Review results
(formerly Score check). Ratings are evaluation evidence, not automatic model training.

Fix the biggest confirmed defect with general fictional regressions, verify and merge before
opening another improvement. Prefer saved evidence to another search. Use saved keys only
through Jobcu code; any focused re-score must be authorized, at medium effort, within existing
monthly/service limits and verified current prices. No fixed per-review ceiling is introduced.
Do not start a full search unless existing instructions explicitly authorize it; obey their
window and limits. Finish useful free analysis when inputs are missing. Save the private review
checkpoint before deleting scratch, preserve owner data/app state, and give simple next steps.
```

## Deep improvement

Use this when you have spare assistant usage and time for a complete improvement session.
Copy this one block into an ongoing or fresh local Jobcu chat; unfinished work comes first.

```text
Deeply analyse and improve Jobcu using your own judgement, original ideas and useful research.
Aim for an exceptional job search app. Go beyond my examples and the current backlog: question
assumptions and investigate better approaches, including ideas I have not thought of.

Follow AGENTS.md's start/resume routine. Recover Right now and In progress in PROGRESS, verify
Git/PR/CI and app state, and preserve existing work. A fresh chat has no earlier context.
Read relevant ENGINEERING sections and inspect the code/tests needed to trace the pipeline;
read SOURCES before source work. Keep setup, usage and contribution guidance detailed.

Investigate where fresh relevant jobs are missed, misunderstood, wrongly excluded, duplicated
or ranked from incomplete evidence. Consider new permitted sources, multilingual discovery,
original full ads, better understanding of user criteria, accurate fit explanations, repeated
API work, safe local reuse, slow steps, recovery and a clean, simple interface. These examples
are not a limit: discover and compare alternatives yourself. Simplify workflows, files and
systems where that removes unnecessary work; keep one home for each fact and one prompt per task.
Make this whole-pipeline assessment routine during active development, without requiring me
to name every defect or complete the optional review screen. Preserve my data unless I explicitly
ask you to reset it. Update the relevant guides, decisions and existing prompts with our decisions.

Actively use public web research and available network/tools to resolve important questions
and uncover opportunities. Prefer primary documentation and original research; verify current
terms, capabilities and prices. Record dated evidence in SOURCES and distinguish facts from
hypotheses. Keep private inputs out of public web queries and shared output; authorized provider
processing goes through Jobcu. Respect the access rules, request budgets and limits in AGENTS.

Make a small shortlist ranked by expected benefit, evidence, effort, risk and verification needs.
Choose the strongest justified goal, explain why briefly, record steps/checks in In progress and
implement it. Do not stop at an audit or suggestions. Keep one active goal; finish or checkpoint
its blocking dependency before another. Leave enough allowance, time and context for checks,
publication and recovery; avoid accumulating unfinished features or working just to use allowance.

Never trade quality for cost or speed. Preserve coverage, freshness, necessary evidence and
accurate criteria/scoring; do not drop uncertain jobs, reuse stale judgements or lower AI effort
to claim savings. Jobcu AI defaults to medium. Support every existing country/profession and use
fictional non-engineering cases when changing matching. Compare meaningful behavior and
performance before/after; use CONTRIBUTING's private review procedure for live claims. Counts
and scores are not proof of accuracy/recall. Identify missing evidence and do useful free work.

Respect standing private authorization and revocations, existing service budgets and app limits.
Spare assistant usage grants no extra private access or paid testing. Prefer saved evidence;
start a new job search only within existing authority, for a clear benefit, and with 24 hours.
Preserve the owner's app state, keep private records outside Git and stop your isolated previews.

Follow AGENTS for verification, diff review, final-head Mac/Windows/privacy CI, merge commits
and synchronized Mac/GitHub state. Update the relevant records/guides. Before ending or running
low, finish the coherent step where practical and save an exact fresh-chat handover. Report what
improved, evidence and limits, unfinished work, and simple direct next steps; link to PROMPTS.
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
