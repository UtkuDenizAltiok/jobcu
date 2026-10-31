import httpx
import pytest

from jobcu import applications, applylink
from jobcu.dedupe import JobGroup
from jobcu.sources.base import FoundJob
from jobcu.sources.bundesagentur import to_found_job

AD = "https://board.example.org/jobs/fictional-1"


@pytest.fixture(autouse=True)
def public_hosts(monkeypatch):
    # No test looks a name up; a literal private address still has to be refused (below).
    monkeypatch.setattr(applylink.socket, "getaddrinfo",
                        lambda host, port: [(0, 0, 0, "", (host_address(host), 0))])


def host_address(host):
    return host if host[0].isdigit() else "93.184.216.34"


def page(*links):
    return "<html><body>" + "".join(links) + "</body></html>"


def client(*replies):
    seen = []
    answers = list(replies)

    def handle(request):
        seen.append(str(request.url))
        return answers.pop(0)

    return httpx.Client(transport=httpx.MockTransport(handle)), seen


def html(text, status=200):
    return httpx.Response(status, text=text, headers={"content-type": "text/html; charset=utf-8"})


@pytest.mark.parametrize("button",
                         ["Apply now", "Jetzt bewerben", "POSTULER", "Apply for this job!"])
@pytest.mark.parametrize("profession", ["nurse", "primary teacher", "power electronics engineer"])
def test_one_clear_apply_button_goes_straight_to_the_other_site(button, profession):
    target = f"https://careers.example.com/apply/{profession.replace(' ', '-')}"
    assert applylink.apply_link_in(page(
        f'<a href="/similar/2">Another {profession} job</a>',
        f'<a href="{target}"> {button} </a>',
        '<a href="/blog/how-to-apply">How to apply</a>',
    ), AD) == target


def test_the_same_button_twice_on_a_page_is_still_one_link():
    target = "https://careers.example.com/1"
    assert applylink.apply_link_in(page(f'<a href="{target}">Apply now</a>',
                                        f'<a href="{target}">Apply</a>'), AD) == target


def test_two_different_apply_links_could_be_another_job_so_the_link_stays():
    assert applylink.apply_link_in(page('<a href="https://a.example.com/1">Apply</a>',
                                        '<a href="https://b.example.com/2">Apply</a>'), AD) is None


def test_a_link_marked_as_the_direct_one_wins_over_buttons_that_open_a_form():
    page_text = page(
        '<a href="#" class="skip">Bewerben</a>',
        '<a class="sRedirect d-none" data-apply-direct-link '
        'href="/redirect?id=1&amp;source=2">This ad is on a partner site</a>')
    assert applylink.apply_link_in(page_text, AD) == (
        "https://board.example.org/redirect?id=1&source=2")


@pytest.mark.parametrize("path",
                         ["/land/ad/1?token=x", "/jobs/apply/ats-redirect/?id=1", "/away/1"])
def test_a_redirect_on_the_same_site_is_followed_by_the_browser(path):
    assert applylink.apply_link_in(page(f'<a href="{path}">Apply now</a>'), AD) == (
        "https://board.example.org" + path)


def test_apply_on_the_same_site_counts_only_where_it_is_known_to_pass_people_on():
    assert applylink.apply_link_in(page('<a href="/jobs/1/apply">Apply now</a>'), AD) is None
    known = "https://www.arbeitnow.com/jobs/1"
    assert applylink.apply_link_in(page('<a href="/jobs/1/apply">Apply now</a>'), known) == (
        "https://www.arbeitnow.com/jobs/1/apply")


@pytest.mark.parametrize("link", [
    '<a href="/register/">Apply now</a>',
    '<a href="https://careers.example.com/login">Apply now</a>',
    '<a href="mailto:jobs@example.com">Apply now</a>',
    '<a href="javascript:apply()">Apply now</a>',
    '<a href="#">Apply now</a>',
    '<a aria-disabled="true">Apply now</a>',
    '<a href="https://www.cv-library.co.uk/job/1">Apply now</a>',
    '<a href="https://careers.example.com/1">Read more</a>',
    '<a href="https://careers.example.com/1">Show more jobs to apply for</a>',
])
def test_anything_unclear_or_unusable_leaves_the_link_as_it_was(link):
    assert applylink.apply_link_in(page(link), AD) is None


def test_a_click_reads_the_page_once_and_never_visits_the_apply_link_itself():
    # These links can be paid per click: only the person's browser follows them.
    http, seen = client(html(page('<a href="https://careers.example.com/1">Apply</a>')))
    assert applylink.destination(AD, http) == "https://careers.example.com/1"
    assert seen == [AD]


@pytest.mark.parametrize("reply", [
    html("Blocked", 403),
    html("Gone", 404),
    html(page('<a href="https://careers.example.com/1">Read more</a>')),
    httpx.Response(200, text="%PDF", headers={"content-type": "application/pdf"}),
])
def test_a_page_that_gives_no_answer_keeps_the_link(reply):
    http, _ = client(reply)
    assert applylink.destination(AD, http) == AD


def test_a_failed_connection_keeps_the_link():
    def handle(request):
        raise httpx.ConnectTimeout("too slow", request=request)

    assert applylink.destination(AD, httpx.Client(transport=httpx.MockTransport(handle))) == AD


def test_an_address_that_redirects_elsewhere_already_skips_its_page():
    http, seen = client(httpx.Response(302, headers={"location": "https://careers.example.com/1"}))
    assert applylink.destination(AD, http) == AD
    assert seen == [AD]  # the browser follows it


def test_a_redirect_on_the_same_site_is_read():
    http, seen = client(httpx.Response(302, headers={"location": "/jobs/moved"}),
                        html(page('<a href="https://careers.example.com/1">Apply</a>')))
    assert applylink.destination(AD, http) == "https://careers.example.com/1"
    assert seen == [AD, "https://board.example.org/jobs/moved"]


def test_too_large_a_page_keeps_the_link(monkeypatch):
    monkeypatch.setattr(applylink, "MAX_PAGE_BYTES", 10)
    http, _ = client(html(page('<a href="https://careers.example.com/1">Apply</a>')))
    assert applylink.destination(AD, http) == AD


@pytest.mark.parametrize("url", [
    "https://de.linkedin.com/jobs/view/1",
    "https://www.glassdoor.co.uk/job/1",
    "https://de.jooble.org/jdp/1",
    "https://www.arbeitsagentur.de/jobsuche/jobdetail/1",
    "https://fictional.wd1.myworkdayjobs.com/careers/job/1",
    "https://job-boards.greenhouse.io/fictional/jobs/1",
    "http://127.0.0.1:8765/api/health",
    "http://192.168.1.2/job",
    "http://localhost/job",
    "ftp://board.example.org/job",
    "https://user:secret@board.example.org/job",
])
def test_sites_not_to_read_are_never_asked(url):
    http, seen = client()
    assert applylink.destination(url, http) == url
    assert seen == []


def test_a_name_that_points_at_this_computer_is_not_read(monkeypatch):
    monkeypatch.setattr(applylink.socket, "getaddrinfo",
                        lambda host, port: [(0, 0, 0, "", ("127.0.0.1", 0))])
    http, seen = client()
    assert applylink.destination(AD, http) == AD
    assert seen == []


def bundesagentur(**details):
    return to_found_job({"referenznummer": "fictional-S"}, {
        "stellenangebotsTitel": "Pflegefachkraft (m/w/d)", "firma": "Fictional Klinik", **details})


def test_the_agency_s_details_name_the_original_ad():
    job = bundesagentur(externeURL="https://ads.example.de/job/1", allianzpartnerName="Example")
    assert job.application_options == [{"source": "Example", "url": "https://ads.example.de/job/1"}]
    assert job.url.endswith("/jobdetail/fictional-S")  # its own page stays a saved link
    unnamed = bundesagentur(externeURL="https://ads.example.de/job/1")
    assert unnamed.application_options[0]["source"] == "Original ad"


@pytest.mark.parametrize("value", [None, "", "www.example.de", "javascript:alert(1)", 7])
def test_no_usable_original_ad_keeps_only_the_agency_s_page(value):
    assert bundesagentur(externeURL=value).application_options == []


def test_a_site_repeating_an_ad_comes_after_the_original():
    job = bundesagentur(externeURL="https://ads.example.de/job/1", allianzpartnerName="Example")
    group = JobGroup(copies=[job], source_kinds={"bundesagentur": "job_board"})
    main, also = applications.links(group, {"bundesagentur": "Bundesagentur für Arbeit"}, set())
    assert main == {"source": "Example", "url": "https://ads.example.de/job/1"}
    assert also == [{"source": "Bundesagentur für Arbeit", "url": job.url}]


def test_a_repeating_site_stays_first_when_it_is_the_only_link():
    job = FoundJob(source="jooble", source_job_id="1", url="https://de.jooble.org/jdp/1",
                   title="Lehrkraft", company="Fictional Schule")
    main, also = applications.links(JobGroup(copies=[job]), {"jooble": "Jooble"}, set())
    assert main["url"] == job.url and also == []
