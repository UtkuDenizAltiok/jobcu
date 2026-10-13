"""Private reuse of successful setup answers, never jobs, research or journey readings."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from jobcu import db
from jobcu.ai.client import MAX_OUTPUT_TOKENS, THINKING_ROOM, AIClient

MAX_AGE_DAYS = 30
KEPT_PER_KIND = 20


def key(client: AIClient, *, reasoning: bool, inputs: list) -> str:
    """Identify the actual generation route/controls and all reusable request inputs."""
    ai = client.settings.ai
    route = {
        "provider": client.provider_id,
        "model": client.model_for(reasoning),
        "effort": ai.reasoning_effort if reasoning else ai.scoring_effort,
        "thinking_room": THINKING_ROOM,
        "output_ceiling": MAX_OUTPUT_TOKENS,
    }
    if client.provider_id == "openai_compatible":
        route.update({name: getattr(ai, name) for name in (
            "base_url", "compatible_protocol", "compatible_reasoning", "compatible_medium",
        )})
    encoded = json.dumps([route, inputs], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def read[T: BaseModel](kind: str, request_key: str, output: type[T]) -> T | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT created_at, answer_json FROM preparation_cache WHERE kind = ? AND key = ?",
            (kind, request_key),
        ).fetchone()
    if row is None:
        return None
    try:
        created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        age = datetime.now(UTC) - created
        if not timedelta(0) <= age <= timedelta(days=MAX_AGE_DAYS):
            return None
        return output.model_validate_json(row["answer_json"])
    except (ValueError, TypeError):
        return None


def write(kind: str, request_key: str, answer: BaseModel) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO preparation_cache (kind, key, answer_json) VALUES (?, ?, ?)",
            (kind, request_key, answer.model_dump_json()),
        )
        conn.execute(
            "DELETE FROM preparation_cache WHERE kind = ? AND key NOT IN "
            "(SELECT key FROM preparation_cache WHERE kind = ? "
            "ORDER BY created_at DESC, key LIMIT ?)",
            (kind, kind, KEPT_PER_KIND),
        )
