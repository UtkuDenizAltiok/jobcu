"""The page that really takes the application, found when the person clicks a job's link.

Many job sites only repeat an ad and send people on to the site that takes applications. When the
person clicks, Jobcu reads that one page and sends their browser straight to its apply link, so the
extra page never appears. Only the click reads a page, never a search: these links can be paid per
click, and a person clicking once is what they pay for. The browser follows the site's own link,
so the site still sees where the visit came from. Anything unclear leaves the link as it was: a
wrong job would be worse than one more page.
"""

import ipaddress
import logging
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

from jobcu.applications import blocked
from jobcu.sources.http import USER_AGENT
from jobcu.sources.jsearch import APPLICATION_SYSTEMS

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 4.0  # the person is waiting for a new tab
MAX_REDIRECTS = 3
MAX_PAGE_BYTES = 2_000_000
# Sites never read: their terms forbid it, they refuse automated visitors, or the person applies
# there. Their links open as they are.
NEVER_READ = frozenset({
    "arbeitsagentur", "cv-library", "glassdoor", "google", "indeed", "jobleads", "jooble",
    "linkedin", "monster", "reed", "stepstone", "totaljobs", "xing", "ziprecruiter",
})
# Sites known to repeat ads: their own /apply address only passes people on. On any other site it
# may be the application form itself, and the person should see the ad first.
PASSES_ON = frozenset({"adzuna", "arbeitnow"})
# The words of an apply button, as the supported countries' job sites write them.
BUTTON_WORDS = frozenset({
    "apply", "apply now", "apply for this job", "apply for this job now", "apply to this job",
    "apply for job", "apply on company site", "apply on employer site", "continue to application",
    "go to application", "bewerben", "jetzt bewerben", "auf diesen job bewerben", "zur bewerbung",
    "zum stellenangebot", "zur stellenanzeige", "zur originalanzeige", "postuler",
    "postuler maintenant", "solliciteren", "nu solliciteren", "candidati", "candidati ora",
    "solicitar", "inscribirse", "aplikuj", "candidatar-se",
})
_REDIRECT_PATH = re.compile(r"/(?:redirect|land|ats-redirect|away|out|external)(?:/|$)", re.I)
_APPLY_PATH = re.compile(r"/apply/?$", re.I)
_ACCOUNT_PATH = re.compile(r"/(?:log-?in|sign-?in|sign-?up|register)(?:/|$)", re.I)


class _Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found: list[tuple[str, str]] = []  # (what the link says, its address)
        self.marked: list[str] = []  # links the site marks as the direct one (Trabajo.org)
        self._open: dict | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._finish()
            self._open, self._text = dict(attrs), []

    def handle_data(self, data):
        if self._open is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self._finish()

    def _finish(self) -> None:
        if self._open is None:
            return
        attrs, self._open = self._open, None
        href = attrs.get("href")
        if not href:
            return
        if "data-apply-direct-link" in attrs:
            self.marked.append(href)
        self.found.append((" ".join("".join(self._text).split()), href))


def _site_words(host: str) -> set[str]:
    return set(host.lower().rstrip(".").split("."))


def apply_link_in(page: str, page_url: str) -> str | None:
    """The page's one apply link, when it leads on; None when there isn't exactly one."""
    anchors = _Anchors()
    anchors.feed(page)
    anchors.close()
    wanted = anchors.marked or [href for text, href in anchors.found
                                if text.casefold().rstrip(" .!→›»") in BUTTON_WORDS]
    targets = {urljoin(page_url, href) for href in wanted}
    if len(targets) != 1:
        return None
    target = targets.pop()
    parts, here = urlsplit(target), urlsplit(page_url)
    if (parts.scheme not in {"http", "https"} or not parts.hostname or target == page_url
            or _ACCOUNT_PATH.search(parts.path) or blocked(target)):
        return None
    if parts.hostname != here.hostname:
        return target
    if _REDIRECT_PATH.search(parts.path) or (
            _APPLY_PATH.search(parts.path) and _site_words(here.hostname or "") & PASSES_ON):
        return target
    return None


def _may_read(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
        if (parts.scheme not in {"http", "https"} or "." not in host or parts.username
                or parts.password or _site_words(host) & NEVER_READ
                or any(host == name or host.endswith("." + name) for name in APPLICATION_SYSTEMS)):
            return False
        return all(ipaddress.ip_address(address[4][0]).is_global
                   for address in socket.getaddrinfo(host, parts.port or None))
    except (OSError, ValueError):
        return False


def _read_page(url: str, http: httpx.Client) -> str | None:
    """The page's text; None unless the address itself answers with a page on its own site. An
    address that redirects elsewhere already skips its page."""
    start = urlsplit(url).hostname
    for _ in range(MAX_REDIRECTS + 1):
        if not _may_read(url) or urlsplit(url).hostname != start:
            return None
        with http.stream("GET", url) as reply:
            if reply.is_redirect:
                url = urljoin(url, reply.headers.get("location", ""))
                continue
            if reply.status_code != 200 or "html" not in reply.headers.get("content-type", ""):
                return None
            body = bytearray()
            for chunk in reply.iter_bytes():
                body.extend(chunk)
                if len(body) > MAX_PAGE_BYTES:
                    return None
            return bytes(body).decode(reply.encoding or "utf-8", errors="replace")
    return None


def destination(url: str, http: httpx.Client | None = None) -> str:
    """Where a click on this link should go. Never fails: any problem leaves the link as it was."""
    client = http or httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False,
                                  headers={"User-Agent": USER_AGENT})
    try:
        page = _read_page(url, client)
        return (apply_link_in(page, url) if page else None) or url
    except (httpx.HTTPError, httpx.InvalidURL, ValueError, UnicodeError) as exc:
        log.info("Apply link not found: %s", type(exc).__name__)
        return url
    finally:
        if http is None:
            client.close()
