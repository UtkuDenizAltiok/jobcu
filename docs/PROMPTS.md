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

## Deep improvement

Use this when you have spare assistant usage and time for a complete improvement session.
It can replace Start in a fresh chat or steer an ongoing chat; unfinished work is recovered first.
The assistant should research, choose and implement, with enough room left to verify and save.
For a shorter paste, use this command; it loads the full prompt below from the local project:

```text
Run the Deep improvement prompt in docs/PROMPTS.md in full. I have spare assistant usage and
time. Recover unfinished work first, then use your own analysis and public research to choose
and implement the most valuable justified improvement. Carry it through verification, merge
and a saved handover, and give me simple next steps.
```

Full prompt:

```text
I have spare assistant usage and time. Take responsibility for deeply understanding and
improving Jobcu: aim for an exceptional job search app through original thinking, useful
research and measured engineering. Go beyond my examples and the current backlog. Challenge
assumptions, consider better approaches and discover opportunities I have not thought of.

First follow AGENTS.md's start/resume routine. Read Right now in docs/PROGRESS.md, verify
Git, PR/CI and app/preview state, preserve work and recover In progress before choosing a new
goal. Treat a fresh chat as having no earlier context. Read relevant current decisions and
architecture, then inspect the code and tests needed to understand the search pipeline.

Trace where relevant fresh jobs can be missed, misunderstood, wrongly excluded, duplicated
or ranked from incomplete evidence. Look for repeated API work, slow steps, weak recovery,
confusing controls and unnecessary complexity. Consider new permitted sources/integrations,
original full ads, multilingual discovery, better understanding of user criteria, trustworthy
fit explanations, safe local reuse and a clean, simple interface. These are starting points,
not a complete list. Keep all supported countries and professions working; follow the current
country priorities and include fictional non-engineering cases when changing matching.

Actively use public web research and available tools where they can resolve a real question
or uncover a valuable alternative. Prefer primary documentation, original research and source
terms; verify current permissions, capabilities and prices before relying on them. Read SOURCES
before source changes. Keep research purposeful, cite dated evidence in its proper home and
distinguish facts, hypotheses and measurements. Keep private inputs out of public web queries
and shared artifacts; authorized provider processing goes through Jobcu code within its limits.
Respect robots, terms and request budgets; no logins, cookies, CAPTCHA solving or bypasses.

Form a small shortlist of the strongest opportunities. Compare expected benefit, supporting
evidence, effort, risk and verification needs. Choose the highest-value justified goal, explain
why briefly and record its steps and checks in In progress before implementing. Do the work,
not just an audit or list of suggestions. Keep one active goal; close or clearly checkpoint it
before another. Continue only while enough time/context/allowance remains to finish and verify
a coherent step. Do not accumulate half-finished features or make changes just to use allowance.

Coverage, freshness and accurate matching come before cost and speed. Do not trade quality for
savings. Never obtain savings by narrowing coverage/freshness, dropping uncertain jobs, skipping
necessary evidence, reusing stale judgements, reducing AI effort or weakening scores/criteria.
Jobcu AI steps default to medium.
Use meaningful fictional regressions and before/after measurements. For live claims, follow
REVIEW.md: counts and scores do not prove accuracy or recall. If evidence is missing, say what
is unverified, do useful free work and identify the exact inputs needed.

Respect existing private authorization, revocations, provider/service budgets and app limits.
This prompt adds public research and engineering authority, not private access or paid-test
permission. Prefer saved search evidence. Start a new job search only if existing authority
allows it, it has a clear benefit and its window is 24 hours. Preserve the owner's chosen app
state; use isolated previews and stop instances you start. Keep private review records outside
Git and never publish personal information, keys, documents, queries, results or logs.

Implement in complete steps, update the relevant records/guides, review the diff and run the
required checks. Push/open a PR, wait for final-head Mac/Windows/privacy CI, merge ready work
with a merge commit and synchronize the Mac checkout and GitHub. Do not call untested work
complete or promise perfection. Before ending or running low, follow the ending routine:
finish the current coherent step where practical, save exact recovery steps, clean disposable
state and read back the handover. Finish with what improved, evidence and limits, anything
unfinished, and simple direct next steps. Link to docs/PROMPTS.md for the next fresh chat.
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
