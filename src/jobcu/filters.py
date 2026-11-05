"""The free rules filter: objective facts only, no AI.

A job is left out only when a fact proves it doesn't fit:
- it was marked Not interested before
- it's proven older than "Posted within": by its earliest copy's date, or because Jobcu
  already showed it in a search before that time began (a job posted again looks new). A
  source that lists ads days after their date (JSearch) doesn't prove that within its lag:
  the job is new to this search unless Jobcu showed it before.
- its closing date for applications has passed
- the source states a job type the user didn't tick
- the source states it's fully remote and remote jobs are excluded
- the source states a country outside the countries searched
- a location condition the AI checked says this place doesn't fit (for example a town that is
  too small, one the person asked to avoid, or too far from the places a condition measures
  to). A job whose place can't be recognised is kept and shown as "not checked" on its card.

Every left-out job is counted with its reason, for "Search details".
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from jobcu import applications, travel, vacancy_evidence
from jobcu.dedupe import JobGroup
from jobcu.freshness import freshness, window_start
from jobcu.jobstore import JobState
from jobcu.location import fits
from jobcu.placenames import names_an_office

REASONS = {
    **vacancy_evidence.REASONS,
    "dismissed": "Marked Not interested before",
    "location_condition": "The place doesn't fit a condition you wrote",
    "too_old": "Older than your \"Posted within\" choice",
    "repost": "Posted again: Jobcu saw it before your \"Posted within\" time",
    "shown_before": "Shown in an earlier search already",
    "closed": "The closing date for applications has passed",
    "job_type": "A job type you didn't tick",
    "remote": "Fully remote (you excluded remote jobs)",
    "country": "In a country you didn't search",
    "application_route": applications.EXCLUSION_REASON,
    "reported_application_route": applications.REPORTED_EXCLUSION_REASON,
}


@dataclass
class FilterOutcome:
    kept: list[int] = field(default_factory=list)  # indexes into the groups
    left_out: Counter = field(default_factory=Counter)
    # Which jobs each reason left out, so the screen can show them if it wants to.
    by_reason: dict[str, list[int]] = field(default_factory=dict)
    # Jobs left out only because Jobcu showed them before the window began, now dated inside it:
    # the search may list them again as reposted (search._reposted_cards).
    reposted: list[int] = field(default_factory=list)


def apply_rules(
    groups: list[JobGroup],
    remembered_states: list[JobState | None],
    *,
    started_at: datetime,
    posted_within_hours: int,
    job_types: list[str],
    exclude_remote: bool,
    countries: list[str],
    conditions: list | None = None,
    first_shown: list[datetime | None] | None = None,
) -> FilterOutcome:
    """`first_shown` says when Jobcu first listed each job with its score and a checked place,
    if ever (jobstore.first_assessed)."""
    outcome = FilterOutcome()
    start = window_start(started_at, posted_within_hours)
    wanted_types = set(job_types)
    reported = applications.reported_urls()
    original = vacancy_evidence.group_reasons(groups, start)
    for index, group in enumerate(groups):
        args = (group, remembered_states[index], start, wanted_types, exclude_remote,
                set(countries), conditions or [], started_at)
        reason = original.get(index) or _reason(
            *args, first_shown[index] if first_shown else None, reported)
        if (reason == "repost" and index not in original
                and freshness(group.posted_at, group.date_precision, start) == "fresh"
                and _reason(*args, None, reported) is None):
            outcome.reposted.append(index)
        if reason:
            outcome.left_out[reason] += 1
            outcome.by_reason.setdefault(reason, []).append(index)
        else:
            outcome.kept.append(index)
    return outcome


def _reason(group, state, start, wanted_types, exclude_remote, countries, conditions,
            now, shown=None, reported=None) -> str | None:
    if state is not None and state.dismissed:
        return "dismissed"
    if route := applications.exclusion_key(group, reported):
        return route
    # "Posted within 24 hours" means what it says, also for sites that list ads days late
    # (JSearch, FreeHire): their late ads were 55 of search 16's 186 cards, and the person asked
    # for nothing older than the window (2026-11-04).
    if freshness(group.posted_at, group.date_precision, start) == "too_old":
        return "repost" if any(copy.older_copy for copy in group.copies) else "too_old"
    # Shown in an earlier search before the window began: the job existed then, whatever date
    # its ads give now (45 of search 11's 349 cards, most re-dated by Adzuna).
    if shown is not None and shown < start:
        return "repost"
    # Shown by an earlier search inside this window: it isn't new to the person, whatever its
    # date says (search 16 showed 60 of search 15's cards again). A date later than that showing
    # is the same job dated again, not a new one: search 17 began 50 minutes earlier in the day
    # than search 16 and showed 5 of its cards again, one dated 19:34 that search 16 had shown at
    # 21:46, and one that a job site dated again 2.5 hours after search 16 showed it.
    if shown is not None and shown < now:
        return "shown_before"
    if group.closes_at is not None and group.closes_at < now:
        return "closed"
    # Left out only if the employer's own career system says it's a type not ticked. A job site's
    # tag alone can be wrong (three of hackajob's £37,000-85,000 engineering roles, and an ad asking
    # for at least 35 hours a week, were "part-time"): the ad text decides those after scoring
    # (search._ad_exclusion).
    if leaves_for_job_type(group, None, wanted_types):
        return "job_type"
    if exclude_remote and fully_remote(group):
        return "remote"
    stated_countries = {c.country for c in group.copies if c.country}
    if stated_countries and not (stated_countries & countries):
        return "country"
    if fails_a_condition(group, conditions):
        return "location_condition"
    return None


def job_types_of(group: JobGroup, scored: dict | None) -> list[str]:
    """The job's types: what its job sites say, unless they leave it open between several
    ("contract" on Adzuna can be fixed-term, freelance or part-time) and the ad text says which
    one it is. When no site says, the ad text decides alone."""
    stated = sorted({t for c in group.copies for t in c.job_types})
    read = (scored or {}).get("job_type")
    # These two hints describe a full-time schedule with an unspecified contract.
    # Student work can also be full-time; the ad may refine this broad schedule.
    student = (read == "internship_or_working_student"
               and set(stated) == {"full_time_permanent", "fixed_term"})
    if read and read != "unclear" and (
            not stated or (len(stated) > 1 and (read in stated or student))):
        return [read]
    return stated


def leaves_for_job_type(group: JobGroup, scored: dict | None, wanted: set[str] | list[str]) -> bool:
    """Whether the job is proven to be of types the person didn't tick: its types
    (job_types_of) aren't ticked and come from the ad text (the score's reading) or the
    employer's own career system. A job site's tag alone can keep a job, never remove it, and an
    ad text that names a ticked type keeps it too."""
    wanted = set(wanted)
    types = job_types_of(group, scored)
    read = (scored or {}).get("job_type")
    if not types or set(types) & wanted or read in wanted:
        return False
    from_ad = bool(read) and read != "unclear" and types == [read]
    from_employer = any(c.job_types and group.source_kinds.get(c.source) == "employer"
                        for c in group.copies)
    return from_ad or from_employer


def fully_remote(group: JobGroup) -> bool:
    """Certainly done fully remotely: every copy that says how the job is done says remote, and no
    copy names an office among its places. Samsara's "London - UK2; Remote - UK" and Wayve's three
    offices plus "Remote, Germany" offer an office, so the ad text decides those after scoring."""
    stating = [c for c in group.copies if c.work_mode]
    return (bool(stating) and all(c.work_mode == "remote" for c in stating)
            and not any(names_an_office(c.location_text) for c in group.copies))


def fails_a_condition(group: JobGroup, conditions: list) -> bool:
    """True when a condition the person wrote about places says this job's place doesn't fit."""
    return any(condition_fit(condition, group) == "no" for condition in conditions)


def condition_fit(condition, group: JobGroup) -> str:
    """"yes", "no" or "unknown" for a job and one of the conditions the person wrote."""
    if condition.kind != "about_job" and travel.workplace_conflict(group):
        return "unknown"
    if condition.kind == "near":
        return travel.answer(condition, group)
    country = next((c.country for c in group.copies if c.country), None)
    answers = {fits(condition, country, place) for place in travel.job_places(group)}
    if "yes" in answers:
        return "yes"
    return "no" if "no" in answers else "unknown"
