# CC-172 continuation — 5 November 2026

The Publisher operating root now accepts the first exact site readback before a
social dispatch exists. Previously `NativeReviewedPublication.tool` demanded an
existing dispatch for every READBACK, including the site prerequisite. Its own
first site request therefore failed with `NATIVE_NEO_EXACT_EXISTING_READBACK_REQUIRED`.
The site request now binds to the reviewed plan, article identity, public-copy
hash and expected URL. Wrong-plan, wrong-copy and wrong-URL requests still fail.

The approved-text short path also consumes saved writer model/effort telemetry
without validating those labels again at publication. Dispatch still requests
Jim's assigned editorial settings; stored observations remain intact. Exact
request/return, source/copy, rights, identity, KILL_SWITCH and duplicate/readback
checks remain in the existing consumer.

## Real timing evidence

The production SQLite database was opened with `mode=ro`. Its latest native
article review remains 4 November 2026 at 12:18:31 GMT+7. No newer approval exists.
All three retained articles with current timing records missed 15 minutes; see
[live timing](live-timing-observation.json). No approval was reset or backdated.

The two current Web consumer files are byte-identical to those executed by
CC-154 at 01:36 GMT+7 on 5 November: site-only records failed with
`NEWSROOM_CANONICAL_REQUIRED`, while the Substack control passed. This continuation
verified their current hashes and records the earlier execution's result, rather
than claiming a new execution. See [dependency evidence](web-consumer-dependency.json).

Codex Web / Ops Product must wire the existing reviewed
`site_publication_candidate_v1.json` into deployment independently of Substack,
render `expected_site_url`, and expose `article_content_sha256` for readback.
Publisher can then measure the next ordinary article against its first approval
clock. This is the remaining outside cause for CC-172; test timings are not a
substitute for actual public dispatch clocks.

No public writes, production-store writes, schedule changes, app restarts,
mailbox access, desktop control or chat messages occurred in this continuation.
Unrelated dirty files are preserved by hash. The execution model/effort is
recorded as gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED; no editorial calls were made.

See [validation and integration](validation.json) for final commits, focused
checks, installed file hashes and preservation results.
