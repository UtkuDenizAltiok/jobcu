# Jobcu roadmap

Planned work in priority order. Jobcu's priorities are, in order: the quality and coverage of
suitable jobs, then cost, then speed. Every item states why it matters and how to know it is
done. Implementation details belong in pull requests; current behavior is described in
[ENGINEERING](ENGINEERING.md) and source evidence in [SOURCES](SOURCES.md).

## Recently completed (October and November 2026)

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
- Stop keeps what is scored: once jobs are scored, stopping a search builds the list from them,
  and "Retry incomplete checks" finishes the rest.
- Only web searches the provider bills count against the free monthly searches and a search's
  share: searches inside requests the provider failed, or a stopped search cancelled, are kept
  in the usage record but not counted where the provider doesn't bill them (measured against
  Google's billing report). Such a failed look-up is tried again like any outage, also when
  paid limits stop work: it no longer pauses the rest of the search's online checks. Cost
  estimates price only the billed searches, and "Search details" names each step's.
- The best jobs of the "same kind of work, with gaps" band no longer tie at its maximum: its top
  two role points rise towards the uncapped band, measured on the judged ads (more of the ten
  best ads in the top ten, as many scores within their judged range).
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
   for a provider whose sources name no pages and tries again after two weeks. Next for such
   providers: reach the employer's own page through more career systems Jobcu reads itself.
7. **Free source allowances.** Make sure monthly free allowances, such as JSearch credits, are
   fully used across searches without paid overruns.
8. **Coverage benchmark.** Compare Jobcu with an independently collected sample of real
   vacancies and fix the largest missing sources or over-strict filters.

## Later: simplicity

9. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
   when a change touches them.
