"""Which career system a web address or page belongs to, and the company's name in it.

Used when the person's AI names an employer's job list (`employers.py`): an address on a career
system Jobcu reads is recognised at once ("moog.wd5.myworkdayjobs.com/MOOG_External_Career_Site"
is Moog's Workday site); an employer's own careers page is opened once, and its links show the
system behind it ("careers.moog.com" links to that Workday site). Systems Jobcu doesn't read
yet are named too, so the next ones to build follow what employers really use (2026-09-30:
Bosch on SmartRecruiters, PULS on Softgarden, AMD and Ricardo on iCIMS).
"""

import re
from urllib.parse import urlsplit

# The career systems Jobcu reads, as (system, pattern, how the board is written). Each board is
# written the way the employer directory writes it (src/jobcu/data/employers.json).
_READABLE: list[tuple[str, re.Pattern, str]] = [
    ("workday", re.compile(
        r"https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?"
        r"(?!wday\b)([A-Za-z0-9_-]+)"), "https://{0}.{1}.myworkdayjobs.com/{2}"),
    ("oracle", re.compile(
        r"([a-z0-9-]+(?:\.[a-z0-9-]+)*\.oraclecloud\.com)/hcmUI/CandidateExperience/"
        r"[a-z]{2}(?:-[A-Z]{2})?/sites/([A-Za-z0-9_]+)"), "{0}/{1}"),
    ("greenhouse", re.compile(
        r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?"
        r"(?!embed\b)([A-Za-z0-9_-]+)"), "{0}"),
    ("greenhouse", re.compile(r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)"), "{0}"),
    ("lever", re.compile(r"jobs\.eu\.lever\.co/([A-Za-z0-9_.-]+)"), "eu/{0}"),
    ("lever", re.compile(r"jobs\.lever\.co/([A-Za-z0-9_.-]+)"), "{0}"),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/(?!api\b)([A-Za-z0-9_.-]+)"), "{0}"),
    ("workable", re.compile(r"apply\.workable\.com/(?!api\b|j\b)([A-Za-z0-9_-]+)"), "{0}"),
    ("recruitee", re.compile(r"\b(?!www\b|app\b|api\b)([a-z0-9-]+)\.recruitee\.com"), "{0}"),
    ("teamtailor", re.compile(
        r"\b(?!www\b|app\b|api\b|career\b|assets\b)([a-z0-9-]+)\.teamtailor\.com"), "{0}"),
    ("dvinci", re.compile(r"\b(?!www\b|static\b|cdn\b)([a-z0-9-]+)\.dvinci-hr\.com"), "{0}"),
    ("dvinci", re.compile(r"\b(?!www\b|static\b|cdn\b)([a-z0-9-]+)\.dvinci-easy\.com"),
     "{0}.dvinci-easy.com"),
    ("personio", re.compile(r"\b([a-z0-9-]+)\.jobs\.personio\.de"), "{0}"),
    ("personio", re.compile(r"\b([a-z0-9-]+)\.jobs\.personio\.com"), "{0}.jobs.personio.com"),
    ("softgarden", re.compile(r"\b(?!www\b|api\b|static\b)([a-z0-9-]+)\.softgarden\.io"),
     "{0}"),
    ("eightfold", re.compile(
        r"https?://([a-z0-9.-]+)/careers\?(?:[^\"'\s<>]*&(?:amp;)?)?domain=([a-z0-9.-]+)"),
     "{0}/{1}"),
]

# Signs in a page that its own address is the career site of a system Jobcu reads.
_OWN_ADDRESS: list[tuple[str, re.Pattern]] = [
    ("successfactors", re.compile(r"rmkcdn\.successfactors\.com")),
    ("teamtailor", re.compile(r"teamtailor-cdn\.com|assets\.teamtailor")),
]

# Systems Jobcu doesn't read yet, recognised so their use can be counted.
_NOT_READ: list[tuple[str, re.Pattern]] = [
    ("SmartRecruiters", re.compile(r"smartrecruiters\.com")),
    ("Softgarden", re.compile(r"softgarden\.de")),
    ("iCIMS", re.compile(r"icims\.com")),
    ("Avature", re.compile(r"avature\.net|/externaljobs\b")),
    ("Taleo", re.compile(r"taleo\.net")),
    ("Jobvite", re.compile(r"jobvite\.com|applytojob\.com")),
    ("JOIN", re.compile(r"join\.com/companies/")),
    ("Phenom", re.compile(r"phenompeople\.com|cdn\.phenompeople")),
    ("Eightfold (without its domain)", re.compile(r"\.eightfold\.ai")),
]


def board_in(text: str) -> tuple[str, str] | None:
    """The first (system, board) of a career system Jobcu reads that an address or a page's text
    names, or None."""
    for system, pattern, form in _READABLE:
        match = pattern.search(text or "")
        if match:
            return system, form.format(*match.groups())
    return None


def own_address_board(url: str, page: str) -> tuple[str, str] | None:
    """(system, board) when the page itself is a career site of a system Jobcu reads, served
    from the employer's own address (SuccessFactors' "jobs.example.com")."""
    host = (urlsplit(url).hostname or "").lower()
    if not host:
        return None
    for system, pattern in _OWN_ADDRESS:
        if pattern.search(page or ""):
            return system, host
    return None


def system_not_read(text: str) -> str | None:
    """The name of a career system Jobcu doesn't read yet that the text points to, or None."""
    for name, pattern in _NOT_READ:
        if pattern.search(text or ""):
            return name
    return None
