# Jobcu roadmap

Planned work in priority order. Jobcu's priorities are, in order: the quality and coverage of
suitable jobs, then cost, then speed. Every item states why it matters and how to know it is
done. Implementation details belong in pull requests; current behavior is described in
[ENGINEERING](ENGINEERING.md) and source evidence in [SOURCES](SOURCES.md).

## Recently completed (October 2026)

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

6. **Federal Employment Agency (Bundesagentur).** The portal stays paused under its terms.
   Seek permission for respectful automated reading, and measure how many of its jobs other
   permitted sources already provide.
7. **Free source allowances.** Make sure monthly free allowances, such as JSearch credits, are
   fully used across searches without paid overruns.
8. **Coverage benchmark.** Compare Jobcu with an independently collected sample of real
   vacancies and fix the largest missing sources or over-strict filters.

## Later: simplicity

9. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
   when a change touches them.
