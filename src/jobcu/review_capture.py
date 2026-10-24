"""Explicit, one-search local evidence capture for an authorized private comparison.

This never starts work, contacts a service or changes settings. Nothing is armed by default.
The assistant arms it only after checking private authorization. Keys, HTTP headers and hidden
reasoning are not collected. Captured prompts/results are private data, never Git fixtures.
"""

import json
import os
import threading
import time
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

from jobcu.paths import ensure_data_dir

ARM_FILE = "review-capture-next-search.json"
# Windows can let two threads rename the same arm file (seen in CI on 2026-10-25), so claims in
# this process take turns; the rename still guards against another process.
_claim_lock = threading.Lock()


def arm_next_search() -> None:
    """One explicit owner-authorized next search; refuse to replace an existing arm."""
    folder = ensure_data_dir()
    with (folder / ARM_FILE).open("x", encoding="utf-8") as stream:
        json.dump({"version": 1, "armed": True}, stream)
    if os.name == "posix":
        (folder / ARM_FILE).chmod(0o600)


def is_armed() -> bool:
    """Read-only preparation check; never consume or recreate a missing one-shot arm."""
    marker = ensure_data_dir() / ARM_FILE
    try:
        return (not marker.is_symlink()
                and json.loads(marker.read_text(encoding="utf-8")) == {"version": 1, "armed": True})
    except (OSError, ValueError):
        return False


def claim(search_id: int, notify) -> "Capture | None":
    with _claim_lock:
        return _claim(search_id, notify)


def _claim(search_id: int, notify) -> "Capture | None":
    base = ensure_data_dir()
    marker = base / ARM_FILE
    if not marker.exists():
        return None
    try:
        if marker.is_symlink():
            raise ValueError("Capture arm must be a local regular file")
        if json.loads(marker.read_text(encoding="utf-8")) != {"version": 1, "armed": True}:
            raise ValueError("Invalid capture request")
        root = base / "review-captures"
        if not root.resolve().is_relative_to(base.resolve()):
            raise ValueError("Capture must remain inside the private data folder")
        root.mkdir(mode=0o700, exist_ok=True)
        folder = root / f"search-{search_id}-{uuid4().hex}"
        folder.mkdir(mode=0o700)
        # Atomic claim: another caller cannot consume the same arm.
        marker.replace(folder / "armed.json")
        capture = Capture(folder, notify)
        capture.event("search", search_id=search_id)
        return capture
    except (OSError, ValueError):
        notify("Private comparison capture could not start. The search can continue, but "
               "its missing review evidence will need checking before a comparison.")
        return None


def _json(value):
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def resume(search_id: int, notify) -> "Capture | None":
    """Reopen only this search's already opted-in capture; never consume a new arm."""
    base = ensure_data_dir()
    root = base / "review-captures"
    try:
        if not root.exists():
            return None
        if not root.resolve().is_relative_to(base.resolve()):
            raise ValueError("Capture must remain inside the private data folder")
        folders = list(root.glob(f"search-{search_id}-*"))
        if not folders:
            return None
        if len(folders) != 1:
            raise ValueError("Ambiguous capture")
        folder = folders[0]
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("Capture must be a local directory")
        marker, events = folder / "armed.json", folder / "events.jsonl"
        if marker.is_symlink() or events.is_symlink():
            raise ValueError("Capture must use local regular files")
        if json.loads(marker.read_text(encoding="utf-8")) != {"version": 1, "armed": True}:
            raise ValueError("Invalid original capture request")
        with events.open(encoding="utf-8") as stream:
            first = json.loads(stream.readline())
        if first.get("kind") != "search" or first.get("search_id") != search_id:
            raise ValueError("Different search capture")
        return Capture(folder, notify)
    except (OSError, ValueError, AttributeError):
        notify("Private comparison capture could not resume. Keep the original evidence; "
               "missing continuation evidence must be checked before a comparison.")
        return None


class Capture:
    def __init__(self, folder, notify):
        self.folder = folder
        self.notify = notify
        self._lock = threading.Lock()
        self._failed = False

    def event(self, kind: str, **values) -> None:
        """Capture failure never discards the owner's running search or causes another call."""
        with self._lock:
            if self._failed:
                return
            try:
                record = json.dumps({"kind": kind, "utc": datetime.now(UTC).isoformat(),
                                     "monotonic": time.monotonic(), **values},
                                    ensure_ascii=False, default=_json)
                path = self.folder / "events.jsonl"
                flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
                fd = os.open(path, flags, 0o600)
                with os.fdopen(fd, "a", encoding="utf-8") as stream:
                    stream.write(record + "\n")
            except (OSError, ValueError, TypeError):
                self._failed = True
                self.notify("Private comparison capture stopped saving evidence. Completed "
                            "search work is preserved; do not treat the capture as complete.")

    def call(self, method, *, step: str, provider: str, **arguments):
        attempt = uuid4().hex
        self.event("ai_start", attempt=attempt, step=step, provider=provider,
                   operation=method.__name__, arguments=arguments)
        started = time.monotonic()
        try:
            reply = method(**arguments)
        except Exception as error:
            self.event("ai_end", attempt=attempt, elapsed=time.monotonic() - started,
                       error=type(error).__name__, usage=getattr(error, "usage", None))
            raise
        self.event("ai_end", attempt=attempt, elapsed=time.monotonic() - started, reply=reply)
        return reply
