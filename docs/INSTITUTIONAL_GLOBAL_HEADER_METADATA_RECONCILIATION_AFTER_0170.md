# Institutional Global Header Metadata Reconciliation (After 0170)

Task label: TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master

This doc records the institutional shell global-header / current-state metadata
reconciliation performed in 0170. No browser, Antigravity, screenshots, exports,
env reads, API calls, or Project Sources refresh occurred.

## Problem Found In 0169 Screenshot Review

The institutional shell global top status/header displayed stale metadata:
- accepted HEAD `15b87ff` (this was the 0159 view-model baseline, not current)
- current gate `telegram_official_docs_credential_validation_gate` (a prior gate)

The accepted code baseline after 0168 is `444ef2c`. Presenting stale values as the
current global state is operator-confusing, though not a live/safety failure (no
forbidden controls or secrets were visible).

## Reconciliation Applied

In `ui/institutional_shell/fixture_data.js` global_state:
- `accepted_head_short` updated from `15b87ff` to `444ef2c` (current global baseline).
- Added `accepted_head_note` clarifying it is the latest accepted code baseline after 0168.
- Added `historical_view_model_baseline` labeling `15b87ff` as 0159 historical lineage.
- `current_gate` updated from the stale Telegram docs gate to
  `0170 browser qa evidence + metadata reconciliation`.
- Added `historical_gate_note` labeling the Telegram official docs gate as historical.
- Added `latest_browser_qa_evidence` = `0169 PASS_WITH_MINOR_EVIDENCE_GAP`.
- `next_allowed_action` rewritten as a human-readable display label plus a
  machine-readable `next_allowed_action_code` field preserving the full ID.

## Metadata Semantics (Now Distinguished)

- Latest accepted code baseline before 0170: `444ef2c`.
- Latest browser QA evidence: `0169 PASS_WITH_MINOR_EVIDENCE_GAP`.
- Global current evidence state after 0169: reconciled to current baseline + gate.
- Historical per-screen implementation gates: e.g. Command Center detail card retains
  `1c03ca0` and the commit/evidence timelines retain `15b87ff` (0159). These are
  labeled historical per-screen / lineage provenance, NOT current global state.
- Future browser/Antigravity tasks require explicit operator/ChatGPT GO.
- Live posting / platform API / scheduler remain disabled. Kill switch remains active.

## Historical Per-Screen Metadata Policy

Older per-screen HEADs that remain in screen detail cards and the Evidence Vault
commit/evidence timelines are intentionally retained as historical provenance:
- They reflect when each screen was implemented or accepted.
- They must not be read as the current global repo baseline.
- The global header is the single source of current-state truth and now shows
  `444ef2c` plus the 0170 gate.

## Long-Label Readability

The next-action label previously could wrap awkwardly (e.g.
`...BEFOR E_ANY_NEXT_TASK`). 0170 uses a human-readable display label with spaces in
`next_allowed_action` and preserves the full machine-readable ID in
`next_allowed_action_code`.

## Validation

- Schema: `schemas/institutional_browser_qa_evidence_metadata_reconciliation_packet.schema.json`
- Validator/summary: `live_contentops/institutional_browser_qa_evidence_metadata_reconciliation.py`
- CLI: `python -m live_contentops.cli pre-alpha-institutional-browser-qa-evidence-metadata-reconciliation-summary`
- Tests: `tests/test_institutional_browser_qa_evidence_metadata_reconciliation.py`
