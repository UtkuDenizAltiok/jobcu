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
current student enrolment, qualifications and professional registration/licences. Doctorates, \
citizenship/security clearance and the right to work or visa sponsorship use their separate \
evidence fields: don't repeat them here. Each check has a short English requirement name and an \
exact short ad_words quote (at most 20 words) from the supplied evidence. profile_words quotes \
the relevant fact in the profile, not an invented explanation. status is met, not_met or \
unclear. Use not_met only when the requirement and a conflicting profile fact are explicit; \
missing information is unclear. A completed qualification is not current student enrolment. A \
desirable qualification is not mandatory; either/or qualifications need only one qualifying \
alternative. Empty list only when no ordinary mandatory \
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
    """Complete scalar facts, without JSON/list punctuation between adjacent skills/degrees.
    Numbers count too: a degree's year, years of experience."""
    if isinstance(value, bool):
        return set()
    if isinstance(value, str):
        return {_plain(value)}
    if isinstance(value, int | float):
        return {_plain(str(value))}
    if isinstance(value, dict):
        return set().union(*(_profile_values(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_profile_values(v) for v in value))
    return set()


def _profile_keys(value) -> set[str]:
    """The profile's field names, as a model writes them in front of a value ("cefr: C1")."""
    if isinstance(value, dict):
        return {_plain(key) for key in value} | set().union(
            *(_profile_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_profile_keys(v) for v in value))
    return set()


def _words(text: str) -> str:
    return " " + " ".join(re.findall(r"\w+|[<>≤≥=+%€$£]", _plain(text))) + " "


def _stated_in(quote: str, text: str) -> bool:
    """The quote's words in a row, in whole words. Punctuation between them doesn't count: an ad's
    bullet list can come back as "A, B, C", and "Für" capitalised differently is the same word.
    Symbols that change a meaning ("> 20", "5+") do count."""
    return _words(quote).strip() != "" and _words(quote) in _words(text)


def quoted_in_ad(words: str, ad: str) -> bool:
    """Whether these words are the ad's own (scoring checks quoted amounts with it)."""
    return _ad_quote(words, ad)


def plain(text: str) -> str:
    return _plain(text)


def _ad_quote(words: str, ad: str) -> bool:
    """A quote from the ad; "..." may leave out what stands between its parts."""
    parts = [part for part in re.split(r"\.{3,}|…", words) if part.strip()]
    apart = _JOINED_AFTER_WORD.sub(r"\1 \2", _JOINED_AFTER_CAPITALS.sub(r"\1 \2", ad))
    return bool(parts) and all(_stated_in(part, ad) or _stated_in(part, apart) for part in parts)


# Some feeds join an ad's lines without a space ("Test und QualitätssicherungAbgeschlossenes
# Studium", "SAP PLMSehr gute", "1 kVErfahrung"; 35 of JSearch's 252 ads in search 15), and a
# faithful quote of the next line then began inside a word: 22 of 32 refused ad quotes. A small
# letter, or capitals, running into a capitalised word mark such a join; the ad's own spelling
# ("LabVIEW", "PCIe") still matches as it is.
_UPPER, _LOWER = "A-ZÀ-ÖØ-Þ", "a-zß-öø-ÿ"
_JOINED_AFTER_WORD = re.compile(rf"([{_LOWER}])([{_UPPER}])")
_JOINED_AFTER_CAPITALS = re.compile(rf"([{_UPPER}])([{_UPPER}][{_LOWER}])")


def _named_facts(words: str, keys: frozenset[str] = frozenset(),
                 values: frozenset[str] = frozenset()) -> list[tuple[str, bool]]:
    """The facts one quote names, and whether each stood in brackets: "MSc Physics (FUT); PCB
    layout" names MSc Physics, FUT and PCB layout. Models join and shorten profile facts so, join
    them with "...", and put a profile field's name in front ("technical_areas: Optics", "finished
    2026"): the name is left out, the value must still be stated."""
    def split(text: str) -> list[str]:
        facts = []
        for fact in re.split(r"[;,]|\.{3,}|…", text):
            fact = fact.strip()
            label = re.match(r"([\w ]+?)\s*:\s*(.+)", fact)
            if label and _plain(label.group(1)) in keys:
                fact = label.group(2).strip()
            elif label and _plain(label.group(1)) in values:
                # "Spanish: Basic": a stated value, then what the profile says about it.
                facts.append(label.group(1).strip())
                fact = label.group(2).strip()
            first, _, rest = fact.partition(" ")
            if rest and _plain(first) in keys:
                fact = rest.strip()
            if fact:
                facts.append(fact)
        return facts

    inside = [fact for part in re.findall(r"\(([^()]*)\)", words) for fact in split(part)]
    outside = split(re.sub(r"\([^()]*\)", ",", words))
    return [(fact, False) for fact in outside] + [(fact, True) for fact in inside]


def _fact_stated(fact: str, in_brackets: bool, values: set[str]) -> bool:
    """A named fact stands in the profile word for word. One word alone needs more: "Ward, care"
    takes "Ward care" apart, while "Debugging" as a skill and "FUT" as a university's short name
    are stated facts."""
    if len(fact.split()) > 1 or in_brackets:
        return any(_stated_in(fact, value) for value in values)
    plain = _plain(fact)
    # A value with a detail in brackets states its first word too: "Basic (actively improving)".
    return plain in values or any(f"({plain})" in value or value.startswith(f"{plain} (")
                                  for value in values)


def _profile_quote(words: str, profile: str | dict) -> bool:
    if _plain(words) in _plain(str(profile)):
        return True
    if not isinstance(profile, dict):
        return False
    # A bag of matching words doesn't count, so changed negation or an invented skill stays
    # unsupported.
    values = _profile_values(profile)
    facts = _named_facts(words, frozenset(_profile_keys(profile)), frozenset(values))
    return bool(facts) and all(_fact_stated(fact, inside, values) for fact, inside in facts)


def ground(checks: list[RequirementCheck] | None, ad_text: str, profile_text: str | dict
           ) -> list[dict] | None:
    """Unsupported comparisons and conflicting answers become unknown, never blockers."""
    if checks is None:
        return None
    found: dict[str, dict] = {}
    for check in checks:
        data = check.model_dump()
        data["proposed_status"] = check.status
        data["grounding_issues"] = []
        data["requirement"] = check.requirement.strip() or "A stated requirement"
        words, fact = _plain(check.ad_words), _plain(check.profile_words)
        if not words or not _ad_quote(check.ad_words, ad_text):
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
