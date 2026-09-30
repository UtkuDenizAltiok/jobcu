# Jobcu progress

Where the project stands, and nothing else: git history says what was done, and
[DECISIONS.md](DECISIONS.md) says why. Kept current as described in [AGENTS.md](../AGENTS.md)
("Sessions").

## Right now

*Updated 2026-09-30. All tests pass; GitHub's tests pass on macOS and Windows.*

### State

Jobcu works end to end. A search reads the documents with the person's own AI, collects jobs from
28 sources (14 of them company career systems, reading 403 employers and those the person's AI finds), lets the AI look at the
career-site titles the search words miss, removes duplicates, applies the rules and the location
conditions, and scores what's left with every AI step at **medium** effort (the owner's choice:
DECISIONS.md, "Back to local sessions"). The location box takes any condition in the person's
own words, shows how each was checked, with sources, and can be corrected with Edit. The owner
has run ten real searches on his Mac (2026-09-22 to 30). Development is in local Claude Code
sessions on his Mac; the cloud sessions' work (2026-09-24) is summarised in DECISIONS.md from
"2026-09-24 (evening)" on.

**Search 10** (2026-09-30, the owner's usual sentence, 72 hours, the first on the Mac with
everything from the cloud sessions), checked by a local session the same evening:
- **46 minutes**, 36 of them waiting for AI answers one at a time; the online look-up of about
  150 jobs took 22 minutes and showed no progress. **Fixed:** up to four AI requests at a time,
  one at a time after a rate limit, and "N of M jobs" on the look-up (DECISIONS.md, "The time a
  search takes"); tried with his Gemini: three to four times faster, about 20 minutes
  expected for such a search.
- **Cost:** about $1.74 of tokens (location $0.08, quick check and titles $0.28, scoring $0.80,
  online look-up $0.57) and **294 web searches** (Gemini: 5,000 free a month, then $14 per
  1,000).
- 751 ads, 668 jobs, 295 scored, **267 cards: 145 in Germany, 119 in the UK, 3 in Ireland**; the
  best GE Vernova's Power Electronics Development Engineer in Berlin (96), then graduate and
  electronics design roles in the UK. 71 of 1,694 career-site titles kept by the AI's look (the
  cloud's low effort kept 147 of 2,166). The online look-up found the town of 22 of 35 jobs and
  the requirements of 125 of 133; one question for more look-ups, answered yes.
- Checked and right: Weichs and Weßling pass the travel limit with Google Maps (176 of 347 trips
  measured by Google); limits for UK nationality and SC clearance (30), a PhD (50), German B2+
  (65), 3–4 years short (80); KLA's graduate roles in Newport reached the cards (88, 86).
- **Ireland:** JobsIreland.ie had no engineering job at all among its 720 newest (0 is right);
  Irish engineering jobs come from career sites, and most on the coverage list were at employers
  Jobcu doesn't read.
- **Coverage list** (26 fresh fitting jobs from LinkedIn's and StepStone's 3-day lists): Jobcu
  found **5 (19%)**. Rightly left out: 2 by his own conditions (Laserline near Koblenz, 51 minutes
  from Bonn; Rostock in Mecklenburg-Vorpommern) and Analog Devices' graduate roles (24 days old
  on its own site; LinkedIn shows reposts as new). **Lost by Jobcu, fixed:** GE Vernova's
  graduate programme in Rugby (the town wasn't recognised) and "Electronic Engineer" titles (the
  search word said "Electronics"): DECISIONS.md, "Search 10's coverage list". **Never
  collected, 17:** agencies seen on LinkedIn (IC Resources, Insignis, Morgan McKinley) and
  employers not in the directory (eMoSys, AES, EDAG, Ricardo, Evolito, Malloy Aeronautics,
  TDK-Lambda, ENGIE, Real, Tyndall, Egis, Kirstein; Boston Scientific added since), and
  FERCHAU's Oberkochen job (FERCHAU's others came through the Bundesagentur): tasks 3 and 5.
  **Added since:** Oracle career sites (Texas Instruments, onsemi, Vertiv and six more) and
  Boston Scientific and Cirrus Logic: DECISIONS.md, "Oracle career sites and more engineering
  employers".
- The far-right condition: 109 towns (41 in Germany, 60 in the UK, 8 in Ireland) and 9 regions
  (the five eastern states, Schwandorf, Weiden, Thurrock, Ashfield; Wales not this time), against
  search 9's 32 towns and Wales: the answer still varies a lot between searches.
- Two cards for one agency job (Augusta's "Hardware-Entwickler Embedded-Elektronik" in Weichs,
  two Adzuna ads) sharing Save and Applied: **fixed**, one card per remembered job.
- **The quality set is complete:** 40 ads and 40 titles rated by Claude. Scored again with
  today's Jobcu, other fields scored too high (PLC commissioning 73, mechanical testing 67) and
  only 28 of 40 landed where the ratings put them. **Fixed:** limits for work that fits only
  partly and for a requirement clearly not met (DECISIONS.md, "Limits for work that fits only
  partly"): now **38 of 40**; good 87–88, okay 60–80, poor 30–75 (median 50). Left: analog chip
  design and RF/EW hardware sometimes judged a neighbouring specialisation. The quick check left
  out 2 of 40 titles worth a look (Quantum Machines' QA engineer, a university's drives lab
  lead).

### In progress

- **PR #31 (Softgarden) waits for GitHub's tests:** merge it with a merge commit when they pass.
- **One complete test search with everything from 2026-09-30** (the employer finder step, the
  Oracle/Personio/Softgarden readers, four AI requests at a time, the fit limits) was started
  and stopped when the session's usage ran out: run a 24-hour search on a scratch copy (or let
  the owner's next 72-hour search show it) and check the step times and the finder's detail.

### Verify before relying on

- **The next search's time and rate limits:** about 20 minutes expected for a 72-hour search;
  no "AI limit reached, continuing more slowly" note on the owner's paid tier.
- **The employer finder in a real search** (built 2026-09-30, tried on its own): the step's
  time (about 3 minutes, every two weeks), what the employers found add to the cards, and no
  employer abroad or unrelated read for nothing.
- **Oracle career sites in a search:** Texas Instruments, onsemi and Vertiv jobs arrive with
  their full ads (read live on 2026-09-30, not yet inside a whole search).
- **Rugby-like towns:** jobs at GE Vernova's Rugby and Stafford sites on cards; no job abroad
  taken for a UK or Irish town of the same name (a bare "Hamilton" would be).
- **The robots.txt reader** (RFC 9309): check at the next `tools/check_employers.py` run that no
  newly read company clearly forbids it.
- **Sources not seen inside a search yet:** "apply by …" on a card, and Le Forem, prospective.ch,
  Werken voor Nederland, NAV and d.vinci in searches of their countries.
- **The regions answer varies from search to search** (above): compare the next searches'
  "Understood as".
- **Cost:** a 72-hour search every two or three days is about $21 a month in tokens now and
  about $42 after the prices double on 1 January 2027, above the €23 AI budget; the web searches
  stay within Gemini's free 5,000 a month at that rhythm, but not with a search a day. Savings may
  never come from a lower effort (the owner) or from fewer fresh jobs (AGENTS.md): see task 2.
- **Google Maps:** Billing → Reports should show only "Compute Route Matrix Essentials" at €0;
  no comparison of Google's times with the AI's estimates yet; the EEA terms for storing
  (SOURCES.md) to confirm when touching `travel.py`.
- **Towns found online:** search 10 found 22 of 35 (search 9: 17 of 41); never run with another
  provider.

### Waiting on the owner

1. **The next search:** restart Jobcu with the launcher (it updates itself from GitHub first; the
   Jobcu still open from search 10 runs the old version) and run a **72-hour search** with his
   usual sentence; then a local session with "Check my latest search" (CONTRIBUTING.md). After
   that, a 72-hour search every two or three days while Jobcu is developed.
2. **The friend's test:** his feedback on installing and using Jobcu.
3. **Only if he wants to send them** (messages in his name): access requests to StepStone,
   Denmark's Jobnet, Poland's CBOP, or a private NAV token. None is needed for the current focus.

The quality set and the coverage list are made by the local check on his behalf (DECISIONS.md,
2026-09-24 night); he may still rate or add jobs himself.

### Next tasks, in order

**The mission** (the owner, 2026-09-24): the best job search app possible, **universal** (any
profession, any of the 30 countries, any wording), clean, reliable and without errors. The
sessions decide everything (DECISIONS.md, 2026-09-24 evening); what costs money, touches his
accounts or needs a message in his name stays his. **The owner's priorities** (DECISIONS.md, "The
owner's priorities"): **Germany first, then the UK and Ireland**, no more sources for other
countries until these three are as strong as possible; test first and most with **a graduate
engineer in electronics and power electronics hardware**; **his own searches are the real test**
and their findings come before everything else. **Every AI step stays at medium effort.** Cost:
at most €25 a month for the owner; free, or under €10 a month, for everyone else.

1. **Check the next search** ("Check my latest search"): everything under "Verify before relying
   on", the ratings and the coverage list; record the findings here and fix them first. Open
   from searches 9 and 10: (a) jobs never collected, above all agencies seen only on LinkedIn and
   StepStone (tasks 3 and 4) and employers missing from the directory (task 5: search 10's list
   above); (f) neighbouring fields and senior roles scoring too high, and the quick check leaving
   out 2 of 40 titles worth a look (task 7).
2. **Cost at medium effort:** measure the next search's cost per step (Settings → Usage, "Search
   details"). If the monthly cost goes above the budget, save where it loses nothing: score only
   what the quick check keeps, send the scoring instructions and profile once per search with
   the provider's context caching (about 3,000 tokens with each of about 60 requests; HANDOVER
   §13, saving 8), and try the batch size with `tools/score_check.py`. Never a lower effort.
3. **More career systems and employers:** Personio and Softgarden are read since 2026-09-30,
   and the employer finder adds each person's employers on them. Next: **Avature** (Siemens:
   site-specific search pages), then employers' own career sites through the standard job data
   (HANDOVER §9.0, the generic JobPosting reader). SmartRecruiters and iCIMS close themselves to
   robots and are not read (DECISIONS.md, "Which career systems come next").
4. **Fewer jobs depending on Adzuna's summaries:** find the same job at its original (the
   employer's career site, the Bundesagentur) before reading it online, and measure how many
   still rely on a summary.
5. **More employer career sites in Germany, the UK and Ireland**, measured with whole searches
   (`tools/made_up_search.py` and the owner's own). Search 10's coverage list names who is
   missing (above). (a) the real addresses of the employers whose guessed Workday sites answered
   422: onsemi turned out to be on Oracle (added); AMD (`careers.amd.com`) and Keysight
   (`jobsearch.keysight.com`) run other systems; Dell, TE Connectivity, Honeywell, Schneider
   Electric, Zeiss and Continental still to find (SOURCES.md); (b) **more Oracle Recruiting
   Cloud employers** (the system is read since 2026-09-30; look for `oraclecloud.com/hcmUI` on
   career pages), **Personio** and **softgarden** career pages (small German employers such as
   eMoSys and AES; check terms, robots.txt and JobPosting first) and **Avature** (Siemens,
   Siemens Energy); (c) more employers on the systems Jobcu reads: semiconductors, power
   electronics, automotive and industrial electronics, drives, defence, medical devices, test and
   measurement, energy (Rohde & Schwarz, Renesas, Arm, Bosch, Ricardo, EDAG seen with their own
   sites; SOURCES.md); (d) whether the robots fix lets more Workday and SuccessFactors companies
   through, and Micron's Eightfold site.
6. **Phase 2's "Done when":** every example sentence from HANDOVER §6, README.md and the owner's
   own, read twice with a real provider, as its author means it. Fix in general terms, never for
   one sentence.
7. **Scoring with the quality set** (`tools/score_check.py --rescore`, on his Mac): 38 of 40
   now. Add ads from each search's check so the set keeps up (good fits especially), watch the
   neighbouring-specialisation calls, then the quick check's two misses. Re-run
   `tools/universality_check.py` after any change to the instructions.
8. **Paused until Germany, the UK and Ireland are as strong as possible:** sources for other
   countries (SOURCES.md), the licence limit for other professions, and the universality audit's
   rest (re-run `tools/universality_check.py` after any change to the AI instructions, which
   stays a rule).
9. **Ready for friends (Phase 4):** a first-run setup screen, updating from GitHub while keeping
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
| 1. Usable first version | A real search with ranked, deduplicated results and reasons | 🔨 Real searches work; the first quality set is rated, the scoring prompt not tuned yet |
| 2. Smart location filter | Understands sentences like "a city by the seaside" | 🔨 Mostly built |
| 3. Maximum coverage | Many more job sources in every supported country | 🔨 Started |
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
- [ ] More career systems and employers; live AI web search for jobs (HANDOVER §9.6)
- [ ] **Done when:** the coverage test shows no large avoidable gaps, and the remaining gaps are
      explained to the owner.

### Phase 4: Ready for friends

- [ ] Full manual test on a real Windows computer and a real Mac
- [ ] Complete everyday-user guides (HANDOVER §2.1), tested on clean computers
- [ ] First-run setup screen and polished double-click launchers
- [ ] Updating from GitHub while keeping the data folder
- [ ] Move the repository to a free GitHub organization and invite friends, choosing with the owner
      how friends can contribute (see DECISIONS.md)
