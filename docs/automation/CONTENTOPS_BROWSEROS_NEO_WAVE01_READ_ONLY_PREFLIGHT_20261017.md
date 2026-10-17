# ContentOps BrowserOS Neo Wave 0/1 Read-Only Preflight — 2026-10-17

Status: `IMPLEMENTED / BOUNDED / READ_ONLY_TOOL_SESSION_AVAILABLE / ADAPTER_BROWSER_UNAVAILABLE / NO_PUBLICATION_AUTHORITY`

## Scope

This receipt covers one isolated BrowserOS Neo lifecycle seam for source recovery. It does not
enable a scheduler, start ContentOps runtime, touch the durable store, use CDP publication roles,
call a provider/model, download media, publish, or deploy. `DurablePublicationCoordinator` remains
the sole publication owner. V2 remains paused and separate.

## Lifecycle contract

`BrowserOSNeoReadOnlyPreflight` uses the official loopback MCP path:

`health/identity check -> at most one Windows shortcut launch after health failure -> one bounded reconnect/identity check -> PASS or BROWSER_UNAVAILABLE`

- Official launcher: `C:\Users\bullw\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\BrowserOS neo.lnk`.
- The default launcher opens only that `.lnk` through the current interactive user session. It does
  not start a server executable directly and does not use another browser.
- A healthy initial endpoint does not launch the shortcut.
- A failed health check can invoke the shortcut at most once when `auto_open=True`; a second run on
  the same preflight object is blocked by the duplicate-launch guard.
- Reconnect is at most one identity check. Allowed MCP tools remain exactly `name_session`, `tabs`,
  and `read`; the preflight itself does not inspect credentials/session material.
- Any unavailable, identity, timeout, launcher, or reconnect failure returns structured
  `BROWSER_UNAVAILABLE` and remains fail-closed. No fallback browser is attempted.

## Implementation and focused proof

Implementation: `live_contentops/browser_rendered_source_recovery_v1.py`.

Focused command:

```powershell
python -m pytest -q tests/test_browser_rendered_source_recovery_v1.py
```

Observed result: `15 passed`.

The tests cover healthy no-launch, one shortcut launch followed by reconnect, launcher failure,
non-shortcut rejection, duplicate-launch guard, identity/protocol checks, cleanup, mutating-tool
rejection, redirect/access/truncation gates, and existing rendered-source behavior.

## Current host observation — 2026-10-17T06:30:24Z

The bounded local adapter preflight was run with `auto_open=false` so this Builder turn did not
launch a desktop shortcut:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -c "import json; from live_contentops.browser_rendered_source_recovery_v1 import BrowserOSNeoReadOnlyPreflight; print(json.dumps(BrowserOSNeoReadOnlyPreflight().run(auto_open=False, reconnect_once=True), sort_keys=True))"
```

First result (`auto_open=false`, no launcher):

```json
{
  "schema_version": "contentops.browseros_neo.read_only_preflight.v1",
  "status": "BROWSER_UNAVAILABLE",
  "failure_class": "BROWSER_UNAVAILABLE",
  "failure_detail": "browseros_neo_mcp_unavailable",
  "endpoint": "http://127.0.0.1:9010/mcp",
  "official_launcher_path": "C:\\Users\\bullw\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\BrowserOS neo.lnk",
  "official_launcher_invoked": false,
  "launcher_attempts": 0,
  "reconnect_attempts": 0,
  "read_only": true,
  "public_write_performed": false,
  "publication_authority": false
}
```

This is an adapter/loopback availability result only. It does not prove the current account,
profile, destination identity, login state, or publication readiness. A separate BrowserOS tool
smoke in this task successfully named the session, listed existing tabs/windows, and opened then
closed a temporary `about:blank` page; that tool readback did not supply a server version or MCP
protocol identity and is not a publication or account proof.

Because the first bounded check was unavailable, the owner-authorized second step ran exactly once
with `auto_open=true,reconnect_once=true`. It invoked the allowlisted shortcut once, attempted one
MCP reconnect/identity check, and returned:

```json
{
  "schema_version": "contentops.browseros_neo.read_only_preflight.v1",
  "status": "BROWSER_UNAVAILABLE",
  "failure_class": "BROWSER_UNAVAILABLE",
  "failure_history": [
    "browseros_neo_mcp_unavailable",
    "browseros_neo_mcp_unavailable"
  ],
  "official_launcher_invoked": true,
  "launcher_attempts": 1,
  "reconnect_attempts": 1,
  "official_launcher_path": "C:\\Users\\bullw\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\BrowserOS neo.lnk",
  "read_only": true,
  "public_write_performed": false,
  "publication_authority": false
}
```

No BrowserOS server name, server version or MCP protocol identity was proven by either adapter
run. The shortcut invocation therefore proves only that the bounded launcher path was attempted;
it does not prove that BrowserOS started, that a session is connected, or that any account/profile/
destination is ready. No fallback browser was tried.

## Direct BrowserOS Neo tool readback — 2026-10-17T06:41:59Z

The official BrowserOS Neo direct agent tool session became available after the adapter result. A
bounded `tabs list` returned one user tab, `chrome://newtab/ (BrowserOS neo)`, and a page-1
snapshot succeeded. The snapshot showed the BrowserOS Neo cockpit extension page with its Cockpit,
MCP, Skills, Audit, Settings and Diagnostics navigation, plus running-session labels. This is
classified as:

`READ_ONLY_TOOL_SESSION_AVAILABLE`

The direct tool observation does **not** establish the adapter's MCP server name/version or
protocol identity, ContentOps account/profile identity, destination readiness, login state,
scheduler/runtime health, or publication authority. No new tab, shortcut, provider/model call,
credential/session inspection or public action was performed in this readback. The earlier adapter
result at `2026-10-17T06:30:24Z` remains `BROWSER_UNAVAILABLE`; the two evidence classes are kept
separate.

## State and next command

- Implemented: official shortcut path, health-first lifecycle, one-launch/reconnect bounds,
  duplicate-launch guard and `BROWSER_UNAVAILABLE` fail-closed result.
- Tested: `15 passed`; Ruff, compileall and `git diff --check` passed. Host adapter readback at
  `2026-10-17T06:30:24Z`: first health-only check unavailable; one launcher/reconnect attempt also
  unavailable. Direct BrowserOS tool readback at `2026-10-17T06:41:59Z`: read-only session
  available, identity/readiness still not verified.
- Integrated/merged/deployed/live-published: not yet; this branch is the Wave 0/1 implementation
  checkpoint only.
- No runtime/store/scheduler/browser-publication mutation occurred; no provider/model call occurred.

Next bounded command, if a future owner-authorized host observation requires a fresh one-shot check
after the current unavailable result:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -c "import json; from live_contentops.browser_rendered_source_recovery_v1 import BrowserOSNeoReadOnlyPreflight; print(json.dumps(BrowserOSNeoReadOnlyPreflight().run(auto_open=True, reconnect_once=True), sort_keys=True))"
```

If the shortcut or interactive session is unavailable, the command must return
`BROWSER_UNAVAILABLE`; do not fall back to another browser or infer readiness.
