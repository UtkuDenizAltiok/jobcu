"""Free monthly web searches: counted in the provider's month, shared fairly over the days."""

from datetime import UTC, datetime

import pytest

from jobcu import db
from jobcu.ai.base import AILimitReached, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.usage import UsageLog, billing_days_left, billing_month_start
from jobcu.search import free_web_search_share
from jobcu.settings import Settings


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


@pytest.mark.parametrize("now,start,days", [
    # Google's month is Pacific time: 10:00 in Turkey on the 1st is still the old month at 06:59Z.
    ("2026-11-01T06:59:00", "2026-10-01T07:00:00", 1),
    ("2026-11-01T07:00:00", "2026-11-01T07:00:00", 30),
    ("2026-12-15T12:00:00", "2026-12-01T08:00:00", 17),  # winter time: UTC-8
])
def test_the_month_follows_pacific_time(now, start, days):
    assert billing_month_start(at(now)) == at(start)
    assert billing_days_left(at(now)) == days


def record(provider, created_at, searches, results=0):
    UsageLog().record(step="job_places", provider=provider, model="fictional-model",
                      usage=Usage(10, 5, web_searches=searches, web_results=results),
                      created_at=created_at)


def test_every_billed_search_at_the_provider_this_month_counts():
    record("gemini", "2026-11-01T06:00:00.000Z", 40)  # still October in Pacific time
    record("gemini", "2026-11-02T09:00:00.000Z", 7)
    record("gemini", "2026-11-03T09:00:00.000Z", 2, results=1)
    record("anthropic", "2026-11-03T09:00:00.000Z", 50)
    assert UsageLog().web_searches_this_month("gemini", at("2026-11-04T00:00:00")) == 10


def settings_with(free, provider="gemini", research=None):
    settings = Settings()
    settings.ai.provider, settings.ai.model = provider, "fictional-model"
    settings.ai.research_provider = research
    settings.limits.free_web_searches = free
    return settings


def test_each_search_gets_a_fair_share_of_what_is_left():
    now = at("2026-11-21T12:00:00")  # ten days left, today included
    record("gemini", "2026-11-05T09:00:00.000Z", 4000)
    with db.connect() as conn:  # this person searches twice a day
        conn.executemany("INSERT INTO searches (started_at, status, form_json) VALUES (?, ?, ?)",
                         [("2026-11-15T09:00:00.000Z", "finished", "{}")] * 28)
    assert free_web_search_share(settings_with(5000), now) == 50
    assert free_web_search_share(settings_with(4000), now) == 0
    assert free_web_search_share(settings_with(None), now) is None
    # The research provider's own searches count, not the main provider's.
    assert free_web_search_share(settings_with(5000, "openrouter", "gemini"), now) == 50
    assert free_web_search_share(settings_with(5000, "openrouter", "anthropic"), now) == 250


class Searcher:
    can_search_the_web = True


def test_a_used_share_stops_research_with_its_own_reason():
    settings = settings_with(None)
    settings.limits.web_search_cap = 10
    client = AIClient(settings, adapter=Searcher(), free_web_search_share=0)
    assert client.web_searches_left() == 0 and client.free_share_reached()
    with pytest.raises(AILimitReached, match="share of this month's free web searches"):
        client.research(step="job_places", system="Fictional", prompt="Fictional")
    # The smaller per-search limit decides when it is the one reached.
    client = AIClient(settings, adapter=Searcher(), free_web_search_share=20)
    assert client.web_searches_left() == 10 and not client.free_share_reached()
