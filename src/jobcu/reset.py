"""Deliberate local deletion, with settings and service allowances preserved."""

import logging
import shutil
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jobcu import db, search
from jobcu.keystore import KEYS_FILENAME
from jobcu.logs import setup_logging
from jobcu.paths import ensure_data_dir
from jobcu.settings import SETTINGS_FILENAME, load_settings, save_settings

Scope = Literal["search", "review", "all"]
router = APIRouter(prefix="/api")

# Children before parents. Review samples have their own reset and survive a search reset.
SEARCH_TABLES = (
    "application_link_reports", "job_states", "job_cards", "job_fingerprints", "job_keys",
    "search_results", "search_pool", "jobs", "searches", "profile_cache", "ad_texts",
    "travel_memory", "found_employers", "employer_searches",
)
KEEP_FILES = {
    SETTINGS_FILENAME, KEYS_FILENAME, "assistant-authorization.json", "README.txt",
    db.DB_FILENAME, db.DB_FILENAME + "-wal", db.DB_FILENAME + "-shm",
    db.DB_FILENAME + "-journal",
}


class ResetBusy(Exception):
    pass


class Mutations:
    """Reject resets during uploads/provider checks; reject writes during a reset."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = 0
        self._resetting = False

    @contextmanager
    def enter(self, *, reset: bool) -> Iterator[None]:
        with self._lock:
            if self._resetting or (reset and self._active):
                raise ResetBusy
            self._active += 1
            self._resetting = reset
        try:
            yield
        finally:
            with self._lock:
                self._active -= 1
                if reset:
                    self._resetting = False


class ResetRequest(BaseModel):
    scope: Scope
    confirm: Literal["RESET"]


@router.post("/data/reset")
def reset_data(body: ResetRequest) -> dict:
    try:
        completed = search.manager.reset(
            lambda: clear_data(body.scope), clear_search=body.scope != "review"
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=500, detail=_failed_message()) from exc
    if not completed:
        raise HTTPException(status_code=500, detail=_failed_message())
    return {"reset": True, "scope": body.scope}


def _failed_message() -> str:
    return ("The reset could not finish. Some data may already be cleared. "
            "Reload the page and try the same reset again.")


def clear_data(scope: Scope) -> bool:
    """Called only with the manager idle and competing API writes excluded.

    Database errors roll back the deletion. A file/compaction error after that commit is
    reported as incomplete, with the current search forgotten so it cannot restore old data.
    No provider calls are made. Files outside the private data folder are never traversed.
    """
    folder = ensure_data_dir()
    if db.db_path(folder).is_symlink():
        raise OSError("The database must be inside the data folder.")
    with db.connect(folder) as conn:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        if tables != set(SEARCH_TABLES) | {"quality_ads", "ai_usage", "source_requests"}:
            raise OSError("Unrecognized data tables; preserve them rather than omit a reset.")
        conn.execute("PRAGMA secure_delete = ON")
        conn.execute("BEGIN IMMEDIATE")
        if scope != "review":
            # Spending is real even after its search is deleted. Remove the old association
            # so a reused SQLite search ID cannot inherit another search's usage.
            conn.execute("UPDATE ai_usage SET search_id = NULL")
            for table in SEARCH_TABLES:
                conn.execute(f"DELETE FROM {table}")
            settings = load_settings(folder)
            settings.search_form.location_text = ""
            settings.search_form.about_you = ""
            save_settings(settings, folder)
        if scope != "search":
            conn.execute("DELETE FROM quality_ads")

    completed = True
    if scope == "all":
        restart_logging = False
        try:
            restart_logging = _close_log_files(folder)
            for path in folder.iterdir():
                if path.name in KEEP_FILES:
                    continue
                try:
                    if path.is_symlink() or not path.is_dir():
                        path.unlink()
                    else:
                        shutil.rmtree(path)
                except OSError:
                    completed = False
        except OSError:
            completed = False
        finally:
            if restart_logging:
                try:
                    setup_logging()
                except OSError:
                    completed = False
    try:
        # Compact committed pages as well as clearing rows. This is local deletion, not a
        # guarantee of forensic erasure from SSDs, OS snapshots or external backups.
        with db.connect(folder) as conn:
            conn.execute("VACUUM")
    except (OSError, sqlite3.Error):
        completed = False
    return completed


def _close_log_files(folder: Path) -> bool:
    restart = False
    root = logging.getLogger()
    for handler in tuple(root.handlers):
        filename = getattr(handler, "baseFilename", None)
        if filename and Path(filename) == folder / "logs" / "jobcu.log":
            root.removeHandler(handler)
            handler.close()
            restart = True
    return restart
