# CC-646 — USD/JPY result correction

The exact supplied correction uses the existing status-post composer, sole
`DurablePublicationCoordinator` and Telegram/Discord API transports. There is
no article, new schedule, browser action or original-post edit.

The shortened backlog key resolves uniquely to
`plan-result-post-f5ecb8c81fed4b645e17580901ac7ff0`. Telegram 189 and Discord
1572145031173906523 are its only confirmed public copies. The Discord result
is in call thread 1572136686857748551; its correction references the result
message itself inside that thread.

Before a correction can send, all four untouched Facebook, Instagram, Threads
and X intents must be cancelled through the coordinator. The transaction
checks the exact intent, rejects existing dispatch/native claims, preserves
request bytes and records a terminal definite no-write. The durable dispatch
claim refuses a later send. Issued/uncertain writes are never cancelled.

The visual is the original public plan 188 chart captured at
2026-11-17T06:29:48.866487Z, before the entry window closed. Its original bytes,
source clock, scale evidence, overlay and TradingView attribution are retained;
it is copied into this correction's media folder and reuses its verified hosted
copy. The correction does not use the later result chart. The supplied body is
unchanged; the existing notices and mandatory TradingView credit are appended.
The exact final text and hash are in [preflight.json](preflight.json).

A SQLite backup of the existing store was exercised first. Four cancellations
were repeatable; original payloads and the two confirmed objects were unchanged;
later dispatch claims were refused. See
[copied-store-cancellation.json](copied-store-cancellation.json) and
[copied-store-prepared.json](copied-store-prepared.json). The temporary database
and PNGs stay outside Git in `local-evidence/CC-646/`.

Run the item module's `cancel`, `prepare`, `publish` and `status` phases once as
needed, always with an explicit evidence path. `publish` continues the same
frozen dispatches; it does not create a new correction or retry an uncertain
write. Runtime action evidence and final verification are retained beside this
file. Model/effort: gpt-6.1-sol/max configured in the observed exec arguments;
actual runtime model/effort telemetry is CONFIGURED_NOT_OBSERVED.

Validation: 156 unique targeted cases have passing latest results. The four-file
run passed 155 and exposed one pre-existing CC-359 assertion missing the mandatory
chart credit; the same failure reproduced with the operating-base composer.
After correcting that assertion, all 13 affected tests passed. Production code
was unchanged after the four-file run. See [validation-summary.json](validation-summary.json).
