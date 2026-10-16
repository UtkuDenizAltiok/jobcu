"""Conservative finite-city decisions with entirely fictional places and jobs."""
from jobcu import travel
from jobcu.dedupe import JobGroup
from jobcu.location import Anchor, Condition
from jobcu.places import Town
from jobcu.sources.base import FoundJob


def scenario(monkeypatch):
    towns = [Town(f'City {i}', 'DE', 50 + i * .2, 9, 500_000) for i in range(3)]
    monkeypatch.setattr(travel, 'anchor_towns', lambda anchor, country: towns)
    job = JobGroup([FoundJob('fictional', 'nurse-1', 'https://jobs.example.test/nurse-1',
                            'Nurse', location_text='Independent Village', country='DE',
                            latitude=50, longitude=8.8)])
    condition = Condition(text='Within 50 minutes of a large city', understood_as='…',
                          kind='near', status='applied', max_minutes=50,
                          anchor=Anchor(description='Large cities'))
    return towns, job, condition


def test_a_third_unmeasured_city_prevents_a_false_rejection(monkeypatch):
    towns, job, condition = scenario(monkeypatch)
    condition.travel[travel.job_key(job)] = {
        'minutes': {towns[0].name: 60, towns[1].name: None}, 'by': travel.MAPS}
    assert travel.answer(condition, job) == 'unknown'
    condition.travel[travel.job_key(job)]['minutes'][towns[2].name] = 30
    assert travel.answer(condition, job) == 'yes'
    condition.travel[travel.job_key(job)]['minutes'][towns[2].name] = 70
    assert travel.answer(condition, job) == 'no'


def test_a_different_workplace_cannot_reuse_a_passing_journey(monkeypatch):
    towns, job, condition = scenario(monkeypatch)
    condition.travel[travel.job_key(job)] = {
        'point': '49.000,7.000', 'minutes': {towns[0].name: 10}, 'by': travel.MAPS}
    assert travel.answer(condition, job) == 'unknown'
    assert '10 min' not in (travel.detail(condition, job) or ('', ''))[0]


def test_legacy_geometric_zero_does_not_override_an_independent_town(monkeypatch):
    towns, job, condition = scenario(monkeypatch)
    # Its coordinates lie within the rough city's radius; its named workplace is different.
    job.copies[0].latitude, job.copies[0].longitude = 50, 9.01
    assert travel.home_town(travel.job_point(job), towns) is None
    condition.travel[travel.job_key(job)] = {'minutes': {towns[0].name: 0}, 'by': 'distance'}
    assert travel.answer(condition, job) == 'unknown'
    assert not travel.detail(condition, job)[0].startswith('in City')


def test_named_city_does_not_make_a_city_centre_journey_zero(monkeypatch):
    towns, job, condition = scenario(monkeypatch)
    point = travel.Point(50, 9.1, 'DE', 'address', towns[0].name)
    assert travel.home_town(point, towns) == towns[0]
    assert travel.home_town(point, towns, to_centre=True) is None
