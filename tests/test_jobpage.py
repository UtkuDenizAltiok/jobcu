"""Job pages without job data (jobpage.py), read the way a person reads them; made-up pages."""

from jobcu import jobpage

AD = ("<p>You design power converters for electric drives, from the first circuit to the "
      "validated board, and you test them in our laboratory with the team.</p>"
      "<h2>What you bring</h2><ul><li>A degree in electrical engineering</li>"
      "<li>Experience with gate drivers and magnetics</li><li>Good English</li></ul>"
      "<p>We offer flexible hours, a modern laboratory, training and a team that enjoys its "
      "work. Apply with your CV; we answer every application within two weeks.</p>")


def page(main, head="<title>Careers | Example Cars</title>"):
    return (f"<html><head>{head}</head><body><header><nav>Jobs Benefits Locations</nav>"
            f"</header><main>{main}</main><footer>Imprint Hamburg</footer></body></html>")


def test_the_town_above_the_title_places_a_page_that_names_no_place_label():
    ad = jobpage.read(page("<div>Drive Development</div><div>Munich</div><div>24.11.2026</div>"
                           "<h1>Hardware Engineer Power Electronics (f/m/x)</h1>" + AD))
    assert ad.title == "Hardware Engineer Power Electronics (f/m/x)"
    assert (ad.place, ad.country) == ("Munich", "DE")
    assert "gate drivers" in ad.text and "Imprint" not in ad.text and "Benefits" not in ad.text


def test_a_place_label_names_the_place_up_to_the_next_label():
    ad = jobpage.read(page("<p>Please switch on JavaScript to use every part of this page.</p>"
                           "<h1>Entwicklungsingenieur Leistungselektronik (m/w/d)</h1>"
                           "<p>Kennziffer: J0001 Einstiegsart: Professionals Einsatzort: "
                           "Stuttgart Gesellschaft: Example Cars AG</p>" + AD))
    assert ad.place == "Stuttgart" and ad.country is None
    assert ad.company == "Example Cars AG"
    listed = jobpage.read(page("<h1>Graduate Engineer</h1><dl><dt>Location:</dt><dd></dd>"
                               "<dd>Bucharest, Cluj</dd></dl>" + AD))
    assert listed.place == "Bucharest, Cluj"  # the value on the label's next line


def test_a_page_with_too_little_text_or_no_title_is_no_ad():
    # A page that builds its ad with scripts shows only its frame.
    assert jobpage.read(page("<h1>Hardware Engineer</h1><div id='app'></div>")) is None
    assert jobpage.read(page("<div>" + AD + "</div>", head="")) is None
    # Without a heading, the page's title names the job (before the site's name).
    titled = jobpage.read(page(AD, head="<title>Stellenanzeige: Elektroniker | Karriereportal | "
                                        "Example Cars</title>"))
    assert titled.title == "Elektroniker"


def test_a_word_in_a_sentence_above_the_title_is_no_town():
    # "On" is a town's name too; a sentence above the title names no place.
    ad = jobpage.read(page("<p>Please switch on JavaScript to use every part of this page.</p>"
                           "<h1>Hardware Engineer</h1>" + AD))
    assert ad.place is None and ad.country is None


def test_a_page_is_read_from_the_title_its_list_gives():
    # A site whose job page opens with its own heading and a country switcher, then the job.
    switcher = ("<h1>About Example Power</h1><p>Change Location : France</p>"
                "<h2>Senior Electrical Design Engineer (m/f/d)</h2>"
                "<p>Location : Exampleton, Devon</p>")
    ad = jobpage.read(page(switcher + AD), "senior electrical design engineer")
    assert ad.title == "Senior Electrical Design Engineer (m/f/d)"  # the page's own spelling
    assert ad.place == "Exampleton, Devon"
    assert ad.text.startswith("Senior Electrical Design Engineer") and "France" not in ad.text
    # Without the list's title the page's main heading stands, as before.
    assert jobpage.read(page(switcher + AD)).title == "About Example Power"
