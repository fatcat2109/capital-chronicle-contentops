# Operator Runbook — X CDP Exact Live-Click Registry Reconciliation

## Purpose

Use this runbook after an exact live-click execution packet records an operator-confirmed X status URL and matching payload hash. The reconciliation step converts that local evidence into an append-ready publication registry row.

## Command

```powershell
python -m live_contentops.x_cdp_exact_live_click_registry_reconciliation_v6 --dry-run --fixture-bundle --write-evidence docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_REGISTRY_RECONCILIATION/task_contentops_v6_x_cdp_exact_live_click_registry_reconciliation_evidence.json
```

## Optional Local Registry Append

Only use `--append-registry` with an explicit reviewed registry path after confirming the evidence packet is correct:

```powershell
python -m live_contentops.x_cdp_exact_live_click_registry_reconciliation_v6 --dry-run --append-registry --registry-path docs/automation/PUBLICATION_IDENTITY_REGISTRY/platform_publication_identity_registry.jsonl
```

## Stop Conditions

Stop if any of these fail:

- execution status is not `EXECUTED_WITH_CAPTURED_PUBLIC_URL`;
- `registry_append_ready` is not true;
- `publication_registry_record_appended` is not false;
- captured URL is not an X/Twitter status URL;
- payload hash or operator-confirmed payload hash mismatches;
- operator account/destination hash is absent;
- browser/CDP/session/API/network/provider/public-fetch flags are not false.

## Non-Claims

This task does not verify that X hosts the URL. It does not open the browser, query X, read session state, or perform a live write.
