# CC-432: Discord analysis reply recovery, 13 November 2026

The existing gold page, Telegram card/reply and Threads card/reply remain confirmed. This run resumes only `plan-analysis-link-plan_230a9464a193ca7a377d0c41-discord` in its original gold thread. The manuscript, public prices, stored issued packets, social text and existing public objects are unchanged; only the malformed HTTP representation is corrected.

The minute consumer retried automatically at 12:00 GMT+7. Discord rejected its text-only reply with HTTP 400, code 50035: the transport had added a URL-only embed with an empty title. The previous HTTP 403/40333 is no longer the current cause. The wrapper also discarded the provider error, so the coordinator treated this local payload error as an ambiguous send and consumed its retry.

The transport now omits an empty optional embed and preserves adapter failures for safe classification. The existing plan-page CLI adds one explicit `link-repair-embed` action. It matches this measured provider rejection to the exact daily failure, validates the unchanged page, link and parent, and performs a fresh authenticated thread read. Only proven absence permits one corrected send through the sole coordinator. It preserves the original failure and uses the existing correction audit. Platform restrictions and uncertain reads still stop writes; the correction cannot allocate a second send after a lost return.

- [Consumer and exact recovery tests](discord-link-tests.xml): 32 passed in 54.34 seconds.
- [Discord transport and link-copy regression](discord-transport-copy-tests.xml): 21 passed in 1.23 seconds.
- [Sanitized provider evidence](discord-midnight-invalid-embed.json): only provider code, field error, event identity, time and request size; no credential material or environment inventory.
- [Initial exact state](before.json), [readback](discord-readback-before.json) and [unchanged resume](discord-resume.json) show no send by this run before the repair.

Base: operating HEAD `b1598b878019c7e995fbad0eb5b254c0242603e7`. Launch process 37064 explicitly configured `gpt-6.1-sol` / `max`; **CONFIGURED_NOT_OBSERVED**. Runtime model and effort telemetry are unavailable. This recovery makes no editorial model call. Finished CC-549 work was preserved and pushed as `2e5e32fc` on its own branch; it is outside this delivery. The two existing telemetry/duplicate-ledger modifications remain outside commits.

The first fix is installed as `1de59244`. Its corrected request reached Discord at `2026-11-13T05:26:41Z` and revealed a second local validation defect, HTTP 400/50035 `MESSAGE_REFERENCE_UNKNOWN_MESSAGE`. A Discord thread starter belongs to its parent announcements channel; sending a message into that exact thread already attaches it to the starter. A same-ID `message_reference` points to a message outside the thread and is invalid there.

The adapter now uses that thread containment for a starter reply and keeps an explicit message reference for a reply to a different message inside the thread. Strict direct readback and lost-ID recovery apply the same rule, still checking the exact thread, body, canonical, bot author in the history search, and foreign references. The issued payload, source body and public parent stay unchanged. `link-repair-reference` permits one correction of this measured second rejection, again after a fresh absence read, through the same coordinator and correction audit.

Final source checks: 60 passed in two sequential bounded runs: [26 consumer/repair checks](discord-repair-tests-final.xml), 25.28 seconds, and [34 adapter, history-recovery and copy checks](discord-wire-recovery-tests-final.xml), 11.56 seconds. The four checks against the first installed fix also passed in 7.08 seconds ([XML](installed-first-fix-tests.xml)).

The final source is installed at `73f8c755e782ed4db41450ebfe8915538756344b`, with live tag `contentops-live-20261113-cc432-thread-reference` and rollback tag `contentops-rollback-20261113-cc432-empty-embed` (base `b1598b87`). [Eight installed consumer/adapter checks](installed-final-consumer-tests.xml) passed in 5.41 seconds.

**DONE.** The exact gold [Discord card](https://discord.com/channels/1519310996030750782/1519311669216673802/1570498124391125187) and [full-analysis reply](https://discord.com/channels/1519310996030750782/1570498124391125187/1570672638332772352) are read back and reconciled confirmed. The [Substack page](https://capitalchronicle.substack.com/p/gold-our-bearish-plan-39543964-entry), [Telegram reply](https://t.me/CapitalChronicle/182) and [Threads reply](https://www.threads.com/@official.capitalchronicle/post/DfppyDVEyr4) retain their confirmed identities. This meets Ops Product's 11 November amendment: the next run's card and analysis link in their Discord thread.

[Closeout](closeout.json) records the actual source hashes, publication identity and verification. [Fresh API readback](discord-final-readback.json), [strict body/canonical/thread/parent checks](discord-strict-public-readback.json), and [card readback](discord-card-readback.json) verify the public result. The original link packet's SHA256 is unchanged: `7e1b35df186d4b43912c0eb7728fa258bf19668966d010a2373c84486e507c98`.

The five original 10 November web-only pages remain confirmed in the store; this run did not republish them or claim fresh browser inspections. No historical expired links were retried, no old public object was edited, no canonical page was added, and no schedule or chat was changed. There is no remaining action for CC-432.
