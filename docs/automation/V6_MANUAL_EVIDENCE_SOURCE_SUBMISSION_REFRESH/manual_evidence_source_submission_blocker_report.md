# Manual Evidence Source Submission Blocker Report

- **Refresh Status**: PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL
- **Active Dispatch Blockers**:

- `destination_binding_incomplete`
- `kill_switch_active`
- `live_write_authorization_missing`
- `operator_approval_incomplete`
- `outbox_creation_blocked`
- `payload_hash_incomplete`
- `safety_review_incomplete`

## Active Blockers Details

1. **evidence_incomplete**
   - *Detail*: Jim has not filled out the 10 required evidence slots in `operator_evidence_fixture.json`.
2. **operator_idea_source_ref_missing**
   - *Detail*: A valid, non-placeholder source reference ref is required.
3. **kill_switch_active**
   - *Detail*: Safety kill switch blocks dispatch.
