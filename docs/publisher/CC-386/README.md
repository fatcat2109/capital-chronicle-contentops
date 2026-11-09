# CC-386 — source-bound replies and the platform constraint

The reply workflow is installed in `A:\Capital Chronicle\ContentOps` at
`161a12c94702241d4e02830339bb2660577e0134`. The item remains **BLOCKED**: X's
current automation rules prohibit the requested website automation. Its automated
reply rules also require recipient opt-in, an opt-out path and prior explicit
written X approval for AI reply bots. Decision 108 says platform rules come first.
Five replies per day does not exempt the requested route.

No public reply was sent. The required three X replies, three Threads replies,
one debate follow-up and 24-hour measurements are all outstanding. No schedule,
credential, subscription, account setting or other chat was changed.

## Installed workflow

- `scripts/run_sourced_replies.py stage|publish|status` uses the existing production
  store, work items, outbox and `DurablePublicationCoordinator`. A reply has its
  own `reply-*` work item. It is neither an article nor a plan-status post.
- Selection binds the held X-list author, exact target URL/author/provider ID,
  claim, stance, sourced addition, exact retained source bytes/known-at clock,
  authored copy, optional owned/licensed image and actual editorial call metadata.
  This runner makes no model call. Reader copy still uses the approved native roles.
- The existing Threads API publishes the frozen reply. Immediately before a new
  write, its provider target ID must resolve to the bound permalink, author and
  claim. Readback verifies the reply edge, own account, exact text and chosen image.
  Images use the existing hosted-media manifest and the item's own `CC-386/media/`
  folder. Text replies retain an explicit null image.
- The existing store lease reserves attempts against five replies per platform/day
  and one per author/day, using the existing GMT+7 production-day convention.
  Repeat calls retain the same dispatch; UNKNOWN_WRITE stays readback-first.
  Rate-limit/warning results stop the platform lane in the existing outbox.
- Follow-ups require an already confirmed parent and a new point/interaction;
  the daily author cap still applies. No invented debate is counted.
- The existing performance supervisor registers the DAILY observation at 24 hours.
  `status` joins those exact observations back to each reply. The existing audience
  baseline consumes them. Unavailable native profile/follow metrics stay unavailable.
  There is no extra scheduler or measurement store.

## Verified and remaining

[platform-rules.json](platform-rules.json) records the four official policy pages,
retrieval date and source update dates. X Automation was updated April 2026;
X Authenticity April 2025; Threads Terms 28 May 2025. The Meta Spam page's dynamic
change log does not expose a stable newer effective date.

[threads-target-lookup.json](threads-target-lookup.json) records the actual official
Threads keyword-search failure: HTTP 403, provider code 10, application lacks
permission. This proves a discovery limitation, not denial of posting permission.
The verified Peter Schiff profile and a substantive thread are retained in
[target-research.json](target-research.json); no provider target ID or publication
was invented. A broader Threads Neo publishing fallback has not been built here;
the chosen API path reuses the current write owner and enforces exact target identity.

[reply-tests.xml](reply-tests.xml): 28 targeted tests passed, covering the reply
consumer, production-feed configuration, exact target/copy, repeat suppression,
uncertain-write recovery, daily/author caps, warnings, provider target identity,
parent reply edge, optional hosted image, existing Threads adapter and CC-359
corrections. The supervisor test proves that confirmed replies reach its existing
DAILY observation path. [coordinator-tests.xml](coordinator-tests.xml) contains the
additional focused canonical-coordinator regressions.

New modules and changed coordinator/quality files pass Ruff. The two older shared
transport modules retain seven pre-existing lint findings, reproduced from the
operating base in [baseline-lint.json](baseline-lint.json). No unrelated lint repair
is included. Git whitespace checks pass.

[live-consumer.json](live-consumer.json) verifies installed file hashes and an
actual installed `status` call against the production store: zero reply work items.
This is installed-consumer evidence, not live posting or audience-response evidence.
The branch starts at fresh remote master and fast-forwards to the operating root's
current accepted HEAD, preserving the newer CC-359/CC-382 consumers. Existing dirty
telemetry, duplicate-ledger and operating-root evidence files remain uncommitted.

The launch arguments read back as `gpt-6.1-sol/high`, **CONFIGURED_NOT_OBSERVED**;
actual runtime model/effort telemetry is unavailable. See [launch-config.json](launch-config.json).

Next owner action: Ops Product establishes a compliant X API/opt-in/AI-approval
route and obtains the Threads application's discovery access, or completes a
compliant Threads browser reply route. Then resume this branch and the same stored
reply identities, publish only thread-specific native-authored arguments, and
collect actual debate and 24-hour responses. No request, post or grant was sent
on Ops Product's behalf.
