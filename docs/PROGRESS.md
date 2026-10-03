# Jobcu progress

Where the project stands, and nothing else: git history says what was done, and
[DECISIONS.md](DECISIONS.md) says why. Kept current as described in [AGENTS.md](../AGENTS.md)
("Sessions").

## Right now

*Updated 2026-10-03. All tests pass; GitHub's tests pass on macOS and Windows.*

### State

Jobcu works end to end. A search reads the documents with the person's own AI, lets the AI find
employers for the person's kind of work (every two weeks), collects jobs from 28 sources (14 of
them company career systems, reading 403 employers plus the ones the AI found), lets the AI look
at the career-site titles the search words miss, removes duplicates, applies the rules and the
location conditions, and scores what's left with every AI step at **medium** effort (the
owner's choice). The location box takes any condition in the person's own words, shows how each
was checked, with sources, and can be corrected with Edit. The owner has run eleven real
searches on his Mac (2026-09-22 to 10-03); development is in local Claude Code sessions there.

**Fixed on 2026-10-03 from search 11** (DECISIONS.md, "The owner's search 11"): jobs Jobcu
showed before the window began, and jobs whose employer's own site shows an older copy, are left
out as **posted again**; **"Always" removes the limit** (Settings shows "No limit"); **England's
nine regions** are known; search words match compounds written apart ("Hardware Entwickler");
the score check holds 50 ads; the coverage tool's titles agree both ways.

**The owner's search 11** (2026-10-03 at noon, 72 hours, his usual sentence; the first real
search with the employer finder): **32 minutes**, no errors, 1,103 ads, 943 different jobs, 395
scored (he answered "Score 195 more", not "Always"), **349 cards** (200 UK, 140 Germany, 9
Ireland). Time: location 4.7 min (1.5 in the test), finder 3, sources 4, quick check and travel
about 5, scoring 4, **the online look-up 10 min** (210 jobs, 413 web searches; it read 205 of
210, as it should). **Cost about $2.43 of tokens and 471 web searches** (search 10: $1.74, 294):
scoring $1.04, look-up $0.86, quick check $0.34. A search every two or three days would be
about $29 a month and 5,600 web searches, above the €23 budget and Gemini's free 5,000. Google
Maps had no trouble. What it showed, most important first:
- **Reposts shown as fresh** (the owner noticed): **45 of the 349 cards** were jobs Jobcu itself
  had shown on 17–24 September, before the 72 hours began (37 Adzuna, 5 Bundesagentur, 3
  Arbeitnow; 13 scored 70+), e.g. Redline's "Senior SMPS Design Engineer" (first shown 22
  September, Adzuna dates it 30 September) and Avd's "Altium PCB Design Engineer". They carried
  "first seen by Jobcu on …" but stayed in the list, against HANDOVER §7 (proven older: hidden).
  The top card, **GE Vernova's Power Electronics Development Engineer in Berlin (94)**, says
  "Posted 4 Days Ago" on GE Vernova's own Workday site, its address ending "-3" (the third
  posting of the requisition; the owner saw it two weeks ago), while Adzuna dates it 2 October:
  the career-site reader dropped its own older copy before the duplicates were compared, so
  only Adzuna's date was left. Hitachi's "R&D Senior Engineer – Power Electronics for Power
  Transformers" says "Date Posted: 2026-02-16" in its text; Workday lists it as new.
- **England's regions are unknown to Jobcu:** the AI answered the far-right condition with five
  English regions above Reform UK's national share (North East, Yorkshire and the Humber, East
  and West Midlands, East of England), and the note says Jobcu "doesn't know" them, so they were
  dropped: only Wales and three German towns besides the eastern states were avoided (search
  10's answer: 109 towns). The shipped regions have England, Scotland, Wales and Northern
  Ireland and their counties, not the nine English regions.
- **"Always" is only as large as this search:** it raises the Settings limit to this search's
  number rounded up to 50 (400 here), so a bigger search asks again.
- **58% of the cards are Adzuna summaries** (204 of 349; 127 of 267 in search 10), and they fill
  the top: 34 of the 40 best are read only from Adzuna's ~500 characters (32 of them UK). They
  are most of the look-up's 210 jobs and its 10 minutes.
- **Quality set** (now 50 ads, 10 added from this search and rated by Claude, 40 titles):
  **48 of 50** score where the ratings put them; the two off are Bond Williams' London
  "Electronics Engineer" (88; asks 2–5 years, "typically your 2nd or 3rd role") and YER's "PCB
  Layout Designer" (77; PCB library and PLM data work, German-only ad). Only 3 of the 50 are good
  fits: the good graduate fits of this search were all Adzuna summaries, which the set can't
  keep. The same NXP graduate role scored 91 in the search and 60 when scored again (embedded
  system work judged "own field" once and "related" once).
- **Coverage list** (21 fresh jobs from StepStone's "last 3 days" and ITJobsWatch, dates checked;
  AES Bremen's "posted 1 day ago" power-electronics job is a December 2025 PDF on AES's own site,
  so a repost, left out): **7 surely found** (FRITZ!, Retsch, SEG Automotive, TKMS, Redline
  Chelmsford, ECM, Carbon 60); missed: on no source Jobcu reads (SIKORA Bremen, SII Ottobrunn,
  expertum Munich, Michael Page Munich, Advancing People Bedford, Ovarro Chesterfield, Xtrac
  Thatcham), German titles none of the search words match ("Hardware Entwickler" in two words,
  "Ingenieur in der Hardware-Entwicklung", "Entwickler Analogelektronik & PCB Layout",
  "Ingenieur*in … Elektronik"). The coverage tool's title match had counted "Electronics
  Engineer" as "Electronics Design Engineer – Mixed Signal / Robotics" (9 of 21 "found").
- Smaller: the employer finder named 120 employers, 6 new readable lists (BorgWarner, Cummins,
  Eaton, Littelfuse, Qorvo, Red Bull Technology; the rest own sites or closed systems: Bosch,
  Infineon, Siemens, ABB, Schneider); eight career hosts refused connections for a minute at
  11:39 (a network hiccup, retried); JobsIreland.ie listed nothing.

### In progress

**Until the owner's next search on Wednesday 2026-10-07** (his words: improve Jobcu as well as
possible, the sessions deciding), each step on its own `local/…` branch, tested and merged:
1. [ ] StepStone and LinkedIn re-checked (2026-10-03): still no read API; LinkedIn closed;
       StepStone only with written permission (a draft email for the owner).
2. [ ] Employers: (a) [x] a sweep of ~230 engineering employers' career pages: 18 readable ones
       added to the directory (Rohde & Schwarz, Hensoldt, VW, TE Connectivity, KION…; SOURCES.md,
       2026-10-03); (b) [x] the employer finder also tries `jobs.`/`careers.` hosts and the
       page's "jobs" link when a careers page shows no system; (c) [ ] a job-sitemap reader
       for sites whose terms allow it (Redline, ECM, expertum), for full ads instead of
       Adzuna summaries.
3. [ ] Adzuna's jobs found at their original (agencies' own sites through the same reader),
       measured by how many cards still rely on a summary.
4. [ ] Cost without losing anything: Gemini's implicit caching (shared instructions first), the
       online look-up's requests.
5. [ ] Avature (Siemens).
6. [ ] A complete made-up search (`tools/made_up_search.py`) to measure all of it.
Done when: each merged with tests, GitHub's tests pass, and "Right now" says what changed.

### Verify before relying on

- **The owner's next search** (the first with the 2026-10-03 fixes): "posted again" counted in
  Search details (search 11 would have had about 45, plus jobs like GE Vernova's Berlin one),
  no job left out that is really new (a second vacancy with the same title at the same company
  and town is the risk), the far-right condition now listing English regions and applying them
  ("Understood as"), and "Always" leaving Settings at "No limit". Time (search 11: 32 minutes,
  10 of them the online look-up) and cost per step.
- **Older copies:** only career sites that list jobs older than the window give them (Workday,
  SuccessFactors, Greenhouse and others; Oracle stops at the window). Watch that no fresh job is
  merged with an unrelated older one.
- **The employer finder over time:** no employer abroad or unrelated read for nothing; forgotten
  when a list disappears; it looks again after 14 days (next: about 2026-10-17).
- **New readers inside real searches:** Oracle (14 cards in search 11), Personio and Softgarden
  (none yet) with full ads; whether a big Softgarden employer's list page shows every job.
- **Fit limits:** real fits never capped (a neighbouring specialisation keeps its score); the
  same NXP graduate role scored 91 in search 11 and 60 when scored again.
- **The regions answer varies from search to search** (search 9: 32 towns and Wales; search
  10: 109 towns; search 11: German states, Wales and five English regions): compare
  "Understood as".
- **Cost:** search 11 cost about $2.43 of tokens and 471 web searches; at a search every two or
  three days that is about $29 a month and 5,600 web searches, above the €23 AI budget and
  Gemini's free 5,000 (prices double on 1 January 2027). Never saved by a lower effort or fewer
  jobs (task 2).
- **The robots.txt reader** (RFC 9309): check at the next `tools/check_employers.py` run that no
  newly read company clearly forbids it.
- **Sources not seen inside a search yet:** "apply by …" on a card, and Le Forem, prospective.ch,
  Werken voor Nederland, NAV and d.vinci in searches of their countries.

### Waiting on the owner

1. **The next search** (a 72-hour search every two or three days, as before): double-click the
   launcher first, so it updates from GitHub and replaces the Jobcu still running (the one that
   ran search 11 has the old code). Answer both questions with **Always** if he wants every job
   scored and looked up in every search; it now means no limit (Settings can set one again).
   Then a local session with "Check my latest search" (CONTRIBUTING.md).
2. **The friend's test:** his feedback on installing and using Jobcu.
3. **Only if he wants to send them** (messages in his name): access requests to StepStone,
   Denmark's Jobnet, Poland's CBOP, or a private NAV token. **StepStone matters now:** 7 of
   search 11's 14 missed coverage-list jobs were on StepStone and no source Jobcu reads.

The quality set and the coverage list are made by the local check on his behalf (DECISIONS.md,
2026-09-24 night); he may still rate or add jobs himself.

### Next tasks, in order

**The mission** (the owner, 2026-09-24): the best job search app possible, **universal** (any
profession, any of the 30 countries, any wording), clean, reliable and without errors. The
sessions decide everything and merge their own tested pull requests (DECISIONS.md, 2026-09-24
evening); what costs money, touches his accounts or needs a message in his name stays his.
**The owner's priorities:** **Germany first, then the UK and Ireland**; test first and most with
**a graduate engineer in electronics and power electronics hardware**; **his own searches are
the real test** and their findings come before everything else. **Every AI step stays at medium
effort.** Cost: at most €25 a month for the owner; free, or under €10 a month, for everyone else.

1. **Check the next search** ("Check my latest search"): "Verify before relying on" above, the
   ratings (`tools/score_check.py --rescore`) and a new coverage list; record the findings here
   and fix them first.
2. **Cost at medium effort** (search 11: $2.43 and 471 web searches, over budget): from
   the next search's cost per step, save only where nothing is lost: context caching for scoring
   and the quick check (Gemini cached none of their repeated instructions), the online look-up's
   jobs per request and web searches per job, and the batch size with `tools/score_check.py`.
   Never a lower effort or fewer jobs.
3. **More career systems and employers** (search 11's coverage list: 7 of 21 found; missed
   SIKORA, SII Technologies, expertum, Michael Page, Advancing People, Ovarro, Xtrac): Avature
   (Siemens: site-specific search pages), then employers' own career sites through the standard
   job data (HANDOVER §9.0, the generic JobPosting reader); the employer finder named 120
   employers in search 11 and only 15 had readable lists (SOURCES.md, "Career systems checked
   on 2026-09-30"). Still missing from search 10's list: AES, EDAG, Ricardo, Evolito, Malloy
   Aeronautics, TDK-Lambda, ENGIE, Real, Tyndall, Egis, Kirstein.
4. **Fewer jobs depending on Adzuna's summaries** (204 of 349 cards in search 11, 34 of the 40
   best): find the same job at its original before reading it online, and measure how many
   still rely on a summary. It is also most of the look-up's time and cost.
5. **Scoring:** the quality set is at HANDOVER's 50 ads with only 3 good fits: at each check,
   swap good fits with full ads in for poor ones that repeat a lesson (a small change to
   `quality.py`), watch the neighbouring-specialisation calls (NXP 91 vs 60), then the quick check's two misses (Quantum Machines' QA
   engineer, a university's drives lab lead). Re-run `tools/universality_check.py` after any
   change to the AI instructions.
6. **Phase 2's "Done when":** every example sentence from HANDOVER §6, README.md and the owner's
   own, read twice with a real provider, as its author means it. Fix in general terms.
7. **Paused until Germany, the UK and Ireland are as strong as possible:** sources for other
   countries (SOURCES.md), the licence limit for other professions, and the universality audit's
   rest.
8. **Ready for friends (Phase 4):** a first-run setup screen, updating from GitHub while keeping
   the data folder, the guides tested on a clean Mac and a clean Windows computer, and the
   repository moved to a free GitHub organization, choosing with the owner how friends
   contribute.

### Known limitations

- The town list contains some city districts as separate places (Hamburg-Wandsbek, London's
  Brent). Harmless for conditions: they lie inside the bigger city.
- SuccessFactors sites whose job pages need JavaScript (Danfoss, SICK, Vitesco, Wacker) or
  redirect (MTU) aren't read, and pages opened for address-list sites aren't remembered between
  searches.
- Facts about places are looked up fresh in every search. Only the AI's travel estimates are
  remembered (30 days); Google's travel times may not be kept (Routes API terms).
- Adzuna's jobs are scored from ~500-character summaries (its pages refuse Jobcu); those
  scoring 50 or more are read online, and the rest keep the summary's evidence.
- A fact the AI can only answer per constituency ("Leipzig II") is kept as the AI wrote it; the
  town list doesn't know constituencies, so such an exception doesn't match its town. Edit fixes
  it ("Except Leipzig").

## Owner's setup and reference numbers

- Data folder `~/Library/Application Support/Jobcu`, with the keys `adzuna_app_id`,
  `adzuna_app_key`, `ai_gemini` and `reed_api_key` (`google_maps` once set up). AI: Google Gemini,
  model `gemini-3.8-flash`, paid (€15 in advance), with Google's spend cap at €23 a month on the
  project "Jobcu AI" (everything together never above €25); web search works on it.
- Real tests only on a copy of that folder, deleted afterwards (AGENTS.md, Commands).
- A German 24-hour search takes about 4 minutes (Workday is the slowest source: about 400
  requests when no place is named); Munich or within 40 km over 72 hours about 3 minutes.
  Re-checking the whole employer directory takes about 15 minutes; `--only-new` for new
  candidates under a minute.

## Milestones

| Phase | What it delivers | Status |
|---|---|---|
| 0. Foundations | Project set-up; Jobcu starts with a double-click | ✅ Done (2026-09-17) |
| 1. Usable first version | A real search with ranked, deduplicated results and reasons | 🔨 Real searches work; the scoring limits are tuned on the quality set (48 of 50) |
| 2. Smart location filter | Understands sentences like "a city by the seaside" | 🔨 Mostly built; England's nine regions known (2026-10-03) |
| 3. Maximum coverage | Many more job sources in every supported country | 🔨 14 career systems, 403 employers, the employer finder |
| 4. Ready for friends | Complete guides, first-run setup, tested on real Mac and Windows computers | Planned |

### Phase 1: Usable first version

- [x] AI provider layer (Anthropic, Google Gemini, OpenAI, any OpenAI-compatible provider) and a
      Settings screen with keys, connection tests, usage meter, monthly limits, prices and source
      switches
- [x] CV and cover letter reading, with "What Jobcu understood"; the profile is reused while the
      documents are unchanged
- [x] Search screen with progress and Search details; hidden multilingual search words
- [x] Time, job type and remote filters; duplicates with the employer's page as main link; quick
      relevance check; scoring with reasons; a scoring limit that asks before doing more
- [x] Results: Save, Applied, Not interested, "New", Saved and Applied lists, sorting, "Posting
      date unknown"
- [ ] A quality set of 30–50 real ads judged for the owner (50 ads and 40 titles rated by
      Claude on 2026-09-24, 30 and 10-03; 48 of 50 scored where rated, but only 3 good fits) and a
      tuned scoring prompt (HANDOVER §13)
- [x] **Done when:** the owner runs a real search on his Mac and gets a ranked, deduplicated list
      with reasons (2026-09-22 and 2026-09-23).

### Phase 2: Smart location filter

- [x] Conditions read from the person's own words; facts looked up on the web with sources; size
      rules; answers per town or per country
- [x] Travel limits to reference places: Google Maps with the person's key, otherwise AI estimates
- [x] "Understood as" with sources, labelled estimates and Edit
- [x] Facts decided per region
- [ ] Other reference data as needed (boundaries, coastlines, the UK
      sponsor register)
- [ ] **Done when:** the example sentences in HANDOVER §6, in README.md and the owner's own
      examples behave as described, each with its working shown.

### Phase 3: Maximum coverage

- [x] 28 sources: Adzuna, Reed, Bundesagentur für Arbeit, service.bund.de, JobsIreland.ie,
      jobs.ac.uk, Teaching Vacancies, NHS Jobs, Le Forem, Werken voor Nederland, NAV,
      EURAXESS, Arbeitnow, Arbetsförmedlingen, and company career sites in 14 systems
      (Greenhouse, Lever, Ashby, Workable, Recruitee, Workday, Teamtailor, SuccessFactors,
      prospective.ch, d.vinci, Eightfold, Oracle, Personio, Softgarden) for 403 employers
- [x] Per-source status, unique-job counts and on/off switches
- [ ] A source for every supported country (HANDOVER §9.0)
- [x] The person's AI finds employers and their career sites (2026-09-30; single jobs found by
      the AI were tried and not shipped, DECISIONS.md)
- [ ] More career systems (Avature) and employers' own career sites (the JobPosting reader)
- [ ] **Done when:** the coverage test shows no large avoidable gaps, and the remaining gaps are
      explained to the owner.

### Phase 4: Ready for friends

- [ ] Full manual test on a real Windows computer and a real Mac
- [ ] Complete everyday-user guides (HANDOVER §2.1), tested on clean computers
- [ ] First-run setup screen and polished double-click launchers
- [ ] Updating from GitHub while keeping the data folder
- [ ] Move the repository to a free GitHub organization and invite friends, choosing with the owner
      how friends can contribute (see DECISIONS.md)
