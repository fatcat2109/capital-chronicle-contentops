# V6 Variant Preview/Hash Approval Contract

## Scope

The packet is a deterministic dry-run bridge from the canonical article engine to platform previews, exact preview hashes, pending approval records, and the Discord dry-run outbox spine.

## Safety

- No provider calls.
- No network/browser use.
- No live sends.
- No env reads or credential hydration.
- Credential/key-name evidence is symbolic only.

## Required Top-Level Fields

- `schema_version`
- `task_label`
- `packet_id`
- `source_article_packet_id`
- `source_article_hash`
- `variants`
- `preview_hash_records`
- `approval_records`
- `discord_dry_run_outbox_packet`
- `redacted_audit_packet`

## Downstream Approval Queue Contract

Each `approval_records[]` entry must remain pending until a future write-scoped approval task:

- `approval_status = pending_operator_review`
- `approved_by = null`
- `approved_at = null`
- `live_dispatch_allowed = false`

Each approval must link to a preview by `preview_id`, and each preview carries the exact preview hash used by the operator queue UI.
