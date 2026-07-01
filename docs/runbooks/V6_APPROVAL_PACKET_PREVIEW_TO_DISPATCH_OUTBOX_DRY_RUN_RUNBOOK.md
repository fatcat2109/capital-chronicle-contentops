# V6 Approval Packet Preview to Dispatch Outbox Dry Run Runbook

This is a local/manual-only runbook for the dispatch outbox dry-run workflow (`TASK_CONTENTOPS_V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_HEAVY_BATCH_V0`).

## Purpose
This workflow converts the accepted platform variant approval packet preview into a dry-run outbox package.
* **No real dispatches**: `executable_outbox_entry_created` and `real_outbox_entry_created` remain `false`.
* **No network/API calls**: All webhook / API counters (`dispatch_request_count`, `webhook_request_count`, `platform_api_request_count`) remain `0`.
* **Lock states**: All live dispatching, auto-publishing, scraper runs, credentials use, and provider API calls remain locked.
* Manual, future, or deferred platform states (such as deferred LinkedIn/Instagram/YouTube/TikTok adapters) are valid states and are not treated as failures.

## Local Files
* Local Builder: `live_contentops/approval_packet_preview_to_dispatch_outbox_dry_run_v6.py`
* Codegen script: `live_contentops/dispatch_outbox_dry_run_v5_adapter_codegen_v6.py`
* Committed JSON Packet: `docs/automation/V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN/approval_packet_preview_to_dispatch_outbox_dry_run_packet.json`
* Static TS Adapter: `ui/contentops_v5/src/data/dispatchOutboxDryRunAdapter.ts`
* Backend Python Tests: `tests/test_approval_packet_preview_to_dispatch_outbox_dry_run_v6.py`
* Codegen Python Tests: `tests/test_dispatch_outbox_dry_run_v5_adapter_codegen_v6.py`
* UI Guardrail Tests: `tests/test_dispatch_outbox_dry_run_ui_guardrail_v6.py`

## Running Local Verification and Adapter Sync Check
From the repository root, run the status and logic validations:
```bash
python -m pytest tests/test_approval_packet_preview_to_dispatch_outbox_dry_run_v6.py tests/test_dispatch_outbox_dry_run_ui_guardrail_v6.py tests/test_dispatch_outbox_dry_run_v5_adapter_codegen_v6.py
```

Verify adapter code-generation matches the packet content:
```bash
python live_contentops/dispatch_outbox_dry_run_v5_adapter_codegen_v6.py
```
