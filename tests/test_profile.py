import json

import pytest
from conftest import FAKE_CV_LINES, make_pdf
from fastapi.testclient import TestClient

from jobcu import db, documents, search
from jobcu import profile as profile_module
from jobcu.ai.base import ProviderAdapter, RawReply, Usage
from jobcu.ai.client import AIClient
from jobcu.app import create_app
from jobcu.profile import Profile, progress_detail, read_profile, read_profile_reusing
from jobcu.settings import Settings

PROFILE = {
    "summary": "An embedded hardware engineer looking for hardware design roles.",
    "current_or_last_role": "Embedded Engineer",
    "field": "Electronics",
    "skills": ["PCB layout"],
    "technical_areas": ["Embedded systems"],
    "years_full_time_experience": 5,
    "years_student_or_part_time_experience": 1,
    "experience_note": "Five years in one company.",
    "seniority": "mid",
    "education": [
        {"degree": "BSc Electrical Engineering", "institution": None, "finished": "2019"}
    ],
    "languages": [
        {
            "language": "English",
            "level_as_written": "fluent",
            "cefr": "C1",
            "cefr_is_estimate": True,
        }
    ],
    "target_roles": ["Hardware Engineer"],
    "target_fields": ["Electronics"],
    "preferences": ["full-time"],
    "work_mode_preference": "not_stated",
    "dealbreakers": [],
    "work_authorisation": None,
    "ignored_as_application_specific": ["Company name: Example Corp"],
}


class RecordingAdapter(ProviderAdapter):
    def __init__(self):
        super().__init__("fake-key")
        self.calls = []

    def complete_json(self, **request):
        self.calls.append(request)
        return RawReply(json.dumps(PROFILE), Usage(100, 50))

    def list_models(self):
        return []


@pytest.fixture
def settings():
    s = Settings()
    s.ai.provider = "openai"
    s.ai.model = "everyday-model"
    s.ai.reasoning_model = "careful-model"
    return s


def test_profile_uses_the_careful_model_and_the_rules(settings):
    adapter = RecordingAdapter()
    profile = read_profile(AIClient(settings, adapter=adapter), "CV TEXT", "LETTER TEXT")
    assert isinstance(profile, Profile)
    call = adapter.calls[0]
    assert call["model"] == "careful-model"
    system = call["system"]
    assert "Do not rate, grade, critique" in system
    assert "Never guess nationality" in system
    assert "one particular job application" in system
    assert "Where the person wants to work is chosen separately" in system
    assert "full-time work" in system
    assert "<<<CV\nCV TEXT\nCV>>>" in call["prompt"]
    assert "<<<COVER_LETTER\nLETTER TEXT\nCOVER_LETTER>>>" in call["prompt"]


@pytest.fixture
def client():
    return TestClient(create_app(), base_url="http://127.0.0.1:8765")


HEADERS = {"X-Jobcu": "1"}


def test_upload_list_and_remove_documents(client):
    response = client.post(
        "/api/documents/cv",
        files={"file": ("My CV.pdf", make_pdf(FAKE_CV_LINES), "application/pdf")},
        headers=HEADERS,
    )
    assert response.status_code == 200
    listed = client.get("/api/documents").json()
    assert listed["documents"]["cv"]["original_name"] == "My CV.pdf"
    assert listed["documents"]["cover_letter"] is None
    client.delete("/api/documents/cv", headers=HEADERS)
    assert client.get("/api/documents").json()["documents"]["cv"] is None


def test_bad_upload_explains_the_problem(client):
    response = client.post(
        "/api/documents/cv", files={"file": ("cv.png", b"x" * 100, "image/png")}, headers=HEADERS
    )
    assert response.status_code == 400
    assert "PDF or DOCX" in response.json()["detail"]


def test_upload_needs_the_jobcu_header(client):
    files = {"file": ("cv.pdf", b"%PDF", "application/pdf")}
    response = client.post("/api/documents/cv", files=files)
    assert response.status_code == 403


def test_preview_without_documents_explains_what_to_do(client):
    data = client.post("/api/profile/preview", headers=HEADERS).json()
    assert data == {"profile": None, "error": "Please upload your CV first."}


def test_preview_returns_the_profile(client, monkeypatch):
    documents.save_upload("cv", "cv.pdf", make_pdf(FAKE_CV_LINES))
    documents.save_upload("cover_letter", "letter.txt", b"I enjoy hardware design work. " * 5)
    seen = {}

    def fake_read_profile(ai_client, cv_text, letter_text, about_you):
        seen["texts"] = (cv_text, letter_text, about_you)
        return Profile.model_validate(PROFILE), False

    monkeypatch.setattr("jobcu.documents_api.read_profile_reusing", fake_read_profile)
    data = client.post("/api/profile/preview", headers=HEADERS).json()
    assert data["error"] is None
    assert data["profile"]["seniority"] == "mid"
    assert "embedded systems" in seen["texts"][0] and seen["texts"][2] == ""
    # The note is used as typed, before any search saved it.
    client.post("/api/profile/preview", headers=HEADERS, json={"about_you": "Irish citizen"})
    assert seen["texts"][2] == "Irish citizen"


def test_unchanged_documents_are_not_read_again(settings):
    """The owner's rule: only understanding the person may be reused, never the job search."""
    adapter = RecordingAdapter()
    client = AIClient(settings, adapter=adapter)
    first, reused = read_profile_reusing(client, "CV TEXT", "LETTER TEXT")
    assert not reused and len(adapter.calls) == 1
    again, reused = read_profile_reusing(client, "CV TEXT", "LETTER TEXT")
    assert reused and len(adapter.calls) == 1 and again == first
    # A changed document, or a different model, means reading them again.
    read_profile_reusing(client, "CV TEXT (updated)", "LETTER TEXT")
    assert len(adapter.calls) == 2
    settings.ai.reasoning_model = "another-model"
    read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT", "LETTER TEXT")
    assert len(adapter.calls) == 3


@pytest.mark.parametrize("history,target", [
    ("Completed master's thesis in motor control", "Hardware Design Engineer"),
    ("Completed nursing placement", "Registered Nurse"),
])
def test_profile_progress_distinguishes_history_from_sought_work(history, target):
    profile = Profile.model_validate({**PROFILE, "current_or_last_role": history,
                                      "target_roles": [target]})
    for reused in (False, True):
        detail = progress_detail(profile, reused)
        assert f"Looking for: {target}" in detail and history not in detail
        assert ("Using saved document understanding" in detail) == reused


def test_reset_forgets_only_profile_cache_and_next_read_is_fresh(client, settings, monkeypatch):
    monkeypatch.setattr(search, "manager", search.SearchManager())
    adapter = RecordingAdapter()
    ai = AIClient(settings, adapter=adapter)
    first, _ = read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    documents.save_upload("cv", "cv.pdf", make_pdf(FAKE_CV_LINES))
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (1, 'finished', '{}')")
        conn.execute("INSERT INTO search_results VALUES (1, ?)", ('{"kept": true}',))
    assert client.delete("/api/profile/cache").status_code == 403
    assert client.delete("/api/profile/cache", headers=HEADERS).json() == {"reset": True}
    assert documents.read_text("cv")
    with db.connect() as conn:
        assert conn.execute("SELECT result_json FROM search_results").fetchone()[0] == (
            '{"kept": true}')
    assert len(adapter.calls) == 1  # reset itself never makes a paid request
    again, reused = read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    assert not reused and again == first and len(adapter.calls) == 2
    assert read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")[1]


def test_reset_cannot_race_a_running_search(client, settings, monkeypatch):
    manager = search.SearchManager()
    manager._current = search.SearchRun(1, settings.search_form, "2026-01-01T00:00:00Z")
    monkeypatch.setattr(search, "manager", manager)
    ai = AIClient(settings, adapter=RecordingAdapter())
    read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    assert client.delete("/api/profile/cache", headers=HEADERS).status_code == 409
    assert read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")[1]


def test_the_persons_note_is_read_with_the_documents_and_changes_the_profile(settings):
    adapter = RecordingAdapter()
    client = AIClient(settings, adapter=adapter)
    read_profile_reusing(client, "CV TEXT", "LETTER TEXT")
    assert "NOTE" not in adapter.calls[0]["prompt"]
    read_profile_reusing(client, "CV TEXT", "LETTER TEXT", "  Irish citizen  ")
    assert len(adapter.calls) == 2
    assert "<<<NOTE\nIrish citizen\nNOTE>>>" in adapter.calls[1]["prompt"]
    assert "the note explicitly state" in adapter.calls[1]["system"]
    _, reused = read_profile_reusing(client, "CV TEXT", "LETTER TEXT", "Irish citizen")
    assert not reused and len(adapter.calls) == 3
    assert read_profile_reusing(client, "CV TEXT", "LETTER TEXT", "Irish citizen")[1]


@pytest.mark.parametrize("changed", ["Irish Citizen", "Irish citizen ", "\nIrish citizen"])
def test_even_one_letter_or_whitespace_edit_requires_new_profile(settings, changed):
    adapter = RecordingAdapter()
    ai = AIClient(settings, adapter=adapter)
    read_profile_reusing(ai, "CV TEXT", "LETTER TEXT", "Irish citizen")
    _, reused = read_profile_reusing(ai, "CV TEXT", "LETTER TEXT", changed)
    assert not reused and len(adapter.calls) == 2
    assert read_profile_reusing(ai, "CV TEXT", "LETTER TEXT", changed)[1]


@pytest.mark.parametrize("field,value", [
    ("reasoning_effort", "high"), ("base_url", "https://second.example.test/v1"),
    ("compatible_protocol", "responses"), ("compatible_reasoning", "thinking"),
    ("compatible_medium", "high"),
])
def test_profile_reuse_respects_actual_host_and_reasoning_controls(settings, field, value):
    settings.ai.provider = "openai_compatible"
    settings.ai.base_url = "https://first.example.test/v1"
    adapter = RecordingAdapter()
    ai = AIClient(settings, adapter=adapter)
    read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    setattr(settings.ai, field, value)
    _, reused = read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    assert not reused and len(adapter.calls) == 2


def test_the_note_is_kept_with_the_search_form(client, monkeypatch):
    monkeypatch.setattr("jobcu.search.manager.start", lambda form: _Started(form))
    form = {"location_text": "", "about_you": "Irish citizen", "posted_within_hours": 24,
            "job_types": ["full_time_permanent"], "exclude_remote": False}
    assert client.post("/api/search", headers=HEADERS, json=form).status_code == 200
    assert client.get("/api/search/form").json()["about_you"] == "Irish citizen"


class _Started:
    def __init__(self, form):
        self.form = form

    def snapshot(self):
        return {"form": self.form.model_dump()}


class SequenceAdapter(ProviderAdapter):
    """Answers each request with the next profile of a list (the last one again after that)."""

    def __init__(self, answers):
        super().__init__("fake-key")
        self.answers, self.calls = list(answers), []

    def complete_json(self, **request):
        self.calls.append(request)
        answer = self.answers[min(len(self.calls), len(self.answers)) - 1]
        return RawReply(json.dumps(answer), Usage(100, 50))

    def list_models(self):
        return []


# A well-formed answer that read too little: no languages, no wanted roles, two degrees and the
# model's own notes in one entry (what a reading of real documents returned on 27 Nov 2026).
INCOMPLETE = {**PROFILE, "languages": [], "target_roles": [], "education": [{
    "degree": "BSc Electrical Engineering (thesis on motor drives, grade 1.7, projects: a 48 W "
              "flyback converter and a BLDC drive, term projects ... wait: keep the degree "
              "clean!) -> separate entries!",
    "institution": "Example University / Second Example University -> separate entries!",
    "finished": "2019"}]}
WORK_RIGHTS = [{"country": "IE", "now": "yes", "later": "yes", "basis": "Irish citizenship"}]


def test_an_answer_without_languages_or_wanted_roles_is_asked_again_and_the_complete_one_kept(
        settings):
    adapter = SequenceAdapter([INCOMPLETE, PROFILE])
    notes = []
    profile, reused = read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT",
                                           "LETTER TEXT", notify=notes.append)
    assert not reused and len(adapter.calls) == 2
    assert profile.languages and profile.target_roles and notes == []
    again = adapter.calls[1]["prompt"]
    assert "IMPORTANT: an earlier answer for these documents was incomplete" in again
    assert "languages is empty" in again and "target_roles is empty" in again
    assert "education entry is far too long" in again
    # The complete reading is the one kept.
    assert read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT",
                                "LETTER TEXT")[1]
    assert len(adapter.calls) == 2


def test_an_incomplete_reading_saved_by_an_earlier_jobcu_is_never_reused(settings):
    ai = AIClient(settings, adapter=SequenceAdapter([PROFILE]))
    key = profile_module._cache_key(ai, "CV TEXT", "LETTER TEXT", "")
    with db.connect() as conn:
        conn.execute("INSERT INTO profile_cache (key, profile_json) VALUES (?, ?)",
                     (key, json.dumps(INCOMPLETE)))
    profile, reused = read_profile_reusing(ai, "CV TEXT", "LETTER TEXT")
    assert not reused and profile.languages == Profile.model_validate(PROFILE).languages
    assert len(ai._adapter.calls) == 1


def test_the_last_complete_reading_of_the_same_documents_stands_in_for_an_incomplete_one(
        settings):
    first = AIClient(settings, adapter=SequenceAdapter([PROFILE]))
    complete, _ = read_profile_reusing(first, "CV TEXT", "LETTER TEXT", "Irish citizen")
    settings.ai.reasoning_model = "newer-model"
    adapter = SequenceAdapter([INCOMPLETE])
    notes = []
    profile, reused = read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT",
                                           "LETTER TEXT", "Irish citizen", notify=notes.append)
    assert len(adapter.calls) == profile_module.READING_ATTEMPTS
    assert profile == complete and not reused
    assert notes == [profile_module.EARLIER_READING]
    # Kept for the newer model too: the next search doesn't pay for three readings again.
    assert read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT", "LETTER TEXT",
                                "Irish citizen") == (complete, True)
    assert len(adapter.calls) == profile_module.READING_ATTEMPTS


def test_a_reading_of_other_documents_never_stands_in(settings):
    read_profile_reusing(AIClient(settings, adapter=SequenceAdapter([PROFILE])), "CV TEXT",
                         "LETTER TEXT")
    settings.ai.reasoning_model = "newer-model"
    notes = []
    profile, _ = read_profile_reusing(AIClient(settings, adapter=SequenceAdapter([INCOMPLETE])),
                                      "ANOTHER CV", "LETTER TEXT", notify=notes.append)
    assert profile.languages == [] and len(notes) == 1
    assert "the languages you speak, the jobs you want and your degrees" in notes[0]


def test_a_reading_that_loses_facts_another_reading_found_in_the_same_documents_is_asked_again(
        settings):
    with_rights = {**PROFILE, "work_authorisation": "Irish citizen", "work_rights": WORK_RIGHTS}
    read_profile_reusing(AIClient(settings, adapter=SequenceAdapter([with_rights])), "CV TEXT",
                         "LETTER TEXT", "Irish citizen")
    settings.ai.reasoning_model = "newer-model"
    lost = {**with_rights, "work_authorisation": None, "work_rights": [],
            "languages": with_rights["languages"] * 0 + [
                {"language": "Irish", "level_as_written": "native", "cefr": "native",
                 "cefr_is_estimate": False}]}
    adapter = SequenceAdapter([lost, with_rights])
    profile, _ = read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT",
                                      "LETTER TEXT", "Irish citizen")
    assert len(adapter.calls) == 2 and profile.work_rights[0].country == "IE"
    assert "work_rights names less than another reading" in adapter.calls[1]["prompt"]


def test_without_any_complete_reading_the_person_is_told_and_it_is_read_again_next_time(
        settings):
    adapter = SequenceAdapter([INCOMPLETE])
    notes = []
    read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT", "LETTER TEXT",
                         notify=notes.append)
    assert len(notes) == 1 and "even when asked again" in notes[0]
    assert len(adapter.calls) == profile_module.READING_ATTEMPTS
    _, reused = read_profile_reusing(AIClient(settings, adapter=adapter), "CV TEXT", "LETTER TEXT")
    assert not reused and len(adapter.calls) == 2 * profile_module.READING_ATTEMPTS


@pytest.mark.parametrize("person", [
    {"field": "Nursing", "skills": ["Wound care"], "target_roles": ["Staff Nurse"],
     "education": [{"degree": "BSc Nursing", "institution": "Example College",
                    "finished": "2021"}]},
    {"field": "Hospitality", "skills": ["Pastry"], "target_roles": ["Sous Chef"],
     "education": [{"degree": "Chef apprenticeship (EFZ)", "institution": None,
                    "finished": "2018"}]},
])
def test_the_checks_hold_for_any_profession(person):
    assert profile_module.reading_problems(Profile.model_validate({**PROFILE, **person})) == []
    assert [name for name, _ in profile_module.reading_problems(
        Profile.model_validate({**PROFILE, **person, "languages": []}))] == ["languages"]
