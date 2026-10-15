"""Reads the standard job data many job pages carry for search engines (schema.org JobPosting).
It gives the full ad text, the posting date, the job type and
whether the job is remote, in the same format on thousands of different sites.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime

from jobcu.freshness import parse_closing, parse_iso
from jobcu.text import html_to_text

# Some sites write the "+" as an HTML entity (ECM Selection: "application/ld&#x2B;json").
_JSON_LD = re.compile(
    r"<script[^>]+type\s*=\s*[\"']application/ld(?:\+|&#x2B;|&#43;)json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)

_EMPLOYMENT_TYPES = {
    "FULL_TIME": ["full_time_permanent", "fixed_term"],
    "PART_TIME": ["part_time"],
    "CONTRACTOR": ["freelance_or_contract"],
    "TEMPORARY": ["fixed_term"],
    "INTERN": ["internship_or_working_student"],
}

# These are statements supplied by the publisher, not inferred requirements. In particular,
# a skills list can contain preferences and education can have an experience alternative.
AD_SECTIONS = (
    ("responsibilities", "Responsibilities"),
    ("qualifications", "Qualifications"),
    ("skills", "Skills"),
    ("educationRequirements", "Education requirements"),
    ("experienceRequirements", "Experience requirements"),
    ("eligibilityToWorkRequirement", "Work eligibility"),
    ("applicantLocationRequirements", "Applicant location requirements"),
    ("securityClearanceRequirement", "Security clearance"),
    ("physicalRequirement", "Physical requirements"),
    ("sensoryRequirement", "Sensory requirements"),
)


def _supplied_text(value, depth: int = 0) -> list[str]:
    """Read known text/credential forms without importing JSON, URLs or unrelated metadata."""
    if depth > 4:
        return []
    if isinstance(value, str):
        return [text] if (text := html_to_text(value)) else []
    if isinstance(value, list):
        return [text for part in value for text in _supplied_text(part, depth + 1)]
    if not isinstance(value, dict):
        return []
    parts = [text for key in ("@value", "name", "description")
             for text in _supplied_text(value.get(key), depth + 1)]
    for key, label in (("credentialCategory", "Credential"), ("educationalLevel", "Level"),
                       ("about", "Subject"), ("recognizedBy", "Recognized by")):
        parts.extend(f"{label}: {text}"
                     for text in _supplied_text(value.get(key), depth + 1))
    months = value.get("monthsOfExperience")
    if (not isinstance(months, bool) and isinstance(months, (str, int, float))
            and re.fullmatch(r"\d+(?:\.\d+)?", str(months))):
        parts.append(f"{months} months")
    return list(dict.fromkeys(parts))


def ad_sections(item: dict) -> list[tuple[str, list[str]]]:
    sections = [(label, texts) for key, label in AD_SECTIONS
                if (texts := _supplied_text(item.get(key)))]
    alternative = item.get("experienceInPlaceOfEducation")
    if isinstance(alternative, bool):
        sections.append(("", ["Experience instead of education: "
                              + ("Yes" if alternative else "No")]))
    return sections


def append_sections(body: str, sections: list[tuple[str, list[str]]]) -> str:
    """Keep wording and field context; never fuzzy-match skills or discard a qualification."""
    for label, texts in sections:
        additions = []
        for text in texts:
            if not text.strip():
                continue
            existing = " ".join(body.split()).casefold()
            needle = " ".join(text.split()).casefold()
            labelled = (label + ": " if label else "") + needle
            already_present = needle == existing or re.search(
                r"(?<!\w)" + re.escape(labelled.casefold()) + r"(?!\w)", existing)
            if not already_present and needle not in [
                    " ".join(value.split()).casefold() for value in additions]:
                additions.append(text)
        if additions:
            heading = label + ":\n" if label else ""
            body = "\n\n".join(part for part in (body, heading + "\n".join(additions))
                                if part)
    return body


@dataclass
class JobPosting:
    title: str = ""
    description: str = ""
    date_posted: datetime | None = None
    date_has_time: bool = False
    company: str | None = None
    location_text: str | None = None
    job_types: list[str] = field(default_factory=list)
    remote: bool = False
    valid_through: datetime | None = None  # when applications close
    country: str | None = None  # the address's country as written ("GB", "Deutschland")
    description_is_complete: bool = False
    original_description: str = field(default="", repr=False)
    sections: list[tuple[str, list[str]]] = field(default_factory=list, repr=False)

    def with_sections(self, body: str) -> str:
        return append_sections(body, self.sections)


def find_job_posting(html: str) -> JobPosting | None:
    for block in _JSON_LD.findall(html or ""):
        try:
            # strict=False: line breaks inside an ad's text are common and harmless.
            data = json.loads(block.strip(), strict=False)
        except ValueError:
            continue
        for item in _items(data):
            if _is_job_posting(item):
                return _read(item)
    return None


def _items(data) -> list[dict]:
    if isinstance(data, list):
        return [item for entry in data for item in _items(entry)]
    if isinstance(data, dict):
        return [data, *_items(data.get("@graph", []))]
    return []


def _is_job_posting(item: dict) -> bool:
    kind = item.get("@type")
    kinds = kind if isinstance(kind, list) else [kind]
    return "JobPosting" in kinds


def _read(item: dict) -> JobPosting:
    posted_text = str(item.get("datePosted") or "")
    types: list[str] = []
    raw_types = item.get("employmentType") or []
    for raw in raw_types if isinstance(raw_types, list) else [raw_types]:
        for mapped in _EMPLOYMENT_TYPES.get(str(raw).upper().replace("-", "_"), []):
            if mapped not in types:
                types.append(mapped)
    organisation = item.get("hiringOrganization")
    company = organisation.get("name") if isinstance(organisation, dict) else organisation
    description = html_to_text(item.get("description")) \
        if isinstance(item.get("description"), str) else ""
    sections = ad_sections(item)
    return JobPosting(
        title=html_to_text(str(item.get("title") or "")),
        description=append_sections(description, sections),
        original_description=description,
        description_is_complete=bool(description),
        sections=sections,
        date_posted=parse_iso(posted_text) if posted_text else None,
        date_has_time="T" in posted_text,
        company=str(company) if company else None,
        location_text=_location(item.get("jobLocation")),
        country=_country(item.get("jobLocation")),
        job_types=types,
        remote=str(item.get("jobLocationType") or "").upper() == "TELECOMMUTE",
        valid_through=parse_closing(str(item.get("validThrough") or "")),
    )


def _country(value) -> str | None:
    for place in value if isinstance(value, list) else [value]:
        address = place.get("address") if isinstance(place, dict) else None
        country = address.get("addressCountry") if isinstance(address, dict) else None
        if isinstance(country, dict):
            country = country.get("name")
        if country:
            return str(country).strip()
    return None


def _location(value) -> str | None:
    places = value if isinstance(value, list) else [value]
    names = []
    for place in places:
        address = place.get("address") if isinstance(place, dict) else None
        if isinstance(address, dict):
            town = address.get("addressLocality") or address.get("addressRegion")
            if town and town not in names:
                names.append(str(town))
    return ", ".join(names) or None
