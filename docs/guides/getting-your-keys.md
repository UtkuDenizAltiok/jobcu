# Set up your keys

Jobcu uses an AI service to understand your documents and compare them with job ads.
Before searching, you choose that service and give Jobcu permission to use your account
through an **API key**. A key is a secret code made on the service's website.

You do not need a Jobcu account. You do need access to your chosen AI provider, which may
require an account, an allowance or billing setup with that company. Read its current prices
and data-use terms: the necessary text from your documents and search goes to that provider.

Keep your key secret. Paste it only into the matching key box in Jobcu, never into chat,
GitHub or a screenshot. After saving, Jobcu hides it and shows only its ending characters.

## Connect your AI service

**Provider** means the company or service supplying the AI. **Model** means the AI version
you choose from that provider. Jobcu lets you choose both; it does not pick one for you.
Use the provider's descriptions, current prices and your account's access to decide.

1. Open Jobcu and click **Settings** at the top of the page.
2. Under **AI provider**, select your chosen service. The key and model boxes appear below it.
3. If you do not have a key, click **Create one on the provider's website**. This opens its
   website in another tab. Follow that service's instructions to create an API key, and copy
   the complete key. You can also use the links below.
4. Return to the Jobcu tab. Paste the key into **API key** and click the **Save** button beside
   that box. **Saved (ends in …)** confirms that the key is stored. You do not need to enter
   it again every time you open Jobcu.
5. Click **Load model list**. Wait for the message below the Model box, then click inside
   **Model** and choose a model available to your account. If your provider gives you a model
   name instead, type that exact name. Loading the list does not choose a model automatically.
6. Leave **Advanced: a second model for reading documents** closed for a basic setup.
   Click the **Save** button below the model settings. This saves your provider and model
   choice separately from the key you saved in step 4.
7. Click **Test connection** and wait for its message. This sends a small request to the AI
   and can use your allowance or paid credit. If it reports a problem, follow
   [AI connection help](troubleshooting.md#my-ai-connection-test-fails) before searching.

| Provider | Key website or instructions |
|---|---|
| Anthropic | [Claude Console](https://platform.claude.com/settings/keys) |
| Google | [Google AI Studio](https://aistudio.google.com/apikey); [key instructions](https://ai.google.dev/gemini-api/docs/api-key) |
| OpenAI | [OpenAI API keys](https://platform.openai.com/api-keys) |
| Other | Use the instructions from the service you chose. See below. |

A successful connection test means Jobcu can send an ordinary AI request. It does not prove
that the model can research the web. Web research can need different account permissions
and can cost extra. If it is unavailable during a search, Jobcu explains, continues the work
it can do, and labels details it could not check. A later search tries research again.

### If you choose Other

**Other (OpenAI-compatible)** is for a service that supplies a compatible connection, including
some AI services running on your own computer. Use it only when you have that service's setup
details. Enter its **Provider address** and exact **Model** name, and save its key if one is
required. Some local services need no key. This connection does not support Jobcu's web research.

## Control usage and cost

AI services may charge when you test a connection, read documents, search or apply corrected
conditions. Your provider's own usage or billing page is the reference for actual charges.
Allowances and prices can change; check them before enabling paid use.

In Jobcu's **Settings**, scroll to **Usage and limits**. It shows what Jobcu has used.
These terms appear there:

- **Tokens** are small pieces of text the AI reads or writes. Providers often price AI work
  by the number of tokens.
- **Web look-ups** are requests asking the AI to find information online.
- **Jobs scored** are job ads the AI has evaluated against your background.

New installs have no per-search scoring or AI web look-up cap. To choose an optional limit,
enter an amount under **Limits**, then click **Save limits**. Existing saved choices are kept.
Per-search limits control when Jobcu asks whether to do more work. Monthly limits stop
further AI work when Jobcu's recorded usage reaches them. A blank box means **No limit**;
it does not mean zero use or free use.

Prices are optional for searching. For a money estimate, add your model's prices:

1. Under **Prices**, click **Add a model**.
2. In the new row, select your provider and enter the same model name you chose above.
3. Copy that model's current prices from the provider's pricing page. **In, per million** is
   the price for one million tokens sent to the AI; **Out, per million** is the price for one
   million tokens it returns. Enter the matching currency, such as USD or EUR.
4. Click **Save prices**. If you use a second model, add and save its prices too.

The **Monthly cost limit** relies on these entered prices and their currency. Missing or
incorrect prices make that limit unreliable.

Jobcu's estimate can leave out web fees and discounts. It cannot guarantee the provider's
final bill. Use any spending controls your provider offers as well, checking whether they
actually stop spending or only send an alert.

You can now return to **Search** and follow [How to use Jobcu](first-search.md#2-add-your-cv-and-cover-letter).
The extra keys below are optional and can be added later.

## Optional job-site keys

Adzuna and Reed keys let Jobcu include ads from those services. Other available sources
need no user key, so you can try Jobcu before setting these up.

1. For **Adzuna**, [register for API access](https://developer.adzuna.com/signup), then find
   **Application ID** and **Application Key** under **API Access Details**. Give truthful
   information about your intended personal use.
2. In Jobcu, open **Settings → Job site keys (optional)**. Paste each Adzuna value into its
   matching box and click **Save** beside each one. Then click **Test Adzuna**.
3. For **Reed**, [request an API key](https://www.reed.co.uk/developers/jobseeker) and follow
   its instructions. Paste it into Reed's **API key** box, click its **Save** button, then
   click **Test Reed**.

Read the test message to confirm each connection worked. Keep these keys secret too.

## Optional Google Maps

Google Maps can provide travel times when your search includes a travel-time condition.
Without a Maps key, Jobcu uses labelled AI estimates. You can leave this setup until later.

If you want Maps, follow these steps on Google's website and in Jobcu:

1. Open [Google Cloud](https://console.cloud.google.com/), create or select a project, and
   check its current billing requirements and prices.
2. Enable the **Routes API**, which supplies travel-time information.
3. In **APIs & Services → Credentials**, create a key and restrict it to **Routes API**.
4. Set request quotas and budget controls suitable for your limit. A quota limits requests;
   an **alerts-only budget does not stop spending**. Follow Google's
   [budget guidance](https://docs.cloud.google.com/billing/docs/how-to/budgets) and
   [Routes quota and billing guidance](https://developers.google.com/maps/documentation/routes/usage-and-billing).
5. Return to Jobcu. Under **Settings → Travel times (optional)**, paste the key into
   **Google Maps API key**, click **Save** beside it, then click **Test Google Maps**.

A successful message begins **Google Maps works** and describes a sample public-transport
journey from Freising station to Munich Hauptbahnhof, departing next Tuesday at 08:00 local
time. It checks that Jobcu can access the service; it does not prove travel-time accuracy.
The result is a whole journey that can include walking and waiting, rather than time spent
only on a train. Each network attempt for this test counts one route element against Jobcu's
monthly Maps limit; retries also count. A cached response adds no attempt. Google's billing
follows its own rules and the request may incur a charge under your account's terms.

If Maps reports a daily/monthly quota or a zero allowance, check **Routes API → Quotas** in
your Google Cloud project. Jobcu cannot change those account limits. Temporary throttling
can be retried within the app's allowance; an unidentified quota is shown without guessing
its reset time. **Settings → Usage and limits** controls Jobcu's own monthly attempt limit,
which does not replace Google quotas or cover requests made by other apps.
An individual route can fail even when Google answers the request. Jobcu keeps other measured
times and labels unavailable journeys or fallback estimates; it does not turn a service error
into proof that a job is unreachable. The [usage guide](first-search.md#4-start-the-search-and-answer-any-questions)
explains these outcomes.

Maps charges depend on the number of journeys checked, the request features and your billing
account's available allowance. Collected job-ad counts are not a bill. Read the dated
[Maps price and cost-control evidence](../SOURCES.md#maps-spending-and-alternatives) before
enabling paid use or increasing a limit. Jobcu's route limit counts attempts, including retries;
it is not a euro spending cap. Google combines account usage across projects, and its billing
month can differ from Jobcu's local counter. Do not rely on an alerts-only budget to stop charges.

Recurring failures need the specific quota/access cause, not an automatic purchase of a higher
tier. Follow [Maps quota help](troubleshooting.md#google-maps-keeps-asking-jobcu-to-slow-down).
Paying for extra requests can help an exhausted allowance; it cannot guarantee a timetable,
the fastest district connection, accurate AI scores or complete job coverage.

These service references were checked on 2026-10-07. Prices and account access still depend
on the services' current terms. Maps retry/quota handling was rechecked on 2026-10-09;
the dated evidence is in [SOURCES](../SOURCES.md#maps-request-limits-and-recovery).
Next: [How to use Jobcu](first-search.md).
