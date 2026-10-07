"""The free benchmark must use disposable fiction, even with a configured data folder."""

import importlib.util
from contextlib import contextmanager
from pathlib import Path

import pytest

from jobcu import db, paths

TOOL = Path(__file__).resolve().parents[1] / "tools" / "benchmark_local_matching.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("benchmark_local_matching", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_benchmark_never_opens_configured_data_and_restores_the_folder(monkeypatch):
    configured = paths.data_dir()
    with db.connect() as conn:
        conn.execute("INSERT INTO jobs (id, title) VALUES (1, 'Fictional saved job')")
    original = db.connect
    temporary = set()

    @contextmanager
    def guarded(*args, **kwargs):
        folder = paths.data_dir()
        assert folder != configured
        temporary.add(folder.parent)
        with original(*args, **kwargs) as conn:
            yield conn

    monkeypatch.setattr(db, "connect", guarded)
    result = load_tool().benchmark("HEAD", jobs=3, ads=3, rounds=1)
    assert result["fictional_only"]
    assert result["repeat_identity_lookup"]["same_ids"]
    assert result["full_ad_comparison"]["same_groups"]
    assert paths.data_dir() == configured and configured.exists()
    assert temporary and all(not folder.exists() for folder in temporary)
    with original() as conn:
        assert conn.execute("SELECT title FROM jobs").fetchone()[0] == "Fictional saved job"


def test_benchmark_failure_restores_configuration_and_deletes_only_temporary_data():
    configured = paths.ensure_data_dir()
    marker = configured / "fictional-preserved.txt"
    marker.write_text("Fictional saved data", encoding="utf-8")
    tool = load_tool()
    with pytest.raises(RuntimeError, match="Simulated failure"):
        with tool.fictional_data():
            temporary = paths.ensure_data_dir()
            assert temporary != configured
            raise RuntimeError("Simulated failure")
    assert not temporary.exists()
    assert paths.data_dir() == configured
    assert marker.read_text(encoding="utf-8") == "Fictional saved data"
