"""Oracle Recruiting Cloud career sites (Texas Instruments, onsemi, Vertiv and others), checked
2026-09-30.

A company's Oracle career site ("Candidate Experience") loads its job list from a public address
on the company's Oracle host:

    GET https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions
        ?onlyData=true&expand=requisitionList.secondaryLocations
        &finder=findReqs;siteNumber={site},limit=100,offset=0,sortBy=POSTING_DATES_DESC

It answers newest first with each job's title, posting day, main place and its country code, and
any other places. A job's own record (`recruitingCEJobRequisitionDetails`, finder `ById`) has
the full ad in parts, the exact posting time and the working time ("Full time"). The hosts
checked have no robots.txt; Jobcu asks for it all the same. The board is written
"host/site", for example "hctz.fa.us2.oraclecloud.com/CX_1001" (onsemi).
"""

import dataclasses
from collections.abc import Iterator
from datetime import date

from jobcu.freshness import day_at_utc, parse_iso
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import (
    CareerSystemSource,
    Employer,
    job_types_from_text,
    work_mode_from_text,
)
from jobcu.text import html_to_text, tidy

LIST = "https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
DETAILS = "https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
PAGE = "https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{id}"
PAGE_SIZE = 100
MAX_PAGES = 10  # 1,000 newest jobs: well over a week for the biggest sites checked
_AD_PARTS = ("ExternalDescriptionStr", "ExternalResponsibilitiesStr",
             "ExternalQualificationsStr")


class OracleSource(CareerSystemSource):
    id = "oracle"
    name = "Company career sites (Oracle)"
    system = "oracle"
    parallel = 4  # every employer has its own host

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        host, site = _board(employer)
        address = LIST.format(host=host)
        if not self.allowed(address, ctx):
            raise SourceError(f"{host} asks automated tools not to read its job list.")
        for page in range(MAX_PAGES):
            finder = (f"findReqs;siteNumber={site},limit={PAGE_SIZE},offset={page * PAGE_SIZE},"
                      "sortBy=POSTING_DATES_DESC")
            data = self.get_json(address, ctx, params={
                "onlyData": "true", "expand": "requisitionList.secondaryLocations",
                "finder": finder})
            search = (data.get("items") or [{}])[0]
            jobs = search.get("requisitionList") or []
            for item in jobs:
                job = to_found_job(item, host, site, employer)
                if job is None:
                    continue
                if start is not None and job.posted_at is not None and (
                        job.posted_at.date() < start.date()):
                    return  # newest first: everything after this is older still
                yield job
            if len(jobs) < PAGE_SIZE or (page + 1) * PAGE_SIZE >= int(
                    search.get("TotalJobsCount") or 0):
                return

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        host, _, rest = job.source_job_id.partition("/")
        site, _, job_id = rest.rpartition("/")
        try:
            data = self.get_json(DETAILS.format(host=host), ctx, params={
                "onlyData": "true", "expand": "all",
                "finder": f'ById;Id="{job_id}",siteNumber={site}'})
        except (SourceError, BudgetExhausted):
            return job
        info = (data.get("items") or [{}])[0]
        parts = [html_to_text(info.get(part)) for part in _AD_PARTS]
        description = tidy("\n\n".join(part for part in parts if part))
        if not description:
            return job
        posted = parse_iso(info.get("ExternalPostedStartDate"))
        return dataclasses.replace(
            job,
            description=description,
            description_is_complete=True,
            posted_at=posted or job.posted_at,
            date_precision="exact" if posted else job.date_precision,
            job_types=job_types_from_text(info.get("JobSchedule")) or job.job_types,
            work_mode=work_mode_from_text(info.get("WorkplaceType")) or job.work_mode,
        )


def _board(employer: Employer) -> tuple[str, str]:
    host, _, site = employer.board.partition("/")
    return host, site or "CX"


def to_found_job(item: dict, host: str, site: str, employer: Employer) -> FoundJob | None:
    job_id = str(item.get("Id") or "").strip()
    title = tidy(item.get("Title") or "")
    if not job_id or not title:
        return None
    places = [(item.get("PrimaryLocation"), item.get("PrimaryLocationCountry"))]
    places += [(place.get("Name"), place.get("CountryCode"))
               for place in item.get("secondaryLocations") or [] if isinstance(place, dict)]
    names = [tidy(name) for name, _ in places if name]
    codes = {(code or "").upper() for _, code in places} - {""}
    # One country gives the job's country; places in several are told apart by their names.
    country = next(iter(codes)) if len(codes) == 1 else None
    try:
        day = date.fromisoformat(item.get("PostedDate") or "")
    except ValueError:
        day = None
    return FoundJob(
        source="oracle",
        source_job_id=f"{host}/{site}/{job_id}",
        url=PAGE.format(host=host, site=site, id=job_id),
        title=title,
        company=employer.name,
        location_text="; ".join(dict.fromkeys(names)) or None,
        country=country,
        posted_at=day_at_utc(day) if day else None,
        date_precision="day" if day else "unknown",
        work_mode=work_mode_from_text(item.get("WorkplaceType")),
    )
