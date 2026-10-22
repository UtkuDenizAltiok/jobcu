"""An old process must not identify itself as newly edited code on its first health read."""

import runpy
from pathlib import Path

import pytest

from jobcu import build


@pytest.mark.parametrize("filename", ["app.py", "app.js", "index.html"])
def test_update_before_first_health_read_is_detected_by_a_new_launcher(tmp_path, filename):
    package = tmp_path / "fictional-package"
    package.mkdir()
    script = package / "build.py"
    script.write_text(Path(build.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    asset = package / filename
    asset.write_text("fictional old implementation", encoding="utf-8")
    running_process = runpy.run_path(str(script))
    # Simulate an update while an app is open, before anybody asks /api/health.
    asset.write_text("fictional new implementation", encoding="utf-8")
    replacement_process = runpy.run_path(str(script))
    old_build, new_build = running_process["build_id"](), replacement_process["build_id"]()
    assert old_build != new_build
    # More health requests cannot make either loaded process change identity.
    assert running_process["build_id"]() == old_build
    unchanged_restart = runpy.run_path(str(script))
    assert replacement_process["build_id"]() == unchanged_restart["build_id"]()
