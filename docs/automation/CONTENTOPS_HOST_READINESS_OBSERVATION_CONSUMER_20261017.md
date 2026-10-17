# ContentOps Current Host Readiness Observation Consumer — 2026-10-17

Status: `IMPLEMENTED / MATRIX_PROVEN / READ_ONLY / FAIL_CLOSED_ON_MISSING_IDENTITY`

## BEFORE

ContentOps had separate BrowserOS preflight, visible identity, destination readback, scheduler
dry-run, hybrid shadow, and Main handoff consumers. Their results were not one immutable readiness
receipt carrying the merged Main packet through the shadow path while separating host observation,
runtime proof, and public proof.

## AFTER

`live_contentops/host_readiness_observation_consumer_v1.py` now consumes one bounded observation
and the existing self-contained Main bridge, reuses the existing identity/readback gates, and
attaches a hashed readiness receipt to the existing Main/editorial/scheduled shadow result.
It records endpoint/server/protocol/tool allowlist, X CDP 9222, publication CDP 9223, exact task
states, bounded process-filter results, visible identity, destination shadow, packet/receipt hashes,
store integrity/counts, scheduler/store/public-write counters, and explicit evidence taxonomy.

If BrowserOS evidence is absent, an injected existing preflight runner is called at most once with
`auto_open=True,reconnect_once=True`; the runner remains responsible for the installed official
`BrowserOS neo.lnk` shortcut and one reconnect. This consumer never launches an executable directly.

## Fixture matrix

Fixture: [host_readiness_observation_matrix_v1.json](../../tests/fixtures/host_readiness_observation_matrix_v1.json)

- `healthy`: `HOST_OBSERVED`; BrowserOS PASS, both CDP boundaries read-only reachable in the
  fixture, exact three disabled tasks, identity `CONFIRMED`, destination `CONFIRMED_SHADOW`,
  `RUNTIME_PROVEN=false`, `PUBLICLY_PROVEN=false`.
- `unavailable`: `FAIL_CLOSED / NOT_VERIFIED`; BrowserOS/CDP/scheduler/process evidence explicitly
  unavailable and visible identity/destination explicitly missing.
- `ambiguous`: `AMBIGUOUS`; visible identity has multiple profiles and destination readback is
  human-required; neither runtime nor public proof is produced.

Every matrix row feeds the same merged Main packet through the existing consumer/editorial/package/
scheduled-shadow path. The shadow path remains `SHADOW_REVIEW_READY` / `SHADOW_CONFIRMED` even when
readiness is fail-closed; no analytical authority changes.

## Current bounded host observation

Observation ID: `host-observation-20261017-134332z` at `2026-10-17T13:43:32Z`.

- BrowserOS MCP: `PASS`; endpoint `http://127.0.0.1:9010/mcp`; server `browseros-neo` `0.0.72`;
  protocol `2025-06-18`; tools exactly `name_session`, `read`, `tabs`; read-only; no shortcut
  launch was needed; no credential/session material read.
- X CDP 9222: `UNAVAILABLE` (`TaskCanceledException`); ingestion-only boundary retained.
- Publication CDP 9223: `UNAVAILABLE` (`TaskCanceledException`); publishing/readback boundary
  retained.
- Exact Windows tasks: all three `Disabled` / state value `1`.
- Bounded process filter (`ContentOps`, `python`, `node`, `msedge`): `113` matches, names
  `msedgewebview2`, `node`, `node_repl`, `pythonw`; this does not establish ownership.
- SQLite: read-only `PRAGMA integrity_check=ok`, foreign-key violations `0`; counts were
  `destination_readiness=9`, `incidents=36`, `outbox_messages=83`, `platform_dispatches=58`,
  `readbacks=85`, `reconciliations=58`, `work_items=92`; no readback text contained
  `UNKNOWN_WRITE`.
- Visible account/destination identity: `MISSING`; destination shadow: `MISSING`.
- Current readiness result: `FAIL_CLOSED / NOT_VERIFIED`; `HOST_OBSERVED=false` for the complete
  readiness claim, `RUNTIME_PROVEN=false`, `PUBLICLY_PROVEN=false`.

## Hashes and counters

- Main packet logical hash: `c496bb5135106202a577d167a4879ab013ae695afa537e472bee14843b5139e8`
- V3 packet hash: `1f035bfc04210f03aff096aa7149b2a2f9dd6ea5ba710fce19365cc947b95d42`
- Existing shadow receipt: `826b54643edabcefe03ace212b8e9da51920d70624fe90d340819296d1d726bb`
- Current readiness receipt: `dd3488d2bf33c4599418f85ea7bb83412d3acca0344a1e6c6ef9be6a5eed2220`
- Healthy fixture readiness receipt: `fcdea7d8725f316d2dd9f764a4cd2700315d036272b30a7af0d358ad3c76148b`
- Unavailable fixture readiness receipt: `d2f3d3f2602dab96c2aa8140f826b875c312e57255ea7066fe41729104fc6ebb`
- Ambiguous fixture readiness receipt: `80dffb71b9e75f35f676b68a9266282730233871275dd83d9f5d3318a50142c9`

All counters remain zero: scheduler started, durable-store writes, database mutation,
model/provider calls, browser actions, public writes, and publication authority.

## Reused and changed

- Reused: `main_analysis_handoff_consumer_v1`, `BrowserOSNeoReadOnlyPreflight`,
  `browseros_identity_shadow_gate_v1`, `destination_readback_shadow_gate_v1`,
  `scheduled_shadow_production_day_v1`, the existing dual-lane/editorial/package owners, and
  the existing destination registry.
- Changed: one observation consumer, one healthy/unavailable/ambiguous fixture matrix, focused
  taxonomy/hash regressions, and this receipt. No second scheduler, publisher, store, destination
  registry, analyzer, or status ledger was created.

## Verification

Focused existing and new set: `95 passed`:

```powershell
python -m pytest -q tests/test_host_readiness_observation_consumer_v1.py tests/test_main_analysis_handoff_consumer_v1.py tests/test_dual_lane_core_v0_shadow_newsroom_v1.py tests/test_scheduled_shadow_production_day_v1.py tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py tests/test_browser_rendered_source_recovery_v1.py
```

Ruff, `py_compile`, and `git diff --check` passed. The current BrowserOS bounded preflight also
returned `PASS` through the existing official MCP/shortcut owner; no account or destination
identity was inferred from that result.

## Closed cells and blockers

- Closed: observation receipt schema, exact hashes, BrowserOS lifecycle contract, tool allowlist,
  CDP role separation, task/process/store counters, identity/readback taxonomy, stale/unavailable/
  ambiguous fail-closed states, Main packet shadow attachment, and proof-layer separation.
- Blockers retained: current visible account/destination identity is missing; CDP 9222 and 9223
  were unavailable; all exact scheduler tasks are disabled; runtime and public proof remain false.

## Exactly one NEXT

Run one owner-authorized, read-only identity observation at the exact destination boundary when
fresh current-host evidence is required; stop on ambiguity, stale evidence, unavailable boundary,
or `UNKNOWN_WRITE`.
