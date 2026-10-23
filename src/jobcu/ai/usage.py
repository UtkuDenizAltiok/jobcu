"""Records the tokens every AI request uses, for the usage meter and monthly limits."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from jobcu import db
from jobcu.ai.base import Usage
from jobcu.settings import ModelPrice


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
                        unreported_requests=MIN(unreported_requests,?) WHERE id=?""",
                        (usage.input_tokens, usage.output_tokens, usage.cached_input_tokens,
                         usage.reasoning_tokens, usage.web_searches, usage.unreported_requests,
                         previous[0]))
                    return
            conn.execute(
                """INSERT INTO ai_usage (search_id, step, provider, model, input_tokens,
                   output_tokens, cached_input_tokens, reasoning_tokens, web_searches,
                   unreported_requests, recovery_id, budget_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           COALESCE(?,strftime('%Y-%m-%dT%H:%M:%fZ','now')))""",
                (search_id, step, provider, model, usage.input_tokens, usage.output_tokens,
                 usage.cached_input_tokens, usage.reasoning_tokens, usage.web_searches,
                 usage.unreported_requests, recovery_id, budget_id, created_at),
            )

    def this_month(self, now: datetime | None = None) -> list[ModelUsage]:
        now = now or datetime.now(UTC)
        month_start = now.strftime("%Y-%m-01T00:00:00")
        return self._by_model("created_at >= ?", (month_start,))

    def ordinary_this_month(self, now: datetime | None = None) -> list[ModelUsage]:
        now = now or datetime.now(UTC)
        return self._by_model("created_at >= ? AND budget_id IS NULL",
                              (now.strftime("%Y-%m-01T00:00:00"),))

    def for_budget(self, budget_id: str, *, after_id: int = 0) -> list[ModelUsage]:
        return self._by_model("budget_id = ? AND id > ?", (budget_id, after_id))

    def for_search(self, search_id: int) -> dict[str, Usage]:
        """Usage per step of one search, for "Search details"."""
        with db.connect(self.folder) as conn:
            rows = conn.execute(
                """SELECT step, SUM(input_tokens), SUM(output_tokens), SUM(cached_input_tokens),
                   SUM(reasoning_tokens), SUM(web_searches), SUM(unreported_requests)
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
                    SUM(unreported_requests)
                    FROM ai_usage WHERE {where} GROUP BY provider, model""",
                params,
            ).fetchall()
        return [ModelUsage(row[0], row[1], Usage(*row[2:])) for row in rows]


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
        price = table.get((item.provider, item.model))
        if price is None:
            complete = complete and not (
                item.usage.input_tokens or item.usage.output_tokens or item.usage.web_searches)
            continue
        currencies.add(price.currency.strip().upper())
        cached = min(max(item.usage.cached_input_tokens, 0), item.usage.input_tokens)
        cached_price = price.cached_input_per_million
        if cached and cached_price is None:
            complete = False
        cost += (item.usage.input_tokens - cached) / 1e6 * price.input_per_million
        cost += cached / 1e6 * (price.input_per_million if cached_price is None else cached_price)
        cost += item.usage.output_tokens / 1e6 * price.output_per_million
        if item.usage.web_searches:
            if price.web_search_per_thousand is None:
                complete = False
            else:
                cost += item.usage.web_searches / 1000 * price.web_search_per_thousand
    if len(currencies) > 1:
        # Adding EUR and USD has no meaningful monetary value without a chosen exchange rate.
        return 0.0, False
    return cost, complete
