# Operator Approval Gate Runbook

Jim, follow these steps to sign off and approve evidence candidate review intent:

## Approval Steps

- [ ] **Step 1**: Open `operator_approval_signature_template.json` in `docs/automation/V6_OPERATOR_APPROVAL_GATE/`.
- [ ] **Step 2**: Fill in your operator ID:
  - `"operator_id": "JIM_OPERATOR"`
- [ ] **Step 3**: Update the approval decision to APPROVED:
  - `"approval_decision": "APPROVED"`
- [ ] **Step 4**: Keep `valid_for_dispatch=false` (do NOT mark dispatch-valid in this lane). Fill only operator identity and review decision intent.
- [ ] **Step 5**: Save the file.
- [ ] **Step 6**: Proceed to `TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_V0` only after exact payload preview and payload hash controls exist.
- [ ] **Step 7**: Note that dispatch validity can only be evaluated after payload hash, destination binding, approval ledger, outbox, and dispatch-readiness gates exist.
