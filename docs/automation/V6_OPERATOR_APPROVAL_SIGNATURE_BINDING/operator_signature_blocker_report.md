# Operator Signature Binding Blocker Report

- **Signature Binding Status**: AWAITING_OPERATOR_SIGNATURE
- **Binding Blockers**:

- `operator_approval_incomplete`

## Boundary Notes

- Binding lane can validate operator intent against exact payload hash only.
- Binding lane cannot authorize dispatch, create outbox entries, bind destinations, hydrate credentials, or mark content public-postable.
- `valid_for_dispatch` must remain `false` in this lane.
