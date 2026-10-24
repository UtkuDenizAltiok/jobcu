"""The provider comparison tool reads captures and scores saved ads without real traffic."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compare_providers",
                                              ROOT / "tools" / "compare_providers.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def run(model, scores):
    return {"model": model, "seconds": 1, "ads": {
        str(i): {"title": f"Fictional job {i}", "score": score, "parts": {}, "reasons": [],
                 "limits": []} for i, score in enumerate(scores)}}


def test_research_requests_are_paired_with_the_structuring_that_quotes_their_notes(tmp_path):
    events = [
        {"kind": "ai_start", "attempt": "a", "step": "job_places", "operation": "research",
         "arguments": {"system": "s", "prompt": "Jobs: J0", "max_searches": 2}},
        {"kind": "ai_end", "attempt": "a", "reply": {"text": "Fictional notes", "sources": []}},
        {"kind": "ai_start", "attempt": "b", "step": "job_places", "operation": "complete_json",
         "arguments": {"schema_name": "OnlineAnswer",
                       "prompt": "Person\n\nResearch notes:\nFictional notes"}},
        {"kind": "ai_end", "attempt": "b", "reply": {"text": "{}"}},
        {"kind": "ai_start", "attempt": "c", "step": "scoring", "operation": "complete_json",
         "arguments": {"schema_name": "ScoringAnswer", "prompt": "JOB J1"}},
        {"kind": "ai_end", "attempt": "c", "reply": {"text": "{}"}},
    ]
    (tmp_path / "events.jsonl").write_text("\n".join(map(json.dumps, events)), encoding="utf-8")
    items = tool.items_from(tool.load_calls(tmp_path))
    assert [(item.kind, len(item.calls)) for item in items] == [
        ("research:OnlineAnswer", 2), ("ScoringAnswer", 1)]


def test_saved_ad_runs_are_compared_with_ranges_and_each_other(capsys):
    labels = {"0": [70, 90], "1": [40, 60], "2": [10, 30]}
    tool.show_saved_ads([run("fictional:candidate", [85, 50, 20])], labels,
                        [run("fictional:baseline", [60, 70, 25])])
    printed = capsys.readouterr().out
    assert "fictional:candidate #2" in printed and "in range 3/3" in printed
    assert "rank agreement 1.000" in printed
    assert "fictional:baseline #1 vs fictional:candidate #2" in printed


def test_other_api_endpoint_settings_reach_the_replay_client(monkeypatch):
    monkeypatch.setattr(tool, "last_usage_id", lambda: 0)
    replayer = tool.Replayer("openai_compatible", "fictional-model", None, {
        "base_url": "https://provider.example/v1", "compatible_protocol": "chat_completions",
        "compatible_reasoning": "thinking", "compatible_medium": "medium"})
    ai = replayer.client.settings.ai
    assert (ai.provider, ai.model, ai.base_url, ai.compatible_reasoning) == (
        "openai_compatible", "fictional-model", "https://provider.example/v1", "thinking")
    assert ai.research_provider is None and not ai.recover_interrupted_requests
