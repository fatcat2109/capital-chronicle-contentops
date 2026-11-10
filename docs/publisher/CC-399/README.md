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

Initial sub-step: 10 focused source/composition/render checks passed on
10 November 2026. Integration and public readback are still pending.
