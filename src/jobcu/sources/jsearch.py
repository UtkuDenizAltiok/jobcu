"""Optional direct JSearch Free account; provider pages/IDs, not HTTP batches, are units.

No enrichment, salary estimates, redirect probing or AI calls. Supplied text enters the same
freshness, duplicate and location gates as other sources. Ambiguously charged requests are
never repeated: an unreadable reply or a second broken connection in a row stops this source;
other feeds continue. Account checks are conservatively reserved as one unit too.
"""

import dataclasses
import ipaddress
import logging
from collections import deque
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from jobcu import db
from jobcu.countries import COUNTRIES
from jobcu.freshness import earliest_possible, freshness, parse_iso, window_start
from jobcu.keystore import KeyStore
from jobcu.settings import load_settings
from jobcu.sources.base import (
    FoundJob,
    JobQuery,
    JobSource,
    SourceContext,
    SourceError,
    SourceReport,
)
from jobcu.sources.budget import (
    BudgetExhausted,
    Limits,
    RequestBudget,
    share_of_month,
    share_until,
)
from jobcu.sources.careers import job_types_from_text
from jobcu.sources.http import KeyCheck, PoliteClient, RequestStopped
from jobcu.text import html_to_text

log = logging.getLogger(__name__)

API = "https://api.openwebninja.com/jsearch"
USAGE = "https://api.openwebninja.com/usage"
KEY_API_KEY = "jsearch_api_key"
KEY_PAGE = "https://www.openwebninja.com/api/jsearch"
MONTHLY_CREDITS = 200
MAX_SEARCH_CREDITS = 40
MAX_PAGES_PER_QUERY = 3
MAX_INTERRUPTIONS = 2  # broken connections in a row before JSearch stops
PRIORITY = ("DE", "IE", "GB", "CH", "NL", "BE", "IT")
_BOARDS = {
    "adzuna",
    "linkedin",
    "indeed",
    "glassdoor",
    "ziprecruiter",
    "monster",
    "google",
    "reed",
    "stepstone",
    "totaljobs",
    "cv-library",
}
_ATS = (
    "myworkdayjobs.com",
    "greenhouse.io",
    "lever.co",
    "personio.de",
    "personio.com",
    "ashbyhq.com",
    "smartrecruiters.com",
    "teamtailor.com",
    "workable.com",
    "recruitee.com",
    "softgarden.io",
    "successfactors.eu",
    "successfactors.com",
)


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _url(value) -> str:
    value = _text(value)
    try:
        p = urlsplit(value)
        host = (p.hostname or "").lower().rstrip(".")
        if (
            p.scheme not in {"https", "http"}
            or not p.hostname
            or "." not in p.hostname
            or p.username is not None
            or p.password is not None
            or p.port not in {None, 443 if p.scheme == "https" else 80}
            or host.endswith((".local", ".localhost", ".internal"))
            or any(c.isspace() for c in value)
            or "\\" in value
        ):
            return ""
        try:
            if not ipaddress.ip_address(host).is_global:
                return ""
        except ValueError:
            # Browsers can interpret shortened/numeric IPv4 forms as local addresses.
            if all(part.isdecimal() or part.lower().startswith("0x") for part in host.split(".")):
                return ""
        return value
    except ValueError:
        return ""


def _direct(url: str, website: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    company = (urlsplit(website).hostname or "").lower().rstrip(".").removeprefix("www.")
    if parsed.path.rstrip("/").lower() in {"", "/jobs", "/careers"} and not parsed.query:
        return False
    if any(part in _BOARDS for part in host.split(".")):
        return False
    return bool(
        (company and (host == company or host.endswith("." + company)))
        or any(host == ats or host.endswith("." + ats) for ats in _ATS)
    )


def to_found_job(item: dict) -> FoundJob | None:
    identity, title = _text(item.get("job_id")), _text(item.get("job_title"))
    website = _url(item.get("employer_website"))
    primary = _url(item.get("job_apply_link"))
    options, direct = [], []
    if primary and item.get("job_apply_is_direct") is True and _direct(primary, website):
        direct.append(primary)
    raw_options = item.get("apply_options")
    for option in raw_options if isinstance(raw_options, list) else []:
        if not isinstance(option, dict) or not (url := _url(option.get("apply_link"))):
            continue
        options.append(
            {"source": "JSearch · " + (_text(option.get("publisher")) or "Job site"), "url": url}
        )
        if option.get("is_direct") is True and _direct(url, website):
            direct.append(url)
    primary = primary or (direct[0] if direct else options[0]["url"] if options else "")
    if not identity or "," in identity or not title or not primary:
        return None
    description = html_to_text(_text(item.get("job_description")))
    stamp = _text(item.get("job_posted_at_datetime_utc"))
    posted = parse_iso(stamp)
    if posted is None:
        epoch = item.get("job_posted_at_timestamp")
        if isinstance(epoch, (int, float)) and not isinstance(epoch, bool):
            try:
                posted = datetime.fromtimestamp(epoch, UTC)
            except (ValueError, OverflowError, OSError):
                pass
    precision = (
        "unknown"
        if posted is None
        else (
            "day"
            if posted.hour == posted.minute == posted.second == posted.microsecond == 0
            or len(stamp) == 10
            else "exact"
        )
    )
    city, state = _text(item.get("job_city")), _text(item.get("job_state"))
    location = _text(item.get("job_location")) or ", ".join(x for x in (city, state) if x)
    country = _text(item.get("job_country")).upper()
    country = "GB" if country == "UK" else country
    types = item.get("job_employment_types")
    type_text = " ".join(t for t in types if isinstance(t, str)) if isinstance(types, list) else ""
    type_text += " " + _text(item.get("job_employment_type"))
    return FoundJob(
        source="jsearch",
        source_job_id=identity,
        url=primary,
        title=title,
        company=_text(item.get("employer_name")) or None,
        location_text=location or None,
        country=country if len(country) == 2 and country.isalpha() else None,
        # The contract does not establish address precision for its coordinates. Let Jobcu
        # locate the named workplace as a town; never upgrade a city centre to an address.
        posted_at=posted,
        date_precision=precision,
        description=description,
        description_is_complete=bool(description and not description.endswith(("…", "..."))),
        job_types=job_types_from_text(type_text),
        work_mode="remote" if item.get("job_is_remote") is True else None,
        employer_url=direct[0] if direct else None,
        salary_text=_text(item.get("job_salary_string")) or None,
        application_options=list({o["url"]: o for o in options}.values()),
    )


def _free_remaining(body: dict) -> int:
    return _free_allowance(body)[0]


def _free_allowance(body: dict) -> tuple[int, datetime]:
    """The Free credits left and when they renew, from a usage receipt."""
    data = body.get("data")
    if not isinstance(data, dict) or data.get("api_id") != "jsearch":
        raise SourceError("JSearch's account check did not identify the expected service.")
    plan = data.get("plan")
    if not isinstance(plan, dict) or plan.get("is_free") is not True:
        raise SourceError("JSearch needs a direct Free account. Jobcu does not use paid plans.")
    status = _text(data.get("status"))
    if status not in {"active", "exceeded"}:
        raise SourceError("JSearch's Free service is not active. Check its account page.")
    quotas = data.get("quotas")
    matches = (
        [q for q in quotas if isinstance(q, dict) and q.get("name") == "Requests"]
        if (isinstance(quotas, list))
        else []
    )
    if len(matches) != 1:
        raise SourceError("JSearch did not report a complete request allowance; no jobs requested.")
    quota = matches[0]
    numbers = [quota.get(k) for k in ("limit", "used", "remaining")]
    if (
        any(type(n) is not int or n < 0 for n in numbers)
        or not 0 < numbers[0] <= MONTHLY_CREDITS
        or numbers[1] + numbers[2] != numbers[0]
    ):
        raise SourceError("JSearch's usage receipt is incomplete; no jobs requested.")
    reset = parse_iso(_text(quota.get("reset_at")))
    if reset is None or reset <= datetime.now(UTC):
        raise SourceError("JSearch did not report a current allowance period; no jobs requested.")
    return (numbers[2] if status == "active" else 0), reset


class Interrupted(SourceError):
    """One request's connection broke; the request is not repeated but other queries go on."""


@dataclass
class Query:
    country: str
    text: str
    language: str
    cursor: str = ""
    pages: int = 0
    cursors: set[str] = dataclasses.field(default_factory=set)


def plan_queries(query: JobQuery, *, offset: int = 0) -> list[Query]:
    countries = sorted(
        set(query.countries) & COUNTRIES.keys(),
        key=lambda c: (PRIORITY.index(c) if c in PRIORITY else len(PRIORITY), c),
    )
    if countries:
        offset %= len(countries)
        countries = countries[offset:] + countries[:offset]
    queues = []
    for country in countries:
        languages = [*COUNTRIES[country].ad_languages, "en"]
        seen, terms = set(), []
        by_language = []
        for language in languages:
            choices = deque()
            for term in sorted(query.terms, key=lambda t: t.kind != "job_title"):
                key = (" ".join(term.text.split()).casefold(), term.language)
                if term.language != language or not key[0] or key in seen:
                    continue
                seen.add(key)
                choices.append(
                    Query(country, f"{term.text.strip()} in {COUNTRIES[country].name}", language)
                )
            by_language.append(choices)
        while any(by_language):
            for choices in by_language:
                if choices:
                    terms.append(choices.popleft())
        queues.append(deque(terms))
    planned = []
    while any(queues):
        for queue in queues:
            if queue:
                planned.append(queue.popleft())
    return planned


class JSearchSource(JobSource):
    id, name, kind = "jsearch", "JSearch", "aggregator"
    details_supply_locations = True
    details_supply_posted_date = True

    def __init__(self):
        self._budget: RequestBudget | None = None
        self._remaining: int | None = None
        self._halted = False
        self._ready = False
        self._key = ""
        self._interrupted_in_a_row = 0

    def unavailable_reason(self, keys: KeyStore) -> str | None:
        return None if keys.get(KEY_API_KEY) else "JSearch: add a direct Free key in Settings."

    def _request(self, url: str, params: dict, ctx: SourceContext) -> dict:
        if self._halted:
            raise SourceError("JSearch stopped after an earlier service or usage problem.")
        assert self._budget is not None
        if url not in {USAGE, f"{API}/search-v2", f"{API}/job-details"}:
            raise SourceError("JSearch refused an unexpected service address.")
        if url != USAGE and not self._ready:
            raise SourceError("JSearch's Free account allowance has not been checked.")

        def check():
            if ctx.should_stop():
                raise RequestStopped("Stopped before a JSearch request.")
            if self._remaining is not None and self._remaining < 1:
                raise BudgetExhausted(
                    "JSearch's Free allowance is used up; other sources continue."
                )
            self._budget.check()

        def spend():
            if ctx.should_stop():
                raise RequestStopped("Stopped before a JSearch request.")
            self._budget.spend()
            ctx.report.requests += 1
            if self._remaining is not None:
                self._remaining -= 1

        try:
            response = ctx.http.get(
                url,
                params=params,
                headers={"x-api-key": self._key},
                cache=False,
                follow_redirects=False,
                retry_transport=False,
                retry_response=lambda _: False,
                check_attempt=check,
                before_attempt=spend,
            )
            if response.status_code in {401, 403}:
                raise SourceError("JSearch did not accept this direct key. Check its Free account.")
            if response.status_code == 429:
                raise SourceError("JSearch reached its service limit. No automatic retry was sent.")
            if response.status_code == 402:
                raise SourceError(
                    "JSearch refused service for billing. No automatic retry was sent."
                )
            if response.status_code != 200:
                raise SourceError(
                    f"JSearch returned code {response.status_code}; this source stopped."
                )
            body = response.json()
            if not isinstance(body, dict) or body.get("status") != "OK":
                raise SourceError("JSearch did not return a complete successful response.")
            self._interrupted_in_a_row = 0
            return body
        except httpx.TransportError as exc:
            # One broken connection lost all of JSearch's jobs in search 9 although the next
            # request worked. The request is never sent again (it may have been charged), but
            # the other queries go on; a second interruption in a row means the service is down.
            log.info("JSearch request interrupted (%s)", type(exc).__name__)
            self._interrupted_in_a_row += 1
            if url == USAGE or self._interrupted_in_a_row >= MAX_INTERRUPTIONS:
                self._halted = True
                raise SourceError(
                    "JSearch's reply was interrupted or unreadable; it was not repeated."
                ) from exc
            raise Interrupted(
                "A JSearch request was interrupted and not repeated; the other queries continued."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._halted = True
            raise SourceError(
                "JSearch's reply was interrupted or unreadable; it was not repeated."
            ) from exc
        except SourceError:
            self._halted = True
            raise

    def _start(self, ctx: SourceContext):
        settings = load_settings()
        if self.id not in settings.source_opt_ins or self.id in settings.sources_disabled:
            raise SourceError("JSearch is switched off. Enable it explicitly in Settings.")
        if self._halted:
            raise SourceError("JSearch stopped after an earlier service or usage problem.")
        if self._ready:
            return
        self._key = ctx.keys.get(KEY_API_KEY) or ""
        if not self._key:
            raise SourceError("JSearch needs a direct Free key in Settings.")
        limits = share_of_month(
            self.id, Limits(per_month=MONTHLY_CREDITS), fewest=2, most=MAX_SEARCH_CREDITS
        )
        self._budget = RequestBudget(self.id, self.name, limits)
        self._budget.used_this_search = ctx.report.requests
        # Avoid spending the last local unit just to learn that no job request can fit.
        self._budget.check(2)
        try:
            self._remaining, renews = _free_allowance(
                self._request(USAGE, {"api_id": self.id}, ctx))
            # The calendar-month share above is only an upper bound: the credits renew on
            # the account's own date, so they are spread until then.
            paced = share_until(self._remaining, renews, fewest=2, most=MAX_SEARCH_CREDITS)
            self._budget.limits = replace(
                limits, per_search=min(limits.per_search or paced, paced))
            self._ready = True
        except SourceError:
            self._halted = True
            raise

    def search(self, query: JobQuery, ctx: SourceContext):
        if not plan_queries(query):
            return
        try:
            self._start(ctx)
            left = min(
                self._remaining or 0, self._budget.limits.per_search - self._budget.used_this_search
            )
            # A small allowance rotates the first countries between searches; a large one
            # uses the owner's normal order. Plans within a country are also interleaved.
            with db.connect() as conn:
                sequence = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
            planned = plan_queries(query, offset=sequence if left < len(query.countries) else 0)
            queue = deque(planned)
            seen = set()
            reserve = 2 if left >= 4 else 0  # selective full-ad recovery shares the same cap
            maximum = self._budget.used_this_search + max(0, left - reserve)
            while queue and not ctx.should_stop():
                if self._budget.used_this_search >= maximum:
                    ctx.report.status = "partial"
                    ctx.report.message = (
                        "JSearch stopped at its discovery allowance; some queries/pages remain. "
                        "Other sources continue and full ads share the same credit ceiling."
                    )
                    break
                current = queue.popleft()
                params = {
                    "query": current.text,
                    "country": current.country.lower(),
                    "language": current.language,
                    "num_pages": 1,
                    # JSearch's relative filters are looser than their names (2026-10-24: "3days"
                    # returned ads stamped 88-184 hours old), so the tightest filter covering the
                    # window loses no fresh ad and leaves more of each page inside the window
                    # ("week" left 62 of 109 results too old for a 72-hour search).
                    "date_posted": "3days" if query.posted_within_hours <= 72 else "week",
                }
                if current.cursor:
                    params["cursor"] = current.cursor
                try:
                    data = self._request(f"{API}/search-v2", params, ctx).get("data")
                except Interrupted as exc:
                    ctx.report.status, ctx.report.message = "partial", str(exc)
                    continue
                if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                    self._halted = True
                    raise SourceError("JSearch's results were incomplete; this source stopped.")
                for item in data["jobs"]:
                    if not isinstance(item, dict) or not (job := to_found_job(item)):
                        ctx.report.status = "partial"
                        ctx.report.message = (
                            "Some JSearch records lacked usable job identity or links."
                        )
                        continue
                    job.source_context = {
                        "country": current.country.lower(),
                        "language": current.language,
                    }
                    fingerprint = (
                        job.source_job_id,
                        job.url,
                        job.description,
                        job.posted_at,
                        job.employer_url,
                        job.country,
                        job.location_text,
                        tuple((o["url"], o["source"]) for o in job.application_options),
                    )
                    if fingerprint in seen:
                        continue
                    seen.add(fingerprint)
                    job.older_copy = (
                        freshness(
                            job.posted_at,
                            job.date_precision,
                            window_start(query.started_at, query.posted_within_hours),
                        )
                        == "too_old"
                    )
                    yield job
                current.pages += 1
                cursor = data.get("cursor")
                if cursor is not None and not isinstance(cursor, str):
                    self._halted = True
                    raise SourceError(
                        "JSearch returned an invalid continuation; this source stopped."
                    )
                if cursor:
                    if cursor in current.cursors or current.pages >= MAX_PAGES_PER_QUERY:
                        ctx.report.status = "partial"
                        ctx.report.message = (
                            "Some JSearch result pages remain outside this search's allowance."
                        )
                    else:
                        current.cursors.add(cursor)
                        current.cursor = cursor
                        queue.append(current)
        except BudgetExhausted as exc:
            ctx.report.status, ctx.report.message = "partial", exc.message

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        locale = {
            k: job.source_context[k] for k in ("country", "language") if job.source_context.get(k)
        }
        if "country" not in locale and job.country:
            locale["country"] = job.country.lower()
        if locale.get("country", "").upper() not in COUNTRIES or "," in job.source_job_id:
            raise SourceError("JSearch's lookup country is missing; earlier evidence kept.")
        self._start(ctx)
        body = self._request(f"{API}/job-details", {"job_id": job.source_job_id, **locale}, ctx)
        data = body.get("data")
        matches = (
            [i for i in data if isinstance(i, dict) and i.get("job_id") == job.source_job_id]
            if isinstance(data, list)
            else []
        )
        if len(matches) != 1 or not (full := to_found_job(matches[0])):
            self._halted = True
            raise SourceError(
                "JSearch's details did not match this vacancy; earlier evidence kept."
            )
        # A failed/shorter details response cannot erase already retrieved evidence.
        updates = {
            k: v
            for k, v in dataclasses.asdict(full).items()
            if v not in (None, "", [])
            and k not in {"older_copy", "posted_at", "date_precision", "source_context"}
        }
        if (
            not full.description
            or (not full.description_is_complete and job.description_is_complete)
            or (len(full.description) < len(job.description)
                and (job.description_is_complete or not full.description_is_complete))
        ):
            updates.pop("description", None)
            updates.pop("description_is_complete", None)
        if full.posted_at and (
            not job.posted_at
            or earliest_possible(full.posted_at, full.date_precision)
            < earliest_possible(job.posted_at, job.date_precision)
        ):
            updates.update(posted_at=full.posted_at, date_precision=full.date_precision)
        updates["application_options"] = list(
            {o["url"]: o for o in [*job.application_options, *full.application_options]}.values()
        )
        return dataclasses.replace(job, **updates)


def check_keys(keys: KeyStore) -> KeyCheck:
    key = keys.get(KEY_API_KEY)
    if not key:
        return KeyCheck(False, "Save your direct JSearch Free key first.")
    source = JSearchSource()
    source._key = key
    source._budget = RequestBudget(
        source.id, source.name, Limits(per_search=1, per_month=MONTHLY_CREDITS)
    )
    http = PoliteClient()
    ctx = SourceContext(
        http, keys, SourceReport(source.id, source.name), lambda: False, lambda message: None
    )
    try:
        remaining = _free_remaining(source._request(USAGE, {"api_id": source.id}, ctx))
        return KeyCheck(
            bool(remaining),
            f"JSearch Free account checked: {remaining} credits remain. "
            "No job query was sent. "
            + (
                "Enable JSearch under Job sources when ready."
                if remaining
                else "Wait for the allowance to reset on its account page."
            ),
        )
    except (SourceError, BudgetExhausted) as exc:
        return KeyCheck(False, str(exc))
    finally:
        http.close()
