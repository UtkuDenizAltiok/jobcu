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
- Reference-city facts reused for 30 days; unknown cities are not bought again until then
  unless the person retries.
- Claude, OpenAI and OpenRouter requests stream, so a silent long request is not cut by a
  network idle limit.
- An ad found online in two versions keeps the stricter requirement and says so.
- A larger private evaluation set (about 200 judged ads with blockers) whose decision metrics,
  pair ordering, top 10, bands, blockers and each model's reasoning share, come straight from
  `tools/compare_providers.py`.
- A one-step recommended AI setup in Settings, in plain language.

## Next: measure, then protect quality

1. **Real-search measurement.** Record per-step web searches, tokens, served tier and wall
   time for the next searches and compare them with the provider's bill. Done when the
   expected savings are confirmed or any regression is fixed.
2. **Provider-neutral answers and fair model comparisons.** Work out a person's work rights
   per target country once, from their documents, so every scoring request compares an ad's
   clause (for example "without sponsorship now or in the future") with stated facts instead
   of re-deriving visa rules. Make sure every model really reasons when asked (some routes
   ignored the request), then compare cheaper models again on equal terms.
3. **Seniority calibration.** Lead, head and principal roles are scored too high for early
   career profiles; plain senior roles stay realistic. Test a rubric change on the evaluation set; ship it only if ordering
   improves without losing blockers or top results.
4. **Stream Other API requests** where a service's streams are shown to report usage, as
   OpenAI and OpenRouter requests now do.

## Then: coverage

5. **Federal Employment Agency (Bundesagentur).** The portal stays paused under its terms.
   Seek permission for respectful automated reading, and measure how many of its jobs other
   permitted sources already provide.
6. **Free source allowances.** Make sure monthly free allowances, such as JSearch credits, are
   fully used across searches without paid overruns.
7. **Coverage benchmark.** Compare Jobcu with an independently collected sample of real
   vacancies and fix the largest missing sources or over-strict filters.

## Later: simplicity

8. **Recommended setup** in one step, in plain language.
9. **Cost preview** before a search, from recent searches' measured usage.
10. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
8. **Cost preview** before a search, from recent searches' measured usage.
10. **Ads published in several versions:** keep the stricter requirement and say so.
11. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
    when a change touches them.
