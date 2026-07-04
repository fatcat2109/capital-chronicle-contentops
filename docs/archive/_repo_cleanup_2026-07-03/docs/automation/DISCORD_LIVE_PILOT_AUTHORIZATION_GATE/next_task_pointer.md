# Next Task Pointer: Discord Webhook One-Request Live Pilot

## Do Not Execute Here

This pointer does not authorize dispatch. It describes a separate future live task.

## Future Task May Send Exactly One Discord Webhook Test Only If Jim Explicitly Requests It

Future task must require and verify:

- exact dispatch_candidate_id
- exact payload_hash
- exact payload preview
- exact target_name
- exact destination_binding_id
- exact credential_handle_id
- env key name
- endpoint family: `discord_execute_webhook`
- host allowlist
- path template
- method: `POST`
- request_budget=1
- retry_budget=0
- timeout=10
- wait=false
- kill switch passed
- idempotency key
- post-request redacted audit
- stop on mismatch
- no hidden destination/account/channel mutation

## Required Future Authorization Phrase

`AUTHORIZE_DISCORD_WEBHOOK_TEST_SEND_NOW`

## Required Kill Switch

- env key: `CONTENTOPS_LIVE_DISPATCH_KILL_SWITCH`
- required value: `ALLOW_DISCORD_TEST_SEND`

## Dispatch Boundary

Future task must explicitly authorize webhook URL hydration and one network request. Without that, current candidate remains non-dispatchable.
