"""The employer's own posting of a job that came only from job sites.

Jobcu reads many employers' career sites itself (careers.py and the directory). Some systems list
jobs newest first, and a search stops reading at the first page of jobs older than its window
(Workday). A job such an employer posted weeks ago, which a job site listed again, came in from
the job site alone: without the employer's link, with the job site's text (often cut short) and
the job site's date. In one saved list, six of the person's best cards were such jobs, 14 to 30
and more days old on the employers' own lists.

Before the full ads are read, each job still in the running that has no employer copy, and whose
employer Jobcu reads on a system that can find a title (Workday's and Oracle's own search; the
whole SuccessFactors list a search reads anyway, every title in its addresses), is looked up
there: the listed jobs for the job's title, the full ads of the closest titles in
the job's country (at most MAX_READ), and the first that Jobcu's duplicate rules take for the
same job (`dedupe.group_duplicates`: the same company, place and title, and matching text) joins
it as its employer copy. The card then leads to the employer's page, scoring reads the
employer's full ad, and a listing older than the window makes the job a repost with the
employer's date (`filters.first_posted_by_employer`). The requests go to the same public list the
search reads, through the same polite client and request budget; no job site is asked and no AI.
"""

import dataclasses
import logging
import re
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from jobcu import dedupe
from jobcu.dedupe import JobGroup
from jobcu.freshness import freshness
from jobcu.sources.base import FoundJob, SourceContext, SourceError, SourceReport
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer, all_employers, job_countries
from jobcu.sources.http import Blocked, RequestStopped

log = logging.getLogger(__name__)

MAX_READ = 3  # full ads read per job: the closest titles the site's search lists
PARALLEL = 4  # employers looked up at once; each site keeps its polite pace


def employer_of(group: JobGroup, employers: dict[str, Employer]) -> Employer | None:
    """The employer Jobcu reads whose name the job's company is, or contains as whole words
    ("Leonardo UK" is Leonardo's). The duplicate rules decide later whether a listing is the job."""
    company = dedupe.normal_company(group.main.company)
    if not company:
        return None
    return employers.get(company) or next(
        (employer for name, employer in employers.items()
         if len(name) > 4 and re.search(rf"\b{re.escape(name)}\b", company)), None)


def needs_posting(group: JobGroup) -> bool:
    return not any(group.source_kinds.get(copy.source) == "employer" for copy in group.copies)


def find(groups: list[JobGroup], indexes: list[int], sources: dict, http, keys,
         reports: dict[str, SourceReport], should_stop: Callable[[], bool],
         note: Callable[[str], None], start: datetime) -> int:
    """Adds the employer's own posting to each job among `indexes` whose posting is found on a
    career site Jobcu reads; returns how many were found. `start` is the window's start."""
    searchable = {source.system: source for source in sources.values()
                  if isinstance(source, CareerSystemSource) and source.finds_by_title}
    if not searchable:
        return 0
    employers: dict[str, Employer] = {}
    for employer in all_employers():
        if employer.system in searchable:
            employers.setdefault(dedupe.normal_company(employer.name), employer)
    work: dict[tuple[str, str], list[int]] = defaultdict(list)
    chosen: dict[tuple[str, str], Employer] = {}
    for index in dict.fromkeys(indexes):
        group = groups[index]
        if not needs_posting(group):
            continue
        employer = employer_of(group, employers)
        country = _country(group)
        if employer is None or (country and country not in employer.countries):
            continue
        key = (employer.system, employer.board)
        chosen[key] = employer
        work[key].append(index)

    def look(key: tuple[str, str]) -> tuple[int, int]:
        employer = chosen[key]
        source = searchable[employer.system]
        report = reports.get(source.id) or SourceReport(source.id, source.name)
        ctx = SourceContext(http, keys, report, should_stop, note)
        found = 0
        for index in work[key]:
            if ctx.should_stop():
                break
            try:
                posting = _posting(groups[index], employer, source, ctx, start)
            except (BudgetExhausted, Blocked, RequestStopped):
                break
            except SourceError as exc:  # its list can't be read now (robots, an outage)
                log.info("Employer's posting: %s couldn't be searched: %s", employer.name, exc)
                break
            except Exception:  # one employer's answer never stops the search
                log.exception("Employer's posting: looking up %s failed", employer.name)
                break
            if posting is not None:
                groups[index].copies.append(posting)
                groups[index].source_kinds = {**groups[index].source_kinds,
                                              posting.source: "employer"}
                found += 1
        return found, len(work[key])

    if not work:
        return 0
    with ThreadPoolExecutor(max_workers=PARALLEL, thread_name_prefix="employer-postings") as pool:
        results = list(pool.map(look, list(work)))
    found = sum(f for f, _ in results)
    log.info("Employers' own postings: %d found for %d jobs of %d employers", found,
             sum(n for _, n in results), len(work))
    return found


def _country(group: JobGroup) -> str | None:
    return next((copy.country for copy in group.copies if copy.country), None)


def _posting(group: JobGroup, employer: Employer, source: CareerSystemSource,
             ctx: SourceContext, start: datetime) -> FoundJob | None:
    title = dedupe.normal_title(dedupe._AD_PREFIX.sub("", group.main.title))
    if not title:
        return None
    listed = source.find_by_title(employer, title, ctx)
    country = _country(group)
    # A list that names a job's country tells another country's vacancy apart before its full
    # ad is read (a title search answers from every country the employer hires in).
    alike = sorted(
        ((dedupe.title_similarity(title, dedupe.normal_title(job.title)), job) for job in listed
         if not country or not (places := job_countries(job)) or country in places),
        key=lambda pair: -pair[0])
    for similarity, job in alike[:MAX_READ]:
        if similarity < dedupe.TITLE_MATCH_WITH_TEXT:
            break
        full = source.load_details(dataclasses.replace(job, job_types=list(job.job_types)), ctx)
        if not (full.description or "").strip():
            continue  # a page without the ad (the job closed, or it didn't load) proves nothing
        places = job_countries(dataclasses.replace(full, country=None))
        if country and country not in places:
            continue  # the same title in another country is another vacancy
        full = dataclasses.replace(
            full, country=country or full.country, employer_url=full.employer_url or full.url,
            older_copy=freshness(full.posted_at, full.date_precision, start) == "too_old")
        kinds = {**group.source_kinds, full.source: "employer"}
        trial = dedupe.group_duplicates([*group.copies, full], kinds)
        if any(len(found.copies) > 1 and any(copy is full for copy in found.copies)
               for found in trial):
            return full
    return None
