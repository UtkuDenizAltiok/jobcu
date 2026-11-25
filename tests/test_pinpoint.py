"""Pinpoint career sites (sources/pinpoint.py), with a made-up company's feed and pages."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from jobcu import listmemory
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.sources import careers, pinpoint
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC)
HAVANT = {"id": "1", "city": "Havant", "name": "Havant", "postal_code": "PO9 1BS",
          "province": "Havant", "street_address": "1 Example Street"}


def posting(number, title, workplace="onsite"):
    return {"id": str(number), "title": title,
            "url": f"https://acme.pinpointhq.com/en/postings/0000000{number}",
            "description": "<div>You design power converters and test them in our lab.</div>",
            "key_responsibilities_header": "Key Responsibilities",
            "key_responsibilities": "<ul><li>Board bring-up</li><li>EMC tests</li></ul>",
            "skills_knowledge_expertise_header": "Skills", "skills_knowledge_expertise":
            "<p>A degree in electrical engineering.</p>", "benefits_header": "", "benefits": "",
            "employment_type": "full_time", "employment_type_text": "Full Time",
            "workplace_type": workplace, "workplace_type_text": workplace.title(),
            "deadline_at": (NOW + timedelta(days=20)).isoformat(), "location": HAVANT}


def page(title, posted):
    data = {"@type": "JobPosting", "title": title, "datePosted": posted.isoformat(),
            "description": "<p>You design power converters.</p>",
            "jobLocation": {"address": {"addressLocality": "Havant", "addressCountry": "GB"}}}
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def company(requested, postings):
    def handler(request):
        path = request.url.path
        requested.append(path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-Agent: *\nDisallow: /mydata\nDisallow: /admin\n")
        if path == "/postings.json":
            return httpx.Response(200, json={"data": postings})
        if path.endswith("00000001"):
            return httpx.Response(200, text=page("Electronics Engineer", NOW - timedelta(hours=5)))
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("pinpoint", "Pinpoint"), lambda: False,
                         lambda message: None)


def search(ctx, terms=("Electronics Engineer",)):
    query = JobQuery(["GB"], [], [SearchTerm(text=t, language="en", kind="job_title")
                                  for t in terms], 24, NOW)
    return list(pinpoint.PinpointSource().search(query, ctx))


def test_the_feed_gives_the_ad_and_the_job_page_its_posting_time(monkeypatch):
    acme = Employer("Acme Aerospace", "pinpoint", "acme", ("GB",))
    monkeypatch.setattr(careers, "load_directory", lambda: (acme,))
    requested = []
    feed = [posting(1, "Electronics Engineer", "hybrid"), posting(2, "Office Manager")]
    [job] = search(company(requested, feed))
    # The matching job's page gave its exact posting time; the ad is the feed's, with its parts.
    assert job.title == "Electronics Engineer" and job.country == "GB"
    assert job.location_text == "Havant, PO9 1BS" and job.work_mode == "hybrid"
    assert job.date_precision == "exact" and job.posted_at < NOW
    assert "Key Responsibilities\n• Board bring-up" in job.description
    assert job.description_is_complete and job.closes_at > NOW
    assert requested.count("/en/postings/00000001") == 1
    assert "/en/postings/00000002" not in requested  # the old unmatched title stays unread

    # The next search takes the page from memory; a job new on the list whose title the search
    # words miss goes to the person's AI with its ad, dated by its first sight.
    listmemory.note("pinpoint", "acme", [p["url"] for p in feed], now=NOW - timedelta(hours=12))
    requested.clear()
    jobs = search(company(requested, [*feed, posting(3, "Test Bench Developer")]))
    by_title = {job.title: job for job in jobs}
    assert sorted(by_title) == ["Electronics Engineer", "Test Bench Developer"]
    assert by_title["Test Bench Developer"].title_unmatched
    assert by_title["Test Bench Developer"].date_precision == "day"
    assert requested == ["/robots.txt", "/postings.json"]


def test_the_directory_check_counts_the_feed_s_places():
    acme = Employer("Acme Aerospace", "pinpoint", "acme", ())
    survey = pinpoint.PinpointSource().survey(
        acme, company([], [posting(1, "Electronics Engineer"), posting(2, "Office Manager")]))
    assert survey.counts["GB"] == 2 and survey.towns["GB"] == {"Havant"}
