import json
import re
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from conftest import FAKE_CV_LINES, make_pdf
from fastapi.testclient import TestClient

from jobcu import applications, db, documents, jobstore, search
from jobcu.ai.base import AIAuthError, ProviderAdapter, RawReply, Usage
from jobcu.app import create_app
from jobcu.settings import SearchForm, Settings, load_settings, save_settings
from jobcu.sources.base import FoundJob, JobSource

HEADERS = {"X-Jobcu": "1"}
PROFILE = {
    "summary": "Hardware engineer.", "current_or_last_role": "Embedded Engineer",
    "field": "Electronics", "skills": ["PCB layout"], "technical_areas": ["Embedded systems"],
    "years_full_time_experience": 5, "years_student_or_part_time_experience": 0,
    "experience_note": "Five years.", "seniority": "mid", "education": [], "languages": [],
    "target_roles": ["Hardware Engineer"], "target_fields": ["Electronics"], "preferences": [],
    "work_mode_preference": "not_stated", "dealbreakers": [], "work_authorisation": None,
    "ignored_as_application_specific": [],
}
LOCATION = {
    "understood_as": "Jobs in Germany.", "limits_countries": True, "countries": ["DE"],
    "places": [], "conditions_about_places": [], "conditions_about_the_job": [],
    "outside_supported_area": [],
}
WORDS = {"terms": [{"text": "Hardware Engineer", "language": "en", "kind": "job_title"}]}


class FakeAI(ProviderAdapter):
    """Answers each kind of request with made-up data."""

    def __init__(self):
        super().__init__("fake")

    def complete_json(self, **request):
        name, prompt = request["schema_name"], request["prompt"]
        if name == "QuickPassAnswer":
            ids = re.findall(r"^(J\d+) \| Nurse", prompt, re.MULTILINE)
            answer = {"clearly_unrelated": ids, "places": []}
        elif name == "ScoringAnswer":
            answer = {"scores": [
                {"job_id": job_id, "ad_language": "English", "languages_asked": [],
                 "years_required": None, "doctorate": "not_required",
                 "citizenship_or_clearance": "no_such_requirement",
                 "citizenship_or_clearance_words": "", "role_and_skills": 35, "seniority": 18,
                 "hard_requirements": 15, "location_and_preferences": 9,
                 "reasons": ["Strong match"], "job_type": "full_time_permanent",
                 "work_mode": "on_site", "fully_remote": False}
                for job_id in re.findall(r"^JOB (J\d+)", prompt, re.MULTILINE)
            ]}
        else:
            answer = {"Profile": PROFILE, "LocationInterpretation": LOCATION,
                      "SearchWordsAnswer": WORDS}[name]
        return RawReply(json.dumps(answer), Usage(10, 5))

    def list_models(self):
        return []


class FakeSource(JobSource):
    id = "fake"
    name = "Fake Jobs"
    kind = "job_board"
    titles = ["Hardware Engineer", "Electronics Engineer", "Nurse"]

    def search(self, query, ctx):
        for i, title in enumerate(self.titles):
            ctx.report.requests += 1
            yield FoundJob(source="fake", source_job_id=str(i), url=f"https://jobs.test/{i}",
                           title=title, company=f"Company {i}", location_text="Berlin",
                           country="DE", posted_at=datetime.now(UTC), date_precision="exact",
                           description="Short")

    def load_details(self, job, ctx):
        job.description, job.description_is_complete = "Full ad text", True
        return job


@pytest.fixture
def ready(monkeypatch):
    """Documents uploaded, AI chosen, the fake AI and the fake job source plugged in."""
    documents.save_upload("cv", "cv.pdf", make_pdf(FAKE_CV_LINES))
    documents.save_upload("cover_letter", "letter.txt", b"I enjoy hardware design work. " * 5)
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "model-a"
    save_settings(settings)
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: FakeAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [FakeSource()])


def wait_until_done(manager, answer=None, timeout=15):
    deadline = time.monotonic() + timeout
    while manager.current.status == "running" and time.monotonic() < deadline:
        if answer is not None and manager.current.question:
            manager.current.answer(answer)
        time.sleep(0.02)
    return manager.current.snapshot()


def track_search_worker(manager, monkeypatch):
    """Let controlled-save tests clean up only after the background worker returns."""
    worker_done = threading.Event()
    original_run = manager._run

    def tracked_run(*args):
        try:
            original_run(*args)
        finally:
            worker_done.set()

    monkeypatch.setattr(manager, "_run", tracked_run)
    return worker_done


@pytest.mark.parametrize("outcome", ["finished", "stopped", "failed"])
@pytest.mark.parametrize("with_jobs", [True, False])
def test_completion_waits_for_saved_results_and_status(monkeypatch, outcome, with_jobs):
    def runner(run):
        run.update("documents", "running")
        if with_jobs:
            run.set_result("jobs", {"cards": [], "hidden": [], "date_unknown": []})
        if outcome == "stopped":
            raise search.SearchStopped
        if outcome == "failed":
            raise AIAuthError("The AI provider didn't accept the key.")

    manager = search.SearchManager(runner=runner)
    worker_done = track_search_worker(manager, monkeypatch)
    saving, release = threading.Event(), threading.Event()
    original_finish = jobstore.finish_search

    def delayed_finish(*args):
        saving.set()
        assert release.wait(10), "Test did not release the final save"
        original_finish(*args)

    monkeypatch.setattr(jobstore, "finish_search", delayed_finish)
    run = manager.start(SearchForm())
    try:
        assert saving.wait(10)
        assert run.snapshot()["status"] == "running"
        assert jobstore.latest_results() is None
        with db.connect() as conn:
            row = conn.execute("SELECT status, finished_at FROM searches WHERE id = ?",
                               (run.id,)).fetchone()
        assert row["status"] == "running" and row["finished_at"] is None
        with pytest.raises(RuntimeError):
            manager.start(SearchForm())
        with pytest.raises(RuntimeError):
            manager.reapply(run.id, [])
    finally:
        release.set()
        assert worker_done.wait(10)

    snapshot = run.snapshot()
    assert snapshot["status"] == outcome
    assert snapshot["steps"][0]["status"] == ("failed" if outcome == "failed" else "skipped")
    with db.connect() as conn:
        row = conn.execute("SELECT status, finished_at FROM searches WHERE id = ?",
                           (run.id,)).fetchone()
    assert row["status"] == outcome and row["finished_at"] is not None
    saved = jobstore.latest_results()
    if with_jobs:
        assert json.loads(saved[1]) == snapshot
    else:
        assert saved is None


@pytest.mark.parametrize("runner_fails", [False, True])
def test_save_failure_keeps_results_visible_and_explains_the_problem(monkeypatch, runner_fails):
    jobs = {"cards": [{"job_id": 9999, "title": "Library Assistant"}],
            "hidden": [], "date_unknown": []}

    def runner(run):
        run.set_result("jobs", jobs)
        if runner_fails:
            raise AIAuthError("The AI provider didn't accept the key.")

    def cannot_save(*args):
        raise OSError("Simulated storage failure")

    monkeypatch.setattr(jobstore, "finish_search", cannot_save)
    manager = search.SearchManager(runner=runner)
    worker_done = track_search_worker(manager, monkeypatch)
    monkeypatch.setattr(search, "manager", manager)
    manager.start(SearchForm())
    assert worker_done.wait(10)
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    current = client.get("/api/search/current").json()["search"]
    assert current["status"] == "failed"
    assert "couldn't save this search" in current["error"]
    assert "Keep Jobcu open" in current["error"]
    assert current["result"]["jobs"] == jobs
    if runner_fails:
        assert current["error"].startswith("The AI provider didn't accept the key.")
    assert jobstore.latest_results() is None


def test_full_search_finds_filters_scores_and_remembers(ready):
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    steps = {step["id"]: step for step in result["steps"]}
    assert all(step["status"] == "done" for name, step in steps.items() if name != "employers")
    # This AI can't search the web, so no employers are looked for, and the search goes on.
    assert steps["employers"]["status"] == "skipped"
    assert "can't look things up" in steps["employers"]["detail"]
    jobs = result["result"]["jobs"]
    titles = [card["title"] for card in jobs["cards"]]
    assert sorted(titles) == ["Electronics Engineer", "Hardware Engineer"]
    assert jobs["counts"]["unrelated"] == 1 and jobs["counts"]["unrelated_titles"] == ["Nurse"]
    card = jobs["cards"][0]
    assert card["score"] == 92 and card["is_new"] and not card["summary_only"]
    assert card["location_checks"][0]["status"] == "verified"
    assert jobs["sources"][0]["unique"] == 2 and jobs["new_count"] == 2

    # The next search recognises the same jobs: no "New" badge.
    manager.start(SearchForm(location_text="Germany"))
    again = wait_until_done(manager)["result"]["jobs"]
    assert again["new_count"] == 0


def test_web_research_refusal_keeps_search_results_and_skips_later_online_steps(ready, monkeypatch):
    from jobcu.ai.base import AIWebSearchUnavailable

    class NoWeb(FakeAI):
        can_search_the_web = True
        research_calls = 0

        def research(self, **request):
            self.research_calls += 1
            raise AIWebSearchUnavailable("Web look-ups unavailable for this project.")

    adapter = NoWeb()
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: adapter)
    # Full ads unavailable: the online step would ordinarily look up both matching summaries.
    monkeypatch.setattr(FakeSource, "load_details", lambda self, job, ctx: job)
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    steps = {step["id"]: step for step in result["steps"]}
    assert steps["employers"]["status"] == steps["places"]["status"] == "skipped"
    assert adapter.research_calls == 1
    assert result["notes"].count("Web look-ups unavailable for this project.") == 1
    cards = result["result"]["jobs"]["cards"]
    assert len(cards) == 2 and all(card["summary_only"] for card in cards)
    from jobcu import quality

    samples = [ad for ad in quality.all_ads() if ad.kind == "scored"]
    assert len(samples) == 2 and all(not ad.description_is_complete for ad in samples)
    assert all(ad.location_plan["countries"] == ["DE"] for ad in samples)


def test_step_timers_survive_progress_updates_and_waiting_and_finish(monkeypatch):
    ticks = [10.0]
    monkeypatch.setattr(search.time, "monotonic", lambda: ticks[0])
    run = search.SearchRun(id=1, form=SearchForm(), started_at="2026-10-06T12:00:00+00:00")
    run.update("scoring", "running")
    ticks[0] = 12
    run.update("scoring", "running", "More progress")
    assert run.snapshot()["steps"][8]["elapsed_seconds"] == 2

    def wait(timeout):
        ticks[0] = 17
        run.answer(True)
        return True

    monkeypatch.setattr(run._answered, "wait", wait)
    assert run.ask({"kind": "fake"})
    ticks[0] = 20
    run.update("scoring", "done")
    ticks[0] = 30
    snapshot = run.snapshot()
    assert snapshot["steps"][8]["elapsed_seconds"] == 10
    assert snapshot["waiting_seconds"] == 5
    assert snapshot["steps"][0]["elapsed_seconds"] == 0


def test_quality_sample_keeps_the_final_online_score(ready, monkeypatch):
    from jobcu import jobplace, quality
    from jobcu.scoring import LanguageAsked

    monkeypatch.setattr(FakeSource, "load_details", lambda self, job, ctx: job)

    def found(client, groups, indexes, profile, on_progress):
        return jobplace.LookedUp(asked=set(indexes), requirements={i: jobplace.Requirements(
            [LanguageAsked(language="German", level="C1", must_have=True)], 12) for i in indexes})

    monkeypatch.setattr(jobplace, "find_online", found)
    monkeypatch.setattr(FakeAI, "can_search_the_web", True)
    monkeypatch.setattr(search, "_find_employers", lambda run, *args:
                        run.update("employers", "skipped"))
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    cards = wait_until_done(manager)["result"]["jobs"]["cards"]
    assert all(card["score"] == 75 for card in cards)
    samples = [ad for ad in quality.all_ads() if ad.kind == "scored"]
    assert [ad.score for ad in samples] == [card["score"] for card in cards]


def test_one_job_the_memory_knows_twice_gets_one_card(ready, monkeypatch):
    # An agency's two summaries with the same title and town stay apart in the duplicate rules
    # but are one job in Jobcu's memory (search 10): one card, not two sharing Save.
    class AgencyTwice(FakeSource):
        def search(self, query, ctx):
            for i, text in enumerate(["Short", "Another short text"]):
                yield FoundJob(source="fake", source_job_id=f"a{i}", url=f"https://jobs.test/a{i}",
                               title="Hardware Engineer", company="Augusta Personaldienst",
                               location_text="Berlin", country="DE",
                               posted_at=datetime.now(UTC), date_precision="exact",
                               description=text)

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [AgencyTwice()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    jobs = wait_until_done(manager)["result"]["jobs"]
    assert [card["title"] for card in jobs["cards"]] == ["Hardware Engineer"]


def test_not_interested_jobs_are_hidden_from_later_searches(ready):
    manager = search.SearchManager()
    manager.start(SearchForm())
    first = wait_until_done(manager)["result"]["jobs"]["cards"]
    jobstore.set_state(first[0]["job_id"], dismissed=True)
    manager.start(SearchForm())
    jobs = wait_until_done(manager)["result"]["jobs"]
    assert len(jobs["cards"]) == 1
    assert [c["title"] for c in jobs["hidden"]] == [first[0]["title"]]


@pytest.mark.parametrize(("title", "field", "skill"), [
    ("Power Electronics Engineer", "Electronics", "Power converter design"),
    ("Registered Nurse", "Nursing", "Clinical patient care"),
])
def test_a_second_employer_opening_reaches_matching_with_fictional_profiles(
        ready, monkeypatch, title, field, skill):
    profile = {**PROFILE, "summary": f"Experienced {title}.", "field": field,
               "skills": [skill], "technical_areas": [field], "target_fields": [field],
               "target_roles": [title], "current_or_last_role": title}
    documents.save_upload("cv", "fictional-cv.pdf", make_pdf([
        "Alex Example", f"{title} with five years of experience. Skills: {skill}. " * 4]))
    documents.save_upload("cover_letter", "fictional-cover-letter.txt",
                          f"I am seeking work as a {title}. I enjoy {skill}. ".encode() * 4)

    class MatchingAI(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps(profile), Usage(10, 5))
            return super().complete_json(**request)

    vacancies = ["example/old"]

    class EmployerSource(FakeSource):
        kind = "employer"

        def search(self, query, ctx):
            for vacancy in vacancies:
                yield FoundJob("fake", vacancy, f"https://careers.example.test/{vacancy}", title,
                               company="Example Employer", location_text="Berlin", country="DE",
                               posted_at=datetime.now(UTC), date_precision="exact")

        def load_details(self, job, ctx):
            return replace(job, description=f"Work as a {title} using {skill}. " * 20,
                           description_is_complete=True)

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: MatchingAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [EmployerSource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    first = wait_until_done(manager)
    assert first["status"] == "finished", first["error"]
    (old,) = first["result"]["jobs"]["cards"]
    jobstore.set_state(old["job_id"], saved=True, dismissed=True)
    vacancies.append("example/new")
    manager.start(SearchForm(location_text="Germany"))
    second = wait_until_done(manager)
    assert second["status"] == "finished", second["error"]
    jobs = second["result"]["jobs"]
    (fresh,) = jobs["cards"]
    assert fresh["job_id"] != old["job_id"] and fresh["is_new"]
    assert fresh["title"] == title and fresh["score"] == old["score"]
    assert not fresh["summary_only"]
    assert not any(fresh["state"].values())
    assert [c["job_id"] for c in jobs["hidden"]] == [old["job_id"]]
    assert jobstore.states([old["job_id"]])[old["job_id"]].saved


def test_search_excludes_known_cvlibrary_only_application_routes(ready, monkeypatch):
    class UnusableSource(FakeSource):
        def search(self, query, ctx):
            for job in super().search(query, ctx):
                if job.source_job_id == "0":
                    job.url = "https://www.cv-library.co.uk/job/fictional-1"
                yield job

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [UnusableSource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    jobs = result["result"]["jobs"]
    assert [c["title"] for c in jobs["cards"]] == ["Electronics Engineer"]
    assert {"reason": "CV-Library application route, with no other saved link", "count": 1} in (
        jobs["counts"]["left_out"])


def test_search_remembers_reported_route_and_undo_allows_it_again(ready):
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    first = wait_until_done(manager)["result"]["jobs"]["cards"]
    marked = first[0]
    applications.report_link(marked["job_id"], marked["main_link"]["url"])
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    jobs = result["result"]["jobs"]
    assert [c["title"] for c in jobs["cards"]] == [first[1]["title"]]
    assert jobs["cards"][0]["score"] == first[1]["score"]
    assert {"reason": applications.REPORTED_EXCLUSION_REASON, "count": 1} in (
        jobs["counts"]["left_out"])
    applications.undo_report(applications.reports()[0]["id"])
    manager.start(SearchForm(location_text="Germany"))
    restored = wait_until_done(manager)["result"]["jobs"]["cards"]
    assert [c["title"] for c in restored] == [c["title"] for c in first]


@pytest.mark.parametrize(("answer", "scored"), [(False, 1), (True, 2)])
def test_scoring_limit_asks_before_doing_more(ready, answer, scored):
    settings = load_settings()
    settings.limits.scoring_cap = 1
    save_settings(settings)
    manager = search.SearchManager()
    manager.start(SearchForm())
    result = wait_until_done(manager, answer=answer)
    cards = result["result"]["jobs"]["cards"]
    assert sum(1 for c in cards if c["score"] is not None) == scored
    assert len(cards) == 2  # unscored jobs are still shown, never silently dropped


def test_always_scoring_them_all_removes_the_limit_for_every_later_search(ready):
    settings = load_settings()
    settings.limits.scoring_cap = 1
    save_settings(settings)
    manager = search.SearchManager()
    manager.start(SearchForm())
    deadline = time.monotonic() + 15
    while manager.current.status == "running" and time.monotonic() < deadline:
        if manager.current.question:
            manager.current.answer(True, always=True)
        time.sleep(0.02)
    cards = manager.current.snapshot()["result"]["jobs"]["cards"]
    assert all(c["score"] is not None for c in cards) and len(cards) == 2
    assert load_settings().limits.scoring_cap is None
    manager.start(SearchForm())  # a later search scores everything without asking
    result = wait_until_done(manager, answer=False)
    assert all(c["score"] is not None for c in result["result"]["jobs"]["cards"])


def test_missing_documents_stop_the_search_with_a_plain_message():
    manager = search.SearchManager()
    manager.start(SearchForm())
    result = wait_until_done(manager)
    assert result["status"] == "failed"
    assert result["error"] == "Please upload your CV first."
    assert result["steps"][0]["status"] == "failed"


def test_ai_problems_are_shown_plainly():
    def runner(run):
        run.update("documents", "running")
        raise AIAuthError("The AI provider didn't accept the key.")

    manager = search.SearchManager(runner=runner)
    manager.start(SearchForm())
    result = wait_until_done(manager)
    assert result["status"] == "failed" and "didn't accept the key" in result["error"]


def test_only_one_search_at_a_time_and_it_can_be_stopped():
    def slow_runner(run):
        run.update("documents", "running")
        while not run.stop_requested:
            time.sleep(0.01)
        raise search.SearchStopped

    manager = search.SearchManager(runner=slow_runner)
    run = manager.start(SearchForm())
    with pytest.raises(RuntimeError):
        manager.start(SearchForm())
    assert manager.stop(run.id)
    assert wait_until_done(manager)["status"] == "stopped"


def test_search_api_job_states_and_results_after_a_restart(ready, monkeypatch):
    manager = search.SearchManager()
    monkeypatch.setattr(search, "manager", manager)
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    body = {"location_text": "Germany", "posted_within_hours": 72,
            "job_types": ["full_time_permanent"], "exclude_remote": True}
    assert client.post("/api/search", json=body, headers=HEADERS).json()["status"] == "running"
    assert load_settings().search_form.posted_within_hours == 72
    wait_until_done(manager)
    card = client.get("/api/search/current").json()["search"]["result"]["jobs"]["cards"][0]

    changed = client.post(f"/api/jobs/{card['job_id']}/state", json={"saved": True},
                          headers=HEADERS).json()
    assert changed["state"]["saved"]
    saved = client.get("/api/jobs/marked/saved").json()["cards"]
    assert [c["job_id"] for c in saved] == [card["job_id"]]

    # After a restart there is no running search, but the last results are still shown,
    # with up-to-date job states.
    monkeypatch.setattr(search, "manager", search.SearchManager())
    restored = client.get("/api/search/current").json()["search"]
    restored_card = next(c for c in restored["result"]["jobs"]["cards"]
                         if c["job_id"] == card["job_id"])
    assert restored["status"] == "finished" and restored_card["state"]["saved"]


def test_search_needs_a_job_type():
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    body = {"location_text": "", "posted_within_hours": 24, "job_types": []}
    assert client.post("/api/search", json=body, headers=HEADERS).status_code == 400


def test_unknown_job_state_is_refused():
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    response = client.post("/api/jobs/999/state", json={"saved": True}, headers=HEADERS)
    assert response.status_code == 404


class SummarySource(FakeSource):
    """A job site whose full ads can't be read, like Adzuna when its pages refuse Jobcu."""

    def load_details(self, job, ctx):
        return job


class ResearchingAI(FakeAI):
    """Speaks A2 German, and finds the full ads online: they ask for good German."""

    can_search_the_web = True

    def __init__(self):
        super().__init__()
        self.looked_up: list[str] = []
        self.person_sent: list[str] = []

    def complete_json(self, **request):
        if request["schema_name"] == "OnlineAnswer":
            ids = re.findall(r"^(J\d+) \|", request["prompt"], re.MULTILINE)
            answer = [{"id": job_id, "found": True, "towns": ["Berlin"], "years_required": 6,
                       "languages_asked": [
                           {"language": "German", "level": "B2", "must_have": True},
                           {"language": "English", "level": "B2", "must_have": True}],
                       "doctorate": "not_required",
                       "citizenship_or_clearance": "no_such_requirement",
                       "citizenship_or_clearance_words": ""}
                      for job_id in ids]
            self.person_sent.append(request["prompt"].split("\n", 1)[0])
            return RawReply(json.dumps({"jobs": answer}), Usage(10, 5))
        if request["schema_name"] == "Profile":
            languages = [{"language": "English", "level_as_written": "fluent", "cefr": "C1",
                          "cefr_is_estimate": True},
                         {"language": "German", "level_as_written": "basic", "cefr": "A2",
                          "cefr_is_estimate": True}]
            return RawReply(json.dumps({**PROFILE, "languages": languages}), Usage(10, 5))
        return super().complete_json(**request)

    def research(self, **request):
        from jobcu.ai.base import ResearchReply, Source

        ids = re.findall(r"^(J\d+) \|", request["prompt"], re.MULTILINE)
        self.looked_up += ids
        return ResearchReply("Both ads ask for good German and English, and 6 years.",
                             [Source("https://jobs.test/ad", "Board")],
                             Usage(10, 5, web_searches=len(ids)))


def test_summaries_near_the_top_are_read_online_and_the_rules_applied(ready, monkeypatch):
    ai = ResearchingAI()
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: ai)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [SummarySource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    assert len(ai.looked_up) == 2  # the two related jobs, both scored from a summary
    assert result["steps"][-1]["detail"] == "Found online: the requirements of 2 of 2 jobs"
    card = result["result"]["jobs"]["cards"][0]
    assert card["summary_only"] and card["score"] == 65
    assert card["limits"] == [{"at": 65, "why": "German B2 required, you have A2"}]
    assert card["score_notes"] == [
        "Languages, experience and other requirements read from the full ad online"]
    # Only what the doctorate and citizenship rules need goes with the look-up.
    assert ai.person_sent and all("work_authorisation" in line and "skills" not in line
                                  for line in ai.person_sent)
    assert card["required_languages"] == ["German B2", "English B2"]


def test_when_the_web_look_ups_run_out_jobcu_asks_before_leaving_jobs_unread(ready, monkeypatch):
    ai = ResearchingAI()
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: ai)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [SummarySource()])
    monkeypatch.setattr("jobcu.jobplace.BATCH_SIZE", 1)
    settings = load_settings()
    settings.limits.web_search_cap = 1
    save_settings(settings)
    manager = search.SearchManager()
    counters = []
    update = search.SearchRun.update

    def track(run, step, status, detail=""):
        if step == "places" and (match := re.fullmatch(r"(\d+) of (\d+) jobs", detail)):
            counters.append(tuple(map(int, match.groups())))
        update(run, step, status, detail)

    monkeypatch.setattr(search.SearchRun, "update", track)
    manager.start(SearchForm(location_text="Germany"))
    questions = []
    deadline = time.monotonic() + 15
    while manager.current.status == "running" and time.monotonic() < deadline:
        if manager.current.question:
            questions.append(manager.current.question)
            manager.current.answer(True)
        time.sleep(0.02)
    result = manager.current.snapshot()
    assert result["status"] == "finished", result["error"]
    assert [q["kind"] for q in questions] == ["web_search_cap"]
    assert "1 more job could be read online" in questions[0]["message"]
    assert "about 1 minute" in questions[0]["message"]
    assert len(ai.looked_up) == 2  # both jobs, the second after the yes
    assert result["steps"][-1]["detail"] == "Found online: the requirements of 2 of 2 jobs"
    assert counters == [(0, 2), (1, 2), (2, 2)]


def test_answering_always_removes_the_limit_so_later_searches_don_t_ask(ready, monkeypatch):
    ai = ResearchingAI()
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: ai)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [SummarySource()])
    monkeypatch.setattr("jobcu.jobplace.BATCH_SIZE", 1)
    settings = load_settings()
    settings.limits.web_search_cap = 1
    save_settings(settings)
    manager = search.SearchManager()
    asked, notes = [], []
    for _ in range(2):
        manager.start(SearchForm(location_text="Germany"))
        deadline = time.monotonic() + 15
        while manager.current.status == "running" and time.monotonic() < deadline:
            if manager.current.question:
                asked.append(manager.current.question["kind"])
                manager.current.answer(True, always=True)
            time.sleep(0.02)
        result = manager.current.snapshot()
        assert result["status"] == "finished", result["error"]
        notes.append(result["notes"])
    assert asked == ["web_search_cap"]  # only the first search asked
    assert load_settings().limits.web_search_cap is None  # no limit, however big the search
    assert any("every search from now on, with no limit" in note for note in notes[0])
    assert len(ai.looked_up) == 4  # both jobs in both searches, the second without asking


def test_look_ups_that_lost_their_turn_to_others_running_are_done_before_asking(ready,
                                                                               monkeypatch):
    class SlowResearchingAI(ResearchingAI):
        def research(self, **request):
            time.sleep(0.2)  # the other look-up starts while this one still holds its allowance
            return super().research(**request)

    ai = SlowResearchingAI()
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: ai)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [SummarySource()])
    monkeypatch.setattr("jobcu.jobplace.BATCH_SIZE", 1)
    settings = load_settings()
    settings.limits.web_search_cap = 2  # enough for both jobs, not for both at once
    save_settings(settings)
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    assert result["question"] is None and sorted(ai.looked_up) == ["J0", "J1"]
    assert result["steps"][-1]["detail"] == "Found online: the requirements of 2 of 2 jobs"
