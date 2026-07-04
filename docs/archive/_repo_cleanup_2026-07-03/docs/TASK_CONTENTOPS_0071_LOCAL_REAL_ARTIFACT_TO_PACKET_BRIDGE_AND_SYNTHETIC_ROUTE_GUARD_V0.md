# TASK_CONTENTOPS_0071_LOCAL_REAL_ARTIFACT_TO_PACKET_BRIDGE_AND_SYNTHETIC_ROUTE_GUARD_V0

## Title & scope
Local-only, fixture-only bridge from real-artifact intake envelopes to the
existing packet/review pipeline, with a synthetic route guard. Determines
whether an intake envelope is eligible to become a local review packet input and
which route it must use. Prevents synthetic/demo/internal/future-placeholder
artifacts from masquerading as real approved Capital Chronicle artifacts.

## Project intent guardrails
Local-first ContentOps control-plane sidecar. Not a live posting engine. Capital
Chronicle artifacts stay authority-bound: approved/exported only, source IDs
required, missing/degraded/proxy data visible, no forecast readiness while
DQR/data sufficiency blocks, market notes show limitations/freshness/educational
posture, and no buy/sell/hold/position-sizing/guaranteed-prediction/execution/
broker/signal-service language.

## What this task built
- `live_contentops/artifact_packet_bridge.py`
  - `build_bridge_record(...)` deterministic route record from intake input.
  - `project_packet_input(...)` safe local packet-candidate projection.
  - `validate_bridge_record(...)` bridge guardrail validation.
  - `build_summary()` CLI summary.
  - internal `_evaluate_synthetic_route_guard` + `_determine_route`.
- `tests/fixtures/editorial/artifact_packet_bridge_input.json` (7 scenarios).
- `tests/test_artifact_packet_bridge.py` (21 tests).
- `live_contentops/cli.py` new `artifact-packet-bridge-summary` command.
- `live_contentops/status.py` next-task pointer advanced to 0072.

## Bridge record contract
bridge_id, intake_id, artifact_id, artifact_family, artifact_type,
artifact_origin, intake_gate_status, bridge_route, bridge_status, route_blockers,
route_warnings, synthetic_route_guard_status, real_artifact_route_allowed,
packet_input_allowed, packet_input_mode, packet_content_type, source_artifact_ids,
source_lineage_refs, limitation_summary, freshness_as_of, dqr_status,
data_sufficiency_status, forecast_readiness_status, proxy_data_status,
missing_data_status, degradation_status, not_public_postable_reason,
local_only=true, advisory_only=true, human_review_required=true,
approval_granted=false, publish_ready=false, provider_call_allowed=false,
search_call_allowed=false, platform_action_allowed=false.

## Supported routes / rules
SYNTHETIC_LOCAL_REVIEW_ROUTE, INTERNAL_TEST_LOCAL_REVIEW_ROUTE,
FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE, APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE,
BLOCKED_ROUTE. Each origin maps only to its route or BLOCKED_ROUTE.
approved_real_artifact route requires approval_source and a non-blocked gate.
No route is public-postable or publish-ready.

## Synthetic route guard
BLOCKS when synthetic/internal/future-placeholder claims approved-real route or
real/source/current authority; claims public/publish-ready; hides origin; drops
not_public_postable_reason; drops DQR/data sufficiency/proxy/missing/degraded
status.

## Packet input projection
Maps a bridge record into a safe local packet candidate: source IDs, lineage,
content type, limitations, freshness, route status, synthetic/real origin, all
safety flags, explicit not-public-postable reason. Never calls LLM/provider/
search, never creates publish-ready content, never grants approval/platform
authority.

## Fixtures
valid_synthetic_product_update -> SYNTHETIC_LOCAL_REVIEW_ROUTE;
future_real_artifact_placeholder -> FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE;
approved_real_artifact_contract_sample -> APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE
(local-review-only, not public postable, explicit fixture disclaimer);
blocked_forecast_readiness_dqr_blocking -> BLOCKED_ROUTE;
blocked_synthetic_claims_approved_real -> BLOCKED_ROUTE;
blocked_market_note_missing_freshness -> BLOCKED_ROUTE;
blocked_forbidden_trading_language -> BLOCKED_ROUTE.

## Verification
- `python -m pytest -q` -> 314 passed.
- `python -m pytest -q tests/test_artifact_packet_bridge.py` -> 21 passed.
- `python -m live_contentops.cli artifact-packet-bridge-summary` ->
  fixture_only=true; requires_real_alpha_artifacts_now=false;
  artifact_packet_bridge_enabled/synthetic_route_guard_enabled/
  human_review_required true; approval_granted/publish_ready/provider/search/
  platform false; all_fixture_outputs_not_public_postable true.

## Risks / warnings
- No real alpha artifacts required or accessed; no Capital Chronicle core repo
  reads/writes. The bridge grants no approval/publish/platform/trading/forecast/
  execution authority.
- No network/provider/LLM/search/platform/credential/scheduling/posting/DM/
  browser capability was introduced.

## Open items
- None blocking. The `.gitignore` working-tree change is operator-owned, was
  not staged/committed/touched.

## Suggested next steps
- TASK_CONTENTOPS_0072_LOCAL_REAL_ARTIFACT_REVIEW_PACKET_FIXTURE_AND_PIPELINE_TRACE_V0
