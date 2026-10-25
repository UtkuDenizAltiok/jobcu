"""Looking the best jobs up online: where they are and what they ask (jobplace.py)."""

from datetime import UTC, datetime

import pytest

from jobcu import jobplace
from jobcu.ai.base import (
    AIInvalidOutput,
    AILimitReached,
    AIUnavailable,
    ResearchReply,
    Source,
    Usage,
)
from jobcu.dedupe import JobGroup, group_duplicates
from jobcu.sources.base import FoundJob

NOW = datetime.now(UTC)


class Researcher:
    """Stands in for the AI client: answers each web look-up with the next scripted notes, and
    each structuring step with the next scripted jobs, one request at a time."""

    parallel_requests = 1

    def __init__(self, notes, structured=()):
        self.notes = list(notes)
        self.structured = list(structured)
        self.prompts = []
        self.structure_prompts = []
        self.notifications = []

    def notify(self, message):
        self.notifications.append(message)

    def research(self, **request):
        self.prompts.append(request["prompt"])
        answer = self.notes.pop(0)
        if isinstance(answer, Exception):
            raise answer
        searched = 0 if answer.startswith("FROM MEMORY") else 1
        return ResearchReply(answer, [Source("https://jobs.test/a", "Board")],
                             Usage(10, 5, web_searches=searched))

    def generate(self, output, **request):
        self.structure_prompts.append(request["prompt"])
        return output.model_validate({"jobs": self.structured.pop(0)})


def jobs(*places):
    found = [FoundJob(source="adzuna", source_job_id=str(i), url="https://x", title=f"Job {i}",
                      company="Acme", location_text=place, country=country, posted_at=NOW,
                      description="Ein spannendes Team.")
             for i, (place, country) in enumerate(places)]
    return group_duplicates(found, {"adzuna": "aggregator"})


def online(job_id, towns=(), languages=(), years=None, found=True):
    return {"id": job_id, "found": found, "towns": list(towns),
            "languages_asked": [{"language": language, "level": level, "must_have": must}
                                for language, level, must in languages],
            "years_required": years, "doctorate": "not_required",
            "citizenship_or_clearance": "no_such_requirement", "citizenship_or_clearance_words": ""}


def test_only_jobs_nothing_places_are_looked_up():
    groups = jobs(("Deutschland", "DE"), ("München", "DE"), ("", None))
    assert [jobplace.needs_looking_up(g) for g in groups] == [True, False, False]
    groups[0].place_from_web = []
    assert not jobplace.needs_looking_up(groups[0])  # looked up already, never again


def test_completed_batch_is_kept_when_a_later_batch_is_interrupted():
    from jobcu.search import SearchStopped

    groups = jobs(*[("Deutschland", "DE")] * 6)
    researcher = Researcher(["Fictional complete notes", SearchStopped()],
                            [[online(f"J{i}", ["Berlin"]) for i in range(5)]])
    saved = {}
    with pytest.raises(SearchStopped):
        jobplace.find_online(researcher, groups, list(range(6)),
                             on_evidence=lambda i, value: saved.__setitem__(i, value))
    assert set(saved) == set(range(5))
    assert all(group.place_from_web == ["Berlin"] for group in groups[:5])
    assert groups[5].place_from_web is None
    restored = jobplace.saved_lookups(groups, saved)
    assert restored.asked == set(range(5))
    assert len(restored.requirements) == 5


def test_completed_online_evidence_survives_pool_storage_without_another_lookup():
    from jobcu import db, pool

    groups = jobs(("Deutschland", "DE"))
    answer = {**online("J0", ["Berlin"]), "requirement_checks": [{
        "requirement": "Registration", "ad_words": "Active registration required",
        "profile_words": "Unsupported fictional quote", "status": "met"}]}
    researcher = Researcher(["Active registration required"], [[answer]])
    saved = {}
    jobplace.find_online(researcher, groups, [0],
                         on_evidence=lambda i, value: saved.__setitem__(i, value))
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id,status,form_json) VALUES(1,'stopped','{}')")
    pool.save(pool.Pool(1, [pool.PoolJob(groups[0], online_evidence=saved[0])], {}))
    loaded = pool.load(1)
    restored = jobplace.saved_lookups([loaded.jobs[0].group], {0: loaded.jobs[0].online_evidence})
    assert restored.asked == {0} and 0 in restored.requirements
    check = restored.requirements[0].requirement_checks[0]
    assert check["status"] == "unclear" and check["proposed_status"] == "met"
    assert check["grounding_issues"] == ["profile_quote_unverified"]
    assert len(researcher.prompts) == len(researcher.structure_prompts) == 1
    assert loaded.jobs[0].group.place_from_web == ["Berlin"]


def test_completed_research_is_not_bought_again_after_structure_failure():
    from jobcu import db, pool
    from jobcu.ai.base import AIAuthError

    class Interrupted(Researcher):
        fail_once = True

        def generate(self, output, **request):
            if self.fail_once:
                self.fail_once = False
                raise AIAuthError("Fictional structure failure")
            return super().generate(output, **request)

    researcher = Interrupted(["Fictional completed research"], [[online("J0", ["Berlin"])]])
    cache = {}
    groups = jobs(("Deutschland", "DE"))
    first = jobplace.find_online(researcher, groups, [0], research_cache=cache)
    assert not first.asked and cache
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id,status,form_json) VALUES(1,'stopped','{}')")
    pool.save(pool.Pool(1, [pool.PoolJob(groups[0])], {}, research_notes=cache))
    loaded = pool.load(1)
    # A later safe conversion uses the original completed notes, not another web operation.
    second = jobplace.find_online(researcher, [loaded.jobs[0].group], [0],
                                  research_cache=loaded.research_notes)
    assert second.asked == {0} and loaded.jobs[0].group.place_from_web == ["Berlin"]
    assert len(researcher.prompts) == 1 and not loaded.research_notes


def test_unavailable_online_checks_explain_missing_evidence_without_clearing_jobs():
    groups = jobs(*[("Deutschland", "DE")] * 6)
    researcher = Researcher([AIUnavailable("fictional outage", "private diagnostic")])
    looked_up = jobplace.find_online(researcher, groups, list(range(6)))
    assert len(researcher.prompts) == 1  # persistent service failure stops queued requests
    assert researcher.notifications == [jobplace.INCOMPLETE_CHECKS]
    assert looked_up.asked == set() and looked_up.requirements == {}
    assert all(group.place_from_web is None for group in groups)
    assert len(groups) == 6 and "private diagnostic" not in str(researcher.notifications)


def test_online_role_reassessment_uses_this_jobs_evidence_and_existing_two_calls():
    from test_requirements import PROFILE, score

    from jobcu import scoring

    groups = jobs(("Berlin", "DE"), ("Munich", "DE"))
    words = "Design high-speed communications hardware and radio systems"
    answers = [{**online("J0"), "role_and_skills": 22, "role_words": words},
               {**online("J1"), "role_and_skills": 22, "role_words": words}]
    researcher = Researcher([f"JOB J0\n{words}.\nJOB J1\nProvide ordinary ward care."], [answers])
    found = jobplace.find_online(researcher, groups, [0, 1], PROFILE)
    assert len(researcher.prompts) == len(researcher.structure_prompts) == 1
    first, second = found.requirements[0], found.requirements[1]
    assert first.role_and_skills == 22 and second.role_and_skills is None
    updated = scoring.with_ad_read_online(score([]), PROFILE, [], None,
                                          role_and_skills=first.role_and_skills,
                                          role_words=first.role_words)
    assert updated["parts"]["role_and_skills"] == 22 and updated["score"] <= 60
    assert "Daily tasks are only partly aligned" in updated["reasons"]
    restored = scoring.with_ad_read_online(
        updated, PROFILE, [], None, role_and_skills=39, role_words="Provide ordinary ward care")
    assert restored["parts"]["role_and_skills"] == 39 and restored["score"] > 80


@pytest.mark.parametrize(("points", "words", "sources", "found"), [
    (22, "Missing ad words", True, True),
    (22, "Ordinary ward care", False, True),
    (22, "Ordinary ward care", True, False),
    (41, "Ordinary ward care", True, True),
    (22, "Ordinary ward care " * 10, True, True),
])
def test_unsupported_online_role_evidence_cannot_replace_a_score(points, words, sources, found):
    answer = {**online("J0", found=found), "role_and_skills": points, "role_words": words}

    class Evidence(Researcher):
        def research(self, **request):
            reply = super().research(**request)
            if not sources:
                reply.sources.clear()
            return reply

    researcher = Evidence(["JOB J0\nOrdinary ward care."], [[answer]])
    result = jobplace._look_up(researcher, ["J0 | Ward Nurse"], 1)["J0"]
    assert result.role_and_skills is None and result.role_words == ""
    assert len(researcher.prompts) == len(researcher.structure_prompts) == 1


def test_original_employer_url_goes_with_the_best_description():
    employer = FoundJob(source="employer", source_job_id="REQ-42", title="Nurse",
                        url="https://employer.test/jobs/REQ-42", country="IE",
                        company="Example Clinic", description="Employer teaser")
    board = FoundJob(source="board", source_job_id="84", title="Nurse", company="Example Clinic",
                     url="https://board.test/84", country="IE", description="Complete nursing ad",
                     description_is_complete=True)
    group = JobGroup(copies=[board, employer],
                     source_kinds={"employer": "employer", "board": "job_board"})
    researcher = Researcher(["notes"], [[online("J0", found=False)]])
    jobplace.find_online(researcher, [group], [0])
    assert "https://employer.test/jobs/REQ-42 | Complete nursing ad" in researcher.prompts[0]
    assert "https://board.test/84" not in researcher.prompts[0]


def test_towns_found_online_count_only_when_real_and_in_the_job_s_country():
    groups = jobs(*[("Deutschland", "DE")] * 6)
    first = [online("J0", ["Freiburg im Breisgau"]),
             online("J1", ["Wietmarschen-Lohne; Berlin"]),  # two sites
             online("J2", found=False),
             online("J3", ["Bayern"]),  # a region, not a town
             online("J4", ["Vienna"])]  # not in Germany
    researcher = Researcher(["notes", "notes"], [first, []])  # J5: not answered at all
    looked_up = jobplace.find_online(researcher, groups, list(range(6)))
    assert looked_up.towns_found == 2 and looked_up.asked == set(range(6))
    assert [g.place_from_web for g in groups] == [
        ["Freiburg im Breisgau"], ["Wietmarschen-Lohne", "Berlin"], [], [], [], []]
    assert len(researcher.prompts) == 2  # five jobs per request
    assert "J0 | Job 0 | Acme | DE | https://x | Ein spannendes Team." in researcher.prompts[0]
    assert researcher.structure_prompts[0].endswith("Research notes:\nnotes")


def test_looking_up_stops_when_the_search_s_allowance_is_used():
    groups = jobs(*[("UK", "GB")] * 7)
    researcher = Researcher(["notes", AILimitReached("used up")],
                            [[online("J0", ["Leeds"])]])
    progress = []
    looked_up = jobplace.find_online(researcher, groups, list(range(7)),
                                     on_progress=lambda done, total: progress.append(done))
    assert looked_up.towns_found == 1 and looked_up.asked == set(range(5))
    assert groups[0].place_from_web == ["Leeds"]
    assert groups[5].place_from_web is None  # not looked up: can be later
    assert progress == [5]  # deferred jobs must not make the counter appear complete
    researcher.notes.append("notes")
    researcher.structured.append([online("J5", ["Leeds"])])
    offset = 7 - len(looked_up.not_asked)
    jobplace.find_online(researcher, groups, looked_up.not_asked,
                        on_progress=lambda done, total: progress.append(offset + done))
    assert progress == [5, 7]  # continuing never moves backwards or counts a job twice


def test_one_unusable_answer_loses_only_its_own_jobs_and_progress_is_counted():
    groups = jobs(*[("UK", "GB")] * 7)
    researcher = Researcher([AIInvalidOutput("not in the format"), "notes"],
                            [[online("J5", ["Leeds"])]])
    progress = []
    looked_up = jobplace.find_online(researcher, groups, list(range(7)),
                                     on_progress=lambda done, total: progress.append(done))
    assert looked_up.asked == {5, 6} and looked_up.not_asked == []
    assert groups[0].place_from_web is None  # can be looked up again later
    assert groups[5].place_from_web == ["Leeds"]
    assert progress == [5, 7]


def test_the_service_being_down_stops_the_jobs_not_asked_yet():
    groups = jobs(*[("UK", "GB")] * 12)
    researcher = Researcher([AIUnavailable("down"), "notes", "notes"])
    looked_up = jobplace.find_online(researcher, groups, list(range(12)))
    assert len(researcher.prompts) == 1 and looked_up.asked == set()
    assert looked_up.not_asked == []  # not a question of web look-ups: nothing to offer


def test_the_full_ad_found_online_gives_its_languages_and_years():
    groups = jobs(("Deutschland", "DE"), ("Radeberg", "DE"), ("Dresden", "DE"))
    answer = [online("J0", ["Radeberg"], [("German", "B2", True), ("English", "B2", False)], 3),
              online("J1"),
              online("J2", found=False)]
    looked_up = jobplace.find_online(Researcher(["notes"], [answer]), groups, [0, 1, 2])
    found = looked_up.requirements
    assert set(found) == {0, 1}
    assert [(a.language, a.level, a.must_have) for a in found[0].languages] == [
        ("German", "B2", True), ("English", "B2", False)]
    assert found[0].years_required == 3
    assert found[1].languages == [] and found[1].years_required is None
    assert found[0].blockers == {"doctorate": "not_required",
                                 "citizenship_or_clearance": "no_such_requirement",
                                 "citizenship_or_clearance_words": "",
                                 "visa_sponsorship": "unclear", "visa_sponsorship_words": "",
                                 "right_to_work_required": "not_stated",
                                 "right_to_work_words": "", "versions_differ": "",
                                 "sponsorship_confirmed": False}
    # Only the job without a town gets one from the answer; the others keep theirs.
    assert groups[0].place_from_web == ["Radeberg"]
    assert all(g.place_from_web is None for g in groups[1:])


def test_online_requirement_audit_survives_structured_model_conversion():
    from test_search import PROFILE

    from jobcu.profile import Profile

    group = jobs(("Berlin", "DE"))[0]
    row = online("J0")
    row["requirement_checks"] = [{
        "requirement": "PCB layout", "ad_words": "An invented required skill",
        "profile_words": "PCB layout", "status": "met"}]
    researcher = Researcher(["JOB J0\nPCB layout is required."], [[row]])
    result = jobplace.find_online(researcher, [group], [0], Profile.model_validate(PROFILE))
    check = result.requirements[0].requirement_checks[0]
    assert check["status"] == "unclear" and check["proposed_status"] == "met"
    assert check["grounding_issues"] == ["ad_quote_unverified"]


def test_an_answer_given_without_searching_the_web_is_asked_again_then_ignored():
    groups = jobs(("Deutschland", "DE"), ("Deutschland", "DE"))
    answer = [online("J0", ["Hamburg"], [("German", "B2", True)]), online("J1")]
    researcher = Researcher(["FROM MEMORY", "notes"], [answer])
    looked_up = jobplace.find_online(researcher, groups, [0, 1])
    assert len(researcher.prompts) == 2 and set(looked_up.requirements) == {0, 1}
    assert groups[0].place_from_web == ["Hamburg"]

    groups = jobs(("Deutschland", "DE"), ("Deutschland", "DE"))
    researcher = Researcher(["FROM MEMORY", "FROM MEMORY"])
    looked_up = jobplace.find_online(researcher, groups, [0, 1])
    assert len(researcher.prompts) == 2 and not researcher.structure_prompts
    assert looked_up.requirements == {} and looked_up.asked == {0, 1}
    assert [g.place_from_web for g in groups] == [[], []]  # asked, nothing to trust


def test_summaries_that_could_make_the_list_are_looked_up_for_their_requirements():
    group = jobs(("Dresden", "DE"))[0]
    scored = {"score": 50, "evidence": {}}
    assert jobplace.needs_requirements(group, scored)
    assert not jobplace.needs_requirements(group, {**scored, "score": 49})
    assert not jobplace.needs_requirements(group, {**scored, "read_online": True})
    assert not jobplace.needs_requirements(group, {"score": 80})  # scored by an older Jobcu
    group.copies[0].description_is_complete = True
    assert not jobplace.needs_requirements(group, scored)
