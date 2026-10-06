# Jobcu progress

Current state and next work. Decisions live in [DECISIONS.md](DECISIONS.md); source facts in
[SOURCES.md](SOURCES.md); detailed completed work in Git history. Follow [AGENTS.md](../AGENTS.md).

## Right now

*Updated 2026-10-06. Local session resumed and review readiness verified; first real search is next.*

### State

Mac recovery, project readiness, session prompts and on-demand use are implemented, tested,
pushed and merged in PRs #42–#48. Session resumption verified clean main `5d90a54`, matching
origin, with passing macOS, Windows and privacy CI on both PR #48 and its merge. The checkout is in
`Developer/jobcu` under the owner's home; it was moved, not copied.
The rebuilt environment and Mac launcher self-test passed after relocation; Git stayed clean.
**Jobcu is stopped by the owner's request.** His default is double-clicking **Start Jobcu.command**
to open it, then closing that terminal window and choosing **Terminate** if prompted to stop it.
Direct terminal commands are optional. Do not automatically start or keep his app running.
The preview port 8799 has no listener and its fictional data was removed.
The previous handover recorded no configured keys, documents, query or search. This session
does not inspect private inputs or results. The posting window defaults to 72 hours.
No live AI or paid requests were made during preparation or this readiness work.
Historical measurements are references, not today's results.

**ChatGPT/Codex** edits the Mac checkout connected to GitHub; published code and handovers are
kept there. "Local" is the execution location, not offline development. The owner confirmed this
workflow: keep GitHub synchronized and run Jobcu on his Mac. The human retains ownership and
the proprietary license; the assistant leads product/engineering work and tested merges. The public code is
separate from all private inputs and results. Country work order: **Germany, Ireland, UK,
Switzerland, Netherlands, Belgium, Italy**. First validation focus: **electronics and technical
engineering**, with general matching and fictional other-profession regressions.

The shipped source directory includes all seven priority countries. Listed employers are not
verified vacancies or measured engineering recall; see the dated matrix in SOURCES.md.
Architecture and evaluation tools are documented in ARCHITECTURE.md and CONTRIBUTING.md;
completed implementation detail belongs in Git. The two canonical start/end prompts are in
[SESSION-PROMPTS.md](SESSION-PROMPTS.md). AGENTS.md requires simple, direct next steps after
every response. No source upload or copy of this chat is needed for the local project.

PR #48's documentation clarification is merged; its stale publication checkpoint is resolved.
The local project chat is active. Next is personal setup and a completed search in Jobcu,
then the separately authorized private review in CONTRIBUTING.md.
The review-readiness update is published in PR #49 (`codex/resume-readiness`, from `5d90a54`):
the aggregate report labels original-search versus correction timings and cumulative usage.
It warns against comparing mismatched scopes; unknown saved kinds remain unknown.
Git and PR #49's checks/merge record establish its final publication state. If interrupted
before merge, finish its Mac/Windows/privacy checks and merge with a merge commit.

### In progress

No unfinished implementation or running search. **614 tests**, Ruff and the privacy guard
passed locally for the reviewed PR #49 change; publication recovery is described above.
Ports 8765/8799 have no listeners; no recognizable abandoned scratch folders were found.
No private-data review, live search or paid call was performed.

**Next session's exact first action:** follow SESSION-PROMPTS.md's start prompt; verify Git
and PR #49's state, recover publication only if needed, then follow CONTRIBUTING.md's review
protocol once the owner completes setup and a search. Actual provider access, coverage,
scoring quality, cost and speed remain unmeasured on the restored Mac.

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

1. On **Wednesday, 2026-10-07**, enter keys, CV, cover letter and private query **in Jobcu only**;
   choose the job types and 72-hour posting window, then complete the search and any limit prompt.
2. Start a Local project chat with **Analyse my latest Jobcu search** using the prepared review
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
