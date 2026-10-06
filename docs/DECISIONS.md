# Current product decisions

This is the current product direction and its reasons. Working authority, priorities, privacy
and release rules live in [AGENTS.md](../AGENTS.md); implementation detail lives in
[ARCHITECTURE.md](ARCHITECTURE.md). See the [dated decision history](archive/DECISION-HISTORY.md)
for earlier choices and superseded plans. New decisions belong here with a date and reason;
retain a superseded decision in the archive when replacing it.

## Search behavior

| Decision | Reason and date |
|---|---|
| Read documents into a structured profile; reuse it only while documents, prompt and model are unchanged. Never reuse job scores. | Save repeated document work while keeping each search's judgement fresh (2026-09-17). |
| Interpret each new query afresh. Conditions can name places, population, travel limits or researched facts; label estimates and unchecked conditions. | People's wording and intentions differ; no personal query is hard-coded (2026-09-17 to 2026-09-24). |
| **Edit** reapplies corrected conditions to the same job pool and reuses earlier evidence. | Correct interpretation without collecting every ad again (2026-09-17; implemented 2026-09-21). |
| Measure travel to the nearest edge of a reference place unless the user asks for its centre. | The person could live anywhere in the place (2026-09-24). |
| Prefer original employer ads and full descriptions. Keep summary evidence and missing conditions labelled. | Missing text must not appear to be complete evidence (2026-09-17; clarified 2026-10-06). |
| Use original posting/closing dates and job memory to suppress expired ads and old reposts. Keep distinct requisitions distinct. | A board's refreshed date is not a new vacancy (2026-09-24; fixes 2026-10-03). |
| Explain scores with rubric parts and deterministic blocker limits; retain low-score jobs. | Users can see why a job ranks where it does; a score is not hiring probability (2026-09-23 to 2026-09-30). |
| Ask before exceeding search limits. **Always** removes that limit for future searches; monthly limits still apply. | An arbitrary cap must not silently discard relevant work (2026-09-30). |
| New installs use a **72-hour posting lookback**; preserve existing saved choices. | A three-day sample suits the first restored-Mac evaluation (2026-10-06). |

## Setup and provider behavior

| Decision | Reason and date |
|---|---|
| Search requires AI configuration, CV and cover letter; first-run guidance links to each. | Make the route to a first search complete (2026-10-06). |
| A successful connection test checks ordinary generation, not web-research access. Definite research refusals explain once and skip that research for one search. | Account/model capability can differ from basic generation; preserve collection/scoring and show uncertainty (2026-10-06). |
| Retry research on a later search; never mark a refused employer lookup as a successful refresh. | A temporary restriction must not suppress future employer discovery (2026-10-06). |
| Keep guides provider-neutral and link to current provider instructions/prices. Remove fixed model recommendations and unmeasured cost/runtime promises. | Capabilities and charges change; the restored Mac has no measured search baseline yet (2026-10-07). This supersedes the guide's 2026-10-03 provider recommendation. |

## Evaluation

| Decision | Reason and date |
|---|---|
| Sample full ads and labelled summaries across score bands; keep final scores, evidence completeness and the original location plan. | Avoid bias from summary omissions, duplicate-first selection or pre-research scores (2026-10-06). |
| Judge every top card independently before reporting precision; use a date-verified independent list before reporting coverage recall. | Counts and broad score bands do not prove search quality (2026-10-06). Procedure: [REVIEW](REVIEW.md). |
| Record step time and answer-wait time; label correction timings separately from cumulative usage. | Corrections and full searches cannot be compared as equivalent performance runs (2026-10-06). |
| Warn when scoring reads only an excerpt of a lengthy ad. | Unseen requirements must not be assumed satisfied (2026-10-06). |

## Project organization — 2026-10-07

- Use [README](../README.md) as the entry point and [PROMPTS](PROMPTS.md) as the sole home of
  start, end and review prompts. The private review procedure lives in REVIEW.md. This
  supersedes the two-prompt/session-file split recorded on 2026-10-06.
- Keep PROGRESS.md short: verified state, unfinished work and next actions. Keep current
  decisions and a source index separate from dated background in `docs/archive/`.
- Preserve the original concept, historical decisions and source evidence in the archive;
  keep shared Git history and licensing intact. Older `HANDOVER` references in code refer to
  `docs/archive/HANDOVER.md`.
- Keep the established `src/`, `tests/`, `tools/` and root launcher layout. It already separates
  runtime code, verification and maintenance; documentation cleanup does not require moving
  working modules or user data.
- Retire fully merged development branches after checking open PRs and attached worktrees.
  Keep every commit reachable from main; unmerged or active branches are preserved.

These choices give each document one purpose and avoid repeating instructions across guides,
prompts and handovers. Future updates follow the information homes in AGENTS.md.
