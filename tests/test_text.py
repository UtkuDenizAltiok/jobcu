import dataclasses

from jobcu.jobposting import find_job_posting
from jobcu.sources.base import FoundJob
from jobcu.text import html_to_text


def test_text_without_tags_has_its_character_references_decoded():
    # A job board's ad text and a career site's job data often come as escaped plain text.
    assert html_to_text("Design &amp; test of power converters") == \
        "Design & test of power converters"
    assert html_to_text("Für unsere Standorte in M&uuml;nchen") == "Für unsere Standorte in München"
    assert html_to_text("Salary up to &pound;55,000&#xa;Location: Fictiontown") == \
        "Salary up to £55,000\nLocation: Fictiontown"
    assert html_to_text("Senior Engineer &#8211; Inverters &#038; Drives") == \
        "Senior Engineer – Inverters & Drives"


def test_a_site_that_escapes_its_text_twice_reads_as_plain_text():
    assert html_to_text("Test Engineer HIL &amp;amp; PHIL") == "Test Engineer HIL & PHIL"
    assert html_to_text("<p>Board bring-up &amp;amp; validation</p>") == \
        "Board bring-up & validation"
    assert html_to_text("<div>&amp;lt;p&amp;gt;Design GaN stages&amp;lt;/p&amp;gt;</div>") == \
        "Design GaN stages"


def test_ampersands_meant_as_written_stay_as_they_are():
    assert html_to_text("R&D Engineer at AT&T") == "R&D Engineer at AT&T"
    assert html_to_text("Q&A sessions; Tom &Jerry") == "Q&A sessions; Tom &Jerry"
    assert html_to_text("An unknown &fictional; name") == "An unknown &fictional; name"
    assert html_to_text("<p>A &lt; B</p>") == "A < B"


def test_job_data_with_escaped_titles_reads_as_the_title_the_employer_wrote():
    page = ('<script type="application/ld+json">{"@type": "JobPosting", '
            '"title": "Testingenieur f\\u00fcr HIL &amp; PHIL Leistungselektronik", '
            '"description": "Sie testen Umrichter &amp; Antriebe."}</script>')
    posting = find_job_posting(page)
    assert posting.title == "Testingenieur für HIL & PHIL Leistungselektronik"
    assert posting.description == "Sie testen Umrichter & Antriebe."


def test_every_reader_s_job_text_is_plain_text_and_its_addresses_stay_as_given():
    # A reader that takes a site's values as they come still gives plain text.
    job = FoundJob("fictional", "7", "https://jobs.example.test/7?a=1&amp;b=2",
                   "Hardware Engineer &#8211; Power &amp;amp; Drives", company="Smith &amp; Sons",
                   location_text="Fictiontown &amp; nearby", description="Design&nbsp;boards",
                   salary_text="&pound;40,000")
    assert job.title == "Hardware Engineer – Power & Drives"
    assert job.company == "Smith & Sons" and job.location_text == "Fictiontown & nearby"
    assert job.description == "Design\xa0boards" and job.salary_text == "£40,000"
    assert job.url == "https://jobs.example.test/7?a=1&amp;b=2"
    # Copies made from a job are plain text too (full ads, remembered ads).
    assert dataclasses.replace(job, title="Test &amp; Validation").title == "Test & Validation"
