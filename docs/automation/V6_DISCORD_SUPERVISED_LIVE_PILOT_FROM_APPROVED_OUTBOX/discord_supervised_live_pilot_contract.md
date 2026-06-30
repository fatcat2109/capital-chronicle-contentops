# V6 Discord Supervised Live Pilot Contract

This contract defines the only allowed live boundary for the V6 Discord supervised pilot from an approved dry-run outbox packet.

## Required Gates

A live webhook POST is allowed only when all conditions pass:

- Operator approval declaration is present.
- `operator_approval_status=approved`.
- `approved_by` is non-empty.
- `approved_at` is non-empty.
- Declaration `exact_payload_hash` equals the recomputed preview hash.
- Dry-run outbox and embedded approval records link to the same hash.
- `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK` is present in env.
- Kill switch is inactive.
- Request budget is exactly `1`.

## Live Boundary

- At most one Discord webhook POST may be attempted.
- No hidden retry is allowed.
- Timeout is finite and small.
- The request body content is exactly the approved preview text.

## Redaction Rules

Persist only redacted result fields:

- success / blocked / failed_redacted
- status class such as `2xx`, `4xx`, or `5xx`
- booleans for env presence and safety flags

Never persist or print:

- Webhook URL or token
- Raw env lines
- Headers
- Response body
- Secret-derived hashes, lengths, prefixes, suffixes, or digests

## Blocked Default

If the approval declaration is absent, invalid, hash-mismatched, kill-switched, or env key missing, emit a blocked result with `request_count=0` and no network call.
