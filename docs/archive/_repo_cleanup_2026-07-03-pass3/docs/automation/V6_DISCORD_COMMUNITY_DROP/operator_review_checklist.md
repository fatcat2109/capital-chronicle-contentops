# Operator Review Checklist

## Staging Status
- **Staging Status**: DISCORD_DROP_REVIEW_READY_WITH_SOURCE_GAP
- **Review Status**: AWAITING_OPERATOR_EVIDENCE_AND_APPROVAL

## Verification Checklist

### 1. Evidence Gap Checklist
- [ ] Supply verified reference for missing source references: `operator_idea_source_ref`

### 2. Payload Hash Checklist
- [ ] Generate exact payload hash of the final content.
- [ ] Confirm `exact_payload_hash_present` is updated to true.

### 3. Destination Binding Checklist
- [ ] Confirm active target channel family: `community_announcements_placeholder`
- [ ] Confirm `destination_binding_present` is updated to true.

### 4. Safety & Environment Checks
- [ ] Verify no secrets, credentials, or webhook URLs are present in the files.
- [ ] Verify `webhook_url_present` and `webhook_url_printed` remain false.

### 5. Final Dispatch Lock
- [ ] Verify `dispatch_allowed_now` remains strictly false until all requirements are met.
- [ ] Verify `public_postable` remains strictly false.
