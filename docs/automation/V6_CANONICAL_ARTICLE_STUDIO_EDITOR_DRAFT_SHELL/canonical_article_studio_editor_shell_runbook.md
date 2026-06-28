# V6 Canonical Article Studio Editor Draft Shell Runbook

This runbook documents operator and system actions for the offline simulated Editor Draft Shell state.

## Operator Review Checklist
1. Confirm that all editor shell slots remain unpopulated (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
