# TASK_CONTENTOPS_0080_LOCAL_MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_DRY_RUN_V0

## Task scope
Wire the local automation-readiness flow end to end against MOCK transports only:
grounded research brief -> draft review packet -> canonical social post ->
platform dry-run payload -> approval check -> kill-switch check -> mock publish
result -> mock post URL -> simulated/manual metrics placeholder -> redacted
audit event. No real platform API clients, credentials, network, scheduling,
scraping, replies/DMs, or live posting.

## Files created/changed
- Created: schemas/mock_publish_request.schema.json
- Created: schemas/mock_publish_result.schema.json
- Created: schemas/mock_metrics_placeholder.schema.json
- Created: schemas/mock_publish_flow_run.schema.json
- Created: live_contentops/mock_publish_flow.py
- Created: fixtures/mock_publish_flow/valid_mock_flow_input.json
- Created: fixtures/mock_publish_flow/invalid_missing_approval_blocks.json
- Created: fixtures/mock_publish_flow/invalid_kill_switch_blocks.json
- Created: fixtures/mock_publish_flow/invalid_live_enabled_rejected.json
- Created: fixtures/mock_publish_flow/invalid_secret_in_audit_rejected.json
- Created: tests/test_mock_publish_flow.py
- Created: docs/MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_AFTER_0080.md
- Created: docs/TASK_CONTENTOPS_0080_LOCAL_MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_DRY_RUN_V0.md (this report)

Note: the originally-suggested fixture
`valid_all_platforms_mock_flow_result.json` was not committed as a static file
because the result is produced deterministically by the flow and asserted in
tests; a static copy would only risk drift. The valid input fixture is included.

## What it does
- Reuses platform_adapter_contracts.render_platform_payload (0078) and
  approval_audit_contracts (0079) gate + redaction logic.
- run_mock_publish_for_platform / run_mock_publish_flow orchestrate all six
  platforms, failing closed per platform.
- Mock publish proceeds only when can_proceed_to_mock_publish allows; otherwise
  status="blocked" with explicit blocking_errors.
- Mock URLs use the mock:// scheme; metrics are simulated/manual placeholders
  only; audit events are redacted and validated.

## What remains disabled
Live posting; platform/provider/LLM/search API clients; credentials/env reads;
network; scheduling; autonomous replies/DMs; scraping; live metrics; public-
postable/publish-ready content; real alpha artifact access; Capital Chronicle
core repo reads/writes.

## Validation run
- python -m pytest -q: 439 passed (was 426; +13 new).
- python -m pytest -q tests/test_mock_publish_flow.py: 13 passed.
- alpha-wait-state-summary: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS;
  public_content_allowed_now=false (wait-state preserved).
- git diff --check: clean.
- Suspicious scan over changed files: only $schema JSON-Schema declarations and
  a test assertion that mock URLs are NOT http(s). No functional network/
  credential/scheduler/SDK code (BENIGN_GUARDRAIL_TEXT).

## Mock flow results for all six platforms (text-only valid post)
- mock_published: x, linkedin, telegram, facebook_page
- blocked (media required by 0078 contract): instagram, tiktok
- With approval missing or default kill switch: all six blocked.

## Next task
TASK_CONTENTOPS_0081_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0
