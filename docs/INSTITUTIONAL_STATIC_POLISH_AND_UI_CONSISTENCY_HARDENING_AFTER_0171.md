# Institutional Static Polish and UI Consistency Hardening (After 0171)

Task: TASK_CONTENTOPS_0171_INSTITUTIONAL_STATIC_POLISH_AND_UI_CONSISTENCY_HARDENING_V0
Mode: static / local-only / fixture-driven. No live capability introduced.

## Baseline

- Required starting baseline: 063b0bc.
- Prior task: 0170 browser QA evidence + global header metadata reconciliation.
- Prior classification: PASS_WITH_PROCESS_CAVEAT (0170 started from d3b340f, a
  harmless documentation-only Project Sources bundle refresh descendant). This
  caveat is preserved, not erased.

## Problem Addressed

After 0169/0170 the global header metadata was reconciled, but the per-screen
hero bands still rendered older per-screen HEADs/gates (for example Command
Center "1c03ca0" / "0161 command center screen implementation") using the same
labels as the global header ("Accepted HEAD", "Current gate"). This could read
as current global state.

## Changes Applied

### Global vs historical metadata clarity
- Global status bar continues to read the reconciled `global_state`
  (`accepted_head_short: 444ef2c`, `current_gate: 0170 browser qa evidence +
  metadata reconciliation`). No regression introduced.
- All six per-screen hero bands in `ui/institutional_shell/app.js` now label the
  per-screen values as historical provenance:
  - "Accepted HEAD" -> "Screen Baseline (historical)"
  - "Current gate" -> "Screen Gate (historical)"
- Affected screens: Command Center, Content Studio, Publish Readiness Tower,
  Evidence Vault, Content Calendar, Visual Export.
- The underlying fixture audit strings (per-screen HEADs/gates and
  `next_allowed_action` task labels) are preserved unchanged so existing screen
  tests and evidence lineage remain intact.

### Safety semantics preserved
- Kill switch remains active.
- Live posting / platform API / scheduler / scraping / evidence mutation remain
  disabled.
- Visual Export remains export-preparation-only; Antigravity remains future-only.
- No active publish/schedule/export/API/evidence mutation controls.
- No secrets, raw env paths, raw request URLs, or raw platform responses visible.

## Contract / Validator

- Module: `live_contentops/institutional_static_polish_ui_consistency_hardening.py`
- Schema: `schemas/institutional_static_polish_ui_consistency_hardening_packet.schema.json`
- CLI: `python -m live_contentops.cli pre-alpha-institutional-static-polish-ui-consistency-hardening-summary`
- Tests: `tests/test_institutional_static_polish_ui_consistency_hardening.py`

The validator proves: required starting baseline 063b0bc, prior classification
PASS_WITH_PROCESS_CAVEAT preserved, 12 screens present, current global metadata
consistent (no stale 15b87ff / Telegram docs gate as current), historical
metadata policy present, zero stale-header regressions, zero forbidden active
controls, kill switch active, zero secrets, and packet_status pass only with no
errors.

## Next Allowed Action

AWAIT OPERATOR/CHATGPT_AUDIT_OF_0171_EVIDENCE_BEFORE_PROJECT_SOURCES_REFRESH_OR_ANY_NEXT_TASK
