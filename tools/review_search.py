"""Review the latest saved search without AI calls, network requests or database writes.

    uv run python tools/review_search.py

Only aggregate measurements are printed: never a query, profile, title, URL, note or key.
Keep even these measurements local unless the owner approves a public summary. Detailed
investigation uses a private scratch copy of the data, as described in CONTRIBUTING.md.
"""

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jobcu.countries import COUNTRIES  # noqa: E402
from jobcu.db import DB_FILENAME  # noqa: E402
from jobcu.paths import data_dir  # noqa: E402
from jobcu.search import STEPS  # noqa: E402
from jobcu.sources import all_sources  # noqa: E402

STATUSES = {"finished", "running", "failed", "stopped"}
SOURCE_STATUSES = {"ok", "partial", "failed", "unavailable", "skipped"}
USAGE_STEPS = {"profile", "location", "search_words", "employers", "quick_pass", "title_screen",
               "scoring", "job_places", "travel", "location_research", "location_structure"}


def number(value) -> float:
    return (float(value) if isinstance(value, (int, float))
            and math.isfinite(value) and value > 0 else 0)


def read_saved(folder: Path) -> tuple[dict | None, list[dict]]:
    """SQLite read-only mode also refuses to create a missing database or run migrations."""
    path = folder / DB_FILENAME
    if not path.is_file():
        return None, []
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT search_id, result_json FROM search_results "
                           "ORDER BY search_id DESC LIMIT 1"
                           ).fetchone()
        if row is None:
            return None, []
        columns = {column["name"] for column in conn.execute("PRAGMA table_info(quality_ads)")}
        complete = ", description_is_complete" if "description_is_complete" in columns else ""
        ads = [dict(row) for row in conn.execute("SELECT kind, url, rating" + complete +
                                                " FROM quality_ads")]
        snapshot = json.loads(row["result_json"])
        latest = conn.execute("SELECT id, status FROM searches ORDER BY id DESC LIMIT 1").fetchone()
        snapshot["review_latest_attempt_status"] = latest["status"] if latest else None
        snapshot["review_is_latest_attempt"] = bool(latest and latest["id"] == row["search_id"])
        return snapshot, ads
    finally:
        conn.close()


def top_quality(cards: list[dict], ads: list[dict]) -> dict:
    """Precision is available only after every top card has an independent rating."""
    ratings: dict[str, set[str]] = {}
    for ad in ads:
        if (ad.get("kind") == "scored" and ad.get("rating") in {"good", "okay", "poor"}
                and ad.get("url")):
            ratings.setdefault(ad["url"], set()).add(ad["rating"])
    top = sorted((c for c in cards if isinstance(c.get("score"), (int, float))),
                 key=lambda c: -c["score"])[:10]
    counts = Counter()
    for card in top:
        urls = [card.get("main_link", {}).get("url"),
                *(link.get("url") for link in card.get("also_on", []))]
        matched = {rating for url in urls for rating in ratings.get(url, set())}
        # Conflicting ratings of copies need review, rather than silently picking a favourable one.
        counts[next(iter(matched)) if len(matched) == 1 else "not_rated"] += 1
    rated = sum(counts[k] for k in ("good", "okay", "poor"))
    return {"size": len(top), "rated": rated,
            **{k: counts[k] for k in ("good", "okay", "poor", "not_rated")},
            "precision_good": round(counts["good"] / len(top), 3)
            if top and rated == len(top) else None}


def review(snapshot: dict, ads: list[dict]) -> dict:
    """Build a measurement report from allowlisted fields; no free text passes through."""
    kind = snapshot.get("kind") if snapshot.get("kind") in {"search", "reapply"} else "unknown"
    result = snapshot.get("result", {})
    jobs = result.get("jobs", {})
    cards = jobs.get("cards", [])
    unknown = jobs.get("date_unknown", [])
    visible = [*cards, *unknown]
    scored = [c for c in visible if isinstance(c.get("score"), (int, float))]
    top = sorted((c for c in cards if isinstance(c.get("score"), (int, float))),
                 key=lambda c: -c["score"])[:10]
    countries = Counter(c.get("country") for c in visible if c.get("country") in COUNTRIES)
    known_sources = {source.id for source in all_sources()}
    sources = [{"id": s["source"],
                "status": s.get("status") if s.get("status") in SOURCE_STATUSES else "unknown",
                **{k: int(number(s.get(k))) for k in ("jobs_found", "unique", "requests")}}
               for s in jobs.get("sources", []) if s.get("source") in known_sources]
    known_steps = {step_id for step_id, _ in STEPS} | {"conditions"}
    timings = {s["id"]: round(number(s.get("elapsed_seconds")), 3)
               for s in snapshot.get("steps", [])
               if s.get("id") in known_steps and "elapsed_seconds" in s}
    usage = {}
    for step, used in result.get("usage", {}).items():
        name = step if step in USAGE_STEPS else "other"
        totals = usage.setdefault(name, Counter())
        totals.update({k: int(number(used.get(k))) for k in
                       ("input_tokens", "output_tokens", "cached_input_tokens",
                        "reasoning_tokens", "web_searches")})
    conditions = result.get("location", {}).get("conditions", [])
    sample = [a for a in ads if a.get("kind") == "scored"]
    rated = [a for a in sample if a.get("rating") in {"good", "okay", "poor"}]
    summary_count = sum(bool(c.get("summary_only")) for c in visible)
    report = {
        "status": snapshot.get("status") if snapshot.get("status") in STATUSES else "unknown",
        "kind": kind,
        "timing_scope": {"search": "original_search", "reapply": "latest_correction"}
                        .get(kind, "unknown"),
        "usage_scope": {"search": "original_search", "reapply": "search_and_all_corrections"}
                       .get(kind, "unknown"),
        "is_latest_attempt": snapshot.get("review_is_latest_attempt"),
        "latest_attempt_status": (snapshot.get("review_latest_attempt_status")
                                  if snapshot.get("review_latest_attempt_status") in STATUSES
                                  else "unknown"),
        "jobs": {"shown": len(visible), "scored": len(scored),
                 "not_scored": len(visible) - len(scored), "date_unknown": len(unknown),
                 "summary_only": summary_count,
                 "summary_share": round(summary_count / len(visible), 3) if visible else None,
                 "top_10_summaries": sum(bool(c.get("summary_only")) for c in top),
                 "top_10_limited": sum(bool(c.get("limits")) for c in top),
                 "possible_duplicates": sum(bool(c.get("possible_duplicate_of")) for c in visible),
                 "unclear_location": sum(any(check.get("status") == "unclear"
                                             for check in c.get("location_checks", []))
                                         for c in visible),
                 "by_country": dict(sorted(countries.items()))},
        "funnel": {k: int(number(jobs.get("counts", {}).get(k))) for k in
                   ("ads_found", "different_jobs", "unrelated", "not_scored", "shown")},
        "conditions": {status: sum(c.get("status") == status for c in conditions)
                       for status in ("applied", "estimate", "not_checked")},
        "sources": sources, "seconds_by_step": timings,
        "waiting_seconds": (round(number(snapshot["waiting_seconds"]), 3)
                            if "waiting_seconds" in snapshot else None),
        "usage_by_step": usage,
        "quality_sample": {"collected": len(sample), "rated": len(rated),
                           "summary_only": sum(not a.get("description_is_complete", True)
                                               for a in sample),
                           "ratings": {r: sum(a.get("rating") == r for a in rated)
                                       for r in ("good", "okay", "poor")}},
        "top_10_quality": top_quality(cards, ads),
        "coverage_recall": None,
        "checks_needed": [],
    }
    checks = report["checks_needed"]
    if snapshot.get("review_is_latest_attempt") is False:
        checks.append("These are older saved results; the latest attempt has no saved results.")
    if report["status"] != "finished":
        checks.append("This saved search did not finish; investigate before comparing quality.")
    if kind == "reapply":
        checks.append("Timings cover only the latest condition correction; usage includes the "
                      "original search and all corrections. Compare complete original searches "
                      "for performance.")
    elif kind == "unknown":
        checks.append("This saved run has no recognized kind; timing and usage scopes are unknown.")
    if not visible:
        checks.append("No visible jobs: inspect source availability and filtering locally.")
    if summary_count:
        checks.append("Verify top summaries against original ads before trusting their rank.")
    if report["conditions"]["not_checked"]:
        checks.append("Some requested conditions were not checked; inspect them locally.")
    if any(s["status"] in {"failed", "unavailable", "partial"} for s in sources):
        checks.append("Source coverage is incomplete; inspect source messages locally.")
    if len(scored) < len(visible):
        checks.append("Some visible jobs were not scored; compare the scoring limit with results.")
    if not timings:
        checks.append("This older search has no step timings; measure the next search.")
    if report["top_10_quality"]["precision_good"] is None:
        checks.append("Independently rate every top-10 card before reporting precision.")
    checks.append("Coverage recall needs a date-verified independent list; "
                  "card counts cannot prove it.")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="private scratch data folder (defaults to Jobcu's data folder)")
    args = parser.parse_args(argv)
    try:
        snapshot, ads = read_saved(args.data_dir or data_dir())
        if snapshot is None:
            print("No saved search yet. Complete your personal setup "
                  "and run a search in Jobcu first.")
            return 0
        print(json.dumps(review(snapshot, ads), indent=2))
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
        print("The saved search could not be reviewed. Inspect the private data folder locally.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
