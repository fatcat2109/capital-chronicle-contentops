# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_AND_RECOVERY_HEAVY_BATCH_V0`

Recommended next task:

```text
TASK_CONTENTOPS_V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_HEAVY_BATCH_V0
```

Purpose: establish the explicit live scope gate checkpoint for the operator recovery runbook.

Do not start live writes, browser/CDP probes, or LLM/provider API calls as part of the next task unless explicitly authorized.
