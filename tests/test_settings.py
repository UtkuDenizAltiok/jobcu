import json

from jobcu.settings import AISettings, Settings, load_settings, save_settings, settings_path


def test_defaults_when_nothing_saved():
    settings = load_settings()
    assert settings.ai.provider is None
    assert settings.limits.scoring_cap is None
    assert settings.limits.web_search_cap is None
    assert settings.search_form.posted_within_hours == 24
    assert settings.ai.compatible_reasoning == "effort"
    assert settings.ai.compatible_medium == "medium"
    assert settings.ai.research_provider is None


def test_legacy_custom_api_keeps_its_unsent_effort_without_changing_medium_default():
    ai = AISettings.model_validate({"provider": "openai_compatible", "model": "old-model"})
    assert ai.compatible_protocol == "chat_completions"
    assert ai.compatible_reasoning == "provider_default"
    assert ai.scoring_effort == ai.reasoning_effort == "medium"
    new = AISettings(provider="openai_compatible", compatible_protocol="responses")
    assert new.compatible_reasoning == "effort"


def test_saved_settings_come_back():
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "some-model"
    settings.search_form.posted_within_hours = 72
    settings.limits.scoring_cap = 100
    settings.limits.web_search_cap = 20
    settings.limits.monthly_token_limit = 100000
    settings.limits.monthly_cost_limit = 25
    settings.limits.maps_monthly_routes = 1000
    save_settings(settings)
    assert load_settings().ai.model == "some-model"
    assert load_settings().search_form.posted_within_hours == 72
    assert load_settings().limits == settings.limits


def test_damaged_settings_file_is_set_aside():
    path = settings_path()
    path.write_text("{broken", encoding="utf-8")
    assert load_settings() == Settings()
    assert path.with_name(path.name + ".damaged").exists()


def test_older_settings_move_from_low_to_medium_thinking_once(temporary_data_dir):
    # The owner's choice (2026-09-24): medium everywhere. "low" was the old default nobody
    # could change on screen.
    old = {"ai": {"provider": "gemini", "model": "m", "scoring_effort": "low",
                  "reasoning_effort": "medium"}}
    temporary_data_dir.mkdir(parents=True, exist_ok=True)
    settings_path().write_text(json.dumps(old), encoding="utf-8")
    settings = load_settings()
    assert settings.ai.scoring_effort == "medium" and settings.version == 2
    # From version 2 on, what is saved stays as saved.
    settings.ai.scoring_effort = "low"
    save_settings(settings)
    assert load_settings().ai.scoring_effort == "low"
    assert Settings().ai.scoring_effort == "medium"
