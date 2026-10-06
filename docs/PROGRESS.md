# Jobcu progress

Current state and next work. Decisions live in [DECISIONS.md](DECISIONS.md); source facts in
[SOURCES.md](SOURCES.md); detailed completed work in Git history. Follow [AGENTS.md](../AGENTS.md).

## Right now

*Updated 2026-10-06. Project preparation is merged; the owner uses Jobcu on demand and it is stopped.*

### State

Mac recovery, project readiness, session prompts and handover are merged in PRs #42–#45.
Main was clean and matched origin at `0bbcf60` before this preference update. The sole local
checkout was moved into `Developer/jobcu` under the owner's home; it was moved, not copied.
The rebuilt environment and Mac launcher self-test passed after relocation; Git stayed clean.
**Jobcu is stopped by the owner's request.** His default is double-clicking **Start Jobcu.command**
to open it, then closing that terminal window and choosing **Terminate** if prompted to stop it.
Direct terminal commands are optional. Do not automatically start or keep his app running.
The preview port 8799 has no listener and its fictional data was removed.
Verified at close: no configured keys, uploaded documents, saved query or saved search. The
posting window is 72 hours. No live AI or paid requests were made during this preparation.
Historical measurements are references, not today's results.

Development is local in **ChatGPT/Codex**. The human owns the project and retains the proprietary
license; the assistant leads product/engineering work and tested merges. The public code is
separate from all private inputs and results. Country work order: **Germany, Ireland, UK,
Switzerland, Netherlands, Belgium, Italy**. First validation focus: **electronics and technical
engineering**, with general matching and fictional other-profession regressions.

Jobcu has 29 source adapters, 15 employer career systems/sitemaps, and 441 listed employers.
The shipped directory has entries in all seven priority countries; listed employers are not
verified current vacancies or measured engineering recall. See the dated matrix in SOURCES.md.

This preparation adds labelled summaries, final scores and original location plans to the quality
sample, fixes duplicate-first sampling, records step/answer-wait timings, and adds a read-only
aggregate review command. Lengthy scoring excerpts are explicitly identified. New installations
use a 72-hour ad-age window; existing selections remain unchanged. Completed Claude cloud tooling
and redundant wrappers are removed. AGENTS.md is shorter; architecture/retained lessons have their
own document; CONTRIBUTING.md contains the local project and result-review workflow. The two
canonical defaults are in [SESSION-PROMPTS.md](SESSION-PROMPTS.md): checkpoint and end a session,
or verify the latest state and resume, including recovery after an unexpected cutoff.

### In progress

No unfinished product implementation. **On-demand use** is recorded in the working rules,
ending prompt and launcher guide. The actual service is stopped and port 8765 was checked closed;
609 tests, Ruff and the privacy guard passed locally. This preference update is prepared on
`codex/on-demand-app`, based on main `0bbcf60`. If publication is interrupted, recover that
branch's PR and final checks, then merge and leave clean main with the service stopped. Once
merged with passing checks, no publication remains. No product code change or new search is needed.

Completed evidence: **609 tests**, Ruff, documentation links and privacy checks passed for PR #44;
macOS/Windows CI also passed on its merge. Prior app verification covered JavaScript syntax,
the Mac launcher and a fictional-data browser check of the 72-hour default, step/wait timings,
summary warning and score reveal after rating. No failed check remains from that work. This
checkpoint changes only the handover record; the final publication must pass the normal checks.

**Next session's exact first action:** use the Start a session prompt in SESSION-PROMPTS.md,
check `git status`, this record and the latest main/PR checks. After any interrupted publication
is resolved, the next product action is the first real-results review using CONTRIBUTING.md;
it waits for the owner's setup and completed search. `uv run python tools/review_search.py`
currently reports no saved search. Actual provider access, coverage, scoring quality, cost and
speed remain untested on the restored Mac; their verification list below is still open.

### Verify before relying on

- **Wednesday's first restored-Mac search:** actual provider/model access, successful document
  parsing, criteria interpretation, source availability, progress, results and usage. A connection
  test checks ordinary generation, not web-research capability. Inspect unchecked conditions and
  unavailable-source messages; scripted tests cannot establish live account capabilities.
- **Freshness/deduplication:** compare original dates, closing dates, repost identity and job memory.
  Old-vacancy suppression and older-copy merging were fixed on 2026-10-03 but have no post-reset
  live measurement. Don't merge genuinely different requisitions at the same company and town.
- **Full-ad coverage:** measure high-ranked summary exposure and the sitemap adapters' contribution.
  The old search had 204 summary cards out of 349 and 34 out of the top 40. Newly added employers
  and adapters need a real multi-source comparison, not another isolated adapter smoke test.
- **Scoring quality/stability:** independently judge the top 10 and rebuild the private 30–50-ad
  sample after the reset. The inherited 48/50 broad-band result had only three good fits and
  omitted summary cards. A neighbouring-specialisation ad varied from 91 to 60 on repeat. Those
  numbers do not establish current accuracy or stable ranking.
- **Efficiency:** the previous reference multi-country search took 32 minutes; online ad research
  took 10 minutes. It used about $2.43 of tokens and 471 web searches. New per-step and answer-wait
  measurements allow a real baseline; token costs omit fees not included in configured prices.
- **Platforms:** automated Mac and Windows checks cover launchers and behavior; a complete human
  install/upload/search session on a freshly installed Windows computer remains unverified.

### Waiting on the owner

1. Add the existing source folder as a **local Jobcu project** in Codex and start a Local chat
   with [SESSION-PROMPTS.md's starting prompt](SESSION-PROMPTS.md#start-a-session).
2. On **Wednesday, 2026-10-07**, enter keys, CV, cover letter and private query **in Jobcu only**;
   choose the job types and 72-hour posting window, then complete the search and any limit prompt.
3. Start a Local project chat with **Analyse my latest Jobcu search** using the prepared review
   prompt. The initial aggregate review makes no paid calls; detailed evidence stays local.

No account change, invitation, source upload or background schedule is required. Do not ask for
private setup in chat, and do not start another search on the owner's behalf without instructions.

### Next tasks

1. **Review the first real results before tuning.** Use CONTRIBUTING.md's protocol: source gaps,
   unknown dates/conditions, top-10 full evidence, independent labels, a date-verified coverage list,
   then targeted fixes. Publish only anonymous aggregate findings and fictional examples.
2. **Improve engineering coverage in country order.** Trace each confirmed miss to collection,
   search words, deduplication, criteria, relevance or a limit. Start with Germany, Ireland and UK;
   then Switzerland, Netherlands, Belgium, Italy. Prefer readable original employers and full ads.
   Engineers Ireland is a manual benchmark candidate pending collection/terms checks. VDAB's
   partnership requirement makes it unsuitable as a simple per-user key source.
3. **Reduce summary dependence and research duplication.** Measure originals merging with board
   summaries and requests per useful full ad. Improve matching/career-system reach where the
   coverage list proves a gap; no blind crawl expansion or lower AI effort.
4. **Stabilize borderline scoring.** Repeat independent cases and compare single/batch runs with
   the same evidence and location plan. Explain field, seniority, language and permit limits;
   preserve adjacent engineering specialisations when the daily work fits the actual profile.
5. **Optimize cost and elapsed time from the baseline.** Inspect repeated prefixes/caching and web
   requests per job, preserve recall and ranking, and separate answer waiting from computation.
   Compare changes on the same private evaluation set before a broader rollout.
6. **Product polish from observed use.** Fix confusing setup/results behavior and accessibility
   issues found during real use. ZIP-update notices and a full clean-Windows check remain later
   release work; ownership and future commercial licensing remain the human's decisions.

### Known limitations

- Some providers/models cannot perform web research. Definite refusals explain once and skip
  further research within that search; existing sources/scoring continue and unchecked conditions
  and summary warnings remain. Confirm exact live behavior after account setup.
- The source directory and title screening improve reach but do not cover every vacancy. Some
  career systems or job boards prohibit/refuse automated access. Never bypass their restrictions.
- Scores combine model judgement with deterministic limits; uncertainty and summary evidence can
  still move rankings. Caps or a higher score are not independently validated hiring likelihood.
- The quality sample is bounded (50 ads, 40 titles) and is rebuilt after the reset. Old samples
  without saved criteria cannot faithfully validate preference scoring. Correction timings cover
  that correction, while token usage for its search ID is cumulative.
- The current review report examines saved results, not a running search; it flags a newer attempt
  with no saved results. Missing historical timings and unlabelled quality stay unknown.
- Provider fees, cached-token discounts and web-research charges are not fully represented by the
  user-entered token price table. Do not present the estimate as an invoice or guaranteed budget.

## Validation goals

These are targets for the next measured development cycle, **not achieved results**:

- No confirmed expired, old or duplicate vacancy presented as a fresh distinct job; every case
  gets a date/requisition check and a fictional regression.
- Every top-10 card independently judged with original evidence where available; report the sample
  size, good/okay/poor counts, uncertainty and any high-ranked blocker.
- A 15–25-job date-verified coverage benchmark with misses explained and fixed in country order.
- Any speed/cost change preserves or improves fit and sample recall at medium effort, on the same
  evaluation set. No claims that high card counts or an isolated unit test prove world-leading quality.
