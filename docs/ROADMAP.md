# Jobcu roadmap

Planned work in priority order. Jobcu's priorities are, in order: the quality and coverage of
suitable jobs, then cost, then speed. Every item states why it matters and how to know it is
done. Implementation details belong in pull requests; current behavior is described in
[ENGINEERING](ENGINEERING.md) and source evidence in [SOURCES](SOURCES.md).

## Recently completed (October and November 2026)

- Mercedes-Benz's jobs are read from its job sitemap (967 jobs, each once in the searched
  country's language). A sitemap whose job addresses don't say "job" is read by the pattern the
  directory gives; pages new on a list are opened first, and the directory check samples the
  whole list when its dates can't order it.
- Five more Workday sites are read: BD's in Germany and Ireland, Frazer-Nash (UK), NCR Atleos
  (hardware engineering in Dundee) and Videojet (Germany, UK). They had answered with Workday's
  human check during a directory check and answered normally when asked again, one at a time.
- Jobcu recognises by itself an employer's own list of plain job links when the person's AI names
  that employer: the shape of the links (a job number in the same place) and one job page with
  job data are enough; such lists are read from the next search on, on any system.
- 55 more employers in electronics hardware are read directly, found through FreeHire's
  catalogue of employers' own job systems: Neura Robotics, Quantum-Systems, Rocket Factory
  Augsburg, Heraeus, STIHL, Enercon, AVL, Knorr-Bremse, SiTime, the Plath group, VACUUMSCHMELZE
  in Germany; AMETEK, Pickering, Spellman, Cambridge GaN Devices, Filtronic, Oxford Quantum
  Circuits, Integral Powertrain, Open Cosmos, Babcock's and Graphcore's graduate jobs and others in
  the UK.
- Employers' own job list pages can be read, whatever application system runs behind them:
  dSPACE, Würth Elektronik (rexx), Pfisterer (MHM) and Diehl (umantis) to start with, and in
  Ireland Tyndall National Institute (JazzHR) and MBRYONICS (Rippling). Where a job's page has
  no job data, the job comes with the title, place and day its list gives it. The German
  application systems without a reader (coveto, JOIN, rexx, umantis, HR4you, onlyfy) were
  counted first: in electronics their ads are few and mostly agencies' and building firms', and
  they reach Jobcu through FreeHire already, so they got no readers of their own.
- Rheinmetall's jobs are read from its own site's sitemap (1,423 jobs). A sitemap listing each
  job in many languages counts it once, in the searched country's language; titles the search
  words miss reach the person's AI when the job is new on the list, as on SuccessFactors.

- A job leaves the list only when its removal is certain: a route that accepts only UK residents
  (CV-Library) or a link the person marks unusable. A page that is gone or refuses the person's
  country is explained on click with a web search, and the job stays. For good jobs whose links
  can't take the application, the person's AI looks up the employer's own posting, kept only when
  its web sources list it; cards found for one posting are marked as possible duplicates.
- Clicks skip middleman pages: Jobcu reads the clicked page then and sends the browser to its one
  clear apply link (never during a search, as such links may be paid per click). Good jobs that
  only had job-site links get the employer's own posting looked up online, and employer pages open
  directly.
- The job memory recognises a job by the town its location names, and marks cards a site listed
  late, so jobs seen before aren't presented as new. A job an earlier search showed with its
  score stays hidden whatever its date (one listed only while its place was being checked comes
  back to be judged); one shown a week or more before and really posted again is assessed again
  and listed with a "Reposted" label.
- The result lists of the last 90 searches are kept; older ones are deleted only when a new
  search starts, never while the person may still apply from the latest list.
- One card for an ad found twice: duplicates are looked for again once the full ads are read
  (an agency's ad that one site lists without its text), a shorter and a longer employer name
  count as one when place, title and text agree, and one ad listed for several towns names the
  other towns on each card. A job joined this way is matched to the job memory again, so an ad
  an earlier search showed doesn't return as new.
- A job site's short summary or cut-off text is treated as part of the ad, not the whole ad,
  without buying JSearch details that would repeat it: one search had five jobs at 70 or more
  judged from such fragments as if every requirement had been seen.
- A company written without its spaces (FreeHire names some by their career site's address,
  "riedelcommunications") is the same company: one saved search had two such jobs as extra cards.
- Town sizes in Germany come from official statistics (Destatis, 2,059 towns) instead of
  GeoNames' mixed-age figures: Braunschweig had wrongly fallen below "0.3% of the country's
  people", so its jobs were measured against Hannover, 79 minutes away.
- Workday's wd1 and wd5 servers (85 employers, Analog Devices and Medtronic among them) are read
  again: a robots.txt behind a human check sets no rules, as the robots standard says, while a check
  on the ads is never passed, so those jobs come with title, place, date and the employer's link.
  Where the employer's own career site lists the same vacancy number (GE Vernova, Johnson &
  Johnson, Thermo Fisher, Danaher, RTX), the full ad is read there instead.
- An employer that starts hiring in a new country is read there at once: on career systems whose
  one answer lists every job (Workday, Greenhouse, Lever, Ashby and others), every directory
  employer is asked in every search, not only those known to hire in the countries searched.
- Gradcracker, the UK's board for engineering and technology graduate jobs, can be read: only the
  graduate lists of the areas the person's search words name (electronic and electrical, hardware,
  ...), whole, with a job counted as posted on the day it first appears there (the board gives no
  dates). Its legal page forbids scraping, so it is off until the person switches it on.
- Jobcu learns employers' own career sites from the jobs it finds: when a job site's copy of a
  job links the employer's Workday, Oracle, Greenhouse or SuccessFactors list and Jobcu doesn't
  read it yet, the list is checked during the search and read from the next search on. Lists that
  move (as NXP's and Dell's did) and new employers are picked up without a directory update, with
  no AI and no web searches; search 21's job links named 13 such sites (Honeywell's newer Oracle
  site, Oxford Nanopore, Ralliant among them).
- Workday is read at one polite pace per Workday server rather than per company: its servers ask
  one computer for a human check once it has sent them a lot, and then refuse every company for a
  while. A server that refuses three companies in a row isn't asked again in that search (one
  company refusing alone doesn't stop the others), and the search's notes say how many asked.
- Siemens' and Siemens Energy's own career sites (Avature) can be read, country by country: Siemens
  had 381 jobs in Germany, 155 in the UK and 15 in Ireland; few of them reached Jobcu through job sites.
  Siemens' terms forbid automated reading, so the source is off until the person switches it on.
- Schneider Electric and AMD are read through their Jibe career sites (newest first, full ads, a
  few requests), and Arm and BAE Systems through their own job sitemaps.
- Phenom career sites can be read: ABB, Siemens Healthineers, Thermo Fisher, Danaher, RTX, GE
  Aerospace and Exyte, each country's list with its posting days in a few requests. ABB's terms
  require permission for scraping, so the source is off until the person switches it on.
- SmartRecruiters career pages can be read: Continental, Aumovio, Renesas, ALTEN, Ramboll, AECOM,
  Wabtec, Assystem, Brainlab, XP Power and Averna. Its terms for job seekers forbid automatic
  access, so the source is off until the person switches it on.
- The employer directory was read again in full and keeps every country an employer has hired
  in, so a job it posts in a country with no opening on the day of the check is still read.
  New: ZEISS, Freudenberg, Signify, Avnet (Silica, EBV), 3M, Rolls-Royce Power Systems' early
  careers, Advanced Energy, Bertrandt, Teradyne, Skyworks, Lear, Celestica, Seagate, Keysight,
  Northrop Grumman, Lam Research, Vertical Aerospace, ZeroAvia, Honeywell Aerospace, Socomec,
  Garrett, and Leonardo UK and Arrow on their Phenom sites.
- More employers read directly: Woodward, BorgWarner, Evolito, Altera, Leidos, Emerson, and Micron's
  and HP's own Eightfold sites; NXP at Workday's newer address (its old one stopped answering) and
  Dell on its new Oracle site.
- Stop keeps what is scored: once jobs are scored, stopping a search builds the list from them,
  and "Retry incomplete checks" finishes the rest.
- Only web searches the provider bills count against the free monthly searches and a search's
  share: searches inside requests the provider failed, or a stopped search cancelled, are kept
  in the usage record but not counted where the provider doesn't bill them (measured against
  Google's billing report). Such a failed look-up is tried again like any outage, also when
  paid limits stop work: it no longer pauses the rest of the search's online checks. Cost
  estimates price only the billed searches, and "Search details" names each step's.
- SuccessFactors career sites with their own job layout are read in full: the ad and its real
  title where the page marks them in a block without a type (five large employers' jobs came
  in with a page address for a title and no text), one title where a page marks it twice, and
  no job where a listed page only says the position is filled.
- Career sites that give no posting date (13 of the 49 SuccessFactors sites) are dated by their
  own list: a job that appears between two readings a day apart is posted that day and joins
  the main list, and one listed since before the window can show a job site's fresh copy to
  be a repost. Before, every job of theirs stayed under "Posting date unknown".
- One card for a job a career site lists once per language: the listings are joined by the
  site's own vacancy number, or by their shared untranslated ad, and the version the person
  reads best is the one scored. Before, the same job showed twice, sometimes 12 points apart.
- Jobs close to the person's own work no longer all show 80: inside the "same kind of work,
  with gaps" band the most a job can score rises with every role point (83 to 93 from 31
  points), and a job with an unconfirmed central requirement can reach 86. Measured on the
  judged ads without AI calls (clear pairs ordered better, 7.7 instead of 5.9 of the ten best
  ads in the top ten, as many scores within their judged range); no score falls. A UK card
  without the sponsorship deduction now says that the ad offers sponsorship.
- A job whose only link can't take the person's application also offers the company's own
  website, when a job site names it, beside the web search.
- A SuccessFactors job posted for several towns is placed in its main town (the one its address
  names), not the first one its page lists: one such job was placed in Spain and left out.
- SuccessFactors titles the search words miss reach the person's AI like other career sites'
  titles: only jobs new on the list since the last reading, in a country searched; a page is
  opened only for a title the AI keeps.
- Jobs that aren't the person's kind of work are ordered like a careful reader would: inside
  the "related job" band the most a job can score rises with its role points (51 to 60), and
  below 28 role points its other gaps (far more experience asked, a language the person lacks)
  count too instead of all showing 60. Measured on the judged ads without AI calls: clear pairs
  ordered better, about 11 more of 62 scores within their judged range, the top ten unchanged;
  no job crosses 70 in a saved list.
- A job the person has never seen, which the employer's own career site lists from before the
  window while a job site dated it again inside it, is listed as reposted, with the day the
  employer first posted it and the employer's page as its link. Before, such jobs were hidden
  where Jobcu read the employer's older entries and shown as new where it didn't.
- A job only job sites listed, of an employer whose Workday, Oracle or SuccessFactors career site Jobcu reads,
  gets the employer's own posting from that site's search: the employer's link, full ad and
  date (an older posting makes it a labelled repost). The posting joins only when the duplicate rules
  take it for the same job.
- Six more employers' own career sites are read (Agile Robots, Riedel Communications, Mynaric,
  planqc, STABL Energy, Delta Energy Systems), found where saved results had good matches only
  through job sites.
- Scoring: a language wished for in the ad's own language counts like a required one; lead, head,
  principal and staff titles are capped for early-career profiles; the sponsorship penalty
  applies to UK jobs only. Roles are graded by closeness to the person's own specialist field,
  and explicit junior, graduate and training-programme roles in their discipline count as the
  same kind of work for early-career people.
- The Federal Employment Agency (Bundesagentur) as an opt-in source under its terms.
- FreeHire, a free source without a key: employers' own ads from about 220 career systems
  (many that Jobcu's employer list doesn't name), with the full text and the employer's link.
  Dated by the earlier of the ad's date and FreeHire's first sight, so re-dated ads stay old.
- Google Flex: the same Gemini model at half the token price, used together with request
  recovery, with retries and a normal-price fallback.
- A fair monthly share of the research provider's free web searches, asking before more.
- Fewer web searches per online job look-up, with the same ads found.
- Reviewed official tables: a city's unlabelled total row counts when it is unambiguous.
- Verified reference-city facts kept for 90 days whichever AI found them (and kept beyond that
  when a new check can't establish the city); a reviewed decision can settle a whole country;
  unknown cities are not bought again for 30 days unless the person retries.
- Free allowances divided equally over the planned searches (a 72-hour search takes three
  parts); paid limits can only tell instead of stopping; Google's travel times can be kept
  for the same place (the person's choice), AI estimates for 90 days.
- Claude, OpenAI and OpenRouter requests stream, so a silent long request is not cut by a
  network idle limit.
- An ad found online in two versions keeps the stricter requirement and says so.
- A larger private evaluation set (about 200 judged ads with blockers) whose decision metrics,
  pair ordering, top 10, bands, blockers and each model's reasoning share, come straight from
  `tools/compare_providers.py`.
- A one-step recommended AI setup in Settings, in plain language.
- A cost preview before each search, from the recent searches' measured usage.
- Provider-neutral scoring: work rights are read once per country and compared with an ad's
  clause in code, every OpenRouter model is checked to really reason, and cheaper models
  were compared again on equal terms (none matched Gemini's ordering).

## Next: measure, then protect quality

1. **Real-search measurement.** Record per-step web searches, tokens, served tier and wall
   time for the next searches and compare them with the provider's bill. Done when the
   expected savings are confirmed or any regression is fixed.
2. **Gemini reference on its own connection.** Compare the evaluation set on Jobcu's native
   Gemini connection (OpenRouter's route reasoned less often), as the reference for the items
   below and for any later model comparison.
3. **Seniority calibration.** Lead, head and principal roles are scored too high for early
   career profiles; plain senior roles stay realistic. A first wording change lowered some
   lead roles but stayed within run-to-run noise; retest with two runs on each side and ship it
   only if ordering improves without losing blockers or top results.
4. **Related roles with different daily work.** Service, field, test-rig and pure project
   management roles can land in the "maybe" band for people who want design work. Test whether
   the rubric's examples or the preferences part should place them lower, under the same rule.
5. **Stream Other API requests** where a service's streams are shown to report usage, as
   OpenAI and OpenRouter requests now do.

## Then: coverage

6. **Original postings for more jobs.** Extend the online look-up of the employer's own posting
   to other good jobs whose only links are sites that refuse Jobcu, prefer employer pages over
   other job sites, and use the original posting date. Measure per AI provider how often the
   right open page is found: the log counts each look-up's postings kept and why the others
   weren't. Measured on Gemini: its sources are redirect links that name no page, so no posting
   could be confirmed and each look-up used about 30 web searches; Jobcu now skips these look-ups
   for a provider whose sources name no pages and tries again after two weeks. Started for such
   providers: a job only job sites listed, of an employer Jobcu reads on Workday, Oracle or SuccessFactors, gets
   the employer's own posting from the employer's list search. Next: Eightfold lists (also read
   newest first).
7. **Free source allowances.** Make sure monthly free allowances, such as JSearch credits, are
   fully used across searches without paid overruns.
8. **Coverage benchmark.** Compare Jobcu with an independently collected sample of real
   vacancies and fix the largest missing sources or over-strict filters.

## Later: simplicity

9. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
   when a change touches them.
