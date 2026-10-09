# Help when something does not work

Find the problem below and follow its steps. Messages on the Jobcu page or in its text
window often explain what needs attention. Keep keys and personal documents out of chat,
screenshots and public reports.

## Jobcu will not open

Check that you unpacked the ZIP download and are opening the start file from the normal
Jobcu folder. Use **Start Jobcu.command** on Mac or **Start Jobcu.bat** on Windows.

If your computer blocks the file, follow the Mac or Windows instructions in
[Start Jobcu](install-and-start.md#start-jobcu). Only allow a copy you trust. Do not switch
off your computer's security protections. If the suggested option is missing, report what
the warning says and which computer you use.

If the helper **uv** could not be installed, check your internet connection and double-click
the start file again. Wait while it prepares; the first start can take a few minutes.

If the download link is unavailable, use the
[public Jobcu page](https://github.com/UtkuDenizAltiok/jobcu). No GitHub invitation is needed.

## The text window opened, but the Jobcu page did not

1. Leave the text window open. Check whether it is still preparing or showing an error.
2. If preparation has finished, open your web browser.
3. Type `http://127.0.0.1:8765` into the address bar and press Enter or Return.

If the page still cannot be reached, report the error message as described at the end of
this guide. Do not copy the whole text window or a private log into a public report.

## The page says Jobcu's engine is not answering

This usually means the part running in the text window has stopped.

1. Close the Jobcu browser tab.
2. Close any old Jobcu text windows; on Mac, choose **Terminate** if asked.
3. Double-click the start file again and wait for Jobcu to open.

Keep the new text window open while using the app. If an older version could not be closed
automatically, closing its Jobcu text window before restarting also resolves that conflict.

## My AI connection test fails

Open **Settings → AI provider** and read the message under **Test connection**.

- If the key is missing or rejected, click **Replace** beside the saved key, paste the complete
  key from the provider, and click the key's **Save** button. Do not paste it into a help message.
- If the model is unknown, click **Load model list**, choose a model your account can use,
  and click **Save** below the model settings.
- If the message says your allowance or billing access is missing, check that on the provider's
  own website. Jobcu cannot change your account or add credit.
- If a search reports a temporary rate limit, allow Jobcu's retry to run. If the allowance is
  exhausted, check the provider's usage page and when access becomes available again.
- For **Other**, check **Custom API format and reasoning** against the service's instructions.
  Responses, Messages and Chat Completions are different formats. A custom reasoning refusal
  stops the request; choose documented controls rather than expect Jobcu to turn thinking off.
  Old custom settings may report unconfirmed provider-default effort.
- If you configured a separate online research provider, its key/model are independent of the
  main connection. Use **Test research connection** for ordinary generation; actual online
  search access remains a separate capability. Saving settings makes no provider request.

After correcting setup, click **Test connection** again. This can use provider allowance or
paid credit. See [Set up your keys](getting-your-keys.md) for the full setup steps.

## My document will not upload

For a CV, use PDF (`.pdf`) or Word (`.docx`). For a cover letter, you can also use plain text
(`.txt`). The older Word `.doc` format is not accepted. Each file must be no larger than 10 MB.

If Jobcu says it cannot find readable text, the file may be a photograph or scan. Export a
PDF or Word copy directly from the original document editor, then upload that copy. For a
password-protected PDF, use a copy without a password.

When the upload works, your file name appears beside **CV** or **Cover letter**.

## Find matching jobs is unavailable

Look at **Make Jobcu yours** and the message below the search button. You need your AI
setup, a CV and a cover letter. Most AI providers need a saved key and model. Complete the
missing item. If another search is still running, wait for it to finish or click **Stop**
before starting a new one.

If clicking the button asks you to choose a job type, tick at least one box under **Job types**.

## The search seems to have paused

Look below the progress steps for a question about scoring more jobs or looking up more
information. Jobcu waits for your answer. Read the question and choose whether to continue
or **Show results now**. Continuing uses more AI; an **Always** choice also changes future limits.

If there is no question, read the progress notes for retries or a reported problem. You can
click **Stop** to cancel. Starting a new search can use AI again.

## Jobcu says it could not save the search

Keep Jobcu open while you read any results still shown. The latest search or condition changes
may be lost if you close it; reopening Jobcu may show the earlier saved results instead.

Check that your computer has free disk space and that Jobcu can write to its data folder.
If the problem continues, follow [I still need help](#i-still-need-help). A new search uses AI
again and may incur further charges.

## Some details say not checked, or research is unavailable

Your model may answer ordinary AI requests without being able to research the web. A
successful connection test alone does not confirm web access.

Read the explanation in Jobcu and check your model/account's research support with the
provider. Jobcu continues what it can do and labels uncertain details. Read the original job
ad yourself before relying on a missing requirement or a travel estimate.

## I see few or no jobs

1. Click **Search details** to see whether sources were unavailable or a limit reduced the work.
2. Read **Understood as**. If Jobcu misunderstood a place condition, click **Edit** and correct it.
3. If your choices are too narrow, try a wider place, a longer **Posted within** window, or
   more job types. Change the search form and click **Find matching jobs** again.

A new search can use more AI. Jobcu does not cover every job site, so an empty result is not
proof that no suitable jobs exist. Check original ads for jobs with unknown dates or incomplete text.

## Google Maps keeps asking Jobcu to slow down

The retry warning can mean a temporary service problem or an account quota. Paying more does
not solve every cause. Read the final Maps note in **Search details**:

- **Jobcu's monthly route limit:** check **Settings → Usage and limits**. This is Jobcu's
  attempt allowance; changing Google billing alone does not change it.
- **Google daily/monthly/zero quota:** open your project in [Google Cloud](https://console.cloud.google.com/),
  then **Google Maps Platform → Quotas**, select **Routes API** and inspect the exhausted limit.
  Check **DistanceMatrix – ComputeRouteMatrix per-element quota per day** separately from
  its per-minute limit. Jobcu uses this matrix operation; the **ComputeRoutes** quota is
  different. A daily limit can stop one search while a monthly allowance is still available.
- **Temporary or unidentified limit:** check the project's quota/usage page and whether
  billing and **Routes API** access are active. An unidentified message does not establish
  when the limit resets. Keep account identifiers and raw error details private.
- **Key rejected:** check its Routes API permission and the project's billing/access setup.
  Use the [key guide](getting-your-keys.md#optional-google-maps); enter keys only in Jobcu.

Choose any increase from actual usage and current prices, with a spending limit and margin.
A Google budget alert is a notification, not a hard cap. Other projects on the same billing
account can use the same allowance; Jobcu cannot see their use. The dated
[service evidence](../SOURCES.md#maps-spending-and-alternatives) explains the limits.
After correcting the specific problem, test once in Jobcu within your allowance; that test
may use paid credit. You do not need a new full search to test access.

Daily and monthly limits are separate: 9,000 elements over 30 days averages 300/day, while
450/day permits 13,500. Daily headroom can allow a busy search; the app's monthly allowance
still stops later calls when used up. Several sampled destinations can cost several elements
for one workplace. Jobcu already reuses identical requests within a search. A location alone
does not identify a journey: destination, transport mode and departure time matter. It does
not indefinitely reuse yesterday's Google travel time; timetables change and storage terms
restrict that cache. This preserves current evidence rather than promise an unverified saving.

Jobs without checked travel evidence need further checking. Current AI fallback times are
labelled estimates, and a long estimate can still exclude a job; city-edge/centre samples
are also approximate. Extra paid usage alone does not establish that good jobs were retained
or that their scores are accurate.

## The Google Maps test gives an unexpected travel time

**Google Maps works** confirms access to the service. The sample is a public-transport journey
between named stations at the stated departure time; it can include walking and waiting.
It is not a promise about the time spent on a particular train.

For a job's travel condition, check the actual workplace address, destination and departure
time. Jobcu compares a calculated city-edge point and city centre unless you ask for the centre
alone. Other districts can have faster connections; a town-centre origin can also differ from
the workplace. Do not change your key just because a duration is unexpected.

## I still need help

Describe which step failed, the short error message, and whether you use Mac or Windows.
If you work on Jobcu with Codex, use your local project chat. Otherwise contact the person
who gave you Jobcu, or use the repository's **Issues** page for a public software problem.

GitHub issues are public. Use fictional examples and do not include API keys, account details,
CVs, cover letters, search text, job results or raw logs. Crop screenshots to the error itself
only when no private information is visible.
