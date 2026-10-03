# Get your keys

A **key** is a long password-like code. It lets Jobcu use a service with your own account, so
the service knows the requests come from you. You need **one**: an **AI key**. Jobcu's AI reads
your CV, understands where you want to work and scores every job.

The free **Adzuna** and **Reed** keys are optional but worth five minutes: Adzuna brings the most
jobs in Germany and the UK, and Reed adds UK jobs. A **Google Maps** key is optional too: it gives
real travel times. Everything else Jobcu searches needs no key.

**Keep keys secret:** never send them to anyone or paste them into a chat. Save each one in your
password manager (or a private note), then paste it into Jobcu's **Settings**.

## AI key: we recommend Google Gemini

Checked on 3 October 2026, **Google Gemini** gives Jobcu the most for the least money. It's the
only one of the big providers with a free allowance, and with billing on it costs about a third
of what the others do, because 5,000 web look-ups a month are included. (Jobcu also works with
Anthropic, OpenAI and others; see the end of this section.)

### Step 1: create a free Gemini key (no card needed)

1. Open [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and sign in with your
   Google account (the one you use for Gmail is fine). Accept Google's terms if asked (Google
   requires you to be 18 or older).
2. Click **Create API key** → choose or create a project → **Create**. Copy the key (it starts
   with `AIza`).
3. In Jobcu: **Settings → AI provider** → choose **Google (Gemini)** → paste the key → **Save**.
4. Click **Load model list**, pick **gemini-3.8-flash** (or a newer model whose name ends in
   **flash**; avoid **pro**, which isn't free and costs much more) → **Save** → **Test
   connection**. You should see that the connection works.

That's enough to search. On the free allowance:

- It costs nothing. Searches are slower, because Google allows only a few requests a minute;
  Jobcu waits by itself ("AI limit reached, continuing more slowly" is normal).
- Google doesn't offer **web look-ups** for free, so three things don't work: facts about
  places that need looking up (for example "cities with a university"), finding extra employers
  for your kind of work, and reading online the full ad of jobs a site shows only as a summary.
  Plain conditions like "Munich or within 40 km" or "a city with at least 100,000 people" still
  work.
- If you live in the EU, the UK or Switzerland, Google's terms say it doesn't use what you send
  on the free allowance to improve its products; elsewhere it may, and people at Google may read
  it. Your CV is part of what's sent.

### Step 2 (recommended): turn on billing with a spending limit

For the best results (web look-ups included) and the fastest searches:

1. In [Google AI Studio](https://aistudio.google.com), open **Billing** → **Set up billing** and
   follow Google's steps (a card; you can buy credit in advance, for example €10).
2. Open **Spend** → **Monthly spend cap** → enter the most you want to pay a month (for example
   **10**) → **Save**. Google pauses your key when it's reached (sometimes a few minutes late),
   so you can't end up paying much more.
3. Nothing changes in Jobcu: the same key now uses the paid tier.

**What it costs** (prices of 3 October 2026, which Google doubles on 1 January 2027): about
**€0.50–2.50 per search**, depending on how many jobs are found and scored. Settings → **Usage
and limits** shows what each search used; add the prices there (input $0.75 and output $3.75
per million tokens for gemini-3.8-flash) and Jobcu shows the cost. Two or three searches a
week usually stay under €10 a month with Jobcu's standard limits.

### Other providers

If you already pay for one, it works too (each search costs roughly three times as much, mostly
because their web look-ups cost extra):

- **Anthropic (Claude):** [platform.claude.com](https://platform.claude.com) → Settings → API keys
  → **Create key**; a low-cost model is **claude-haiku-4-5**.
- **OpenAI:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → **Create new
  secret key**; choose a low-cost **mini** model.
- **Others:** choose "Other (OpenAI-compatible)" and enter the address, key and model from the
  provider's documentation. Web look-ups don't work with these.

Copy a key right away (it's often shown only once). When you add payment details anywhere, set a
monthly spending limit there.

## Adzuna (free)

1. Sign up at [developer.adzuna.com/signup](https://developer.adzuna.com/signup). For the form,
   use e.g. *Personal or academic research*, *N/A* visitors, *Europe*, *Career Services*.
2. Sign in → **API Access Details** → copy the **Application ID** and **Application Key**.

## Reed (free)

1. Go to [reed.co.uk/developers/jobseeker](https://www.reed.co.uk/developers/jobseeker) → **Sign up
   for a reed.co.uk API Key** → fill in name and email → **Register**.
2. Copy the key shown on screen or sent by email.

## Google Maps (optional, for travel times)

Only needed if you write things like *"at most 50 minutes by public transport to a big city"*.
Without it, the AI estimates travel times. Google asks for a card, but gives a free allowance
every month, and Jobcu stops below it.

1. Open [console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate),
   name the project *Jobcu Google Maps* → **Create**. Add a billing account when Google asks.
2. [Budgets & alerts](https://console.cloud.google.com/billing/budgets) → **Create budget** →
   **Alerts only**, name *Jobcu Google Maps*, project *Jobcu Google Maps*, amount **1** →
   **Finish**. Google then emails you if Maps ever costs anything.
3. Open the [Routes API](https://console.cloud.google.com/apis/library/routes.googleapis.com) →
   **Enable**. In Europe, Google first asks you to accept its European terms: type *Confirm* →
   **Accept & continue**. Google then creates a key by itself.
4. [Credentials](https://console.cloud.google.com/apis/credentials) → click the key → name it
   *Jobcu Google Maps key* → under **API restrictions** keep only **Routes API** → **Save**.
5. Daily limit, so Google itself stops before the free allowance: **Google Maps Platform →
   Quotas** → *ComputeRouteMatrix per-element quota per day* → ⋮ → **Edit quota** → untick
   **Unlimited**, type **320** → **Done** → **Submit request** → **Confirm**.
6. Back in **Credentials** → **Show key** → copy it. In Jobcu: **Settings → Travel times** →
   paste the key → **Save** → **Test Google Maps**.

➡️ Next: [Your first search](first-search.md)
