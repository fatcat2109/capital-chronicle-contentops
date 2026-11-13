# CC-432: Discord analysis reply recovery, 13 November 2026

The existing gold page, Telegram card/reply and Threads card/reply remain confirmed. This run resumes only `plan-analysis-link-plan_230a9464a193ca7a377d0c41-discord` in its original gold thread. No manuscript, public price, issued request, social text or existing public object changes.

The minute consumer retried automatically at 12:00 GMT+7. Discord rejected its text-only reply with HTTP 400, code 50035: the transport had added a URL-only embed with an empty title. The previous HTTP 403/40333 is no longer the current cause. The wrapper also discarded the provider error, so the coordinator treated this local payload error as an ambiguous send and consumed its retry.

The transport now omits an empty optional embed and preserves adapter failures for safe classification. The existing plan-page CLI adds one explicit `link-repair-embed` action. It matches this measured provider rejection to the exact daily failure, validates the unchanged page, link and parent, and performs a fresh authenticated thread read. Only proven absence permits one corrected send through the sole coordinator. It preserves the original failure and uses the existing correction audit. Platform restrictions and uncertain reads still stop writes; the correction cannot allocate a second send after a lost return.

- [Consumer and exact recovery tests](discord-link-tests.xml): 32 passed in 54.34 seconds.
- [Discord transport and link-copy regression](discord-transport-copy-tests.xml): 21 passed in 1.23 seconds.
- [Sanitized provider evidence](discord-midnight-invalid-embed.json): only provider code, field error, event identity, time and request size; no credential material or environment inventory.
- [Initial exact state](before.json), [readback](discord-readback-before.json) and [unchanged resume](discord-resume.json) show no send by this run before the repair.

Base: operating HEAD `b1598b878019c7e995fbad0eb5b254c0242603e7`. Launch process 37064 explicitly configured `gpt-6.1-sol` / `max`; **CONFIGURED_NOT_OBSERVED**. Runtime model and effort telemetry are unavailable. This recovery makes no editorial model call. Finished CC-549 work was preserved and pushed as `2e5e32fc` on its own branch; it is outside this delivery. The two existing telemetry/duplicate-ledger modifications remain outside commits.

Operating-root integration, live/rollback tags and the exact public reply readback follow in this folder before the backlog can say DONE.
