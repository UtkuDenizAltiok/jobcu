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
- Claude requests stream, so a silent long request is not cut by a network idle limit.

## Next: measure, then protect quality

1. **Real-search measurement.** Record per-step web searches, tokens, served tier and wall
   time for the next searches and compare them with the provider's bill. Done when the
   expected savings are confirmed or any regression is fixed.
2. **Larger evaluation set.** Grow the private labelled ad set to about 150 ads, covering
   blockers, seniority, language requirements and visa wording, and report its metrics
   (pair ordering, top-10 overlap, blockers) directly from `tools/compare_providers.py`.
3. **Seniority calibration.** Lead, head and principal roles are scored too high for early
   career profiles. Test a rubric change on the evaluation set; ship it only if ordering
   improves without losing blockers or top results.
4. **Stream the remaining AI formats.** Chat Completions and Responses requests (OpenRouter,
   OpenAI, Other API) should stream like Gemini and Claude do.

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
10. **Ads published in several versions:** keep the stricter requirement and say so.
11. **Module size:** split `search.py` and `location.py` only along existing stage boundaries
    when a change touches them.
