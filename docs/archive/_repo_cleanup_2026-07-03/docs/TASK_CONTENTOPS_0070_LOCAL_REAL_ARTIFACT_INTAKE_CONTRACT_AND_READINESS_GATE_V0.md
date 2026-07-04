# TASK_CONTENTOPS_0070_LOCAL_REAL_ARTIFACT_INTAKE_CONTRACT_AND_READINESS_GATE_V0

## Title & scope
Local-only, fixture-only real-artifact intake contract and readiness gate (v0).
Defines how FUTURE approved Capital Chronicle alpha artifacts will be accepted
into ContentOps once they exist. Requires no real alpha artifacts now; reads and
mutates NO Capital Chronicle core repo. Every fixture/demo/synthetic artifact is
explicitly NOT PUBLIC POSTABLE.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine. Capital
Chronicle artifacts must remain authority-bound: approved/exported only, source
artifact IDs required, missing/degraded/proxy data visible, no forecast
readiness while DQR/data sufficiency blocks, market notes show limitations/
freshness/educational posture, and no buy/sell/hold/position-sizing/guaranteed-
prediction/execution/broker/signal-service language.

## What this task built
- `live_contentops/real_artifact_intake.py`
  - `build_intake_envelope(...)` deterministic intake envelope.
  - `evaluate_readiness_gate(...)` deterministic readiness gate.
  - `build_summary()` CLI summary.
- `tests/fixtures/editorial/real_artifact_intake_input.json` (6 scenarios).
- `tests/test_real_artifact_intake.py` (18 tests).
- `live_contentops/cli.py` new `real-artifact-intake-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0071.

## Intake envelope contract
intake_id, artifact_id, artifact_family, artifact_type, artifact_origin,
artifact_status, approved_for_contentops, approval_source, approval_timestamp,
source_artifact_ids, source_lineage_refs, freshness_as_of, limitation_summary,
data_sufficiency_status, dqr_status, forecast_readiness_status, proxy_data_status,
missing_data_status, degradation_status, educational_general_only,
no_financial_advice, not_public_postable_reason, local_only=true,
advisory_only=true, human_review_required=true, approval_granted=false,
publish_ready=false, provider_call_allowed=false, search_call_allowed=false,
platform_action_allowed=false.

## Supported families / origins
Families: data_sufficiency, forecast_readiness, failure_forensics,
build_in_public, macro_education, product_update, market_note.
Origins: synthetic_fixture, internal_test_fixture, future_real_artifact_placeholder,
approved_real_artifact. The first three are always NOT PUBLIC POSTABLE.

## Readiness gate
gate_status in BLOCKED / NEEDS_OPERATOR_REVIEW / READY_FOR_LOCAL_REVIEW_ONLY,
plus blockers, warnings, required_missing_fields, authority_boundary_flags,
contentops_allowed, not_public_postable, publish_ready=false,
approval_granted=false, platform_action_allowed=false.

## Gate blocks when
artifact_id missing; source_artifact_ids missing for sourced families
(data_sufficiency/forecast_readiness/failure_forensics/market_note);
approved_real_artifact without approval_source; forecast readiness while
DQR/data sufficiency is blocking; missing/proxy/degraded data hidden;
market_note missing freshness/limitations/educational posture; forbidden
finance/execution language; synthetic/internal/placeholder fixture claiming
real/approved/public-ready; or any attempt to set publish_ready/approval_granted/
platform_action_allowed.

## READY_FOR_LOCAL_REVIEW_ONLY only when
required IDs/lineage present, limitations/freshness visible, data sufficiency/
DQR/forecast states explicit, no forbidden finance/execution claims, content
non-public and human-review-required, and no platform/provider/search action.

## Fixtures
valid_synthetic_product_update -> READY_FOR_LOCAL_REVIEW_ONLY (not public
postable); future_real_artifact_placeholder -> NEEDS_OPERATOR_REVIEW;
blocked_market_note_missing_freshness -> BLOCKED;
blocked_forecast_readiness_dqr_blocking -> BLOCKED;
blocked_synthetic_claims_approved_real -> BLOCKED;
blocked_forbidden_trading_language -> BLOCKED.

## Verification
- `python -m pytest -q` -> 293 passed.
- `python -m pytest -q tests/test_real_artifact_intake.py` -> 18 passed.
- `python -m live_contentops.cli real-artifact-intake-summary` ->
  fixture_only=true; requires_real_alpha_artifacts_now=false;
  real_artifact_intake_enabled/readiness_gate_enabled/human_review_required true;
  approval_granted/publish_ready/provider/search/platform false;
  all_fixture_outputs_not_public_postable true.

## Risks / warnings
- No real alpha artifacts required or accessed; no Capital Chronicle core repo
  reads/writes. The gate grants no approval/publish/platform/trading/forecast/
  execution authority.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0071_LOCAL_REAL_ARTIFACT_TO_PACKET_BRIDGE_AND_SYNTHETIC_ROUTE_GUARD_V0
