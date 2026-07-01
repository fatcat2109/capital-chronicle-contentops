# ContentOps V5 Substack Manual Publication URL Audit Import Browser QA

Canonical target: `ui/contentops_v5/`

## Result

PASS. Canonical V5 loaded locally and showed the V6 Substack manual publication URL audit import packet in all required views.

## Verified views

- Manual Export: `Substack manual publication URL audit import` panel visible with status, URL hash, and verification/safety flags.
- Approval Queue: `Substack URL audit import pending review` visible with blocked controls and `enabled=false`.
- Evidence Vault: `Substack publication URL audit evidence` visible under Forensic tab with safety flags.

## Safety invariants observed

- `url_network_verified=false`
- `substack_api_used=false`
- `provider_call_made=false`
- `network_call_made=false`
- `credential_read_made=false`
- `env_value_read_made=false`
- `browser_session_used=false`
- `live_publish_performed_by_contentops=false`
- `manual_publication_claim_operator_supplied=true`
- approve/send/publish/dispatch/schedule controls remain blocked
- no URL fetching or network scraping was executed
- no V4 or standalone dashboard targeted

## Screenshots

- `manual_export_url_audit.png`
- `approval_queue_url_audit.png`
- `evidence_vault_url_audit.png`
