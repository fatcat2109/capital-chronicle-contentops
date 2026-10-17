# ContentOps BrowserOS Neo Wave 5 Identity Shadow Gate — 2026-10-17

Status: `IMPLEMENTED / INJECTED_UI_PROVEN / DISABLED_BY_DEFAULT / ACCOUNT_IDENTITY_NOT_AUTHORITY`

## Scope

This slice adds a read-only visible-UI identity shadow evaluator to the existing scheduled dry-run
owner. It consumes only caller-supplied account/destination labels and snapshot text. It never
opens or selects a browser account, reads cookies/storage/tokens, logs in, clicks, types, publishes,
comments, starts the scheduler, writes the durable store, or changes account/session state.

The optional gate is disabled by default and normal scheduler/publication behavior is unchanged.
Any result other than an exact visible-label match remains unproven and cannot grant account,
publication, numeric, factual, or runtime authority.

## Contract

- `CONFIRMED`: one exact visible account label and one exact visible destination match the expected
  values; `account_identity_proven=true` is limited to this visible shadow evidence.
- `AMBIGUOUS`: conflicting visible labels or an expected-label mismatch.
- `MISSING`: required expected/observed labels are absent.
- `HUMAN_REQUIRED`: visible UI/snapshot text is truncated or otherwise incomplete.
- `DISABLED_BY_DEFAULT`: no UI metadata or snapshot is inspected.
- Every evaluated result includes SHA-256 hashes for redacted visible metadata, redacted snapshot
  text, and the combined identity evidence. Credential/session fields are replaced before hashing;
  no secret value is returned.

## Focused proof

```powershell
python -m pytest -q tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py
```

The proof covers exact identity, mismatch, missing/truncated UI, credential redaction, disabled
zero-inspection behavior, and inclusion in the scheduled dry-run receipt. All inputs are injected
fixtures; no live BrowserOS session is used.

## Integration boundary

- Implemented/tested: branch only, from `master` head `3b8391e070874517a98f85a23edfe734775d2a6a`.
- Integrated/merged/deployed/live-published: not yet.
- The gate remains opt-in and shadow-only; scheduler, store, runtime, provider/model, account
  selection, session state, and publication ownership remain unchanged.

## Wave 6 destination readback shadow extension

The existing scheduled dry-run owner now accepts one optional injected canonical destination
readback shadow. For the named Substack destination it compares platform/kind/binding, canonical
public object ID/URL, payload hash, readback hash, and `RECONCILED_CONFIRMED` state. It returns
`CONFIRMED_SHADOW`, `MISMATCH`, `MISSING`, `HUMAN_REQUIRED`, `UNKNOWN_WRITE`, or
`DISABLED_BY_DEFAULT` and hashes only redacted evidence. `UNKNOWN_WRITE` remains stop-retry-readback-
reconcile. This extension does not claim a live write, account authority, publication success, or
runtime readiness and does not change `DurablePublicationCoordinator` ownership.

## End-to-end hybrid pipeline shadow packet

The stacked review packet now composes injected results from the existing owners into one
`hybrid_pipeline_shadow.v1` receipt: HTTP/official-API-first source recovery, BrowserOS preflight,
visible identity, canonical Substack destination readback, and Chrome CDP 9222 ingestion-only
boundary. It requires the existing shared request budget/one recovery attempt and exact
`RECONCILED_CONFIRMED` destination evidence; `UNKNOWN_WRITE`, missing, mismatch, or human-required
states remain fail-closed. The packet is shadow-only and does not start scheduler/runtime, touch the
store, call a model/provider, select an account, or publish.
