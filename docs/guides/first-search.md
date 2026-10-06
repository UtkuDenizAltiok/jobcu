# Your first search

The default **72-hour** window looks for jobs posted during the previous three days.
It describes the age of the ads, not how long the search runs. Your saved window stays selected.

## 1. Settings

1. The Search page shows **Make Jobcu yours**: your AI, CV and cover letter, with a count of
   what is ready. Click **Set up AI** to open Settings; **Add CV** and **Add Cover letter**
   open the document picker directly. You can complete these in any order.
2. **AI provider:** if you followed [Get your keys](getting-your-keys.md), this is done. Otherwise
   choose your provider, paste your key → **Save**, click **Load model list** and pick a model
   (for Google Gemini: **gemini-3.8-flash**), then **Test connection**.
3. **Job site keys (optional):** paste your Adzuna and Reed keys → **Save** → **Test**. Most of
   Jobcu's job sites and company career pages need no key.

Keys are saved only on your computer.

When Google refuses web look-ups for your model or API project, Jobcu explains once and skips
further online research in that search. It still reads job sources and scores the ads.
Conditions needing web research say **not checked**; extra employers and summary-only ads
cannot be researched online. Check your model's support and the project's billing in Google AI
Studio, or choose another model/provider. A new search tries again after you make a change.

## 2. Your documents

On **Search**, add your **CV** and a **cover letter** (PDF, Word or text). A general cover letter
saying what work you want works best. **What Jobcu understood** shows how your documents were read.

**Anything your documents don't say** (optional): for example your citizenship, or a newer
language level. Jobcu only uses it to judge ads that ask for a citizenship, a security clearance
or a language level. Without your citizenship, Jobcu never assumes one.

## 3. Search

1. **Where do you want to work?** Write it your way, e.g. *Dublin or Cork*, *Munich or within 50 km*,
   or with conditions such as *Germany, only towns with at least 100,000 people* or *at most 50
   minutes by public transport to a big city*. Jobcu checks conditions itself or looks them up on
   the web. Travel times come from Google Maps if you added a key, otherwise they're AI estimates.
   They go to the nearest part of a town, since you could live anywhere in it; write *city
   centre* if you mean the centre.
2. Choose **Posted within** (72 hours or 1 week finds more) and the **job types**.
3. Click **Find matching jobs** (available when all three setup items are ready). It takes 5 to
   30 minutes: longer for several countries, 72 hours or more,
   and on a free AI allowance. You can do other things meanwhile; keep Jobcu's small window open.
   The screen shows each step as it goes, and how many jobs it has checked so far.
   Every two weeks your AI also looks for employers who hire for your kind of work; Jobcu then
   reads their own job lists in every search. **Search details** names the ones it found.
4. If a search reaches a limit from Settings (how many jobs to score, how many web look-ups),
   it asks before doing more. **Always** does it now and in every later search: the limit in
   Settings becomes **No limit** (your monthly limit still holds), and you can type a number
   there again.

## 4. Results

- **Score (0–100):** how well a job fits you, with short reasons. Under them, the card shows how
  the score adds up: role & skills (up to 40), seniority (20), languages (15), requirements (15)
  and location & wishes (10). That's why two jobs can differ by a single point.
- **"Limited to …":** a clear blocker keeps a job's score low, whatever the rest adds up to:
  - a language asked at two or more levels above yours (for example German B2 when you have A2):
    at most 65, and 0 for languages. "Good" or "very good" counts as B2, "fluent" as C1;
  - a citizenship or security clearance you definitely can't get: at most 30;
  - a required PhD you don't have: at most 50;
  - 3 or 4 years of experience beyond yours: at most 80; 5 or more: at most 75; 8 or more: at
    most 60;
  - work that fits yours only partly: a related job whose daily tasks are partly different, at
    most 60; only loosely related, at most 45; another field, at most 30;
  - a requirement you clearly don't meet (for example a placement only for students, or a
    licence you don't have): at most 55.

  An ad written in a language you speak below B2 that doesn't say what level it needs scores low
  for languages, but isn't limited. Jobs with a low score still stay in your list.
- **New:** not seen in an earlier search.
- **"apply by 8 October":** the closing date, when the job site gives one ("closes soon" in the
  last two days). Jobs whose closing date has passed are left out.
- **"first seen by Jobcu on 14 August":** the ad says it's new, but Jobcu showed you this job
  before that date, so it's probably an old ad posted again. If Jobcu showed it before your
  **Posted within** time began, or the employer's own site shows it as older, the job is left
  out as **posted again** (Search details counts these).
- **Understood as:** how Jobcu read where you want to work. If something is wrong, click **Edit**
  to switch a condition off, fix its list of places or its town size, reword it or add one. In a
  list of places, **All of Saxony** means a whole state, county or district, and **Except
  Leipzig** a town inside it that is the other way. Your changes are applied to the jobs already
  found, without searching again.
- **Left out by your conditions** (at the bottom) lists the jobs a condition ruled out.
- **"(from the ad text)"** or **"(found online)"** after a town: the job site didn't say where the
  job is, so Jobcu read the town from the ad, or your AI found the ad online (for the best jobs).
  If no town can be found, the card says so and the job stays in your list.
- **"Scored from a short summary of the ad"**: the job site gives only the start of the ad (Adzuna
  always does). For every such job that could make your list, your AI looks the full ad up online
  and applies the rules above to it; the card then says **"Languages and experience read from the
  full ad online"**.
- **Open job** opens the ad. **Save**, **Applied** and **Not interested** keep your list tidy;
  "Not interested" hides a job for good (**Show hidden** undoes it).
- **Search details:** which sites were searched, why some jobs were left out, and time spent in
  each step, including time waiting for your answers.
- **"Only part of this lengthy ad was read for scoring"**: check the original ad for requirements
  that may be outside the part Jobcu scored.

## 5. Keeping an eye on cost

**Settings → Usage and limits** shows what Jobcu used this month and in your last search. Add
what your provider charges per million tokens and Jobcu estimates the cost. You can set a monthly
limit, how many jobs are scored and how many web look-ups your AI may do in one search before
Jobcu asks whether to do more (leave a box empty for no limit), and switch off any job source
you don't want searched.

## 6. Feedback

**Score check** saves a small sample of jobs and titles from your searches. Read the ad and give
your own judgement before Jobcu reveals its score. Samples saved only as short summaries are
labelled: open the original ad before rating because requirements may be missing. Your ratings
stay in your private data folder.

Tell Utku: do the top jobs fit you? Is any score clearly wrong? Was anything confusing?
