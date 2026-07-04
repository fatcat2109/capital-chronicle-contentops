# Operator Approval Queue and Audit Log

The Operator Approval Queue and Audit Log (`cc-live-contentops/live_contentops/approval_queue.py` and `audit_log.py`) represent the deterministic human review boundary for live content operations.

### Purpose
- **Approval Queue:** Takes policy decisions and turns them into human-reviewable items.
- **Audit Log:** Captures an append-only deterministic record of policy evaluations and human actions.

### Local-Only Status
These modules contain zero network bindings. 
An approval action inside the queue produces an `APPROVED_FOR_FUTURE_DRY_RUN_ONLY` status, which does **not** equal a live platform publish. It merely clears the item for a dry-run provider integration.

### Redaction and Secrets
Audit events automatically scan and reject payloads that contain sensitive patterns, enforcing a `REDACTED` state and setting `safe_to_log = False` if any keys exist.

### Forbidden Actions
The operator queue strictly enforces that items cannot be acted upon with:
- `publish_now`
- `schedule_now`
- `send_now`
- `auto_approve`
- `auto_publish`
- `autonomous_reply`
- `dm_user`

### Upstream/Downstream Flow
Policy Engine (0038) -> Operator Queue (0039) -> Future Provider Gateway Dry Run (0040)
