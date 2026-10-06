# Jobcu progress

Where the project stands, and nothing else: git history says what was done, and
[DECISIONS.md](DECISIONS.md) says why. Kept current as described in [AGENTS.md](../AGENTS.md)
("Sessions").

## Right now

*Updated 2026-10-06. Recovery implementation passes 593 local tests and GitHub checks on macOS and Windows (PR #42).*

### State

Jobcu works end to end. A search reads the documents with the person's own AI, lets the AI find
employers for the person's kind of work (every two weeks), collects jobs from 29 sources (15 of
them company career systems and job sitemaps, reading 441 employers plus the ones the AI found), lets the AI look
at the career-site titles the search words miss, removes duplicates, applies the rules and the
location conditions, and scores what's left with every AI step at **medium** effort (the
owner's choice). The location box takes any condition in the person's own words, shows how each
was checked, with sources, and can be corrected with Edit. Eleven real searches were measured before the Mac reset; the measurements below are
historical, not results from the restored machine. **Development now continues directly with
the owner through ChatGPT/Codex** (CONTRIBUTING.md). **The repository is public**, with the
existing proprietary LICENSE; all user data stays outside it.

**Recovered and improved on 2026-10-06:** uv and the locked Python environment are restored,
the baseline 566 tests and launcher self-test passed; the improved version passes 593 tests
and Ruff, with one upstream Starlette deprecation warning. First-run guidance now covers AI, CV and
cover letter with direct actions and readiness checks. The app refuses personal data folders
inside a Git checkout, and the safety guard also blocks private runtime settings and logs.
A scan of all 209 inherited commits' 1,090 unique file versions found no blocked document/key
files or matching secret patterns; this is a pattern-based check, not proof about every sentence.
Definite Gemini web-research refusals now produce one explanation and skip further research
in that search; sources and scoring continue, unsupported conditions stay unchecked, and the
employer refresh is not falsely remembered as successful. The changed screens were checked on
this Mac with fictional documents: direct uploads, missing provider address, completion after
reload, document removal and a narrow layout. No real provider requests or paid tests were run.

**Fixed on 2026-10-03 from search 11** (DECISIONS.md, "The owner's search 11"): jobs Jobcu
showed before the window began, and jobs whose employer's own site shows an older copy, are left
out as **posted again**; **"Always" removes the limit** (Settings shows "No limit"); **England's
nine regions** are known; search words match compounds written apart ("Hardware Entwickler");
the score check holds 50 ads; the coverage tool's titles agree both ways. **Coverage, the same
day:** 38 employers join the directory (Rohde & Schwarz, Hensoldt, Fraunhofer, Liebherr, VW
Group, TE Connectivity, KION, EDAG, QinetiQ, ESB…; SOURCES.md, 2026-10-03); the employer finder
follows a careers page's job link and tries `jobs.`/`careers.`/`job.` hosts (33 of 156 employers
recognised instead of 11); a new reader for job sitemaps with JobPosting pages gives full ads
from Redline Group, ECM Selection and expertum (sites whose terms allow it); made-up hosts are no
longer retried. None of this has run inside a real search yet.

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

Nothing. The recovery implementation and its checks are complete in PR #42;
the restored app is running with an empty private data folder. Temporary previews and
fictional documents have been removed. Personal setup and the first real search are next.

### Verify before relying on

- **A real first search on the restored Mac:** documents and keys need entering again. Verify
  actual provider access, progress, results and cost. The app's ordinary connection test does
  not check web-research access. The exact free-tier refusal remains untested with a real key;
  capability, quota and authentication distinctions are covered by scripted regression tests.

- **The owner's next search** (the first with the 2026-10-03 fixes): "posted again" counted in
  Search details (search 11 would have had about 45, plus jobs like GE Vernova's Berlin one),
  no job left out that is really new (a second vacancy with the same title at the same company
  and town is the risk), the far-right condition now listing English regions and applying them
  ("Understood as"), and "Always" leaving Settings at "No limit". Time (search 11: 32 minutes,
  10 of them the online look-up) and cost per step.
- **The 38 new employers and the sitemap reader inside a real search:** requests per career
  system (each may make up to 1,500 a search; Hensoldt lists 1,020 German jobs), Redline's and
  ECM's full ads merging with Adzuna's summaries of the same jobs (fewer "Scored from a short
  summary"), and the time added.
- **Gemini's free tier** (what the guide recommends to start): it has no web look-ups. Check
  with a free key what Jobcu shows (the employer finder, place conditions that need facts, the
  online look-up) and make the message plain; today the wording isn't known.
- **The finder's deeper look** at its next refresh (about 2026-10-17 for the owner): employers
  found through `jobs.`/`careers.` hosts are the company's own, not a namesake's.
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

1. **Restore personal setup in Jobcu:** enter the AI key in Settings, choose a model and test
   the connection, then upload the CV and cover letter. No saved Jobcu data was present on the
   reset Mac; GitHub contains code, not a backup of these private files. Never paste keys into chat.
2. **The first new search:** a 72-hour search in the priority countries. Then a local session
   can review it with permission, using a scratch copy and publishing only anonymous findings.
   Friends can download the public code without GitHub invitations; the proprietary license
   still applies to use and contributions.
3. **Only if he wants to send them** (messages in his name): written permission from the
   Stepstone Group (one request covers StepStone.de, Totaljobs, IrishJobs and Jobs.ie; a draft is
   in SOURCES.md, "LinkedIn, StepStone…"), Denmark's Jobnet, Poland's CBOP, a private NAV token.
   **LinkedIn has no route:** no read API, and its terms forbid automated reading.

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
2. **Measure the new research fallback with a real key:** definite refusals now explain once
   and skip the unavailable steps. Verify the account's actual response and that no known source
   coverage disappears; do not assume every free-tier model has the same capabilities.
3. **Cost at medium effort** (search 11: $2.43 and 471 web searches, over the owner's budget):
   Gemini cached none of the scoring and quick check's repeated instructions (about 1,400 tokens
   of system instruction plus the person's background) though it caches long shared prefixes by
   itself: find out why; the online look-up's jobs per request and web searches per job; the
   batch size with `tools/score_check.py`. Never a lower effort or fewer jobs.
4. **More employers and systems:** recruiters with job sitemaps whose terms allow it (check terms
   first: Hays and Rise Technical forbid it), Avature (Siemens: RSS without places, no JobPosting
   on its pages), SuccessFactors' shared career pages (`career5.successfactors.eu`: Brose's older
   site, IAV), the employer finder's 103 unrecognised employers of the sweep (SOURCES.md).
5. **Fewer jobs depending on Adzuna's summaries** (204 of 349 cards in search 11): measure after
   the sitemap reader; find the same job at its original before reading it online.
6. **Scoring:** the quality set is at HANDOVER's 50 ads with only 3 good fits: at each check,
   swap good fits with full ads in for poor ones that repeat a lesson (a small change to
   `quality.py`), watch the neighbouring-specialisation calls (NXP 91 vs 60), then the quick check's two misses (Quantum Machines' QA
   engineer, a university's drives lab lead). Re-run `tools/universality_check.py` after any
   change to the AI instructions.
7. **Phase 2's "Done when":** every example sentence from HANDOVER §6, README.md and the owner's
   own, read twice with a real provider, as its author means it. Fix in general terms.
8. **Paused until Germany, the UK and Ireland are as strong as possible:** sources for other
   countries (SOURCES.md), the licence limit for other professions, and the universality audit's
   rest.
9. **Ready for friends (Phase 4):** first-run guidance is implemented. Next: a "new version"
   notice for ZIP installs, simpler updating while preserving private data, and a complete
   manual install/use check on a clean Windows computer. The public repository already permits
   downloads without invitations; an organization is optional, not a release prerequisite.

### Known limitations

- The town list contains some city districts as separate places (Hamburg-Wandsbek, London's
  Brent). Harmless for conditions: they lie inside the bigger city.
- SuccessFactors sites whose job pages need JavaScript (SICK, Wacker) or redirect (MTU)
  aren't read, and pages opened for address-list sites aren't remembered between
  searches.
- Facts about places are looked up fresh in every search. Only the AI's travel estimates are
  remembered (30 days); Google's travel times may not be kept (Routes API terms).
- Adzuna's jobs are scored from ~500-character summaries (its pages refuse Jobcu); those
  scoring 50 or more are read online, and the rest keep the summary's evidence.
- A fact the AI can only answer per constituency ("Leipzig II") is kept as the AI wrote it; the
  town list doesn't know constituencies, so such an exception doesn't match its town. Edit fixes
  it ("Except Leipzig").

## Local setup and reference measurements

- A restored Git checkout, uv, Python and locked dependencies are ready. Personal data uses
  the standard separate Jobcu folder (AGENTS.md, Project layout); there are no restored keys,
  documents, search history or quality ratings. Never record actual account/project identifiers
  or user-entered values here.
- Real provider checks need the owner's permission and keys through Jobcu's code, on a scratch
  copy of the data folder that is deleted afterwards. Existing limits and medium effort remain.
- Historical timings: a German 24-hour search took about four minutes; a 72-hour named-town
  search about three. Re-check after recovery; the multi-country reference search above took
  32 minutes and needs cost and lookup improvements.

## Milestones

| Phase | What it delivers | Status |
|---|---|---|
| 0. Foundations | Project set-up; Jobcu starts with a double-click | ✅ Done (2026-09-17) |
| 1. Usable first version | A real search with ranked, deduplicated results and reasons | 🔨 Real searches work; the scoring limits are tuned on the quality set (48 of 50) |
| 2. Smart location filter | Understands sentences like "a city by the seaside" | 🔨 Mostly built; England's nine regions known (2026-10-03) |
| 3. Maximum coverage | Many more job sources in every supported country | 🔨 15 career systems and job sitemaps, 441 employers, the employer finder |
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
- [x] First-run guidance for AI, CV and cover letter; double-click launchers verified on the restored Mac
- [ ] Updating from GitHub while keeping the data folder
- [x] Public code downloads without invitations; contributions through pull requests under the existing license
