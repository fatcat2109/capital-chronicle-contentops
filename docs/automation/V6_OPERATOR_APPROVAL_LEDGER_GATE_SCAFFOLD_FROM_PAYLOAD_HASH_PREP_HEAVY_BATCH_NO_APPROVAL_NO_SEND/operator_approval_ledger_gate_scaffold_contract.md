# V6 Operator Approval Ledger Gate Scaffold Contract

## Input Requirements

Upstream payload hash prep bundle eligibility must be true, with blockers empty, non-empty previews, and candidate status not_approved.

## Declaration Scaffold

- mode is operator_approval_gate_scaffold_only.
- scope is payload_hash_preview_review_only.
- exact phrase is NOT_APPROVED_IN_THIS_SCAFFOLD.
- lists of approved IDs, hashes, platforms must be empty.
- approval_granted_now, publication_approved_now, outbox_approved_now, dispatch_approved_now, and live_send_approved_now must be false.
- requesting flags (provider, env, credential, network, browser, executable, public, metrics) must be false.
- destination binding and credential handle must be absent.

## Ledger Record Shell

- mode is scaffold_only_no_approval.
- status is not_approved.
- valid_for flags (preview, outbox, dispatch, publication, live_send) must be false.
- explicit outbox and live-send task requirements must be true.

## Hard False State

Consolidated bundle `eligible_for_future_outbox_preparation_task` and `eligible_for_live_send_now` are false. All side-effect and publish flags are false.
