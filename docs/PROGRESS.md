# Jobcu progress

Current state and recovery only. Rules: [AGENTS](../AGENTS.md); reusable actions:
[PROMPTS](PROMPTS.md); decisions and implementation: [ENGINEERING](ENGINEERING.md).
Completed details live in Git and PRs. Private evaluation follows
[CONTRIBUTING](../CONTRIBUTING.md#review-a-completed-search).

## Right now

*Updated 2026-10-08. Engineering checks use fictional data.*

### State

- [PR #81](https://github.com/UtkuDenizAltiok/jobcu/pull/81) is implemented, tested, pushed
  and merged with a merge commit. Implementation head: `46f9bd9`; merge: `e223222`.
  Exact-head PR Mac/Windows/privacy CI passed and the Mac checkout was synchronized.
  Merged-main run `37838571490` also passed Mac, Windows and privacy checks at `e223222`.
- Maps counts attempted elements for every retry, checks allowance before waits and commits
  spending atomically. Known daily/monthly/zero quotas stop immediately; temporary/unidentified
  failures retain bounded recovery. Successful cached/earlier measurements survive later
  failures. Both measurement rounds share one meter. Missing routes after request-level
  failures remain labelled estimates/unchecked within the existing AI limits.
- Maps wait details update the current step and preserve its timer; a single note replaces
  repeated wait-length warnings. Logs contain code/quota scope, without raw account-specific
  provider messages. The first progress count now explicitly says ads collected before
  matching and duplicate removal. Existing snapshots/messages remain unchanged.
- Local checks passed: **855 tests**, Ruff, privacy, whitespace and isolated startup self-test.
  The 36 added fictional cases verify quota formats, recovery, allowance/cancellation/cache
  behavior, concurrent budgets, profession-independent labels and progress timing. Primary
  evidence lives in [SOURCES](SOURCES.md#maps-request-limits-and-recovery); controlled before/
  after waits/elements and limits live in [ENGINEERING](ENGINEERING.md#maps-recovery).
  No live accuracy, recall, cost or end-to-end speed improvement is claimed. Existing
  deprecation warning remains. AI medium/provider choice, scoring and JavaScript are unchanged.
- The owner requested saved-search review. Latest completed results, original-run timings,
  source/count/date evidence and Maps logs were inspected on a read-only private backup.
  Detailed findings, snapshot/pool evidence and review status were saved outside Git; scratch
  was deleted. New early-title evidence is available, but blind top-card judgements and
  independent original posting dates/coverage still limit claims. Saved Maps diagnostics do
  not identify the quota period; no Google account/billing settings were changed.
- No new search, paid test or provider/Maps/vacancy request was made by this session. Owner
  data, ratings and authorization are preserved. The owner closed Jobcu during work; both
  app ports are stopped. Development can proceed while it is open, preserving owner state.

### In progress

The Maps implementation is merged. If this record remains on `codex/maps-recovery-handover`
(base `e223222`), only publication/final verification remains. Local end checks passed
**855 tests**, Ruff, privacy and whitespace; startup self-test passed and stopped. No failed
check remains. Exact next action: publish/recover this branch's PR, verify its exact-head
Mac/Windows/privacy CI, merge with a merge commit,
synchronize main and verify final-main CI. A pushed/merged change is not a passed check.

After completed handover publication, no unfinished feature remains. In a fresh chat, run
AGENTS' start routine and recheck private authority/checkpoint. Read the latest private
`saved_evidence_resume` entry/evidence directory; older review fields describe earlier searches.
Independent originals/labels remain a dependency; new early-title evidence is preserved.
Checkpoint that dependency before the next free goal: reproduce partial matrix service errors
being treated as no route, preserve successful samples and keep uncertain jobs, with fictional
engineering and non-engineering cases. Keep one active goal. No new paid test or search is granted.

### Verify before relying on

- Ranking/title screening: independent full-ad judgement, every top-10 label and new early
  rejection/unknown evidence remain unfinished; old counts cannot reconstruct discarded titles.
- Coverage: an independent date-verified 15–25-job benchmark remains, in AGENTS' country order.
- Interpretation/location: live quality, timing and repeated-search savings remain unmeasured;
  Maps journeys and faster districts need live validation.
- Beginner installation and fresh Windows install/upload/search walkthroughs remain untested.

### Waiting on the owner

- No new keys, documents or settings are required; enter private inputs only in Jobcu.
- Search on demand: double-click **Start Jobcu.command**, choose **24 hours**, then search
  when ready. After completion, use [Review](PROMPTS.md#review-a-search).
- With spare assistant usage/time, copy [Deep improvement](PROMPTS.md#deep-improvement).
  Before closing a chat, use [End](PROMPTS.md#end-a-session), wait for the saved confirmation,
  then use [Start](PROMPTS.md#start-a-session) in a fresh local chat.
- Report an unusable route with **Application link problem**; **Excluded links** can undo it.
  This uses no AI allowance. Searches run on demand without assistant supervision.

### Next tasks

1. Reproduce per-element Maps errors versus confirmed no-route outcomes; preserve partial
   valid measurements and retain uncertain jobs before changing filtering. This is the next
   free goal. [Research leads](ENGINEERING.md#research-leads-requiring-their-own-verified-goal)
   also cover newly revealed workplace evidence and unresolved-place rejection.
2. Audit original-date provenance source by source, including modification-time fallbacks.
   Use primary contracts and independent dates; keep uncertain evidence labelled. Do not tune
   collection to a smaller raw count or call saved metadata independent freshness proof.
3. Independently judge full evidence/early titles and trace a date-verified coverage sample
   within private authority. Follow the updated private checkpoint and country work order.
4. Review slower online/interpretation work on saved evidence; paired live timing/ranking work
   needs its own bounded authority. Other-source retry accounting remains a separate audit.
5. Fresh Windows installation/upload/search walkthrough remains later free engineering work;
   launcher CI is not a beginner's installation or live-search validation.

### Known limitations

- Counts do not measure market recall; scores are not hiring odds. Summaries, unknown dates
  and unchecked conditions are incomplete evidence. Historical snapshots keep original labels.
- Opaque application destinations and automatic final-host checks are unverified. A changed
  redirect needs a new report; undo restores retained links, while an omitted vacancy may need
  the next on-demand search. An alternative link does not prove registration access.
- Maps edge/centre samples are approximate. Correction timings cover the latest correction;
  usage accumulates. Token estimates can omit fees/discounts and are not invoices.
- A failed final save can lose visible results on closing; earlier saved searches remain.
