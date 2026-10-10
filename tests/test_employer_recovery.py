"""Offline discovery recovery: a failed lookup is not two weeks of coverage."""

from datetime import timedelta

import pytest
from test_employers import NOW, NURSE, FakeTeamtailor, FinderAI, ai_client, web

from jobcu import db, employers, search
from jobcu.ai.base import (
    AIAuthError,
    AIInvalidOutput,
    AILimitReached,
    AIModelNotFound,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIRefused,
    AIUnavailable,
    AIWebSearchUnavailable,
    ResearchReply,
    Source,
    Usage,
)
from jobcu.countries import COUNTRIES
from jobcu.location import LocationPlan
from jobcu.settings import SearchForm, Settings
from jobcu.sources.careers import found_employers

TEACHER = NURSE.model_copy(update={"summary": "Fictional primary teacher with six years teaching",
                                  "field": "Primary education", "target_roles": ["Teacher"],
                                  "target_fields": ["Primary education"],
                                  "skills": ["Lesson planning"]})
HARDWARE = NURSE.model_copy(update={"summary": "Fictional hardware engineer with six years in R&D",
                                   "field": "Hardware engineering",
                                   "target_roles": ["Hardware engineer"],
                                   "target_fields": ["Electronics"],
                                   "skills": ["Circuit design"]})


class CountryAI(FinderAI):
    def __init__(self, outcomes):
        super().__init__("")
        self.outcomes = outcomes

    def research(self, **request):
        self.asked.append(request["prompt"])
        code = next(code for code in self.outcomes
                    if f"Place: {COUNTRIES[code].name}" in request["prompt"])
        answer = self.outcomes[code]
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, ResearchReply):
            return answer
        return ResearchReply(answer, [Source("https://employer.example.test/careers")],
                             Usage(100, 50, web_searches=1))


def client_for(ai):
    client = ai_client(ai)
    client.parallel_requests = 1
    client.patient = False
    return client


@pytest.mark.parametrize("profile", [NURSE, TEACHER, HARDWARE],
                         ids=["nursing", "teaching", "hardware"])
@pytest.mark.parametrize("error", [AIUnavailable, AIRateLimited, AIInvalidOutput,
                                   AIOutputTruncated, AIRefused])
def test_failed_country_retries_next_search_without_repeating_success(profile, error, monkeypatch):
    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    ai = CountryAI({"IE": "Beacon Hospital | IE | https://beacon.teamtailor.com",
                    "DE": error("Research incomplete")})
    client = client_for(ai)
    first = employers.find(client, web({}), profile, ["IE", "DE"], [], now=NOW)
    assert employers._last_looked(employers.subject_of(profile), ["IE", "DE"]) == {"IE": NOW}
    assert first.failed_countries == ["DE"]
    assert first.new == ["Beacon Hospital"]
    assert client.web_searches_used == 0

    ai.outcomes["DE"] = "NONE"
    again = employers.find(client, web({}), profile, ["IE", "DE"], [],
                           now=NOW + timedelta(days=1))
    assert again.looked and not again.failed_countries
    assert again.read == 1 and found_employers()[0].name == "Beacon Hospital"
    assert len([p for p in ai.asked if "Place: Ireland" in p]) == 1
    assert len([p for p in ai.asked if "Place: Germany" in p]) >= 2


@pytest.mark.parametrize("code", list(COUNTRIES))
@pytest.mark.parametrize("profile", [NURSE, TEACHER], ids=["nursing", "teaching"])
def test_cited_explicit_empty_result_is_reused_but_blank_answer_is_not(code, profile):
    ai = CountryAI({code: ""})
    client = client_for(ai)
    first = employers.find(client, web({}), profile, [code], [], now=NOW)
    assert employers._last_looked(employers.subject_of(profile), [code]) == {}
    assert first.failed_countries == [code]
    ai.outcomes[code] = "NONE"
    complete = employers.find(client, web({}), profile, [code], [], now=NOW)
    assert not complete.failed_countries
    reused = employers.find(client, web({}), profile, [code], [], now=NOW + timedelta(days=1))
    assert not reused.looked and reused.since == NOW and len(ai.asked) == 2


@pytest.mark.parametrize("answer", [
    ResearchReply("NONE", [], Usage(100, 50, web_searches=1)),
    ResearchReply("I could not finish this lookup", [Source("https://example.test")], Usage()),
    ResearchReply("| Employer | Country | URL |", [Source("https://example.test")], Usage()),
])
def test_unfinished_or_uncited_empty_research_does_not_become_a_refresh(answer):
    result = employers.find(client_for(CountryAI({"IE": answer})), web({}), NURSE,
                            ["IE"], [], now=NOW)
    assert result.failed_countries == ["IE"]
    assert employers._last_looked(employers.subject_of(NURSE), ["IE"]) == {}


def test_uncited_names_are_verified_and_kept_without_claiming_discovery_complete(monkeypatch):
    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    answer = ResearchReply("Beacon Hospital | IE | https://beacon.teamtailor.com", [], Usage())
    result = employers.find(client_for(CountryAI({"IE": answer})), web({}), NURSE,
                            ["IE"], [], now=NOW)
    assert result.new == ["Beacon Hospital"] and result.read == 1
    assert result.failed_countries == ["IE"]
    assert employers._last_looked(employers.subject_of(NURSE), ["IE"]) == {}


def test_names_in_another_country_do_not_prove_requested_country_was_completed(monkeypatch):
    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    result = employers.find(client_for(CountryAI({
        "DE": "Beacon Hospital | IE | https://beacon.teamtailor.com"})), web({}), NURSE,
        ["DE"], [], now=NOW)
    assert result.new == ["Beacon Hospital"] and result.failed_countries == ["DE"]
    assert employers._last_looked(employers.subject_of(NURSE), ["DE"]) == {}


def test_completed_parallel_country_survives_a_simultaneous_account_error(monkeypatch):
    import threading

    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    started = threading.Event()
    refused = threading.Event()

    class ParallelAI(CountryAI):
        def research(self, **request):
            if "Place: Ireland" in request["prompt"]:
                started.set()
                assert refused.wait(5)
            else:
                assert "Place: Germany" in request["prompt"]
                assert started.wait(5)
                refused.set()
            return super().research(**request)

    ai = ParallelAI({"IE": "Beacon Hospital | IE | https://beacon.teamtailor.com",
                     "DE": AIQuotaExhausted("Account limit"), "FR": "NONE"})
    client = client_for(ai)
    client.parallel_requests = 2
    with pytest.raises(AIQuotaExhausted):
        employers.find(client, web({}), NURSE, ["IE", "DE", "FR"], [], now=NOW)
    assert found_employers()[0].name == "Beacon Hospital"
    assert employers._last_looked(employers.subject_of(NURSE), ["IE", "DE", "FR"]) == {
        "IE": NOW}
    assert client.web_searches_used == 0 and len(ai.asked) == 2


@pytest.mark.parametrize("error", [AIAuthError, AIModelNotFound, AIQuotaExhausted,
                                   AILimitReached, AIWebSearchUnavailable])
def test_account_or_allowance_error_stops_pending_work_and_keeps_completed_country(error,
                                                                                 monkeypatch):
    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    ai = CountryAI({"IE": "Beacon Hospital | IE | https://beacon.teamtailor.com",
                    "DE": error("Cannot continue"), "FR": "NONE"})
    with pytest.raises(error):
        employers.find(client_for(ai), web({}), NURSE, ["IE", "DE", "FR"], [], now=NOW)
    assert len(ai.asked) == 2
    assert found_employers()[0].name == "Beacon Hospital"
    assert employers._last_looked(employers.subject_of(NURSE), ["IE", "DE", "FR"]) == {
        "IE": NOW}


def test_partial_discovery_has_a_truthful_progress_note(monkeypatch):
    monkeypatch.setattr(employers, "find", lambda *args, **kwargs:
                        employers.Found(looked=True, failed_countries=["DE"]))
    run = search.SearchRun(id=1, form=SearchForm(), started_at=NOW.isoformat())
    settings = Settings()
    plan = LocationPlan(text="Germany or Ireland", understood_as="Germany or Ireland",
                        countries=["DE", "IE"], places=[], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    search._find_employers(run, settings, client_for(CountryAI({})), web({}), NURSE, plan)
    assert run.result["employers"]["failed_countries"] == ["DE"]
    assert "incomplete" in run.step("employers").detail.lower()
    assert any("Germany" in note and "next search" in note for note in run.notes)


def test_migration_preserves_old_history_but_does_not_trust_ambiguous_refresh(temporary_data_dir):
    import sqlite3

    temporary_data_dir.mkdir(parents=True)
    conn = sqlite3.connect(temporary_data_dir / db.DB_FILENAME)
    for migration in db.MIGRATIONS[:13]:
        conn.executescript(migration)
    conn.execute("PRAGMA user_version = 13")
    subject = employers.subject_of(NURSE)
    conn.execute("INSERT INTO employer_searches VALUES (?, 'IE', ?)", (subject, NOW.isoformat()))
    conn.execute("INSERT INTO jobs (id, title) VALUES (1, 'Fictional Nurse')")
    conn.execute("INSERT INTO job_states (job_id, saved, applied) VALUES (1, 1, 1)")
    conn.execute("INSERT INTO quality_ads "
                 "(kind,source,source_job_id,title,url,text,rating,rated_by) "
                 "VALUES ('scored','fake','1','Fictional Nurse','','Full ad','good','owner')")
    conn.execute("INSERT INTO found_employers VALUES "
                 "('teamtailor','beacon','Fictional Hospital',?,0,'{}','2026-10-09')", ('["IE"]',))
    conn.commit()
    conn.close()
    assert employers._last_looked(subject, ["IE"]) == {}
    with db.connect() as conn:
        assert conn.execute("SELECT searched_at FROM employer_searches").fetchone()[0] == (
            NOW.isoformat())
        assert tuple(conn.execute("SELECT saved, applied FROM job_states").fetchone()) == (1, 1)
        assert tuple(conn.execute("SELECT rating, rated_by FROM quality_ads").fetchone()) == (
            "good", "owner")
        assert conn.execute("SELECT name FROM found_employers").fetchone()[0] == (
            "Fictional Hospital")
    ai = CountryAI({"IE": "NONE"})
    employers.find(client_for(ai), web({}), NURSE, ["IE"], [], now=NOW)
    employers.find(client_for(ai), web({}), NURSE, ["IE"], [], now=NOW + timedelta(days=1))
    assert len(ai.asked) == 1
