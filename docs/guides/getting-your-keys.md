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

**Other (OpenAI-compatible)** accepts three common API formats, including compatible services
running on your computer. It is not limited to Gemini or one subscription. Get the address,
model ID, supported format and thinking controls from the service's current instructions.

1. Choose **Other**, enter **Provider address**, and save its key if required. Use the base
   address, without the final `/chat/completions`, `/responses` or `/messages`. Use HTTPS for
   remote services; local services may use their documented local HTTP address.
2. Open **Custom API format and reasoning**. Select **Chat Completions**, **Responses** or
   **Messages** as documented. A Messages base can include `/v1`; Jobcu avoids duplicating it.
3. For Chat Completions, choose the documented **Reasoning control**. **Send the selected
   effort** sends medium by default. **Enable thinking** sends an enabled-thinking request,
   with depth controlled by the provider. **Provider default** makes no effort request and
   reports that effort is unconfirmed; older saved custom configurations keep this behavior.
   If the service lacks medium, its **Native value for medium** can explicitly be high/max.
   These mappings are disclosed; they do not prove equal reasoning or quality.
4. Enter the exact **Model**, **Save**, then **Test connection**. A rejected custom thinking
   control stops the request; Jobcu does not quietly switch it off. Check the selected format
   and controls rather than replace the key blindly. Some models lack required structured
   output even when their service supports this API format.

Custom API formats do not automatically include online research. Use the separate option
below to preserve it. A connection test does not prove matching accuracy, research access,
permission for this use or subscription capacity.

### Use a separate provider for online research

Optional: keep a provider with cited web search while using a different main API for document
reading and scoring. Existing one-provider setups continue to work without this option.

1. Open **Optional: a separate provider for online research** under the main AI settings.
2. Choose **Online research provider**. Leave **Same as main AI** for the existing behavior.
   A separate provider must be one of the supported native Anthropic, Google or OpenAI options.
3. Enter its exact **Online research model** and save its **Research provider API key**.
   If that provider's key is already saved, the same masked key is used. Enter it only in Jobcu.
4. Click the main **Save** button. **Test research connection** checks that model's ordinary
   generation and may cost a small amount; it does not make a web search or prove tool access.
5. During searches, online research uses that provider; subsequent structured extraction still
   uses the main AI. Necessary text goes to the relevant chosen providers. Both appear in
   usage and share Jobcu's limits; their service charges/allowances remain separate. When
   research is refused, Jobcu labels uncertainty rather than silently switch to another API.

### Recommended setup now

**Recommendation checked 2026-10-09:** keep your working **Google → Gemini 3.8 Flash** setup
at **Medium** while the assistant evaluates **GPT-6 Luna at medium** for lower running cost.
Keep Google Maps for measured journeys. Your agreed total ceiling is **EUR30/month**; it is
not a promised bill or an implemented account-wide cap. The
[decision and comparison](../ENGINEERING.md#practical-service-choice--2026-10-09) explain why.

Leave the working settings as they are for now. Go's models are not shown to be worse.
The assistant will compare Go with buying the same model's API directly; a fixed subscription
can cost more at low usage. Keeping Gemini only for necessary web research is a promising
option now supported by Jobcu. The assistant must still compare quality before switching.
You do not need to choose among models or run a new search for this decision.

Before buying Go only for Jobcu, its provider must clarify personal job-matching use outside a
coding agent. If seeking that clarification yourself, use this non-private question:

> Does Go permit a local personal job-search app to use its API for document interpretation
> and JSON job matching, with an honest app user agent and stable session header?

No message has been sent for you. A subscription or successful connection alone cannot prove
matching accuracy or available web research. Keep Go **Use balance** off if you later choose
it; otherwise reaching its included limit can trigger extra charges.

For recurring Maps refusals:

1. Open [Google Cloud's Routes quotas page](https://console.cloud.google.com/apis/api/routes.googleapis.com/quotas).
   Select the existing project whose Maps key you saved in Jobcu.
2. Find **Compute Route Matrix** quotas and current usage. Check the element-per-minute quota
   and any daily restrictions. Check that this project's billing is enabled and **Routes API**
   is enabled. Compute Routes is a different API operation; changing its quota may not help.
3. Resolve the specific refused quota or access setting before raising Jobcu's monthly Maps
   limit. Keep the existing key and saved settings unless the diagnosis requires a change.
   Google's documented standard rate is 3,000 matrix elements per minute, but a project can
   have different limits; this is not an instruction to request an arbitrary increase.
4. Check **Billing → Reports** for the Routes SKU and **Billing → Credits** for any eligible
   Cloud credit. AI Studio's Gemini balance cannot pay this bill. Keep spending within the
   agreed total; a budget alert alone cannot enforce it.

The assistant handles interpretation and application work. The owner handles required account
and payment steps, and enters secrets only in Jobcu. Keep account details out of shared
screenshots and GitHub. The [Maps troubleshooting guide](troubleshooting.md#google-maps-keeps-asking-jobcu-to-slow-down)
explains quota messages and uncertainty. Changing billing alone cannot prove better scores.

### Considering OpenCode Go

The current operational recommendation is **keep Gemini while evaluating a cheaper main API**.
MiMo-V2.6-Pro, DeepSeek V4.1 Flash and GLM-5.3 are also serious candidates. The
[complete assessment](../ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09) explains their
test priority and limits. Gemini has not been proved better at matching jobs; working today,
lower prices and coding benchmarks are different evidence from accurate job understanding.
Research checked on **2026-10-09** prioritizes GPT-6 Luna, MiMo-V2.6-Pro, DeepSeek V4.1 Flash,
Haiku 5.5 and GLM-5.3-Flash. This is a comparison order, not proven superiority. Read the
[decision and workload examples](../ENGINEERING.md#complete-catalogue-and-universal-api-decision--2026-10-09) and
[dated service evidence](../SOURCES.md#opencode-go-and-ai-credit-eligibility) before buying Go
solely for Jobcu or replacing your current setup.

Go advertises a dollar-priced subscription for coding clients. Confirm it permits personal
job matching and document processing through Jobcu. Its model allowances share capacity, and
advertised request counts are estimates for coding conversations. One daily search with a
24-hour posting window can still involve many long requests. Additional balance use can cost
extra; a subscription is not unlimited API access.

Models use different published API formats. Jobcu's **Other** option now accepts these formats,
with explicit thinking controls and a separate online-research option. Configure from the
service's documented format; compatibility still needs verification. Keep your working provider
while quality and permission are checked. Do not enter a Go key in Jobcu's native **OpenAI**
or **Anthropic** key boxes: those connect to the named providers, not to Go. Never send a key
through chat. No paid Go test or automatic provider switch was performed.

After permitted use and quality are established, the documented Go base is
`https://opencode.ai/zen/go/v1`, entered under **Other**. GPT-6 Luna uses **Responses**, Haiku
5.5 **Messages**, and the MiMo/DeepSeek/GLM candidates **Chat Completions**. Model IDs and
current allowances are in the linked service evidence. MiMo's enabled-thinking control differs
from a literal medium effort; DeepSeek/GLM native mappings need host verification. This is
configuration guidance, not permission to send private data or an instruction to buy Go.

For Jobcu alone, also compare a model's direct API with the subscription: it may avoid a fixed
fee and integration work. Include web-tool charges and your actual workload; a token-only price
is not the full search bill. The dated decision above compares that option without changing
your chosen provider or claiming that a different model has better matching accuracy.

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
A configured **Compute Route Matrix daily** cap can stop one search even when Jobcu's monthly
allowance remains. It differs from the per-minute rate and the **Compute Routes** operation.
Adjust only the diagnosed limit using actual usage and the agreed budget. A higher daily
limit does not enlarge Jobcu's monthly allowance, guarantee free use, or improve route accuracy.
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

**AI Studio prepaid credit is for the Gemini API, not Google Maps.** Separately issued Cloud
promotional credit can have different eligibility and an expiry date; check the actual credit
grant. Do not assume that stopping Gemini moves its balance to Maps. The
[credit evidence](../SOURCES.md#opencode-go-and-ai-credit-eligibility) was checked on 2026-10-09.

These service references were checked on 2026-10-07. Prices and account access still depend
on the services' current terms. Maps retry/quota handling was rechecked on 2026-10-09;
the dated evidence is in [SOURCES](../SOURCES.md#maps-request-limits-and-recovery).
Next: [How to use Jobcu](first-search.md).
