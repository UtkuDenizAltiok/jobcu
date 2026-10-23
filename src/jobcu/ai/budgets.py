"""Explicit local extra allowances, separate from ordinary monthly AI limits.

An allowance never creates a search or resets usage. Its opening balance includes earlier
spending; new receipts are tagged durably. Automatic selection requires the exact prepared
search, documents and AI settings. Other searches keep their ordinary monthly limits.
"""

import hashlib
import json
from dataclasses import asdict

from pydantic import BaseModel, Field, ValidationError

from jobcu import db, documents, review_capture
from jobcu.ai.base import AIBadRequest
from jobcu.ai.usage import UsageLog, estimate_cost
from jobcu.paths import ensure_data_dir
from jobcu.settings import SearchForm, Settings

FILENAME = "ai-extra-allowances.json"


class ExtraAllowance(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    ceiling: float = Field(gt=0, allow_inf_nan=False)
    currency: str = Field(min_length=1)
    price_currency: str = Field(min_length=1)
    cost_multiplier: float = Field(gt=0, allow_inf_nan=False)
    opening_spent: float = Field(ge=0, allow_inf_nan=False)
    opening_usage_complete: bool = False
    accounted_through_usage_id: int = Field(ge=0)
    search_fingerprint: str = Field(min_length=64, max_length=64)
    active: bool = True
    capture_required: bool = False


def load() -> list[ExtraAllowance]:
    try:
        values = json.loads((ensure_data_dir() / FILENAME).read_text(encoding="utf-8"))
        result = [ExtraAllowance.model_validate(value) for value in values]
        if len({item.id for item in result}) != len(result):
            raise ValueError("Duplicate allowance IDs")
        return result
    except FileNotFoundError:
        return []
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        raise AIBadRequest("Jobcu couldn't read the separate AI allowance. Check its local "
                           "record before starting; no allowance was reset.") from exc


def get(allowance_id: str) -> ExtraAllowance:
    for allowance in load():
        if allowance.id == allowance_id:
            return allowance
    raise AIBadRequest("The separate AI allowance is missing. Jobcu kept its usage; "
                       "restore the local allowance record before continuing.")


def fingerprint(settings: Settings, form: SearchForm) -> str:
    infos = [documents.get_info(kind) for kind in ("cv", "cover_letter")]
    identity = [form.model_dump(), settings.ai.model_dump(),
                [asdict(info) if info else None for info in infos]]
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()


def for_setup(settings: Settings, form: SearchForm) -> str | None:
    allowances = [item for item in load() if item.active]
    if not allowances:
        return None
    identity = fingerprint(settings, form)
    selected = [item.id for item in allowances if item.search_fingerprint == identity]
    if len(selected) > 1:
        raise AIBadRequest("More than one extra allowance matches this search. "
                           "Choose one in the local allowance record before starting.")
    return selected[0] if selected else None


def for_search(search_id: int) -> str | None:
    with db.connect() as conn:
        row = conn.execute("SELECT budget_id FROM searches WHERE id=?", (search_id,)).fetchone()
    return row[0] if row else None


def summary(allowance: ExtraAllowance, settings: Settings) -> dict:
    usage = UsageLog().for_budget(allowance.id, after_id=allowance.accounted_through_usage_id)
    cost, complete = estimate_cost(usage, settings.prices)
    spent = allowance.opening_spent + cost * allowance.cost_multiplier
    return {"id": allowance.id, "label": allowance.label, "currency": allowance.currency,
            "ceiling": allowance.ceiling, "spent": round(spent, 6),
            "remaining": round(max(0, allowance.ceiling - spent), 6),
            "cost_is_complete": complete and allowance.opening_usage_complete,
            "active": allowance.active}


def check_preparation(allowance_id: str | None) -> None:
    if allowance_id is None or not get(allowance_id).capture_required:
        return
    if not review_capture.is_armed():
        raise AIBadRequest("Comparison evidence capture is not ready. Prepare the trial before "
                           "starting; no job-site or AI request has been sent.")
