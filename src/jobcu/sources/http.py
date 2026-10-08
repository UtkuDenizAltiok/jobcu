"""Polite HTTP for job sources.

- a clear User-Agent naming Jobcu
- a minimum pause between requests to the same site
- waits and retries on "too many requests" and temporary server errors, respecting Retry-After
- answers are remembered during one search, so the same page is never fetched twice
- never logs request addresses, because some contain keys
"""

import logging
import random
import re
import socket
import threading
import time
from collections.abc import Callable
from datetime import UTC
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

from jobcu import __version__

log = logging.getLogger(__name__)

USER_AGENT = f"Jobcu/{__version__} (personal job search app)"
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
DEFAULT_MIN_INTERVAL = 1.0  # seconds between requests to the same site
MAX_RETRIES = 3
MAX_BACKOFF_SECONDS = 120.0
STOP_POLL_SECONDS = 0.2


def client(**kwargs) -> httpx.Client:
    # trust_env=False: never send requests through proxies set elsewhere on the computer.
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=True,
        trust_env=False,
        **kwargs,
    )


# Pauses between requests for sites with known limits (Adzuna allows 25 a minute).
SITE_INTERVALS = {
    "api.adzuna.com": 2.6,
    "www.reed.co.uk": 0.5,
    "rest.arbeitsagentur.de": 0.7,
    "jobsireland.ie": 2.0,
    "www.jobs.ac.uk": 1.5,
    "euraxess.ec.europa.eu": 4.0,
    # Company career systems' public job lists (Lever's robots.txt asks for 1 s).
    "boards-api.greenhouse.io": 0.5,
    "api.lever.co": 1.0,
    "api.eu.lever.co": 1.0,
    "api.ashbyhq.com": 1.0,
    "apply.workable.com": 1.0,
    "www.arbeitnow.com": 1.0,
    "www.arbeitnow.co.uk": 1.0,
    # Sweden's open job data (CC0, no stated limit): pages are big, so a short pause is enough.
    "jobsearch.api.jobtechdev.se": 0.5,
    # The German public sector's portal: its robots.txt asks for "Crawl-delay: 30".
    "www.service.bund.de": 30.0,
    # The Dutch government's job site: its robots.txt allows "Request-rate: 10/1".
    "www.werkenvoornederland.nl": 0.3,
    # NAV's job feed (Norway): no stated limit; each full ad is one small answer.
    "pam-stilling-feed.nav.no": 0.5,
}


class KeyCheck:
    """The result of testing a job site key, in plain words."""

    def __init__(self, ok: bool, message: str) -> None:
        self.ok = ok
        self.message = message


class Blocked(Exception):
    """The site refused Jobcu (e.g. bot protection). Jobcu never tries to get around this."""


class RequestStopped(Exception):
    """Stop was requested before a source request could start."""


class RobotsRules:
    """A site's robots.txt, read as the standard says (RFC 9309): the group for Jobcu's name,
    or else the one for every robot; within it the most specific rule (the longest path)
    decides, and an Allow wins a tie. Python's own reader takes the first matching rule instead,
    so "Disallow: /" followed by "Allow: /careers" wrongly shut Jobcu out of pages the site
    allows."""

    def __init__(self, text: str = "", *, allow_all: bool = False, disallow_all: bool = False):
        self.allow_all, self.disallow_all = allow_all, disallow_all
        self._rules: list[tuple[bool, str]] = []
        groups: list[tuple[list[str], list[tuple[bool, str]]]] = []
        agents: list[str] = []
        rules: list[tuple[bool, str]] = []
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = (part.strip() for part in line.split(":", 1))
            field = field.lower()
            if field == "user-agent":
                if rules:  # a new group starts
                    groups.append((agents, rules))
                    agents, rules = [], []
                agents.append(value.lower())
            elif field in ("allow", "disallow") and agents:
                if value:  # an empty Disallow allows everything
                    rules.append((field == "allow", value))
        if agents:
            groups.append((agents, rules))
        mine = [r for names, r in groups if any(n.split("/")[0] == "jobcu" for n in names)]
        anyone = [r for names, r in groups if "*" in names]
        for chosen in mine or anyone:
            self._rules.extend(chosen)

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        anchored = pattern.endswith("$")
        expression = "".join(".*" if c == "*" else re.escape(c)
                             for c in (pattern[:-1] if anchored else pattern))
        return re.match(expression + ("$" if anchored else ""), path) is not None

    def allows(self, url: str) -> bool:
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        parts = urlsplit(url)
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        best: tuple[int, bool] | None = None
        for allow, pattern in self._rules:
            if self._matches(pattern, path):
                key = (len(pattern), allow)
                if best is None or key > best:
                    best = key
        return True if best is None else best[1]


class PoliteClient:
    """One per search. Safe to share between sources running in parallel."""

    def __init__(
        self,
        min_intervals: dict[str, float] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        transport: httpx.BaseTransport | None = None,
        resolve: Callable[[str], object] | None = None,
        should_stop: Callable[[], bool] | None = None,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
        on_wait: Callable[[str, float], None] | None = None,
    ) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=True,
            trust_env=False,
            transport=transport,
        )
        self._min_intervals = SITE_INTERVALS if min_intervals is None else min_intervals
        self._last_request: dict[str, float] = {}
        self._cooldowns: dict[str, float] = {}
        self._blocked_hosts: set[str] = set()
        self._host_locks: dict[str, threading.Lock] = {}
        self._lock = threading.Lock()
        self._cache: dict[tuple, httpx.Response] = {}
        self._sleep = sleep
        self._should_stop = should_stop
        self._clock = clock
        self._wall_clock = wall_clock
        self._on_wait = on_wait
        self.request_count: dict[str, int] = {}
        self._resolve = resolve or (lambda host: socket.getaddrinfo(host, 443))
        self._hosts_exist: dict[str, bool] = {}

    def close(self) -> None:
        self._client.close()

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def request(self, method: str, url: str, *, cache: bool = True,
                check_attempt: Callable[[], None] | None = None,
                before_attempt: Callable[[], None] | None = None,
                retry_response: Callable[[httpx.Response], bool] | None = None,
                **kwargs) -> httpx.Response:
        self._check_stop()
        key = (method, url, repr(sorted((kwargs.get("params") or {}).items())),
               repr(kwargs.get("json")))
        if cache and key in self._cache:
            return self._cache[key]
        host = urlsplit(url).hostname or ""
        for attempt in range(MAX_RETRIES + 1):
            self._check_stop()
            if check_attempt is not None:
                check_attempt()
            self._wait_turn(host)
            if before_attempt is not None:
                before_attempt()
            try:
                response = self._client.request(method, url, **kwargs)
            except httpx.TransportError as exc:
                # A host name that doesn't exist won't appear by waiting: an address the
                # person's AI guessed cost 15 seconds of retries each (search 11).
                if attempt == MAX_RETRIES or (isinstance(exc, httpx.ConnectError)
                                              and not self._exists(host)):
                    raise
                if check_attempt is not None:
                    check_attempt()
                log.info("Network problem with %s (%s), retrying", host, type(exc).__name__)
                self._pause(min(2 ** attempt * 2, MAX_BACKOFF_SECONDS)
                            + random.uniform(0, 1), host)
                continue
            finally:
                with self._lock:
                    self.request_count[host] = self.request_count.get(host, 0) + 1
            if response.status_code in (401, 403, 429) and _looks_like_bot_protection(response):
                with self._lock:
                    self._blocked_hosts.add(host)
                raise Blocked(host)
            if response.status_code == 429 or response.status_code >= 500:
                wait = _retry_after(response, now=self._wall_clock())
                if wait is None:
                    wait = min(2 ** attempt * 5, MAX_BACKOFF_SECONDS)
                # Even the final failed attempt tells other readers when they may resume.
                with self._lock:
                    self._cooldowns[host] = max(
                        self._cooldowns.get(host, 0.0), self._clock() + wait,
                    )
                if retry_response is not None and not retry_response(response):
                    break
                if attempt == MAX_RETRIES:
                    break
                if check_attempt is not None:
                    check_attempt()
                if wait > 0 and self._on_wait is not None:
                    self._on_wait(host, wait)
                log.info("%s answered %s, waiting %.0fs", host, response.status_code, wait)
                continue
            break
        if cache and response.status_code == 200:
            self._cache[key] = response
        return response

    def _exists(self, host: str) -> bool:
        """Whether the host name has an address at all (asked once per host)."""
        with self._lock:
            known = self._hosts_exist.get(host)
        if known is None:
            try:
                known = bool(self._resolve(host))
            except OSError:
                known = False
            with self._lock:
                self._hosts_exist[host] = known
        return known

    def _wait_turn(self, host: str) -> None:
        with self._lock:
            host_lock = self._host_locks.setdefault(host, threading.Lock())
        while True:
            self._check_request(host)
            if host_lock.acquire(timeout=STOP_POLL_SECONDS):
                break
        try:
            interval = self._min_intervals.get(host, DEFAULT_MIN_INTERVAL)
            while True:
                self._check_request(host)
                with self._lock:
                    until = max(self._last_request.get(host, 0.0) + interval,
                                self._cooldowns.get(host, 0.0))
                self._pause(max(0.0, until - self._clock()), host)
                # An in-flight response can extend the deadline while this reader waits.
                with self._lock:
                    if self._cooldowns.get(host, 0.0) <= until:
                        break
            self._last_request[host] = self._clock()
        finally:
            host_lock.release()

    def _check_stop(self) -> None:
        if self._should_stop is not None and self._should_stop():
            raise RequestStopped("Search stopped before another source request.")

    def _check_request(self, host: str) -> None:
        self._check_stop()
        with self._lock:
            if host in self._blocked_hosts:
                raise Blocked(host)

    def _pause(self, seconds: float, host: str) -> None:
        self._check_request(host)
        if self._should_stop is None:
            if seconds > 0:
                self._sleep(seconds)
        else:
            while seconds > 0:
                step = min(seconds, STOP_POLL_SECONDS)
                self._sleep(step)
                seconds -= step
                self._check_request(host)
        self._check_request(host)


def _retry_after(response: httpx.Response, *, now: float | None = None) -> float | None:
    """RFC 9110: non-negative integer seconds or an HTTP date, never a shortened delay."""
    value = (response.headers.get("retry-after") or "").strip()
    if re.fullmatch(r"[0-9]+", value):
        return float(value)
    try:
        when = parsedate_to_datetime(value)
        if when.tzinfo is None:  # obsolete asctime form still denotes GMT
            when = when.replace(tzinfo=UTC)
        return max(0.0, when.timestamp() - (time.time() if now is None else now))
    except (TypeError, ValueError, OverflowError):
        return None


def _looks_like_bot_protection(response: httpx.Response) -> bool:
    text = response.text[:2000].lower()
    return any(
        marker in text
        for marker in ("captcha", "cf-chl", "cloudflare", "are you a robot", "access denied",
                       # Amazon CloudFront's firewall, seen on Adzuna's pages (SOURCES.md)
                       "request blocked")
    )
