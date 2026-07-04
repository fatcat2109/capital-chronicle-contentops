# Mock Adapter Publish Flow and Metrics Capture - After TASK_CONTENTOPS_0080

LOCAL ONLY | ADVISORY ONLY | MOCK TRANSPORT ONLY | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK
NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING | NO LIVE METRICS
HUMAN (OPERATOR) APPROVAL REQUIRED

This layer wires the automation-readiness rails end to end against MOCK
transports only. It proves the publish sequence can be ordered safely while the
train stays parked. Nothing posts, schedules, scrapes, or fetches.

## End-to-end flow
1. Grounded research brief (validated by 0076).
2. Draft review packet (validated by 0077).
3. Canonical social post (0078 shape).
4. Platform dry-run payload via `platform_adapter_contracts.render_platform_payload`.
5. Approval ledger record validated (0079).
6. Publish kill-switch state validated (0079).
7. Mock publish result produced ONLY if `can_proceed_to_mock_publish` allows
   (approval == operator_approved_for_mock_publish AND kill switch permits mock).
8. Mock post URL (clearly-fake `mock://` scheme, not a real endpoint).
9. Simulated/manual metrics placeholder (never fetched or scraped).
10. Redacted audit event (0079 redaction logic).

## Components
- `schemas/mock_publish_request.schema.json`
- `schemas/mock_publish_result.schema.json`
- `schemas/mock_metrics_placeholder.schema.json`
- `schemas/mock_publish_flow_run.schema.json`
- `live_contentops/mock_publish_flow.py`
- `fixtures/mock_publish_flow/*.json`

## Fail-closed semantics
- Live publishing is impossible. Every request/result/audit carries
  `live_posting_enabled=false`; `can_proceed_to_live_publish_later(...)` always
  denies.
- Mock publish is `blocked` when approval is missing, revoked, blocked, the wrong
  state, the kill switch blocks mock, or the dry-run render fails.
- Metrics are `simulated_placeholder`/`manual_placeholder` only;
  `fetched_from_platform=false`, `scraped=false`, `network_accessed=false`,
  `values=null`. No performance inference.
- Mock URLs use the `mock://` scheme; never real http(s) platform URLs and never
  intended for verification.
- All outputs are `dry_run=true`, `mock_only=true`, `not_public_postable=true`,
  `credential_accessed=false`, `network_accessed=false`,
  `requires_operator_approval=true`. Nothing is promoted to public-ready.

## Platform behavior note
With a text-only canonical post, text-capable platforms (x, linkedin, telegram,
facebook_page) mock-publish; media-required platforms (instagram, tiktok) block
in the dry-run render. This is the 0078 adapter contract behaving as designed,
not a live-capability difference.

## Boundary restatement
Mock orchestration only. No live posting, no platform/provider/LLM/search API
clients, no credentials, no network, no scheduling, no replies/DMs, no scraping.
Official platform-doc verification is deferred to 0081. Artifact-backed Capital
Chronicle content remains blocked until real approved alpha artifacts exist.
