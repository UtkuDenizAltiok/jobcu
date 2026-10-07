"""The score check: ads kept from real searches and what the person thinks of them."""

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from jobcu import db, quality
from jobcu.app import create_app

HEADERS = {"X-Jobcu": "1"}


@pytest.fixture
def client():
    return TestClient(create_app(), base_url="http://127.0.0.1:8765")


def ad(job_id, score=None, title="Hardware Engineer", text="The whole ad"):
    return {"source": "greenhouse", "source_job_id": job_id, "title": title,
            "company": "Fake Devices", "location": "Dublin, Ireland",
            "url": f"https://example.test/{job_id}", "score": score, "text": text}


def test_a_search_keeps_a_spread_of_its_jobs_and_left_out_titles():
    scored = [ad(str(i), score=score) for i, score in enumerate([95, 88, 70, 65, 55, 50, 30, 20])]
    titles = [ad(f"t{i}", title="Servicetechniker") for i in range(3)]
    added = quality.collect_from_search(scored, titles)
    assert added == {"scored": 8, "title_only": 3}
    kept = quality.all_ads()
    assert {a.score for a in kept if a.kind == "scored"} == {95, 88, 70, 65, 55, 50, 30, 20}
    assert quality.progress()["scored"] == {"wanted": 50, "collected": 8, "rated": 0}

    # The same jobs in the next search aren't kept twice.
    assert quality.collect_from_search(scored, titles) == {"scored": 0, "title_only": 0}


def test_only_a_few_jobs_per_search_and_never_more_than_wanted():
    many = [ad(str(i), score=i) for i in range(100)]
    assert quality.collect_from_search(many, [])["scored"] == quality.PER_SEARCH["scored"]
    # Jobs are taken from every part of the score range, not just the top.
    scores = sorted(a.score for a in quality.all_ads())
    assert scores[0] < 40 and scores[-1] > 74


def test_repeated_samples_do_not_hide_new_jobs_and_duplicate_inserts_do_not_use_room():
    initial = [ad(str(i), score=80) for i in range(49)]
    assert quality.add("scored", initial) == 49
    assert quality.add("scored", [initial[0], ad("new", score=95)]) == 1
    assert any(a.title == "Hardware Engineer" and a.score == 95 for a in quality.all_ads())


def test_a_search_samples_new_items_even_when_the_first_choices_were_seen_before():
    old = [ad(str(i), score=80) for i in range(8)]
    quality.collect_from_search(old, [])
    assert quality.collect_from_search([*old, ad("new", score=95)], [])["scored"] == 1


def test_sampling_covers_full_ads_and_top_summaries_and_keeps_their_context(client):
    full = ad("full", score=80)
    summary = {**ad("summary", score=95, text="Only a summary"),
               "description_is_complete": False, "location_plan": {"text": "Fake criteria"}}
    quality.collect_from_search([full, summary], [])
    data = client.get("/api/quality", headers=HEADERS).json()["ads"]
    assert len(data) == 2
    saved = next(a for a in data if a["score"] == 95)
    assert saved["description_is_complete"] is False
    assert saved["location_plan"] == {"text": "Fake criteria"}


def test_rating_an_ad_and_taking_it_back(client):
    quality.collect_from_search([ad("1", score=80)], [ad("t1", title="Cleaner")])
    data = client.get("/api/quality", headers=HEADERS).json()
    scored_ad = next(a for a in data["ads"] if a["kind"] == "scored")
    assert scored_ad["rating"] is None and scored_ad["score"] == 80
    assert {b["id"] for b in data["blockers"]} == set(quality.BLOCKERS)

    answer = client.put(f"/api/quality/{scored_ad['id']}", headers=HEADERS,
                        json={"rating": "poor", "blockers": ["language", "nonsense"],
                              "note": "German C1"}).json()
    assert answer["ad"]["rating"] == "poor" and answer["ad"]["blockers"] == ["language"]
    assert answer["ad"]["rated_by"] == "owner" and answer["progress"]["scored"]["rated"] == 1

    answer = client.put(f"/api/quality/{scored_ad['id']}", headers=HEADERS,
                        json={"rating": None, "blockers": [], "note": ""}).json()
    assert answer["ad"]["rating"] is None and answer["progress"]["scored"]["rated"] == 0


def test_titles_have_their_own_answers(client):
    quality.collect_from_search([], [ad("t1", title="Cleaner")])
    title_ad = next(a for a in client.get("/api/quality", headers=HEADERS).json()["ads"]
                    if a["kind"] == "title_only")
    ok = client.put(f"/api/quality/{title_ad['id']}", headers=HEADERS,
                    json={"rating": "worth_a_look"})
    assert ok.json()["ad"]["rating"] == "worth_a_look"
    # A rating from the wrong list is refused, as is an unknown job.
    assert client.put(f"/api/quality/{title_ad['id']}", headers=HEADERS,
                      json={"rating": "good"}).status_code == 400
    assert client.put("/api/quality/999", headers=HEADERS,
                      json={"rating": "good"}).status_code == 404


@pytest.mark.parametrize("legacy", [False, True])
def test_assistant_review_preserves_owner_and_legacy_labels(legacy):
    quality.add("scored", [ad("one", score=80)])
    ad_id = quality.all_ads()[0].id
    owner = quality.rate(ad_id, "good", ["field"], "Owner's own assessment")
    if legacy:
        with db.connect() as conn:
            conn.execute("UPDATE quality_ads SET rated_by = NULL WHERE id = ?", (ad_id,))
        owner = quality.all_ads()[0]
    for rating in ("poor", None):
        actual = quality.rate(ad_id, rating, ["seniority"], "Assistant review", by="assistant")
        assert actual == owner


def test_assistant_can_rate_empty_ads_and_revise_its_own_labels():
    quality.add("scored", [ad("one", score=80)])
    ad_id = quality.all_ads()[0].id
    first = quality.rate(ad_id, "okay", [], "Evidence checked", by="assistant")
    assert first.rating == "okay" and first.rated_by == "assistant"
    second = quality.rate(ad_id, "poor", ["seniority"], "Further evidence", by="assistant")
    assert second.rating == "poor" and second.rated_by == "assistant"
    owner = quality.rate(ad_id, "good", [], "Owner's judgement")
    assert owner.rating == "good" and owner.rated_by == "owner"


def test_owner_edit_between_assistant_read_and_write_survives(monkeypatch):
    quality.add("scored", [ad("one", score=80)])
    ad_id = quality.all_ads()[0].id
    connect = db.connect
    pending = True

    class Cursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def fetchone(self):
            row = self.cursor.fetchone()
            self.cursor.fetchall()  # finish the read before the separate owner transaction
            quality.rate(ad_id, "good", ["field"], "Owner edit during review")
            return row

    class Connection:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, sql, params=()):
            nonlocal pending
            cursor = self.conn.execute(sql, params)
            if pending and sql.startswith("SELECT kind FROM quality_ads WHERE id"):
                pending = False
                return Cursor(cursor)
            return cursor

    @contextmanager
    def controlled_connect(*args, **kwargs):
        with connect(*args, **kwargs) as conn:
            yield Connection(conn)

    monkeypatch.setattr(db, "connect", controlled_connect)
    actual = quality.rate(ad_id, "poor", ["seniority"], "Assistant review", by="assistant")
    assert actual.rating == "good" and actual.rated_by == "owner"
    assert actual.note == "Owner edit during review" and actual.blockers == ["field"]
