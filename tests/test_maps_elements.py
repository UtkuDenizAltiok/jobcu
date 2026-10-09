"""Fictional partial route responses: errors must not become job exclusions."""

import json

import httpx
import pytest
from test_location_evidence import card_check
from test_maps_recovery import near, setup
from test_search import ready  # noqa: F401
from test_travel import group

from jobcu import db, travel
from jobcu.ai.base import AIError
from jobcu.countries import COUNTRIES
from jobcu.filters import condition_fit, fails_a_condition
from jobcu.travel import TravelGuess, TravelGuesses


def failed(index=0, code=13):
    return {"destinationIndex": index, "status": {"code": code,
            "message": "Unavailable for projects/fictional-private-id"}}


def measured(index, minutes):
    return {"destinationIndex": index, "status": {}, "condition": "ROUTE_EXISTS",
            "duration": f"{minutes * 60}s"}


def absent(index):
    return {"destinationIndex": index, "status": {}, "condition": "ROUTE_NOT_FOUND"}


def run_case(elements, *, client=None):
    notes, requests = [], []
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=elements)
    meter, http, _, _ = setup(handler)
    meter._note = notes.append
    meter._client = client
    condition, job = near(), group("Freising")
    condition.anchor.research_status = "applied"
    meter.measure([condition], [job], [0])
    return meter, http, condition, job, notes, requests


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
def test_service_errors_retain_uncertain_jobs_and_explain_them(title, caplog):
    meter, http, condition, job, notes, requests = run_case([failed(), failed(1)])
    try:
        job.main.title = title
        assert condition_fit(condition, job) == "unknown"
        assert not fails_a_condition(job, [condition])
        check = card_check(condition, job)
        assert check["status"] == "unclear" and "checked" in check["detail"]
        assert check["source"] == 'Not checked'
        assert "private-id" not in str(notes) + caplog.text
        assert len(requests) == 1 and meter._routes.used_this_search == 2
    finally:
        http.close()


@pytest.mark.parametrize(("elements", "answer"), [
    ([failed(), measured(1, 19)], "yes"),
    ([failed(), measured(1, 60)], "unknown"),
    ([absent(0), measured(1, 60)], "no"),
    ([absent(0), absent(1)], "no"),
    ([absent(0), failed(1)], "unknown"),
    ([measured(1, 60)], "unknown"),
    ([{"destinationIndex": 0, "condition": "ROUTE_EXISTS", "duration": "infs"},
      measured(1, 60)], "unknown"),
])
def test_partial_samples_preserve_measured_success_without_proving_failed_alternatives(
        elements, answer):
    _, http, condition, job, _, _ = run_case(elements)
    try:
        assert condition_fit(condition, job) == answer
        if any(element.get("duration") == "3600s" for element in elements):
            assert "60 min" in travel.detail(condition, job)[0]
            assert travel.detail(condition, job)[1] == travel.MAPS
    finally:
        http.close()


class GuessingClient:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def generate(self, schema, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.replies, AIError):
            raise self.replies
        return TravelGuesses(answers=self.replies)


def test_unknown_routes_use_labelled_fallback_and_only_remember_ai_evidence():
    client = GuessingClient([TravelGuess(id="P0", town="Munich", minutes=22)])
    _, http, condition, job, _, _ = run_case([failed(), failed(1)], client=client)
    try:
        assert condition_fit(condition, job) == "yes"
        assert travel.detail(condition, job) == ("Munich, 22 min by public transport",
                                               travel.ESTIMATE)
        assert card_check(condition, job)["status"] == "estimate"
        assert len(client.calls) == 1
        with db.connect() as conn:
            saved = conn.execute("SELECT minutes, measured_by FROM travel_memory").fetchall()
            assert [(row["minutes"], row["measured_by"]) for row in saved] == [
                (22, travel.ESTIMATE)]
    finally:
        http.close()


def test_omitted_ai_answer_stays_unknown_instead_of_becoming_no_route():
    client = GuessingClient([])
    _, http, condition, job, _, _ = run_case([failed(), failed(1)], client=client)
    try:
        assert len(client.calls) == 1
        assert condition_fit(condition, job) == "unknown"
        with db.connect() as conn:
            assert not conn.execute("SELECT 1 FROM travel_memory").fetchall()
    finally:
        http.close()


@pytest.mark.parametrize('elements', [[failed(), failed(1)], [failed(), measured(1, 60)]])
def test_unchecked_routes_and_partial_attribution_survive_saved_plan_roundtrip(elements):
    _, http, condition, job, _, _ = run_case(elements)
    try:
        restored = type(condition).model_validate_json(condition.model_dump_json())
        assert condition_fit(restored, job) == 'unknown'
        assert travel.detail(restored, job) == travel.detail(condition, job)
        assert card_check(restored, job)['status'] == 'unclear'
    finally:
        http.close()


@pytest.mark.parametrize('bad', [
    {'destinationIndex': 0, 'originIndex': 1, 'condition': 'ROUTE_EXISTS', 'duration': '1s'},
    {'destinationIndex': False, 'condition': 'ROUTE_EXISTS', 'duration': '1s'},
    {'destinationIndex': -1, 'condition': 'ROUTE_EXISTS', 'duration': '1s'},
    {'destinationIndex': 3, 'condition': 'ROUTE_EXISTS', 'duration': '1s'},
    {'destinationIndex': 0, 'status': {'code': '0'}, 'condition': 'ROUTE_NOT_FOUND'},
    {'destinationIndex': 0, 'status': {'code': {}}, 'condition': 'ROUTE_NOT_FOUND'},
    {'destinationIndex': 0, 'status': {'code': []}, 'condition': 'ROUTE_NOT_FOUND'},
    {'destinationIndex': 0, 'status': 'bad', 'condition': 'ROUTE_NOT_FOUND'},
    {'destinationIndex': 0, 'condition': 'ROUTE_EXISTS', 'duration': '-60s'},
    {'destinationIndex': 0, 'condition': 'ROUTE_EXISTS'},
    {'destinationIndex': 0, 'condition': 'UNKNOWN'},
    'malformed element',
])
def test_invalid_elements_do_not_prove_failure_or_supply_a_false_shortcut(bad):
    _, http, condition, job, _, _ = run_case([bad, measured(1, 60)])
    try:
        assert condition_fit(condition, job) == 'unknown'
        assert '60 min' in travel.detail(condition, job)[0]
    finally:
        http.close()


def test_conflicting_matrix_indices_stay_unknown_and_default_zero_fields_work():
    _, http, condition, job, _, _ = run_case([
        measured(0, 1), measured(0, 90), absent(1)])
    try:
        assert condition_fit(condition, job) == 'unknown'
    finally:
        http.close()
    _, http, condition, job, _, _ = run_case([
        {'condition': 'ROUTE_EXISTS', 'duration': '0s'}, absent(1)])
    try:
        assert condition_fit(condition, job) == 'yes'
        assert travel.detail(condition, job)[0] == 'in Munich'
    finally:
        http.close()


@pytest.mark.parametrize('reply', [[], {'unexpected': 'response'}, None])
def test_incomplete_matrix_bodies_stay_unknown(reply):
    _, http, condition, job, _, _ = run_case(reply)
    try:
        assert condition_fit(condition, job) == 'unknown'
    finally:
        http.close()


def test_confirmed_no_route_never_triggers_ai_fallback():
    client = GuessingClient([])
    _, http, condition, job, _, _ = run_case([absent(0), absent(1)], client=client)
    try:
        assert condition_fit(condition, job) == 'no' and not client.calls
        assert travel.detail(condition, job) == (
            'No sampled journey found by public transport', travel.MAPS)
    finally:
        http.close()


@pytest.mark.parametrize('answers', [
    [TravelGuess(id='P0', town='Unrequested city', minutes=1)],
    [TravelGuess(id='P9', town='Munich', minutes=1)],
    [TravelGuess(id='P0', town='Munich', minutes=22),
     TravelGuess(id='P0', town='Munich', minutes=70)],
    AIError('Fictional provider unavailable'),
])
def test_invalid_or_unavailable_fallback_does_not_invent_a_decision(answers):
    _, http, condition, job, _, _ = run_case(
        [failed(), failed(1)], client=GuessingClient(answers))
    try:
        assert condition_fit(condition, job) == 'unknown'
        with db.connect() as conn:
            assert not conn.execute('SELECT 1 FROM travel_memory').fetchall()
    finally:
        http.close()


@pytest.mark.parametrize('mapped_minutes', [19, 60])
def test_mixed_town_readings_preserve_maps_and_label_only_the_needed_estimate(mapped_minutes):
    from jobcu import places
    from jobcu.location import TownRef

    towns = [places.find('Munich', 'DE'), places.find('Landshut', 'DE')]
    requests = []
    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        elements = []
        for index, destination in enumerate(body['destinations']):
            coordinates = destination['waypoint']['location']['latLng']
            town = min(towns, key=lambda t: places.km(
                t.latitude, t.longitude, coordinates['latitude'], coordinates['longitude']))
            elements.append(measured(index, mapped_minutes) if town.name == 'Munich'
                            else failed(index))
        return httpx.Response(200, json=elements)
    meter, http, _, _ = setup(handler)
    client = GuessingClient([TravelGuess(id='P0', town='Landshut', minutes=22)])
    meter._client = client
    condition, job = near(), group('Freising')
    condition.anchor.named.append(TownRef(name='Landshut', country='DE'))
    try:
        meter.measure([condition], [job], [0])
        entry = condition.travel[travel.job_key(job)]
        assert entry['minutes']['Munich'] == mapped_minutes
        assert entry['by_town']['Munich'] == travel.MAPS
        assert condition_fit(condition, job) == 'yes'
        assert len(requests) == 1 and meter._routes.used_this_search == 4
        with db.connect() as conn:
            rows = conn.execute('SELECT minutes, measured_by FROM travel_memory').fetchall()
            saved = [(row['minutes'], row['measured_by']) for row in rows]
        if mapped_minutes == 19:
            assert not client.calls and not saved
            assert card_check(condition, job)['status'] == 'verified'
        else:
            assert len(client.calls) == 1 and saved == [(22, travel.ESTIMATE)]
            assert '| to: Landshut' in client.calls[0]['prompt']
            assert 'Munich' not in client.calls[0]['prompt']
            assert entry['by_town']['Landshut'] == travel.ESTIMATE
            assert travel.detail(condition, job)[1] == travel.ESTIMATE
            assert card_check(condition, job)['status'] == 'estimate'
        meter.measure([condition], [job], [0])
        assert len(requests) == 1 and len(client.calls) == (mapped_minutes != 19)
    finally:
        http.close()


@pytest.mark.parametrize('unit', ['1/d/{project}', '1/mo/{project}', '1/min/{project}'])
def test_persistent_element_quota_preserves_partial_time_and_stops_later_requests(unit, caplog):
    from test_maps_recovery import quota

    error = quota(unit, value='0' if '/min/' in unit else '10').json()['error']
    error['code'] = 8
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[measured(0, 19),
                                         {'destinationIndex': 1, 'status': error}])
    meter, http, clock, _ = setup(handler)
    notes = []
    meter._note = notes.append
    condition, jobs = near(), [group('Freising', '1'), group('Dachau', '2')]
    try:
        meter.measure([condition], jobs, [0, 1])
        assert condition_fit(condition, jobs[0]) == 'yes'
        assert condition_fit(condition, jobs[1]) == 'unknown'
        assert len(requests) == 1 and meter._routes.used_this_search == 2
        assert not clock.sleeps
        assert 'fictional-project' not in str(notes) + caplog.text
    finally:
        http.close()


def test_limit_edits_reuse_partial_passes_but_do_not_reuse_an_old_reference_city():
    from jobcu.location import TownRef

    meter, http, condition, job, _, requests = run_case([failed(), measured(1, 19)])
    try:
        assert condition_fit(condition, job) == 'yes'
        condition.max_minutes = 20
        meter.measure([condition], [job], [0])
        assert len(requests) == 1 and condition_fit(condition, job) == 'yes'
        condition.max_minutes = 15
        meter.measure([condition], [job], [0])
        assert condition_fit(condition, job) == 'unknown'
        assert len(requests) == 1  # the identical HTTP answer is reused within this search
        condition.anchor.named = [TownRef(name='Landshut', country='DE')]
        meter.measure([condition], [job], [0])
        assert len(requests) == 2
        assert 'Munich' not in condition.travel[travel.job_key(job)]['minutes']
    finally:
        http.close()


@pytest.mark.parametrize('country', list(COUNTRIES))
@pytest.mark.parametrize('title', ['Hardware Engineer', 'Primary Teacher'])
def test_route_errors_retain_jobs_in_every_supported_country(country, title):
    from jobcu import places
    from jobcu.location import Anchor, TownRef

    town = places.towns_in(country)[0]
    meter, http, _, _ = setup(lambda request: httpx.Response(200, json=[failed(), failed(1)]))
    condition = near()
    condition.anchor = Anchor(named=[TownRef(name=town.name, country=country)])
    job = group('Fictional workplace', latitude=town.latitude + 0.6, longitude=town.longitude)
    job.main.country, job.main.title = country, title
    try:
        meter.measure([condition], [job], [0])
        assert condition_fit(condition, job) == 'unknown'
        assert not fails_a_condition(job, [condition])
        assert meter._routes.used_this_search == 2
    finally:
        http.close()


@pytest.mark.parametrize('code', [7, 16])
def test_element_access_refusal_keeps_valid_data_and_stops_later_network_reads(code):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[measured(0, 19), failed(1, code)])
    meter, http, _, _ = setup(handler)
    condition, jobs = near(), [group('Freising', '1'), group('Dachau', '2')]
    try:
        meter.measure([condition], jobs, [0, 1])
        assert condition_fit(condition, jobs[0]) == 'yes'
        assert condition_fit(condition, jobs[1]) == 'unknown'
        assert len(requests) == 1
    finally:
        http.close()


@pytest.mark.parametrize(('role', 'field'), [
    ('Hardware Engineer', 'Electronics'), ('Library Assistant', 'Library services'),
])
def test_a_search_scores_and_keeps_uncertain_routes_but_excludes_confirmed_no_routes(
        ready, monkeypatch, role, field):  # noqa: F811
    import re
    from datetime import UTC, datetime

    from conftest import make_pdf
    from test_search import PROFILE, FakeAI, wait_until_done

    from jobcu import documents, search
    from jobcu.ai.base import RawReply, Usage
    from jobcu.settings import SearchForm
    from jobcu.sources.base import FoundJob, JobSource

    documents.save_upload('cv', 'cv.pdf', make_pdf([
        'Alex Example', f'{role} with five years of professional experience.',
        f'Field: {field}.', 'Languages: English fluent.']))
    documents.save_upload('cover_letter', 'letter.txt',
                          f'I want to work as a {role}. '.encode() * 5)
    scored = []
    class RouteAI(FakeAI):
        def complete_json(self, **request):
            kind = request['schema_name']
            if kind == 'Profile':
                answer = {**PROFILE, 'summary': f'Experienced {role}.',
                          'current_or_last_role': role, 'field': field,
                          'skills': ['Teamwork'], 'technical_areas': [],
                          'target_roles': [role], 'target_fields': [field]}
            elif kind == 'SearchWordsAnswer':
                answer = {'terms': [{'text': role, 'language': 'en', 'kind': 'job_title'}]}
            elif kind == 'LocationInterpretation':
                answer = {'understood_as': 'Germany, near Munich.', 'limits_countries': True,
                          'countries': ['DE'], 'places': [], 'conditions_about_places': [{
                              'text': 'Within 35 minutes of Munich', 'understood_as': 'Near Munich',
                              'kind': 'near', 'max_minutes': 35, 'travel_mode': 'transit',
                              'anchor': {'description': 'Munich', 'named': [
                                  {'name': 'Munich', 'country': 'DE'}]}}],
                          'conditions_about_the_job': [], 'outside_supported_area': []}
            elif kind == 'TravelGuesses':
                answer = {'answers': []}  # no invented answer when the provider omits this job
            elif kind == 'QuickPassAnswer':
                answer = {'clearly_unrelated': [], 'places': []}
            elif kind == 'ScoringAnswer':
                scored.extend(re.findall(r'^JOB (J\d+)', request['prompt'], re.MULTILINE))
                return super().complete_json(**request)
            else:
                return super().complete_json(**request)
            return RawReply(json.dumps(answer), Usage(10, 5))

    class PlacedSource(JobSource):
        id, name, kind = 'placed', 'Fictional placed jobs', 'job_board'
        def search(self, query, ctx):
            for job_id, location in [('uncertain', 'Freising'), ('no-route', 'Dachau')]:
                yield FoundJob(source=self.id, source_job_id=job_id,
                               url=f'https://example.test/{job_id}', title=role,
                               company=f'Fictional {job_id}', location_text=location,
                               country='DE', posted_at=datetime.now(UTC), date_precision='exact',
                               description=f'Full fictional {role} duties and requirements.',
                               description_is_complete=True)

    def fake_reading(self, origin, towns, mode, to_centre=False):
        if origin.town == 'Freising':
            return travel.TravelReading({}, {town.name for town in towns})
        return travel.TravelReading({town.name: None for town in towns})

    from jobcu.keystore import KeyStore
    keys = KeyStore()
    keys.set(travel.KEY_NAME, 'fictional-maps-key')
    monkeypatch.setattr('jobcu.ai.client.AIClient.adapter', lambda self: RouteAI())
    monkeypatch.setattr('jobcu.pipeline.all_sources', lambda: [PlacedSource()])
    monkeypatch.setattr(travel.GoogleMaps, 'minutes', fake_reading)
    manager = search.SearchManager()
    manager.start(SearchForm(location_text='Germany, within 35 minutes of Munich'))
    result = wait_until_done(manager)
    assert result['status'] == 'finished', result['error']
    jobs = result['result']['jobs']
    assert len(scored) == 1
    assert [card['location'] for card in jobs['cards']] == ['Freising']
    assert [card['location'] for card in jobs['ruled_out_by_conditions']] == ['Dachau']
    assert jobs['cards'][0]['location_checks'][-1]['status'] == 'unclear'
    assert result['result']['profile']['field'] == field
