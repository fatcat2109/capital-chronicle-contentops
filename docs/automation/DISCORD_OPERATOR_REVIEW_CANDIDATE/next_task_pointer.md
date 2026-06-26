# Next Task Pointer: Future Discord Live Pilot Authorization Gate

## Do Not Execute Here

This pointer describes requirements for a separate future live pilot task. It does not authorize dispatch.

## Future Live Pilot Must Require

- exact dispatch_candidate_id
- exact payload_hash
- exact payload_id
- exact target_name
- exact destination_binding_id
- exact credential_handle_id
- exact rendered payload preview
- endpoint family: Discord webhook execute
- official endpoint documentation confirmation
- host allowlist: discord.com / discordapp.com only after official confirmation
- method: POST
- request budget: 1 request
- retries: 0 unless explicitly approved
- fixed small timeout
- kill switch check
- idempotency key
- duplicate suppression key
- post-request redacted audit event
- stop on any mismatch
- no hidden destination/account/channel change

## Required Safety Gates

Future task must separately authorize webhook URL hydration and network dispatch. Without that authorization, candidates remain non-dispatchable.
