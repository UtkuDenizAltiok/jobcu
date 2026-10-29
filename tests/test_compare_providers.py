"""The provider comparison tool reads captures and scores saved ads without real traffic."""

import importlib.util
import json
import re
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
    labels = {"ranges": {"0": [70, 90], "1": [40, 60], "2": [10, 30]}, "blockers": {"2": 30}}
    candidate = {**run("fictional:candidate", [85, 50, 20]),
                 "usage": {"rows": 1, "input_tokens": 9, "output_tokens": 10,
                           "reasoning_tokens": 4}}
    tool.show_saved_ads([candidate], labels, [run("fictional:baseline", [60, 70, 45])])
    printed = capsys.readouterr().out
    candidate_line = next(line for line in printed.splitlines()
                          if "fictional:candidate #2" in line)
    assert candidate_line.split()[2:8] == ["1.000", "3/3", "3/3", "3/3", "0.0", "1/1"]
    assert candidate_line.split()[-1] == "40%"
    assert tool.thinking({"usage": {"rows": 4, "output_tokens": 10, "reasoning_tokens": 4,
                                    "rows_without_reasoning": 1}}) == "40% (1/4 requests none!)"
    silent = {"rows": 2, "output_tokens": 10, "reasoning_tokens": 0}
    assert tool.thinking({"model": "anthropic:claude-haiku-5-5", "usage": silent}) == (
        "not reported")
    assert tool.thinking({"model": "openrouter:fictional", "usage": silent}) == "none!"
    assert "blocker missed: 2 45 (at most 30)" in printed
    assert "fictional:baseline #1 vs fictional:candidate #2" in printed


def test_label_metrics_count_only_clearly_different_pairs_and_ties_as_half():
    labels = {"ranges": {"a": [70, 90], "b": [72, 88], "c": [40, 50], "d": [10, 20]}}
    found = tool.label_metrics(run("fictional:m", []) | {"ads": {
        i: {"score": s} for i, s in {"a": 60, "b": 80, "c": 60, "d": 10}.items()}}, labels)
    # a-b are too close to count; a ties with c (half), the other four clear pairs are right.
    assert found["clear_pairs"] == 4.5 / 5
    assert found["big_misses"] == [] and found["in_range"] == 2
    assert found["bands"] == 2  # a (apply) scored as maybe, c (skip) scored as maybe


def test_an_ad_file_is_scored_with_its_own_profile_and_each_ads_place(monkeypatch, tmp_path):
    from jobcu.ai.base import ProviderAdapter, RawReply, Usage
    from jobcu.ai.client import AIClient
    from jobcu.dedupe import group_duplicates
    from jobcu.settings import Settings
    from jobcu.sources.base import FoundJob

    class Scripted(ProviderAdapter):
        prompts = []

        def complete_json(self, **request):
            self.prompts.append(request["prompt"])
            return RawReply(json.dumps({"scores": [{
                "job_id": job_id, "ad_language": "English", "languages_asked": [],
                "years_required": None, "doctorate": "not_required",
                "citizenship_or_clearance": "no_such_requirement",
                "citizenship_or_clearance_words": "", "role_and_skills": 38, "seniority": 18,
                "hard_requirements": 15, "location_and_preferences": 9, "reasons": ["Fits"],
                "job_type": "unclear", "work_mode": "unclear", "fully_remote": False}
                for job_id in re.findall(r"JOB (J\d+)", request["prompt"])]}), Usage(1, 1))

        def list_models(self):
            return []

    jobs = [FoundJob(source="board", source_job_id=str(i), url="https://jobs.example/1",
                     title=f"Fictional engineer {i}", company="Example Ltd",
                     location_text="Exampletown", country=country, description="Fictional ad",
                     description_is_complete=True)
            for i, country in enumerate(["GB", "DE"])]
    profile = {"summary": "Fictional analog designer.", "current_or_last_role": None,
               "field": "Electronics", "skills": [], "technical_areas": [],
               "years_full_time_experience": 0, "years_student_or_part_time_experience": 1,
               "experience_note": "", "seniority": "graduate_or_entry", "education": [],
               "languages": [], "target_roles": [], "target_fields": [], "preferences": [],
               "work_mode_preference": "not_stated", "dealbreakers": [],
               "work_authorisation": None, "ignored_as_application_specific": []}
    ads = tmp_path / "ads.json"
    ads.write_text(json.dumps({"profile": profile, "ads": [
        {"id": f"x{i}", "plan": None,
         "group": tool.pool.group_to_dict(group_duplicates([job], {"board": "job_board"})[0])}
        for i, job in enumerate(jobs)]}), encoding="utf-8")
    monkeypatch.setattr(tool, "last_usage_id", lambda: 0)
    monkeypatch.setattr(tool, "run_usage", lambda *_: {
        "rows": 1, "input_tokens": 5, "output_tokens": 5, "reasoning_tokens": 0})
    replayer = tool.Replayer("gemini", "fictional-model", None)
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    replayer.client = AIClient(settings, adapter=Scripted("fake"))
    [result] = tool.saved_ads_runs(replayer, 1, ads)
    assert "Fictional analog designer." in Scripted.prompts[0]
    assert "Exampletown (GB)" in Scripted.prompts[0]
    # The UK job is marked down for unconfirmed sponsorship, as in a real search.
    assert result["ads"]["x1"]["score"] - result["ads"]["x0"]["score"] == 5
    assert tool.thinking(result) == "none!"


def test_other_api_endpoint_settings_reach_the_replay_client(monkeypatch):
    monkeypatch.setattr(tool, "last_usage_id", lambda: 0)
    replayer = tool.Replayer("openai_compatible", "fictional-model", None, {
        "base_url": "https://provider.example/v1", "compatible_protocol": "chat_completions",
        "compatible_reasoning": "thinking", "compatible_medium": "medium"})
    ai = replayer.client.settings.ai
    assert (ai.provider, ai.model, ai.base_url, ai.compatible_reasoning) == (
        "openai_compatible", "fictional-model", "https://provider.example/v1", "thinking")
    assert ai.research_provider is None and not ai.recover_interrupted_requests
