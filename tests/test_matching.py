from jobcu.keywords import SearchTerm
from jobcu.location import Place
from jobcu.sources.matching import matches_places, matches_terms, term_matches
from jobcu.text import normalise


def term(text, language="en", kind="job_title"):
    return SearchTerm(text=text, language=language, kind=kind)


def test_normalise_removes_accents_case_and_punctuation():
    assert normalise("München-Süd, Straße") == "munchen sud strasse"


def test_term_words_match_in_any_order_and_inside_longer_words():
    assert term_matches("Hardware Engineer", "Engineer (Hardware Design)")
    assert term_matches("Elektronik", "Entwickler Leistungselektronik (m/w/d)")
    assert term_matches("hardware engineer", "Senior Hardware Engineering Lead")
    assert not term_matches("Hardware Engineer", "Software Engineer")


def test_a_word_matches_with_or_without_its_plural_s():
    # Search 10's coverage list: "Electronics Engineer" had never matched "Electronic Engineer".
    assert term_matches("Electronics Engineer", "Electronic Engineer")
    assert term_matches("Electronics Engineer", "FY27 Electronic Engineering Graduate")
    assert term_matches("Nurses", "Staff Nurse, ICU")
    assert term_matches("Electronic Engineer", "Electronics Engineer")  # as before
    assert not term_matches("Electronics Engineer", "Electrical Engineer")
    assert not term_matches("Ops", "Op Engineer")  # short words stay whole words


def test_a_compound_matches_when_written_apart_or_with_a_hyphen():
    # Search 11's coverage list: Michael Page's "Hardware Entwickler (m/w/d)" in Erding.
    for title in ("Hardware Entwickler (m/w/d)", "Hardware-Entwickler (w/m/d) Leistungselektronik",
                  "Senior Hardwareentwickler"):
        assert term_matches("Hardwareentwickler", title), title
    assert term_matches("Leiterplattendesign", "Leiterplatten-Design und Layout")
    assert term_matches("Hardwareontwikkelaar", "Hardware-ontwikkelaar Embedded")  # Dutch too
    assert not term_matches("Hardwareentwickler", "Hardware Engineer")
    assert not term_matches("SMPS", "S MPS")  # short terms only as written


def test_short_words_must_match_whole_words():
    assert not term_matches("IT", "Digital Marketing Executive")
    assert term_matches("IT support", "IT Support Engineer")
    assert term_matches("PCB", "PCB Layout Designer")


def test_field_words_can_match_the_ad_text_but_job_titles_only_the_title():
    terms = [term("Hardware Engineer"), term("power electronics", kind="field_or_skill")]
    assert matches_terms(terms, {"en"}, "Test Engineer", "Work on power electronics for trains")
    assert not matches_terms([term("Hardware Engineer")], {"en"}, "Test Engineer",
                             "Support our hardware engineer team")
    assert not matches_terms(terms, {"de"}, "Hardware Engineer")


def test_places_match_by_name_in_either_language():
    munich = Place(name="Munich", local_name="München", country="DE", kind="city", radius_km=None)
    assert matches_places([munich], "DE", "80331 München")
    assert matches_places([munich], "DE", "Munich, Bavaria")
    assert not matches_places([munich], "DE", "Berlin")
    # No place named in this country, or no location known: nothing to rule the job out.
    assert matches_places([munich], "AT", "Wien")
    assert matches_places([munich], "DE", None)


def test_irish_counties_in_addresses_match_the_named_place():
    dublin = Place(name="Dublin", local_name="Dublin", country="IE", kind="city", radius_km=None)
    assert matches_places([dublin], "IE", "Unit 4, Swords, Co. Dublin, K67 X123")
    assert not matches_places([dublin], "IE", "Ballincollig, Co. Cork")
