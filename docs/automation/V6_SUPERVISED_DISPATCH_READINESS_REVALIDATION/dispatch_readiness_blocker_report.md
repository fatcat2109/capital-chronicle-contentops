# Supervised Dispatch Readiness Blocker Report

## Active Blockers Table

| Blocker ID | Severity | Source Ref | Required Next Action |
| --- | --- | --- | --- |
| `operator_signature_missing` | CRITICAL | docs\automation\V6_OPERATOR_APPROVAL_SIGNATURE_BINDING\operator_signature_validation_report.json | Jim runs operator approval capture local run step to create valid signature. |
| `destination_binding_incomplete` | CRITICAL | docs\automation\V6_DESTINATION_BINDING_OUTBOX_DRAFT\destination_binding_outbox_draft_packet.json | Verify target destination bindings and confirm review-only state is mapped. |
| `outbox_creation_blocked` | CRITICAL | docs\automation\V6_DESTINATION_BINDING_OUTBOX_DRAFT\outbox_draft_validation_report.json | Supervised review must construct outbox draft before dispatch queueing. |
| `live_write_authorization_missing` | CRITICAL | live_contentops/supervised_dispatch_readiness_revalidation_v6.py | Dispatch authorization token/override must be requested in a separate task. |
| `safety_review_incomplete` | CRITICAL | live_contentops/supervised_dispatch_readiness_revalidation_v6.py | Review that content contains no financial predictions, hype, or mock statistics. |
| `kill_switch_active` | CRITICAL | live_contentops/supervised_dispatch_readiness_revalidation_v6.py | Keep global dispatch kill-switch enabled until final manual approval. |
| `public_postable_false` | CRITICAL | live_contentops/supervised_dispatch_readiness_revalidation_v6.py | Content postable capability is locked; do not mark public postable. |

## Unsafe Material Findings
- Unsafe Materials Detected: None
