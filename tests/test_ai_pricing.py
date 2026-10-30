"""Fictional tariffs: fees, cache discounts and missing billing evidence stay explicit."""

import pytest

from jobcu.ai.base import AILimitReached, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.usage import ModelUsage, UsageLog, estimate_cost
from jobcu.settings import ModelPrice, Settings, load_settings, save_settings


def price(**changes):
    return ModelPrice(provider="gemini", model="fictional-model", input_per_million=2,
                      output_per_million=8, **changes)


def used(**counts):
    return ModelUsage("gemini", "fictional-model", Usage(**counts))


def test_cache_and_search_fees_are_priced_without_counting_thinking_twice():
    cost, complete = estimate_cost([used(input_tokens=1_000_000, cached_input_tokens=400_000,
                                        output_tokens=200_000, reasoning_tokens=150_000,
                                        web_searches=100)], [price(
                                            cached_input_per_million=.2,
                                            web_search_per_thousand=10)])
    assert cost == pytest.approx(1.2 + .08 + 1.6 + 1)
    assert complete


def test_separately_billed_result_pages_are_priced_and_stay_out_of_the_query_count():
    cost, complete = estimate_cost([used(web_searches=4, web_results=20)],
                                   [price(web_search_per_thousand=5)])
    assert cost == pytest.approx(24 * 5 / 1000) and complete
    _, complete = estimate_cost([used(web_results=3)], [price()])
    assert not complete  # a billed page without a search price is not a known zero


@pytest.mark.parametrize("counts", [{"web_searches": 10},
                                   {"input_tokens": 100, "cached_input_tokens": 50},
                                   {"unreported_requests": 1}])
def test_missing_tariffs_or_usage_cannot_be_a_complete_estimate(counts):
    assert not estimate_cost([used(**counts)], [price()])[1]


def test_explicit_zero_search_rate_is_different_from_a_missing_rate():
    cost, complete = estimate_cost([used(web_searches=10)], [price(web_search_per_thousand=0)])
    assert cost == 0 and complete
    assert not estimate_cost([used(web_searches=10)], [])[1]


def test_different_currencies_are_not_added_as_if_they_were_the_same_money():
    other = ModelUsage("openai", "fictional-other", Usage(input_tokens=1_000_000))
    tariff = ModelPrice(provider="openai", model="fictional-other", input_per_million=1,
                        output_per_million=2, currency="EUR")
    assert estimate_cost([used(input_tokens=1_000_000), other], [price(), tariff]) == (0, False)


def test_search_only_charges_reach_the_monthly_spending_limit_before_dispatch():
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.prices = [price(web_search_per_thousand=10)]
    settings.limits.monthly_cost_limit = 1
    log = UsageLog()
    log.record(step="location", provider="gemini", model="fictional-model",
               usage=Usage(web_searches=100))
    client = AIClient(settings, usage_log=log)
    # A charged tool call can reach the limit even when it reports no token usage.
    with pytest.raises(AILimitReached, match="spending limit"):
        client._check_monthly_limit()


def test_when_paid_limits_only_tell_the_ai_goes_on_with_one_note_a_search():
    # The owner (2026-10-30): never cap a paid service; say when a monthly limit is passed.
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.prices = [price(web_search_per_thousand=10)]
    settings.limits.monthly_cost_limit = 1
    settings.limits.monthly_token_limit = 10
    settings.limits.paid_limits = "tell"
    log = UsageLog()
    log.record(step="location", provider="gemini", model="fictional-model",
               usage=Usage(input_tokens=50, web_searches=100))
    notes = []
    client = AIClient(settings, usage_log=log, notify=notes.append)
    client._check_monthly_limit()
    client._check_monthly_limit()
    assert len(notes) == 2  # the token limit and the cost limit, each said once
    assert "passed your monthly token limit" in notes[0] and "passed your limit of 1" in notes[1]
    # Missing prices only mean the cost can't be estimated; nothing stops either.
    settings.prices = []
    unpriced = AIClient(settings, usage_log=log, notify=notes.append)
    with unpriced._request("location", "gemini", "fictional-model"):
        pass
    assert "can't estimate this month's AI cost" in notes[-1]


@pytest.mark.parametrize("case", ["missing_model", "missing_search_price", "mixed_currencies"])
def test_configured_spending_limit_refuses_an_unpriceable_dispatch(case):
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.limits.monthly_cost_limit = 20
    settings.prices = [] if case == "missing_model" else [price()]
    if case == "mixed_currencies":
        settings.prices.append(ModelPrice(provider="openai", model="fictional-other",
                                          input_per_million=1, output_per_million=2,
                                          currency="EUR"))
    client = AIClient(settings, usage_log=UsageLog())
    named = {"missing_model": "no price for gemini · fictional-model",
             "missing_search_price": "no search price for gemini · fictional-model",
             "mixed_currencies": "more than one currency: EUR, USD"}[case]
    with pytest.raises(AILimitReached, match="Save current prices") as refused:
        with client._request("location", "gemini", "fictional-model",
                             research=case == "missing_search_price"):
            pytest.fail("Unpriceable request was dispatched")
    assert named in refused.value.message


def test_a_price_saved_while_a_search_runs_applies_at_once():
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.limits.monthly_cost_limit = 20
    client = AIClient(settings, usage_log=UsageLog())  # started before the price existed
    with pytest.raises(AILimitReached, match="no price for gemini · fictional-model"):
        client._check_monthly_limit(provider="gemini", model="fictional-model")
    saved = load_settings()
    saved.prices = [price()]
    save_settings(saved)
    client._check_monthly_limit(provider="gemini", model="fictional-model")
