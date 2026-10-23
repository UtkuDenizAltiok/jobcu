"""Extra trial spending never consumes or resets an ordinary monthly allowance."""

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from jobcu import db
from jobcu.ai import budgets
from jobcu.ai.base import AILimitReached, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.usage import UsageLog, estimate_cost
from jobcu.app import create_app
from jobcu.settings import ModelPrice, SearchForm, Settings, load_settings, save_settings


def configure(folder):
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.limits.monthly_cost_limit = 1
    settings.limits.monthly_token_limit = 1_000_000
    settings.prices = [ModelPrice(provider="gemini", model="fictional-model",
                                  input_per_million=1, output_per_million=1)]
    save_settings(settings)
    log = UsageLog()
    log.record(step="scoring", provider="gemini", model="fictional-model",
               usage=Usage(900_000), search_id=None)
    log.record(step="scoring", provider="gemini", model="fictional-model",
               usage=Usage(3_000_000), search_id=None, budget_id="fictional-extra")
    allowance = budgets.ExtraAllowance(
        id="fictional-extra", label="Fictional extra evaluation", ceiling=5, currency="EUR",
        price_currency="USD", cost_multiplier=1, opening_spent=3,
        accounted_through_usage_id=2, search_fingerprint=budgets.fingerprint(
            settings, settings.search_form))
    (folder / budgets.FILENAME).write_text(json.dumps([allowance.model_dump()]), encoding="utf-8")
    return settings, log, allowance


def test_ordinary_and_extra_limits_are_independent_with_previous_spending(temporary_data_dir):
    settings, log, allowance = configure(temporary_data_dir)
    assert estimate_cost(log.this_month(), settings.prices)[0] == pytest.approx(3.9)
    AIClient(settings, usage_log=log).check_search_budget()  # ordinary use is only 0.9
    extra = AIClient(settings, usage_log=log, budget_id=allowance.id)
    extra.check_search_budget()  # prior extra spending is 3 of 5, not a fresh 5
    log.record(step="scoring", provider="gemini", model="fictional-model",
               usage=Usage(2_000_000), budget_id=allowance.id)
    with pytest.raises(AILimitReached, match="separate extra"):
        extra.check_search_budget()
    AIClient(settings, usage_log=log).check_search_budget()
    assert budgets.summary(allowance, settings)["spent"] == 5
    assert load_settings().limits == settings.limits


def test_an_exhausted_ordinary_budget_does_not_block_a_bounded_extra(temporary_data_dir):
    settings, log, allowance = configure(temporary_data_dir)
    log.record(step="scoring", provider="gemini", model="fictional-model",
               usage=Usage(200_000))
    with pytest.raises(AILimitReached):
        AIClient(settings, usage_log=log).check_search_budget()
    AIClient(settings, usage_log=log, budget_id=allowance.id).check_search_budget()


def test_allowance_selection_requires_exact_prepared_inputs(temporary_data_dir):
    settings, _, allowance = configure(temporary_data_dir)
    assert budgets.for_setup(settings, settings.search_form) == allowance.id
    assert budgets.for_setup(settings, SearchForm(posted_within_hours=72)) is None
    changed = settings.model_copy(deep=True)
    changed.ai.model = "another-model"
    assert budgets.for_setup(changed, settings.search_form) is None


def test_cumulative_receipt_and_search_reset_preserve_extra_attribution(temporary_data_dir):
    from jobcu import reset

    settings, log, allowance = configure(temporary_data_dir)
    with db.connect() as conn:
        conn.execute("INSERT INTO searches(id,status,form_json,budget_id) "
                     "VALUES(8,'failed','{}',?)", (allowance.id,))
    log.record(step="scoring", provider="gemini", model="fictional-model", search_id=8,
               recovery_id="fictional-operation", usage=Usage(100_000, unreported_requests=1))
    assert reset.clear_data("searches")
    log.record(step="scoring", provider="gemini", model="fictional-model", search_id=None,
               recovery_id="fictional-operation", usage=Usage(200_000))
    assert budgets.summary(allowance, settings)["spent"] == pytest.approx(3.2)
    assert estimate_cost(log.ordinary_this_month(), settings.prices)[0] == pytest.approx(0.9)
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ai_usage").fetchone()[0] == 3


def test_budget_meters_keep_combined_receipts_and_opening_uncertainty(temporary_data_dir):
    settings, _, _ = configure(temporary_data_dir)
    response = TestClient(create_app(), base_url="http://127.0.0.1").get("/api/usage").json()
    assert response["this_month"]["cost"] == 3.9
    assert response["ordinary_this_month"]["cost"] == 0.9
    assert response["extra_allowances"][0]["spent"] == 3
    assert not response["extra_allowances"][0]["cost_is_complete"]
    assert response["limits"]["monthly_cost_limit"] == settings.limits.monthly_cost_limit
    assert response["search_budget_problem"] is None


def test_ordinary_month_reset_does_not_reset_one_off_extra(temporary_data_dir):
    settings, log, allowance = configure(temporary_data_dir)
    log.record(step="scoring", provider="gemini", model="fictional-model",
               usage=Usage(500_000), budget_id=allowance.id, created_at="2026-01-01T00:00:00Z")
    assert not log.ordinary_this_month(datetime(2030, 1, 1, tzinfo=UTC))
    assert budgets.summary(allowance, settings)["spent"] == 3.5


def test_missing_or_consumed_capture_blocks_only_a_capture_required_trial(temporary_data_dir):
    from jobcu import review_capture, search
    from jobcu.ai.base import AIBadRequest

    settings, _, allowance = configure(temporary_data_dir)
    allowance.capture_required = True
    (temporary_data_dir / budgets.FILENAME).write_text(
        json.dumps([allowance.model_dump()]), encoding="utf-8")
    with pytest.raises(AIBadRequest, match="capture is not ready"):
        search.SearchManager().start(settings.search_form)
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0] == 0
    review_capture.arm_next_search()
    budgets.check_preparation(allowance.id)
    assert review_capture.claim(99, lambda _: None) is not None
    with pytest.raises(AIBadRequest):
        budgets.check_preparation(allowance.id)


def test_same_extra_receipts_keep_their_tag_after_restart_cleanup(temporary_data_dir):
    from jobcu.ai import request_recovery
    from jobcu.ai.request_recovery import RecoveryContext

    _, _, allowance = configure(temporary_data_dir)
    request_recovery.track(RecoveryContext(True, 'gemini', 'scoring', budget_id=allowance.id),
                           'fictional-pending', 'fictional-model')
    request_recovery.release('gemini', 'fictional-pending', deleted=False)
    row, = request_recovery.pending(force=True)
    assert row['budget_id'] == allowance.id


@pytest.mark.parametrize('change', ['closed', 'wrong_currency'])
def test_extra_allowance_cannot_silently_fall_back_to_ordinary(temporary_data_dir, change):
    settings, log, allowance = configure(temporary_data_dir)
    if change == 'closed':
        allowance.active = False
    else:
        allowance.price_currency = 'GBP'
    (temporary_data_dir / budgets.FILENAME).write_text(
        json.dumps([allowance.model_dump()]), encoding='utf-8')
    with pytest.raises(AILimitReached):
        AIClient(settings, usage_log=log, budget_id=allowance.id).check_search_budget()
    assert estimate_cost(log.ordinary_this_month(), settings.prices)[0] == pytest.approx(0.9)
