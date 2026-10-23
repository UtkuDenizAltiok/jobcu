"""Opt-in comparison evidence stays local and cannot start or repeat paid work."""

import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import BaseModel

from jobcu import review_capture
from jobcu.ai.base import AIQuotaExhausted, AIUnavailable, RawReply, Usage
from jobcu.ai.client import AIClient
from jobcu.settings import AISettings, Settings


def records(capture):
    return [json.loads(line) for line in
            (capture.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def test_capture_is_absent_by_default(temporary_data_dir):
    assert review_capture.claim(7, lambda message: pytest.fail(message)) is None
    assert not (temporary_data_dir / "review-captures").exists()


def test_one_arm_is_claimed_once_and_cannot_be_silently_replaced():
    review_capture.arm_next_search()
    with pytest.raises(FileExistsError):
        review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))
    assert records(capture)[0]["search_id"] == 7
    assert review_capture.claim(8, lambda message: pytest.fail(message)) is None
    if os.name == "posix":
        assert capture.folder.stat().st_mode & 0o077 == 0
        assert (capture.folder / "events.jsonl").stat().st_mode & 0o077 == 0


def test_parallel_claim_cannot_capture_two_searches():
    review_capture.arm_next_search()
    with ThreadPoolExecutor(max_workers=2) as pool:
        captured = list(pool.map(lambda number: review_capture.claim(number, lambda _: None),
                                 [7, 8]))
    assert sum(value is not None for value in captured) == 1


def test_continuation_reopens_only_its_original_capture_and_keeps_next_arm():
    review_capture.arm_next_search()
    original = review_capture.claim(7, lambda message: pytest.fail(message))
    review_capture.arm_next_search()
    assert review_capture.resume(8, lambda message: pytest.fail(message)) is None
    resumed = review_capture.resume(7, lambda message: pytest.fail(message))
    assert resumed.folder == original.folder
    resumed.event("continuation")
    assert [row["kind"] for row in records(original)] == ["search", "continuation"]
    assert review_capture.claim(8, lambda message: pytest.fail(message)) is not None


def test_continuation_does_not_create_capture_without_original_opt_in(temporary_data_dir):
    assert review_capture.resume(7, lambda message: pytest.fail(message)) is None
    assert not (temporary_data_dir / "review-captures").exists()


def test_continuation_rejects_ambiguous_or_mismatched_capture():
    review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))
    path = capture.folder / "events.jsonl"
    path.write_text('{"kind":"search","search_id":8}\n', encoding="utf-8")
    notes = []
    assert review_capture.resume(7, notes.append) is None
    assert len(notes) == 1
    (capture.folder.parent / "search-7-other").mkdir()
    assert review_capture.resume(7, notes.append) is None
    assert len(notes) == 2


def test_capture_rejects_repository_data_folder(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setenv("JOBCU_DATA_DIR", str(repo / "private"))
    with pytest.raises(ValueError, match="outside a Git"):
        review_capture.arm_next_search()


@pytest.mark.skipif(os.name == "nt", reason="Unprivileged Windows symlinks are unavailable")
@pytest.mark.parametrize("component", ["marker", "root"])
def test_capture_rejects_symlink_escape(temporary_data_dir, tmp_path, component):
    review_capture.arm_next_search()
    if component == "root":
        (temporary_data_dir / "review-captures").symlink_to(tmp_path / "elsewhere")
    else:
        marker = temporary_data_dir / review_capture.ARM_FILE
        marker.rename(tmp_path / "elsewhere")
        marker.symlink_to(tmp_path / "elsewhere")
    notices = []
    assert review_capture.claim(7, notices.append) is None
    assert len(notices) == 1


@pytest.mark.skipif(os.name == "nt", reason="Unprivileged Windows symlinks are unavailable")
def test_continuation_rejects_a_linked_capture_folder(tmp_path):
    review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))
    target = tmp_path / "elsewhere"
    capture.folder.rename(target)
    capture.folder.symlink_to(target)
    notes = []
    assert review_capture.resume(7, notes.append) is None
    assert len(notes) == 1


class Answer(BaseModel):
    ok: bool


@pytest.mark.parametrize("profession", ["power electronics", "nursing", "teaching"])
def test_ai_capture_preserves_exact_schema_repairs_evidence_and_receipts(profession):
    review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))

    class Adapter:
        count = 0
        key = "fictional-secret-not-a-prompt"

        def complete_json(self, **arguments):
            self.count += 1
            return RawReply('invalid' if self.count == 1 else '{"ok":true}', Usage(100, 30))

    adapter = Adapter()
    client = AIClient(Settings(ai=AISettings(provider="mimo", model="fictional-model")),
                      adapter=adapter, capture=capture)
    assert client.generate(Answer, step="scoring", system="Do not invent facts.",
                           prompt=f"Fictional {profession} ad.").ok
    events = records(capture)
    starts = [row for row in events if row["kind"] == "ai_start"]
    ends = [row for row in events if row["kind"] == "ai_end"]
    assert len(starts) == len(ends) == adapter.count == 2
    assert starts[0]["arguments"]["prompt"] == f"Fictional {profession} ad."
    assert "IMPORTANT" in starts[1]["arguments"]["prompt"]
    assert starts[0]["arguments"]["schema"]["required"] == ["ok"]
    assert starts[0]["arguments"]["effort"] == "medium"
    assert all(row["reply"]["usage"]["output_tokens"] == 30 for row in ends)
    assert all(row["elapsed"] >= 0 for row in ends)
    assert adapter.key not in (capture.folder / "events.jsonl").read_text(encoding="utf-8")


def test_failed_call_is_recorded_once_without_provider_envelope_or_retry():
    review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))
    calls = []

    def complete_json(**arguments):
        calls.append(arguments)
        error = AIQuotaExhausted("Fictional refusal", "unnecessary-provider-envelope")
        error.usage = Usage(20, 2)
        raise error

    with pytest.raises(AIQuotaExhausted):
        capture.call(complete_json, step="profile", provider="mimo", prompt="Fictional text")
    assert len(calls) == 1
    end = records(capture)[-1]
    assert end["error"] == "AIQuotaExhausted" and end["usage"]["input_tokens"] == 20
    assert "unnecessary-provider-envelope" not in json.dumps(end)


def test_saving_failure_does_not_repeat_or_lose_a_successful_answer():
    notes = []
    review_capture.arm_next_search()
    capture = review_capture.claim(7, notes.append)
    (capture.folder / "events.jsonl").unlink()
    (capture.folder / "events.jsonl").mkdir()  # reproduce an I/O failure
    calls = []

    def complete_json():
        calls.append(1)
        return RawReply('{"ok":true}', Usage(10, 2))

    assert capture.call(complete_json, step="scoring", provider="mimo").text == '{"ok":true}'
    assert len(calls) == len(notes) == 1


def test_retry_wait_intervals_are_distinct_from_processing():
    review_capture.arm_next_search()
    capture = review_capture.claim(7, lambda message: pytest.fail(message))

    class Adapter:
        count = 0

        def complete_json(self, **arguments):
            self.count += 1
            if self.count == 1:
                raise AIUnavailable("Fictional temporary failure")
            return RawReply('{"ok":true}', Usage(20, 2))

    ai = AIClient(Settings(ai=AISettings(provider="mimo", model="fictional-model")),
                  adapter=Adapter(), capture=capture, sleep=lambda seconds: None)
    ai.generate(Answer, step="scoring", system="Fictional", prompt="Fictional")
    kinds = [row["kind"] for row in records(capture)]
    assert kinds == ["search", "ai_start", "ai_end", "ai_wait_start", "ai_wait_end",
                     "ai_start", "ai_end"]
