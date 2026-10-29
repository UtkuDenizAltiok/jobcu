"""Internal API behind the Settings screen: AI provider, model, keys, key checks, what has been
used this month, the limits, the price table and which job sources are on."""

import statistics
from dataclasses import replace
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jobcu import db, travel
from jobcu.ai import budgets
from jobcu.ai.base import AIError
from jobcu.ai.client import AIClient, check_research_setup, check_setup
from jobcu.ai.providers import PROVIDERS, configured_adapter
from jobcu.ai.usage import ModelUsage, UsageLog, estimate_cost, total_tokens
from jobcu.keystore import KeyStore, KeyStoreError, mask
from jobcu.settings import (
    AISettings,
    CompatibleMedium,
    CompatibleProtocol,
    CompatibleReasoning,
    LimitSettings,
    ModelPrice,
    ProviderId,
    ResearchProviderId,
    load_settings,
    save_settings,
)
from jobcu.sources import (
    OPT_IN_SOURCES,
    TERMS_NOTES,
    adzuna,
    all_sources,
    disabled_sources,
    jsearch,
    reed,
)
from jobcu.sources.http import PoliteClient

router = APIRouter(prefix="/api")

JOB_SITE_KEYS = {
    adzuna.KEY_APP_ID: "Adzuna Application ID",
    adzuna.KEY_APP_KEY: "Adzuna Application Key",
    reed.KEY_API_KEY: "Reed API key",
    jsearch.KEY_API_KEY: "JSearch direct Free key",
}
TRAVEL_KEYS = {travel.KEY_NAME: "Google Maps API key"}
ALLOWED_KEYS = ({info.key_name for info in PROVIDERS.values()} | set(JOB_SITE_KEYS)
                | set(TRAVEL_KEYS))


def _key_status(keys: KeyStore, name: str) -> dict:
    try:
        value = keys.get(name)
    except KeyStoreError:
        value = None
    return {"name": name, "saved": bool(value), "hint": mask(value) if value else None}


@router.get("/settings")
def get_settings() -> dict:
    settings = load_settings()
    keys = KeyStore()
    return {
        "ai": settings.ai.model_dump(),
        "providers": [
            {
                "id": info.id,
                "name": info.name,
                "key_page": info.key_page,
                "needs_base_url": info.needs_base_url,
                "key_optional": info.key_optional,
                "model_hint": info.model_hint,
                "can_research": info.adapter.can_search_the_web,
                "can_recover_requests": getattr(info.adapter, "can_recover_requests", False),
                "can_flex": getattr(info.adapter, "can_flex", False),
                "reasoning_notice": getattr(info.adapter, "reasoning_notice", ""),
                "key": _key_status(keys, info.key_name),
            }
            for info in PROVIDERS.values()
        ],
        "job_site_keys": [
            {**_key_status(keys, name), "label": label,
             "key_page": jsearch.KEY_PAGE if name == jsearch.KEY_API_KEY else None}
            for name, label in JOB_SITE_KEYS.items()
        ],
        "travel_keys": [
            {**_key_status(keys, name), "label": label} for name, label in TRAVEL_KEYS.items()
        ],
    }


class AIChoice(BaseModel):
    provider: ProviderId | None
    model: str = ""
    reasoning_model: str = ""
    base_url: str = ""
    compatible_protocol: CompatibleProtocol = "chat_completions"
    compatible_reasoning: CompatibleReasoning = "effort"
    compatible_medium: CompatibleMedium = "medium"
    research_provider: ResearchProviderId | None = None
    research_model: str = ""
    recover_interrupted_requests: bool = False
    flex_processing: bool = False


# Jobcu's measured recommendation (docs/SOURCES.md, Gemini running costs): one Gemini model for
# every step at Google's half-price Flex tier, which needs request recovery, and Google's free
# monthly web searches shared across searches. Other settings, keys and prices stay as they are.
RECOMMENDED_AI = {"provider": "gemini", "model": "gemini-3.8-flash", "reasoning_model": "",
                  "research_provider": None, "research_model": "", "flex_processing": True,
                  "recover_interrupted_requests": True, "scoring_effort": "medium",
                  "reasoning_effort": "medium"}
RECOMMENDED_FREE_WEB_SEARCHES = 5000


@router.post("/settings/recommended")
def use_recommended_setup() -> dict:
    settings = load_settings()
    settings.ai = AISettings.model_validate({**settings.ai.model_dump(), **RECOMMENDED_AI})
    settings.limits.free_web_searches = RECOMMENDED_FREE_WEB_SEARCHES
    save_settings(settings)
    return get_settings()


@router.put("/settings/ai")
def put_ai_settings(choice: AIChoice) -> dict:
    settings = load_settings()
    updates = choice.model_dump(exclude_unset=True)
    for name in ("model", "reasoning_model", "base_url", "research_model"):
        if name in updates:
            updates[name] = updates[name].strip()
    # Validate the complete result, preserving fields older clients don't send.
    settings.ai = AISettings.model_validate({**settings.ai.model_dump(), **updates})
    save_settings(settings)
    return get_settings()


class KeyValue(BaseModel):
    value: str


def _allowed(name: str) -> str:
    if name not in ALLOWED_KEYS:
        raise HTTPException(status_code=404, detail="Unknown key.")
    return name


@router.put("/keys/{name}")
def put_key(name: str, body: KeyValue) -> dict:
    keys = KeyStore()
    try:
        keys.set(_allowed(name), body.value)
    except KeyStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _key_status(keys, name)


@router.delete("/keys/{name}")
def delete_key(name: str) -> dict:
    keys = KeyStore()
    keys.delete(_allowed(name))
    return _key_status(keys, name)


class ModelListRequest(BaseModel):
    provider: ProviderId
    base_url: str = ""
    compatible_protocol: CompatibleProtocol = "chat_completions"


@router.post("/ai/models")
def list_models(request: ModelListRequest) -> dict:
    info = PROVIDERS[request.provider]
    key = KeyStore().get(info.key_name) or ""
    if not key and not info.key_optional:
        return {"models": [], "error": "Please save your key for this provider first."}
    if info.needs_base_url and not request.base_url.strip():
        return {"models": [], "error": "Please enter the provider's address first."}
    try:
        ai = AISettings(provider=request.provider, base_url=request.base_url,
                        compatible_protocol=request.compatible_protocol)
        models = configured_adapter(request.provider, key, ai, timeout=30).list_models()
    except AIError as exc:
        return {"models": [], "error": exc.message}
    return {"models": models, "error": None}


@router.post("/ai/check")
def check_ai() -> dict:
    result = check_setup(load_settings(), KeyStore(), usage_log=UsageLog())
    return {"ok": result.ok, "message": result.message}


@router.post("/ai/research-check")
def check_research_ai() -> dict:
    result = check_research_setup(load_settings(), KeyStore(), usage_log=UsageLog())
    return {"ok": result.ok, "message": result.message}


@router.post("/job-sites/{site}/check")
def check_job_site(site: str) -> dict:
    checks = {"adzuna": adzuna.check_keys, "reed": reed.check_keys,
              "jsearch": jsearch.check_keys}
    if site not in checks:
        raise HTTPException(status_code=404, detail="Unknown job site.")
    result = checks[site](KeyStore())
    return {"ok": result.ok, "message": result.message}


@router.post("/travel/check")
def check_travel() -> dict:
    http = PoliteClient()
    try:
        ok, message = travel.check_key(KeyStore(), http)
    finally:
        http.close()
    return {"ok": ok, "message": message}


class Limits(BaseModel):
    # Empty (None) means no limit; a cap not sent at all stays as it was.
    scoring_cap: int | None = Field(default=None, ge=1)
    web_search_cap: int | None = Field(default=None, ge=0)
    free_web_searches: int | None = Field(default=None, ge=0)
    searches_per_month: int | None = Field(default=None, ge=1, le=300)
    monthly_token_limit: int | None = None
    monthly_cost_limit: float | None = None
    maps_monthly_routes: int | None = None


@router.put("/settings/limits")
def put_limits(limits: Limits) -> dict:
    settings = load_settings()
    sent = limits.model_fields_set
    settings.limits = LimitSettings(
        scoring_cap=(limits.scoring_cap if "scoring_cap" in sent
                     else settings.limits.scoring_cap),
        web_search_cap=(limits.web_search_cap if "web_search_cap" in sent
                        else settings.limits.web_search_cap),
        free_web_searches=(limits.free_web_searches if "free_web_searches" in sent
                           else settings.limits.free_web_searches),
        searches_per_month=(limits.searches_per_month if "searches_per_month" in sent
                            else settings.limits.searches_per_month),
        monthly_token_limit=limits.monthly_token_limit,
        monthly_cost_limit=limits.monthly_cost_limit,
        maps_monthly_routes=(limits.maps_monthly_routes if limits.maps_monthly_routes is not None
                             else settings.limits.maps_monthly_routes),
    )
    save_settings(settings)
    return get_usage()


class Prices(BaseModel):
    prices: list[ModelPrice]


@router.put("/settings/prices")
def put_prices(body: Prices) -> dict:
    settings = load_settings()
    settings.prices = body.prices
    save_settings(settings)
    return get_usage()


class SourceChoice(BaseModel):
    disabled: list[str]
    enabled: list[str] | None = None


@router.put("/settings/sources")
def put_sources(choice: SourceChoice) -> dict:
    known = {source.id for source in all_sources()}
    settings = load_settings()
    settings.sources_disabled = sorted(set(choice.disabled) & known)
    if choice.enabled is not None:
        settings.source_opt_ins = sorted(set(choice.enabled) & OPT_IN_SOURCES -
                                        set(settings.sources_disabled))
    save_settings(settings)
    return get_usage()


def _source_requests(now: datetime) -> tuple[dict[str, int], dict[str, int]]:
    day = now.strftime("%Y-%m-%d")
    with db.connect() as conn:
        today = conn.execute(
            "SELECT source, SUM(count) AS used FROM source_requests WHERE day = ? GROUP BY source",
            (day,),
        ).fetchall()
        month = conn.execute(
            "SELECT source, SUM(count) AS used FROM source_requests "
            "WHERE substr(day, 1, 7) = ? GROUP BY source",
            (day[:7],),
        ).fetchall()
    return ({row["source"]: row["used"] for row in today},
            {row["source"]: row["used"] for row in month})


def _money(usages: list[ModelUsage], prices: list[ModelPrice]) -> dict:
    cost, complete = estimate_cost(usages, prices)
    currencies = {price.currency for price in prices} or {"USD"}
    return {"tokens": total_tokens(usages), "cost": round(cost, 2), "cost_is_complete": complete,
            "currency": currencies.pop() if len(currencies) == 1 else "",
            "unreported_requests": sum(item.usage.unreported_requests for item in usages)}


def _free_web_searches(settings, log: UsageLog, now: datetime) -> dict | None:
    """The research provider's free web searches used in its billing month (Pacific time)."""
    provider = settings.ai.research_provider or settings.ai.provider
    if settings.limits.free_web_searches is None or provider is None:
        return None
    return {"provider": provider, "allowance": settings.limits.free_web_searches,
            "used": log.web_searches_this_month(provider, now)}


# Recent finished searches with today's main AI that describe what the next search will use.
TYPICAL_SEARCHES = 3


def _typical_search(settings, log: UsageLog) -> dict | None:
    """What a search like the recent ones used with today's main AI: the median of the last
    finished searches that used it, so the cost of a search is known before it starts."""
    provider, model = settings.ai.provider, settings.ai.model.strip()
    if not provider or not model:
        return None
    with db.connect() as conn:
        ids = [row[0] for row in conn.execute(
            "SELECT id FROM searches WHERE status = 'finished' ORDER BY id DESC LIMIT 30")]
    picked = []
    for search_id in ids:
        used = log.for_search_by_model(search_id)
        if any(item.provider == provider and item.model in (model, f"{model} (flex)")
               for item in used):
            picked.append(used)
        if len(picked) == TYPICAL_SEARCHES:
            break
    if not picked:
        return None
    # Tokens are priced here; web searches are counted, since free allowances may cover them.
    tokens_only = [[replace(item, usage=replace(item.usage, web_searches=0, web_results=0))
                    for item in used] for used in picked]
    costs = [estimate_cost(used, settings.prices) for used in tokens_only]
    currencies = {price.currency for price in settings.prices} or {"USD"}
    return {
        "searches": len(picked),
        "tokens": round(statistics.median(total_tokens(used) for used in picked)),
        "token_cost": round(statistics.median(cost for cost, _ in costs), 2),
        "cost_is_complete": all(complete for _, complete in costs),
        "currency": currencies.pop() if len(currencies) == 1 else "",
        "web_searches": round(statistics.median(
            sum(item.usage.web_searches for item in used) for used in picked)),
    }


@router.get("/usage")
def get_usage(now: datetime | None = None) -> dict:
    """What has been used this month and in the last search, and the state of every source."""
    now = now or datetime.now(UTC)
    settings = load_settings()
    log = UsageLog()
    this_month = log.this_month(now)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id, started_at, status FROM searches ORDER BY id DESC LIMIT 1"
        ).fetchone()
    last_search = None
    if row is not None:
        used = log.for_search_by_model(row["id"])
        last_search = {"started_at": row["started_at"], **_money(used, settings.prices)}
    today, month = _source_requests(now)
    budget_problem = None
    extra_allowances = []
    try:
        extra_allowances = budgets.load()
        budget_id = budgets.for_setup(settings, settings.search_form)
        AIClient(settings, usage_log=log, budget_id=budget_id).check_search_budget()
        if row is None or row["status"] != "running":
            budgets.check_preparation(budget_id)
    except AIError as exc:
        budget_problem = exc.message
    return {
        "search_budget_problem": budget_problem,
        "ordinary_this_month": _money(log.ordinary_this_month(now), settings.prices),
        "extra_allowances": [budgets.summary(item, settings) for item in extra_allowances],
        "this_month": {
            **_money(this_month, settings.prices),
            "by_model": [
                {"provider": item.provider, "model": item.model,
                 **_money([item], settings.prices)}
                for item in sorted(this_month, key=lambda i: (i.provider, i.model))
            ],
        },
        "last_search": last_search,
        "typical_search": _typical_search(settings, log),
        "free_web_searches": _free_web_searches(settings, log, now),
        "travel": {"routes_this_month": month.get("google_maps_routes", 0)},
        "limits": settings.limits.model_dump(),
        "prices": [price.model_dump() for price in settings.prices],
        "sources": [
            {
                "id": source.id,
                "name": source.name,
                "enabled": source.id not in disabled_sources(settings),
                "requests_today": today.get(source.id, 0),
                "requests_this_month": month.get(source.id, 0),
                "needs_key": bool(source.unavailable_reason(KeyStore())),
                "unit": "credits reserved" if source.id == "jsearch" else "requests",
                "note": TERMS_NOTES.get(source.id, ""),
            }
            for source in all_sources()
        ],
    }
