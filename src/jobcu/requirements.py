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
    central_to_role: bool = Field(default=False,
        description="Required specialist/practical expertise central to the daily work")


RULES = """\
requirement_checks: list every mandatory requirement except language level, overall seniority \
and number of years, which have separate fields. Include specific technical/domain knowledge \
and practical skill prerequisites, also when written as "experience with" a technology, plus \
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
 Do not reduce a required-skills section to its degree alone. A matching tool name or basic \
familiarity does not establish the required depth; use unclear unless the profile supports it.\
 Mark central_to_role true for mandatory specialist/domain/practical expertise central to the \
main work, not for a degree, years, generic soft skills or an incidental tool. Shared PCB tools \
do not establish high-speed/RF computing expertise; general ward work does not establish \
specialist clinical practice; lesson planning does not establish a different teaching subject.\
"""


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<!\S)[•●](?=\s|$)", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _profile_values(value) -> set[str]:
    """Complete scalar facts, without JSON/list punctuation between adjacent skills/degrees."""
    if isinstance(value, str):
        return {_plain(value)}
    if isinstance(value, dict):
        return set().union(*(_profile_values(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_profile_values(v) for v in value))
    return set()


def _profile_quote(words: str, profile: str | dict) -> bool:
    if _plain(words) in _plain(str(profile)):
        return True
    if not isinstance(profile, dict):
        return False
    parts = [_plain(part) for part in words.split(",")]
    # A composed quote must consist entirely of complete stated values. Do not turn a bag
    # of matching words, changed negation or an invented skill into supported evidence.
    return len(parts) > 1 and all(parts) and set(parts) <= _profile_values(profile)


def ground(checks: list[RequirementCheck] | None, ad_text: str, profile_text: str | dict
           ) -> list[dict] | None:
    """Unsupported comparisons and conflicting answers become unknown, never blockers."""
    if checks is None:
        return None
    ad = _plain(ad_text)
    found: dict[str, dict] = {}
    for check in checks:
        data = check.model_dump()
        data["proposed_status"] = check.status
        data["grounding_issues"] = []
        data["requirement"] = check.requirement.strip() or "A stated requirement"
        words, fact = _plain(check.ad_words), _plain(check.profile_words)
        if not words or words not in ad:
            data["grounding_issues"].append("ad_quote_unverified")
        if check.status != "unclear" and (
                not fact or not _profile_quote(check.profile_words, profile_text)):
            data["grounding_issues"].append("profile_quote_unverified")
        if data["grounding_issues"]:
            data["status"] = "unclear"
        key = words or _plain(data["requirement"])
        if key in found:
            found[key]["central_to_role"] |= data["central_to_role"]
            if found[key]["status"] != data["status"]:
                found[key]["status"] = "unclear"
                found[key]["proposed_status"] = "unclear"
                found[key]["grounding_issues"] = ["conflicting_comparisons"]
        else:
            found[key] = data
    return list(found.values())


def revalidate(checks: list[dict] | None, ad_text: str, profile: dict) -> list[dict] | None:
    """Repair validation from retained proposals; never infer a lost legacy judgement."""
    if checks is None:
        return None
    updated = []
    for stored in checks:
        proposed = stored.get("proposed_status")
        if stored["status"] != "unclear" or proposed not in {"met", "not_met"}:
            # Confirmed outcomes and genuinely uncertain/conflicting comparisons stay as
            # recorded. An old unknown has no recoverable verdict: do not infer one.
            updated.append(dict(stored))
            continue
        check = RequirementCheck.model_validate({**stored, "status": proposed})
        updated.extend(ground([check], ad_text, profile))
    return updated


def update_check(earlier: dict | None, later: dict) -> dict:
    """Unsupported replacements retain the grounded clause and one failed proposal for audit."""
    if earlier is None:
        return later
    if earlier.get("central_to_role"):
        later = {**later, "central_to_role": True}
    if (later.get("grounding_issues") and "grounding_issues" in earlier
            and "ad_quote_unverified" not in earlier["grounding_issues"]):
        return {**earlier, "last_retry": later}
    if earlier["status"] == "not_met" and later["status"] == "unclear":
        return earlier
    return later


def merge(earlier: list[dict] | None, later: list[dict] | None) -> list[dict] | None:
    """An incomplete research note cannot erase a known requirement by omission."""
    if later is None:
        return earlier
    combined = {_plain(check["requirement"]): check for check in earlier or []}
    for check in later:
        key = _plain(check["requirement"])
        combined[key] = update_check(combined.get(key), check)
    return list(combined.values())


@dataclass
class Judgement:
    points: int
    limits: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def special_blocker(evidence: dict) -> bool:
    return (evidence.get("doctorate") == "required_person_lacks_it"
            or evidence.get("citizenship_or_clearance") == "required_definitely_out_of_reach")


def _unknown_note(check: dict) -> str:
    details = {
        "ad_quote_unverified": "the supporting ad wording could not be verified",
        "profile_quote_unverified": "the supporting profile wording could not be verified",
        "conflicting_comparisons": "the returned comparisons disagreed",
    }
    reason = "; ".join(details[i] for i in check.get("grounding_issues", []) if i in details)
    reason = reason or check.get("explanation", "")
    retry = "; ".join(details[i] for i in check.get("last_retry", {}).get("grounding_issues", [])
                      if i in details)
    if retry:
        reason = (reason + "; " if reason else "") + "latest retry: " + retry
    return (f"{check['requirement']}: could not be confirmed" + (f" — {reason}" if reason else ""))


def judge(evidence: dict, points: int) -> Judgement:
    """The existing rubric bands, made consistent with supported comparison verdicts."""
    if "requirements_complete" not in evidence:
        return Judgement(points)  # legacy evidence keeps its original rubric behaviour
    checks = evidence.get("requirement_checks")
    unmet = [c for c in checks or [] if c["status"] == "not_met"]
    unknown = [c for c in checks or [] if c["status"] == "unclear"]
    notes = [_unknown_note(c) for c in unknown]
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
