# Set up your keys

A key lets Jobcu use a service through your account. Keep it secret: enter it in Jobcu's
**Settings**, never in chat, GitHub or a screenshot. Your chosen AI receives text from your
documents and search; check its data-use terms before choosing it.

## AI setup

Choose the provider and model you want. Jobcu does not choose one for you.

| Provider | Create or manage an API key |
|---|---|
| Anthropic | [Claude Console](https://platform.claude.com/settings/keys) |
| Google | [Google AI Studio](https://aistudio.google.com/apikey); [current key instructions](https://ai.google.dev/gemini-api/docs/api-key) |
| OpenAI | [OpenAI API keys](https://platform.openai.com/api-keys) |
| Other | Follow that provider's instructions for its OpenAI-compatible address, model and key, if required. |

1. Create a key in your chosen provider's account, following its current instructions.
2. In **Settings → AI provider**, select the provider, enter the key and **Save**.
3. Click **Load model list**, choose a model, save it and **Test connection**.
4. For **Other (OpenAI-compatible)**, enter its address and model; some local services need no key.

A connection test checks ordinary generation. Web research may need different model/account
permissions and may cost extra; it is unavailable with the generic compatible adapter.
If research is refused, Jobcu explains and carries on with job sources/scoring, leaving
unchecked conditions and summary warnings visible. A later search tries again.

## Cost and limits

Use your provider's current pricing and account limits. Free allowances, web fees and privacy
terms vary; no fixed per-search price or runtime is promised here. Before enabling billing,
check which controls actually stop spending and which only alert you.

In **Settings → Usage and limits**, enter model token prices and set monthly/search limits.
Jobcu's estimate can omit web fees and discounts; compare it with the provider's own usage page.

## Optional job-source keys

- **Adzuna:** [register for API access](https://developer.adzuna.com/signup), then copy the
  Application ID and Application Key from **API Access Details**. Use truthful personal-use details.
- **Reed:** [request an API key](https://www.reed.co.uk/developers/jobseeker) and follow its instructions.

Enter them in **Settings → Job site keys**, save and test. Most sources need no user key.

## Optional Google Maps

Without Maps, Jobcu uses labelled AI travel estimates. To use Maps:

1. Create/select a project in [Google Cloud](https://console.cloud.google.com/), check current
   billing terms, and enable the **Routes API**.
2. Create a key in **APIs & Services → Credentials** and restrict it to **Routes API**.
3. Set request quotas and budget controls suitable for your limit. An **alerts-only budget does
   not stop spending**; follow Google's [budget guidance](https://docs.cloud.google.com/billing/docs/how-to/budgets)
   and [Routes quota/billing guidance](https://developers.google.com/maps/documentation/routes/usage-and-billing).
4. Enter the key in **Settings → Travel times**, **Save**, then **Test Google Maps**.

These key/budget references were checked on 2026-10-07. Prices and account access still depend
on the services' current terms. Next: [Your first search](first-search.md).
