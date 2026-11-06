"""Half-price processing a provider kept failing is paused for a few days, then tried again.

On 2026-11-06 Google cancelled or lost every Gemini Flex request sent with request recovery while
normal processing worked. Jobcu then sends lost work once at the normal price and ends Flex for
that search (gemini_adapter.FLEX_FAILURES); without memory, every later search would spend its
first requests finding that out again. A pause written then makes the next searches start at the
normal price, and Flex is tried again after PAUSE_DAYS, so its savings return without anyone
changing a setting.
"""

from datetime import UTC, datetime, timedelta

from jobcu import db

PAUSE_DAYS = 3
_KIND = "flex_paused"


def paused(provider: str) -> bool:
    """Whether the provider's half-price processing failed in a search in the last PAUSE_DAYS."""
    try:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT created_at FROM preparation_cache WHERE kind = ? AND key = ?",
                (_KIND, provider)).fetchone()
    except Exception:  # noqa: BLE001 - no memory available: try Flex as chosen
        return False
    if row is None:
        return False
    try:
        since = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
    except ValueError:
        return False
    return timedelta(0) <= datetime.now(UTC) - since < timedelta(days=PAUSE_DAYS)


def pause(provider: str) -> None:
    with db.connect() as conn:
        conn.execute("INSERT OR REPLACE INTO preparation_cache (kind, key, answer_json) "
                     "VALUES (?, ?, '{}')", (_KIND, provider))
