"""Fictional vacancy evidence; no provider requests or personal data."""
import pytest
from test_scoring import PLAN, PROFILE, Scripted, client, groups, score_json

from jobcu.scoring import (
    JobScore,
    evidence_priority,
    finish,
    judge,
    score_groups,
    sponsorship_confirmed,
    with_ad_read_online,
)


@pytest.mark.parametrize('role', ['Electronics Engineer', 'Teacher', 'Nurse', 'Chef'])
def test_uk_deduction_is_exact_and_survives_caps_and_repeated_judgement(role):
    person = PROFILE.model_copy(update={'field': role, 'target_roles': [role]})
    raw = JobScore.model_validate(score_json('J0', role=30))
    original = finish(raw, person, country='DE', ad_text='Design work.')
    uk = finish(raw, person, country='GB', ad_text='Design work.')
    assert original['score'] == 80  # role band already limits the total
    assert uk['score'] == 75
    assert sum(d['points'] for d in uk['deductions']) == 5
    assert judge(uk, person)['score'] == 75
    assert evidence_priority(uk) == 80  # missing sponsorship must not block its own research
    assert uk['parts'] == original['parts']


@pytest.mark.parametrize('words', [
    'Visa sponsorship is available for this role',
    'We offer visa sponsorship for the successful applicant',
    'We will sponsor your visa',
])
def test_only_explicit_supported_offer_removes_the_deduction(words):
    raw = JobScore.model_validate(score_json('J0', visa_sponsorship='available_for_this_job',
                                              visa_sponsorship_words=words))
    result = finish(raw, PROFILE, country='GB', ad_text=words + '.')
    assert result['deductions'] == []
    assert result['evidence']['sponsorship_confirmed'] is True


@pytest.mark.parametrize(('words', 'ad'), [
    ('Visa sponsorship is available', 'Visa sponsorship is not available.'),
    ('offer visa sponsorship', 'We do not offer visa sponsorship.'),
    ('offer visa sponsorship', 'We won’t offer visa sponsorship.'),
    ('offer visa sponsorship', "We don't offer visa sponsorship."),
    ('Visa sponsorship is available', 'Visa sponsorship is available subject to approval.'),
    ('Visa sponsorship is available', 'Visa sponsorship is available for some roles.'),
    ('We hold a sponsor licence', 'We hold a sponsor licence.'),
    ('International candidates welcome', 'International candidates welcome.'),
    ('Visa sponsorship is available', 'Relocation assistance is provided.'),
    ('Visa sponsorship may be considered', 'Visa sponsorship may be considered.'),
    ('No sponsorship required', 'No sponsorship required.'),
])
def test_negative_conditional_company_policy_and_invented_quotes_stay_deducted(words, ad):
    assert not sponsorship_confirmed('available_for_this_job', words, ad)


def test_profile_visa_eligibility_is_not_an_employer_offer():
    raw = JobScore.model_validate(score_json('J0'))
    person = PROFILE.model_copy(update={'work_authorisation': 'Eligible for an independent visa'})
    result = finish(raw, person, country='GB', ad_text='Teacher wanted.')
    assert result['deductions'][0]['points'] == 5
    assert finish(raw, person, country='IE')['deductions'] == []
    assert finish(raw, person, country=None)['deductions'] == []


def test_batch_scoring_keeps_the_actual_vacancy_country():
    found = groups('Teacher')
    found[0].copies[0].country = 'GB'
    adapter = Scripted(lambda request: {'scores': [score_json('J0')]})
    result = score_groups(client(adapter), PROFILE, PLAN, found, [0])[0]
    assert result['evidence']['job_country'] == 'GB'
    assert result['deductions'][0]['points'] == 5


def test_online_recovery_changes_the_deduction_without_doubling_it():
    result = finish(JobScore.model_validate(score_json('J0')), PROFILE, country='GB')
    original = result['score']
    confirmed = with_ad_read_online(result, PROFILE, [], None, sponsorship_confirmed=True)
    assert confirmed['score'] == original + 5
    assert confirmed['deductions'] == []
    missing = with_ad_read_online(confirmed, PROFILE, [], None, sponsorship_confirmed=False)
    assert missing['score'] == original


def test_screening_uncertainty_is_explicit_without_inventing_ineligibility():
    raw = JobScore.model_validate(score_json('J0', citizenship_or_clearance=
        'required_possible_or_unclear', citizenship_or_clearance_words='may require screening'))
    result = finish(raw, PROFILE)
    assert any('eligibility is unconfirmed: may require screening' in n for n in result['notes'])
    assert not any(limit['at'] == 30 for limit in result['limits'])


def test_online_offer_is_scoped_to_its_own_vacancy_notes():
    from test_jobplace import Researcher, jobs, online

    from jobcu.jobplace import find_online

    offer = 'Visa sponsorship is available for this role'
    structured = [{**online(f'J{i}'), 'visa_sponsorship': 'available_for_this_job',
                   'visa_sponsorship_words': offer} for i in range(2)]
    researcher = Researcher([f'JOB J0\n{offer}.\nJOB J1\nSponsorship is not offered.'],
                            [structured])
    found = find_online(researcher, jobs(('Town A', 'GB'), ('Town B', 'GB')), [0, 1])
    assert found.requirements[0].blockers['sponsorship_confirmed'] is True
    assert found.requirements[1].blockers['sponsorship_confirmed'] is False
    assert len(researcher.prompts) == len(researcher.structure_prompts) == 1


def test_the_deduction_never_produces_a_negative_score():
    from test_scoring import SPEAKER

    raw = JobScore.model_validate(score_json('J0', role=0, seniority=0, hard_requirements=0,
        location_and_preferences=0, languages_asked=[
            {'language': 'German', 'level': 'C2', 'must_have': True}]))
    result = finish(raw, SPEAKER, country='GB')
    assert result['score'] == 0
    assert result['deductions'][0]['points'] == 5
