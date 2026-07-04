# V6 Operator Approval Queue Evidence Vault Contract

## Scope

Deterministic local view-model packet for reviewing committed evidence before any future write-scoped approval workflow.

## Safety

- Reads committed packet files only.
- No provider calls, network calls, browser session use, env reads, or live sends.
- All live approval/send/dispatch controls in the static UI are disabled.
- Sample key presence is labeled `sample_fixture_only`, not runtime proof.

## Required Sections

- `approval_queue_items`
- `evidence_vault_items`
- `article_preview_summary`
- `variant_preview_cards`
- `discord_outbox_card`
- `live_pilot_status_card`
- `redacted_audit_summary`

## Approval Queue Item

Each item includes queue IDs, platform, variant/preview IDs, exact preview hash, pending status, null approval actor/timestamp, live dispatch false, excerpt, source canonical hash, and required operator action.

## Evidence Vault Item

Each item includes source file path, packet ID, hash, safety flags, display status, and caveats.
