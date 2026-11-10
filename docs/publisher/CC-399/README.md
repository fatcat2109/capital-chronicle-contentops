# CC-399 — Call cards and their threads

The plan-status consumer now aggregates new calls by Main's run identity. Each
run has one announcement and one source-bound card per call. Later fills and
endings retain their card key. The existing outbox, transports and sole
DurablePublicationCoordinator remain the publication owners.

The cards use the exported target, tick, entry deadline, time exit and stated
chance when present. Mapped public instruments never borrow a target or tick
from another price basis. Missing values stay absent. Ending words use Main's
scorer; a time exit is never called an expired trade. Untriggered direction is
shown only when Main supplies it.

Decision 113 replaces the three short reasons with CC-432's structured summary
and full-analysis link. The consumer accepts an optional `analysis_publication`
on its plan: `plan_id`, the matching `registration_hash`, a confirmed
`canonical_url` under `https://capitalchronicle.substack.com/p/`, and `summary`.
The summary has the public fields `macro`, `fundamental`, `technical`,
`geopolitical`, `priced_in`, `scenarios` and `desk_process`. Each destination
retains the link and uses the available room for the structured summary.
CC-432 owns the filtered page and this publication result; CC-399 reads no Main
run folder. No model is called. Until that result exists, the held source
reasons remain the available explanation, using decision 110's fixed glossary
and number check. This fallback is not full-analysis acceptance.

The run is configured as `gpt-6.1-sol` / `max`, read from the parent launch
arguments and labelled `CONFIGURED_NOT_OBSERVED`. No editorial model call is
part of this deterministic implementation.

The copied-store acceptance makes one run announcement and five cards, then
dispatches a fill and an ending to their exact card through the real
coordinator with controlled transports. Parent identities are checked again
at the write boundary. An unavailable parent defers only that destination.
The bounded Notes request opens the exact parent and requires parent readback.

Discord threads use the official create-thread endpoint and a bot credential;
the thread's id is its starter message id. Read-before-create prevents a lost
thread-create return from creating another thread. Messages use an exact card
reference. Without `DISCORD_BOT_TOKEN`, the child message is a definite no-write
with `DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE`; other destinations continue.

28 targeted composition, coordinator-consumption and Discord adapter checks
passed. See [card-and-thread-tests.xml](card-and-thread-tests.xml). The binary
visual example was inspected for zone, invalidation, target and ET window
legibility. Integration and the next natural morning/ending readbacks are
still pending.

The Meta route now keeps the same reader structure: Facebook puts image cards
in comments under the run photo; Instagram uses one run carousel and binds
each card to its verified image slot. Later updates comment under that run and
name the call's short id. They never publish another setup image. The official
[Instagram publishing guide](https://developers.facebook.com/documentation/instagram-platform/content-publishing)
was read on 10 November: carousel children are containers in one published
object, with a limit of 20 media items; image publishing requires JPEG. The new
renderer therefore supplies square JPEG cards through the existing media owner.

60 targeted card, ending and official-adapter checks passed in 21.65 seconds;
see [final-card-tests.xml](final-card-tests.xml). The earlier shared run passed
287 checks with two reproduced baseline failures: the old delayed format-3
Threads copy exceeds 500 characters after the notice change, and an X test
expects the retired X request route. `9b94d318` reproduces the former; `begin_x`
is byte-for-byte unchanged for the latter. CC-431 owns X restoration. Those
legacy failures do not describe format-4 card dispatch.

The final summary/parent checks passed 26 tests in 22.94 seconds. The live-export
dry run read Main's own contract reader, used the existing production outbox
identities and returned OK without a store or public write. See
[summary-and-parent-tests.xml](summary-and-parent-tests.xml) and
[current-export-dry-run.json](current-export-dry-run.json).
