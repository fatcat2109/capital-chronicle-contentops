# Next Task Pointer — Discord Minimal-Content Repair

## Current Result

Minimal-content live pilot returned exact HTTP status `403`.

Diagnostic interpretation: `credential_unauthorized`.

## Recommended Next Task

Repair or replace `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL` safely:

1. Verify webhook still exists in Discord UI.
2. Verify webhook belongs to intended announcements channel.
3. Re-copy webhook URL into Windows User Environment Variable `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL` if needed.
4. Do not print, hash, length-count, prefix, suffix, or store the env value.
5. After correction, run a new explicit one-request live pilot task with request budget `1`, retry budget `0`.

## Carry Forward

- Use `payload_mode=minimal_content_only` until connectivity succeeds.
- Keep `allowed_mentions={"parse":[]}`.
- Keep response body and headers unrecorded unless Jim explicitly authorizes diagnostic body capture.
