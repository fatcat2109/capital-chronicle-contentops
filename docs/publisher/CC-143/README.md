# CC-143 â€” web-first articles and daily email digest

Base: f7169bc049e48378de83c7032bae30ac855dd9f6 (current operating root when claimed).
Branch: backlog/cc-143-web-first-digest.
Launch readback: gpt-6.1-sol / high, CONFIGURED_NOT_OBSERVED.
No editorial model was invoked in this engineering run.

New ordinary Substack intents select WEB_ONLY. Only an exact frozen daily-digest
packet in the existing outbox selects DAILY_EMAIL_DIGEST. Issued historical
intents and request hashes remain unchanged. An uncertain delivery-mode return
is UNKNOWN_WRITE and never permission to retry.

The existing supervisor tick prepares the digest after the 19:00 GMT+7 cutoff.
It copies only confirmed public-feed titles and canonical links; it creates no
new analysis, source facts, scheduler, email service or publication owner.
Undispatched/unsent packets retain their exact contents and operation across
restarts/days. Later eligible articles are selected once in the next packet.
The existing NativeNeoExecutor and DurablePublicationCoordinator perform the
actual identity, send, readback and recovery steps.

Operator commands use scripts/run_native_desktop_editorial.py with the applied
--rollout: digest, digest-resume, digest-tool-begin and digest-tool-submit.
The latter three require the actual --native-invocation-id; begin/submit use
--request-sha256 and submit takes the exact observed --response.
Decision 54 supersedes the older code-timeout/other-tab instructions: preserve
the dedicated draft and untouched Gmail tab, wait on the code screen, never
read a mailbox or enter a code. No new calendar or chat message is used.

Read-only Neo observation, 4 November 2026 about 05:16 GMT+7: Published lists four
posts. Midterm post 223293057 has Recipients 4 and Open rate 25%. This does not
prove web-only delivery. No post or digest was created/sent by this observation.
The existing live sealed feed has three records (oil, FOMC and CPI); midterm is
not yet in that feed. Missing records are not inferred or fabricated.

Validation: digest-tests.xml (13 focused tests); publication-tests.xml (149
publication/native-executor/latency checks); digest-consumer-tests.xml (57
checks after email-proof and host-consumer changes; selections overlap).
CLI help and Python syntax checks pass. The retained-feed preview is prepared
in an isolated temporary store and copies two actual sealed-feed articles;
retained-feed-preview.json preserves their hashes and the no-write scope. These isolated
fixtures do not prove a live web-only post, digest email, account or process reload.

Live operating-root integration and the two real Substack acceptance readbacks
remain required. The active task explicitly leaves live integration to Ops;
no DONE claim is made from a branch delivery.

Final continuation checks: native-loop-tests.xml has 15 passing isolated checks.
It exercises the actual native identity -> publish -> dashboard readback protocol,
requires exact account/object/URL email proof, and resumes without another send.
The actual supervisor tick prepares one packet at 19:00 and repeats it idempotently,
without invoking an editorial cycle or a browser. A web-only confirmation leaves
WEB_CONFIRMED_EMAIL_READBACK_REQUIRED until the dashboard confirms the email send.

The tick prepares native work; it cannot invoke BrowserOS MCP from a background
Python process. The existing Publisher runner/conversation must consume the
prepared digest through digest-resume. Exact 19:00 email dispatch is NOT proven
or claimed. No additional timer, automation or schedule was created to hide that
remaining operating dependency. Persistent processes have not reloaded this code.

Next action belongs to Ops: review/integrate the pushed branch, wire the existing
Publisher consumer to the due digest continuation, and collect a real web-only
article readback plus the digest's sent-email dashboard readback. Preserve every
existing draft/code tab and UNKNOWN_WRITE; no replacement post or draft is allowed.
