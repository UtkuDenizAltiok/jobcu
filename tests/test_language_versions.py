"""One vacancy a career site lists once per language is one job, in the person's language."""

import httpx
import pytest
from test_careers import SF_ADDRESSES, context, employer, query, sf_full_page, sf_own_layout_page

from jobcu import pipeline
from jobcu.dedupe import group_duplicates
from jobcu.profile import LanguageSkill, Profile
from jobcu.sources import careers, successfactors
from jobcu.sources.base import FoundJob

KINDS = {"successfactors": "employer", "adzuna": "aggregator"}
PERSON = Profile.model_validate({
    "summary": "Fictional engineer.", "current_or_last_role": None, "field": "Electronics",
    "skills": [], "technical_areas": [], "years_full_time_experience": 0,
    "years_student_or_part_time_experience": 2, "experience_note": "", "seniority": "junior",
    "education": [], "languages": [], "target_roles": ["Hardware Engineer"],
    "target_fields": [], "preferences": [], "work_mode_preference": "not_stated",
    "dealbreakers": [], "work_authorisation": None, "ignored_as_application_specific": [],
})


def speaks(**levels):
    return PERSON.model_copy(update={"languages": [
        LanguageSkill(language=language, level_as_written=level, cefr=level,
                      cefr_is_estimate=False) for language, level in levels.items()]})


def version(job_id, language, title, text, *, vacancy="jobs.fake.example/vacancy-3387"):
    return FoundJob(source="successfactors", source_job_id=f"jobs.fake.example/{job_id}",
                    url=f"https://jobs.fake.example/job/Town-Title/{job_id}/", title=title,
                    company="FakeCo", location_text="Stuttgart", country="DE",
                    description=text, description_is_complete=True,
                    source_context={"requisition": vacancy, "language": language})


GERMAN = version("1418617233", "de", "Hardwareentwickler (m/w/d)",
                 "Sie entwickeln Leiterplatten für Antriebe. " * 30)
ENGLISH = version("1418617333", "en", "Hardware Engineer (m/f/d)",
                  "You design circuit boards for drives. " * 30)


def test_the_two_language_listings_of_one_vacancy_are_one_job():
    # November 2026: a site's 919 listed pages held 440 such pairs; in one saved history 18 of
    # 54 career-site cards were the same nine jobs twice.
    groups = group_duplicates([GERMAN, ENGLISH], KINDS)
    assert [len(group.copies) for group in groups] == [2]
    # Another vacancy of the employer with the same title and place stays its own job, and
    # listings without the site's word stay apart as before.
    other = version("1500000033", "de", GERMAN.title, GERMAN.description,
                    vacancy="jobs.fake.example/vacancy-4000")
    assert len(group_duplicates([GERMAN, ENGLISH, other], KINDS)) == 2
    unmarked = [FoundJob(**{**vars(job), "source_context": {}}) for job in (GERMAN, ENGLISH)]
    assert len(group_duplicates(unmarked, KINDS)) == 2


@pytest.mark.parametrize("levels,kept", [
    ({"English": "C1", "German": "A2"}, "en"),
    ({"German": "C2", "English": "B1"}, "de"),
    ({"Italian": "C2"}, "de"),  # reads neither: the job country's own language
    ({}, "de"),
])
def test_the_version_the_person_reads_best_is_the_one_kept(levels, kept):
    board_copy = FoundJob(source="adzuna", source_job_id="9", url="https://adzuna.example/9",
                          title=GERMAN.title, company="FakeCo", location_text="Stuttgart",
                          country="DE", description="Summary.")
    group = group_duplicates([GERMAN, ENGLISH, board_copy], KINDS)[0]
    assert len(group.copies) == 3
    chosen = pipeline.prefer_language_versions([group], speaks(**levels))[0]
    assert [copy.source_context.get("language") for copy in chosen.copies
            if copy.source == "successfactors"] == [kept]
    assert any(copy.source == "adzuna" for copy in chosen.copies)  # other sites' copies stay
    assert chosen.best_description_copy.source_context["language"] == kept


def test_versions_with_one_language_or_none_named_are_left_as_they_are():
    same = [version("1", "de", "Hardwareentwickler", "Derselbe Text. " * 40),
            version("2", "de", "Hardwareentwickler", "Derselbe Text. " * 40)]
    group = group_duplicates(same, KINDS)[0]
    assert pipeline.prefer_language_versions([group], speaks(English="C1"))[0] is group
    assert pipeline.prefer_language_versions([group], None)[0] is group


def test_the_reader_marks_pages_that_end_at_one_vacancy_number(monkeypatch):
    german = sf_own_layout_page("Hardwareentwickler (m/w/d)", "Sie entwickeln Leiterplatten.")
    english = sf_own_layout_page("Hardware Engineer (m/f/d)", "You design circuit boards.")
    addresses = SF_ADDRESSES.replace("Anting-Hardware-Engineer-201805/666",
                                     "B%C3%BChl-Hardware-Engineer-%28mfd%29-77815/655")
    pages = {"555": ("3387-de_DE", german), "655": ("3387-en_US", english)}

    def handler(request):
        path = request.url.path.rstrip("/")
        if path == "/robots.txt":
            return httpx.Response(404)
        if path == "/sitemap.xml":
            return httpx.Response(200, content=addresses.encode(),
                                  headers={"content-type": "text/xml"})
        last = path.split("/")[-1]
        if last in pages:  # the listed number leads to the vacancy's own address
            return httpx.Response(301, headers={
                "location": f"https://jobs.fake.example/job/Title/{pages[last][0]}/"})
        return httpx.Response(200, text=next(page for end, page in pages.values() if end == last))

    fake = employer("successfactors", board="jobs.fake.example", countries=("DE",))
    monkeypatch.setattr(careers, "load_directory", lambda: (fake,))
    jobs = list(successfactors.SuccessFactorsSource().search(
        query(["DE"], hours=72), context(handler, "successfactors")))
    assert [job.source_context for job in jobs] == [
        {"requisition": "jobs.fake.example/vacancy-3387", "language": "de"},
        {"requisition": "jobs.fake.example/vacancy-3387", "language": "en"}]
    assert len(group_duplicates(jobs, KINDS)) == 1


def test_an_untranslated_ad_under_two_language_listings_is_one_vacancy():
    # One site showed the same German ad under its German and its English listing, with only
    # the page's own sentences translated: 10 of 10 pairs, half to three quarters alike.
    ad = [f"Aufgabe {n}: Baugruppen entwickeln und in Betrieb nehmen." for n in range(12)]

    def listing(job_id, language, frame, **changes):
        return FoundJob(**{**vars(version(job_id, language, "Hardwareentwickler (w/m/d)",
                                          "\n".join([*ad, *frame]))),
                           "source_context": {"language": language}, **changes})

    german = listing("1336327755", "de", ["Bewerben Sie sich online.", "Fragen? Schreiben Sie."])
    english = listing("1336327855", "en", ["Please apply online.", "Questions? Write to us."])
    marked = successfactors.same_ad_twice([german, english])
    assert marked[0].source_context["requisition"] == marked[1].source_context["requisition"]
    assert [m.source_context["language"] for m in marked] == ["de", "en"]
    assert len(group_duplicates(marked, KINDS)) == 1
    # Another title, another place, or two listings in one language with other texts: apart.
    for other in (listing("2", "en", ["Please apply online."], title="Systems Engineer"),
                  listing("3", "en", ["Please apply online."], location_text="Ulm"),
                  listing("4", "de", ["Please apply online.", "Questions? Write to us."])):
        assert all("requisition" not in job.source_context
                   for job in successfactors.same_ad_twice([german, other]))
    # Mostly different lines are another ad, whatever the language.
    different = listing("5", "en", [f"Task {n}: test rigs." for n in range(40)])
    assert "requisition" not in successfactors.same_ad_twice([german, different])[0].source_context


def test_the_reader_marks_one_ad_shown_under_two_listings_as_one_vacancy():
    day = __import__("datetime").datetime(2026, 11, 10, tzinfo=__import__("datetime").UTC)
    page = sf_full_page("Hardwareentwickler (w/m/d)", "Bühl, DE, 77815", day)
    one = successfactors.from_page_address(
        "https://jobs.fake.example/job/B%C3%BChl-Hardwareentwickler-77815/1336327755/",
        employer("successfactors", board="jobs.fake.example"))
    two = successfactors.from_page_address(
        "https://jobs.fake.example/job/B%C3%BChl-Hardwareentwickler-77815/1336327855/",
        employer("successfactors", board="jobs.fake.example"))
    read = [FoundJob(**{**vars(job), "title": "Hardwareentwickler (w/m/d)",
                        "description": "Design boards.", "description_is_complete": True})
            for job in (one, two)]
    other = FoundJob(**{**vars(read[0]), "source_job_id": "jobs.fake.example/9",
                        "description": "Another ad."})
    marked = successfactors.same_ad_twice([*read, other])
    assert marked[0].source_context["requisition"] == marked[1].source_context["requisition"]
    assert "requisition" not in marked[2].source_context
    assert successfactors.version_of("https://jobs.fake.example/job/x/1336327755/",
                                     page.replace("<html>", '<html lang="de-DE">'),
                                     "jobs.fake.example") == {"language": "de"}
