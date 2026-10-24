"""Records the tokens every AI request uses, for the usage meter and monthly limits."""

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jobcu import db
from jobcu.ai.base import Usage
from jobcu.settings import ModelPrice

# Google counts its free monthly web searches in Pacific time (the free 5,000 renew on the 1st
# at 00:00 in California, 10:00 in Turkey).
BILLING_ZONE = ZoneInfo("America/Los_Angeles")


def billing_month_start(now: datetime) -> datetime:
    local = now.astimezone(BILLING_ZONE)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)


def billing_days_left(now: datetime) -> int:
    """Days left in the billing month, today included."""
    local = now.astimezone(BILLING_ZONE)
    return calendar.monthrange(local.year, local.month)[1] - local.day + 1


@dataclass
class ModelUsage:
    provider: str
    model: str
    usage: Usage


class UsageLog:
    def __init__(self, folder: Path | None = None) -> None:
        self.folder = folder

    def record(
        self, *, step: str, provider: str, model: str, usage: Usage, search_id: int | None = None,
        recovery_id: str | None = None, created_at: str | None = None,
        budget_id: str | None = None,
    ) -> None:
        model = billed_model(model, usage)
        with db.connect(self.folder) as conn:
            if budget_id is None and search_id is not None:
                search = conn.execute("SELECT budget_id FROM searches WHERE id=?",
                                      (search_id,)).fetchone()
                budget_id = search[0] if search else None
            if recovery_id is not None:
                conn.execute("BEGIN IMMEDIATE")
                previous = conn.execute(
                    "SELECT id FROM ai_usage WHERE provider=? AND recovery_id=?",
                    (provider, recovery_id)).fetchone()
                if previous is not None:
                    conn.execute(
                        """UPDATE ai_usage SET input_tokens=MAX(input_tokens,?),
                        output_tokens=MAX(output_tokens,?),
                        cached_input_tokens=MAX(cached_input_tokens,?),
                        reasoning_tokens=MAX(reasoning_tokens,?),
                        web_searches=MAX(web_searches,?),
                        unreported_requests=MIN(unreported_requests,?),
                        web_results=MAX(web_results,?) WHERE id=?""",
                        (usage.input_tokens, usage.output_tokens, usage.cached_input_tokens,
                         usage.reasoning_tokens, usage.web_searches, usage.unreported_requests,
                         usage.web_results, previous[0]))
                    return
            conn.execute(
                """INSERT INTO ai_usage (search_id, step, provider, model, input_tokens,
                   output_tokens, cached_input_tokens, reasoning_tokens, web_searches,
                   unreported_requests, recovery_id, budget_id, web_results, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           COALESCE(?,strftime('%Y-%m-%dT%H:%M:%fZ','now')))""",
                (search_id, step, provider, model, usage.input_tokens, usage.output_tokens,
                 usage.cached_input_tokens, usage.reasoning_tokens, usage.web_searches,
                 usage.unreported_requests, recovery_id, budget_id, usage.web_results,
                 created_at),
            )

    def this_month(self, now: datetime | None = None) -> list[ModelUsage]:
        now = now or datetime.now(UTC)
        month_start = now.strftime("%Y-%m-01T00:00:00")
        return self._by_model("created_at >= ?", (month_start,))

    def ordinary_this_month(self, now: datetime | None = None) -> list[ModelUsage]:
        now = now or datetime.now(UTC)
        return self._by_model("created_at >= ? AND budget_id IS NULL",
                              (now.strftime("%Y-%m-01T00:00:00"),))

    def web_searches_this_month(self, provider: str, now: datetime | None = None) -> int:
        """Billed web search units at one provider in its billing month, every step and
        allowance included: they all come out of the provider's free monthly searches."""
        start = billing_month_start(now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%S")
        with db.connect(self.folder) as conn:
            return conn.execute(
                "SELECT COALESCE(SUM(web_searches + web_results), 0) FROM ai_usage "
                "WHERE provider = ? AND created_at >= ?", (provider, start)).fetchone()[0]

    def for_budget(self, budget_id: str, *, after_id: int = 0) -> list[ModelUsage]:
        return self._by_model("budget_id = ? AND id > ?", (budget_id, after_id))

    def for_search(self, search_id: int) -> dict[str, Usage]:
        """Usage per step of one search, for "Search details"."""
        with db.connect(self.folder) as conn:
            rows = conn.execute(
                """SELECT step, SUM(input_tokens), SUM(output_tokens), SUM(cached_input_tokens),
                   SUM(reasoning_tokens), SUM(web_searches), SUM(unreported_requests),
                   SUM(web_results)
                   FROM ai_usage WHERE search_id = ? GROUP BY step""",
                (search_id,),
            ).fetchall()
        return {row[0]: Usage(*row[1:]) for row in rows}

    def for_search_by_model(self, search_id: int, step: str | None = None) -> list[ModelUsage]:
        """One search's usage per model (of one step, if given), so its cost can be estimated."""
        if step is not None:
            return self._by_model("search_id = ? AND step = ?", (search_id, step))
        return self._by_model("search_id = ?", (search_id,))

    def _by_model(self, where: str, params: tuple) -> list[ModelUsage]:
        with db.connect(self.folder) as conn:
            rows = conn.execute(
                f"""SELECT provider, model, SUM(input_tokens), SUM(output_tokens),
                    SUM(cached_input_tokens), SUM(reasoning_tokens), SUM(web_searches),
                    SUM(unreported_requests), SUM(web_results)
                    FROM ai_usage WHERE {where} GROUP BY provider, model""",
                params,
            ).fetchall()
        return [ModelUsage(row[0], row[1], Usage(*row[2:])) for row in rows]


FLEX = " (flex)"
# Google's Flex price is half of every standard token price; search fees are not reduced.
FLEX_SHARE = 0.5


def billed_model(model: str, usage: Usage) -> str:
    """Flex usage is kept apart from the same model's normal-price usage."""
    return model + FLEX if usage.service_tier == "flex" and not model.endswith(FLEX) else model


def price_for(prices: dict[tuple[str, str], ModelPrice], provider: str,
              model: str) -> ModelPrice | None:
    """The saved price; Flex usage without its own row costs half the model's normal tokens."""
    price = prices.get((provider, model))
    if price is None and model.endswith(FLEX):
        normal = prices.get((provider, model.removesuffix(FLEX)))
        if normal is not None:
            price = normal.model_copy(update={
                "model": model,
                "input_per_million": normal.input_per_million * FLEX_SHARE,
                "output_per_million": normal.output_per_million * FLEX_SHARE,
                "cached_input_per_million": None if normal.cached_input_per_million is None
                else normal.cached_input_per_million * FLEX_SHARE})
    return price


def total_tokens(usages: list[ModelUsage]) -> int:
    return sum(u.usage.input_tokens + u.usage.output_tokens for u in usages)


def estimate_cost(usages: list[ModelUsage], prices: list[ModelPrice]) -> tuple[float, bool]:
    """Estimated cost from the user's price table.

    Price reported usage before account allowances, taxes and other service fees. Thinking is
    already included in output. Missing cache prices use the regular input price; missing
    search prices omit those fees. Either omission makes the estimate incomplete.
    """
    table = {(p.provider, p.model): p for p in prices}
    cost = 0.0
    complete = True
    currencies: set[str] = set()
    for item in usages:
        complete = complete and item.usage.unreported_requests == 0
        price = price_for(table, item.provider, item.model)
        if price is None:
            complete = complete and not (
                item.usage.input_tokens or item.usage.output_tokens or item.usage.web_searches
                or item.usage.web_results)
            continue
        currencies.add(price.currency.strip().upper())
        cached = min(max(item.usage.cached_input_tokens, 0), item.usage.input_tokens)
        cached_price = price.cached_input_per_million
        if cached and cached_price is None:
            complete = False
        cost += (item.usage.input_tokens - cached) / 1e6 * price.input_per_million
        cost += cached / 1e6 * (price.input_per_million if cached_price is None else cached_price)
        cost += item.usage.output_tokens / 1e6 * price.output_per_million
        billed = item.usage.web_searches + item.usage.web_results
        if billed:
            if price.web_search_per_thousand is None:
                complete = False
            else:
                cost += billed / 1000 * price.web_search_per_thousand
    if len(currencies) > 1:
        # Adding EUR and USD has no meaningful monetary value without a chosen exchange rate.
        return 0.0, False
    return cost, complete
