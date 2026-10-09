# Jobcu

Jobcu finds fresh job ads, ranks their fit to your CV and cover letter, and explains each score.
It runs on your Mac or Windows computer and connects to job sources and your chosen AI provider.
Custom APIs can use Chat Completions, Responses or Messages. An optional separate provider can
handle cited online research while your main AI reads documents and scores jobs; see
[AI setup](docs/guides/getting-your-keys.md#if-you-choose-other).
This is an early test version; live coverage and scoring quality still need measured validation.

Everyday navigation is **Search** and **Settings**. Optional **Settings → Review results** helps
compare scores with independent ratings; it is not required to use Jobcu. To start fresh, use
the [confirmed reset controls](docs/guides/first-search.md#clear-data-and-start-fresh), which keep
your settings, keys and real usage counters.

## Use Jobcu

You do not need programming experience. You use Jobcu through a page in your web browser.
You need an internet connection, your CV, a cover letter, and access to an AI service of your
choice. An **API key** is a secret code from that service which lets Jobcu use your account.
[The setup guide](docs/guides/getting-your-keys.md) explains how to get and enter one.

1. **Open Jobcu.** Open your Jobcu folder and double-click **Start Jobcu.command** on Mac or
   **Start Jobcu.bat** on Windows. A text window opens, followed by the Jobcu page in your
   browser. Keep the text window open: it runs the app. If you do not have the folder yet,
   follow [Install and start](docs/guides/install-and-start.md).
2. **Connect your AI service.** Click **Settings** at the top of the Jobcu page. Choose your
   provider, save its API key, choose a model, and click **Test connection**. A model is the
   version of the AI you want to use. Follow [Set up your keys](docs/guides/getting-your-keys.md)
   for the individual steps and cost controls.
3. **Add your documents.** Click **Search** at the top. Click **Add CV**, choose your CV file,
   then do the same with **Add Cover letter**. Your file names appear when they have been added.
   Jobcu uses these documents to understand your experience and the work you want.
4. **Say where you want to work.** In **Where do you want to work?**, write your preferred
   places and conditions in ordinary words. For example: *Dublin or Cork* or *Germany, within
   50 minutes of a city centre by public transport*.
5. **Choose the age and types of jobs.** **Posted within: 24 hours** means ads posted in the
   previous day and suits a daily search. Tick the job types you want, such as permanent work
   or internships. Wider posting windows are available.
6. **Start the search.** Click **Find matching jobs**. Keep Jobcu open and watch its progress.
   If it asks whether to use more AI, read the question and choose whether to continue.
7. **Read the matches.** Each job has a score and reasons. Click **Open job** to read the
   original advertisement and apply on the employer's or job site's page. **Save** keeps a
   job for later; **Applied** records an application you have already made.
8. **Close Jobcu when finished.** Close the text window that opened in step 1. On Mac,
   choose **Terminate** if asked. Close the browser tab too. Use the same start file next time;
   your saved setup and jobs remain on your computer.

The [first-search guide](docs/guides/first-search.md) walks through these steps in more detail,
including correcting a misunderstood condition and understanding warnings on a job.
If something does not work, follow [Troubleshooting](docs/guides/troubleshooting.md).

## Write your search in your own words

In **Where do you want to work?**, you can describe what matters to you about a place,
including conditions Jobcu asks your AI to research online. For example:

- *Dublin or Cork.*
- *Germany or Ireland, within 50 minutes of a city centre by public transport.*
- *Anywhere in Europe, in a city with at least 0.3% of that country's population.*
- *Exclude cities where far-right parties received a higher share of votes than their
  national share in that country's latest national parliamentary election.*
- *Somewhere with several Turkish supermarkets and shops open on Sunday.*
- *A university town where more than 20% of the population are students.*
- *Within 30 minutes of Munich city centre by public transport.*

You can combine these conditions in one request. For an exact shop count, write something
like *at least three Turkish supermarkets*. The [usage guide](docs/guides/first-search.md#more-detailed-requests)
explains the examples and gives a combined request.
To exclude remote jobs, tick **Don't include remote jobs** on the Search page.

Jobcu searches its supported countries, computes population limits from its included data,
and asks your chosen AI to research facts such as election results and shops where web
research is available. Read **Understood as**, the sources supplied and any **AI estimate**
or **not checked** labels. Unchecked conditions do not exclude jobs. Use **Edit** to correct
a misunderstanding and apply it to the jobs already found.

## Privacy and cost

Your keys, documents, query and results stay outside the source folder and GitHub. A search
sends the necessary text to the AI providers you chose and search words to job sources.
Jobcu has no user accounts, telemetry or cloud storage, and never logs in to job sites.

Provider charges depend on your model, account and search. Prices and limits in Jobcu are
optional controls; new installs have no per-search scoring or AI web-check cap. Jobcu's usage
estimate may omit web fees and discounts; it is not an invoice.

## Project documents

For assistant development, use **Start** once in a local project chat, then **Review** after
a completed search or **Deep improvement** without needing a new search. Both assess coverage
and improve the app. Use **End** before closing the chat; the next chat recovers saved unfinished
work without choosing a new task. Copy the blocks from [PROMPTS](docs/PROMPTS.md).

| You need | Open |
|---|---|
| Copy a session, search-review or improvement prompt | [PROMPTS](docs/PROMPTS.md) |
| See current work and the next action | [PROGRESS](docs/PROGRESS.md) |
| Develop Jobcu with Codex | [CONTRIBUTING](CONTRIBUTING.md) |
| Read the working rules | [AGENTS](AGENTS.md) |
| Find product decisions, code, tools and lessons | [ENGINEERING](docs/ENGINEERING.md) |
| Check source methods, restrictions and evidence | [SOURCES](docs/SOURCES.md) |
| Look up dated background | [Original concept](docs/archive/HANDOVER.md), [decision history](docs/archive/DECISION-HISTORY.md), [source research](docs/archive/SOURCE-RESEARCH.md) |

## Ownership and data credits

The code is publicly readable under the proprietary [LICENSE](LICENSE).
© 2026 Utku Deniz Altiok. All rights reserved.

Town, region and postcode data: © [GeoNames](https://www.geonames.org/),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Belgian job offers: © Le Forem, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
School jobs in England contain public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
