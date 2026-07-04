# Pre-Alpha Manual Review Workflow and Approval Packet (Task 0098)

Local-only, deterministic. Consumes 0097 review queue items plus a MANUAL human
review decision and emits approval / revision / rejection packets.

## Posture

- No network/search/provider/LLM/platform/credential access.
- No posting, no `.env` reads, no auto-approval.
- "Approval" means ready for future MANUAL publish prep only. It never means
  live posting, publish-now, or platform action.
- All output packets pin: `public_postable=false`, `publish_allowed_now=false`,
  `platform_publish_allowed_now=false`, `live_execution_allowed_now=false`,
  `final_operator_check_required=true`.

## Decision model

`schemas/pre_alpha_manual_review_decision.schema.json`

Decisions: `approve_manual_publish_prep`, `request_revision`, `reject`.

Validation (`validate_decision`):
- Requires a non-empty `reviewer_id_placeholder` (no auto-approval).
- Pins `auto_approval=false`, `reviewer_required=true`, `manual_publish_only=true`.
- Rejects `publish_allowed_now`, `platform_publish_allowed_now`,
  `live_execution_allowed_now` if not false.
- `request_revision` requires `required_revision_notes`.
- `reject` requires a `decision_reason`.
- `approve_manual_publish_prep` requires an allowed `approved_platform_family`
  and is blocked if the decision declares unresolved findings OR if an
  independent re-scan of the linked review item surfaces forbidden language,
  alpha implication, or an unverified numeric market claim.

## Approval packet

`schemas/pre_alpha_approval_packet.schema.json`

`build_approval_packet(rendered_packet_id, review_item, decision)`:
- Fails closed: any validation error or re-scan finding forces
  `approval_status="rejected"`, `manual_publish_prep_ready=false`, and populates
  `blocked_reasons`.
- `approved_text` is carried only on a clean approval; revision/rejection emit
  an empty string.
- Defense in depth: re-scans the review item body for forbidden language,
  alpha implication, and unverified numeric market claims, reusing the
  `grounded_research_brief` and 0095 detectors (single source of truth).
- `approval_audit_trail` records queue item, decision, reviewer, timestamp, and
  final status.

## Integration with 0097

The review item shape matches `pre_alpha_review_queue_item.schema.json`. The
workflow reuses `ALLOWED_CONTENT_TYPES`, `ALLOWED_PLATFORM_FAMILIES`,
`STATIC_TIMESTAMP`, and `_scan_numeric_market_claim` from the 0095 engine and
the forbidden-language/alpha scans from `grounded_research_brief`.

## CLI

`python -m live_contentops.cli pre-alpha-manual-review-summary`

## Fixtures

Valid: `valid_approve_manual_only`, `valid_request_revision`,
`valid_reject_guardrail`.

Invalid (fail closed): `invalid_auto_approval`, `invalid_publish_allowed_now`,
`invalid_missing_reviewer`, `invalid_unresolved_guardrail_findings`.

## Next task

TASK_CONTENTOPS_0099_PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_V0
