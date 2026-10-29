import pytest
from fastapi.testclient import TestClient

from jobcu.ai.base import Usage
from jobcu.ai.usage import UsageLog
from jobcu.app import create_app
from jobcu.keystore import KeyStore
from jobcu.settings import load_settings, save_settings

HEADERS = {"X-Jobcu": "1"}


@pytest.fixture
def client():
    return TestClient(create_app(), base_url="http://127.0.0.1:8765")


def test_settings_list_providers_alphabetically_with_no_default(client):
    data = client.get("/api/settings").json()
    names = [p["name"] for p in data["providers"]]
    assert names == sorted(names[:-1]) + ["Other API"]
    assert data["ai"]["provider"] is None
    assert all(not p["key"]["saved"] for p in data["providers"])


def test_keys_are_saved_masked_and_removed(client):
    value = "fake-" + "k" * 20 + "wxyz"
    saved = client.put("/api/keys/reed_api_key", json={"value": value}, headers=HEADERS).json()
    assert saved == {"name": "reed_api_key", "saved": True, "hint": "••••wxyz"}
    assert KeyStore().get("reed_api_key") == value
    assert value not in client.get("/api/settings").text
    client.delete("/api/keys/reed_api_key", headers=HEADERS)
    assert KeyStore().get("reed_api_key") is None


def test_unknown_key_names_are_refused(client):
    response = client.put("/api/keys/anything", json={"value": "x" * 20}, headers=HEADERS)
    assert response.status_code == 404


def test_ai_choice_is_saved(client):
    body = {"provider": "openai", "model": " some-model ", "reasoning_model": "", "base_url": ""}
    data = client.put("/api/settings/ai", json=body, headers=HEADERS).json()
    assert data["ai"]["model"] == "some-model"
    assert load_settings().ai.provider == "openai"


def test_custom_format_and_research_choice_save_without_calls_or_key_exposure(client):
    body = {"provider": "openai_compatible", "model": " main-example ",
            "base_url": " https://provider.example/v1 ", "compatible_protocol": "responses",
            "compatible_reasoning": "effort", "compatible_medium": "medium",
            "research_provider": "gemini", "research_model": " research-example "}
    data = client.put("/api/settings/ai", json=body, headers=HEADERS).json()
    assert data["ai"]["compatible_protocol"] == "responses"
    assert data["ai"]["research_model"] == "research-example"
    assert data["ai"]["scoring_effort"] == data["ai"]["reasoning_effort"] == "medium"
    assert [p["id"] for p in data["providers"] if p["can_research"]] == [
        "anthropic", "gemini", "openai", "mimo"]
    client.put("/api/settings/ai", json={"provider": "openai_compatible", "model": "another"},
               headers=HEADERS)
    assert load_settings().ai.research_provider == "gemini"
    assert load_settings().ai.compatible_protocol == "responses"


@pytest.mark.parametrize("field,value", [("compatible_protocol", "unknown"),
                                        ("compatible_medium", "low"),
                                        ("research_provider", "openai_compatible")])
def test_invalid_protocol_effort_and_unsupported_research_are_refused(client, field, value):
    response = client.put("/api/settings/ai", json={"provider": "openai", field: value},
                          headers=HEADERS)
    assert response.status_code == 422


def test_custom_model_list_uses_selected_protocol(client, monkeypatch):
    from jobcu import settings_api
    calls = []
    class Listed:
        def list_models(self):
            return ["fictional-model"]
    def configured(provider, key, ai, *, timeout):
        calls.append((provider, key, ai.compatible_protocol, ai.base_url, timeout))
        return Listed()
    monkeypatch.setattr(settings_api, "configured_adapter", configured)
    response = client.post("/api/ai/models", json={"provider": "openai_compatible",
                           "base_url": "https://provider.example/v1",
                           "compatible_protocol": "messages"}, headers=HEADERS)
    assert response.json()["models"] == ["fictional-model"]
    assert calls == [("openai_compatible", "", "messages", "https://provider.example/v1", 30)]


def test_openrouter_is_offered_with_its_key_page_and_needs_no_address(client, monkeypatch):
    from jobcu import settings_api
    router = next(p for p in client.get("/api/settings").json()["providers"]
                  if p["id"] == "openrouter")
    assert router["key_page"] == "https://openrouter.ai/settings/keys"
    assert not router["needs_base_url"] and not router["key_optional"]
    assert not router["can_research"] and "@" in router["model_hint"]
    calls = []
    class Listed:
        def list_models(self):
            return ["fictional/model"]
    def configured(provider, key, ai, *, timeout):
        calls.append((provider, key))
        return Listed()
    monkeypatch.setattr(settings_api, "configured_adapter", configured)
    client.put("/api/keys/ai_openrouter", json={"value": "fake-" + "r" * 20}, headers=HEADERS)
    response = client.post("/api/ai/models", json={"provider": "openrouter"}, headers=HEADERS)
    assert response.json() == {"models": ["fictional/model"], "error": None}
    assert calls == [("openrouter", "fake-" + "r" * 20)]


def test_research_probe_without_configuration_has_no_provider_calls(client):
    data = client.post("/api/ai/research-check", headers=HEADERS).json()
    assert not data["ok"] and "choose an online research provider and model" in data["message"]


def test_model_list_needs_a_saved_key(client):
    data = client.post("/api/ai/models", json={"provider": "anthropic"}, headers=HEADERS).json()
    assert data["models"] == [] and "save your key" in data["error"]


def test_job_site_check_without_keys_explains_what_to_do(client):
    data = client.post("/api/job-sites/adzuna/check", headers=HEADERS).json()
    assert not data["ok"]
    assert data["message"] == "Please save both the Application ID and the Application Key."


def test_unknown_job_site_is_refused(client):
    assert client.post("/api/job-sites/nowhere/check", headers=HEADERS).status_code == 404


def test_usage_shows_the_month_the_last_search_and_the_sources(client):
    from datetime import UTC, datetime

    from jobcu import db
    from jobcu.ai.base import Usage
    from jobcu.ai.usage import UsageLog

    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (7, 'finished', '{}')")
        conn.execute(
            "INSERT INTO source_requests (day, source, count) VALUES (?, 'adzuna', 12)",
            (datetime.now(UTC).strftime("%Y-%m-%d"),),
        )
    UsageLog().record(step="scoring", provider="openai", model="a-model",
                      usage=Usage(input_tokens=1_000_000, output_tokens=500_000), search_id=7)

    data = client.get("/api/usage", headers=HEADERS).json()
    assert data["this_month"]["tokens"] == 1_500_000
    assert data["this_month"]["cost_is_complete"] is False  # no prices saved yet
    assert data["last_search"]["tokens"] == 1_500_000
    adzuna = next(s for s in data["sources"] if s["id"] == "adzuna")
    assert adzuna["requests_today"] == 12 and adzuna["enabled"]
    assert {s["id"] for s in data["sources"]} >= {"jobsireland", "workday", "arbeitnow"}

    # The user's own price table turns tokens into money.
    prices = [{"provider": "openai", "model": "a-model", "input_per_million": 2,
               "output_per_million": 8, "currency": "EUR"}]
    data = client.put("/api/settings/prices", json={"prices": prices}, headers=HEADERS).json()
    assert data["this_month"]["cost"] == 6.0 and data["this_month"]["cost_is_complete"]
    assert data["last_search"]["cost"] == 6.0 and data["this_month"]["currency"] == "EUR"


def test_missing_request_usage_stays_visible_with_zero_known_tokens_and_saved_prices(client):
    from jobcu.ai.base import Usage
    from jobcu.ai.usage import UsageLog

    UsageLog().record(step="employers", provider="gemini", model="fictional-model",
                      usage=Usage(unreported_requests=2))
    prices = [{"provider": "gemini", "model": "fictional-model", "input_per_million": 1,
               "output_per_million": 2, "currency": "EUR"}]
    data = client.put("/api/settings/prices", json={"prices": prices}, headers=HEADERS).json()
    month = data["this_month"]
    assert month["tokens"] == 0 and month["cost"] == 0
    assert not month["cost_is_complete"] and month["unreported_requests"] == 2
    assert month["by_model"][0]["unreported_requests"] == 2


def test_limits_and_source_switches_are_saved(client):
    data = client.put("/api/settings/limits", headers=HEADERS, json={
        "scoring_cap": 40, "monthly_token_limit": 2_000_000, "monthly_cost_limit": 25.0,
    }).json()
    assert data["limits"]["scoring_cap"] == 40
    assert data["limits"]["monthly_token_limit"] == 2_000_000
    assert data["limits"]["web_search_cap"] is None  # not sent: default remains unlimited
    data = client.put("/api/settings/limits", headers=HEADERS, json={
        "scoring_cap": 40, "web_search_cap": 20}).json()
    assert data["limits"]["web_search_cap"] == 20 and load_settings().limits.web_search_cap == 20
    data = client.put("/api/settings/limits", headers=HEADERS, json={"scoring_cap": 40}).json()
    assert data["limits"]["web_search_cap"] == 20  # not sent: the saved choice is preserved
    # An empty box means no limit.
    data = client.put("/api/settings/limits", headers=HEADERS, json={
        "scoring_cap": None, "web_search_cap": None}).json()
    assert data["limits"]["scoring_cap"] is None and data["limits"]["web_search_cap"] is None
    assert load_settings().limits.scoring_cap is None

    assert data["free_web_searches"] is None  # not set: nothing to count
    settings = load_settings()
    settings.ai.provider = "gemini"
    save_settings(settings)
    UsageLog().record(step="job_places", provider="gemini", model="fictional-model",
                      usage=Usage(10, 5, web_searches=12))
    data = client.put("/api/settings/limits", headers=HEADERS,
                      json={"free_web_searches": 5000}).json()
    assert data["limits"]["free_web_searches"] == 5000
    assert data["free_web_searches"] == {"provider": "gemini", "allowance": 5000, "used": 12}
    data = client.put("/api/settings/limits", headers=HEADERS, json={"scoring_cap": 40}).json()
    assert data["limits"]["free_web_searches"] == 5000  # not sent: the saved choice is preserved

    data = client.put("/api/settings/sources", headers=HEADERS,
                      json={"disabled": ["workday", "not-a-source"]}).json()
    switched_off = {s["id"] for s in data["sources"] if not s["enabled"]}
    # Optional sources need a positive opt-in.
    assert switched_off == {"workday", "jsearch", "bundesagentur"}
    assert load_settings().sources_disabled == ["workday"]


def test_a_source_with_restrictive_terms_says_so_and_runs_only_when_switched_on(client):
    from jobcu.settings import save_settings
    from jobcu.sources import accepted_terms

    data = client.get("/api/usage", headers=HEADERS).json()
    source = next(s for s in data["sources"] if s["id"] == "bundesagentur")
    assert not source["enabled"] and "terms" in source["note"] and not source["needs_key"]
    assert accepted_terms(load_settings()) == frozenset()

    data = client.put("/api/settings/sources", headers=HEADERS,
                      json={"disabled": [], "enabled": ["bundesagentur"]}).json()
    assert next(s for s in data["sources"] if s["id"] == "bundesagentur")["enabled"]
    assert accepted_terms(load_settings()) == {"bundesagentur"}
    settings = load_settings()
    settings.sources_disabled = ["bundesagentur"]  # switched off again: no longer accepted
    save_settings(settings)
    assert accepted_terms(load_settings()) == frozenset()


def test_jsearch_key_and_legacy_source_choice_do_not_enable_optional_source(client):
    value = "fictional-jsearch-key-123456"
    response = client.put("/api/keys/jsearch_api_key", json={"value": value}, headers=HEADERS)
    assert response.status_code == 200 and value not in client.get("/api/settings").text
    response = client.put("/api/settings/sources", json={"disabled": []}, headers=HEADERS)
    source = next(s for s in response.json()["sources"] if s["id"] == "jsearch")
    assert not source["enabled"] and source["unit"] == "credits reserved"
    assert load_settings().source_opt_ins == []


def test_optional_source_needs_positive_choice_and_preserves_other_limits(client):
    from jobcu.settings import save_settings

    settings = load_settings()
    settings.limits.monthly_cost_limit = 18
    settings.sources_disabled = ["workday"]
    save_settings(settings)
    client.put("/api/settings/sources", headers=HEADERS,
               json={"disabled": ["workday"], "enabled": ["jsearch", "unknown"]})
    settings = load_settings()
    assert settings.source_opt_ins == ["jsearch"]
    assert settings.sources_disabled == ["workday"] and settings.limits.monthly_cost_limit == 18
    client.put("/api/settings/sources", headers=HEADERS, json={"disabled": ["workday"]})
    assert load_settings().source_opt_ins == ["jsearch"]  # older client preserves the choice
    client.put("/api/settings/sources", headers=HEADERS,
               json={"disabled": ["jsearch"], "enabled": ["jsearch"]})
    assert load_settings().source_opt_ins == []


def test_jsearch_account_check_without_key_sends_no_query(client):
    response = client.post("/api/job-sites/jsearch/check", headers=HEADERS).json()
    assert not response["ok"] and "Free key" in response["message"]


def test_recovery_requires_explicit_choice_and_survives_older_settings_clients(client):
    assert client.get('/api/settings').json()['ai']['recover_interrupted_requests'] is False
    body = {'provider': 'gemini', 'model': 'fictional-model',
            'recover_interrupted_requests': True}
    assert client.put('/api/settings/ai', json=body, headers=HEADERS).status_code == 200
    client.put('/api/settings/ai', json={'provider': 'gemini', 'model': 'changed-model'},
               headers=HEADERS)
    data = client.get('/api/settings').json()
    assert data['ai']['recover_interrupted_requests'] is True
    assert [p['id'] for p in data['providers'] if p['can_recover_requests']] == ['gemini']
    client.put('/api/settings/ai', json={'provider': 'gemini',
               'recover_interrupted_requests': False}, headers=HEADERS)
    assert load_settings().ai.recover_interrupted_requests is False


def test_the_recommended_setup_is_one_step_and_keeps_everything_else(client):
    settings = load_settings()
    settings.ai.provider, settings.ai.model = "openrouter", "fictional/model"
    settings.ai.reasoning_model = "fictional/thinker"
    settings.ai.research_provider, settings.ai.research_model = "anthropic", "fictional-claude"
    settings.limits.monthly_cost_limit = 40
    save_settings(settings)
    data = client.post("/api/settings/recommended", headers=HEADERS).json()
    ai = data["ai"]
    assert (ai["provider"], ai["model"], ai["reasoning_model"]) == (
        "gemini", "gemini-3.8-flash", "")
    assert ai["research_provider"] is None and ai["research_model"] == ""
    assert ai["flex_processing"] and ai["recover_interrupted_requests"]
    assert (ai["scoring_effort"], ai["reasoning_effort"]) == ("medium", "medium")
    saved = load_settings()
    assert saved.limits.free_web_searches == 5000 and saved.limits.monthly_cost_limit == 40
    assert client.post("/api/settings/recommended").status_code in (400, 403)  # needs X-Jobcu


def test_a_search_like_the_recent_ones_is_estimated_before_it_starts(client):
    from jobcu import db

    settings = load_settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    settings.limits.free_web_searches = 5000
    save_settings(settings)
    client.put("/api/settings/prices", headers=HEADERS, json={"prices": [
        {"provider": "gemini", "model": "fictional-model", "input_per_million": 1,
         "output_per_million": 10, "web_search_per_thousand": 14}]})
    log = UsageLog()
    with db.connect() as conn:
        for search_id, status in ((1, "finished"), (2, "finished"), (3, "failed"), (4, "finished")):
            conn.execute("INSERT INTO searches (id, status, form_json) VALUES (?, ?, '{}')",
                         (search_id, status))
    for search_id, output, searches in ((1, 100_000, 50), (2, 200_000, 80), (3, 900_000, 0),
                                        (4, 300_000, 120)):
        log.record(step="scoring", provider="gemini", model="fictional-model",
                   usage=Usage(input_tokens=100_000, output_tokens=output,
                               web_searches=searches), search_id=search_id)
    typical = client.get("/api/usage").json()["typical_search"]
    # The median of the finished searches; web searches are counted, not priced.
    assert typical["searches"] == 3 and typical["tokens"] == 300_000
    assert typical["token_cost"] == 2.1 and typical["web_searches"] == 80
    settings = load_settings()
    settings.ai.model = "another-model"
    save_settings(settings)
    assert client.get("/api/usage").json()["typical_search"] is None
