"""Web searches inside the provider's free monthly searches cost nothing in Jobcu's estimates."""

import pytest

from jobcu.ai.base import Usage
from jobcu.ai.usage import UsageLog, estimate_cost, free_allowances
from jobcu.settings import ModelPrice, Settings

MODEL = "gemini-4-fictional"
PRICE = ModelPrice(provider="gemini", model=MODEL, input_per_million=1.0,
                   output_per_million=2.0, web_search_per_thousand=14.0)


def searched(search_id: int, searches: int, when: str, *, step: str = "job_places") -> None:
    UsageLog().record(step=step, provider="gemini", model=MODEL, search_id=search_id,
                      usage=Usage(input_tokens=1000, web_searches=searches), created_at=when)


def cost_of(search_id: int, allowance: int | None) -> float:
    log = UsageLog(free_searches={"gemini": allowance} if allowance else None)
    cost, complete = estimate_cost(log.for_search_by_model(search_id), [PRICE])
    assert complete
    return cost


def test_searches_inside_the_free_month_cost_nothing_and_those_past_it_are_priced():
    searched(1, 6, "2026-11-10T20:00:00.000Z")
    searched(2, 6, "2026-11-12T20:00:00.000Z")
    tokens = 1000 / 1e6 * 1.0
    assert cost_of(1, 10) == pytest.approx(tokens)
    assert cost_of(2, 10) == pytest.approx(tokens + 2 / 1000 * 14.0)  # 4 free, 2 paid
    # Without an allowance every billed search is priced, as before.
    assert cost_of(1, None) == pytest.approx(tokens + 6 / 1000 * 14.0)


def test_the_allowance_renews_with_the_provider_s_billing_month_in_pacific_time():
    searched(1, 10, "2026-11-30T20:00:00.000Z")
    # 1 December 07:00 UTC is still 30 November in California: the same month, nothing left.
    searched(2, 3, "2026-12-01T07:00:00.000Z")
    searched(3, 3, "2026-12-01T09:00:00.000Z")  # 1 December in California: a new allowance
    assert cost_of(2, 10) == pytest.approx(0.001 + 3 / 1000 * 14.0)
    assert cost_of(3, 10) == pytest.approx(0.001)


def test_every_step_and_search_shares_the_month_s_allowance_in_order():
    searched(1, 4, "2026-11-10T20:00:00.000Z", step="employers")
    searched(1, 4, "2026-11-10T20:05:00.000Z", step="job_places")
    log = UsageLog(free_searches={"gemini": 5})
    employers = log.for_search_by_model(1, step="employers")[0]
    places = log.for_search_by_model(1, step="job_places")[0]
    assert (employers.free_search_units, places.free_search_units) == (4, 1)
    assert places.paid_search_units == 3 and places.billed_search_units == 4


def test_free_searches_need_no_search_price_for_a_complete_estimate():
    searched(1, 3, "2026-11-10T20:00:00.000Z")
    unpriced = PRICE.model_copy(update={"web_search_per_thousand": None})
    log = UsageLog(free_searches={"gemini": 100})
    assert estimate_cost(log.for_search_by_model(1), [unpriced]) == (pytest.approx(0.001), True)
    assert estimate_cost(UsageLog().for_search_by_model(1), [unpriced])[1] is False


def test_the_allowance_is_the_research_provider_s_from_settings():
    settings = Settings()
    assert free_allowances(settings) == {}
    settings.ai.provider = "gemini"
    settings.limits.free_web_searches = 5000
    assert free_allowances(settings) == {"gemini": 5000}
    settings.ai.research_provider = "anthropic"
    assert free_allowances(settings) == {"anthropic": 5000}
