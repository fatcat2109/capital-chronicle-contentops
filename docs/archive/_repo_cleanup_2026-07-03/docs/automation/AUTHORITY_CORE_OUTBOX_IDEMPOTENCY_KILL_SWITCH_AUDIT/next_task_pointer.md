# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_ACCOUNT_BINDING_PERMISSION_SCOPE_VERIFIER_CORE_V0`

Rationale:

- Outbox/idempotency/kill-switch/audit core now has deterministic no-live contracts.
- Next core dependency should verify account binding and permission scopes before supervised live readiness can be considered in future tasks.

Constraints to carry forward:

- No live platform calls.
- No credential hydration.
- No environment reads.
- No browser/CDP.
- No UI work unless explicitly requested.
