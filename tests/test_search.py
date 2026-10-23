import json
import re
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from conftest import FAKE_CV_LINES, make_pdf
from fastapi.testclient import TestClient

from jobcu import applications, db, documents, jobstore, search
from jobcu.ai.base import AIAuthError, ProviderAdapter, RawReply, Usage
from jobcu.app import create_app
from jobcu.settings import SearchForm, Settings, load_settings, save_settings
from jobcu.sources.base import FoundJob, JobSource, SourceError

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
                 "requirement_checks": [],
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


def wait_until_done(manager, answer=None, timeout=60):
    # Functional completion, not a 15-second performance requirement. Windows CI can spend
    # seconds on each fictional request's local storage; keep a finite hang guard.
    deadline = time.monotonic() + timeout
    while manager.current.status == "running" and time.monotonic() < deadline:
        if answer is not None and manager.current.question:
            manager.current.answer(answer)
        time.sleep(0.02)
    return manager.current.snapshot()


@pytest.mark.parametrize("profession", ["Power Electronics Engineer", "ICU Nurse", "Teacher"])
@pytest.mark.parametrize("outcome", ["stopped", "failed"])
def test_interrupted_initial_search_keeps_full_candidate_evidence(
        ready, monkeypatch, profession, outcome):
    from jobcu import pool, review_capture

    class Source(FakeSource):
        titles = [profession]

        def load_details(self, job, ctx):
            return replace(job, description=f"Full fictional {profession} requirements.",
                           description_is_complete=True)

    class Reader(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps({**PROFILE, "field": profession,
                    "target_roles": [profession], "target_fields": [profession]}), Usage(10, 5))
            if request["schema_name"] == "QuickPassAnswer":
                return RawReply('{"clearly_unrelated": [], "places": []}', Usage(10, 5))
            return super().complete_json(**request)

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Source()])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: Reader())

    def interrupted(*args, **kwargs):
        if outcome == "stopped":
            raise search.SearchStopped
        raise AIAuthError("Fictional provider failure after full ads were read.")

    monkeypatch.setattr(search.scoring, "score_groups", interrupted)
    review_capture.arm_next_search()
    manager = search.SearchManager()
    run = manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == outcome
    kept = pool.load(run.id)
    assert kept is not None and kept.search_id == run.id
    assert len(kept.jobs) == 1
    job = kept.jobs[0]
    assert job.group.best_description_copy.description == (
        f"Full fictional {profession} requirements.")
    assert job.group.best_description_copy.description_is_complete
    assert job.unrelated is False and job.scored is None
    records = [json.loads(line) for line in
               (run.capture.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    checkpoint = next(record for record in records if record["kind"] == "pool_checkpoint")
    assert checkpoint["interrupted"] is True
    assert checkpoint["pool"]["search_id"] == run.id
    assert checkpoint["pool"]["jobs"][0]["group"]["copies"][0]["description_is_complete"]
    assert records[-1]["kind"] == "finished"


def test_interrupted_pool_save_failure_keeps_original_error_and_private_evidence(
        ready, monkeypatch):
    from jobcu import pool, review_capture

    def interrupted(*args, **kwargs):
        raise AIAuthError("Original fictional provider failure.")

    def failed_save(*args):
        raise OSError("Fictional disk failure")

    monkeypatch.setattr(search.scoring, "score_groups", interrupted)
    monkeypatch.setattr(pool, "save", failed_save)
    review_capture.arm_next_search()
    manager = search.SearchManager()
    run = manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "failed"
    assert snapshot["error"] == "Original fictional provider failure."
    assert any("couldn't keep" in note for note in snapshot["notes"])
    records = [json.loads(line) for line in
               (run.capture.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(record["kind"] == "pool_checkpoint" for record in records)


@pytest.mark.parametrize("profession", ["Hardware Engineer", "Community Nurse", "Primary Teacher"])
def test_original_search_keeps_completed_scores_before_a_later_failure(
        ready, monkeypatch, profession):
    from jobcu import pool

    class Source(FakeSource):
        titles = [f"{profession} {i}" for i in range(9)]

    class Reader(FakeAI):
        scoring_calls = 0

        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps({**PROFILE, "field": profession,
                    "target_roles": [profession], "target_fields": [profession]}), Usage(10, 5))
            if request["schema_name"] == "ScoringAnswer":
                self.scoring_calls += 1
                if self.scoring_calls > 1:
                    raise AIAuthError("Fictional later scoring failure")
            return super().complete_json(**request)

    reader = Reader()
    monkeypatch.setattr("jobcu.ai.client.PARALLEL_REQUESTS", 1)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Source()])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: reader)
    manager = search.SearchManager()
    run = manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "failed"
    kept = pool.load(run.id)
    assert len(kept.jobs) == 9
    assert sum(job.scored is not None for job in kept.jobs) == 4
    assert all(job.unrelated is False for job in kept.jobs)


@pytest.mark.parametrize("profession", ["Hardware Engineer", "Community Nurse", "Primary Teacher"])
@pytest.mark.parametrize("failure", ["before_dispatch", "optional_research"])
def test_fresh_search_finishes_automatically_through_recoverable_failures(
        ready, monkeypatch, profession, failure):
    from jobcu.ai.base import AIConnectionError

    class Source(FakeSource):
        titles = [profession]

        def load_details(self, job, ctx):
            return job  # fictional summary requires the later online ad check

    class Reader(FakeAI):
        can_search_the_web = True
        score_attempts = research_attempts = 0

        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps({**PROFILE, "field": profession,
                    "target_roles": [profession], "target_fields": [profession]}), Usage(10, 5))
            if request["schema_name"] == "ScoringAnswer":
                self.score_attempts += 1
                if failure == "before_dispatch" and self.score_attempts == 1:
                    raise AIConnectionError("Fictional connect failure", request_sent=False)
            return super().complete_json(**request)

        def research(self, **request):
            from jobcu.ai.base import ResearchReply
            self.research_attempts += 1
            if failure == "optional_research":
                error = AIConnectionError("Fictional missing terminal frame", request_sent=True)
                error.usage = Usage(web_searches=2, unreported_requests=1)
                raise error
            return ResearchReply("Fictional completed notes", [], Usage(10, 5, web_searches=1))

    reader = Reader()
    monkeypatch.setattr("jobcu.ai.client.PARALLEL_REQUESTS", 1)
    monkeypatch.setattr("jobcu.ai.client.AIClient._wait", lambda *args, **kwargs: None)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Source()])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: reader)
    monkeypatch.setattr(search, "_find_employers", lambda run, *args:
                        run.update("employers", "skipped"))
    # Ordinary structure extraction for the successful fictional research.
    original = reader.complete_json
    def complete(**request):
        if request["schema_name"] == "OnlineAnswer":
            return RawReply('{"jobs":[]}', Usage(10, 5))
        return original(**request)
    monkeypatch.setattr(reader, "complete_json", complete)
    manager = search.SearchManager()
    manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "finished" and snapshot["error"] is None
    assert [j["title"] for j in snapshot["result"]["jobs"]["cards"]] == [profession]
    assert reader.score_attempts == (2 if failure == "before_dispatch" else 1)
    if failure == "optional_research":
        assert reader.research_attempts == 1  # a possibly billed request is never replayed
        assert any("incomplete usage" in n or "complete usage" in n for n in snapshot["notes"])


@pytest.mark.parametrize("profession,task", [
    ("Hardware Engineer", "Design electronic hardware"),
    ("Community Nurse", "Deliver community nursing care"),
    ("Primary Teacher", "Teach primary school pupils"),
])
def test_fresh_search_recovers_native_research_without_another_generation(
        ready, monkeypatch, profession, task):
    import httpx
    from google import genai
    from google.genai import types
    from test_gemini_background import operation
    from test_jobplace import online

    from jobcu.ai.client import AIClient
    from jobcu.ai.gemini_adapter import GeminiAdapter

    class Source(FakeSource):
        titles = [profession]

        def load_details(self, job, ctx):
            return job

    records, requests, gets = {}, [], {}
    reader = FakeAI()
    def handle(request):
        requests.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        if request.method == "POST":
            body = json.loads(request.content)
            identifier = f"fictional-{len(records)}"
            records[identifier] = body
            return httpx.Response(200, json={"id": identifier, "status": "in_progress"})
        identifier = request.url.path.rsplit("/", 1)[1]
        body = records[identifier]
        gets[identifier] = gets.get(identifier, 0) + 1
        if body.get("tools") and gets[identifier] == 1:
            raise httpx.ReadError("Fictional research connection loss", request=request)
        final = operation(identifier, research=bool(body.get("tools")))
        if body.get("tools"):
            words = f"JOB J0\n{task}. This vacancy is based in Berlin."
            final["steps"][-1]["content"] = [{"type": "text", "text": words,
                "annotations": [{"type": "url_citation", "url": "https://jobs.test/0",
                                 "start_index": 0, "end_index": len(words.encode())}]}]
        else:
            fields = body["response_format"]["schema"]["properties"]
            name = next(name for name, field in [
                ("Profile", "summary"), ("LocationInterpretation", "understood_as"),
                ("SearchWordsAnswer", "terms"), ("QuickPassAnswer", "clearly_unrelated"),
                ("ScoringAnswer", "scores"), ("OnlineAnswer", "jobs")] if field in fields)
            if name == "Profile":
                answer = {**PROFILE, "field": profession, "target_roles": [profession],
                          "target_fields": [profession]}
            elif name == "OnlineAnswer":
                answer = {"jobs": [{**online("J0", ["Berlin"]), "requirement_checks": [],
                                    "role_and_skills": 35, "role_words": task}]}
            else:
                answer = json.loads(reader.complete_json(
                    schema_name=name, prompt=body["input"]).text)
            final["steps"][-1]["content"] = [{"type": "text", "text": json.dumps(answer)}]
        return httpx.Response(200, json=final)

    sdk = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
        client_args={"transport": httpx.MockTransport(handle)},
        retry_options=types.HttpRetryOptions(attempts=1)))
    native = GeminiAdapter("fictional-key")
    native._genai_client = sdk
    settings = load_settings()
    settings.ai.recover_interrupted_requests = True
    settings.ai.model = "gemini-3.8-flash"
    save_settings(settings)
    original = AIClient.__init__
    def initialize(self, *args, **kwargs):
        kwargs["sleep"] = lambda seconds: None
        original(self, *args, **kwargs)
    monkeypatch.setattr(AIClient, "__init__", initialize)
    monkeypatch.setattr(AIClient, "adapter", lambda self: native)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Source()])
    monkeypatch.setattr(search, "_find_employers", lambda run, *args:
                        run.update("employers", "skipped"))
    manager = search.SearchManager()
    try:
        manager.start(SearchForm())
        snapshot = wait_until_done(manager)
        assert snapshot["status"] == "finished" and snapshot["error"] is None
        cards = snapshot["result"]["jobs"]["cards"]
        assert len(cards) == 1 and cards[0]["title"] == profession
        research = [key for key, body in records.items() if body.get("tools")]
        assert len(research) == 1 and gets[research[0]] == 2
        assert snapshot["result"]["usage"]["job_places"]["unreported_requests"] == 0
        assert sum(method == "DELETE" for method, _ in requests) == len(records)
        with db.connect() as conn:
            assert conn.execute("SELECT COUNT(*) FROM ai_recovery_requests").fetchone()[0] == 0
    finally:
        sdk.close()


def test_completed_filtering_is_not_reopened_after_full_ads(ready, monkeypatch):
    updates = []
    update = search.SearchRun.update

    def track(run, step_id, status, detail=""):
        updates.append((step_id, status))
        return update(run, step_id, status, detail)

    monkeypatch.setattr(search.SearchRun, "update", track)
    manager = search.SearchManager()
    manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "finished"
    steps = {step["id"]: step for step in snapshot["steps"]}
    assert steps["filtering"]["status"] == steps["eligibility"]["status"] == "done"
    details_end = updates.index(("details", "done"))
    assert ("eligibility", "running") in updates[details_end:]
    assert ("filtering", "running") not in updates[details_end:]


@pytest.mark.parametrize("title", ["Hardware Engineer", "Community Nurse", "Primary Teacher"])
@pytest.mark.parametrize("outcome", ["stopped", "failed"])
def test_resume_before_cards_keeps_identity_and_never_collects_again(
        ready, monkeypatch, title, outcome):
    from jobcu import pipeline, review_capture

    class Source(FakeSource):
        titles = [title]

    monkeypatch.setattr(pipeline, "all_sources", lambda: [Source()])
    original = search.scoring.score_groups
    def interrupt(*args, **kwargs):
        if outcome == "stopped":
            raise search.SearchStopped
        raise AIAuthError("Fictional interrupted provider")
    monkeypatch.setattr(search.scoring, "score_groups", interrupt)
    review_capture.arm_next_search()
    manager = search.SearchManager()
    run = manager.start(SearchForm())
    first = wait_until_done(manager)
    assert first["status"] == outcome and "jobs" not in first["result"]
    monkeypatch.setattr(search.scoring, "score_groups", original)
    def forbidden(*args, **kwargs):
        pytest.fail("Continuing saved work must never collect sources again")
    monkeypatch.setattr(pipeline, "collect", forbidden)
    manager = search.SearchManager()  # Reopen with no in-memory run.
    monkeypatch.setattr(search, "manager", manager)
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        current = client.get("/api/search/current").json()["search"]
        assert current["can_resume"] and not current["can_edit_conditions"]
        response = client.post(f"/api/search/{run.id}/resume", headers=HEADERS)
        assert response.status_code == 200
    resumed = wait_until_done(manager)
    assert resumed["status"] == "finished", resumed["error"]
    assert resumed["id"] == first["id"] and resumed["started_at"] == first["started_at"]
    assert resumed["form"] == first["form"] and resumed["kind"] == "resume"
    if outcome == "failed":
        assert "Before continuation: Fictional interrupted provider" in resumed["notes"]
    assert [card["title"] for card in resumed["result"]["jobs"]["cards"]] == [title]
    assert manager.current.capture.folder == run.capture.folder
    events = [json.loads(line) for line in
              (run.capture.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    continuation = next(i for i, event in enumerate(events) if event["kind"] == "continuation")
    assert any(event["kind"] == "ai_end" for event in events[continuation + 1:])
    assert events[continuation]["previous_snapshot"]["status"] == outcome
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0] == 1


def test_stop_distinguishes_interrupted_work_from_steps_not_reached():
    run = search.SearchRun(1, SearchForm(), datetime.now(UTC).isoformat())
    run.update("filtering", "running")
    run.update("filtering", "done", "Duplicates removed")
    run.update("details", "running")
    run.update("details", "done", "Full ads read")
    run.update("eligibility", "running", "Checking workplaces")
    search._mark_remaining(run, "skipped", stopped=True)
    assert run.step("filtering").status == run.step("details").status == "done"
    assert run.step("eligibility").status == "interrupted"
    assert run.step("scoring").status == run.step("places").status == "skipped"


def test_source_retry_notice_is_one_per_host_but_capture_keeps_each_wait():
    from types import SimpleNamespace

    run = search.SearchRun(1, SearchForm(), datetime.now(UTC).isoformat())
    events = []
    run.capture = SimpleNamespace(event=lambda kind, **values: events.append((kind, values)))
    for seconds in (5, 10, 20):
        search._source_wait_note(run, "employer.example.test", seconds)
    search._source_wait_note(run, "other.example.test", 5)
    assert len(run.notes) == 2
    assert "20 seconds" in run.notes[0] and "5 seconds" in run.notes[1]
    assert [event[1]["seconds"] for event in events] == [5, 10, 20, 5]
    assert all(event[0] == "source_wait_requested" for event in events)


@pytest.mark.parametrize("title", [
    "Power Supply Engineer", "Patient Care Nurse", "Early Years Teacher"])
def test_unicode_duplicate_copies_are_assessed_once_before_cards_are_saved(ready, monkeypatch,
                                                                        title):
    scored_ids = []

    class TrackedAI(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "ScoringAnswer":
                scored_ids.extend(re.findall(r"^JOB (J\d+)", request["prompt"], re.MULTILINE))
            return super().complete_json(**request)

    class Copies(FakeSource):
        def search(self, query, ctx):
            for i, name in enumerate([title, title.replace(" ", "‑", 1)]):
                yield FoundJob(source="fake" if i == 0 else "another", source_job_id=str(i),
                               url=f"https://jobs.test/{i}", title=name, company="Example Works",
                               location_text="Berlin", country="DE", posted_at=datetime.now(UTC),
                               date_precision="exact", description="Short")

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: TrackedAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Copies()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished"
    cards = result["result"]["jobs"]["cards"]
    assert len(cards) == len(scored_ids) == 1
    assert {cards[0]["main_link"]["url"], *(link["url"] for link in cards[0]["also_on"])} == {
        "https://jobs.test/0", "https://jobs.test/1"}


@pytest.mark.parametrize("title", [
    "Power Electronics Engineer", "Registered Nurse", "Primary Teacher"])
def test_decorated_recruiter_copies_use_one_assessment_and_keep_their_saved_mark(
        ready, monkeypatch, title):
    from jobcu.dedupe import JobGroup

    text = " ".join(f"Fictional duty {i} includes development validation and reporting."
                    for i in range(60))
    names = [title, f"Gesucht: {title}", f"{title} - Example Recruitment Ltd"]
    copies = [FoundJob("fake", str(i), f"https://jobs.test/{i}", name,
              company="Example Recruitment Services" if i == 1 else "Example Recruitment Ltd",
              location_text="Berlin", country="DE", posted_at=datetime.now(UTC),
              date_precision="exact", description=text) for i, name in enumerate(names)]
    with db.connect() as conn:
        old_search = conn.execute("INSERT INTO searches (status,form_json) "
                                  "VALUES ('finished','{}')").lastrowid
    ids, _ = jobstore.remember([JobGroup([c], source_kinds={"fake": "job_board"})
                               for c in copies], old_search)
    jobstore.set_state(ids[1], saved=True)
    assessed = []

    class Tracked(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "ScoringAnswer":
                assessed.extend(re.findall(r"^JOB (J\d+)", request["prompt"], re.MULTILINE))
            return super().complete_json(**request)

    class Copies(FakeSource):
        def search(self, query, ctx):
            yield from copies

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: Tracked())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Copies()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    cards = result["result"]["jobs"]["cards"]
    assert len(cards) == len(assessed) == 1
    assert cards[0]["state"]["saved"]
    assert all(s.saved for s in jobstore.states(ids).values())


def test_two_identical_searches_reuse_setup_but_collect_and_score_afresh(ready, monkeypatch):
    calls, collections = [], []

    class TrackedAI(FakeAI):
        def complete_json(self, **request):
            name = request["schema_name"]
            calls.append(name)
            if name == "SearchWordsAnswer":
                return RawReply(json.dumps({"terms": [
                    {"text": text, "language": code, "kind": kind}
                    for code in ("en", "de")
                    for kind, text in (("job_title", "Hardware Engineer"),
                                       ("field_or_skill", "PCB design"))]}), Usage(10, 5))
            reply = super().complete_json(**request)
            if name == "ScoringAnswer" and calls.count(name) == 2:
                answer = json.loads(reply.text)
                for score in answer["scores"]:
                    score["role_and_skills"] = 20
                return RawReply(json.dumps(answer), reply.usage)
            return reply

    class TrackedSource(FakeSource):
        def search(self, query, ctx):
            collections.append(query)
            yield from super().search(query, ctx)

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: TrackedAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [TrackedSource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    first = wait_until_done(manager)
    manager.start(SearchForm(location_text="Germany"))
    second = wait_until_done(manager)
    assert first["status"] == second["status"] == "finished"
    assert calls.count("Profile") == calls.count("LocationInterpretation") == 1
    assert calls.count("SearchWordsAnswer") == 1
    assert calls.count("ScoringAnswer") == 2 and len(collections) == 2
    assert second["result"]["jobs"]["cards"][0]["score"] < \
        first["result"]["jobs"]["cards"][0]["score"]
    for step in second["steps"]:
        if step["id"] == "location":
            assert "Using saved location understanding" in step["detail"]
        if step["id"] == "search_words":
            assert "Using saved search words" in step["detail"]


@pytest.mark.parametrize("changed_box", ["about_you", "location_text"])
@pytest.mark.parametrize("edit", ["a", " ", "\n"])
def test_setup_box_edits_reanalyse_even_when_ai_returns_the_same_understanding(
        ready, monkeypatch, changed_box, edit):
    calls, queries = [], []

    class SameUnderstandingAI(FakeAI):
        def complete_json(self, **request):
            calls.append(request["schema_name"])
            if request["schema_name"] == "SearchWordsAnswer":
                return RawReply(json.dumps({"terms": [
                    {"text": text, "language": code, "kind": kind}
                    for code in ("en", "de")
                    for kind, text in (("job_title", "Hardware Engineer"),
                                       ("field_or_skill", "PCB design"))]}), Usage(10, 5))
            return super().complete_json(**request)

    class TrackedSource(FakeSource):
        def search(self, query, ctx):
            queries.append(query)
            yield from super().search(query, ctx)

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: SameUnderstandingAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [TrackedSource()])
    manager = search.SearchManager()
    form = SearchForm(location_text="Germany", about_you="A fictional note")
    manager.start(form)
    first = wait_until_done(manager)
    changed = form.model_copy(update={changed_box: getattr(form, changed_box) + edit})
    manager.start(changed)
    second = wait_until_done(manager)
    assert first["status"] == second["status"] == "finished"
    assert calls.count("Profile") == (2 if changed_box == "about_you" else 1)
    assert calls.count("LocationInterpretation") == (2 if changed_box == "location_text" else 1)
    assert calls.count("SearchWordsAnswer") == 2
    assert calls.count("ScoringAnswer") == 2 and len(queries) == 2
    assert first["result"]["search_words"] == second["result"]["search_words"]
    assert [c["score"] for c in first["result"]["jobs"]["cards"]] == \
        [c["score"] for c in second["result"]["jobs"]["cards"]]
    manager.start(changed)
    third = wait_until_done(manager)
    assert third["status"] == "finished"
    assert calls.count("SearchWordsAnswer") == 2  # identical edited text now reuses safely
    assert calls.count("ScoringAnswer") == 3 and len(queries) == 3


@pytest.mark.parametrize("case", ["old", "closed", "unknown"])
def test_greenhouse_detail_dates_decide_before_scoring_and_unknown_stays_visible(
    ready, monkeypatch, case,
):
    from jobcu.sources.careers import Employer
    from jobcu.sources.greenhouse import GreenhouseSource, to_found_job

    scored_calls, detail_calls = [], []

    class TrackedAI(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "ScoringAnswer":
                scored_calls.append(request)
            return super().complete_json(**request)

    class FictionalGreenhouse(GreenhouseSource):
        def covers(self, query):
            return True

        def search(self, query, ctx):
            yield replace(to_found_job({"id": 1, "title": "Hardware Engineer",
                         "updated_at": datetime.now(UTC).isoformat(),
                         "absolute_url": "https://example.test/job",
                         "location": {"name": "Berlin"}},
                         Employer("Fictional Devices", "greenhouse", "fictional", ("DE",))),
                         country="DE")

        def get_json(self, url, ctx):
            detail_calls.append(url)
            data = {"content": "<p>Full fictional hardware engineering requirements.</p>"}
            if case == "old":
                data["first_published"] = (datetime.now(UTC) - timedelta(days=20)).isoformat()
            if case == "closed":
                data["first_published"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
                data["application_deadline"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
            return data

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [FictionalGreenhouse()])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: TrackedAI())
    manager = search.SearchManager()
    manager.start(SearchForm())
    result = wait_until_done(manager)
    assert result["status"] == "finished" and len(detail_calls) == 1
    cards = result["result"]["jobs"]
    if case == "unknown":
        assert len(scored_calls) == 1 and len(cards["date_unknown"]) == 1
        assert not cards["cards"] and cards["date_unknown"][0]["posted_at"] is None
    else:
        assert scored_calls == []
        assert not cards["cards"] and not cards["date_unknown"]


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
    assert snapshot["steps"][0]["status"] == {
        "failed": "failed", "stopped": "interrupted", "finished": "skipped"}[outcome]
    with db.connect() as conn:
        row = conn.execute("SELECT status, finished_at FROM searches WHERE id = ?",
                           (run.id,)).fetchone()
    assert row["status"] == outcome and row["finished_at"] is not None
    saved = jobstore.latest_results()
    assert json.loads(saved[1]) == snapshot


def test_failed_latest_attempt_without_cards_survives_app_restart(monkeypatch):
    from jobcu import pool

    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id,status,form_json) VALUES (1,'finished','{}')")
        conn.execute("INSERT INTO search_results VALUES (1, ?)",
                     (json.dumps({"id": 1, "result": {"jobs": {"cards": []}}}),))

    def interrupted(run):
        run.note("Fictional interrupted workplace research.")
        raise AIAuthError("Fictional service failure before scoring.")

    manager = search.SearchManager(runner=interrupted)
    run = manager.start(SearchForm())
    wait_until_done(manager)
    # A new manager models reopening Jobcu: it has no current in-memory run.
    monkeypatch.setattr(search, "manager", search.SearchManager())
    monkeypatch.setattr(pool, "exists", lambda search_id: True)
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        saved = client.get("/api/search/current").json()["search"]
    assert saved["id"] == run.id and saved["status"] == "failed"
    assert saved["error"] == "Fictional service failure before scoring."
    assert not saved["can_edit_conditions"]
    with db.connect() as conn:
        assert conn.execute("SELECT 1 FROM search_results WHERE search_id=1").fetchone()


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
    assert card["score"] == 80 and card["is_new"] and not card["summary_only"]
    assert card["location_checks"][0]["status"] == "verified"
    assert jobs["sources"][0]["unique"] == 2 and jobs["new_count"] == 2

    # The next search recognises the same jobs: no "New" badge.
    manager.start(SearchForm(location_text="Germany"))
    again = wait_until_done(manager)["result"]["jobs"]
    assert again["new_count"] == 0


def test_opt_in_capture_keeps_raw_rejected_jobs_full_ads_and_exact_run(ready):
    from jobcu import review_capture

    review_capture.arm_next_search()
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany", posted_within_hours=72))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    capture = manager.current.capture
    events = [json.loads(line) for line in
              (capture.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    raw = next(event for event in events if event["kind"] == "collected")
    assert "Nurse" in {job["title"] for job in raw["jobs"]}
    decided = next(event for event in events if event["kind"] == "decided")
    assert any(copy["description_is_complete"] for job in decided["pool"]["jobs"]
               for copy in job["group"]["copies"])
    assert events[-1]["kind"] == "finished"
    assert events[-1]["snapshot"]["id"] == result["id"]
    assert events[-1]["snapshot"]["form"]["posted_within_hours"] == 72
    manager.start(SearchForm(location_text="Germany"))
    assert wait_until_done(manager)["status"] == "finished"
    assert manager.current.capture is None


@pytest.mark.parametrize(("title", "field", "skill"), [
    ("Power Electronics Engineer", "Electronics", "Power converter design"),
    ("Registered Nurse", "Nursing", "Clinical patient care"),
])
def test_recovered_full_requirements_reach_matching_and_change_the_explanation(
        ready, monkeypatch, title, field, skill):
    full = f"{title}. Full fictional ad: at least eight years of experience are required."
    profile = {**PROFILE, "summary": f"Experienced {title}.", "field": field,
               "skills": [skill], "technical_areas": [field], "target_fields": [field],
               "target_roles": [title], "current_or_last_role": title}
    documents.save_upload("cv", "fictional-cv.pdf", make_pdf([
        "Alex Example", f"{title} with five years of experience. Skills: {skill}. " * 4]))
    documents.save_upload("cover_letter", "fictional-letter.txt",
                          f"I am seeking work as a {title}. I enjoy {skill}. ".encode() * 4)

    class MatchingAI(FakeAI):
        evidence = []

        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps(profile), Usage(10, 5))
            reply = super().complete_json(**request)
            if request["schema_name"] == "ScoringAnswer":
                self.evidence.append(request["prompt"])
                answer = json.loads(reply.text)
                for score in answer["scores"]:
                    score["years_required"] = 8 if full in request["prompt"] else None
                return RawReply(json.dumps(answer), reply.usage)
            return reply

    class MatchedCopy(FakeSource):
        def __init__(self, name, kind):
            self.id, self.name, self.kind = name, name, kind
            self.reads = 0

        def search(self, query, ctx):
            yield FoundJob(source=self.id, source_job_id="1", url=f"https://{self.id}.test/1",
                           title=title, company="Fictional Employer", location_text="Berlin",
                           country="DE", posted_at=datetime.now(UTC), date_precision="exact",
                           description="Short summary without requirements")

        def load_details(self, job, ctx):
            self.reads += 1
            if self.kind == "employer":
                raise SourceError("Fictional unavailable detail")
            return replace(job, description=full, description_is_complete=True)

    adapter = MatchingAI()
    employer, board = MatchedCopy("employer", "employer"), MatchedCopy("board", "job_board")
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: adapter)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [employer, board])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    cards = result["result"]["jobs"]["cards"]
    assert len(cards) == 1 and employer.reads == board.reads == 1
    assert len(adapter.evidence) == 1 and full in adapter.evidence[0]
    assert not cards[0]["summary_only"] and cards[0]["score"] == 80
    assert any("8+ years" in limit["why"] for limit in cards[0]["limits"])
    # A new search reuses bounded-age text but makes a fresh matching judgement.
    manager.start(SearchForm(location_text="Germany"))
    again = wait_until_done(manager)
    assert again["status"] == "finished", again["error"]
    assert len(adapter.evidence) == 2 and full in adapter.evidence[1]
    assert employer.reads == board.reads == 1
    assert again["result"]["jobs"]["cards"][0]["score"] == 80


@pytest.mark.parametrize(("new_fact", "reason"), [
    ({"posted_at": datetime.now(UTC) - timedelta(days=10)}, "too_old"),
    ({"closes_at": datetime.now(UTC) - timedelta(days=1)}, "closed"),
    ({"country": "AT"}, "country"),
    ({"job_types": ["part_time"]}, "job_type"),
    ({"work_mode": "remote"}, "remote"),
])
@pytest.mark.parametrize("cached", [False, True])
def test_objective_facts_in_full_evidence_are_checked_before_scoring(
        ready, monkeypatch, new_fact, reason, cached):
    from jobcu.filters import REASONS

    copy = FoundJob(source="fake", source_job_id="1", url="https://jobs.test/1",
                    title="Hardware Engineer", company="Fictional Employer",
                    country="DE", location_text="Berlin", posted_at=datetime.now(UTC),
                    date_precision="exact", description="Short summary")
    full = replace(copy, description="Full fictional requirements", description_is_complete=True,
                   **new_fact)

    class OneCopy(FakeSource):
        reads = 0

        def search(self, query, ctx):
            yield copy

        def load_details(self, job, ctx):
            self.reads += 1
            return full

    class NoScoring(FakeAI):
        def complete_json(self, **request):
            assert request["schema_name"] != "ScoringAnswer", "Ineligible job reached scoring"
            return super().complete_json(**request)

    source = OneCopy()
    if cached:
        jobstore.remember_ad(full)
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [source])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: NoScoring())
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany", exclude_remote=True,
                             job_types=["full_time_permanent"]))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    jobs = result["result"]["jobs"]
    assert jobs["cards"] == jobs["date_unknown"] == []
    assert jobs["counts"]["left_out"] == [{"reason": REASONS[reason], "count": 1}]
    assert source.reads == (0 if cached else 1)


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
    assert next(step for step in run.snapshot()["steps"] if step["id"] == "scoring")[
        "elapsed_seconds"] == 2

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
    assert next(step for step in snapshot["steps"] if step["id"] == "scoring")[
        "elapsed_seconds"] == 10
    assert snapshot["waiting_seconds"] == 5
    assert snapshot["steps"][0]["elapsed_seconds"] == 0


def test_quality_sample_keeps_the_final_online_score(ready, monkeypatch):
    from jobcu import jobplace, quality
    from jobcu.scoring import LanguageAsked

    monkeypatch.setattr(FakeSource, "load_details", lambda self, job, ctx: job)

    def found(client, groups, indexes, profile, on_progress, *, on_evidence=None,
              research_cache=None):
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


@pytest.mark.parametrize("role", ["Hardware Engineer", "Nurse", "Teacher"])
@pytest.mark.parametrize("include_students", [False, True])
def test_online_checks_skip_proven_ad_exclusions(ready, monkeypatch, role, include_students):
    from jobcu import jobplace

    class Roles(FakeSource):
        def search(self, query, ctx):
            for i, prefix in enumerate(("Student", "Remote", "Local", "Unknown")):
                yield FoundJob(
                    source="fake", source_job_id=str(i), url=f"https://jobs.test/{i}",
                    title=f"{prefix} {role}", company=f"Fictional Employer {i}",
                    country="DE", location_text="Berlin", posted_at=datetime.now(UTC),
                    date_precision="exact", description="Fictional vacancy summary.",
                    job_types=(["full_time_permanent", "fixed_term"]
                               if prefix != "Unknown" else []),
                )

        def load_details(self, job, ctx):
            return job

    class AdFacts(FakeAI):
        can_search_the_web = True

        def complete_json(self, **request):
            reply = super().complete_json(**request)
            answer = json.loads(reply.text)
            if request["schema_name"] == "Profile":
                answer.update(summary=f"Fictional {role}.", field=role,
                              target_roles=[role], target_fields=[role])
            if request["schema_name"] == "ScoringAnswer":
                for score in answer["scores"]:
                    block = re.search(
                        rf"JOB {score['job_id']}\b(.*?)(?=\nJOB |\Z)",
                        request["prompt"], re.DOTALL)[1]
                    if f"Student {role}" in block:
                        score["job_type"] = "internship_or_working_student"
                    if f"Remote {role}" in block:
                        score.update(fully_remote=True, work_mode="remote")
                    if f"Unknown {role}" in block:
                        score["job_type"] = "unclear"
            return RawReply(json.dumps(answer), reply.usage)

    looked_up = []

    def online(client, groups, indexes, profile, on_progress, *, on_evidence=None,
               research_cache=None):
        looked_up.extend(groups[i].main.title for i in indexes)
        return jobplace.LookedUp(asked=set(indexes))

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [Roles()])
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: AdFacts())
    monkeypatch.setattr(jobplace, "find_online", online)
    monkeypatch.setattr(search, "_find_employers", lambda run, *args:
                        run.update("employers", "skipped"))
    wanted = ["full_time_permanent", "fixed_term"]
    if include_students:
        wanted.append("internship_or_working_student")
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany", job_types=wanted, exclude_remote=True))
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "finished", snapshot["error"]
    expected = {f"Local {role}", f"Unknown {role}"} | (
        {f"Student {role}"} if include_students else set())
    assert set(looked_up) == expected
    assert {card["title"] for card in snapshot["result"]["jobs"]["cards"]} == expected
    left_out = {row["reason"]: row["count"]
                for row in snapshot["result"]["jobs"]["counts"]["left_out"]}
    assert left_out["Fully remote, according to the ad text"] == 1
    assert left_out.get("A job type you didn't tick, according to the ad text", 0) == (
        0 if include_students else 1)


@pytest.mark.parametrize("same_reference", [False, True])
def test_agency_names_cannot_replace_copy_evidence(ready, monkeypatch, same_reference):
    # Two summaries do not prove one vacancy. An exact source reference does.
    class AgencyTwice(FakeSource):
        def search(self, query, ctx):
            for i, text in enumerate(["Short", "Another short text"]):
                reference = "a0" if same_reference else f"a{i}"
                yield FoundJob(source="fake", source_job_id=reference,
                               url=f"https://jobs.test/{reference}",
                               title="Hardware Engineer", company="Augusta Personaldienst",
                               location_text="Berlin", country="DE",
                               posted_at=datetime.now(UTC), date_precision="exact",
                               description=text)

    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [AgencyTwice()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    jobs = wait_until_done(manager)["result"]["jobs"]
    cards = jobs["cards"]
    assert [card["title"] for card in cards] == ["Hardware Engineer"] * (
        1 if same_reference else 2)
    assert len({card["job_id"] for card in cards}) == len(cards)
    if not same_reference:
        jobstore.set_state(cards[0]["job_id"], saved=True)
        states = jobstore.states([card["job_id"] for card in cards])
        assert states[cards[0]["job_id"]].saved
        assert cards[1]["job_id"] not in states


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
    snapshot = wait_until_done(manager)
    assert snapshot["status"] == "stopped"
    assert search.STOPPED_NOTE in snapshot["notes"]
    assert search.STOPPING_NOTE not in snapshot["notes"]
    assert search.STOPPED_NOTE in json.loads(jobstore.latest_results()[1])["notes"]


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
    assert card["summary_only"] and card["score"] == 76  # below the new maximum
    assert card["limits"] == [
        {"at": 80, "why": "German B2 required, you have A2"},
        {"at": 80, "why": "Some gaps in the main work or a neighbouring specialisation"},
    ]
    assert card["score_notes"] == [
        "Online evidence used to check requirements",
        "Only incomplete ad evidence was available; other requirements may be missing"]
    # Eligibility comparisons need stated qualifications, study status and skills too.
    assert ai.person_sent and all("work_authorisation" in line and "skills" in line
                                  and "education" in line for line in ai.person_sent)
    assert all("ignored_as_application_specific" not in line for line in ai.person_sent)
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


def test_grounded_eligibility_limit_reaches_visible_card_without_hiding_job(ready, monkeypatch):
    fact = "Laboratory safety certificate has expired."
    clause = "Must hold a current laboratory safety certificate"

    class EligibilityAI(FakeAI):
        def complete_json(self, **request):
            if request["schema_name"] == "Profile":
                return RawReply(json.dumps({**PROFILE, "summary": "Hardware engineer. " + fact}),
                                Usage(10, 5))
            reply = super().complete_json(**request)
            if request["schema_name"] == "ScoringAnswer":
                answer = json.loads(reply.text)
                for score in answer["scores"]:
                    score["hard_requirements"] = 14  # contradicts the explicit comparison
                    score["requirement_checks"] = [{
                        "requirement": "Current laboratory safety certificate",
                        "ad_words": clause, "profile_words": fact, "status": "not_met",
                    }]
                return RawReply(json.dumps(answer), reply.usage)
            return reply

    class EligibilitySource(FakeSource):
        titles = ["Hardware Engineer"]

        def load_details(self, job, ctx):
            job.description, job.description_is_complete = clause + ". Hardware design.", True
            return job

    documents.save_upload("cover_letter", "letter.txt",
                          ("I seek regular hardware design work and enjoy laboratory teamwork. "
                           + fact).encode("utf-8"))
    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: EligibilityAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [EligibilitySource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany"))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    card = result["result"]["jobs"]["cards"][0]
    assert card["title"] == "Hardware Engineer" and card["score"] == 55
    assert card["parts"]["hard_requirements"] == 10
    assert card["limits"] == [{
        "at": 55, "why": "Current laboratory safety certificate: not met by the stated profile",
    }, {"at": 80, "why": "Some gaps in the main work or a neighbouring specialisation"}]


@pytest.mark.parametrize('profession', ['Power Electronics Engineer', 'Community Nurse', 'Teacher'])
def test_reached_limit_refuses_start_before_any_collection_or_cache_work(ready, monkeypatch,
                                                                       profession):
    from jobcu import review_capture
    from jobcu.ai.base import AILimitReached
    from jobcu.ai.usage import UsageLog

    settings = load_settings()
    settings.limits.monthly_token_limit = 1
    save_settings(settings)
    UsageLog().record(step='scoring', provider='gemini', model='model-a', usage=Usage(2))
    review_capture.arm_next_search()
    def forbidden(*args, **kwargs):
        pytest.fail('A blocked attempt must not run preparation, collection or generation')
    monkeypatch.setattr(search, 'read_profile_reusing', forbidden)
    monkeypatch.setattr('jobcu.pipeline.collect', forbidden)
    manager = search.SearchManager()
    with pytest.raises(AILimitReached):
        manager.start(SearchForm(about_you=profession))
    assert manager.current is None
    with db.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM searches').fetchone()[0] == 0
    from jobcu.paths import data_dir
    assert (data_dir()/review_capture.ARM_FILE).exists()


def test_api_budget_refusal_does_not_replace_saved_query_or_start_work(ready, monkeypatch):
    from jobcu.ai.usage import UsageLog

    settings = load_settings()
    settings.limits.monthly_token_limit = 1
    save_settings(settings)
    UsageLog().record(step='scoring', provider='gemini', model='model-a', usage=Usage(2))
    monkeypatch.setattr(search, 'manager', search.SearchManager())
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    result = client.post('/api/search', json=SearchForm(location_text='New place').model_dump(),
                         headers=HEADERS)
    assert result.status_code == 400 and 'monthly' in result.json()['detail']
    assert load_settings().search_form == settings.search_form
    assert client.get('/api/usage').json()['search_budget_problem']


@pytest.mark.parametrize('profession', ['Hardware Engineer', 'Community Nurse', 'Teacher'])
def test_title_stage_failure_retains_raw_collection_without_a_capture(ready, monkeypatch,
                                                                    profession):
    class Source(FakeSource):
        titles = [profession]
        def search(self, query, ctx):
            for job in super().search(query, ctx):
                job.title_unmatched = True
                yield job
    def failed(*args, **kwargs):
        raise AIAuthError('Fictional title-stage refusal')
    monkeypatch.setattr('jobcu.pipeline.all_sources', lambda: [Source()])
    monkeypatch.setattr(search, 'screen_titles', failed)
    manager = search.SearchManager()
    run = manager.start(SearchForm())
    snapshot = wait_until_done(manager)
    assert snapshot['status'] == 'failed' and run.capture is None
    evidence = snapshot['result']['collected_evidence']
    assert evidence['stage'] == 'before_title_screening'
    assert [job['title'] for job in evidence['jobs']] == [profession]
    assert evidence['reports'][0]['requests'] == 1
    assert evidence['jobs'][0]['posted_at']
    with db.connect() as conn:
        saved = json.loads(conn.execute('SELECT result_json FROM search_results WHERE search_id=?',
                                        (run.id,)).fetchone()[0])
    assert saved['result']['collected_evidence'] == evidence


def test_fresh_search_uses_its_extra_allowance_when_ordinary_budget_is_exhausted(
        ready, temporary_data_dir):
    from test_extra_budgets import configure
    settings, log, allowance = configure(temporary_data_dir)
    log.record(step='scoring', provider='gemini', model='fictional-model', usage=Usage(200_000))
    ordinary_before = log.ordinary_this_month()
    manager = search.SearchManager()
    run = manager.start(settings.search_form)
    snapshot = wait_until_done(manager)
    assert snapshot['status'] == 'finished'
    assert log.ordinary_this_month() == ordinary_before
    with db.connect() as conn:
        rows = conn.execute('SELECT DISTINCT budget_id FROM ai_usage WHERE search_id=?',
                             (run.id,)).fetchall()
    assert [row[0] for row in rows] == [allowance.id]
    assert load_settings().limits == settings.limits
