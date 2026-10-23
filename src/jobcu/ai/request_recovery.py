"""Local metadata for explicitly permitted temporary provider interactions.

No prompts, answers or keys are stored here. Outstanding IDs survive closing/resetting
Jobcu so their remote work can be cancelled, bills reconciled and stored records deleted.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from jobcu import db
from jobcu.ai.base import Usage
from jobcu.paths import data_dir

_lock = threading.RLock()
_active: set[tuple[str, str, str]] = set()


@dataclass
class RecoveryContext:
    enabled: bool
    provider: str
    step: str
    search_id: int | None = None
    checkpoint: Callable[[], None] = lambda: None
    sleep: Callable[[float], None] = time.sleep
    notify: Callable[[str], None] = lambda message: None
    progress: Callable[[str], None] = lambda message: None
    observe: Callable[[Usage, str], None] = lambda usage, request_id: None
    account: Callable[[Usage, str], None] = lambda usage, request_id: None
    capture: object = None

    def wait(self, seconds: float, *, retry: bool = False) -> None:
        """Polling is provider processing time; failed retrieval waits are retry waits."""
        started = time.monotonic()
        if retry and self.capture:
            self.capture.event("ai_wait_start", requested=seconds, error="RecoveryRetrieval")
        try:
            while seconds > 0:
                self.checkpoint()
                pause = min(seconds, 1.0)
                self.sleep(pause)
                seconds -= pause
            self.checkpoint()
        finally:
            if retry and self.capture:
                self.capture.event("ai_wait_end", started=started,
                                   elapsed=max(0, time.monotonic() - started))


def _identity(provider: str, interaction_id: str) -> tuple[str, str, str]:
    return str(data_dir().resolve()), provider, interaction_id


def track(context: RecoveryContext, interaction_id: str, model: str) -> None:
    with _lock, db.connect() as conn:
        conn.execute(
            """INSERT INTO ai_recovery_requests
            (provider,interaction_id,model,search_id,step) VALUES(?,?,?,?,?)""",
            (context.provider, interaction_id, model, context.search_id, context.step))
        _active.add(_identity(context.provider, interaction_id))


def terminal(provider: str, interaction_id: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE ai_recovery_requests SET terminal=1 "
                     "WHERE provider=? AND interaction_id=?", (provider, interaction_id))


def claim(provider: str, interaction_id: str) -> bool:
    with _lock:
        identity = _identity(provider, interaction_id)
        if identity in _active:
            return False
        _active.add(identity)
        return True


def release(provider: str, interaction_id: str, *, deleted: bool) -> None:
    with _lock:
        if deleted:
            with db.connect() as conn:
                conn.execute("DELETE FROM ai_recovery_requests "
                             "WHERE provider=? AND interaction_id=?", (provider, interaction_id))
        else:
            with db.connect() as conn:
                conn.execute("UPDATE ai_recovery_requests SET not_before=? "
                             "WHERE provider=? AND interaction_id=? AND terminal=1",
                             (time.time() + 60, provider, interaction_id))
        _active.discard(_identity(provider, interaction_id))


def unclaim(provider: str, interaction_id: str) -> None:
    """Release a process-local claim even if writing its durable record failed."""
    with _lock:
        _active.discard(_identity(provider, interaction_id))


def pending(provider: str | None = None, *, force: bool = False) -> list[dict]:
    with _lock, db.connect() as conn:
        query, params = "SELECT * FROM ai_recovery_requests WHERE not_before<=?", [
            float("inf") if force else time.time()]
        if provider:
            query += " AND provider=?"
            params.append(provider)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows if
                _identity(row["provider"], row["interaction_id"]) not in _active]


def cleanup_orphans() -> None:
    """On-demand app startup cleanup only; never create another model interaction."""
    from jobcu.ai.gemini_adapter import GeminiAdapter
    from jobcu.keystore import KeyStore

    rows = pending("gemini", force=True)
    if not rows:
        return
    key = KeyStore().get("ai_gemini")
    if not key:
        return  # Keep IDs until the saved credential is available again.
    adapter = GeminiAdapter(key)
    context = RecoveryContext(False, "gemini", "recovery_cleanup")
    adapter.cleanup_pending(context, force=True)
