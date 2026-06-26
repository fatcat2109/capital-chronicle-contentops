# Next Task Pointer

Recommended next task: Discord webhook supervised send gate design.

## Preconditions

- Keep current dry-run renderer as mandatory input.
- Require approval ledger integration before any send.
- Keep `live_write_allowed_now` false until explicit future live gate task.
- Never hydrate, print, hash, prefix/suffix, or length-count webhook URLs or tokens in logs.

## Suggested Scope

1. Add approval packet schema for one Discord webhook payload.
2. Add live-send gate stub that refuses by default.
3. Add audit event shape with credential handle ID and destination binding ID only.
4. Add tests proving no network call occurs without explicit live authorization.
