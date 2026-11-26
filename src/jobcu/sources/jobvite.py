"""Jobvite career sites, checked 2026-11-26 (SOURCES.md).

A company's list page, `https://jobs.jobvite.com/{company}/jobs`, links every open job
(`/{company}/job/{id}`) under its title, with its place beside it, and each job's page carries the
standard job data (JobPosting: title, posting day, country, the whole ad). The host has no
robots.txt (no rules). It is read like other employers' own list pages (listpages.py): the whole
list once a search, the pages of the titles that match the search words, titles new on the list
to the person's AI. Power Integrations' gate-driver development in Ense is on it.

Jobvite's terms of use forbid scraping content "on or through" its site, so the source is read
only for a person who switches it on in Settings and so accepts that for their own job search
(sources.TERMS_NOTES); no legal action against readers of job pages was found.
"""

import dataclasses
import re

from jobcu.sources.base import SourceContext
from jobcu.sources.careers import Employer
from jobcu.sources.listpages import ListPageSource
from jobcu.sources.sitemaps import Listed

_COMPANY = re.compile(r"jobs\.jobvite\.com/([A-Za-z0-9_-]+)")


def job_pattern(board: str) -> str | None:
    """The address pattern of a Jobvite company's job pages, from its list's address."""
    match = _COMPANY.search(board or "")
    return rf"jobs\.jobvite\.com/{re.escape(match.group(1))}/job/(\w+)" if match else None


class JobviteSource(ListPageSource):
    id = "jobvite"
    name = "Company career sites (Jobvite)"
    system = "jobvite"

    def _listing(self, employer: Employer, ctx: SourceContext, languages: list[str]
                 ) -> list[Listed]:
        # A list learned from a job's link has no pattern in the directory: Jobvite's is known.
        if not employer.jobs:
            employer = dataclasses.replace(employer, jobs=job_pattern(employer.board))
        return super()._listing(employer, ctx, languages)
