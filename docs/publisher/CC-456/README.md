# CC-456: official API replies to mentions

Decision 122 extends the existing CC-386 sourced-reply owner and CC-455 native
reply pack. The sole DurablePublicationCoordinator retains dispatch, identity,
KILL_SWITCH, exactly-once and readback ownership. General X articles keep their
existing route. Browser replies remain parked.

The official OAuth 1.0a adapter reads named keys only through secret_store_v1.
Missing keys stop the first real request boundary with X_API_KEYS_NOT_SET,
without a network request or charge, while retaining Jim's CC-455 pack.
Native drafts use the same public desk/frozen-call source checks and preserve
actual versus configured model telemetry. Model and effort labels do not gate.

A target must have an API-bound mention entity or a verified quote of our
account. The adapter re-reads it before sending and verifies the returned own
reply's author, exact copy and reply parent. Lost responses remain readback-first;
a bounded own-post read can recover an exact reply but cannot prove absence.
Opt-outs, Jim's observed manual replies and the daily prepaid cap prevent fresh
sends. The cap reserves an undiscounted upper bound before each request, retains
uncertain costs, and records published-rate estimates separately from an invoice.
X's prior written approval for AI replies is an external platform requirement.
The Automated profile label remains unchanged under decision 122.

Initial validation: responder-tests.xml has 21 passes; reply-regressions.xml has
54 passes across CC-386, CC-455 and CC-456. Ruff passes for all changed Python.
These use isolated stores and a controlled HTTP server function, not X accounts.
Installation and the real no-key acceptance are recorded after the final check.
No schedule, browser write, account setup, payment or application restart is part
of this run. Branch base and preserved dirty files are in run-context.json.

The final adapter caches its verified account identity for one UTC day, bound to
the same credentials with a one-way HMAC. Every write refreshes identity again.
This removes an otherwise unnecessary paid user read on each empty poll. The
current manual pack also drops an API interaction once its dispatch is confirmed
or uncertain; the historical pack and exact outbox bytes stay preserved. A later
external approval reference can resume an existing frozen draft without changing
its copy or model labels. Each API request's cost record names the poll/reply
scope and its returned resource count, with no headers or key values.

[SETUP.md](SETUP.md) prepares Jim's developer use-case text, prepaid purchase and
hidden-input Credential Manager command. The console actually showed developer
onboarding; the reviewed public pricing page gives no purchase minimum. USD 1 is
a proposed starting credit, not a claimed checkout price. At zero mentions,
96 empty polls/day return no charged posts; the conservative daily identity
check adds USD 0.30 over 30 days. No schedule was created or changed.

The final recovery check retains pending API rows even after their manual buttons
are removed or their draft window expires. Only a new send checks draft freshness;
readback remains available for the original target and text. The scoped request
costs travel in the run record with the exact reply key.

The three-file reply regression ran 62 cases: 61 passed, and the KILL_SWITCH
case initially assumed a per-destination result even when the coordinator's
existing recovery guard stops earlier. The actual provider was never called.
The corrected case checks both that early refusal and the final adapter boundary;
kill-switch-final.xml records its pass. The original test result remains retained.

The canonical coordinator file passed 111 tests in one serial pytest process
(coordinator-regression.xml). Its coordinator source stayed unchanged during
that run. The final reply-only rerun covers the API recovery extension and
budget contention alongside both existing reply paths. A budget reservation held
by another request returns X_API_BUDGET_BUSY before a network call; it does not
turn a local reservation failure into an unknown public write.

Final result: final-reply-regressions-v2.xml has 63 passes with zero failures,
and coordinator-regression.xml has 111 passes. All 174 targeted cases passed.
Ruff and the explicit-path whitespace check pass. validation.json binds the
source hashes and retains the earlier assertion failure and its correction.
