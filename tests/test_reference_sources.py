"""Current fictional sources support bounded reference checks across user conditions."""

import csv
import io
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
    provider_id = "gemini"

    def __init__(self, pages, rows=None, fact="Weekend service", failure=False,
                 model="fictional-model"):
        self.settings = Settings(place_evidence=[PlaceEvidenceSet(
            fact_key=reference_sources.fact_key(fact), sources=pages)])
        self.rows = [reply()] if rows is None else rows
        self.calls, self.failure, self.model = [], failure, model

    def checkpoint(self):
        pass

    def model_for(self, reasoning):
        return self.model

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
    # It reads the source again for a later check; a changed page is compared again.
    later = [city()]
    reference_sources.check(client, condition, later, http=HTTP("The service has closed."))
    assert later[0].meets is None and len(client.calls) == 2  # the old quote is gone


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


REQUEST = "Germany. Live in a fictional city that has a staffed weekend service."


def test_reviewed_request_applies_to_its_single_fact_whatever_its_wording():
    client = Client([page()], fact="Weekend service")
    client.settings.place_evidence[0].request_key = reference_sources.request_key(REQUEST)
    checks = [city()]
    reference_sources.check(client, "The city must have a staffed weekend service", checks,
                            http=HTTP(), request=f"  {REQUEST} ")
    assert checks[0].meets is True and len(client.calls) == 1


@pytest.mark.parametrize("request_text", [None, "Germany. Live in a fictional city."])
def test_reworded_fact_without_the_same_single_fact_request_buys_nothing(request_text):
    client, http = Client([page()], fact="Weekend service"), HTTP()
    client.settings.place_evidence[0].request_key = reference_sources.request_key(REQUEST)
    checks = [city()]
    reference_sources.check(client, "The city must have a staffed weekend service", checks,
                            http=http, request=request_text)
    assert checks[0].meets is None and not client.calls and not http.calls


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


def test_additional_context_pages_do_not_disable_a_complete_city_comparison():
    pages = [page(), *[page(url=f"https://context.example.test/{i}", towns=[])
                      for i in range(8)]]
    client, checks = Client(pages), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP())
    assert checks[0].meets is True and len(client.calls) == 1


def test_each_country_gets_its_own_comparison_and_source_identity():
    pages = [page(), page(url="https://second.example.test/services", country="GB")]
    client, checks = Client(pages), [city(), city(country="GB")]
    reference_sources.check(client, "Weekend service", checks, http=HTTP())
    assert [c.meets for c in checks] == [True, True] and len(client.calls) == 2
    assert all("C1 |" not in call["prompt"] for call in client.calls)


def test_overloaded_country_batch_keeps_an_independent_country_available():
    pages = [page(), *[page(url=f"https://context.example.test/{i}", towns=[])
                      for i in range(16)],
             page(url="https://second.example.test/services", country="GB")]
    client, checks = Client(pages), [city(), city(country="GB")]
    reference_sources.check(client, "Weekend service", checks, http=HTTP())
    assert [c.meets for c in checks] == [None, True] and len(client.calls) == 1
    assert "page limit" in checks[0].evidence


def csv_text(rows, *, delimiter=","):
    output = io.StringIO(newline="")
    csv.writer(output, delimiter=delimiter, lineterminator="\n").writerows(rows)
    return output.getvalue()


def selected_csv_page(**extra):
    selection = {"columns": ["City", "Date", "Service", "Count"],
                 "equals": {"City": ["Springford"], "Date": ["2030-01-02"]}}
    selection.update(extra)
    return page(csv_selection=selection,
                required_labels_by_town={"Springford": "Springford"})


@pytest.mark.parametrize("condition", ["Circuit-training service", "Weekend nursing service",
                                       "Bilingual teaching service"])
def test_complete_large_csv_preserves_all_reviewed_rows_within_existing_input_budget(condition):
    rows = [["City", "Date", "Service", "Count", "Unneeded metadata"]]
    rows.extend([["Otherford", "2030-01-02", "Unavailable", "0", "x" * 600]
                 for _ in range(1000)])
    rows.extend([["Springford", "2030-01-02", "Staffed", "14", "x" * 600],
                 ["Springford", "2030-01-02", "Night", "0", "x" * 600]])
    body = csv_text(rows)
    assert reference_sources.MAX_CONTEXT_CHARS < len(body) < reference_sources.MAX_DOCUMENT_BYTES
    quote = "Springford,2030-01-02,Staffed,14"
    client = Client([selected_csv_page()], [reply(quotes=[reference_sources.Quote(
        source_id="S0", words=quote)])], fact=condition)
    checks = [city()]
    sources = reference_sources.check(client, condition, checks, http=HTTP(body))
    assert checks[0].meets is True and sources[0].url == CITY_URL
    assert len(client.calls) == 1 and len(client.calls[0]["prompt"]) < 2000
    assert "City,Date,Service,Count\n" in client.calls[0]["prompt"]
    assert "Springford,2030-01-02,Night,0" in client.calls[0]["prompt"]
    assert "Otherford" not in client.calls[0]["prompt"]
    assert "Unneeded metadata" not in client.calls[0]["prompt"]


def test_csv_scope_is_exact_fresh_and_cannot_reuse_an_old_city_quotation():
    header = ["City", "Date", "Service", "Count"]
    first = csv_text([header, ["Springford", "2030-01-02", "Staffed", "14"],
                      ["Springford County", "2030-01-02", "Staffed", "99"],
                      ["Springford", "2029-01-02", "Staffed", "98"]])
    quote = "Springford,2030-01-02,Staffed,14"
    client = Client([selected_csv_page()], [reply(quotes=[reference_sources.Quote(
        source_id="S0", words=quote)])])
    original = [city()]
    reference_sources.check(client, "Weekend service", original, http=HTTP(first))
    assert original[0].meets is True
    assert "County" not in client.calls[0]["prompt"]
    assert "2029-01-02" not in client.calls[0]["prompt"]
    changed = [city()]
    reference_sources.check(client, "Weekend service", changed, http=HTTP(csv_text(
        [header, ["Springford", "2030-01-02", "Closed", "0"]])))
    assert changed[0].meets is None and len(client.calls) == 2
    absent = [city()]
    reference_sources.check(client, "Weekend service", absent, http=HTTP(csv_text(
        [header, ["Springford County", "2030-01-02", "Staffed", "99"]])))
    assert absent[0].meets is None and len(client.calls) == 2


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_csv_preserves_bom_quoted_delimiters_newlines_zeroes_and_all_allowed_values(delimiter):
    rows = [["City", "Date", "Service", "Count", "Ignored"],
            ["Springford", "2030-01-02", 'Night, day; and\tweekend\n"staffed"', "0", "noise"],
            ["Springford", "2030-01-03", "Later", "2", "noise"]]
    body = "\ufeff" + csv_text(rows, delimiter=delimiter)
    source = selected_csv_page(delimiter=delimiter,
                              equals={"Date": ["2030-01-02", "2030-01-03"]})
    content = reference_sources._read(HTTP(body), source, {})
    parsed = list(csv.reader(io.StringIO(content, newline=""), delimiter=delimiter))
    assert parsed == [row[:4] for row in rows]


@pytest.mark.parametrize("body", [
    "", "City,Date,Service,Count\n",  # a header is not evidence that a count is zero
    "City,Date,Service,Service,Count\nSpringford,2030-01-02,Staffed,Staffed,14\n",
    "City,Date,Service\nSpringford,2030-01-02,Staffed\n",
    "City,Date,Service,Count\nSpringford,2030-01-02,Staffed,14\nOtherford,2030-01-02\n",
    'City,Date,Service,Count\nSpringford,2030-01-02,"Staffed,14\n',
    "City,Date,Service,Count\nSPRINGFORD,2030-01-02,Staffed,14\n",
    "City,Date,Service,Count\n Springford,2030-01-02,Staffed,14\n",
    "<html>Login or download temporarily unavailable</html>",
    "%PDF fictional table",  # CSV selection must never fall back to a different reader
])
def test_invalid_incomplete_or_nonmatching_csv_buys_no_comparison(body):
    client, checks = Client([selected_csv_page()]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert not client.calls and checks[0].meets is None and not checks[0].sources


def test_csv_unknown_filter_column_and_dropped_geographic_label_cannot_pass():
    body = "City,Date,Service,Count\nSpringford,2030-01-02,Staffed,14\n"
    pages = [selected_csv_page(equals={"District": ["Springford"]}),
             selected_csv_page(columns=["Date", "Service", "Count"])]
    for source in pages:
        client, checks = Client([source]), [city()]
        reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
        assert not client.calls and checks[0].meets is None


def test_csv_projection_preserves_network_and_context_bounds_without_partial_evidence(monkeypatch):
    body = "City,Date,Service,Count\nSpringford,2030-01-02,Staffed,14\n"
    for http in (HTTP(body, robots="User-agent: *\nDisallow: /"), HTTP(body, status=302)):
        client = Client([selected_csv_page()])
        reference_sources.check(client, "Weekend service", [city()], http=http)
        assert not client.calls
    for limit, value in [("MAX_DOCUMENT_BYTES", 25), ("MAX_CONTEXT_CHARS", 25)]:
        with monkeypatch.context() as patch:
            patch.setattr(reference_sources, limit, value)
            client, checks = Client([selected_csv_page()]), [city()]
            reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
            assert not client.calls and checks[0].meets is None


@pytest.mark.parametrize("condition", ["Circuit-training capacity", "Weekend nursing capacity",
                                       "Bilingual teaching capacity"])
@pytest.mark.parametrize("meets", [True, False])
def test_geography_citation_cannot_replace_a_required_city_measurement(condition, meets):
    pages = [page(),
             page(url="https://city.example.test/counts", must_cite_for_towns=["Springford"])]
    client = Client(pages, [reply(meets=meets)], fact=condition)
    checks = [city()]
    reference_sources.check(client, condition, checks, http=HTTP())
    assert checks[0].meets is None and not checks[0].sources
    assert "required" in checks[0].evidence.lower()


def test_unavailable_required_reference_does_not_buy_an_unsupported_comparison():
    class MissingTable(HTTP):
        def get(self, url, **options):
            if url.endswith("/counts"):
                return httpx.Response(403, text="Unavailable")
            return super().get(url, **options)

    pages = [page(), page(url="https://city.example.test/counts",
                          must_cite_for_towns=["Springford"])]
    client, checks = Client(pages), [city()]
    reference_sources.check(client, "Weekend service", checks, http=MissingTable())
    assert checks[0].meets is None and not client.calls
    assert "required" in checks[0].evidence.lower()


def test_a_required_table_quote_for_another_city_cannot_borrow_geography_from_context():
    source = page(url="https://city.example.test/counts", towns=["Springford", "Otherford"],
                  must_cite_for_towns=["Springford"],
                  required_labels_by_town={"Springford": "F101 Springford"})
    words = "F101 Springford: 14 staff.\nF102 Otherford: 99 staff."
    client = Client([page(), source], [reply(quotes=[
        reference_sources.Quote(source_id="S0", words=FACT),
        reference_sources.Quote(source_id="S1", words="F102 Otherford: 99 staff.")])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(words + "\n" + FACT))
    assert checks[0].meets is None and not checks[0].sources


@pytest.mark.parametrize("meets", [True, False])
def test_all_current_required_city_and_country_quotes_admit_the_supported_result(meets):
    pages = [page(required_labels_by_town={"Springford": "F101 Springford"},
                  must_cite_for_towns=["Springford"]),
             page(url=NATIONAL_URL, towns=[], must_cite_for_towns=["Springford"])]
    words = "F101 Springford: 14 staff.\nNational comparison threshold: 10 staff."
    client = Client(pages, [reply(meets=meets, quotes=[
        reference_sources.Quote(source_id="S0", words="F101 Springford: 14 staff."),
        reference_sources.Quote(source_id="S1",
                                words="National comparison threshold: 10 staff.")])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(words))
    assert checks[0].meets is meets and checks[0].checked_at and len(checks[0].sources) == 2
    assert 'required source IDs: ["S0", "S1"]' in client.calls[0]["prompt"]


def test_missing_required_city_label_is_rejected_before_a_paid_comparison():
    pages = [page(), page(url="https://city.example.test/counts",
                          must_cite_for_towns=["Springford"],
                          required_labels_by_town={"Springford": "F101 Springford"})]
    client, checks = Client(pages), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(FACT))
    assert checks[0].meets is None and not client.calls


def test_a_missing_dependency_keeps_an_independent_city_available():
    class MissingTable(HTTP):
        def get(self, url, **options):
            if url.endswith("/counts"):
                return httpx.Response(403, text="Unavailable")
            return super().get(url, **options)

    quote = "Otherford: " + FACT
    pages = [page(towns=["Springford", "Otherford"]),
             page(url="https://city.example.test/counts", must_cite_for_towns=["Springford"])]
    client = Client(pages, [reply(quotes=[reference_sources.Quote(source_id="S0", words=quote)])])
    checks = [city(), city(name="Otherford")]
    reference_sources.check(client, "Weekend service", checks, http=MissingTable(quote))
    assert [c.meets for c in checks] == [None, True]
    assert len(client.calls) == 1 and "C0 | Otherford" in client.calls[0]["prompt"]


def test_conflicting_required_city_scope_cannot_silently_drop_the_dependency():
    pages = [page(), page(url="https://city.example.test/counts", towns=["Otherford"],
                          must_cite_for_towns=["Springford"])]
    client, checks = Client(pages), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(FACT))
    assert checks[0].meets is None and not client.calls


def calculated_page():
    return page(csv_selection={"columns": ["City", "Group", "Member", "Count"],
        "calculation": {"group_by": ["Group"], "sum_columns": ["Count"],
                        "row_identity": ["Member"]}}, must_cite_for_towns=["Springford"],
        required_labels_by_town={"Springford": "Springford"})


def calculation_quote(total=1000, *, kind="calculation"):
    return reference_sources.Quote(source_id="S0", kind=kind,
        words=csv_text([["total", "Springford", "", total, 1000, "", ""]]).rstrip())


@pytest.mark.parametrize("condition", ["Circuit-training capacity", "Weekend nursing capacity",
                                       "Bilingual teaching capacity"])
def test_exact_calculation_avoids_raw_input_overload_without_losing_source_rows(condition):
    rows = [["City", "Group", "Member", "Count"],
            *[["Springford", "A", "x" * 600 + str(i), "1"] for i in range(1000)]]
    body = csv_text(rows)
    assert len(body) > reference_sources.MAX_CONTEXT_CHARS
    client = Client([calculated_page()], [reply(quotes=[calculation_quote()])], fact=condition)
    checks = [city()]
    sources = reference_sources.check(client, condition, checks, http=HTTP(body))
    assert checks[0].meets is True and sources[0].url == CITY_URL
    assert len(client.calls[0]["prompt"]) < 3000
    assert "LOCAL CALCULATION" in client.calls[0]["prompt"]
    assert checks[0].evidence.startswith("Includes exact totals calculated locally")
    assert '"kind": "calculation"' in checks[0].evidence


@pytest.mark.parametrize("quote", [calculation_quote(999), calculation_quote(kind="source"),
    reference_sources.Quote(source_id="S0", kind="calculation", words="Springford,A,one,1")])
def test_invented_calculations_and_mislabelled_publisher_quotes_cannot_pass(quote):
    body = csv_text([["City", "Group", "Member", "Count"], ["Springford", "A", "one", "1"]])
    client, checks = Client([calculated_page()], [reply(quotes=[quote])]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert checks[0].meets is None and not checks[0].sources


def test_current_raw_source_quotes_remain_verifiable_beside_calculations():
    words = "Springford,A,one,1"
    body = "City,Group,Member,Count\n" + words + "\n"
    client = Client([calculated_page()], [reply(quotes=[reference_sources.Quote(
        source_id="S0", words=words)])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert checks[0].meets is True
    assert not checks[0].evidence.startswith("Includes exact totals calculated locally")


@pytest.mark.parametrize("body", [
    "City,Group,Member,Count\nSpringford,A,one,1\nOtherford,A,two,2\n",
    "City,Group,Member,Count\nSpringford,A,one,1\nSpringford,A,two,NaN\n",
])
def test_ambiguous_or_invalid_calculation_buys_no_comparison(body):
    client, checks = Client([calculated_page()]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert not client.calls and checks[0].meets is None


@pytest.mark.parametrize("limit", ["MAX_DOCUMENT_BYTES", "MAX_CONTEXT_CHARS"])
def test_calculated_views_keep_the_original_network_and_per_source_input_limits(monkeypatch, limit):
    monkeypatch.setattr(reference_sources, limit, 10)
    body = "City,Group,Member,Count\nSpringford,A,one,1\n"
    client, checks = Client([calculated_page()]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert not client.calls and checks[0].meets is None


def test_multiple_calculations_still_obey_the_combined_context_budget(monkeypatch):
    first = calculated_page()
    second = first.model_copy(update={"url": "https://second.example.test/counts"})
    body = "City,Group,Member,Count\nSpringford,A,one,1\n"
    view = reference_sources.calculate(body, first.csv_selection)
    monkeypatch.setattr(reference_sources, "MAX_CONTEXT_CHARS", 2 * len(view) - 1)
    assert reference_sources._read(HTTP(body), first, {}) == body
    client, checks = Client([first, second]), [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP(body))
    assert not client.calls and checks[0].meets is None


def test_a_calculation_citation_is_not_available_for_an_untransformed_source():
    client = Client([page()], [reply(quotes=[reference_sources.Quote(
        source_id="S0", words=FACT, kind="calculation")])])
    checks = [city()]
    reference_sources.check(client, "Weekend service", checks, http=HTTP())
    assert checks[0].meets is None and not checks[0].sources


def test_calculating_a_required_source_cannot_drop_its_geographic_identity():
    source = calculated_page()
    source.csv_selection.calculation.row_identity.append("City")
    # Declaring the city as an individual-row identity would hide it in named groups.
    client, checks = Client([source]), [city()]
    reference_sources.check(client, "Weekend service", checks,
                            http=HTTP("City,Group,Member,Count\nSpringford,A,one,1\n"))
    assert not client.calls and checks[0].meets is None



def test_identical_evidence_reuses_a_verified_city_verdict_without_another_comparison():
    client = Client([page()])
    first = [city()]
    reference_sources.check(client, "Weekend service", first, http=HTTP())
    again = [city()]
    sources = reference_sources.check(client, "Weekend service", again, http=HTTP())
    assert again[0].meets is True and len(client.calls) == 1
    assert again[0].evidence == first[0].evidence and again[0].checked_at == first[0].checked_at
    assert sources == first[0].sources
    # Another model is another reading: it is asked, never handed this model's verdict.
    other = Client([page()], model="another-fictional-model")
    reference_sources.check(other, "Weekend service", [city()], http=HTTP())
    assert len(other.calls) == 1


def test_an_unknown_city_is_never_kept_and_is_compared_again():
    client = Client([page()], rows=[reply(meets=None)])
    for _ in range(2):
        checks = [city()]
        reference_sources.check(client, "Weekend service", checks, http=HTTP())
        assert checks[0].meets is None
    assert len(client.calls) == 2


def test_a_reused_city_leaves_only_the_others_for_the_comparison():
    lakeside = page("https://lakeside.example.test/services", towns=["Lakeside"])
    client = Client([page(), lakeside])
    reference_sources.check(client, "Weekend service", [city()], http=HTTP())
    both = [city(), city("Lakeside")]
    reference_sources.check(client, "Weekend service", both, http=HTTP())
    assert [c.meets for c in both] == [True, True] and len(client.calls) == 2
    asked = client.calls[1]["prompt"]
    assert "C0 | Lakeside" in asked and "Springford" not in asked
