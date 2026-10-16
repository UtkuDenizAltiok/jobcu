"""Fictional requests and clocks separate request work from retry/source waiting."""
import logging

import pytest
from test_ai_cost_recovery import Answer, ScriptedAdapter, Stopped, settings

from jobcu.ai.base import AIUnavailable
from jobcu.ai.client import AIClient
from jobcu.sources.http import PoliteClient


def test_request_and_actual_retry_times_are_separate_and_contain_no_prompt(monkeypatch, caplog):
    now = [0.0]
    monkeypatch.setattr('jobcu.ai.client.time.monotonic', lambda: now[0])
    monkeypatch.setattr('jobcu.ai.client.random.uniform', lambda a, b: 0)

    class Timed(ScriptedAdapter):
        def complete_json(self, **request):
            now[0] += 1.25
            return super().complete_json(**request)

    adapter = Timed(AIUnavailable('Temporary fictional outage'), '{"ok":true,"word":"ok"}')
    client = AIClient(settings(), adapter=adapter, sleep=lambda seconds: now.__setitem__(
        0, now[0] + seconds))
    with caplog.at_level(logging.INFO, logger='jobcu.ai.client'):
        client.generate(Answer, step='scoring', system='Fictional policy',
                        prompt='PRIVATE_FICTIONAL_JOB_TEXT')
    messages = [record.message for record in caplog.records]
    attempts = [m for m in messages if m.startswith('AI attempt finished')]
    assert len(attempts) == 2 and all('elapsed=1.250s' in m for m in attempts)
    assert all('request_kind=structured' in m for m in attempts)
    assert any('elapsed=5.000s requested=5.000s' in m for m in messages)
    assert all('PRIVATE_FICTIONAL_JOB_TEXT' not in m for m in messages)
    assert 'outcome=AIUnavailable' in attempts[0] and 'outcome=complete' in attempts[1]


def test_cancelled_retry_records_elapsed_wait_instead_of_entire_planned_wait(monkeypatch, caplog):
    now = [0.0]
    monkeypatch.setattr('jobcu.ai.client.time.monotonic', lambda: now[0])
    monkeypatch.setattr('jobcu.ai.client.random.uniform', lambda a, b: 0)

    def checkpoint():
        if now[0] >= 1:
            raise Stopped()

    client = AIClient(settings(), adapter=ScriptedAdapter(AIUnavailable('Fictional outage')),
                      checkpoint=checkpoint, sleep=lambda seconds: now.__setitem__(
                          0, now[0] + seconds))
    with caplog.at_level(logging.INFO), pytest.raises(Stopped):
        client.generate(Answer, step='scoring', system='Policy', prompt='Fictional job')
    assert 'elapsed=1.000s requested=5.000s' in caplog.text


def test_source_pause_records_actual_wait_without_an_external_request(monkeypatch, caplog):
    now = [0.0]
    monkeypatch.setattr('jobcu.sources.http.time.monotonic', lambda: now[0])
    http = PoliteClient(sleep=lambda seconds: now.__setitem__(0, now[0] + seconds))
    try:
        with caplog.at_level(logging.INFO, logger='jobcu.sources.http'):
            http._pause(3, 'fictional.example.test')
        assert 'elapsed=3.000s requested=3.000s' in caplog.text
        assert http.request_count == {}
    finally:
        http.close()
