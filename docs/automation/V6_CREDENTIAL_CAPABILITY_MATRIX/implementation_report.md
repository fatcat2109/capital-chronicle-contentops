# V6 Redacted Credential Capability Matrix ? Alias Repair Report

Task label: `TASK_CONTENTOPS_V6_CAPABILITY_MATRIX_ALIAS_REPAIR_V0`

## Scope

Repaired the V6 credential capability matrix alias handling while preserving the redaction boundary.

## Files

- `live_contentops/unified_credential_capability_matrix.py`
- `tests/test_unified_credential_capability_matrix.py`
- `docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json`
- `docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/implementation_report.md`

## Repairs

- Added Discord specific webhook aliases:
  - `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL`
  - `DISCORD_SUBSTACK_DROPS_WEBHOOK_URL`
  - `DISCORD_PRODUCT_UPDATES_WEBHOOK_URL`
- Added Discord specific channel and role aliases without requiring generic `DISCORD_CHANNEL_ID` or `DISCORD_ROLE_ID`.
- Added 9router aliases:
  - `NINE_ROUTER_API_KEY`
  - `NINE_ROUTER_BASE_URL`
  - `NINE_ROUTER_MODEL`
  - `CC_UI_PROVIDER_LIVE_BOUNDARY_NINE_ROUTER`
- Retained legacy provider aliases:
  - `NINEROUTER_API_KEY`
  - `ROUTER_API_KEY`
  - `OPENROUTER_API_KEY`
  - `AI_PROVIDER_API_KEY`
- Added `THREADS_USER_ACCESS_TOKEN` and kept Threads separate from Meta Graph.
- Classified Meta, Facebook, Instagram, and Threads as scope-proof/live-gate required rather than unconditional live-ready.
- Added blank/nonblank status for env key values without printing values.
- Added `live_write_allowed_now: false` to every row.
- Added malformed summary count while keeping raw malformed line contents hidden.

## Redaction policy

The matrix outputs only key names, boolean presence, blank/nonblank/missing status, and readiness metadata.
It does not output raw secrets, webhook URLs, token length, token prefix/suffix, hashes/digests, cookies, session data, localStorage, browser profile secrets, or raw malformed line contents.

## Runtime boundary

No browser/CDP, live platform/API probes, cookies, browser storage, or platform writes were used for this repair.
`live_write_allowed_now` remains `false` for all rows.
