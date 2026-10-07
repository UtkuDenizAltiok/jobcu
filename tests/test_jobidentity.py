"""Fictional vacancies: recall and owner marks must survive identity ambiguities."""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest

from jobcu import db, jobstore
from jobcu.dedupe import JobGroup
from jobcu.filters import apply_rules
from jobcu.settings import JOB_TYPES
from jobcu.sources.base import FoundJob


def group(vacancy, title="Power Electronics Engineer", *, source="employer", kind="employer",
          country="DE", company="Example Ltd"):
    return JobGroup([FoundJob(source, vacancy, f"https://jobs.example.test/{vacancy}", title,
                             company=company, location_text="Berlin", country=country,
                             posted_at=datetime.now(UTC), date_precision="exact")],
                    source_kinds={source: kind})


def new_search():
    with db.connect() as conn:
        return conn.execute(
            "INSERT INTO searches (status, form_json) VALUES ('running', '{}')").lastrowid


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_new_employer_requisition_inherits_neither_old_marks_nor_old_freshness(title):
    old, fresh = group("example/old", title), group("example/new", title)
    (old_id,), _ = jobstore.remember([old], new_search())
    jobstore.set_state(old_id, saved=True, applied=True, dismissed=True)
    with db.connect() as conn:
        conn.execute("UPDATE jobs SET first_seen_at = ? WHERE id = ?",
                     ((datetime.now(UTC) - timedelta(days=20)).isoformat(), old_id))
    assert jobstore.find_job_ids([fresh]) == [None]
    (new_id,), new = jobstore.remember([fresh], new_search())
    assert new_id != old_id and new == [True]
    assert jobstore.states([new_id]) == {}
    seen = jobstore.first_seen([new_id])
    outcome = apply_rules([fresh], [None], started_at=datetime.now(UTC),
                          posted_within_hours=24, job_types=list(JOB_TYPES),
                          exclude_remote=False, countries=["DE"], first_shown=[seen[new_id]])
    assert outcome.kept == [0] and not outcome.left_out
    assert jobstore.states([old_id])[old_id].dismissed
    assert jobstore.find_job_ids([old, fresh]) == [old_id, new_id]


def test_exact_source_id_outranks_an_older_title_match():
    old = group("example/old")
    fresh = group("example/new")
    (old_id,), _ = jobstore.remember([old], new_search())
    (new_id,), _ = jobstore.remember([fresh], new_search())
    assert new_id > old_id
    jobstore.set_state(old_id, dismissed=True)
    jobstore.set_state(new_id, saved=True)
    assert jobstore.find_job_ids([fresh]) == [new_id]
    again, new = jobstore.remember([fresh], new_search())
    assert again == [new_id] and new == [False]
    assert jobstore.states(again)[new_id].saved
    assert not jobstore.states(again)[new_id].dismissed


def test_ambiguous_title_match_cannot_pick_one_of_two_known_requisitions():
    first, second = group("example/first"), group("example/second")
    ids, _ = jobstore.remember([first, second], new_search())
    assert len(set(ids)) == 2
    board = group("board-copy", source="board", kind="job_board")
    assert jobstore.find_job_ids([board]) == [None]
    (board_id,), new = jobstore.remember([board], new_search())
    assert board_id not in ids and new == [True]
    assert jobstore.find_job_ids([first, second, board]) == [*ids, board_id]


def test_unique_cross_source_copy_preserves_marks_and_same_batch_new_status():
    first = group("board-copy", source="board", kind="job_board")
    original = group("example/original")
    first.copies.append(original.main)
    first.source_kinds.update(original.source_kinds)
    ids, new = jobstore.remember([first, original], new_search())
    assert ids[0] == ids[1] and new == [True, True]
    jobstore.set_state(ids[0], saved=True, dismissed=True)
    another = group("aggregator-copy", source="aggregator", kind="aggregator")
    assert jobstore.find_job_ids([another]) == [ids[0]]
    again, flags = jobstore.remember([another], new_search())
    assert again == [ids[0]] and flags == [False]
    assert jobstore.states(again)[ids[0]].saved and jobstore.states(again)[ids[0]].dismissed


def test_memory_cannot_join_current_groups_that_full_evidence_kept_separate():
    from jobcu.dedupe import group_duplicates

    first = group("oncology", title="Registered Nurse", source="a", kind="job_board")
    second = group("community", title="Registered Nurse", source="b", kind="job_board")
    first.main.description = (
        "Provide hospital oncology care for patients receiving chemotherapy. " * 20)
    second.main.description = (
        "Visit families at home and provide community public health support. " * 20)
    first.main.description_is_complete = second.main.description_is_complete = True
    groups = group_duplicates([first.main, second.main], {"a": "job_board", "b": "job_board"})
    assert len(groups) == 2
    ids, new = jobstore.remember(groups, new_search())
    assert len(set(ids)) == 2 and new == [True, True]
    jobstore.set_state(ids[0], dismissed=True)
    assert not jobstore.states([ids[1]])
    assert jobstore.find_job_ids(groups) == ids


def test_an_unknown_current_group_cannot_inherit_a_known_sibling_names_mark():
    first = group("old", source="board", kind="job_board")
    second = group("new", source="board", kind="job_board")
    (old_id,), _ = jobstore.remember([first], new_search())
    jobstore.set_state(old_id, dismissed=True)
    assert jobstore.find_job_ids([first, second]) == [old_id, None]
    ids, _ = jobstore.remember([first, second], new_search())
    assert ids[0] == old_id and ids[1] != old_id


def test_batch_name_ambiguity_keeps_proven_countries_distinct_without_losing_unique_copies():
    first = group("old-de", source="a", kind="job_board")
    second = group("old-ie", source="a", kind="job_board", country="IE")
    ids, _ = jobstore.remember([first, second], new_search())
    copies = [group("copy-de", source="b", kind="job_board"),
              group("copy-ie", source="b", kind="job_board", country="IE")]
    assert jobstore.find_job_ids(copies) == ids


def test_new_requisition_cannot_use_an_old_board_copy_to_inherit_old_identity():
    old = group("example/old")
    old.copies.append(group("board-copy", source="board", kind="job_board").main)
    (old_id,), _ = jobstore.remember([old], new_search())
    jobstore.set_state(old_id, dismissed=True)
    fresh = group("example/new")
    fresh.copies.append(old.copies[1])
    assert jobstore.find_job_ids([fresh]) == [None]
    (new_id,), _ = jobstore.remember([fresh], new_search())
    assert new_id != old_id
    assert jobstore.find_job_ids([old, fresh]) == [old_id, new_id]


def test_same_names_in_different_countries_do_not_transfer_marks():
    first = group("de-job", title="Registered Nurse", source="a", kind="job_board")
    second = group("ie-job", title="Registered Nurse", source="b", kind="job_board", country="IE")
    (first_id,), _ = jobstore.remember([first], new_search())
    jobstore.set_state(first_id, dismissed=True)
    assert jobstore.find_job_ids([second]) == [None]
    (second_id,), _ = jobstore.remember([second], new_search())
    assert first_id != second_id
    assert jobstore.find_job_ids([first, second]) == [first_id, second_id]


def test_unknown_country_does_not_rule_out_a_unique_copy():
    first = group("de-job", source="a", kind="job_board")
    second = group("copy", source="b", kind="job_board", country=None)
    (job_id,), _ = jobstore.remember([first], new_search())
    assert jobstore.find_job_ids([second]) == [job_id]


def test_legacy_identity_is_preserved_but_a_new_employer_id_stays_new():
    old = group("example/old")
    search_id = new_search()
    with db.connect() as conn:
        job_id = conn.execute("INSERT INTO jobs (title, first_seen_search_id) VALUES (?, ?)",
                              (old.main.title, search_id)).lastrowid
        conn.executemany("INSERT INTO job_keys (key, job_id) VALUES (?, ?)", [
            ("copy:employer:example/old", job_id),
            ("job:example|power electronics engineer|berlin", job_id)])
        conn.execute("INSERT INTO job_fingerprints (key, job_id) VALUES (?, ?)",
                     ("job:example|power electronics engineer|berlin", job_id))
    jobstore.set_state(job_id, saved=True)
    assert jobstore.find_job_ids([old]) == [job_id]
    assert jobstore.find_job_ids([group("example/new")]) == [None]
    assert jobstore.states([job_id])[job_id].saved
    board = group("copy", source="board", kind="job_board")
    assert jobstore.find_job_ids([board]) == [job_id]


def test_legacy_card_country_prevents_a_known_cross_country_name_match():
    search_id = new_search()
    with db.connect() as conn:
        job_id = conn.execute("INSERT INTO jobs (title, first_seen_search_id) VALUES (?, ?)",
                              ("Registered Nurse", search_id)).lastrowid
        conn.execute("INSERT INTO job_fingerprints (key, job_id) VALUES (?, ?)",
                     ("job:example|registered nurse|berlin", job_id))
    jobstore.save_cards([{"job_id": job_id, "country": "DE"}])
    foreign = group("ie-job", title="Registered Nurse", source="board", kind="job_board",
                    country="IE")
    assert jobstore.find_job_ids([foreign]) == [None]


def test_large_lookup_and_state_reads_fit_lower_sqlite_parameter_limits(monkeypatch):
    groups = [group(f"example/{i}", company=f"Example {i}") for i in range(1000)]
    first = new_search()
    ids, _ = jobstore.remember(groups, first)
    assert len(set(ids)) == len(groups)
    with db.connect() as conn:
        conn.executemany("INSERT INTO job_states (job_id, saved) VALUES (?, 1)",
                         [(i,) for i in ids])
    original = db.connect
    statements = []

    @contextmanager
    def limited(*args, **kwargs):
        with original(*args, **kwargs) as conn:
            conn.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 64)
            conn.set_trace_callback(statements.append)
            yield conn

    monkeypatch.setattr(db, "connect", limited)
    assert jobstore.find_job_ids(groups[::-1]) == ids[::-1]
    lookups = [s for s in statements
               if s.startswith("SELECT key, job_id FROM job_keys WHERE key IN")]
    assert len(lookups) <= 20  # batch queries, rather than one query for every job
    assert len(jobstore.states([*ids, *ids])) == len(ids)
    assert all(state.saved for state in jobstore.states(ids).values())
    assert len(jobstore.first_seen(ids)) == len(ids)
    again, new = jobstore.remember(groups, new_search())
    assert again == ids and new == [False] * len(groups)


def test_failed_identity_save_rolls_back_new_jobs_and_preserves_old_history():
    (job_id,), _ = jobstore.remember([group("example/old")], new_search())
    jobstore.set_state(job_id, saved=True, applied=True)
    original = {"job_id": job_id, "title": "Fictional Engineer", "score": 91}
    jobstore.save_cards([original])
    with db.connect() as conn:
        conn.execute("""
            CREATE TRIGGER fail_identity BEFORE INSERT ON job_fingerprints
            BEGIN SELECT RAISE(FAIL, 'Simulated identity storage failure'); END;
        """)
    with pytest.raises(sqlite3.IntegrityError, match="Simulated identity storage failure"):
        jobstore.remember([group("example/new")], new_search())
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM job_keys").fetchone()[0] == 1
        assert json.loads(conn.execute("SELECT card_json FROM job_cards").fetchone()[0]) == original
    state = jobstore.states([job_id])[job_id]
    assert state.saved and state.applied


def test_simultaneous_saves_allocate_one_identity_for_the_same_vacancy():
    search_id = new_search()
    start = threading.Barrier(8)
    results, errors = [], []

    def save():
        try:
            start.wait(timeout=10)
            results.append(jobstore.remember([group("example/same")], search_id))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=save) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    assert not any(thread.is_alive() for thread in threads)
    assert not errors and len(results) == 8
    assert len({ids[0] for ids, _ in results}) == 1
    assert all(new == [True] for _, new in results)
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM job_keys").fetchone()[0] == 1
