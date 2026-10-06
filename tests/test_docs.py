import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = sorted(
    [*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md"), *(ROOT / ".github").rglob("*.md")]
)
LINK = re.compile(r"\]\(([^)\s]+)\)")


def _anchors(path):
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)', text))
    seen = Counter()
    fenced = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
        if fenced:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            slug = re.sub(r"[^\w\- ]", "", heading[1].lower()).replace(" ", "-")
            anchors.add(f"{slug}-{seen[slug]}" if seen[slug] else slug)
            seen[slug] += 1
    return anchors


@pytest.mark.parametrize("doc", MARKDOWN_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_links_between_documents_work(doc):
    for target in LINK.findall(doc.read_text(encoding="utf-8")):
        link = urlsplit(target)
        if link.scheme or link.netloc:
            continue  # external links are checked when their facts change
        path = (doc.parent / unquote(link.path)).resolve() if link.path else doc
        assert path.exists(), f"{doc.relative_to(ROOT)} links to missing {target}"
        if link.fragment and path.suffix == ".md":
            assert unquote(link.fragment) in _anchors(path), (
                f"{doc.relative_to(ROOT)} links to missing section {target}"
            )


# The records stay usable after any interruption only if their structure holds (AGENTS.md,
# "Information homes" and "Sessions").

def _project_map() -> str:
    text = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    return text.split("## Project layout", 1)[1].split("## Evaluation data and timing", 1)[0]


def test_the_project_map_lists_every_module_and_tool():
    listed = _project_map()
    package = ROOT / "src" / "jobcu"
    names = [p.name for p in package.glob("*.py") if p.name != "__init__.py"]
    names += [f"{p.name}/" for p in package.iterdir() if p.is_dir() and not p.name.startswith("_")]
    names += [f"tools/{p.name}" for p in (ROOT / "tools").glob("*.py")]
    missing = [name for name in names if name not in listed]
    assert not missing, f"ARCHITECTURE.md's project map doesn't mention {missing}"


def test_progress_keeps_the_sections_a_new_session_needs():
    text = (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    right_now = text.split("## Right now", 1)[1].split("\n## ", 1)[0]
    assert re.search(r"\*Updated \d{4}-\d{2}-\d{2}\.", right_now)
    for section in ("State", "In progress", "Verify before relying on", "Waiting on the owner",
                    "Next tasks", "Known limitations"):
        assert f"### {section}" in right_now, f"'Right now' lost its '{section}' section"


def test_the_prompts_for_ai_assistants_point_at_real_sections():
    prompts = " ".join((ROOT / "docs" / "PROMPTS.md").read_text(encoding="utf-8").split())
    rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for section in ("Starting, or resuming after any interruption", "Ending a session"):
        assert section in prompts and f"### {section}" in rules
