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

Decision 110's amended CC-399 instruction replaces Antigravity with the first
three source reasons, at most 200 characters each, and a fixed glossary. No
model is called. Every number is compared with that call's own source reasons.

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
