from datetime import UTC, datetime
from itertools import permutations

import pytest

from jobcu.dedupe import JobGroup, group_duplicates, normal_company, normal_title, title_similarity
from jobcu.sources.base import FoundJob

KINDS = {"adzuna": "aggregator", "board": "job_board"}
TEXT = "We design power electronics for electric cars and need an engineer. " * 20


def job(source="adzuna", job_id="1", title="Hardware Engineer (m/w/d)", company="Acme GmbH",
        city="München", **extra):
    return FoundJob(source=source, source_job_id=job_id, url=f"https://{source}/{job_id}",
                    title=title, company=company, location_text=city, country="DE", **extra)


def test_names_are_normalised():
    assert normal_company("ACME Deutschland GmbH & Co. KG") == "acme"
    assert normal_title("Hardwareentwickler (m/w/d)") == normal_title("Hardwareentwickler (w/m/d)")


@pytest.mark.parametrize("role,requirement", [
    ("Power Electronics Engineer", "Four years designing power converters are required."),
    ("Registered Nurse", "Current nursing registration is required."),
    ("Primary Teacher", "An education degree and fluent German are required."),
])
@pytest.mark.parametrize("secondary_kind", ["aggregator", "job_board", "linkedin"])
@pytest.mark.parametrize("original_first", [False, True])
def test_longer_secondary_copy_cannot_hide_an_original_requirement(
    role, requirement, secondary_kind, original_first
):
    original = job("official", title=role, description=f"Fictional vacancy. {requirement}",
                   description_is_complete=True)
    secondary = job("secondary", title=role, description="A rewarding fictional role. " * 30,
                    description_is_complete=True)
    copies = [original, secondary] if original_first else [secondary, original]
    group = JobGroup(copies, source_kinds={"official": "employer", "secondary": secondary_kind})
    assert group.best_description_copy is original
    assert requirement in group.best_description_copy.description
    assert group.copies == copies  # retain both source descriptions and identities


@pytest.mark.parametrize("original_text,complete", [("Summary", False), ("", True), (" ", True)])
def test_incomplete_or_empty_original_cannot_displace_usable_complete_text(original_text, complete):
    original = job("official", description=original_text, description_is_complete=complete)
    secondary = job("secondary", description=TEXT, description_is_complete=True)
    group = JobGroup([original, secondary], source_kinds={"official": "employer"})
    assert group.best_description_copy is secondary


def test_same_provenance_keeps_richer_complete_text_and_a_link_does_not_change_provenance():
    short = job("one", description="Fictional complete text.", description_is_complete=True,
                employer_url="https://employer.example.test/jobs/one")
    long = job("two", description=TEXT, description_is_complete=True)
    group = JobGroup([short, long], source_kinds={"one": "aggregator", "two": "aggregator"})
    assert group.best_description_copy is long
    group.source_kinds = {"one": "employer", "two": "employer"}
    assert group.best_description_copy is long


VACANCY_TEXT = " ".join(f"Fictional duty {i} involves development validation and reporting."
                        for i in range(60))


@pytest.mark.parametrize("role", [
    "Power Electronics Engineer", "Registered Nurse", "Primary Teacher"])
def test_recruitment_decorations_do_not_create_more_assessments_of_the_same_ad(role):
    names = [role, f"Gesucht: {role}", f"Wir suchen: {role}", f"{role} gesucht",
             f"{role} - Fictional Works Ltd", f"{role} - Berlin"]
    copies = [job(job_id=str(i), title=title, company="Fictional Works Ltd", city="Deutschland",
                  description=VACANCY_TEXT) for i, title in enumerate(names)]
    grouped = group_duplicates(copies, KINDS)
    assert len(grouped) == 1 and len(grouped[0].copies) == len(copies)
    assert {c.title for c in grouped[0].copies} == set(names)  # original evidence retained


@pytest.mark.parametrize("different", ["text", "town", "level", "reference", "requisition"])
def test_decorated_titles_do_not_override_distinct_vacancy_evidence(different):
    a = job(title="Power Electronics Engineer - Berlin", city="Deutschland",
            description=VACANCY_TEXT, description_is_complete=True)
    b = job(job_id="2", title="Gesucht: Power Electronics Engineer - Berlin", city="Deutschland",
            description=VACANCY_TEXT, description_is_complete=True)
    kinds = dict(KINDS)
    if different == "text":
        b.description = "Community outreach and family care. " * 50
    elif different == "town":
        b.title = "Power Electronics Engineer - Hamburg"
    elif different == "level":
        b.title = "Senior Power Electronics Engineer - Berlin"
    elif different == "reference":
        b.title = "Power Electronics Engineer 99881 - Berlin"
    else:
        a.source = b.source = "employer"
        kinds["employer"] = "employer"
    assert len(group_duplicates([a, b], kinds)) == 2


@pytest.mark.parametrize("company", [
    "Example Recruitment Services", "Example Recruitment Division"])
def test_recruiter_division_label_needs_matching_vacancy_evidence(company):
    first = job(company="Example Recruitment Ltd", description=VACANCY_TEXT)
    second = job(job_id="2", company=company, description=VACANCY_TEXT)
    assert len(group_duplicates([first, second], KINDS)) == 1
    second.description = "Unrelated client position with a different remit. " * 30
    assert len(group_duplicates([first, second], KINDS)) == 2
    second.description = VACANCY_TEXT
    second.country = "IE"
    assert len(group_duplicates([first, second], KINDS)) == 2


@pytest.mark.parametrize("dash", ["‐", "‑", "‒", "–", "—", "﹘", "－"])
@pytest.mark.parametrize("title", [
    "Power Supply Engineer", "Patient Care Nurse", "Early Years Teacher"])
def test_unicode_dashes_keep_word_boundaries_and_one_evidence_unit(dash, title):
    variant = title.replace(" ", dash, 1)
    original = job("board", "original", title=title, company="Fictional Works Ltd",
                   description=TEXT, description_is_complete=True,
                   posted_at=datetime(2026, 10, 1, tzinfo=UTC), date_precision="day")
    summary = job("adzuna", "summary", title=variant, company=f"Fictional{dash}Works Ltd",
                  description="A brief description.",
                  posted_at=datetime(2026, 10, 2, tzinfo=UTC), date_precision="exact")
    groups = group_duplicates([summary, original], KINDS)
    assert len(groups) == 1
    assert groups[0].main is original
    assert len(groups[0].copies) == 2 and groups[0].best_description_copy.description == TEXT
    assert groups[0].posted_at == original.posted_at


@pytest.mark.parametrize("different", ["country", "city", "level", "requisition", "evidence"])
def test_unicode_normalisation_does_not_relax_distinct_vacancy_guards(different):
    a = job("board", "one", title="Patient Care Nurse", company="Example Clinic")
    b = job("adzuna", "two", title="Patient‑Care Nurse", company="Example Clinic")
    kinds = dict(KINDS)
    if different == "country":
        b.country = "IE"
    elif different == "city":
        b.location_text = "Berlin"
    elif different == "level":
        b.title = "Senior Patient‑Care Nurse"
    elif different == "requisition":
        a.source = b.source = "employer"
        kinds["employer"] = "employer"
    else:
        a.description = "Hospital oncology and chemotherapy care. " * 30
        b.description = "Home visits for community public health. " * 30
        a.description_is_complete = b.description_is_complete = True
    assert len(group_duplicates([a, b], kinds)) == 2


def test_titles_at_different_levels_or_with_different_words_differ():
    assert title_similarity("lead electronics engineer", "electronics engineer") == 0
    assert title_similarity("entwicklungsingenieur elektronik",
                            "entwicklungsingenieur elektrotechnik") == 0
    assert title_similarity("verification engineer 586971", "verification engineer 586969") == 0
    assert title_similarity("electrical design engineer", "electrical desig engineer") >= 90


def test_the_same_job_on_two_sources_becomes_one_card_with_the_best_link():
    groups = group_duplicates(
        [job("adzuna", "1", city="Munich"), job("board", "9", company="ACME GmbH")], KINDS
    )
    assert len(groups) == 1
    assert groups[0].main.source == "board"  # job boards rank above aggregators


def test_same_title_in_far_apart_places_stays_separate():
    a = job(job_id="1", latitude=48.14, longitude=11.58)
    b = job(job_id="2", city="Hamburg", latitude=53.55, longitude=9.99)
    assert len(group_duplicates([a, b], KINDS)) == 2


def test_agency_ads_need_matching_text_to_merge():
    a = job(job_id="1", company="Ferchau GmbH")
    b = job(job_id="2", company="Ferchau GmbH")
    assert len(group_duplicates([a, b], KINDS)) == 2
    a.description = b.description = TEXT
    a.description_is_complete = b.description_is_complete = True
    assert len(group_duplicates([a, b], KINDS)) == 1


def test_earliest_date_of_all_copies_counts():
    old = datetime(2026, 9, 1, tzinfo=UTC)
    new = datetime(2026, 9, 16, tzinfo=UTC)
    groups = group_duplicates([
        job("adzuna", "1", posted_at=new, date_precision="exact"),
        job("board", "2", posted_at=old, date_precision="day"),
    ], KINDS)
    assert groups[0].posted_at == old and groups[0].date_precision == "day"


def test_agency_repeat_of_an_employer_ad_is_flagged_not_merged():
    employer = job("board", "1", title="Power Electronics Engineer", company="Acme GmbH",
                   description=TEXT, description_is_complete=True)
    agency = job("board", "2", title="Power Electronics Engineer", company="Brunel GmbH",
                 description=TEXT, description_is_complete=True)
    groups = group_duplicates([employer, agency], KINDS)
    assert len(groups) == 2
    flagged = [g for g in groups if g.possible_duplicate_of is not None]
    assert len(flagged) == 1 and flagged[0].main.company == "Brunel GmbH"


def test_a_country_or_region_alone_never_stops_a_match():
    # Search 8: most Adzuna ads say only "Deutschland"; the same job on another site gives its
    # town and full ad, but "Deutschland" had counted as a town, so almost none merged.
    kinds = {"adzuna": "aggregator", "board": "job_board"}
    for place in ("Deutschland", "Sachsen", ""):
        groups = group_duplicates([job("adzuna", "1", city=place),
                                   job("board", "9", city="Radeberg")], kinds)
        assert len(groups) == 1, place
    # Two towns still keep two jobs apart, big cities included.
    groups = group_duplicates([job("adzuna", "1", city="Munich"), job("board", "9", city="Berlin")],
                              kinds)
    assert len(groups) == 2


def test_a_postcode_or_a_district_is_the_same_place_as_its_town():
    # Search 9: Reed's "BB113BP" and Adzuna's "Burnley, Lancashire" were shown as two jobs, and
    # so were "Heeley, Sheffield" and "Sheffield".
    def uk(source, job_id, city):
        return FoundJob(source=source, source_job_id=job_id, url=f"https://{source}/{job_id}",
                        title="Electronics Design Engineer", company="Corriculo Ltd",
                        location_text=city, country="GB")

    kinds = {"adzuna": "aggregator", "reed": "job_board"}
    for a, b in (("BB113BP", "Burnley, Lancashire"), ("Heeley, Sheffield", "Sheffield")):
        assert len(group_duplicates([uk("reed", "1", a), uk("adzuna", "2", b)], kinds)) == 1, a
    assert len(group_duplicates([uk("reed", "1", "BB113BP"), uk("adzuna", "2", "Leeds")],
                                kinds)) == 2


def test_a_career_sites_label_in_brackets_is_not_part_of_the_company():
    # Search 9: the directory's "Rolls-Royce (professional)" never merged with "Rolls-Royce plc".
    assert normal_company("Rolls-Royce (professional)") == normal_company("Rolls-Royce plc")
    assert normal_company("Acme (UK) Ltd") == normal_company("ACME Ltd")


def test_two_summaries_of_one_agency_ad_merge_only_when_nearly_word_for_word_the_same():
    # Search 9: AMF's ad in Castleford came twice from Adzuna, both summaries, both scored 87.
    summary = ("Our client, a manufacturer of power supplies, is looking for an electronics "
               "design engineer to join its growing team in Castleford. You will design analogue "
               "and power circuits, lay out boards and test prototypes in the lab, working "
               "closely with production and quality. A degree in electronic engineering and "
               "some hands-on design experience are needed; training is given.")
    a = job(job_id="1", company="AMF Recruitment", description=summary)
    b = job(job_id="2", company="AMF Recruitment", description=summary + " Apply today.")
    assert len(group_duplicates([a, b], KINDS)) == 1
    # Different clients' summaries of a similar role stay apart, and so do very short ones.
    other = summary.replace("power supplies", "medical lasers").replace("Castleford", "Leeds") \
        .replace("analogue and power circuits", "laser driver boards")
    c = job(job_id="3", company="AMF Recruitment", description=other)
    assert len(group_duplicates([a, c], KINDS)) == 2
    short = [job(job_id=n, company="AMF Recruitment", description="Electronics engineer wanted.")
             for n in ("4", "5")]
    assert len(group_duplicates(short, KINDS)) == 2


def test_an_agency_ad_and_a_job_site_summary_of_it_are_one_job():
    # Search 15: one recruiter's graduate ad came as two cards, 88 from JSearch's full ad and 75
    # from Adzuna's summary of it.
    full = ("Graduate Electronics Engineer - Derby - LM1257f. My client, a manufacturer of "
            "specialist electronic equipment, seeks a graduate electronics engineer to join its "
            "growing team near Derby. You will design analogue and digital circuits, lay out "
            "boards and test prototypes, working with production and quality. A degree in "
            "electronic engineering is needed; training is given. ") + "Benefits and more. " * 30
    summary = full[:420] + "…"
    a = job("board", "1", company="Advanced Technical Recruitment", city="Derby",
            description=full, description_is_complete=True)
    b = job("adzuna", "2", company="Advanced Technical Recruitment", city="Derby",
            description=summary)
    assert len(group_duplicates([a, b], KINDS)) == 1
    # Another client's ad with the same title, and a summary too short to tell, stay apart.
    other = summary.replace("specialist electronic equipment", "medical lasers") \
        .replace("analogue and digital circuits", "laser driver boards and power stages")
    c = job("adzuna", "3", company="Advanced Technical Recruitment", city="Derby",
            description=other)
    assert len(group_duplicates([a, c], KINDS)) == 2
    d = job("adzuna", "4", company="Advanced Technical Recruitment", city="Derby",
            description=full[:120])
    assert len(group_duplicates([a, d], KINDS)) == 2


def test_a_summary_never_joins_two_different_full_ads():
    full = ("Our client designs power converters for rail and marine customers and seeks an "
            "electronics engineer for its lab near Derby. You will design and test boards, "
            "simulate circuits, write test reports, support production and quality teams, visit "
            "suppliers now and then and help the service team with returned units. A degree in "
            "electronic engineering and some lab experience are needed; training is given. "
            "The role is permanent, full time and based on site with flexible hours. ") * 2
    other = ("Our client builds medical lasers and needs an electronics engineer near Derby to "
             "align optics, calibrate laser drivers, keep the clean room running and train "
             "hospital technicians on site. Night shifts may be needed during audits. ") * 3
    summary = full[:440]
    jobs = [job("board", "1", company="AMF Recruitment", city="Derby", description=full,
                description_is_complete=True),
            job("board", "2", company="AMF Recruitment", city="Derby", description=other,
                description_is_complete=True),
            job("adzuna", "3", company="AMF Recruitment", city="Derby", description=summary)]
    for order in permutations(jobs):
        groups = group_duplicates(list(order), KINDS)
        assert len(groups) == 2
        assert {len(g.copies) for g in groups} == {1, 2}


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_distinct_employer_vacancies_stay_separate_even_with_identical_ad_templates(title):
    kinds = {**KINDS, "employer": "employer"}
    jobs = [job("employer", f"example/req-{n}", title=title, description=TEXT,
                description_is_complete=True) for n in (1, 2)]
    groups = group_duplicates(jobs, kinds)
    assert len(groups) == 2
    assert {g.main.source_job_id for g in groups} == {"example/req-1", "example/req-2"}
    assert all(g.possible_duplicate_of is None for g in groups)


def test_a_board_copy_cannot_transitively_merge_two_employer_requisitions():
    kinds = {**KINDS, "employer": "employer"}
    jobs = [job("employer", "example/req-1"), job("board", "copy"),
            job("employer", "example/req-2")]
    for order in permutations(jobs):
        groups = group_duplicates(list(order), kinds)
        assert len(groups) == 2
        assert all(len({c.source_job_id for c in g.copies if c.source == "employer"}) == 1
                   for g in groups)


def test_empty_ids_do_not_merge_unrelated_jobs_or_countries():
    jobs = [job("board", "", title="Power Electronics Engineer"),
            job("board", "", title="Registered Nurse", company="Example Care"),
            FoundJob("board", "", "https://example.test/chef", "Chef", country="IE")]
    assert len(group_duplicates(jobs, KINDS)) == 3


def test_matching_full_ads_are_needed_when_both_copies_supply_them():
    jobs = [job("adzuna", "power", title="Engineer", description=(
                "Design semiconductor power converters and validate electrical safety. " * 20),
                description_is_complete=True),
            job("board", "radio", title="Engineer", description=(
                "Develop radio antennas and test wireless communications in a test room. " * 20),
                description_is_complete=True)]
    assert len(group_duplicates(jobs, KINDS)) == 2
    jobs[1].description = jobs[0].description + " Apply today."
    assert len(group_duplicates(jobs, KINDS)) == 1


def test_a_summary_cannot_bridge_conflicting_complete_ads():
    power = job("adzuna", "power", title="Engineer", description=(
        "Design semiconductor power converters and validate electrical safety. " * 20),
        description_is_complete=True)
    radio = job("board", "radio", title="Engineer", description=(
        "Develop radio antennas and test wireless communications in a test room. " * 20),
        description_is_complete=True)
    summary = job("other", "summary", title="Engineer", description="An engineer is wanted.")
    for order in permutations([power, radio, summary]):
        groups = group_duplicates(list(order), KINDS)
        assert len(groups) == 2
        assert all(not ({"power", "radio"} <= {c.source_job_id for c in g.copies}) for g in groups)


def test_exact_source_identity_survives_changed_full_ad_text():
    before = job("board", "same-req", description="An earlier full description. " * 20,
                 description_is_complete=True)
    after = job("board", "same-req", description="Revised duties and qualifications. " * 20,
                description_is_complete=True)
    assert len(group_duplicates([before, after], KINDS)) == 1


def test_identical_short_complete_copies_preserve_the_existing_match():
    jobs = [job("adzuna", "copy", description="Full ad text", description_is_complete=True),
            job("board", "original", description="Full ad text", description_is_complete=True)]
    assert len(group_duplicates(jobs, KINDS)) == 1


def test_comparison_text_is_prepared_once_per_distinct_ad(monkeypatch):
    from jobcu import dedupe

    original = dedupe._shingles
    calls = []

    def prepare(text, size=5):
        calls.append(text)
        return original(text, size)

    monkeypatch.setattr(dedupe, "_shingles", prepare)
    jobs = [job(job_id=str(i), company="Example Recruitment", description=(
                f"product{i} responsibility{i} qualification{i} location{i} benefit{i} " * 30),
                description_is_complete=True) for i in range(12)]
    groups = group_duplicates(jobs, KINDS)
    assert len(groups) == len(jobs)
    assert len(calls) == len(set(calls)) == len(jobs)


WHOLE_AD = " ".join(f"Task {n} covers fictional converter design step {n} for the team."
                    for n in range(60))


def test_one_complete_ad_under_several_titles_is_one_job():
    titles = ["Elektronik-Ingenieur", "Hardwareentwickler - Elektronik",
              "Hardware Engineer - Electronics"]
    jobs = [job("board", str(n), title=title, company="Fictional Works",
                description=WHOLE_AD, description_is_complete=True)
            for n, title in enumerate(titles)]
    groups = group_duplicates(jobs, KINDS)
    assert len(groups) == 1 and len(groups[0].copies) == 3


@pytest.mark.parametrize("different", ["level", "agency", "summary", "text", "requisition"])
def test_a_retitled_ad_needs_a_whole_matching_text_and_the_same_level(different):
    a = job("board", "1", title="Elektronik-Ingenieur", company="Fictional Works",
            description=WHOLE_AD, description_is_complete=True)
    b = job("board", "2", title="Hardware Engineer - Electronics", company="Fictional Works",
            description=WHOLE_AD, description_is_complete=True)
    kinds = dict(KINDS)
    if different == "level":
        b.title = "Senior Hardware Engineer - Electronics"
    elif different == "agency":
        a.company = b.company = "Fictional Recruitment Ltd"
    elif different == "summary":
        b.description_is_complete = False
    elif different == "text":
        b.description = WHOLE_AD.replace("converter", "inverter", 6)
    else:
        a.source = b.source = "employer"
        kinds["employer"] = "employer"
    assert len(group_duplicates([a, b], kinds)) == 2


# A whole ad with no repeated sentence, as real ads are.
WHOLE_AD = " ".join(f"Task {n}: design converter stage {n}, test it on rig {n} and report."
                    for n in range(60))


@pytest.mark.parametrize("short,long", [
    ("Acme", "Acme Robotics"), ("Acme", "Acme Robotics Germany Tech Experts GmbH"),
    ("Example Works GmbH", "Example Works GmbH Leeds")])
def test_one_ad_under_a_shorter_and_a_longer_employer_name_is_one_job(short, long):
    # One search showed the same ad twice under two spellings of eight employers' names
    # (a parent and a division, a company and its branch), scored up to 20 points apart.
    full = dict(description=WHOLE_AD, description_is_complete=True)
    assert len(group_duplicates([job(company=short, **full),
                                 job("board", company=long, **full)], KINDS)) == 1
    # Also when one site gives only the start of the ad.
    summary = job(company=short, description=WHOLE_AD[:700])
    assert len(group_duplicates([summary, job("board", company=long, **full)], KINDS)) == 1
    # The name's start alone proves nothing: another text, title or town is another job.
    other = dict(description="We build test rigs for wind turbines in our plant. " * 20,
                 description_is_complete=True)
    for different in (job("board", company=long, **other),
                      job("board", company=long, title="Software Engineer", **full),
                      job("board", company=long, city="Hamburg", **full),
                      job("board", company=long)):
        assert len(group_duplicates([job(company=short, **full), different], KINDS)) == 2


def test_full_ads_read_later_join_two_jobs_that_looked_different_at_first():
    from jobcu.dedupe import same_jobs

    # An agency's ad is another site's copy only when the texts match, and one site lists it
    # without its text: four such ads were two cards each in one search.
    listed = job("board", company="Fictional Staffing GmbH")
    with_text = job(company="Fictional Staffing GmbH", description=TEXT,
                    description_is_complete=True)
    another = job("board", "2", title="Test Engineer", company="Fictional Staffing GmbH")
    groups = group_duplicates([listed, with_text, another], KINDS)
    assert len(groups) == 3 and same_jobs(groups, [0, 1, 2]) == {}
    listed.description, listed.description_is_complete = TEXT, True
    assert same_jobs(groups, [0, 1, 2]) == {1: 0}
    assert same_jobs(groups, [2, 1, 0]) == {0: 1}  # the first one named stays
    assert same_jobs(groups, [0, 2]) == {} and same_jobs(groups, []) == {}


def test_one_ad_listed_for_several_towns_names_the_other_towns_and_stays_separate():
    from jobcu.dedupe import same_ad_elsewhere

    full = dict(description=WHOLE_AD, description_is_complete=True)
    munich, hamburg = job(**full), job(job_id="2", city="Hamburg", **full)
    # A recruiter's template for another role is alike, not the same ad.
    template = job(job_id="3", city="Köln", description=" ".join(
        f"Task {n}: design converter stage {n}, test it on rig {n} and report." if n % 6
        else f"Duty {n}: validate battery pack {n} and write up result {n}."
        for n in range(60)), description_is_complete=True)
    other_title = job(job_id="4", title="Software Engineer", city="Berlin", **full)
    other_poster = job(job_id="5", company="Another Employer GmbH", city="Bremen", **full)
    groups = group_duplicates([munich, hamburg, template, other_title, other_poster], KINDS)
    assert len(groups) == 5
    assert same_ad_elsewhere(groups, list(range(5))) == {0: [1], 1: [0]}
