# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_LIVE_GATE_STATE_MACHINE_AND_ERROR_CLASSIFIER_CORE_V0`

## Rationale

The account binding permission/scope verifier now provides local-only fail-closed binding status, blocker reasons, and approval invalidation fields.

Next logical core layer: deterministic live-gate state machine and error classifier that can consume:

- platform universe gates
- payload class contracts
- approval ledger state
- outbox/idempotency/kill-switch state
- binding permission/scope verifier blockers

## Constraints For Next Task

- Core backend/domain-contract only.
- No UI work.
- No browser QA.
- No screenshots.
- No Playwright.
- No credential hydration.
- No read-only live probe unless explicitly authorized by task.
- No live write enablement.
