import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from jobcu import db, quality, reset, search
from jobcu.app import create_app
from jobcu.keystore import KeyStore
from jobcu.logs import setup_logging
from jobcu.settings import SearchForm, Settings, load_settings, save_settings

HEADERS = {"X-Jobcu": "1"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(search, "manager", search.SearchManager())
    return TestClient(create_app(), base_url="http://127.0.0.1:8765")


@pytest.fixture
def populated(temporary_data_dir):
    settings = Settings(search_form=SearchForm(location_text="Fictional town", about_you="Note"))
    settings.ai.provider = "openai_compatible"
    settings.ai.model = "fictional-model"
    settings.limits.monthly_token_limit = 500
    settings.sources_disabled = ["arbeitnow"]
    settings.search_form.posted_within_hours = 6
    save_settings(settings)
    KeyStore().set("reed_api_key", "fictional-key-value")
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id,status,form_json) VALUES (7,'finished','{}')")
        conn.execute("INSERT INTO jobs (id,title,company) VALUES (5,'Nurse','Fictional Clinic')")
        conn.execute("INSERT INTO job_keys VALUES ('example',5)")
        conn.execute("INSERT INTO job_fingerprints VALUES ('example',5,'DE')")
        conn.execute("INSERT INTO job_states (job_id,saved,applied,dismissed) VALUES (5,1,1,1)")
        conn.execute("INSERT INTO job_cards (job_id,card_json) VALUES (5,'{}')")
        conn.execute("INSERT INTO search_results VALUES (7,'{}')")
        conn.execute("INSERT INTO search_pool VALUES (7,'{}')")
        conn.execute("INSERT INTO application_link_reports (url,job_id,source) "
                     "VALUES ('https://example.test/apply',5,'example')")
        conn.execute("INSERT INTO profile_cache (key,profile_json) VALUES ('example','{}')")
        conn.execute("INSERT INTO ad_texts (source,source_job_id,details_json) "
                     "VALUES ('example','ad','{}')")
        conn.execute("INSERT INTO travel_memory VALUES ('a','b','train','ai',12,'2026-10-09')")
        conn.execute("INSERT INTO found_employers VALUES "
                     "('example','board','Fictional Clinic','DE',0,'Town','2026-10-09')")
        conn.execute("INSERT INTO employer_searches (subject,country,searched_at,complete) "
                     "VALUES ('nursing','DE','2026-10-09',1)")
        conn.execute("INSERT INTO ai_usage (search_id,step,provider,model,input_tokens,"
                     "output_tokens,cached_input_tokens,reasoning_tokens,web_searches) "
                     "VALUES (7,'scoring','openai_compatible','fictional-model',100,20,0,0,0)")
        day = datetime.now(UTC).strftime("%Y-%m-%d")
        conn.execute("INSERT INTO source_requests VALUES (?, 'google_maps', 8)", (day,))
    quality.add("scored", [{"source": "example", "source_job_id": "ad", "title": "Nurse",
                           "url": "https://example.test/ad", "text": "Fictional ad", "score": 70}])
    quality.rate(quality.all_ads()[0].id, "good", [], "Owner review")
    folder = temporary_data_dir
    for directory, filename in [("documents", "cv.pdf"), ("logs", "jobcu.log.1"),
                                ("assistant-reviews", "review.json")]:
        (folder / directory).mkdir(exist_ok=True)
        (folder / directory / filename).write_text("Fictional private evidence", encoding="utf-8")
    (folder / "assistant-authorization.json").write_text('{"scope":"fictional"}', encoding="utf-8")
    (folder / "assistant-checkpoint.json").write_text('{"evidence":"fictional"}', encoding="utf-8")
    return folder


def count(table):
    with db.connect() as conn:
        return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def request_reset(client, scope):
    return client.post("/api/data/reset", headers=HEADERS,
                       json={"scope": scope, "confirm": "RESET"})


@pytest.mark.parametrize("scope", ["search", "review", "all"])
def test_scopes_clear_exact_data_preserve_choices_and_real_spending(client, populated, scope):
    before = load_settings().model_dump()
    response = request_reset(client, scope)
    assert response.status_code == 200 and response.json() == {"reset": True, "scope": scope}
    assert all(count(table) == (1 if scope == "review" else 0) for table in reset.SEARCH_TABLES)
    assert count("quality_ads") == (1 if scope == "search" else 0)
    with db.connect() as conn:
        usage = conn.execute("SELECT * FROM ai_usage").fetchone()
        assert usage["input_tokens"] == 100 and usage["output_tokens"] == 20
        assert usage["search_id"] == (7 if scope == "review" else None)
        assert conn.execute("SELECT count FROM source_requests").fetchone()[0] == 8
    after = load_settings().model_dump()
    if scope != "review":
        before["search_form"].update(location_text="", about_you="")
    assert after == before
    assert KeyStore().get("reed_api_key") == "fictional-key-value"
    assert (populated / "assistant-authorization.json").read_text() == '{"scope":"fictional"}'
    for name in ("documents", "assistant-reviews", "logs", "assistant-checkpoint.json"):
        assert (populated / name).exists() == (scope != "all")
    assert request_reset(client, scope).status_code == 200  # safe to repeat


def test_clear_search_forgets_finished_run_and_stays_empty_after_restart(client, populated):
    run = search.SearchRun(id=7, form=SearchForm(), started_at="now", status="finished")
    search.manager._current = run
    assert request_reset(client, "review").status_code == 200
    assert search.manager.current is run
    assert request_reset(client, "search").status_code == 200
    assert client.get("/api/search/current").json() == {"search": None}
    search.manager = search.SearchManager()
    assert client.get("/api/search/current").json() == {"search": None}
    assert client.get("/api/jobs/marked/saved").json() == {"cards": []}
    assert client.get("/api/applications/excluded").json() == {"links": []}
    assert client.get("/api/usage").json()["this_month"]["tokens"] == 120


@pytest.mark.parametrize("body", [{"scope": "all"}, {"scope": "all", "confirm": "yes"},
                                  {"scope": "settings", "confirm": "RESET"}])
def test_explicit_valid_confirmation_required(client, populated, body):
    assert client.post("/api/data/reset", headers=HEADERS, json=body).status_code == 422
    assert count("jobs") == 1


def test_reset_requires_local_page_header_and_origin(client, populated):
    body = {"scope": "all", "confirm": "RESET"}
    assert client.post("/api/data/reset", json=body).status_code == 403
    assert client.post("/api/data/reset", json=body,
                       headers={**HEADERS, "Origin": "https://example.test"}).status_code == 403
    assert count("jobs") == 1


@pytest.mark.parametrize("scope", ["search", "review", "all"])
def test_no_reset_during_search_or_final_save(client, populated, scope):
    search.manager._current = search.SearchRun(id=7, form=SearchForm(), started_at="now")
    assert request_reset(client, scope).status_code == 409
    assert count("jobs") == 1 and count("quality_ads") == 1
    assert load_settings().search_form.location_text == "Fictional town"


def test_database_error_rolls_back_deletion_and_keeps_current(client, populated, monkeypatch):
    run = search.SearchRun(id=7, form=SearchForm(), started_at="now", status="finished")
    search.manager._current = run
    connect = db.connect

    class FailingConnection:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, sql, *args):
            if sql == "DELETE FROM searches":
                raise sqlite3.OperationalError("Fictional disk failure")
            return self.connection.execute(sql, *args)

    @contextmanager
    def fail(*args):
        with connect(*args) as conn:
            yield FailingConnection(conn)

    monkeypatch.setattr(db, "connect", fail)
    response = request_reset(client, "all")
    assert response.status_code == 500
    assert search.manager.current is run and count("jobs") == 1
    assert (populated / "documents" / "cv.pdf").exists()


def test_failed_file_delete_is_incomplete_and_retry_finishes(client, populated, monkeypatch):
    rmtree = reset.shutil.rmtree
    search.manager._current = search.SearchRun(id=7, form=SearchForm(), started_at="now",
                                              status="finished")

    def fail(path):
        if path.name == "documents":
            raise PermissionError("Fictional file in use")
        rmtree(path)

    monkeypatch.setattr(reset.shutil, "rmtree", fail)
    assert request_reset(client, "all").status_code == 500
    assert count("jobs") == 0 and search.manager.current is None
    assert (populated / "documents" / "cv.pdf").exists()
    monkeypatch.setattr(reset.shutil, "rmtree", rmtree)
    assert request_reset(client, "all").status_code == 200
    assert not (populated / "documents").exists() and count("ai_usage") == 1


def test_unknown_future_table_is_not_silently_left_behind(client, populated):
    with db.connect() as conn:
        conn.execute("CREATE TABLE future_private_data (text TEXT)")
    assert request_reset(client, "all").status_code == 500
    assert count("jobs") == 1


@pytest.mark.parametrize("journal_mode", ["DELETE", "PERSIST", "WAL"])
def test_deleted_profile_text_is_not_left_in_compacted_database(client, populated, journal_mode):
    marker = "fictional-private-profile-for-reset-verification"
    with db.connect() as conn:
        conn.execute(f"PRAGMA journal_mode = {journal_mode}")
        conn.execute("UPDATE profile_cache SET profile_json = ?", (marker,))
    assert marker.encode() in db.db_path().read_bytes()
    assert request_reset(client, "search").status_code == 200
    assert marker.encode() not in db.db_path().read_bytes()
    assert not db.db_path().with_name(db.DB_FILENAME + "-journal").exists()
    assert not db.db_path().with_name(db.DB_FILENAME + "-wal").exists()


def test_full_reset_closes_and_recreates_its_log_on_windows_too(client, populated):
    setup_logging()
    try:
        assert request_reset(client, "all").status_code == 200
        assert (populated / "logs" / "jobcu.log").read_text(encoding="utf-8") == ""
        assert not (populated / "logs" / "jobcu.log.1").exists()
    finally:
        reset._close_log_files(populated)


def test_full_reset_unlinks_links_without_deleting_external_originals(client, populated):
    outside = populated.parent / "originals"
    outside.mkdir()
    (outside / "original.txt").write_text("Original nursing CV", encoding="utf-8")
    try:
        (populated / "linked-originals").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("This Windows account cannot create symbolic links.")
    assert request_reset(client, "all").status_code == 200
    assert (outside / "original.txt").read_text(encoding="utf-8") == "Original nursing CV"
    assert not (populated / "linked-originals").exists()


def test_reset_blocks_concurrent_writes_but_health_stays_available(client, populated, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    clear = reset.clear_data

    def held(scope):
        assert not search.manager._lock.acquire(blocking=False)
        entered.set()
        assert release.wait(5)
        return clear(scope)

    monkeypatch.setattr(reset, "clear_data", held)
    with ThreadPoolExecutor() as executor:
        pending = executor.submit(request_reset, client, "all")
        try:
            assert entered.wait(5)
            assert client.put("/api/settings/ai", headers=HEADERS, json={
                "provider": None, "model": "changed"}).status_code == 409
            assert client.post("/api/search", headers=HEADERS,
                               json=SearchForm().model_dump()).status_code == 409
            assert client.get("/api/health").status_code == 200
        finally:
            release.set()
        assert pending.result().status_code == 200
    assert load_settings().ai.model == "fictional-model"


def test_inflight_action_blocks_reset_without_cancelling_it(populated):
    app = create_app()
    entered, release = threading.Event(), threading.Event()

    @app.post("/api/held-action")
    def held():
        entered.set()
        assert release.wait(5)
        return {"done": True}

    with TestClient(app, base_url="http://127.0.0.1:8765") as client, ThreadPoolExecutor() as pool:
        pending = pool.submit(client.post, "/api/held-action", headers=HEADERS)
        try:
            assert entered.wait(5)
            assert request_reset(client, "all").status_code == 409
            assert count("jobs") == 1
        finally:
            release.set()
        assert pending.result().json() == {"done": True}
    assert request_reset(client, "review").status_code == 200
