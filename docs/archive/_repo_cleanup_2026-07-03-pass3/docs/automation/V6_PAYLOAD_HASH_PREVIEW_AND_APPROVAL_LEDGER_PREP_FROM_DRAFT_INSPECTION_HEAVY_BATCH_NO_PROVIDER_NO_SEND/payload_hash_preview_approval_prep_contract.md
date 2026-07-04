# V6 Payload Hash Preview and Approval Ledger Prep Contract

## Input Requirements

Draft inspection bundle eligibility must have `eligible_for_payload_hash_preview_task` and `eligible_for_approval_ledger_preparation_task` set to true, blockers empty, and all target/status checks satisfied.

## Previews

- Supported platforms: substack, discord, telegram, x_manual, linkedin_org_deferred, tiktok_deferred.
- Adapter classes: manual_fallback_adapter, deferred_adapter, future_webhook_adapter, review_only.
- Payload hashes must exclude webhook URLs, secret material, browser profile, or session cookies.
- Symbolic placeholders only for destination and credentials.

## Approval Ledger Prep Candidate

- Approval status is not_approved.
- `approval_granted_now`, `valid_for_outbox`, `valid_for_dispatch`, publication_ready, dispatch_allowed, and live_send_allowed are false.
- Revocation is supported.
- Future requirements (expiration, destination, credential, revalidation, redacted audit) are true.

## Hard False State

Consolidated bundle `eligible_for_future_outbox_preparation_task` and `eligible_for_live_send_now` are false. All side-effect and publish flags are false.
