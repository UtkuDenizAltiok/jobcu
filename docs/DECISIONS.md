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
| Show sought roles in profile progress; label the most recent role as history. Offer **Reset document understanding** to forget cached profiles and read again on the next search. | Completed study or placement work must not look like a requested role. Reset costs no AI calls itself, keeps documents/results, and preserves default reuse (2026-10-07). |
| Interpret each new query afresh. Conditions can name places, population, travel limits or researched facts; label estimates and unchecked conditions. | People's wording and intentions differ; no personal query is hard-coded (2026-09-17 to 2026-09-24). |
| Interpret countries, places and condition types together in one medium-effort request; apply the existing population, travel and research checks afterwards. | Avoid asking the AI to read and classify the same request twice. Fictional country/commute/nursing checks verify preserved conditions; live speed and interpretation still need measurement (2026-10-07). |
| **Edit** reapplies corrected conditions to the same job pool and reuses earlier evidence. | Correct interpretation without collecting every ad again (2026-09-17; implemented 2026-09-21). |
| Report completion only after final results and status are saved together. If saving fails, keep available results visible and explain that closing Jobcu may lose them. | A finished heading must mean the latest results can be restored; a controlled fictional test reproduced completion preceding persistence after the Windows CI restore failure (2026-10-07). |
| Measure travel to the nearest edge of a reference place unless the user asks for its centre. | The person could live anywhere in the place (2026-09-24). |
| For Maps journeys into a reference city, compare the calculated edge point and city centre, keeping the faster available journey. Explicit centre requests still measure the centre alone; explain that sampling can miss faster districts. | A geometric edge can have a worse connection than the centre. Fictional regressions reproduce a reachable job rejected by an edge-only journey. This clarifies the anywhere-in-the-place intent above without claiming an exact fastest commute (2026-10-07). |
| Prefer original employer ads and full descriptions. Keep summary evidence and missing conditions labelled. | Missing text must not appear to be complete evidence (2026-09-17; clarified 2026-10-06). |
| Use original posting/closing dates and job memory to suppress expired ads and old reposts. Keep distinct requisitions distinct. | A board's refreshed date is not a new vacancy (2026-09-24; fixes 2026-10-03). |
| Explain scores with rubric parts and deterministic blocker limits; retain low-score jobs. | Users can see why a job ranks where it does; a score is not hiring probability (2026-09-23 to 2026-09-30). |
| Ask before exceeding search limits. **Always** removes that limit for future searches; monthly limits still apply. | An arbitrary cap must not silently discard relevant work (2026-09-30). |
| Count attempted online checks cumulatively; deferred jobs remain pending when a limit is reached. Supply the original URL to research the same vacancy. | Fictional regressions reproduce the counter moving backwards on continuation. Titles alone can identify different requisitions (2026-10-07). |
| New installs use a **24-hour posting lookback**; preserve existing saved choices. The owner chooses daily 24-hour searches. | Support earlier applications with daily on-demand use (owner, 2026-10-07). Supersedes the 72-hour first-evaluation default of 2026-10-06; wider windows remain available. |

## Setup and provider behavior

| Decision | Reason and date |
|---|---|
| Search requires AI configuration, CV and cover letter; first-run guidance links to each. | Make the route to a first search complete (2026-10-06). |
| The Maps key test uses named stations, says public transport, shows the weekday-morning departure assumption and explains that it checks access. Count it against the local route limit. | General TRANSIT includes walking and other modes; a successful sample must not be presented as a train-only timetable or overall accuracy check (2026-10-07). |
| A successful connection test checks ordinary generation, not web-research access. Definite research refusals explain once and skip that research for one search. | Account/model capability can differ from basic generation; preserve collection/scoring and show uncertainty (2026-10-06). |
| Retry research on a later search; never mark a refused employer lookup as a successful refresh. | A temporary restriction must not suppress future employer discovery (2026-10-06). |
| Keep guides provider-neutral and link to current provider instructions/prices. Remove fixed model recommendations and unmeasured cost/runtime promises. | Capabilities and charges change; the restored Mac has no measured search baseline yet (2026-10-07). This supersedes the guide's 2026-10-03 provider recommendation. |
| Write everyday guides for first-time users: explain terms, give one clear action per step, name the actual controls and say how to confirm success. Put optional setup after the basic route; keep owner/Codex review instructions in their project documents. | Friends using Jobcu may have little technical experience. Plain language needs enough explanation to complete a task, rather than the shortest possible text (owner, 2026-10-07). |
| Keep concrete examples of richer place requests in README and the usage guide, including election vote shares, Turkish supermarkets, Sunday opening, student populations and combined commute conditions. Define thresholds and label research limits. | The examples help users understand the range of requests they can make; simplifying the guides should preserve them without claiming unmeasured accuracy (owner, 2026-10-07). |

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
