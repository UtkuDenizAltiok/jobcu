"""The employer's own posting, found online, for good jobs whose links can't take the application
(livepostings.py)."""

from jobcu import livepostings
from jobcu.ai.base import AILimitReached, AIRefused, AIUnavailable, ResearchReply, Source, Usage
from jobcu.dedupe import JobGroup
from jobcu.sources.base import FoundJob

UK_PAGE = "https://www.learn4good.com/jobs/luton/uk/engineering/{}/e/"
CAREERS = "https://careers.fakeco.example/jobs/{}"


class Researcher:
    """Stands in for the AI client: each web look-up answers with the next scripted notes and
    sources, each structuring step with the next scripted addresses."""

    parallel_requests = 1

    def __init__(self, replies, structured=()):
        self.replies = list(replies)
        self.structured = list(structured)
        self.prompts = []

    def research(self, **request):
        self.prompts.append(request["prompt"])
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        text, sources, searches = reply
        return ResearchReply(text, [Source(url) for url in sources], Usage(10, 5,
                                                                           web_searches=searches))

    def generate(self, output, **request):
        return output.model_validate({"jobs": self.structured.pop(0)})


def group(n, *urls):
    copies = [FoundJob(source="jsearch", source_job_id=f"{n}-{k}", url=url,
                       title="Hardware Engineer", company="FakeCo", location_text="Luton, UK",
                       country="GB", description="FakeCo in Luton builds radar test systems.")
              for k, url in enumerate(urls or [UK_PAGE.format(n)])]
    return JobGroup(copies, source_kinds={"jsearch": "aggregator"})


def test_only_good_jobs_whose_links_take_only_uk_visitors_are_looked_up():
    good = {"score": 75}
    assert livepostings.needs_posting(group(1), good)
    assert not livepostings.needs_posting(group(1), {"score": 40})
    assert not livepostings.needs_posting(group(1), None)
    assert not livepostings.needs_posting(group(1, "https://board.example.org/jobs/1"), good)
    assert not livepostings.needs_posting(group(1, UK_PAGE.format(1),
                                                "https://board.example.org/jobs/1"), good)
    # The owner's rule: a job reachable only through CV-Library stays left out, unasked.
    assert not livepostings.needs_posting(group(1, "https://www.cv-library.co.uk/job/1"), good)
    assert livepostings.needs_posting(group(1, UK_PAGE.format(1),
                                            "https://www.cv-library.co.uk/job/1"), good)
    looked_up = group(1)
    looked_up.link_from_web = ""
    assert not livepostings.needs_posting(looked_up, good)


def test_an_address_is_kept_only_when_the_provider_s_web_search_returned_it():
    groups = [group(0), group(1), group(2), group(3)]
    notes = (f"JOB J0 {CAREERS.format(0)}\nJOB J1 {CAREERS.format(1)}\n"
             "JOB J2 https://www.cv-library.co.uk/job/2\nJOB J3 NOT FOUND")
    client = Researcher(
        [(notes, [CAREERS.format(0) + "/", "https://www.cv-library.co.uk/job/2"], 3)],
        [[{"id": "J0", "url": CAREERS.format(0)}, {"id": "J1", "url": CAREERS.format(1)},
          {"id": "J2", "url": "https://www.cv-library.co.uk/job/2"}, {"id": "J3", "url": ""}]])
    assert livepostings.find_postings(client, groups, [0, 1, 2, 3]) == 1
    # J1's address appears only in the written notes; J2 is CV-Library; J3 wasn't found.
    assert [g.link_from_web for g in groups] == [CAREERS.format(0), "", "", ""]
    assert "radar test systems" in client.prompts[0]
    assert "J3 | Hardware Engineer" in client.prompts[0]


def test_an_answer_from_memory_finds_nothing_and_is_asked_again_next_time():
    groups = [group(0)]
    client = Researcher([(f"JOB J0 {CAREERS.format(0)}", [CAREERS.format(0)], 0)])
    assert livepostings.find_postings(client, groups, [0]) == 0
    assert groups[0].link_from_web is None


def test_a_job_s_own_or_uk_visitors_only_pages_are_never_its_open_posting():
    groups = [group(0), group(1)]
    other_uk = UK_PAGE.format(99)
    client = Researcher(
        [(f"JOB J0 {UK_PAGE.format(0)}\nJOB J1 {other_uk}", [UK_PAGE.format(0), other_uk], 2)],
        [[{"id": "J0", "url": UK_PAGE.format(0)}, {"id": "J1", "url": other_uk}]])
    assert livepostings.find_postings(client, groups, [0, 1]) == 0
    assert [g.link_from_web for g in groups] == ["", ""]


def test_a_site_that_only_repeats_other_sites_ads_is_never_the_open_posting():
    # Search 17's one find was a JobLeads page: it refuses Jobcu and shows the employer only to
    # paying members, no nearer the employer than the link the job had.
    groups = [group(0), group(1), group(2)]
    pages = ["https://www.jobleads.com/uk/job/hardware-engineer--luton--e1", "https://bebee.com/gb"
             "/jobs/embedded-software-engineer--fj-123", CAREERS.format(2)]
    client = Researcher(
        [("\n".join(f"JOB J{n} {page}" for n, page in enumerate(pages)), pages, 3)],
        [[{"id": f"J{n}", "url": page} for n, page in enumerate(pages)]])
    assert livepostings.find_postings(client, groups, [0, 1, 2]) == 1
    assert [g.link_from_web for g in groups] == ["", "", CAREERS.format(2)]
    assert "only lists other sites' ads" in livepostings.RESEARCH_SYSTEM


def test_reached_ai_limit_leaves_the_rest_unasked_and_a_cached_look_up_isn_t_paid_twice():
    groups = [group(n) for n in range(7)]
    cache = {}
    first = Researcher([(f"JOB J0 {CAREERS.format(0)}", [CAREERS.format(0)], 5),
                        AILimitReached("limit")],
                       [[{"id": "J0", "url": CAREERS.format(0)}]])
    assert livepostings.find_postings(first, groups, list(range(7)), research_cache=cache) == 1
    assert groups[0].link_from_web == CAREERS.format(0)
    assert all(g.link_from_web is None for g in groups[5:]) and len(cache) == 1
    again = [group(n) for n in range(5)]
    cached = Researcher([], [[{"id": "J0", "url": CAREERS.format(0)}]])
    assert livepostings.find_postings(cached, again, list(range(5)), research_cache=cache) == 1
    assert cached.prompts == []


def test_a_declined_answer_skips_only_its_own_jobs_and_a_lost_connection_stops():
    groups = [group(n) for n in range(10)]
    client = Researcher([AIRefused("declined"),
                         (f"JOB J5 {CAREERS.format(5)}", [CAREERS.format(5)], 5)],
                        [[{"id": "J5", "url": CAREERS.format(5)}]])
    assert livepostings.find_postings(client, groups, list(range(10))) == 1
    assert all(g.link_from_web is None for g in groups[:5])  # asked again next time
    assert groups[5].link_from_web == CAREERS.format(5)
    stopped = Researcher([AIUnavailable("down")])
    assert livepostings.find_postings(stopped, [group(n) for n in range(10)], list(range(10))) == 0
    assert len(stopped.prompts) == 1


def test_jobs_whose_found_posting_is_one_page_are_possible_duplicates_of_the_best_scored():
    groups = [group(n) for n in range(5)]
    for n, url in enumerate([CAREERS.format(1), CAREERS.format(1) + "/", CAREERS.format(2), "",
                             None]):
        groups[n].link_from_web = url
    scores = {0: 70, 1: 75, 2: 75, 3: 80, 4: 80}
    assert livepostings.same_postings(groups, [0, 1, 2, 3, 4], scores.get) == {0: 1}


def board_group(n, *urls, kinds=None):
    copies = [FoundJob(source=f"s{k}", source_job_id=f"{n}-{k}", url=url,
                       title="Hardware Engineer", company="FakeCo", location_text="Munich",
                       country="DE", description="FakeCo in Munich builds power converters.")
              for k, url in enumerate(urls)]
    return JobGroup(copies, source_kinds=kinds or {f"s{k}": "aggregator" for k in range(len(urls))})


ADZUNA = "https://www.adzuna.de/details/{}"
BA = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"


def test_a_good_job_whose_links_all_lead_through_job_sites_gets_its_employer_page_looked_up():
    # Search 18's best jobs had only Adzuna, Arbeitsagentur and trabajo links; one ended on
    # CV-Library behind Adzuna and one on a blank page.
    good, weak = {"score": 70}, {"score": 55}
    assert livepostings.needs_posting(board_group(1, ADZUNA.format(1), BA.format(1)), good)
    assert not livepostings.needs_posting(board_group(1, ADZUNA.format(1)), weak)
    workday = "https://fakeco.wd3.myworkdayjobs.com/External/job/Munich/HW_1"
    assert not livepostings.needs_posting(board_group(1, ADZUNA.format(1), workday), good)
    own = board_group(1, "https://careers.fakeco.example/1", kinds={"s0": "employer"})
    assert not livepostings.needs_posting(own, good)
    unknown = board_group(1, "https://jobs.fakeco.example/hardware-engineer")
    assert not livepostings.needs_posting(unknown, good)  # likely the employer's own site


def test_only_the_employers_page_of_that_vacancy_counts_as_a_direct_link():
    groups = [board_group(n, ADZUNA.format(n)) for n in range(4)]
    pages = ["https://de.linkedin.com/jobs/view/hardware-engineer-1", "https://fakeco.example/jobs/",
             CAREERS.format(2), "https://fakeco.example/stellenangebote?id=77"]
    client = Researcher(
        [("\n".join(f"JOB J{n} {page}" for n, page in enumerate(pages)), pages, 4)],
        [[{"id": f"J{n}", "url": page} for n, page in enumerate(pages)]])
    assert livepostings.find_postings(client, groups, [0, 1, 2, 3]) == 2
    assert [g.link_from_web for g in groups] == ["", "", CAREERS.format(2), pages[3]]
    assert "| employer's page |" in client.prompts[0]
    uk_only = Researcher([(f"JOB J0 {CAREERS.format(0)}", [CAREERS.format(0)], 1)],
                         [[{"id": "J0", "url": CAREERS.format(0)}]])
    livepostings.find_postings(uk_only, [group(0)], [0])
    assert "| any page open to applicants from any country |" in uk_only.prompts[0]
