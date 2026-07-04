# ContentOps V5 Substack Manual Export Operator Handoff Browser QA

Canonical target: `ui/contentops_v5/`

## Result

PASS. Canonical V5 loaded locally and showed the V6 Substack manual export operator handoff packet in all required views.

## Verified views

- Manual Export: `Substack operator handoff packet` panel visible with handoff/export/evidence hashes and manual-copy-only safety flags.
- Approval Queue: `Substack operator handoff pending review` visible with blocked controls and `enabled=false`.
- Evidence Vault: `Substack operator handoff evidence packet` visible with bound evidence cards and safety flags.

## Safety invariants observed

- `manual_copy_only=true`
- `live_publish_allowed=false`
- `substack_api_used=false`
- approve/send/publish/dispatch/schedule controls remain blocked
- no V4 or standalone dashboard targeted

## Screenshots

- `manual_export_scrolled.png`
- `approval_queue_view.png`
- `evidence_vault_scrolled.png`
