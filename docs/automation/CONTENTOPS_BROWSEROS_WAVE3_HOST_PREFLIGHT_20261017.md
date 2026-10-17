# ContentOps BrowserOS Neo Wave 3 Host Preflight — 2026-10-17

Status: `PASS / HEALTHY / READ_ONLY / TIME_QUALIFIED / NO_PUBLICATION_AUTHORITY`

## Scope and boundary

This receipt records one bounded local BrowserOS Neo adapter preflight from the Wave 3 dry-run
head. It is host/runtime evidence for the adapter at the observed time. It does not establish
the current account or browser profile identity, destination login/readiness, scheduler or
ContentOps runtime health, provider/model readiness, or publication authority. It does not enable
the scheduler/runtime, touch the durable store, call a provider/model, inspect credentials or
session material, or perform a public write.

`BrowserOSNeoReadOnlyPreflight` remains the only owner of this lifecycle check. The existing
Simple scheduler, evidence resolver, BrowserOS callback, and publication boundaries are unchanged.

## Exact command and observation

Observed at `2026-10-17T07:09:22Z` from branch `codex/browseros-wave3-host-proof`, based on PR64
head `9e283d65ba1561a026861fa8ea4d0c8e69ba7aa9`:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -c "import json; from live_contentops.browser_rendered_source_recovery_v1 import BrowserOSNeoReadOnlyPreflight; print(json.dumps(BrowserOSNeoReadOnlyPreflight().run(auto_open=True, reconnect_once=True), sort_keys=True))"
```

Observed structured result:

```json
{
  "allowed_tools": ["name_session", "read", "tabs"],
  "auto_open_attempts": 0,
  "auto_open_requested": true,
  "credential_or_session_material_read": false,
  "endpoint": "http://127.0.0.1:9010/mcp",
  "fail_closed_on_unavailable": true,
  "failure_class": null,
  "launcher_attempts": 0,
  "lifecycle_state": "HEALTHY",
  "mcp_protocol_version": "2025-06-18",
  "model_call_count": 0,
  "official_launcher_invoked": false,
  "official_launcher_kind": "WINDOWS_SHORTCUT_LNK",
  "official_launcher_path": "C:\\Users\\bullw\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\BrowserOS neo.lnk",
  "public_write_performed": false,
  "publication_authority": false,
  "read_only": true,
  "reconnect_attempts": 0,
  "schema_version": "contentops.browseros_neo.read_only_preflight.v1",
  "server_name": "browseros-neo",
  "server_version": "0.0.72",
  "status": "PASS"
}
```

The healthy initial check avoided the official shortcut (`official_launcher_invoked=false`,
`launcher_attempts=0`) and required no reconnect. The adapter proved only the loopback server
identity/protocol and the read-only tool allowlist at this time. A later unavailable result or
identity change remains possible; do not promote this receipt to a live account, publication, or
unattended-runtime claim.

## Verification and integration state

- Implemented: durable current-epoch host readback receipt only.
- Tested: the exact preflight command above returned `PASS` with the fields shown verbatim.
- Integrated/merged/deployed/live-published: not yet; this docs-only branch is stacked on PR64.
- No scheduler/runtime/publication/database mutation occurred.
