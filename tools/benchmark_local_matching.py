"""Compare local identity/deduplication work with a Git baseline, using fictional data only.

Run: uv run python tools/benchmark_local_matching.py --baseline 61b133d
This makes no network/provider calls, never reads saved user data, and deletes its temporary DB.
Results measure two local components, not live search speed, ranking quality or market recall.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import types
from contextlib import contextmanager
from pathlib import Path

from jobcu import db, dedupe, jobstore
from jobcu.dedupe import JobGroup
from jobcu.sources.base import FoundJob

ROOT = Path(__file__).resolve().parents[1]


def baseline_module(module: str, revision: str):
    source = subprocess.check_output(
        ["git", "show", f"{revision}:src/jobcu/{module}.py"], cwd=ROOT, encoding="utf-8")
    name = f"jobcu_benchmark_baseline_{module}"
    loaded = types.ModuleType(name)
    sys.modules[name] = loaded
    exec(compile(source, name, "exec"), loaded.__dict__)
    return loaded


@contextmanager
def fictional_data():
    previous = os.environ.get("JOBCU_DATA_DIR")
    try:
        with tempfile.TemporaryDirectory(prefix="jobcu-local-matching-") as folder:
            os.environ["JOBCU_DATA_DIR"] = str(Path(folder) / "data")
            yield
    finally:
        if previous is None:
            os.environ.pop("JOBCU_DATA_DIR", None)
        else:
            os.environ["JOBCU_DATA_DIR"] = previous


def median_ms(work, rounds: int) -> float:
    work()  # warm both implementations before measuring
    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        work()
        times.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(times), 3)


def identity_selects(work, expected: list[int]) -> int:
    statements = []
    original = db.connect

    @contextmanager
    def traced(*args, **kwargs):
        with original(*args, **kwargs) as conn:
            conn.set_trace_callback(statements.append)
            yield conn

    db.connect = traced
    try:
        assert work() == expected
    finally:
        db.connect = original
    return sum(s.startswith("SELECT") and "FROM job_keys" in s for s in statements)


def text_preparations(module, work) -> int:
    calls = []
    original = module._shingles

    def counted(text, size=5):
        calls.append(True)
        return original(text, size)

    module._shingles = counted
    try:
        work()
    finally:
        module._shingles = original
    return len(calls)


def benchmark(revision: str, *, jobs=1000, ads=40, rounds=5) -> dict:
    old_dedupe = baseline_module("dedupe", revision)
    old_store = baseline_module("jobstore", revision)
    with fictional_data():
        groups = [JobGroup([FoundJob(
            "employer", f"example/{i}", f"https://jobs.example.test/{i}", f"Fictional role {i}",
            company=f"Example {i}", location_text="Berlin", country="DE")],
            source_kinds={"employer": "employer"}) for i in range(jobs)]
        with db.connect() as conn:
            search_id = conn.execute(
                "INSERT INTO searches (status, form_json) VALUES ('running', '{}')").lastrowid
        ids, _ = jobstore.remember(groups, search_id)
        def before():
            return old_store.find_job_ids(groups)

        def after():
            return jobstore.find_job_ids(groups)

        assert before() == after() == ids
        lookup = {
            "jobs": jobs, "rounds": rounds,
            "before_identity_selects": identity_selects(before, ids),
            "after_identity_selects": identity_selects(after, ids),
            "before_ms": median_ms(before, rounds), "after_ms": median_ms(after, rounds),
            "same_ids": True,
        }
        postings = [FoundJob(
            "board", str(i), f"https://jobs.example.test/ad/{i}", "Registered Nurse",
            company="Example Recruitment", location_text="Berlin", country="DE",
            description=(
                f"unit{i} responsibility{i} qualification{i} location{i} benefit{i} " * 200),
            description_is_complete=True) for i in range(ads)]

        def compare(module):
            grouped = module.group_duplicates(postings, {"board": "job_board"})
            assert {tuple(c.source_job_id for c in g.copies) for g in grouped} == {
                (str(i),) for i in range(ads)}

        comparison = {
            "ads": ads, "rounds": rounds,
            "before_text_preparations": text_preparations(old_dedupe,
                                                         lambda: compare(old_dedupe)),
            "after_text_preparations": text_preparations(dedupe, lambda: compare(dedupe)),
            "before_ms": median_ms(lambda: compare(old_dedupe), rounds),
            "after_ms": median_ms(lambda: compare(dedupe), rounds), "same_groups": True,
        }
    return {"baseline": revision, "fictional_only": True,
            "repeat_identity_lookup": lookup, "full_ad_comparison": comparison}


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Use a positive count.")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Existing local Git commit to compare")
    parser.add_argument("--jobs", type=positive, default=1000)
    parser.add_argument("--ads", type=positive, default=40)
    parser.add_argument("--rounds", type=positive, default=5)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.baseline, jobs=args.jobs, ads=args.ads, rounds=args.rounds),
                     indent=2))


if __name__ == "__main__":
    main()
