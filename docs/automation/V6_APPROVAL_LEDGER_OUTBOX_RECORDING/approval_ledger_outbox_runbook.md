# V6 Approval Ledger & Outbox Recording Runbook

This runbook guides Jim and automated validators to verify inert ledger and outbox previews before final commit.

## 1. Local Signature Binding Verification
- Confirm that the local operator signature matches the payload hash.
- Ensure supervised dispatch readiness has no blockers before commits are made.

## 2. Validation Scanning
- Confirm no credentials, secret cookies, webhooks, or local user paths exist.
