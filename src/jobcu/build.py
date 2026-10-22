"""A fingerprint of Jobcu's code, so a newer copy can recognise an older one still running."""

import hashlib
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parent


def _fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(_PACKAGE.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".html", ".css", ".js", ".svg", ".json"}:
            digest.update(path.relative_to(_PACKAGE).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


# Bind identity when this process imports the application, before its first health request.
# Reading changed files lazily would let old loaded Python report a newer checkout's build.
_PROCESS_BUILD = _fingerprint()


def build_id() -> str:
    return _PROCESS_BUILD
