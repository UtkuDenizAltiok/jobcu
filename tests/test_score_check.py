"""Rescoring preserves evidence completeness and the original search criteria."""

import importlib.util
from pathlib import Path

from jobcu import quality
from jobcu.location import LocationPlan

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("score_check", ROOT / "tools" / "score_check.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def ad(ad_id=1, **extra):
    return quality.Ad(id=ad_id, kind="scored", title="PRIVATE_MARKER", company="PRIVATE_MARKER",
                      location="PRIVATE_MARKER", url="https://example.test/1", score=95,
                      text="PRIVATE_MARKER", **extra)


def test_saved_summaries_do_not_become_full_ads_on_rescore():
    assert not tool.as_job(ad(description_is_complete=False)).description_is_complete
    assert tool.as_job(ad()).description_is_complete


def test_rescore_uses_recorded_location_plans_and_aggregate_output(monkeypatch, capsys):
    monkeypatch.setattr(tool, "AIClient", lambda *args, **kwargs: object())
    monkeypatch.setattr(tool.documents, "read_text", lambda kind: "fake document")
    monkeypatch.setattr(tool, "read_profile_reusing", lambda *args: (object(), True))
    calls = []

    def score(client, profile, plan, groups, indexes, batch_size):
        calls.append((plan.understood_as, groups[indexes[0]].best_description_copy
                      .description_is_complete))
        return {i: {"score": 80} for i in indexes}

    monkeypatch.setattr(tool, "score_groups", score)
    plan = LocationPlan(text="", understood_as="Fictional preferences", countries=["DE"],
                        places=[], not_checked_yet=[], outside_supported_area=[], broad=False)
    ads = [ad(location_plan=plan.model_dump(), description_is_complete=False), ad(2)]
    assert tool.rescore(ads, 4, "medium", False, aggregate=True) == {1: 80, 2: 80}
    assert calls == [("Fictional preferences", False), ("Anywhere.", True)]
    assert "PRIVATE_MARKER" not in capsys.readouterr().out


def test_aggregate_report_omits_titles_companies_and_notes(capsys):
    tool.report([ad(rating="poor", description_is_complete=False)], {1: 95}, aggregate=True)
    text = capsys.readouterr().out
    assert "PRIVATE_MARKER" not in text
    assert "saved as summaries" in text and "0 of 1" in text
