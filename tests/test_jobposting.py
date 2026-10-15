import json
from datetime import UTC, datetime

import pytest

from jobcu.jobposting import find_job_posting
from jobcu.sources.adzuna import AdzunaSource


def page(posting: dict, wrap_in_graph=False) -> str:
    data = {"@context": "https://schema.org", "@graph": [{"@type": "WebPage"}, posting]} \
        if wrap_in_graph else posting
    return f'<html><script type="application/ld+json">{json.dumps(data)}</script></html>'


POSTING = {
    "@type": "JobPosting",
    "title": "Power Electronics Engineer",
    "description": "<p>You design <b>inverters</b>.</p><ul><li>PCB layout</li></ul>" * 10,
    "datePosted": "2026-09-16T08:30:00+02:00",
    "employmentType": ["FULL_TIME", "INTERN"],
    "hiringOrganization": {"@type": "Organization", "name": "Acme GmbH"},
    "jobLocation": [{"@type": "Place", "address": {"addressLocality": "München"}}],
    "jobLocationType": "TELECOMMUTE",
}


def test_job_posting_data_is_read_even_inside_a_graph():
    posting = find_job_posting(page(POSTING, wrap_in_graph=True))
    assert posting.title == "Power Electronics Engineer"
    assert "• PCB layout" in posting.description and "<b>" not in posting.description
    assert posting.date_posted == datetime(2026, 9, 16, 6, 30, tzinfo=UTC)
    assert posting.company == "Acme GmbH" and posting.location_text == "München"
    assert posting.job_types == ["full_time_permanent", "fixed_term",
                                 "internship_or_working_student"]
    assert posting.remote


def test_job_data_with_an_encoded_type_and_raw_line_breaks_is_read():
    # ECM Selection writes the "+" as "&#x2B;", and many sites leave line breaks in the text.
    page = ('<script type="application/ld&#x2B;json">{"@type": "JobPosting", '
            '"title": "Graduate Electronics Engineer", "datePosted": "2026-09-30", '
            '"description": "<p>Design boards.\nTest them.</p>", "jobLocation": {"@type": '
            '"Place", "address": {"addressLocality": "Nottingham"}}}</script>')
    found = find_job_posting(page)
    assert found.title == "Graduate Electronics Engineer"
    assert found.location_text == "Nottingham" and "Test them" in found.description


def test_pages_without_job_data_give_nothing():
    assert find_job_posting("<html><script type='application/ld+json'>{bad json</script>") is None
    assert find_job_posting(page({"@type": "Organization"})) is None


@pytest.mark.parametrize(('title', 'duties', 'skills'), [
    ('Hardware Engineer', 'Design isolated power converters.', 'Gate-drive measurements'),
    ('Nurse', 'Provide patient care.', 'Current nursing registration'),
    ('Teacher', 'Teach mathematics.', 'Classroom assessment'),
])
def test_separate_original_requirements_reach_the_ad_text(title, duties, skills):
    found = find_job_posting(page({
        '@type': 'JobPosting', 'title': title, 'description': '<p>Join Example.</p>',
        'responsibilities': duties, 'skills': ['<b>' + skills + '</b>', 'German C1 required'],
        'qualifications': 'Certification preferred, not required.',
        'experienceRequirements': {'@type': 'OccupationalExperienceRequirements',
                                   'monthsOfExperience': 36},
        'educationRequirements': {'@type': 'EducationalOccupationalCredential',
                                  'credentialCategory': 'Bachelor degree',
                                  'about': 'Applied science'},
        'experienceInPlaceOfEducation': True,
        'eligibilityToWorkRequirement': 'Existing work permission required; no sponsorship.',
    }))
    assert duties in found.description and skills in found.description
    assert 'German C1 required' in found.description
    assert 'Certification preferred, not required.' in found.description
    assert '36 months' in found.description and 'Bachelor degree' in found.description
    assert 'Applied science' in found.description
    assert 'Experience instead of education: Yes' in found.description
    assert 'no sponsorship.' in found.description
    assert '<b>' not in found.description and '@type' not in found.description


def test_structured_fields_do_not_invent_text_or_a_complete_ad():
    found = find_job_posting(page({
        '@type': 'JobPosting', 'title': 'Lab Technician',
        'skills': {'@type': 'DefinedTerm', 'description': 'Sample preparation'},
        'educationRequirements': {'@type': 'EducationalOccupationalCredential',
                                  'url': 'https://credentials.example/unknown'},
        'experienceRequirements': {'@type': 'OccupationalExperienceRequirements',
                                   'monthsOfExperience': None},
        'qualifications': [None, False, 123, {'unrelated': 'Do not import this'}],
    }))
    assert found.description == 'Skills:\nSample preparation'
    assert not found.description_is_complete


def test_identical_sections_are_not_repeated_but_distinct_skill_names_survive():
    found = find_job_posting(page({
        '@type': 'JobPosting',
        'description': '<p>JavaScript required.</p><p>Skills:<br>German C1 required.</p>',
        'skills': ['German C1 required.', 'Java', 'Java'],
    }))
    assert found.description.count('German C1 required.') == 1
    assert found.description.endswith('Skills:\nJava')


def test_short_identical_values_keep_their_requirement_context_and_negation():
    found = find_job_posting(page({
        '@type': 'JobPosting', 'description': 'No German C1 required. Experience: Not required.',
        'qualifications': 'German C1 required.', 'securityClearanceRequirement': 'Not required.',
    }))
    assert 'Qualifications:\nGerman C1 required.' in found.description
    assert 'Security clearance:\nNot required.' in found.description


def test_adzuna_never_reads_its_own_job_pages():
    # Its firewall and robots.txt refuse Jobcu: the full ad comes from
    # the same job on another site, or from the person's AI reading it online.
    from jobcu.sources.base import JobSource

    assert AdzunaSource.load_details is JobSource.load_details
