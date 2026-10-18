# ContentOps Multi-Window Newsroom Cycle Consumer — 2026-10-18

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

ContentOps had the portable host receipt, post-merge replay consumer, V3/editorial shadow path,
and scheduled shadow owner, but no consumer that preserved Main's three-window intelligence bundle
as one newsroom decision with exact, proxy/context, contradiction, duplicate, freshness, and
authority boundaries.

## AFTER

`multi_window_newsroom_cycle_consumer_v1.py` consumes the exact top-level contract
`CapitalChronicleMultiWindowIntelligenceCycleBundleV1` and emits
`contentops.multi_window_newsroom_cycle_receipt.v1`.

The consumer validates canonical JSON/self-hash, parent Goal 9 receipt hash, Main/ContentOps
source heads, clocks/freshness, rights/redaction, proof layers, authority flags, and zero-effect
counters. It requires exactly `CURRENT_REAL`, `RECENT_REPLAY`, and `PROXY_CONTEXT` windows.

Exact eligible claims can be selected. Proxy/context claims remain qualitative context. Duplicate
claims are collapsed, contradictions are quarantined, stale/future/rights-invalid/authority/
UNKNOWN_WRITE inputs fail closed, and only the existing scheduled shadow owner is called for a
healthy synthetic cycle. That owner returns the canonical article/package/destination shadow
receipt with exactly eight derivative destinations and interruption/resume state.

## Current-real preservation

The current-real fixture carries the audited Goal 8 host facts:

- BrowserOS MCP read-only observation `PASS`;
- CDP 9222 and 9223 `UNAVAILABLE`;
- all three scheduled tasks `Disabled`;
- account and destination identity `MISSING`;
- SQLite read-only integrity `ok` and zero-effect counters;
- runtime/public proof false and classification `NOT_VERIFIED`.

It remains blocked from composition with `current_real_host_boundary_not_verified`.

## Fixture matrix

- Bundle fixtures: [multi_window_newsroom_cycle_bundles_v1.json](../../tests/fixtures/multi_window_newsroom_cycle_bundles_v1.json)
- Durable receipts: [multi_window_newsroom_cycle_receipts_v1.json](../../tests/fixtures/multi_window_newsroom_cycle_receipts_v1.json)

Cases: `current_real`, `healthy`, `duplicate_collapse`, `contradiction_quarantine`, `proxy_only`,
`stale`, `future`, `tampered`, `authority_flag`, `unknown_write`, `interruption_resume`.

## REUSED / CHANGED

- Reused: Goal 8 portable/post-merge receipts, scheduled shadow owner, V3/editorial/destination
  shadow seams, eight-destination registry, and zero-effect boundaries.
- Changed: one pure multi-window consumer/composer, compact bundle/receipt fixtures, focused tests,
  and this durable handoff.
- Main, database files, scheduler/status owners, publication authority, and dirty canonical
  ContentOps checkout were not edited.

## EVIDENCE

Focused Goal 10 tests cover all eleven cases and deterministic receipt hashes. Healthy synthetic
reaches `SHADOW_CONFIRMED` only through the injected scheduled shadow owner; runtime/public proof
remain false. Current-real remains `NOT_VERIFIED / BLOCKED`.

## BLOCKERS

No current host/runtime/public promotion is claimed. Main multi-window producer remains
`FIXTURE_ONLY` on this branch; the receipt binds Main/ContentOps heads and parent Goal 9 hash so a
later merged producer can be substituted without changing semantics.

## Exactly one NEXT

Have Main provide the merged multi-window bundle with the same contract and parent receipt binding;
consume it through this seam and retain the resulting receipt as shadow-only evidence.
