"""Fictional setup reuse: equal answers, fewer requests, fresh research and job judgements."""

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from test_profile import PROFILE

from jobcu import db, location, preparation
from jobcu.ai.base import AIInvalidOutput, AIUnavailable, ProviderAdapter, RawReply, Usage
from jobcu.ai.client import AIClient
from jobcu.countries import COUNTRIES
from jobcu.keywords import generate_search_words, generate_search_words_reusing
from jobcu.location import Condition, Source, interpret_location, interpret_location_reusing
from jobcu.profile import Profile
from jobcu.settings import Settings


class SetupAI(ProviderAdapter):
    def __init__(self, country="DE", conditions=None):
        super().__init__("fictional-key")
        self.country = country
        self.conditions = conditions or []
        self.calls = []
        self.failure = None
        self.omit_language = None
        self.omit_kind = None

    def complete_json(self, **request):
        self.calls.append(request)
        if self.failure:
            raise self.failure
        if request["schema_name"] == "LocationInterpretation":
            answer = {
                "understood_as": "The requested country and conditions.",
                "limits_countries": True, "countries": [self.country], "places": [],
                "conditions_about_places": self.conditions, "conditions_about_the_job": [],
                "outside_supported_area": [],
            }
        elif request["schema_name"] == "SearchWordsAnswer":
            languages = re.findall(r"\(([a-z]{2})\)", request["prompt"].split("\n", 1)[0])
            answer = {"terms": [
                {"text": text, "language": code, "kind": kind}
                for code in languages if code != self.omit_language
                for kind, text in (("job_title", "Fictional Specialist"),
                                   ("field_or_skill", "Fictional Specialism"))
                if kind != self.omit_kind
            ]}
        else:
            raise AssertionError(request["schema_name"])
        return RawReply(json.dumps(answer), Usage(100, 50))

    def list_models(self):
        return []


def client(adapter):
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "fictional-model"
    return AIClient(settings, adapter=adapter, patient=False)


@pytest.mark.parametrize("country", list(COUNTRIES))
def test_unchanged_reading_reuses_all_supported_countries_without_provider_requests(country):
    ai = SetupAI(country)
    first, reused = interpret_location_reusing(client(ai), f"Jobs in {COUNTRIES[country].name}")
    second, reused_again = interpret_location_reusing(
        client(ai), f"Jobs in {COUNTRIES[country].name}")
    assert first == second and first.countries == [country]
    assert not reused and reused_again and len(ai.calls) == 1
    assert ai.calls[0]["effort"] == "medium"


@pytest.mark.parametrize("profession", ["Electronics", "Nursing", "Teaching"])
def test_identical_setup_keeps_the_answers_and_halves_two_searches_setup_requests(profession):
    person = Profile.model_validate({**PROFILE, "field": profession, "target_roles": [profession]})
    ai = SetupAI()
    fresh = client(ai)
    before = [(interpret_location(fresh, "Germany"),
               generate_search_words(fresh, person, ["en", "de"])) for _ in range(2)]
    assert len(ai.calls) == 4
    ai.calls.clear()
    after = [(interpret_location_reusing(client(ai), "Germany")[0],
              generate_search_words_reusing(client(ai), person, ["en", "de"])[0])
             for _ in range(2)]
    assert after == before and len(ai.calls) == 2


def test_changed_text_profile_languages_model_and_effort_require_new_answers():
    ai = SetupAI()
    c = client(ai)
    person = Profile.model_validate(PROFILE)
    interpret_location_reusing(c, "Germany")
    interpret_location_reusing(c, "Ireland")
    assert len(ai.calls) == 2
    generate_search_words_reusing(c, person, ["en"])
    changed = person.model_copy(update={"target_roles": ["Nursing Team Leader"]})
    generate_search_words_reusing(c, changed, ["en"])
    generate_search_words_reusing(c, changed, ["en", "fr"])
    c.settings.ai.model = "another-fictional-model"
    generate_search_words_reusing(c, changed, ["en", "fr"])
    c.settings.ai.scoring_effort = "high"
    generate_search_words_reusing(c, changed, ["en", "fr"])
    assert len(ai.calls) == 7


@pytest.mark.parametrize("field,value", [
    ("provider", "openai"), ("model", "other-model"), ("reasoning_model", "reading-model"),
    ("reasoning_effort", "high"),
])
def test_changed_location_generation_route_is_not_a_cache_hit(field, value):
    ai = SetupAI()
    c = client(ai)
    interpret_location_reusing(c, "Germany")
    setattr(c.settings.ai, field, value)
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


@pytest.mark.parametrize("field,value", [
    ("base_url", "https://second.example.test/v1"), ("compatible_protocol", "responses"),
    ("compatible_reasoning", "thinking"), ("compatible_medium", "high"),
])
def test_custom_host_and_native_controls_belong_to_the_request_identity(field, value):
    ai = SetupAI()
    c = client(ai)
    c.settings.ai.provider = "openai_compatible"
    c.settings.ai.base_url = "https://first.example.test/v1"
    interpret_location_reusing(c, "Germany")
    setattr(c.settings.ai, field, value)
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


def test_fallback_sorting_route_changes_invalidate_reading_even_with_same_reasoning_model():
    ai = SetupAI()
    c = client(ai)
    c.settings.ai.reasoning_model = "same-reading-model"
    interpret_location_reusing(c, "Germany")
    c.settings.ai.model = "changed-sorting-model"
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


def test_updated_location_prompt_invalidates_interpretation(monkeypatch):
    ai = SetupAI()
    c = client(ai)
    interpret_location_reusing(c, "Germany")
    monkeypatch.setattr(location, "INTERPRET_SYSTEM", location.INTERPRET_SYSTEM + "\nNew rule.")
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


@pytest.mark.parametrize("age", [timedelta(days=31), timedelta(days=-1)])
def test_expired_or_future_dated_reading_is_not_reused(age):
    ai = SetupAI()
    c = client(ai)
    interpret_location_reusing(c, "Germany")
    with db.connect() as conn:
        conn.execute("UPDATE preparation_cache SET created_at = ?",
                     ((datetime.now(UTC) - age).isoformat(),))
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


def test_damaged_payload_is_rebuilt_and_a_hit_does_not_extend_its_age():
    ai = SetupAI()
    c = client(ai)
    interpret_location_reusing(c, "Germany")
    with db.connect() as conn:
        created = conn.execute("SELECT created_at FROM preparation_cache").fetchone()[0]
    interpret_location_reusing(c, "Germany")
    with db.connect() as conn:
        assert conn.execute("SELECT created_at FROM preparation_cache").fetchone()[0] == created
        conn.execute("UPDATE preparation_cache SET answer_json = 'broken'")
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


def test_failed_generation_is_not_saved_and_can_succeed_on_the_next_search():
    ai = SetupAI()
    c = client(ai)
    ai.failure = AIUnavailable("Fictional connection failure")
    with pytest.raises(AIUnavailable):
        interpret_location_reusing(c, "Germany")
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM preparation_cache").fetchone()[0] == 0
    ai.failure = None
    _, reused = interpret_location_reusing(c, "Germany")
    assert not reused and len(ai.calls) == 2


def test_partial_word_groups_stay_retryable_and_completed_groups_survive():
    ai = SetupAI()
    c = client(ai)
    person = Profile.model_validate(PROFILE)
    languages = ["en", "de", "fr", "it", "nl", "pl"]
    ai.omit_language = "pl"
    words, reused = generate_search_words_reusing(c, person, languages)
    assert not reused and {w.language for w in words} == set(languages[:-1])
    ai.omit_language = None
    words, reused = generate_search_words_reusing(c, person, languages)
    assert not reused and {w.language for w in words} == set(languages)
    assert len(ai.calls) == 3  # the first five languages were kept
    _, reused = generate_search_words_reusing(c, person, languages)
    assert reused and len(ai.calls) == 3


@pytest.mark.parametrize("missing_kind", ["job_title", "field_or_skill"])
def test_missing_word_kind_does_not_freeze_an_incomplete_answer(missing_kind):
    ai = SetupAI()
    c = client(ai)
    person = Profile.model_validate(PROFILE)
    ai.omit_kind = missing_kind
    generate_search_words_reusing(c, person, ["en"])
    ai.omit_kind = None
    terms, reused = generate_search_words_reusing(c, person, ["en"])
    assert not reused and len(ai.calls) == 2
    assert {term.kind for term in terms} == {"job_title", "field_or_skill"}


def test_reused_reading_retries_failed_place_facts_and_keeps_cited_research_fresh(monkeypatch):
    ai = SetupAI(conditions=[{
        "text": "near a university town", "understood_as": "Near universities",
        "kind": "near", "max_minutes": 45, "travel_mode": "transit",
        "anchor": {"description": "university towns", "needs_the_web": True,
                   "look_up": "university towns"},
    }])
    calls = []

    def research(*args):
        calls.append(args)
        if len(calls) == 1:
            return Condition(text="university towns", understood_as="Unknown",
                             status="not_checked", kind="could_not_check", note="Try later")
        return Condition(text="university towns", understood_as="The current original fact",
                         status="applied", kind="towns_that_fit",
                         towns=[location.TownRef(name="Berlin", country="DE")],
                         sources=[Source(url="https://university.example.test/current")])

    monkeypatch.setattr(location, "_research_condition", research)
    first, _ = interpret_location_reusing(client(ai), "Germany near a university town")
    second, reused = interpret_location_reusing(client(ai), "Germany near a university town")
    assert first.conditions[0].kind == "could_not_check"
    assert reused and len(ai.calls) == 1 and len(calls) == 2
    assert second.conditions[0].anchor.research_status == "applied"
    assert second.conditions[0].sources[0].url.endswith("/current")


@pytest.mark.parametrize("sorting_succeeds", [True, False])
def test_successful_fallback_reading_is_reused_but_failed_sorting_is_not(
        monkeypatch, sorting_succeeds):
    ai = SetupAI()
    c = client(ai)
    calls = []

    def generate(output, **request):
        calls.append(output.__name__)
        if output is location.LocationInterpretation:
            raise AIInvalidOutput("Fictional older model format")
        if output is location.LocationUnderstanding:
            return output(understood_as="German towns", limits_countries=True, countries=["DE"],
                          places=[], conditions_about_places=["50,000 people"],
                          conditions_about_the_job=[], outside_supported_area=[])
        if not sorting_succeeds:
            raise AIUnavailable("Fictional sorting interruption")
        return output(conditions=[location.SortedCondition(
            text="50,000 people", understood_as="Large towns", kind="town_size", min_people=50000)])

    monkeypatch.setattr(c, "generate", generate)
    first, _ = interpret_location_reusing(c, "Germany, towns with 50,000 people")
    second, reused = interpret_location_reusing(c, "Germany, towns with 50,000 people")
    assert first == second and reused == sorting_succeeds
    assert len(calls) == (3 if sorting_succeeds else 6)


def test_preparation_migration_preserves_existing_history_ratings_and_usage(temporary_data_dir):
    temporary_data_dir.mkdir(parents=True)
    with sqlite3.connect(temporary_data_dir / db.DB_FILENAME) as conn:
        for migration in db.MIGRATIONS[:15]:
            conn.executescript(migration)
        conn.execute("PRAGMA user_version = 15")
        conn.execute("INSERT INTO searches (id,status,form_json) VALUES (1,'finished','{}')")
        conn.execute("INSERT INTO profile_cache (key,profile_json) VALUES ('old','{}')")
        conn.execute("INSERT INTO quality_ads (kind,source,source_job_id,title,url,text,rating) "
                     "VALUES ('scored','fictional','1','Fictional Nurse','','Original','good')")
        conn.execute("INSERT INTO ai_usage (step,provider,model,input_tokens,output_tokens,"
                     "cached_input_tokens,reasoning_tokens,web_searches,unreported_requests) "
                     "VALUES ('location','gemini','fictional',10,5,0,0,0,1)")
    with db.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        assert conn.execute("SELECT COUNT(*) FROM preparation_cache").fetchone()[0] == 0
        assert conn.execute("SELECT rating FROM quality_ads").fetchone()[0] == "good"
        assert conn.execute("SELECT unreported_requests FROM ai_usage").fetchone()[0] == 1
        assert conn.execute("SELECT status FROM searches").fetchone()[0] == "finished"
        assert conn.execute("SELECT key FROM profile_cache").fetchone()[0] == "old"


def test_setup_history_is_bounded_per_kind():
    answer = location.LocationInterpretation(
        understood_as="Germany", limits_countries=True, countries=["DE"], places=[],
        conditions_about_places=[], conditions_about_the_job=[], outside_supported_area=[])
    for i in range(preparation.KEPT_PER_KIND + 3):
        preparation.write("location", str(i), answer)
    preparation.write("other", "keep", answer)
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM preparation_cache WHERE kind='location'"
                            ).fetchone()[0] == preparation.KEPT_PER_KIND
        assert conn.execute("SELECT COUNT(*) FROM preparation_cache WHERE kind='other'"
                            ).fetchone()[0] == 1
