"""Records the tokens every AI request uses, for the usage meter and monthly limits."""

import calendar
from collections import Counter
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
# Providers that don't bill a request which ended without a usage report: one they failed, or
# one cancelled before its answer. Google's billing report by SKU showed it on three search
# days (November 2026): its token counts equalled the finished requests' to the token, and its
# search queries were theirs within 5%, while the unfinished requests held as many searches
# again. Elsewhere such searches still count: nothing measured says they are free.
UNFINISHED_REQUESTS_FREE = frozenset({"gemini"})
_UNFINISHED = "unreported_requests > 0 AND input_tokens = 0 AND output_tokens = 0"


def billing_month_start(now: datetime) -> datetime:
    local = now.astimezone(BILLING_ZONE)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)


def _billing_month(created_at: str) -> tuple[int, int]:
    """The provider's billing month (Pacific time) of a usage record's time."""
    moment = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    local = moment.astimezone(BILLING_ZONE)
    return local.year, local.month


def free_allowances(settings) -> dict[str, int]:
    """The free web searches a month of the research provider, from Settings: Google gives 5,000
    a month, shared by its Gemini 3 and newer models, then bills $14 a thousand (pricing page,
    read 2026-11-28). Its bill showed a search's 351 searches under its free search item, at
    nothing, while Jobcu's estimate had priced them at $4.91."""
    allowance = settings.limits.free_web_searches
    provider = settings.ai.research_provider or settings.ai.provider
    return {provider: allowance} if allowance and provider else {}


def billing_days_left(now: datetime) -> int:
    """Days left in the billing month, today included."""
    local = now.astimezone(BILLING_ZONE)
    return calendar.monthrange(local.year, local.month)[1] - local.day + 1


@dataclass
class ModelUsage:
    provider: str
    model: str
    usage: Usage
    # Of `usage.web_searches`, those seen inside requests the provider doesn't bill
    # (`billed_searches`): they stay on record and are never priced.
    unbilled_searches: int = 0
    # Of the billed search units, those inside the provider's free searches of their month
    # (`UsageLog.free_searches`): they count against the allowance and cost nothing.
    free_search_units: int = 0

    @property
    def billed_search_units(self) -> int:
        """What the provider bills for searching: queries and result pages."""
        return self.usage.web_searches - self.unbilled_searches + self.usage.web_results

    @property
    def paid_search_units(self) -> int:
        """The billed search units past the free monthly searches: those that cost money."""
        return max(0, self.billed_search_units - self.free_search_units)


class UsageLog:
    def __init__(self, folder: Path | None = None, *,
                 free_searches: dict[str, int] | None = None) -> None:
        self.folder = folder
        # Free web search units a month per provider (`free_allowances`): usage read through
        # this log prices only the searches past them.
        self.free_searches = free_searches or {}

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
        allowance included: they all come out of the provider's free monthly searches.
        Searches the provider doesn't bill (`billed_searches`) are left out."""
        start = billing_month_start(now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%S")
        with db.connect(self.folder) as conn:
            return conn.execute(
                "SELECT COALESCE(SUM(web_searches + web_results), 0) FROM ai_usage "
                f"WHERE provider = ? AND created_at >= ? AND {_BILLED}",
                (provider, start)).fetchone()[0]

    def web_searches_of_search(self, search_id: int, *, without_step: str) -> int:
        """Billed search queries of one search so far, outside a step with its own allowance."""
        with db.connect(self.folder) as conn:
            return conn.execute(
                "SELECT COALESCE(SUM(web_searches), 0) FROM ai_usage "
                f"WHERE search_id = ? AND step != ? AND {_BILLED}",
                (search_id, without_step)).fetchone()[0]

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

    def billed_searches_by_step(self, search_id: int) -> dict[str, int]:
        """Billed search queries per step of one search, for "Search details"."""
        with db.connect(self.folder) as conn:
            return dict(conn.execute(
                "SELECT step, SUM(web_searches) FROM ai_usage "
                f"WHERE search_id = ? AND {_BILLED} GROUP BY step", (search_id,)).fetchall())

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
                    SUM(unreported_requests), SUM(web_results),
                    SUM(CASE WHEN {_BILLED} THEN 0 ELSE web_searches END)
                    FROM ai_usage WHERE {where} GROUP BY provider, model""",
                params,
            ).fetchall()
            free = self._free_units(conn, where, params) if self.free_searches else Counter()
        usages = [ModelUsage(row[0], row[1], Usage(*row[2:9]), row[9]) for row in rows]
        for item in usages:
            item.free_search_units = min(item.billed_search_units,
                                         free[(item.provider, item.model)])
        return usages

    def _free_units(self, conn, where: str, params: tuple) -> Counter:
        """Of the billed search units of the records matching `where`, those inside their
        provider's free searches: each billing month's allowance (Pacific time) is used up in
        the order the requests were made, by every step and search."""
        found: Counter = Counter()
        wanted = {row_id: (provider, model) for row_id, provider, model in conn.execute(
            f"SELECT id, provider, model FROM ai_usage WHERE ({where}) AND {_BILLED} "
            "AND web_searches + web_results > 0", params)}
        if not wanted:
            return found
        for provider, allowance in self.free_searches.items():
            used: Counter = Counter()
            for row_id, created_at, units in conn.execute(
                    "SELECT id, created_at, web_searches + web_results FROM ai_usage "
                    f"WHERE provider = ? AND {_BILLED} AND web_searches + web_results > 0 "
                    "AND id <= ? ORDER BY id", (provider, max(wanted))):
                month = _billing_month(created_at)
                inside = max(0, min(units, allowance - used[month]))
                used[month] += units
                if inside and row_id in wanted:
                    found[wanted[row_id]] += inside
        return found


_BILLED = "NOT (provider IN ({}) AND {})".format(
    ", ".join(f"'{provider}'" for provider in sorted(UNFINISHED_REQUESTS_FREE)), _UNFINISHED)


def billed_searches(provider: str, usage: Usage) -> int:
    """The search queries of one request that its provider bills: none when the request ended
    without a usage report at a provider that doesn't bill such requests."""
    unfinished = usage.unreported_requests and not (usage.input_tokens or usage.output_tokens)
    return 0 if unfinished and provider in UNFINISHED_REQUESTS_FREE else usage.web_searches


FLEX = " (flex)"
BATCH = " (batch)"
# Google's Flex and Batch prices are half of every standard token price; search fees are not
# reduced.
FLEX_SHARE = 0.5
TIER_SUFFIXES = {"flex": FLEX, "batch": BATCH}


def billed_model(model: str, usage: Usage) -> str:
    """Flex and Batch usage are kept apart from the same model's normal-price usage."""
    suffix = TIER_SUFFIXES.get(usage.service_tier)
    return model + suffix if suffix and not model.endswith(suffix) else model


def price_for(prices: dict[tuple[str, str], ModelPrice], provider: str,
              model: str) -> ModelPrice | None:
    """The saved price; Flex or Batch usage without its own row costs half the model's normal
    tokens."""
    price = prices.get((provider, model))
    suffix = next((suffix for suffix in (FLEX, BATCH) if model.endswith(suffix)), None)
    if price is None and suffix is not None:
        normal = prices.get((provider, model.removesuffix(suffix)))
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

    Price reported usage before account credits, taxes and other service fees. Thinking is
    already included in output. Missing cache prices use the regular input price; missing
    search prices omit those fees. Either omission makes the estimate incomplete. Searches
    the provider doesn't bill (`ModelUsage.unbilled_searches`) cost nothing: one search's
    estimate priced 553 searches where the provider's report billed 431 (November 2026).
    Nor do searches inside the free monthly searches (`ModelUsage.free_search_units`, read
    through a log that knows the allowance).
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
                item.usage.input_tokens or item.usage.output_tokens
                or item.paid_search_units)
            continue
        currencies.add(price.currency.strip().upper())
        cached = min(max(item.usage.cached_input_tokens, 0), item.usage.input_tokens)
        cached_price = price.cached_input_per_million
        if cached and cached_price is None:
            complete = False
        cost += (item.usage.input_tokens - cached) / 1e6 * price.input_per_million
        cost += cached / 1e6 * (price.input_per_million if cached_price is None else cached_price)
        cost += item.usage.output_tokens / 1e6 * price.output_per_million
        paid = item.paid_search_units
        if paid:
            if price.web_search_per_thousand is None:
                complete = False
            else:
                cost += paid / 1000 * price.web_search_per_thousand
    if len(currencies) > 1:
        # Adding EUR and USD has no meaningful monetary value without a chosen exchange rate.
        return 0.0, False
    return cost, complete
