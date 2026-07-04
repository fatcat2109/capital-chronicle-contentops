# V6 Payload Preview & Hash Verification Runbook

Jim, follow these steps to verify payload preview truth and deterministic hash state:

## Verification Steps
- [ ] **Step 1**: Review `payload_preview_exact_review.json` under `docs/automation/V6_PAYLOAD_PREVIEW_HASH/`.
- [ ] **Step 2**: Confirm the preview uses committed delegated evidence summary facts only.
- [ ] **Step 3**: Inspect `payload_hash_inputs_redacted.json` for deterministic safe inputs only.
- [ ] **Step 4**: If status is `READY_FOR_OPERATOR_REVIEW`, confirm `payload_hash_record.json` matches the preview inputs exactly.
- [ ] **Step 5**: If status is `BLOCKED_EXACT_PAYLOAD_MISSING`, keep this lane blocked and do not advance approval binding.
- [ ] **Step 6**: Next recommended task remains `TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0`.
