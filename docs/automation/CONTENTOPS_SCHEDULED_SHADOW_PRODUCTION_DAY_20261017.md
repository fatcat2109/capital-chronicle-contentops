# ContentOps Scheduled Shadow Production Day — 2026-10-17

Status: `IMPLEMENTED / FIXTURE_PROVEN / DISABLED_BY_DEFAULT / NO_LIVE_WRITE`

## Before

Existing ContentOps already had separate bounded seams for HTTP-first/rendered-source recovery,
BrowserOS preflight, visible identity, destination readback, scheduler dry-run and the accepted
Simple-to-`DurablePublicationCoordinator` handoff. No single injected invocation represented one
complete production-day opportunity from source evidence through canonical/derivative package
shadow and interruption recovery.

## After

`run_scheduled_shadow_production_day(...)` composes existing owner contracts into one immutable
receipt. It validates:

- HTTP/API-first source recovery, shared request budget and one BrowserOS recovery attempt;
- BrowserOS read-only preflight, including bounded official shortcut launch/reconnect metadata;
- Chrome CDP 9222 ingestion-only X boundary;
- grounded evidence, report-truth provenance and selected candidate decision;
- one qualified canonical Substack payload with epistemic state;
- exactly eight existing derivative destinations and payload hashes;
- exact canonical destination readback shadow and reconciliation;
- interruption resume without semantic rerun;
- `UNKNOWN_WRITE` stop -> readback -> reconcile semantics.

The invocation is disabled by default and performs no scheduler start, store/database/status write,
model/provider call, browser action, account selection, login, credential/session read, comment or
publication. It returns a SHA-256 immutable receipt hash and explicit fail-closed states.

## Verification

```powershell
python -m pytest -q tests/test_scheduled_shadow_production_day_v1.py tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py
```

Focused proof covers complete cycle success, disabled zero-side-effect behavior, stale/truncated
evidence, resumable interruption, destination mismatch and `UNKNOWN_WRITE`. Existing scheduler,
destination and publication owner regressions remain separate and unchanged.

## Closed cells and evidence

- Closed: source ordering, one recovery attempt, BrowserOS lifecycle metadata, X/CDP boundary,
  grounded editorial decision, canonical payload, eight derivative package set, destination
  identity/readback, immutable receipt, interruption/restart contract and unknown-write stop.
- Evidence: new fixture suite; focused existing regressions; Ruff; compileall; diff check; exact-head
  CI on the parent destination-shadow slice and the pipeline shadow PR.
- Not proven: current live account/session/destination readiness, live public-object state, live
  publication or current scheduler activation.

## Exactly one next phase

Run one owner-authorized, read-only current-host observation at the canonical destination boundary;
stop on identity ambiguity or `UNKNOWN_WRITE`.
