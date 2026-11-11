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
