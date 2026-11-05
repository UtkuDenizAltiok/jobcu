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
# Lines a merge leaves when both sides were kept (the roadmap kept them on 2026-11-05).
CONFLICT = re.compile(r"^(<<<<<<<|>>>>>>>) ", re.MULTILINE)


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


def _project_map() -> str:
    text = (ROOT / "docs" / "ENGINEERING.md").read_text(encoding="utf-8")
    return text.split("## Project layout", 1)[1]


def test_the_project_map_lists_every_module_and_tool():
    listed = _project_map()
    package = ROOT / "src" / "jobcu"
    names = [p.name for p in package.glob("*.py") if p.name != "__init__.py"]
    names += [f"{p.name}/" for p in package.iterdir() if p.is_dir() and not p.name.startswith("_")]
    names += [f"tools/{p.name}" for p in (ROOT / "tools").glob("*.py")]
    missing = [name for name in names if name not in listed]
    assert not missing, f"ENGINEERING.md's project map doesn't mention {missing}"


def test_no_file_keeps_the_marks_of_an_unfinished_merge():
    files = [*MARKDOWN_FILES, *(ROOT / "src").rglob("*.*"), *(ROOT / "tests").rglob("*.py"),
             *(ROOT / "tools").rglob("*.py")]
    for path in files:
        if path.suffix in {".py", ".md", ".js", ".css", ".html", ".json", ".toml"}:
            text = path.read_text(encoding="utf-8")
            assert not CONFLICT.search(text), f"{path.relative_to(ROOT)} has merge marks"
