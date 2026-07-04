# Next Task Pointer: Discord Approval Ledger and Outbox Binding

## Recommended Next Task

Build non-live approval ledger and outbox binding for Discord payload hash packets.

## Scope Recommendation

- Persist approval packet records locally.
- Bind outbox entries to exact payload hash, payload ID, destination binding ID, credential handle ID, and payload type.
- Keep `valid_for_dispatch=false` unless separate future explicit live gate task authorizes dispatch.
- Keep webhook URL loading disabled.
- Keep Discord bot deferred.
- Keep network calls disabled.

## Do Not Do Yet

- Do not send Discord webhook request.
- Do not hydrate webhook URL.
- Do not connect Discord bot.
- Do not create live dispatch success audit.
