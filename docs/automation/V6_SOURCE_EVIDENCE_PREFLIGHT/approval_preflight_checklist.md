# Approval Preflight Checklist

## Preflight Check
- **Review Status**: AWAITING_SOURCE_EVIDENCE
- **Unresolved Source References**: `operator_idea_source_ref`

## Preflight Review Areas

### 1. Source Evidence Checklist
- [ ] Ensure all missing source references are mapped to verified operator evidence.
- [ ] Confirm `evidence_complete` is true.

### 2. Exact Payload Hash Checklist
- [ ] Generate exact payload hash of content drafts.
- [ ] Confirm `exact_payload_hash_present` is updated to true.

### 3. Destination Binding Checklist
- [ ] Ensure non-sensitive channel family matches a valid local registry layout.
- [ ] Confirm `destination_binding_present` is true.

### 4. Safety Constraints Checklist
- [ ] Confirm no hype language is present.
- [ ] Confirm no trading signals, stop loss/take profit, position sizing, or price predictions are present.
- [ ] Confirm no webhook URLs, raw tokens, or credential variables exist in any file.

## Final Review Check
- **Dispatch Blocked Note**: Dispatch remains strictly blocked. `dispatch_allowed_now` is false.
