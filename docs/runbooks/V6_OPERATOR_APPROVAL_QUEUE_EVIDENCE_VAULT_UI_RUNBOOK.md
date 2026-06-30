# V6 Operator Approval Queue + Evidence Vault UI Runbook

## Purpose

Review committed canonical article, variant preview hashes, pending approvals, Discord dry-run outbox evidence, redacted audit status, and blocked live-pilot state without performing any live action.

## Regenerate Packet

```powershell
python -m live_contentops.operator_approval_queue_evidence_vault_v6 --output docs/automation/V6_OPERATOR_APPROVAL_QUEUE_EVIDENCE_VAULT_UI/sample_operator_approval_queue_evidence_vault_packet.json
```

## Open Static UI

Open locally:

```text
ui/operator_approval_queue_evidence_vault/index.html
```

## Operator Rules

- Treat all approval controls as preview-only.
- Do not use this screen as runtime credential proof.
- `sample_fixture_only` means committed fixture evidence, not a live env check.
- Live pilot remains blocked until a future task explicitly scopes write behavior and runtime gates.
