# Institutional Shell View Model Source of Truth and Drift Guard (After 0172)

Task: TASK_CONTENTOPS_0172_INSTITUTIONAL_SHELL_VIEW_MODEL_SOURCE_OF_TRUTH_AND_DRIFT_GUARD_V0
Mode: static / local-only / deterministic. No network, env, credential, browser,
Antigravity, screenshot, export, or Project Sources refresh.

## Baseline

- Required starting baseline: 667f0ad.
- Prior accepted task: 0171 static polish + UI consistency hardening.
- Prior classification: PASS.

## Problem

0170 and 0171 fixed the *presentation* of stale metadata, but the underlying
risk remained: institutional shell global state and per-screen metadata are
hand-edited static fixture labels, easy to drift back into an inconsistent or
stale state. This task adds the first source-of-truth + drift-guard layer.

## Source-of-truth model

`live_contentops/institutional_shell_view_model_source_of_truth.py` is the
canonical, deterministic, local-only model. It distinguishes:

1. last accepted/audited baseline entering this task (667f0ad)
2. current task gate label under implementation
3. historical per-screen implementation provenance (labeled historical)
4. browser QA evidence provenance (0169 PASS_WITH_MINOR_EVIDENCE_GAP, reconciled
   by 0170)
5. current safety posture (all live/forbidden capabilities OFF)
6. future-only / live-disabled platform status
7. next-task discipline

### Baseline honesty rule

The model records `required_starting_baseline = 667f0ad` and
`last_accepted_baseline_entering_task = 667f0ad`. It does NOT claim the
post-task HEAD as accepted before commit + audit. `baseline_semantics`
explicitly states the post-task HEAD is unknown until commit + audit.

## Drift guard

`run_drift_checks()` deterministically inspects the static shell assets and
fails on any of:

- `accepted_head_short: "15b87ff"` presented as current
- `current_gate: "telegram_official_docs..."` presented as current
- missing per-screen historical labels ("Screen Baseline (historical)",
  "Screen Gate (historical)") in `app.js`
- missing fixture historical provenance notes
  (`historical_view_model_baseline`, `historical_gate_note`)
- missing browser QA evidence provenance (`latest_browser_qa_evidence`, `0169`)
- incomplete 12-screen inventory
- `live_posting_enabled_now: true` or `platform_api_allowed_now: true` in fixture

On the current accepted assets the drift guard returns zero findings.

## Contract / Validator

- Module: `live_contentops/institutional_shell_view_model_source_of_truth.py`
- Schema: `schemas/institutional_shell_view_model_source_of_truth_packet.schema.json`
- CLI: `python -m live_contentops.cli pre-alpha-institutional-shell-view-model-source-of-truth-summary`
- Tests: `tests/test_institutional_shell_view_model_source_of_truth.py`

The validator fails on any forbidden flag true, required flag not true, stale
header regression, screen count != 12, drift findings present, secrets visible,
forbidden controls active, kill switch not active, or packet_status pass with
errors.

## Manual update discipline

When a future task changes the accepted baseline or current gate, update the
constants in the source-of-truth module and the fixture together. The drift
guard test will fail if the fixture presents stale values as current or drops
historical/browser-QA provenance, preventing silent regression.

## Next Allowed Action

AWAIT OPERATOR/CHATGPT_AUDIT_OF_0172_EVIDENCE_BEFORE_ANY_NEXT_TASK
