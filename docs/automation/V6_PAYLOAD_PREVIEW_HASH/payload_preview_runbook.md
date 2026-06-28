# V6 Payload Preview & Hash Verification Runbook

Jim, please follow these steps to verify the deterministic payload hash:

## Verification Steps
- [ ] **Step 1**: Review `payload_preview_exact_review.json` under `docs/automation/V6_PAYLOAD_PREVIEW_HASH/`.
- [ ] **Step 2**: Inspect the safe, redacted hash input keys in `payload_hash_inputs_redacted.json`.
- [ ] **Step 3**: Confirm that the payload hash record is successfully captured in `payload_hash_record.json`.
- [ ] **Step 4**: Note that changing the payload body text, platform type, source mapping, or policy parameters will automatically regenerate a new payload hash.
- [ ] **Step 5**: Once satisfied, proceed to `TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0`.
