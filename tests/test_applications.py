import json
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from jobcu import applications, db, jobstore, search
from jobcu.app import create_app
from jobcu.dedupe import JobGroup
from jobcu.sources.base import FoundJob

CV_LINK = "https://www.cv-library.co.uk/job/fictional-1"
EMPLOYER_LINK = "https://careers.example.test/jobs/fictional-1"
OPAQUE_LINK = "https://www.adzuna.co.uk/jobs/land/ad/fictional-1"
HEADERS = {"X-Jobcu": "1"}


@pytest.mark.parametrize(("url", "expected"), [
    (CV_LINK, True),
    ("https://apply.cv-library.co.uk/fictional", True),
    ("https://CV-LIBRARY.CO.UK.:443/fictional", True),
    ("https://tracker.example.test/go?url=" + quote(CV_LINK, safe=""), True),
    ("https://tracker.example.test/go?target=" + quote(
        "https://other.example.test/go?url=" + quote(CV_LINK, safe=""), safe=""), True),
    ("https://cv-library.co.uk.example.test/fictional", False),
    ("https://example.test/?note=" + quote(CV_LINK, safe=""), False),
    ("https://www.adzuna.co.uk/jobs/land/ad/fictional-1", False),
    ("https://[invalid", False),
])
def test_destination_exclusion_uses_host_boundaries_and_exposed_redirects(url, expected):
    assert applications.blocked(url) is expected


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse"])
def test_same_vacancy_keeps_employer_alternative_and_never_offers_cvlibrary(title):
    group = JobGroup([
        FoundJob("board", "fictional-1", CV_LINK, title, company="Example Ltd",
                 employer_url=CV_LINK, description="Full fictional ad",
                 description_is_complete=True),
        FoundJob("other", "fictional-1", "https://board.example.test/fictional-1", title,
                 company="Example Ltd", employer_url=EMPLOYER_LINK),
    ], source_kinds={"board": "job_board", "other": "aggregator"})
    assert not applications.unavailable(group)
    main, other = applications.links(group, {"other": "Other board"})
    assert main == {"source": "Employer's site", "url": EMPLOYER_LINK}
    assert other == [{"source": "Other board", "url": "https://board.example.test/fictional-1"}]
    assert group.best_description_copy.description == "Full fictional ad"


def test_board_alternative_is_used_and_blocked_only_vacancy_is_unavailable():
    group = JobGroup([FoundJob("board", "fictional-1", CV_LINK, "Chef")])
    assert applications.unavailable(group)
    group.copies.append(FoundJob("other", "fictional-1", EMPLOYER_LINK, "Chef"))
    assert not applications.unavailable(group)
    assert applications.links(group, {}) == ({"source": "other", "url": EMPLOYER_LINK}, [])


def test_opaque_aggregator_is_not_a_proven_alternative_to_known_cvlibrary():
    group = JobGroup([
        FoundJob("board", "fictional-1", CV_LINK, "Chef"),
        FoundJob("adzuna", "fictional-1", "https://www.adzuna.co.uk/jobs/land/ad/fictional-1",
                 "Chef"),
    ])
    assert applications.unavailable(group)
    card = {"main_link": {"source": "CV-Library", "url": CV_LINK},
            "also_on": [{"source": "Adzuna", "url": group.copies[1].url}]}
    assert applications.clean_card(card)["application_link_unavailable"]


def test_unknown_redirect_is_labelled_without_claiming_its_host_is_blocked():
    card = {"main_link": {"source": "Adzuna",
                          "url": "https://www.adzuna.co.uk/jobs/land/ad/fictional-1"},
            "also_on": []}
    cleaned = applications.clean_card(card)
    assert cleaned["main_link"] == card["main_link"]
    assert cleaned["application_destination_unverified"]
    assert not cleaned["application_link_unavailable"]


def test_restored_recommendations_remove_blocked_routes_without_rewriting_history(monkeypatch):
    snapshot = {
        "id": 1, "status": "finished", "notes": [], "result": {"jobs": {
            "cards": [
                {"job_id": 1, "title": "Engineer", "score": 95, "is_new": True,
                 "main_link": {"source": "Board", "url": CV_LINK}, "also_on": []},
                {"job_id": 2, "title": "Nurse", "score": 90, "is_new": False,
                 "main_link": {"source": "Board", "url": CV_LINK},
                 "also_on": [{"source": "Employer", "url": EMPLOYER_LINK}]},
            ], "date_unknown": [], "hidden": [], "new_count": 1,
            "counts": {"shown": 2, "left_out": []},
        }},
    }
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (1, 'finished', '{}')")
    original = json.dumps(snapshot)
    jobstore.finish_search(1, "finished", original)
    monkeypatch.setattr(search, "manager", search.SearchManager())
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    jobs = client.get("/api/search/current").json()["search"]["result"]["jobs"]
    assert [c["job_id"] for c in jobs["cards"]] == [2]
    assert jobs["cards"][0]["score"] == 90
    assert jobs["cards"][0]["main_link"]["url"] == EMPLOYER_LINK
    assert jobs["counts"]["shown"] == 1 and jobs["new_count"] == 0
    assert jobs["counts"]["left_out"] == [{"reason": applications.EXCLUSION_REASON, "count": 1}]
    assert jobstore.latest_results()[1] == original


def test_saved_application_history_keeps_state_and_disables_blocked_link(monkeypatch):
    card = {"job_id": 1, "title": "Chef", "score": 95,
            "state": {"saved": True, "applied": False, "dismissed": False},
            "main_link": {"source": "Board", "url": CV_LINK}, "also_on": []}
    monkeypatch.setattr(jobstore, "marked_cards", lambda kind: [card])
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    shown = client.get("/api/jobs/marked/saved").json()["cards"][0]
    assert shown["state"] == card["state"] and shown["score"] == 95
    assert not shown["main_link"]["url"] and shown["application_link_unavailable"]
    assert card["main_link"]["url"] == CV_LINK


def saved_card(title="Power Electronics Engineer", url=OPAQUE_LINK, also_on=None):
    group = JobGroup([FoundJob("board", "fictional-1", url, title, company="Example Ltd")])
    with db.connect() as conn:
        search_id = conn.execute(
            "INSERT INTO searches (status, form_json) VALUES ('running', '{}')"
        ).lastrowid
    (job_id,), _ = jobstore.remember([group], search_id)
    card = {"job_id": job_id, "title": title, "score": 93, "is_new": True,
            "state": {"saved": True, "applied": True, "dismissed": False},
            "main_link": {"source": "Board", "url": url}, "also_on": also_on or []}
    jobstore.save_cards([card])
    jobstore.set_state(job_id, saved=True, applied=True)
    snapshot = {"id": search_id, "status": "finished", "notes": [], "result": {"jobs": {
        "cards": [card], "date_unknown": [], "hidden": [], "new_count": 1,
        "counts": {"shown": 1, "left_out": []},
    }}}
    original = json.dumps(snapshot)
    jobstore.finish_search(search_id, "finished", original)
    return group, card, original


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_reported_opaque_route_survives_restart_and_undo_preserves_history(monkeypatch, title):
    group, card, original = saved_card(title)
    monkeypatch.setattr(search, "manager", search.SearchManager())
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    path = f"/api/jobs/{card['job_id']}/application-link"
    response = client.post(path, json={"url": OPAQUE_LINK}, headers=HEADERS)
    assert response.json() == {"excluded": True}
    # A second report is idempotent; a fresh app/manager reads the persisted choice.
    assert client.post(path, json={"url": OPAQUE_LINK}, headers=HEADERS).status_code == 200
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    assert applications.unavailable(group)
    jobs = client.get("/api/search/current").json()["search"]["result"]["jobs"]
    assert jobs["cards"] == [] and jobs["new_count"] == 0
    assert jobs["counts"] == {"shown": 0, "left_out": [
        {"reason": applications.REPORTED_EXCLUSION_REASON, "count": 1}]}
    for kind in ("saved", "applied"):
        (shown,) = client.get(f"/api/jobs/marked/{kind}").json()["cards"]
        assert shown["application_link_unavailable"] and not shown["main_link"]["url"]
        assert shown["score"] == card["score"] and shown["state"] == card["state"]
    (report,) = client.get("/api/applications/excluded").json()["links"]
    assert report["title"] == title and report["url"] == OPAQUE_LINK
    response = client.delete(f"/api/applications/excluded/{report['id']}", headers=HEADERS)
    assert response.status_code == 200
    assert applications.reports() == [] and not applications.unavailable(group)
    restored = client.get("/api/search/current").json()["search"]["result"]["jobs"]
    assert restored["cards"][0]["main_link"]["url"] == OPAQUE_LINK
    assert restored["cards"][0]["score"] == 93
    assert jobstore.latest_results()[1] == original
    with db.connect() as conn:
        stored_card = json.loads(conn.execute("SELECT card_json FROM job_cards").fetchone()[0])
    assert stored_card == card


def test_reporting_chooses_same_vacancy_alternative_and_preserves_unknown_jobs():
    group, card, _ = saved_card(also_on=[{"source": "Employer", "url": EMPLOYER_LINK}])
    applications.report_link(card["job_id"], OPAQUE_LINK)
    cleaned = applications.clean_card(card)
    assert cleaned["main_link"]["url"] == EMPLOYER_LINK and cleaned["score"] == 93
    assert not cleaned["application_link_unavailable"]
    group.copies.append(FoundJob("employer", "fictional-1", EMPLOYER_LINK, group.main.title))
    assert applications.links(group, {})[0]["url"] == EMPLOYER_LINK
    other = JobGroup([FoundJob("board", "fictional-2", OPAQUE_LINK + "-other", group.main.title,
                              company=group.main.company)])
    assert not applications.unavailable(other)
    assert applications.links(other, {})[0]["url"] == OPAQUE_LINK + "-other"
    assert applications.clean_card({"main_link": {"url": OPAQUE_LINK + "-other"}})[
        "application_destination_unverified"]


def test_another_opaque_redirect_does_not_prove_an_alternative_to_a_reported_route():
    group, card, _ = saved_card()
    applications.report_link(card["job_id"], OPAQUE_LINK)
    group.copies.append(FoundJob("other", "fictional-2", OPAQUE_LINK + "-other", "Engineer"))
    assert applications.unavailable(group)


def test_only_saved_links_can_be_reported_and_local_header_is_required():
    _, card, _ = saved_card()
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    path = f"/api/jobs/{card['job_id']}/application-link"
    assert client.post(path, json={"url": OPAQUE_LINK}).status_code == 403
    assert client.post(path, json={"url": OPAQUE_LINK}, headers={
        **HEADERS, "Origin": "https://elsewhere.example.test"}).status_code == 403
    assert client.post(path, json={"url": EMPLOYER_LINK}, headers=HEADERS).status_code == 400
    assert client.post(path, json={"url": "javascript:void(0)"}, headers=HEADERS).status_code == 400
    assert client.post("/api/jobs/9999/application-link", json={"url": OPAQUE_LINK},
                       headers=HEADERS).status_code == 404
    assert applications.reports() == []
    client.post(path, json={"url": OPAQUE_LINK}, headers=HEADERS)
    (report,) = applications.reports()
    undo = f"/api/applications/excluded/{report['id']}"
    assert client.delete(undo).status_code == 403
    assert client.delete(undo, headers=HEADERS).status_code == 200
    assert client.delete(undo, headers=HEADERS).status_code == 404


def test_a_click_opens_only_saved_links_and_needs_no_page_header(monkeypatch):
    _, card, _ = saved_card(url="https://board.example.org/jobs/1", also_on=[
        {"source": "Other", "url": "https://other.example.org/2"}])
    monkeypatch.setattr("jobcu.applylink.destination",
                        lambda url: f"https://careers.example.com/?{url[-1]}")
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")

    def opened(job_id, url):
        return client.get(f"/api/jobs/{job_id}/open?url={quote(url, safe='')}",
                          follow_redirects=False)

    for url, ending in (("https://board.example.org/jobs/1", "1"),
                        ("https://other.example.org/2", "2")):
        reply = opened(card["job_id"], url)
        assert reply.status_code == 302 and reply.headers["cache-control"] == "no-store"
        assert reply.headers["location"] == f"https://careers.example.com/?{ending}"
    # Never a way to send someone anywhere else.
    assert opened(card["job_id"], "https://evil.example.net/").status_code == 400
    assert opened(card["job_id"], "javascript:alert(1)").status_code == 400
    assert opened(9999, "https://board.example.org/jobs/1").status_code == 404


def test_failed_report_rolls_back_without_affecting_saved_results():
    import sqlite3

    _, card, original = saved_card()
    with db.connect() as conn:
        conn.execute("""
            CREATE TRIGGER fail_link_report BEFORE INSERT ON application_link_reports
            BEGIN SELECT RAISE(FAIL, 'Simulated storage failure'); END;
        """)
    with pytest.raises(sqlite3.IntegrityError, match="Simulated storage failure"):
        applications.report_link(card["job_id"], OPAQUE_LINK)
    assert applications.reports() == [] and jobstore.latest_results()[1] == original


def test_stale_undo_cannot_remove_a_different_new_report():
    _, card, _ = saved_card(also_on=[{"source": "Employer", "url": EMPLOYER_LINK}])
    applications.report_link(card["job_id"], OPAQUE_LINK)
    old_id = applications.reports()[0]["id"]
    applications.undo_report(old_id)
    applications.report_link(card["job_id"], EMPLOYER_LINK)
    with pytest.raises(KeyError):
        applications.undo_report(old_id)
    assert applications.reported_urls() == {EMPLOYER_LINK}


@pytest.mark.parametrize("path", ["details", "land/ad", "jobs/details", "jobs/land/ad"])
@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse"])
def test_unusable_advertisement_report_survives_tracking_changes_but_undo_restores(path, title):
    first = "https://www.adzuna.co.uk/jobs/land/ad/123?se=old&v=old&utm_source=first"
    changed = f"https://adzuna.co.uk/{path}/123?se=new&v=new&utm_source=second"
    group, card, original = saved_card(title, first)
    applications.report_link(card["job_id"], first)
    group.copies[0].url = changed
    current = {**card, "main_link": {"source": "Board", "url": changed}}
    assert applications.unavailable(group)
    assert applications.clean_card(current)["application_link_unavailable"]
    assert applications.clean_card(current)["application_link_reported"]
    (report,) = applications.reports()
    applications.undo_report(report["id"])
    assert not applications.unavailable(group)
    assert applications.clean_card(current)["main_link"]["url"] == changed
    assert jobstore.latest_results()[1] == original


@pytest.mark.parametrize("other", [
    "https://www.adzuna.co.uk/jobs/details/124?utm_source=new",
    "https://www.adzuna.de/details/123?utm_source=new",
    "https://www.adzuna.co.uk/jobs/details/123?destination=different",
    "https://www.adzuna.co.uk:8443/jobs/details/123",
    "https://www.adzuna.co.uk/jobs/details/fictional-123",
    "https://board.example.test/jobs/details/123",
])
def test_unverified_advertisement_alias_never_becomes_a_reported_destination(other):
    first = "https://www.adzuna.co.uk/jobs/details/123?utm_source=old"
    cleaned = applications.clean_card({"main_link": {"url": other}}, {first})
    assert not cleaned["application_link_unavailable"]
    assert not cleaned["application_link_reported"]
    assert cleaned["main_link"]["url"] == other


def test_tracking_alias_exclusion_keeps_an_independent_employer_link_and_exact_urls():
    first = "https://www.adzuna.co.uk/jobs/details/123?utm_source=first"
    changed = "https://www.adzuna.co.uk/jobs/land/ad/123?utm_source=second&se=new"
    group, card, _ = saved_card(url=first)
    applications.report_link(card["job_id"], first)
    group.copies[0].url = changed
    group.copies.append(FoundJob("employer", "fictional-1", EMPLOYER_LINK, group.main.title))
    assert not applications.unavailable(group)
    assert applications.links(group, {})[0]["url"] == EMPLOYER_LINK
    cleaned = applications.clean_card({**card, "main_link": {"url": changed},
                                      "also_on": [{"url": EMPLOYER_LINK}]})
    assert cleaned["main_link"]["url"] == EMPLOYER_LINK and cleaned["score"] == card["score"]
    assert group.copies[0].url == changed  # provider advertiser URL is never normalized away


@pytest.mark.parametrize("title", ["Power Design Engineer", "Ward Nurse", "Primary Teacher",
                                   "Pastry Chef"])
def test_saved_independent_employer_link_becomes_primary_without_resolving_adzuna(title):
    _, card, original = saved_card(title)
    card["also_on"] = [{"source": "Employer's site", "url": EMPLOYER_LINK}]
    before = json.dumps(card)
    shown = applications.clean_card(card)
    assert shown["main_link"] == card["also_on"][0]
    assert shown["also_on"] == [card["main_link"]]
    assert not shown["application_destination_unverified"]
    assert shown["score"] == card["score"]
    assert json.dumps(card) == before and jobstore.latest_results()[1] == original
    assert applications.clean_card(shown) == shown  # repeated display is stable


@pytest.mark.parametrize("alternative", [
    {"source": "Employer's site", "url": CV_LINK},
    {"source": "Employer's site", "url": OPAQUE_LINK + "-other"},
    {"source": "Another board", "url": EMPLOYER_LINK},
])
def test_unproven_or_blocked_alternative_does_not_claim_a_direct_employer_route(alternative):
    card = {"main_link": {"source": "Adzuna", "url": OPAQUE_LINK},
            "also_on": [alternative]}
    shown = applications.clean_card(card, set())
    if alternative["url"] == CV_LINK:
        assert shown["application_link_unavailable"]
    else:
        assert shown["main_link"] == card["main_link"]
        assert shown["application_destination_unverified"]


def test_reported_independent_employer_route_is_never_promoted_over_adzuna():
    card = {"main_link": {"source": "Adzuna", "url": OPAQUE_LINK},
            "also_on": [{"source": "Employer's site", "url": EMPLOYER_LINK}]}
    shown = applications.clean_card(card, {EMPLOYER_LINK})
    assert shown["application_link_unavailable"]
    assert not shown["main_link"]["url"]
