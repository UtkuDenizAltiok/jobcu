"""Current fictional sources support bounded reference checks across user conditions."""

from types import SimpleNamespace

import httpx
import pytest

from jobcu import reference_sources
from jobcu.ai.base import AIConnectionError
from jobcu.location import ReferenceCheck
from jobcu.settings import PlaceEvidencePage, PlaceEvidenceSet, Settings

FACT = "A staffed weekend service is available."
CITY_URL = "https://city.example.test/services"
NATIONAL_URL = "https://national.example.test/standard"


def city(name="Springford", country="DE"):
    return ReferenceCheck(name=name, country=country, latitude=50, longitude=8)


def page(url=CITY_URL, *, country="DE", towns=None, **extra):
    return PlaceEvidencePage(url=url, title="Fictional authority", country=country,
                             towns=["Springford"] if towns is None else towns,
                             permission="Fictional reuse permission, checked today", **extra)


def reply(*, explanation="The requested service is available in this city.", quotes=None,
          meets=True, id="C0"):
    quotes = quotes if quotes is not None else [
        reference_sources.Quote(source_id="S0", words=FACT)]
    return reference_sources.Answer(id=id, meets=meets, explanation=explanation,
                                    quotes=quotes)


class Client:
    def __init__(self, pages, rows=None, fact="Weekend service", failure=False):
        self.settings = Settings(place_evidence=[PlaceEvidenceSet(
            fact_key=reference_sources.fact_key(fact), sources=pages)])
        self.rows = [reply()] if rows is None else rows
        self.calls, self.failure = [], failure

    def checkpoint(self):
        pass

    def generate(self, output, **request):
        assert output is reference_sources.Answers
        self.calls.append(request)
        if self.failure:
            raise AIConnectionError("Fictional failed comparison")
        return reference_sources.Answers(cities=self.rows)


class HTTP:
    def __init__(self, body=FACT, *, robots="User-agent: *\nAllow: /", status=200):
        self.body, self.robots, self.status, self.calls = body, robots, status, []

    def get(self, url, **options):
        assert options.get("follow_redirects") is False
        self.calls.append(url)
        text, status = (self.robots, 200) if url.endswith("robots.txt") else (
            self.body, self.status)
        return httpx.Response(status, text=text)

    def close(self):
        pass


@pytest.mark.parametrize("condition", ["Certified circuit-training service",
                                       "Weekend nursing service", "Bilingual teaching service"])
def test_exact_fact_uses_current_pages_and_selected_model_without_a_hosted_search(condition):
    client = Client([page()], fact=condition)
    checks, http = [city()], HTTP()
    sources = reference_sources.check(client, condition, checks, http=http)
    assert checks[0].meets is True and checks[0].checked_at
    assert checks[0].sources == sources and sources[0].url == CITY_URL
    assert FACT in checks[0].evidence and len(client.calls) == 1
    assert FACT in client.calls[0]["prompt"]
    # It reads the source again for a later check; no earlier facts/verdicts are cached here.
    later = [city()]
    reference_sources.check(client, condition, later, http=HTTP("The service has closed."))
    assert later[0].meets is None  # the old quotation is no longer present


@pytest.mark.parametrize("rows", [[], [reply(id="C9")], [reply(), reply(meets=False)],
    [reply(quotes=[])], [reply(quotes=[reference_sources.Quote(source_id="S9", words=FACT)])],
    [reply(quotes=[reference_sources.Quote(source_id="S0", words="The service is unavailable.")])],
    [reply(explanation="")], [reply(meets=None)]])
def test_omissions_duplicates_and_unsupported_words_do_not_establish_city_facts(rows):
    checks = [city()]
    reference_sources.check(Client([page()], rows), "Weekend service", checks, http=HTTP())
    assert checks[0].meets is None


def test_national_or_another_city_evidence_cannot_establish_this_city():
    for source in (page(towns=[]), page(towns=["Otherford"]), page(country="GB")):
        client, checks = Client([source]), [city()]
        reference_sources.check(client, "Weekend service", checks, http=HTTP())
        assert checks[0].meets is None and not client.calls


@pytest.mark.parametrize("http", [HTTP(robots="User-agent: *\nDisallow: /services"),
                                HTTP(status=302), HTTP(status=403), HTTP(body="%PDF broken")])
def test_blocked_redirected_or_unreadable_pages_trigger_no_paid_comparison(http):
    client, checks = Client([page()]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=http)
    assert checks[0].meets is None and not client.calls


@pytest.mark.parametrize("url", ["http://example.test/data", "https://localhost/data",
    "https://127.0.0.1/data", "https://user:password@example.test/data",
    "https://example.test:8765/data", "https://something.local/data"])
def test_unapproved_network_destinations_are_not_requested(url):
    client, http = Client([page(url)]), HTTP()
    reference_sources.check(client, "Weekend service", [city()], http=http)
    assert not http.calls and not client.calls


def test_unrelated_condition_and_web_disabled_preserve_existing_choices_without_requests():
    client, http = Client([page()]), HTTP()
    reference_sources.check(client, "No weekend service", [city()], http=http)
    client.settings.use_web_search = False
    reference_sources.check(client, "Weekend service", [city()], http=http)
    assert not http.calls and not client.calls


def test_signed_comparisons_are_not_folded_into_the_opposite_fact():
    client = Client([page()], [reply(quotes=[reference_sources.Quote(
        source_id="S0", words="The index is < 20.")])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP("The index is > 20."))
    assert checks[0].meets is None


def test_failed_comparison_is_not_followed_by_a_hidden_research_dispatch():
    client = Client([page()], failure=True)
    with pytest.raises(AIConnectionError):
        reference_sources.check(client, "Weekend service", [city()], http=HTTP())
    assert len(client.calls) == 1


def test_page_selection_rejects_unknown_pdf_pages_without_a_partial_pass(monkeypatch):
    reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **kw: FACT)])
    monkeypatch.setattr(reference_sources, "PdfReader", lambda stream: reader)
    client, checks = Client([page(pages=[2])]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP("%PDF fictional"))
    assert checks[0].meets is None and not client.calls


def test_shared_table_requires_a_city_specific_quote_and_supports_reviewed_aliases():
    source = page(towns=["Springford", "Otherford"],
                  aliases_by_town={"Springford": ["Frühlingsfurt"]})
    for words, expected in [("Otherford: service available", None),
                            ("Frühlingsfurt: service available", True)]:
        client = Client([source], [reply(quotes=[reference_sources.Quote(
            source_id="S0", words=words)])])
        checks = [city()]
        reference_sources.check(client, "Weekend service", checks, http=HTTP(words))
        assert checks[0].meets is expected


def test_pdf_selection_keeps_common_and_requested_city_pages_only(monkeypatch):
    reader = SimpleNamespace(pages=[SimpleNamespace(
        extract_text=lambda *, extraction_mode, i=i: f"Table page {i}") for i in range(1, 5)])
    monkeypatch.setattr(reference_sources, "PdfReader", lambda stream: reader)
    client = Client([page(pages=[1], pages_by_town={"Springford": [2], "Otherford": [4]})])
    reference_sources.check(client, "Weekend service", [city()], http=HTTP("%PDF fictional"))
    prompt = client.calls[0]["prompt"]
    assert "Table page 1" in prompt and "Table page 2" in prompt
    assert "Table page 3" not in prompt and "Table page 4" not in prompt


def test_successful_source_evidence_reaches_reference_and_travel_admission_without_research(
        monkeypatch):
    from jobcu import reference_places, travel
    from jobcu.dedupe import JobGroup
    from jobcu.location import Anchor, Condition
    from jobcu.sources.base import FoundJob

    client = Client([page()])  # deliberately has no hosted-research method
    monkeypatch.setattr(reference_sources, "PoliteClient", lambda **kw: HTTP())
    town = SimpleNamespace(name="Springford", country="DE", latitude=50, longitude=8)
    result = reference_places.check(client, "Weekend service", [town])
    assert result.status == "applied" and result.reference_checks[0].meets is True
    condition = Condition(text="Near a service", understood_as="Near a service", kind="near",
                          status="estimate", max_minutes=50, travel_mode="transit",
                          anchor=Anchor(min_people=100000, looked_up=True,
                                        research_status="applied", look_up="Weekend service",
                                        reference_checks=result.reference_checks))
    assert condition.reference_status == "applied"
    job = JobGroup([FoundJob(source="fictional", source_job_id="1", title="Nurse",
                            url="https://example.test/job", country="DE", latitude=50,
                            longitude=8, location_text="Springford")])
    monkeypatch.setattr(travel, "anchor_towns", lambda *args: [town])
    condition.travel[travel.job_key(job)] = {"minutes": {"Springford": 0}, "by": "distance"}
    assert travel.answer(condition, job) == "yes" and len(client.calls) == 1


def test_later_comparison_failure_keeps_each_completed_city_and_buys_no_hosted_research(
        monkeypatch):
    from jobcu import reference_places

    names = [f"Fictional City {i}" for i in range(9)]
    body = "\n".join(f"{name}: {FACT}" for name in names)
    rows = [reply(id=f"C{i}", quotes=[reference_sources.Quote(
        source_id="S0", words=f"{name}: {FACT}")]) for i, name in enumerate(names[:8])]
    client = Client([page(towns=names)], rows)
    original = client.generate

    def generate(output, **request):
        if client.calls:
            client.failure = True
        assert request["max_output_tokens"] == reference_sources.ANSWER_TOKENS
        return original(output, **request)

    client.generate = generate
    monkeypatch.setattr(reference_sources, "PoliteClient", lambda **kw: HTTP(body))
    towns = [SimpleNamespace(name=n, country="DE", latitude=50, longitude=i)
             for i, n in enumerate(names)]
    result = reference_places.check(client, "Weekend service", towns)
    assert [c.meets for c in result.reference_checks] == [True] * 8 + [None]
    assert all(c.evidence and c.sources for c in result.reference_checks[:8])
    assert "Checked 8 of 9" in result.note and len(client.calls) == 2


@pytest.mark.parametrize("rows,reason", [([], "omitted"),
    ([reply(meets=None, explanation="The two bounds overlap.")], "Unverified comparison"),
    ([reply(quotes=[])], "supporting quotes")])
def test_missing_facts_and_rejected_evidence_keep_their_actual_unchecked_reason(rows, reason):
    checks = [city()]
    reference_sources.check(Client([page()], rows), "Weekend service", checks, http=HTTP())
    assert checks[0].meets is None and checks[0].checked_at is None
    assert reason in checks[0].evidence and not checks[0].sources


def test_same_named_county_cannot_replace_a_reviewed_city_or_buy_a_comparison():
    client = Client([page(required_labels_by_town={"Springford": "07 1 02 Springford, City"})])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks,
                            http=HTTP("07 1 03 Springford, County: service available"))
    assert not client.calls and checks[0].meets is None
    assert "geographic unit" in checks[0].evidence


@pytest.mark.parametrize("quote,expected", [("07 1 03 Springford, County", None),
                                           ("07 1 02 Springford, City", True)])
def test_geographic_identity_is_required_in_the_citation_even_beside_a_same_named_county(
        quote, expected):
    client = Client([page(required_labels_by_town={"Springford": "07 1 02 Springford, City"})],
                    [reply(quotes=[reference_sources.Quote(source_id="S0", words=quote)])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(
        "07 1 02 Springford, City: service available\n07 1 03 Springford, County: unavailable"))
    assert checks[0].meets is expected
    assert "07 1 02 Springford, City" in client.calls[0]["prompt"]
