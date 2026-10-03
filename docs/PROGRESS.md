# Jobcu progress

Where the project stands, and nothing else: git history says what was done, and
[DECISIONS.md](DECISIONS.md) says why. Kept current as described in [AGENTS.md](../AGENTS.md)
("Sessions").

## Right now

*Updated 2026-10-01. All tests pass; GitHub's tests pass on macOS and Windows.*

### State

Jobcu works end to end. A search reads the documents with the person's own AI, lets the AI find
employers for the person's kind of work (every two weeks), collects jobs from 28 sources (14 of
them company career systems, reading 403 employers plus the ones the AI found), lets the AI look
at the career-site titles the search words miss, removes duplicates, applies the rules and the
location conditions, and scores what's left with every AI step at **medium** effort (the
owner's choice). The location box takes any condition in the person's own words, shows how each
was checked, with sources, and can be corrected with Edit. The owner has run ten real searches
on his Mac (2026-09-22 to 30); development is in local Claude Code sessions there.

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
  "Ingenieur*in … Elektronik"). The coverage tool's title match counted "Electronics Engineer"
  as "Electronics Design Engineer – Mixed Signal / Robotics" (one title's words inside the
  other's), so it overstated finds.
- Smaller: the employer finder named 120 employers, 6 new readable lists (BorgWarner, Cummins,
  Eaton, Littelfuse, Qorvo, Red Bull Technology; the rest own sites or closed systems: Bosch,
  Infineon, Siemens, ABB, Schneider); eight career hosts refused connections for a minute at
  11:39 (a network hiccup, retried); JobsIreland.ie listed nothing.

### In progress

**Checking the owner's search 11** (2026-10-03, 72 hours, 349 cards, 32 minutes), on branch
`local/check-search-11`, with a scratch copy of his data folder in the session's scratchpad
(delete it when done):
1. [x] Study the search (results, scores, places, notes, sources, cost, time).
2. [x] Rate the new ads kept for the score check; `tools/score_check.py --rescore`.
3. [x] A coverage list of 15–25 fresh jobs found on the web; `tools/coverage_test.py`.
4. [x] Record the findings here, delete the scratch copy, tests, merge.
5. [ ] Fix, most important first, each in its own tested, merged step:
   a. [ ] Reposts: a job Jobcu showed before the window began is hidden as older; career
          sites keep their older copies for the duplicate comparison, so an aggregator's newer
          date for an older original is caught (GE Vernova Berlin).
   b. [ ] "Always" means no limit from now on (Settings shows it and can set one again).
   c. [ ] England's nine regions in the shipped regions, so a condition answered with them
          applies.
   d. [ ] Search words match German compounds written apart or with a hyphen.
   e. [ ] The coverage tool's title match agrees both ways.
Done when: findings recorded with examples, fixes merged with tests, GitHub's tests pass.

### Verify before relying on

- **The owner's next search** (the first real one with everything above): its time (about 20
  minutes for 72 hours, plus 3 for the finder), the finder's step detail and the employers it
  adds, the online look-up's detail (it must read nearly all jobs it lists, or ask), no "AI limit
  reached" note on his paid tier, and the cost per step (Search details).
- **The employer finder over time:** no employer abroad or unrelated read for nothing; forgotten
  when a list disappears; it looks again after 14 days.
- **New readers inside real searches:** Oracle, Personio and Softgarden jobs on cards with full
  ads; whether a big Softgarden employer's list page shows every job.
- **Fit limits:** real fits never capped (a neighbouring specialisation keeps its score); watch
  analog chip design and RF/EW hardware.
- **Rugby-like towns:** GE Vernova's Rugby and Stafford jobs on cards; no job abroad taken for a
  UK or Irish town of the same name (a bare "Hamilton" would be).
- **Google Maps:** it asked Jobcu to slow down in the test search (per-minute quota): whether
  that happens in the owner's searches, and Billing → Reports still at €0.
- **The regions answer varies from search to search** (search 9: 32 towns and Wales; search 10:
  109 towns, no Wales): compare "Understood as".
- **Cost:** about $1.7 of tokens for a 72-hour search; a search every two or three days is about
  $21 a month now and about $42 after the prices double on 1 January 2027, above the €23 AI
  budget; web searches stay within Gemini's free 5,000 a month at that rhythm. Never saved by a
  lower effort or fewer jobs (task 2).
- **The robots.txt reader** (RFC 9309): check at the next `tools/check_employers.py` run that no
  newly read company clearly forbids it.
- **Sources not seen inside a search yet:** "apply by …" on a card, and Le Forem, prospective.ch,
  Werken voor Nederland, NAV and d.vinci in searches of their countries.

### Waiting on the owner

1. **The next search, Saturday 2026-10-03 at noon:** double-click the launcher (it updates
   itself from GitHub and replaces the old Jobcu still running), run a **72-hour search** with
   his usual sentence, and answer both questions with **Always** (score them all; look them all
   up). The first search with the employer finder takes about 3 minutes longer. Then a local
   session with "Check my latest search" (CONTRIBUTING.md).
2. **The friend's test:** his feedback on installing and using Jobcu.
3. **Only if he wants to send them** (messages in his name): access requests to StepStone,
   Denmark's Jobnet, Poland's CBOP, or a private NAV token. None is needed for the current focus.

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
2. **Cost at medium effort:** from the next search's cost per step, save only where nothing is
   lost: context caching for scoring and the quick check (Gemini cached none of their repeated
   instructions in search 10, but 43% of the online look-up's), and the batch size with
   `tools/score_check.py`. Never a lower effort or fewer jobs.
3. **More career systems and employers:** Avature (Siemens: site-specific search pages), then
   employers' own career sites through the standard job data (HANDOVER §9.0, the generic
   JobPosting reader); the employer finder names the systems in use (SOURCES.md, "Career systems
   checked on 2026-09-30"). Missing employers from search 10's coverage list: AES, EDAG,
   Ricardo, Evolito, Malloy Aeronautics, TDK-Lambda, ENGIE, Real, Tyndall, Egis, Kirstein.
4. **Fewer jobs depending on Adzuna's summaries** (127 of 267 cards in search 10): find the same
   job at its original before reading it online, and measure how many still rely on a summary.
5. **Scoring:** keep the quality set growing with each check (good fits especially), watch the
   neighbouring-specialisation calls, then the quick check's two misses (Quantum Machines' QA
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
| 1. Usable first version | A real search with ranked, deduplicated results and reasons | 🔨 Real searches work; the quality set is complete and the scoring limits are tuned on it (38 of 40) |
| 2. Smart location filter | Understands sentences like "a city by the seaside" | 🔨 Mostly built |
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
- [ ] A quality set of 30–50 real ads judged for the owner (40 ads and 40 titles rated by Claude
      on 2026-09-24 and 30, good fits among them) and a tuned scoring prompt (HANDOVER §13)
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
