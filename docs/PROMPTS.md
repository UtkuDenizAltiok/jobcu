# Jobcu prompts

In a **local chat in the Jobcu project**, paste Start once, then Review, Deep improvement or
your own task. Use End before closing the chat. Start also recovers an interrupted chat;
it prepares the assistant and can finish recorded unfinished work, but never picks a new task.
Review and Deep improvement use that prepared session without repeating startup.

| When | Prompt |
|---|---|
| Prepare a fresh chat or recover after an interruption | [Start a session](#start-a-session) |
| Improve Jobcu using the latest completed search | [Review a search](#review-a-search) |
| Find and implement improvements without needing a new search | [Deep improvement](#deep-improvement) |
| Finish or park work and prepare a fresh chat | [End a session](#end-a-session) |

[AGENTS](../AGENTS.md#sessions) is the single home for recovery, checks and publication rules;
[PROGRESS](PROGRESS.md#right-now) holds the handover. Start, Deep improvement and End grant
no new private access, paid calls or job searches. Review grants only the private scope stated
in its block. Standing authorization, revocations and service limits still control further
work; spare assistant usage is separate from Jobcu's provider budget. Enter private inputs in
Jobcu, not chat. All four prompts preserve your data and work whether Jobcu is open or closed.

## Start a session

Use this once in a fresh chat. After a cutoff, use the same prompt to recover existing work.

```text
Prepare this local Jobcu chat for my next task. A fresh chat has no previous conversation
context. Follow AGENTS.md's "Starting, or resuming after any interruption" routine: read
Right now in docs/PROGRESS.md and verify the handover against uncommitted work, Git and
relevant PR/CI. Preserve existing work and my chosen app state; read only what recovery needs.

If In progress contains an already authorized unfinished goal, recover its exact next action
and finish safe, practical remaining steps within that scope. If blocked, save the dependency
and exact next action. Do not select a new goal, investigate new improvements or act on
the backlog.
If the previous goal is complete, clear its stale checkpoint. Do not repeat unchanged checks
or begin a private review, paid call or job search just to prepare the chat.

Report briefly that the chat is ready, any recovered work and any blocking dependency. Then
wait for my next task. Start is preparation and recovery, not a new improvement task.
```

## Review a search

After Start, use this when a new Jobcu search has finished. The assistant reviews saved evidence
and develops improvements; you do not need to fill in the optional review screen or close Jobcu.
The detailed method lives in [CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).

```text
Review my latest completed Jobcu search and improve the app from what you find. Use this
prepared session; refresh only changed state, without repeating Start. Recover or checkpoint
an existing active goal before opening this one. Follow CONTRIBUTING.md's "Review a completed
search" procedure within AGENTS.md's rules.

You may privately read my Jobcu documents, query and saved search evidence and add assistant
ratings while preserving owner/legacy ratings. Check standing authorization and revocations
before private work or calls. Keep detailed evidence and the review checkpoint outside Git;
do not publish personal information or real-result aggregates, or put private inputs in web
queries. Preserve my data and app state; use an authorized isolated copy for investigations.

Start with the read-only saved review; flag a newer unfinished attempt. Judge full evidence
against the actual documents and criteria before seeing scores, including every top-10 job.
Use CONTRIBUTING's balanced 30–50-ad review, not only the top 10; reuse unchanged saved
judgements and distinguish a reviewed sample from a whole-results or coverage claim.
Investigate freshness, misses, duplicates, exclusions, requirements, travel evidence, ranking
and explanations across the whole pipeline. Distinguish original search timing from corrections
and cumulative usage. Keep missing evidence unknown; counts and scores alone do not prove
accuracy or recall.
Use recorded run boundaries rather than screenshot times to measure duration. Separate useful
evidence work, provider failures/retry waits and time waiting for my answers before changing
limits or removing checks. Preserve complete answers and diagnose the failure path.
Separate service limits from missing evidence before recommending more paid usage.
Before provider changes, verify permitted app use, actual reasoning/tool support and token-based
windows; coding benchmarks and advertised request counts do not establish matching quality.
Do not equate integration ease or a vendor's effort labels with model quality. Evaluate
credible alternatives fairly, verifying native reasoning controls and independent fit outcomes.
Compare the complete current catalogue, shared token allowances and direct API alternatives;
preserve fresh cited research when separating main and research providers. Reuse only evidence
whose rights, request identity and freshness permit it, not stale route or scoring judgements.
Make technical model/source decisions yourself and give me simple account/setup steps.
Prefer one provider/model when it meets the task; extra models are options, not user homework.
Do not recommend a subscription from model count alone; verify its intended app use and shared
allowance, and implement clarity rather than repeatedly hand unresolved choices back to me.
Separate model capability, hosted features, current Jobcu integration and permitted use.
Do not reject a provider from shared limits alone; calculate daily/monthly demand and sensitivity.
Treat original hosted-tool reports as leads to verify, not universal support or fee guarantees.
Before recommending spending, compare fixed subscription fees with the complete direct API bill,
including hosted search calls and retrieved content. Use saved usage when authorized, include
thinking/tool charges and shared allowances, and distinguish a ceiling from an invoice or cap.
Ask me only for a necessary new spending ceiling or account instruction, not to choose models.
Use your own judgement and relevant public primary research; optional user ratings are not
homework or automatic model training.
Check useful structured fields already returned before adding research requests. Compare
discounted same-model processing with other models, including latency/recovery and full bills;
equal-token arithmetic is a scenario, not proof of equal quality or actual demand.
Check discovery refresh provenance: failed/blank country lookups must remain retryable,
completed countries/employers must survive partial failures, and a small result count is not
proof of absent employers. A reachable/internal portal API is not permission to collect it.

Assess coverage and the contribution of existing and potential sources/search methods: unique
fresh relevant jobs, original evidence, country/profession gaps, reliability and request cost.
Read SOURCES and verify terms before source changes. Add useful permitted methods, improve
weak ones, or replace/remove methods shown to add no useful value or harm results. Account
for unique jobs, better evidence and backup value before removal; missing evidence or temporary
failures do not prove no value.

Rank a small shortlist by benefit, evidence, effort, risk and verification needs. Choose the
strongest justified improvement, record steps/checks in In progress, and implement it with
general fictional regressions. Compare meaningful behavior before/after, state evidence limits,
update the relevant records/guides and verify/publish under AGENTS. Do not stop at an audit.
Prefer saved evidence; no new search or paid test is authorized by this prompt. Further calls
need existing explicit scope and budget. If blocked, complete useful free work and checkpoint
the exact dependency. An authorized new search must use 24 hours and existing frequency limits.
Finish with what improved, what remains and simple next steps.
```

## Deep improvement

After Start, use this when you want development time without doing another search. A newly
completed search is not required; older saved evidence can help within existing authorization.

```text
Deeply analyse and improve Jobcu using your own judgement, original ideas and useful research.
Use this prepared session; refresh only changed state, without repeating Start. Recover or
checkpoint an existing active goal first. A new search is not required; use public evidence,
code/tests and any older saved evidence already authorized for private review.

Question assumptions across the whole app and pipeline, beyond my examples and the backlog.
Investigate coverage/freshness, multilingual discovery, permitted sources and original ads,
criteria understanding, travel evidence, exclusions/duplicates, scoring/explanations, repeated
API work, recovery and a simple interface. These are starting points, not a limit. Simplify
overlapping workflows/files while preserving detailed setup, usage and contribution guidance.
Diagnose slow steps from saved timings and failures; distinguish useful work, retries and time
waiting for my answers. Improve recovery without removing necessary evidence checks.
Separate service limits from missing evidence before recommending more paid usage.
Before provider changes, verify permitted app use, actual reasoning/tool support and token-based
windows; coding benchmarks and advertised request counts do not establish matching quality.
Do not equate integration ease or a vendor's effort labels with model quality. Evaluate
credible alternatives fairly, verifying native reasoning controls and independent fit outcomes.
Compare the complete current catalogue, shared token allowances and direct API alternatives;
preserve fresh cited research when separating main and research providers. Reuse only evidence
whose rights, request identity and freshness permit it, not stale route or scoring judgements.
Make technical model/source decisions yourself and give me simple account/setup steps.
Prefer one provider/model when it meets the task; extra models are options, not user homework.
Do not recommend a subscription from model count alone; verify its intended app use and shared
allowance, and implement clarity rather than repeatedly hand unresolved choices back to me.
Separate model capability, hosted features, current Jobcu integration and permitted use.
Do not reject a provider from shared limits alone; calculate daily/monthly demand and sensitivity.
Treat original hosted-tool reports as leads to verify, not universal support or fee guarantees.
Before recommending spending, compare fixed subscription fees with the complete direct API bill,
including hosted search calls and retrieved content. Use saved usage when authorized, include
thinking/tool charges and shared allowances, and distinguish a ceiling from an invoice or cap.
Ask me only for a necessary new spending ceiling or account instruction, not to choose models.

Assess coverage independently of result counts. Compare existing and potential sources/search
methods for unique fresh relevant jobs, original evidence, country/profession gaps, reliability
and request cost. Add useful permitted methods, improve weak ones, or replace/remove methods
shown to add no useful value or harm results. Account for unique jobs, better evidence and
backup value before removal; missing evidence or temporary failures do not prove no value.
Decide and implement the best justified approach rather than keep a source simply because
it already exists.
Check useful structured fields already returned before adding research requests. Compare
discounted same-model processing with other models, including latency/recovery and full bills;
equal-token arithmetic is a scenario, not proof of equal quality or actual demand.
Check discovery refresh provenance: failed/blank country lookups must remain retryable,
completed countries/employers must survive partial failures, and a small result count is not
proof of absent employers. A reachable/internal portal API is not permission to collect it.

Actively use public primary documentation and original research to resolve important questions
and discover opportunities. Read SOURCES before source work; verify current terms, capabilities
and prices, record dated evidence there and distinguish facts from hypotheses. Keep private
inputs out of web queries/public output; authorized provider processing goes through Jobcu.

Rank a small shortlist by expected benefit, evidence, effort, risk and verification needs.
Choose the strongest justified goal, explain why briefly, record steps/checks in In progress
and implement a complete improvement. Keep one active goal and reserve time/context for checks,
publication and recovery. Do not stop at suggestions or open features just to use allowance.

Follow AGENTS' quality, access and verification rules: preserve coverage, freshness and accurate
criteria/scoring; keep uncertain jobs and fresh judgements. All AI defaults to medium; support
all countries/professions and include fictional non-engineering matching cases. Compare
meaningful behavior/performance before and after; use CONTRIBUTING's private procedure for
live claims. Missing evidence is a dependency, not a reason to invent accuracy or savings.

This grants no new private access, paid tests or job searches. Respect standing authority,
revocations and service limits; spare assistant usage adds no provider budget. Preserve my
data/app state. An authorized new search must use 24 hours and existing frequency limits.
Update the relevant guides, decisions and prompts, verify/publish under AGENTS,
and finish with improvements, evidence/limits, unfinished work and simple next steps.
```

## End a session

Use this while the chat can still respond. Wait for the handover confirmation, then open a
fresh local Jobcu chat and use Start. Your own running Jobcu search can finish independently.

```text
End this Jobcu session and prepare a fresh chat that will not know this conversation. Follow
AGENTS.md's "Ending a session" routine. Stop new goals, research, searches and paid calls.
Checkpoint first; finish the smallest safe coherent step if interrupting would leave broken
or unreviewable work, including necessary checks/publication where practical. Otherwise park
it precisely. Preserve unrelated work, my data and my chosen app state.

Update changed facts in Right now/In progress: authorized remaining scope, branch/known head,
PR/CI, implemented/tested/pushed/merged status, failed/unrun checks, dependencies and one exact
next action. Save durable decisions in their existing homes and private evidence outside Git.
Keep the handover concise and sufficient for recovery, not a transcript. Reuse valid checks;
do not repeat startup or full tests merely to end, and do not force an unverified merge.

Complete or checkpoint publication, clean up only your disposable scratch/previews, and read
back the handover against actual Git/CI and relevant service state. Report what is saved,
verified or unfinished, link to docs/PROMPTS.md and give simple next steps. Then stop.
```
