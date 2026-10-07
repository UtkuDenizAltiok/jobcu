from jobcu import db


def test_database_is_created_and_up_to_date(temporary_data_dir):
    with db.connect() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert version == len(db.MIGRATIONS)
    assert "ai_usage" in tables
    assert (temporary_data_dir / db.DB_FILENAME).exists()


def test_connecting_again_keeps_data():
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO ai_usage (step, provider, model, input_tokens, output_tokens, "
            "cached_input_tokens, reasoning_tokens, web_searches) VALUES ('t','p','m',1,2,0,0,0)"
        )
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ai_usage").fetchone()[0] == 1


def test_quality_evidence_migration_preserves_existing_ratings(temporary_data_dir):
    import sqlite3

    from jobcu import quality

    temporary_data_dir.mkdir(parents=True)
    conn = sqlite3.connect(temporary_data_dir / db.DB_FILENAME)
    for migration in db.MIGRATIONS[:10]:
        conn.executescript(migration)
    conn.execute("PRAGMA user_version = 10")
    conn.execute("INSERT INTO quality_ads (kind, source, source_job_id, title, url, text, rating) "
                 "VALUES ('scored', 'fake', '1', 'Fictional Engineer', '', 'Full ad', 'good')")
    conn.commit()
    conn.close()
    (ad,) = quality.all_ads()
    assert ad.description_is_complete and ad.location_plan is None
    assert ad.rating == "good" and ad.text == "Full ad"


def test_many_parts_of_jobcu_can_open_a_new_database_at_once():
    import threading

    errors = []

    def open_database():
        try:
            with db.connect() as conn:
                conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
        except Exception as exc:  # collected so the test can show them
            errors.append(exc)

    threads = [threading.Thread(target=open_database) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []


def test_application_link_migration_preserves_existing_marks_and_ratings(temporary_data_dir):
    import sqlite3

    temporary_data_dir.mkdir(parents=True)
    conn = sqlite3.connect(temporary_data_dir / db.DB_FILENAME)
    for migration in db.MIGRATIONS[:11]:
        conn.executescript(migration)
    conn.execute("PRAGMA user_version = 11")
    conn.execute("INSERT INTO jobs (id, title) VALUES (1, 'Fictional Nurse')")
    conn.execute("INSERT INTO job_states (job_id, saved, applied) VALUES (1, 1, 1)")
    conn.execute("INSERT INTO quality_ads (kind, source, source_job_id, title, url, text, rating, "
                 "rated_by) VALUES ('scored', 'fake', '1', 'Fictional Nurse', '', 'Full ad', "
                 "'good', 'owner')")
    conn.commit()
    conn.close()
    with db.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        assert tuple(conn.execute("SELECT saved, applied FROM job_states").fetchone()) == (1, 1)
        assert tuple(conn.execute("SELECT rating, rated_by FROM quality_ads").fetchone()) == (
            "good", "owner")
        assert conn.execute("SELECT COUNT(*) FROM application_link_reports").fetchone()[0] == 0


def test_identity_migration_preserves_legacy_jobs_and_reports(temporary_data_dir):
    import sqlite3

    temporary_data_dir.mkdir(parents=True)
    conn = sqlite3.connect(temporary_data_dir / db.DB_FILENAME)
    for migration in db.MIGRATIONS[:12]:
        conn.executescript(migration)
    conn.execute("PRAGMA user_version = 12")
    conn.execute("INSERT INTO jobs (id, title) VALUES (1, 'Fictional Nurse')")
    keys = [("copy:employer:example/old", 1), ("job:example|nurse|berlin", 1)]
    conn.executemany("INSERT INTO job_keys (key, job_id) VALUES (?, ?)", keys)
    conn.execute("INSERT INTO job_states (job_id, saved, applied) VALUES (1, 1, 1)")
    conn.execute("INSERT INTO application_link_reports (url, job_id, source) VALUES "
                 "('https://jobs.example.test/old', 1, 'Example')")
    conn.commit()
    conn.close()
    with db.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        saved_keys = sorted(tuple(row) for row in conn.execute("SELECT key, job_id FROM job_keys"))
        assert saved_keys == keys
        saved_name = conn.execute("SELECT key, job_id, country FROM job_fingerprints").fetchone()
        assert tuple(saved_name) == ("job:example|nurse|berlin", 1, "")
        assert tuple(conn.execute("SELECT saved, applied FROM job_states").fetchone()) == (1, 1)
        assert conn.execute("SELECT url FROM application_link_reports").fetchone()[0] == (
            "https://jobs.example.test/old")
