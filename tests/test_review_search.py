"""Local review metrics must be useful without revealing user text or changing their database."""

import importlib.util
import json
from pathlib import Path

import pytest

from jobcu import db

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review_search", ROOT / "tools" / "review_search.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def card(score=90, url="https://example.test/1", **extra):
    return {"score": score, "title": "PRIVATE_MARKER", "country": "DE",
            "main_link": {"url": url}, "also_on": [], **extra}


def snapshot(cards=None):
    return {"status": "finished", "form": {"location_text": "PRIVATE_MARKER"},
            "steps": [{"id": "scoring", "label": "PRIVATE_MARKER", "elapsed_seconds": 15}],
            "waiting_seconds": 5, "notes": ["PRIVATE_MARKER"], "result": {
                "profile": {"summary": "PRIVATE_MARKER"}, "location": {"conditions": [
                    {"text": "PRIVATE_MARKER", "status": "not_checked"}]},
                "usage": {"scoring": {"input_tokens": 100, "output_tokens": 20},
                          "PRIVATE_MARKER": {"input_tokens": 5}},
                "jobs": {"cards": cards if cards is not None else [card(summary_only=True)],
                         "date_unknown": [card(80, country="IE")],
                         "sources": [{"source": "adzuna", "name": "PRIVATE_MARKER",
                                      "message": "PRIVATE_MARKER", "status": "unavailable"},
                                     {"source": "PRIVATE_MARKER", "status": "failed"}],
                         "counts": {"ads_found": 20, "different_jobs": 15, "unrelated": 10}}}}


def test_report_excludes_all_free_text_and_exposes_uncertainty():
    report = tool.review(snapshot(), [])
    assert "PRIVATE_MARKER" not in json.dumps(report)
    assert report["jobs"]["shown"] == 2 and report["jobs"]["summary_share"] == .5
    assert report["jobs"]["by_country"] == {"DE": 1, "IE": 1}
    assert report["jobs"]["date_unknown"] == 1
    assert report["jobs"]["top_10_summaries"] == 1
    assert report["conditions"]["not_checked"] == 1
    assert report["seconds_by_step"] == {"scoring": 15}
    assert report["waiting_seconds"] == 5
    assert report["usage_by_step"]["other"]["input_tokens"] == 5
    assert report["coverage_recall"] is None and report["top_10_quality"]["precision_good"] is None
    assert len(report["sources"]) == 1


def test_precision_requires_every_top_card_and_conflicting_ratings_count_as_unjudged():
    cards = [card(95), card(80, url="https://example.test/2")]
    rated = [{"kind": "scored", "url": "https://example.test/1", "rating": "good"}]
    assert tool.review(snapshot(cards), rated)["top_10_quality"]["precision_good"] is None
    rated.append({"kind": "scored", "url": "https://example.test/2", "rating": "poor"})
    assert tool.review(snapshot(cards), rated)["top_10_quality"]["precision_good"] == .5
    cards[0]["also_on"] = [{"url": "https://example.test/2"}]
    quality = tool.review(snapshot(cards), rated)["top_10_quality"]
    assert quality["precision_good"] is None and quality["not_rated"] == 1
    cards[0]["also_on"] = []
    rated.append({"kind": "scored", "url": "https://example.test/1", "rating": "poor"})
    quality = tool.review(snapshot(cards), rated)["top_10_quality"]
    assert quality["precision_good"] is None and quality["not_rated"] == 1


def test_empty_and_legacy_results_do_not_invent_quality_or_timing():
    report = tool.review({"status": "stopped", "result": {}}, [])
    assert report["jobs"]["shown"] == 0 and report["jobs"]["summary_share"] is None
    assert report["seconds_by_step"] == {}
    assert report["waiting_seconds"] is None
    assert report["top_10_quality"]["precision_good"] is None
    assert any("did not finish" in c for c in report["checks_needed"])
    assert report["career_titles"] is None


def test_career_title_report_allows_counts_but_never_rejected_jobs_or_notes():
    saved = snapshot([])
    saved["result"]["career_titles"] = {
        "total": 4, "reviewed": 3, "unrelated": 2, "unreviewed": 1,
        "failed_batches": 1, "unrelated_ads": 3,
        "left_out": [{"title": "PRIVATE FICTIONAL TITLE", "company": "PRIVATE COMPANY",
                      "url": "https://private.example.test/ad"}],
        "note": "PRIVATE NOTE",
    }
    report = tool.review(saved, [])
    assert report["career_titles"] == {k: saved["result"]["career_titles"][k] for k in
                                        ("total", "reviewed", "unrelated", "unreviewed",
                                         "failed_batches", "unrelated_ads")}
    assert "PRIVATE" not in json.dumps(report)


@pytest.mark.parametrize("kind,timing_scope,usage_scope", [
    ("search", "original_search", "original_search"),
    ("reapply", "latest_correction", "search_and_all_corrections"),
    (None, "unknown", "unknown"),
    ("PRIVATE_MARKER", "unknown", "unknown"),
])
def test_performance_scopes_are_explicit_and_unknown_kinds_stay_private(
        kind, timing_scope, usage_scope):
    saved = snapshot()
    if kind is not None:
        saved["kind"] = kind
    report = tool.review(saved, [])
    assert report["kind"] == (kind if kind in {"search", "reapply"} else "unknown")
    assert report["timing_scope"] == timing_scope
    assert report["usage_scope"] == usage_scope
    assert "PRIVATE_MARKER" not in json.dumps(report)
    if kind == "reapply":
        assert any("original search and all corrections" in c for c in report["checks_needed"])
    elif timing_scope == "unknown":
        assert any("scopes are unknown" in c for c in report["checks_needed"])
    else:
        assert not any("corrections" in c for c in report["checks_needed"])


def test_saved_correction_keeps_its_timings_and_cumulative_usage_separate(temporary_data_dir):
    saved = snapshot()
    saved["kind"] = "reapply"
    saved["steps"] = [{"id": "conditions", "elapsed_seconds": 2},
                      {"id": "scoring", "elapsed_seconds": 0}]
    saved["waiting_seconds"] = 1
    # The original search spent these tokens; the correction did not score any ads.
    saved["result"]["usage"] = {"scoring": {"input_tokens": 100, "output_tokens": 20}}
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (1, 'finished', '{}')")
        conn.execute("INSERT INTO search_results VALUES (1, ?)", (json.dumps(saved),))
    path = temporary_data_dir / db.DB_FILENAME
    before = path.read_bytes()
    saved, ads = tool.read_saved(temporary_data_dir)
    report = tool.review(saved, ads)
    assert path.read_bytes() == before
    assert report["kind"] == "reapply"
    assert report["timing_scope"] == "latest_correction"
    assert report["seconds_by_step"] == {"conditions": 2, "scoring": 0}
    assert report["waiting_seconds"] == 1
    assert report["usage_scope"] == "search_and_all_corrections"
    assert report["usage_by_step"]["scoring"]["input_tokens"] == 100


def test_review_never_creates_missing_data(temporary_data_dir, capsys):
    assert tool.read_saved(temporary_data_dir) == (None, [])
    assert tool.main(["--data-dir", str(temporary_data_dir)]) == 0
    assert "No saved search" in capsys.readouterr().out
    assert not temporary_data_dir.exists()


def test_sqlite_is_read_only_and_older_results_are_identified(temporary_data_dir):
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (1, 'finished', '{}')")
        conn.execute("INSERT INTO search_results VALUES (1, ?)", (json.dumps(snapshot()),))
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (2, 'failed', '{}')")
    path = temporary_data_dir / db.DB_FILENAME
    before = path.read_bytes()
    saved, ads = tool.read_saved(temporary_data_dir)
    report = tool.review(saved, ads)
    assert path.read_bytes() == before
    assert report["is_latest_attempt"] is False and report["latest_attempt_status"] == "failed"
    assert any("older saved" in c for c in report["checks_needed"])
