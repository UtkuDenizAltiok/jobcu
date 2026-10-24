"""Compares AI providers on the exact requests of one captured search.

A private comparison capture records every AI request of one search with its answer. This tool
sends the same requests to another provider and model and compares the answers step by step.
Scores are finished by Jobcu's own rules for both answers, so only the AI's reading differs.
Research is repeated with the other provider's own web search, and its notes are turned into
the app's format by that provider too. Settings, saved searches and the capture stay unchanged.

    uv run python tools/compare_providers.py CAPTURE --to mimo:mimo-v2.6-pro
    ... --steps scoring,quick_pass --limit 10 --budget <allowance id> --out report.json
    ... --to gemini:gemini-3.8-flash       the same model again: how much answers vary anyway
    ... --setup                            fresh document/location readings and search words
    uv run python tools/compare_providers.py --saved-ads --runs 2 \
        --to openrouter:deepseek/deepseek-v4.1-flash-1017@fireworks --labels labels.json \
        --out runs.json

CAPTURE is a folder in the data folder's review-captures. Requests are paid: about as many as
the captured search sent for the chosen steps, recorded in the usage log (with --budget, against
that separate allowance). The report and printed lists contain private job and profile details.

`--saved-ads` needs no capture: it scores the ads the Score check keeps (data folder), with the
newest saved profile and each ad's recorded location plan, so every model gets the same test.
`--labels` compares the scores with a private file of expected ranges ({"ranges": {id: [lo,
hi]}}); `--against` with earlier runs. OpenRouter is `--to openrouter:<model>[@host]` with its
saved key. Any other service is `--to openai_compatible:<model>` with `--base-url` (and the
protocol/reasoning options Settings offers); it uses the key saved for "Other API".
"""

import argparse
import ast
import json
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pydantic import BaseModel  # noqa: E402

from jobcu import (  # noqa: E402
    jobplace,
    keywords,
    location,
    recheck,
    reference_places,
    reference_sources,
    relevance,
    scoring,
    travel,
)
from jobcu import profile as profiles  # noqa: E402
from jobcu.ai.base import AIError, Citation, ResearchReply, Source, Usage  # noqa: E402
from jobcu.ai.client import THINKING_ROOM, AIClient, in_parallel  # noqa: E402
from jobcu.ai.schema import extract_json, strict_json_schema  # noqa: E402
from jobcu.ai.usage import ModelUsage, UsageLog, estimate_cost  # noqa: E402
from jobcu.countries import COUNTRIES, languages_for  # noqa: E402
from jobcu.dedupe import group_duplicates  # noqa: E402
from jobcu.keystore import KeyStore  # noqa: E402
from jobcu.location import ReferenceCheck  # noqa: E402
from jobcu.settings import load_settings  # noqa: E402
from jobcu.sources.base import FoundJob  # noqa: E402

OUTPUTS: dict[str, type[BaseModel]] = {model.__name__: model for model in (
    scoring.ScoringAnswer, relevance.QuickPassAnswer, relevance.TitleScreen,
    jobplace.OnlineAnswer, reference_places.ReferenceAnswers, reference_sources.Answers,
    location.LocationInterpretation, location.LocationUnderstanding, location.SortedConditions,
    location.CheckedCondition, profiles.Profile, keywords.SearchWordsAnswer,
    recheck.Comparisons, travel.TravelGuesses,
)}
# Structuring steps that read research notes: replayed together with their research.
NOTES_MARK = "Research notes:\n"
BANDS = ((70, "good"), (50, "fair"), (0, "low"))


@dataclass
class Call:
    number: int
    step: str
    operation: str
    arguments: dict
    reply: dict | None
    error: str | None
    elapsed: float | None


@dataclass
class Item:
    """One replayed request, or one research request with its structuring request."""

    step: str
    kind: str  # the output's name, or "research:<output>"
    calls: list[Call]
    result: dict = field(default_factory=dict)


def load_calls(folder: Path) -> list[Call]:
    starts, calls = {}, []
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            if event["kind"] == "ai_start":
                starts[event["attempt"]] = event
            elif event["kind"] == "ai_end" and event["attempt"] in starts:
                start = starts.pop(event["attempt"])
                calls.append(Call(len(calls), start["step"], start["operation"],
                                  start["arguments"], event.get("reply"), event.get("error"),
                                  event.get("elapsed")))
    return calls


def items_from(calls: list[Call]) -> list[Item]:
    """Pair each research request with the structuring request that quotes its notes."""
    done = [call for call in calls if call.reply is not None]
    structured = {}
    for research in (c for c in done if c.operation == "research"):
        notes = research.reply.get("text", "")
        for other in done:
            if (other.operation == "complete_json" and other.step == research.step
                    and other.number not in structured and notes.strip()
                    and NOTES_MARK + notes in other.arguments["prompt"]):
                structured[other.number] = research
                break
    items, paired = [], {research.number: number for number, research in structured.items()}
    for call in done:
        if call.number in structured:
            continue
        if call.operation == "research":
            if call.number in paired:
                follow = next(c for c in done if c.number == paired[call.number])
                items.append(Item(call.step, f"research:{follow.arguments['schema_name']}",
                                  [call, follow]))
            continue
        items.append(Item(call.step, call.arguments["schema_name"], [call]))
    return items


def requested_tokens(arguments: dict) -> int:
    """The step's own answer room, before the client adds the same thinking room again."""
    room = THINKING_ROOM.get(arguments.get("effort") or "", 0)
    return max(500, arguments["max_output_tokens"] - room)


def parse(kind: str, text: str):
    try:
        return OUTPUTS[kind].model_validate(extract_json(text))
    except (ValueError, KeyError):
        return None


def research_reply(data: dict) -> ResearchReply:
    citations = data.get("citations")
    return ResearchReply(
        data.get("text", ""), [Source(**s) for s in data.get("sources") or []],
        Usage(**(data.get("usage") or {})),
        None if citations is None else [Citation(**c) for c in citations])


class Replayer:
    def __init__(self, provider: str, model: str, budget: str | None,
                 endpoint: dict | None = None) -> None:
        settings = load_settings().model_copy(deep=True)
        ai = settings.ai
        ai.provider, ai.model, ai.reasoning_model = provider, model, ""
        for name, value in (endpoint or {}).items():
            setattr(ai, name, value)  # base_url and the compatible_* controls for Other API
        ai.research_provider, ai.research_model = None, ""
        # Stateless requests: replays never ask a provider to retain an operation.
        ai.recover_interrupted_requests = False
        settings.use_web_search = True
        self.usage = UsageLog()
        self.client = AIClient(settings, KeyStore(), usage_log=self.usage, budget_id=budget,
                               notify=lambda message: print(f"  notice: {message}"))
        self.provider, self.model = provider, model
        self.first_usage_id = last_usage_id()

    def generate(self, call: Call, prompt: str | None = None) -> tuple[BaseModel, float]:
        arguments = call.arguments
        output = OUTPUTS[arguments["schema_name"]]
        if strict_json_schema(output) != arguments["schema"]:
            print(f"  warning: {output.__name__} changed since the capture; replaying the "
                  "current format")
        effort = arguments.get("effort")
        ai = self.client.settings.ai
        ai.scoring_effort = ai.reasoning_effort = effort
        started = time.monotonic()
        answer = self.client.generate(
            output, step=call.step, system=arguments["system"],
            prompt=arguments["prompt"] if prompt is None else prompt,
            max_output_tokens=requested_tokens(arguments))
        return answer, time.monotonic() - started

    def research(self, call: Call) -> tuple[ResearchReply, float]:
        arguments = call.arguments
        started = time.monotonic()
        reply = self.client.research(
            step=call.step, system=arguments["system"], prompt=arguments["prompt"],
            max_searches=arguments["max_searches"],
            max_output_tokens=requested_tokens(arguments), effort=arguments.get("effort"))
        return reply, time.monotonic() - started


# ---------------------------------------------------------------------------
# Replaying and comparing each kind of request
# ---------------------------------------------------------------------------


def replay(replayer: Replayer, item: Item) -> dict:
    first = item.calls[0]
    started = time.monotonic()
    try:
        if item.kind.startswith("research:"):
            return replay_research(replayer, item)
        answer, elapsed = replayer.generate(first)
        before = parse(item.kind, first.reply["text"])
        return {"baseline": before.model_dump() if before else None,
                "baseline_valid": before is not None,
                "candidate": answer.model_dump(), "elapsed": elapsed,
                "baseline_elapsed": first.elapsed}
    except AIError as exc:
        return {"error": type(exc).__name__, "message": exc.message,
                "elapsed": time.monotonic() - started}
    except (ValueError, KeyError) as exc:  # an unreadable capture entry, not a provider answer
        return {"error": type(exc).__name__, "message": str(exc)[:300],
                "elapsed": time.monotonic() - started}


def replay_research(replayer: Replayer, item: Item) -> dict:
    research, structure = item.calls
    before_notes = research_reply(research.reply)
    reply, research_elapsed = replayer.research(research)
    prompt = structure.arguments["prompt"]
    kind = item.kind.split(":", 1)[1]
    if kind == "ReferenceAnswers":
        text, lines = reference_parts(research.arguments["prompt"])
        sources = {f"S{i}": s for i, s in enumerate(reply.sources)}
        links = (None if reply.citations is None else {
            key: [c.text for c in reply.citations
                  if c.url == source.url and reply.text.count(c.text) == 1]
            for key, source in sources.items()})
        new_prompt = reference_places._structure_prompt(text, lines, reply.text, sources, links)
    else:
        head = prompt.split(NOTES_MARK + before_notes.text, 1)[0]
        new_prompt = head + NOTES_MARK + reply.text
    answer, elapsed = replayer.generate(structure, new_prompt)
    before = parse(kind, structure.reply["text"])
    result = {
        "baseline": before.model_dump() if before else None, "baseline_valid": before is not None,
        "candidate": answer.model_dump(), "elapsed": research_elapsed + elapsed,
        "baseline_elapsed": (research.elapsed or 0) + (structure.elapsed or 0),
        "baseline_notes": before_notes.text, "candidate_notes": reply.text,
        "baseline_sources": [s.url for s in before_notes.sources],
        "candidate_sources": [s.url for s in reply.sources],
        "baseline_web": before_notes.usage.web_searches, "candidate_web": reply.usage.web_searches,
    }
    if kind == "ReferenceAnswers":
        result["cities"] = reference_outcomes(research, before_notes, before, reply, answer)
    return result


def reference_parts(prompt: str) -> tuple[str, list[str]]:
    found = re.match(r"Condition \(data\):\n<<<\n(.*)\n>>>\nReference cities:\n(.*)\Z",
                     prompt, re.DOTALL)
    if not found:
        raise ValueError("Unrecognised reference-city research request")
    return found[1], found[2].split("\n")


def reference_outcomes(research: Call, before_notes, before, reply, answer) -> list[dict]:
    """Apply Jobcu's own validation to both answers: a claim without its source is unknown."""
    _, lines = reference_parts(research.arguments["prompt"])
    codes = {country.name: code for code, country in COUNTRIES.items()}
    names = [line.split(" | ")[1:3] for line in lines]
    outcomes = []
    for label, notes, structured in (("baseline", before_notes, before),
                                     ("candidate", reply, answer)):
        checks = [ReferenceCheck(name=name, country=codes[country]) for name, country in names]
        if structured is not None:
            sources = {f"S{i}": s for i, s in enumerate(notes.sources)}
            links = (None if notes.citations is None else {
                key: [c.text for c in notes.citations
                      if c.url == source.url and notes.text.count(c.text) == 1]
                for key, source in sources.items()})
            reference_places._apply(checks, structured, notes.text, sources, links)
        outcomes.append({label: [c.meets for c in checks]})
    return [{"city": name, "country": country, "baseline": outcomes[0]["baseline"][i],
             "candidate": outcomes[1]["candidate"][i]} for i, (name, country) in enumerate(names)]


# Scoring --------------------------------------------------------------------

JOB_BLOCK = re.compile(
    r"JOB (J\d+)\nTitle: (.*)\nCompany: (.*)\nLocation: (.*)\n.*?\nSalary: .*?\n"
    r"Ad text( \(only the start of the ad is available\))?:\n<<<\n(.*?)\n>>>", re.DOTALL)


def scoring_jobs(prompt: str) -> tuple[profiles.Profile, dict[str, dict]]:
    person = prompt.split("THE PERSON'S PROFILE:\n", 1)[1].split(
        "\n\nWHERE THE PERSON WANTS TO WORK:", 1)[0]
    profile = profiles.Profile.model_validate(
        {"ignored_as_application_specific": [], **ast.literal_eval(person)})
    jobs = {}
    for found in JOB_BLOCK.finditer(prompt):
        country = re.search(r"\(([A-Z]{2})\)\s*$", found[4])
        jobs[found[1]] = {"title": found[2], "company": found[3], "location": found[4],
                          "complete": not found[5], "text": found[6],
                          "country": country[1] if country else None}
    return profile, jobs


def finished_scores(answer: dict | None, profile, jobs: dict) -> dict[str, dict]:
    scores = {}
    for raw in (answer or {}).get("scores", []):
        job = jobs.get(raw["job_id"])
        if job is None or raw["job_id"] in scores:
            continue
        done = scoring.finish(scoring.JobScore.model_validate(raw), profile,
                              ad_text=job["text"], complete=job["complete"],
                              country=job["country"])
        scores[raw["job_id"]] = {"score": done["score"], "parts": done["parts"],
                                 "reasons": done["reasons"],
                                 "limits": [limit["why"] for limit in done["limits"]],
                                 "languages": done["required_languages"],
                                 "years": raw.get("years_required"),
                                 "citizenship": raw.get("citizenship_or_clearance")}
    return scores


def band(score: int) -> str:
    return next(name for low, name in BANDS if score >= low)


def spearman(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None

    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        result = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                result[order[k]] = (i + j) / 2
            i = j + 1
        return result

    a, b = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    try:
        return statistics.correlation(a, b)
    except statistics.StatisticsError:
        return None


def compare_scoring(items: list[Item]) -> dict:
    rows = []
    for item in items:
        if "candidate" not in item.result:
            continue
        profile, jobs = scoring_jobs(item.calls[0].arguments["prompt"])
        before = finished_scores(item.result["baseline"], profile, jobs)
        after = finished_scores(item.result["candidate"], profile, jobs)
        for job_id, job in jobs.items():
            if job_id in before and job_id in after:
                rows.append({"title": job["title"], "company": job["company"],
                             "location": job["location"], "complete": job["complete"],
                             "baseline": before[job_id], "candidate": after[job_id]})
    pairs = [(r["baseline"]["score"], r["candidate"]["score"]) for r in rows]
    differences = [b - a for a, b in pairs]
    top = sorted(range(len(rows)), key=lambda i: -pairs[i][0])[:10]
    top_candidate = sorted(range(len(rows)), key=lambda i: -pairs[i][1])[:10]
    return {
        "jobs": len(rows),
        "mean_absolute_difference": statistics.fmean(map(abs, differences)) if rows else None,
        "mean_difference_candidate_minus_baseline": statistics.fmean(differences)
        if rows else None,
        "spearman": spearman(pairs),
        "same_band": sum(band(a) == band(b) for a, b in pairs),
        "within_10": sum(abs(d) <= 10 for d in differences),
        "top_10_overlap": len(set(top) & set(top_candidate)),
        "rows": rows,
    }


# Quick checks ----------------------------------------------------------------


def listed_titles(prompt: str, prefix: str) -> dict[str, str]:
    return {found[1]: found[2].strip() for found in re.finditer(
        rf"^({prefix}\d+) \| ([^|]*)\|", prompt, re.MULTILINE)}


def compare_unrelated(items: list[Item], prefix: str) -> dict:
    both = only_baseline = only_candidate = kept = 0
    differences = []
    total = 0
    for item in items:
        if "candidate" not in item.result or not item.result["baseline_valid"]:
            continue
        titles = listed_titles(item.calls[0].arguments["prompt"], prefix)
        before = set(item.result["baseline"]["clearly_unrelated"]) & titles.keys()
        after = set(item.result["candidate"]["clearly_unrelated"]) & titles.keys()
        total += len(titles)
        both += len(before & after)
        kept += len(titles.keys() - before - after)
        for job_id in sorted(before - after):
            only_baseline += 1
            differences.append({"left_out_by": "baseline", "title": titles[job_id]})
        for job_id in sorted(after - before):
            only_candidate += 1
            differences.append({"left_out_by": "candidate", "title": titles[job_id]})
    return {"titles": total, "both_left_out": both, "both_kept": kept,
            "only_baseline_left_out": only_baseline, "only_candidate_left_out": only_candidate,
            "differences": differences}


# Online job checks ------------------------------------------------------------


def compare_online(items: list[Item]) -> dict:
    rows = []
    for item in items:
        if "candidate" not in item.result:
            continue
        titles = listed_titles(item.calls[0].arguments["prompt"], "J")
        before = {j["id"]: j for j in (item.result["baseline"] or {}).get("jobs", [])}
        after = {j["id"]: j for j in item.result["candidate"].get("jobs", [])}
        for job_id, title in titles.items():
            a, b = before.get(job_id, {}), after.get(job_id, {})
            rows.append({
                "title": title,
                "found": (a.get("found"), b.get("found")),
                "towns": (a.get("towns"), b.get("towns")),
                "years": (a.get("years_required"), b.get("years_required")),
                "languages": ([f"{x['language']} {x['level']}" for x in a.get(
                    "languages_asked", [])], [f"{x['language']} {x['level']}"
                                             for x in b.get("languages_asked", [])]),
                "citizenship": (a.get("citizenship_or_clearance"),
                                b.get("citizenship_or_clearance")),
                "role": (a.get("role_and_skills"), b.get("role_and_skills")),
            })
    found = [r["found"] for r in rows]
    return {
        "jobs": len(rows),
        "baseline_found": sum(bool(a) for a, _ in found),
        "candidate_found": sum(bool(b) for _, b in found),
        "both_found": sum(bool(a) and bool(b) for a, b in found),
        "same_towns_when_both_found": sum(
            r["found"] == (True, True) and sorted(r["towns"][0] or []) == sorted(
                r["towns"][1] or []) for r in rows),
        "rows": rows,
    }


def compare_cities(items: list[Item]) -> dict:
    rows = [row for item in items for row in item.result.get("cities", [])]
    return {"cities": len(rows),
            "baseline_known": sum(r["baseline"] is not None for r in rows),
            "candidate_known": sum(r["candidate"] is not None for r in rows),
            "agree_when_both_known": sum(r["baseline"] == r["candidate"] for r in rows
                                         if None not in (r["baseline"], r["candidate"])),
            "rows": rows}


# Usage -----------------------------------------------------------------------


def costs(items: list[Item], replayer: Replayer, baseline: tuple[str, str]) -> dict:
    prices = load_settings().prices
    before = Usage()
    for item in items:
        for call in item.calls:
            if call.reply and call.reply.get("usage"):
                before += Usage(**call.reply["usage"])
    from jobcu import db

    with db.connect() as conn:
        rows = conn.execute(
            """SELECT SUM(input_tokens), SUM(output_tokens), SUM(cached_input_tokens),
               SUM(reasoning_tokens), SUM(web_searches), SUM(unreported_requests)
               FROM ai_usage WHERE id > ? AND provider = ? AND model = ?""",
            (replayer.first_usage_id, replayer.provider, replayer.model)).fetchone()
    after = [ModelUsage(replayer.provider, replayer.model, Usage(*(v or 0 for v in rows)))]
    estimate_before, complete_before = estimate_cost([ModelUsage(*baseline, before)], prices)
    estimate_after, complete_after = estimate_cost(after, prices)
    return {"baseline_usage": before.__dict__,
            "baseline_estimate": round(estimate_before, 4),
            "baseline_estimate_complete": complete_before,
            "candidate_usage": [u.usage.__dict__ for u in after],
            "candidate_estimate": round(estimate_after, 4),
            "candidate_estimate_complete": complete_after}


def capture_events(folder: Path, *kinds: str) -> dict[str, dict]:
    found = {}
    with (folder / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            if event["kind"] in kinds and event["kind"] not in found:
                found[event["kind"]] = event
    return found


def compare_setup(folder: Path, providers: list[tuple[str, str]], budget: str | None,
                  endpoint: dict | None = None) -> dict:
    """Ask each provider to read the captured documents and location text freshly.

    Searches reuse these readings, so a capture rarely holds them. The location reading stops
    before research: facts about places are compared through the replayed research requests.
    """
    found = capture_events(folder, "documents", "inputs")
    documents, form = found["documents"], found["inputs"]["form"]
    readings = {}
    for provider, model in providers:
        client = Replayer(provider, model, budget,
                          endpoint if provider == "openai_compatible" else None).client
        started = time.monotonic()
        try:
            profile = profiles.read_profile(client, documents["cv"], documents["cover_letter"],
                                            form.get("about_you", ""))
            reading, _ = location._read_location(client, form["location_text"].strip())
            plan = location.plan_from(form["location_text"].strip(),
                                      location.LocationUnderstanding.model_validate({
                                          **reading.model_dump(),
                                          "conditions_about_places": [
                                              c.text for c in reading.conditions_about_places],
                                          "conditions_about_the_job": [
                                              c.text for c in reading.conditions_about_the_job]}))
            words = keywords.generate_search_words(
                client, profile, languages_for(plan.countries, plan.places))
        except AIError as exc:
            readings[f"{provider}:{model}"] = {"error": type(exc).__name__,
                                                "message": exc.message}
            continue
        readings[f"{provider}:{model}"] = {
            "seconds": round(time.monotonic() - started, 1),
            "profile": profile.model_dump(), "location": reading.model_dump(),
            "search_words": [w.model_dump() for w in words]}
    for name, reading in readings.items():
        print(f"\n== {name}")
        if "error" in reading:
            print(f"   {reading['error']}: {reading['message']}")
            continue
        profile, where = reading["profile"], reading["location"]
        print(f"   {reading['seconds']}s; seniority {profile['seniority']}; full-time years "
              f"{profile['years_full_time_experience']}; languages "
              + ", ".join(f"{s['language']} {s['cefr']}" for s in profile["languages"]))
        print(f"   target roles: {', '.join(profile['target_roles'])}")
        print(f"   work authorisation: {profile['work_authorisation']}")
        print(f"   location: {where['understood_as']} countries {where['countries']}")
        for condition in where["conditions_about_places"] + where["conditions_about_the_job"]:
            anchor = condition.get("anchor") or {}
            print(f"   - {condition['kind']}: {condition['understood_as']} | minutes "
                  f"{condition['max_minutes']} {condition['travel_mode']} | share "
                  f"{condition['min_share_of_country'] or anchor.get('min_share_of_country')}"
                  f" | look up: {anchor.get('look_up') or ''}")
        by_language: dict[str, list[str]] = {}
        for word in reading["search_words"]:
            by_language.setdefault(word["language"], []).append(word["text"])
        for language, texts in by_language.items():
            print(f"   words {language} ({len(texts)}): {', '.join(texts)}")
    return readings


def saved_ads_runs(replayer: Replayer, runs: int) -> list[dict]:
    """Score the Score check's saved ads `runs` times with one model; same inputs every time."""
    from jobcu import db, quality

    with db.connect() as conn:
        row = conn.execute("SELECT profile_json FROM profile_cache ORDER BY created_at DESC "
                           "LIMIT 1").fetchone()
    if row is None:
        raise SystemExit("No saved profile yet: run a search first.")
    profile = profiles.Profile.model_validate_json(row["profile_json"])
    ads = [ad for ad in quality.all_ads() if ad.kind == "scored"]
    groups = [group_duplicates([FoundJob(
        source=ad.kind, source_job_id=str(ad.id), url=ad.url, title=ad.title,
        company=ad.company, location_text=ad.location, description=ad.text,
        description_is_complete=ad.description_is_complete)], {ad.kind: "job_board"})[0]
        for ad in ads]
    anywhere = location.LocationPlan(text="", understood_as="Anywhere.", countries=[], places=[],
                                     not_checked_yet=[], outside_supported_area=[], broad=True)
    by_plan: dict[str, list[int]] = {}
    for index, ad in enumerate(ads):
        by_plan.setdefault(json.dumps(ad.location_plan, sort_keys=True), []).append(index)
    results = []
    for run in range(runs):
        started, scored = time.monotonic(), {}
        for indexes in by_plan.values():
            recorded = ads[indexes[0]].location_plan
            plan = location.LocationPlan.model_validate(recorded) if recorded else anywhere
            try:
                scored.update(scoring.score_groups(replayer.client, profile, plan, groups,
                                                   indexes))
            except AIError as exc:
                print(f"  run {run + 1}: {type(exc).__name__}: {exc.message}")
        results.append({"model": f"{replayer.provider}:{replayer.model}",
                        "seconds": round(time.monotonic() - started),
                        "ads": {str(ad.id): {
                            "title": ad.title, "score": scored[i]["score"],
                            "parts": scored[i]["parts"], "reasons": scored[i]["reasons"],
                            "limits": [limit["why"] for limit in scored[i]["limits"]]}
                            for i, ad in enumerate(ads) if i in scored}})
        print(f"  run {run + 1}: {len(results[-1]['ads'])}/{len(ads)} ads scored in "
              f"{results[-1]['seconds']}s")
    return results


def show_saved_ads(runs: list[dict], labels: dict | None, others: list[dict]) -> None:
    every = [*others, *runs]
    names = [f"{run['model']} #{i + 1}" for i, run in enumerate(every)]
    if labels:
        print("\nAgainst the expected ranges (within 5 points counts as in range):")
        for name, run in zip(names, every, strict=True):
            ids = [i for i in labels if i in run["ads"]]
            if not ids:
                print(f"  {name:45} no ads scored")
                continue
            scores = [run["ads"][i]["score"] for i in ids]
            middle = [sum(labels[i]) / 2 for i in ids]
            near = sum(labels[i][0] - 5 <= s <= labels[i][1] + 5
                       for i, s in zip(ids, scores, strict=True))
            off = statistics.fmean(max(0, labels[i][0] - s, s - labels[i][1])
                                   for i, s in zip(ids, scores, strict=True))
            agreement = spearman(list(zip(scores, middle, strict=True)))
            print(f"  {name:45} rank agreement {agreement:.3f} | "
                  f"in range {near}/{len(ids)} | average miss {off:.1f}")
    print("\nBetween runs (average difference / rank agreement):")
    for a in range(len(every)):
        for b in range(a + 1, len(every)):
            ids = [i for i in every[a]["ads"] if i in every[b]["ads"]]
            pairs = [(every[a]["ads"][i]["score"], every[b]["ads"][i]["score"]) for i in ids]
            print(f"  {names[a]} vs {names[b]}: "
                  f"{statistics.fmean(abs(x - y) for x, y in pairs):.1f} / {spearman(pairs):.3f}")


def last_usage_id() -> int:
    from jobcu import db

    with db.connect() as conn:
        return conn.execute("SELECT COALESCE(MAX(id), 0) FROM ai_usage").fetchone()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("capture", type=Path, nargs="?", help="a folder in review-captures")
    parser.add_argument("--to", required=True, help="provider:model to compare with")
    parser.add_argument("--steps", help="comma-separated steps, e.g. scoring,quick_pass")
    parser.add_argument("--kinds", help="comma-separated answer formats, e.g. ScoringAnswer")
    parser.add_argument("--limit", type=int, help="at most this many requests per format")
    parser.add_argument("--budget", help="a separate allowance ID for this paid comparison")
    parser.add_argument("--out", type=Path, help="write the full private report here")
    parser.add_argument("--setup", action="store_true",
                        help="compare fresh document and location readings and search words "
                             "instead of replaying requests")
    parser.add_argument("--saved-ads", action="store_true",
                        help="score the Score check's saved ads instead of a capture")
    parser.add_argument("--runs", type=int, default=1, help="with --saved-ads: repetitions")
    parser.add_argument("--labels", type=Path, help="with --saved-ads: expected score ranges")
    parser.add_argument("--against", type=Path, nargs="*", default=[],
                        help="with --saved-ads: earlier --out files to compare with")
    parser.add_argument("--base-url", default="", help="Other API: the provider's address")
    parser.add_argument("--protocol", default="chat_completions",
                        choices=["chat_completions", "responses", "messages"])
    parser.add_argument("--reasoning", default="effort",
                        choices=["effort", "thinking", "provider_default"])
    parser.add_argument("--medium", default="medium", choices=["medium", "high", "max"])
    args = parser.parse_args()
    provider, _, model = args.to.partition(":")
    if not model:
        parser.error("--to needs provider:model")
    endpoint = ({"base_url": args.base_url, "compatible_protocol": args.protocol,
                 "compatible_reasoning": args.reasoning, "compatible_medium": args.medium}
                if provider == "openai_compatible" else None)
    if provider == "openai_compatible" and not args.base_url:
        parser.error("Other API needs --base-url")
    if args.saved_ads:
        runs = saved_ads_runs(Replayer(provider, model, args.budget, endpoint), args.runs)
        labels = None
        if args.labels:
            labels = {key: value for key, value in
                      json.loads(args.labels.read_text(encoding="utf-8"))["ranges"].items()}
        others = [run for path in args.against
                  for run in json.loads(path.read_text(encoding="utf-8"))]
        show_saved_ads(runs, labels, others)
        if args.out:
            args.out.write_text(json.dumps(runs, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        return 0
    if args.capture is None:
        parser.error("a capture folder is needed unless --saved-ads is given")
    captured = capture_events(args.capture, "inputs")["inputs"]["ai"]
    if args.setup:
        readings = compare_setup(args.capture, [(captured["provider"], captured["model"]),
                                                (provider, model)], args.budget, endpoint)
        if args.out:
            args.out.write_text(json.dumps(readings, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        return 0
    calls = load_calls(args.capture)
    if not calls:
        print("The capture holds no AI requests.")
        return 1
    baseline = (captured["provider"], calls[0].arguments["model"])
    items = items_from(calls)
    if args.steps:
        items = [i for i in items if i.step in args.steps.split(",")]
    if args.kinds:
        items = [i for i in items if i.kind.split(":")[-1] in args.kinds.split(",")
                 or i.kind in args.kinds.split(",")]
    if args.limit:
        counted: dict[str, int] = {}
        chosen = []
        for item in items:
            counted[item.kind] = counted.get(item.kind, 0) + 1
            if counted[item.kind] <= args.limit:
                chosen.append(item)
        items = chosen
    skipped = [i for i in items if i.kind.split(":")[-1] not in OUTPUTS]
    items = [i for i in items if i not in skipped]
    print(f"Replaying {len(items)} requests on {provider}:{model} "
          f"(captured on {baseline[0]}:{baseline[1]})")
    replayer = Replayer(provider, model, args.budget, endpoint)
    done = 0

    def progress(item: Item, result: dict) -> None:
        nonlocal done
        done += 1
        item.result = result
        state = result.get("error") or "ok"
        print(f"  {done}/{len(items)} {item.step} {item.kind}: {state} "
              f"({result.get('elapsed', 0):.0f}s, "
              f"captured {result.get('baseline_elapsed') or 0:.0f}s)")

    try:
        in_parallel(replayer.client, lambda item: replay(replayer, item), items, progress)
    except KeyboardInterrupt:
        print("Stopped; reporting the finished requests.")

    by_kind: dict[str, list[Item]] = {}
    for item in items:
        by_kind.setdefault(item.kind, []).append(item)
    report = {"capture": str(args.capture), "baseline": ":".join(baseline),
              "candidate": args.to, "skipped": [i.kind for i in skipped], "formats": {}}
    for kind, group in by_kind.items():
        ok = [i for i in group if "candidate" in i.result]
        entry = {"requests": len(group), "answered": len(ok),
                 "errors": [i.result.get("error") for i in group if "error" in i.result],
                 "baseline_unreadable": sum(not i.result.get("baseline_valid", True) for i in ok),
                 "median_seconds": statistics.median([i.result["elapsed"] for i in ok])
                 if ok else None,
                 "median_captured_seconds": statistics.median(
                     [i.result["baseline_elapsed"] or 0 for i in ok]) if ok else None}
        name = kind.split(":")[-1]
        if name == "ScoringAnswer":
            entry["comparison"] = compare_scoring(group)
        elif name == "TitleScreen":
            entry["comparison"] = compare_unrelated(group, "T")
        elif name == "QuickPassAnswer":
            entry["comparison"] = compare_unrelated(group, "J")
        elif name == "OnlineAnswer":
            entry["comparison"] = compare_online(group)
        elif name == "ReferenceAnswers":
            entry["comparison"] = compare_cities(group)
        entry["items"] = [{"result": i.result} for i in group]
        report["formats"][kind] = entry
    report["usage"] = costs(items, replayer, baseline)
    show(report)
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str),
                            encoding="utf-8")
        print(f"\nFull report: {args.out}")
    return 0


def show(report: dict) -> None:
    print(f"\n{report['baseline']} (captured) vs {report['candidate']} (replayed)")
    for kind, entry in report["formats"].items():
        print(f"\n== {kind}: {entry['answered']}/{entry['requests']} answered, errors "
              f"{entry['errors'] or 'none'}, median {entry['median_seconds'] or 0:.0f}s "
              f"(captured {entry['median_captured_seconds'] or 0:.0f}s)")
        found = entry.get("comparison")
        if not found:
            continue
        print("   " + ", ".join(f"{key} {value:.2f}" if isinstance(value, float)
                                else f"{key} {value}" for key, value in found.items()
                                if not isinstance(value, list)))
        if kind.endswith("ScoringAnswer"):
            for row in sorted(found["rows"], key=lambda r: -abs(
                    r["candidate"]["score"] - r["baseline"]["score"]))[:15]:
                print(f"   {row['baseline']['score']:3} -> {row['candidate']['score']:3}  "
                      f"{row['title'][:60]} | {'; '.join(row['candidate']['reasons'])[:80]}")
        elif "differences" in found:
            for difference in found["differences"][:40]:
                print(f"   only {difference['left_out_by']} left out: {difference['title'][:80]}")
    usage = report["usage"]
    print(f"\nEstimated cost: captured {usage['baseline_estimate']} "
          f"({'complete' if usage['baseline_estimate_complete'] else 'incomplete'}), "
          f"replay {usage['candidate_estimate']} "
          f"({'complete' if usage['candidate_estimate_complete'] else 'incomplete'})")


if __name__ == "__main__":
    sys.exit(main())
