"""Ordinary mandatory requirements, grounded in the evidence supplied for this job.

Language, years, doctorate and citizenship/clearance have separate established policies.
Quotes establish that a comparison uses supplied text; they cannot prove its interpretation.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

MAX_POINTS = 15
BLOCKED_POINTS = 10
BLOCKER_LIMIT = 55


class RequirementCheck(BaseModel):
    requirement: str = Field(description="Short English name of the mandatory requirement")
    ad_words: str = Field(description="Exact short quote stating the requirement")
    profile_words: str = Field(description="Exact relevant profile quote, or empty if unknown")
    status: Literal["met", "not_met", "unclear"]


RULES = """\
requirement_checks: list every mandatory non-language/non-experience requirement, including \
current student enrolment, qualifications, professional registration/licences and work permission. \
Doctorates and citizenship/security clearance use their separate evidence fields: don't repeat \
them here. Each check has a short English requirement name and an exact short ad_words quote \
(at most 20 words) from the supplied evidence. profile_words quotes the relevant fact in the \
profile, not an invented explanation. status is met, not_met or unclear. Use not_met only when \
the requirement and a conflicting profile fact are explicit; missing information is unclear. \
A completed qualification is not current student enrolment. Visa eligibility is not a granted \
visa or an already-held right to work. A desirable qualification is not mandatory; either/or \
qualifications need only one qualifying alternative. Empty list only when no ordinary mandatory \
requirements are stated. If the ad is incomplete, unseen requirements remain unknown.\
"""


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


def ground(checks: list[RequirementCheck] | None, ad_text: str, profile_text: str
           ) -> list[dict] | None:
    """Unsupported comparisons and conflicting answers become unknown, never blockers."""
    if checks is None:
        return None
    ad, person = _plain(ad_text), _plain(profile_text)
    found: dict[str, dict] = {}
    for check in checks:
        data = check.model_dump()
        data["requirement"] = check.requirement.strip() or "A stated requirement"
        words, fact = _plain(check.ad_words), _plain(check.profile_words)
        if not words or words not in ad or (
            check.status != "unclear" and (not fact or fact not in person)
        ):
            data["status"] = "unclear"
        key = words or _plain(data["requirement"])
        if key in found:
            if found[key]["status"] != data["status"]:
                found[key]["status"] = "unclear"
        else:
            found[key] = data
    return list(found.values())


def merge(earlier: list[dict] | None, later: list[dict] | None) -> list[dict] | None:
    """An incomplete research note cannot erase a known requirement by omission."""
    if later is None:
        return earlier
    combined = {_plain(check["requirement"]): check for check in earlier or []}
    for check in later:
        key = _plain(check["requirement"])
        previous = combined.get(key)
        if previous and previous["status"] == "not_met" and check["status"] == "unclear":
            continue
        combined[key] = check
    return list(combined.values())


@dataclass
class Judgement:
    points: int
    limits: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def special_blocker(evidence: dict) -> bool:
    return (evidence.get("doctorate") == "required_person_lacks_it"
            or evidence.get("citizenship_or_clearance") == "required_definitely_out_of_reach")


def judge(evidence: dict, points: int) -> Judgement:
    """The existing rubric bands, made consistent with supported comparison verdicts."""
    if "requirements_complete" not in evidence:
        return Judgement(points)  # legacy evidence keeps its original rubric behaviour
    checks = evidence.get("requirement_checks")
    unmet = [c for c in checks or [] if c["status"] == "not_met"]
    unknown = [c for c in checks or [] if c["status"] == "unclear"]
    notes = [f"{c['requirement']}: could not be confirmed" for c in unknown]
    if checks is None:
        notes.append("Mandatory requirements were not fully checked")
    if not evidence["requirements_complete"]:
        notes.append("Only incomplete ad evidence was available; other requirements may be missing")
    if unmet:
        return Judgement(min(points, BLOCKED_POINTS), [
            {"at": BLOCKER_LIMIT, "why": f"{c['requirement']}: not met by the stated profile"}
            for c in unmet
        ], notes)
    if evidence.get("legacy_requirement_blocker"):
        return Judgement(min(points, BLOCKED_POINTS), notes=notes)
    if special_blocker(evidence):
        return Judgement(min(points, BLOCKED_POINTS), notes=notes)
    if unknown or checks is None or not evidence["requirements_complete"] or (
        evidence.get("citizenship_or_clearance") == "required_possible_or_unclear"
    ):
        return Judgement(max(BLOCKED_POINTS + 1, min(points, MAX_POINTS - 1)), notes=notes)
    return Judgement(MAX_POINTS, notes=notes)
