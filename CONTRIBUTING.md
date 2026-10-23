# Develop Jobcu

Jobcu is a local Python application with a plain browser UI. No JavaScript build step is
required. The implementation map is in
[ENGINEERING.md](docs/ENGINEERING.md#project-layout).

## Setup

Use Python 3.13, Git and uv. From the repository root:

```bash
uv sync --locked
git config core.hooksPath .githooks
uv run jobcu
```

The Mac and Windows launchers provide the normal user entry points. The launcher checks for
updates on clean main; uncommitted edits are not mirrored to GitHub automatically.

## Checks and publication

```bash
uv run ruff check .
uv run pytest
uv run python tools/check_no_secrets.py --all
git diff --check
```

Tests use disposable fictional data and mocked provider/source traffic. They need no API keys.
`tests/test_docs.py` checks local links and the module/tool map. JavaScript changes also need a
syntax check. GitHub runs the full suite and launcher checks on macOS and Windows, plus the
privacy guard.

For isolated startup checks, set `JOBCU_DATA_DIR` to a disposable directory outside every Git
checkout, `JOBCU_NO_BROWSER=1` and `JOBCU_SELFTEST=1`. Normal app port: 8765; preview port: 8799.


## Private data

Jobcu stores private data outside the checkout, using the platform data directory unless
`JOBCU_DATA_DIR` is set. On macOS the default is `~/Library/Application Support/Jobcu`; Windows
uses the platform's local application-data directory. `paths.ensure_data_dir()` enforces the
repository boundary. Keys, settings, documents, saved searches, reviews, logs and captures must
never be copied into Git or public output.

## Tools

The [tool index](docs/ENGINEERING.md#tools) describes the maintained utilities. Some tools are
read-only and offline; others can make source/provider requests. Their command-line help and
code define the options.

The user-facing setup and troubleshooting guides are linked from [README](README.md#use-jobcu).
