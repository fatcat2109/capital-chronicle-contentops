# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_PIPELINE_LIVE_REHEARSAL_AND_EVIDENCE_READBACK_V0` ? Controlled live/provider rehearsal and evidence readback completed. Dispatch was correctly blocked before platform posting because provider timeout/short draft quality gates failed. (COMPLETED LOCALLY; commit pending)

Recommended next task:

```text
TASK_CONTENTOPS_V6_PROVIDER_TIMEOUT_AND_DRAFT_QUALITY_RECOVERY_V0
```

Purpose: Harden provider timeout handling and draft quality recovery discovered by the controlled rehearsal, then rerun live/provider evidence readback toward dispatch readiness.
