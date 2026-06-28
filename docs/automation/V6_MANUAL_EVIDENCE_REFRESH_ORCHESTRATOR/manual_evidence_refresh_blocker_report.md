# Manual Evidence Refresh Blocker Report

- **Overall Pipeline Status**: PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL
- **Active Dispatch Blockers**:

- `destination_binding_incomplete`
- `kill_switch_active`
- `live_write_authorization_missing`
- `operator_approval_incomplete`
- `outbox_creation_blocked`
- `payload_hash_incomplete`
- `safety_review_incomplete`

## Blocker Descriptions

1. **destination_binding_incomplete**
   - *Detail*: No target endpoint or destination has been authorized for write operations.
2. **evidence_incomplete**
   - *Detail*: Required evidence slots are empty or contain default placeholders.
3. **operator_idea_source_ref_missing**
   - *Detail*: Jim has not supplied a verified source reference in the console fixture.
4. **kill_switch_active**
   - *Detail*: Safe-mode override is active, blocking all outbound network publish requests.
