# Next Task Pointer — Discord One-Request Live Pilot

## Current Result

The first one-request live pilot attempted exactly one POST and returned status class `4xx`.

## Recommended Next Task

Investigate Discord webhook credential/destination mismatch without exposing the raw webhook URL:

1. Confirm `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL` is the intended announcements webhook in Jim's Windows User Environment Variables.
2. Do not print, hash, length-count, prefix, or suffix the env value.
3. Use Discord UI or safe manual confirmation to verify the target channel/webhook still exists.
4. If credential is corrected, run a new explicit one-request live pilot task with request budget `1` and retry budget `0`.

## Carry Forward

- Keep request budget hard cap at `1`.
- Keep retry budget at `0`.
- Keep `allowed_mentions={"parse":[]}`.
- Keep response body and headers unrecorded.
