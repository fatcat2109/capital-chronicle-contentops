# Platform Adapter Contracts and Dry-Run Renderer - After TASK_CONTENTOPS_0078

LOCAL ONLY | ADVISORY ONLY | DRY-RUN ONLY | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK | NO SCHEDULING
NO REPLIES/DMS | NO SCRAPING | HUMAN (OPERATOR) APPROVAL REQUIRED

This is automation READINESS only. It maps a valid review-only canonical social
post into deterministic per-platform DRY-RUN payload previews. It never posts,
schedules, replies, DMs, scrapes, calls a platform/provider API, reads
credentials, or marks anything publish-ready/public-postable.

## Important: limits are placeholders, not verified truth
All platform text/media limits in the capability registry are CONSERVATIVE LOCAL
PLACEHOLDERS, recorded as
`constraint_source = "local_placeholder_until_0081_official_docs_verification"`.
Official platform docs verification is a later task (0081). Nothing here should
be treated as verified official platform truth.

## Components
- `schemas/canonical_social_post.schema.json` - canonical social post contract.
- `schemas/platform_dry_run_payload.schema.json` - dry-run payload preview contract.
- `live_contentops/platform_adapter_contracts.py` - registry + validator + renderer.
- `fixtures/platform_dry_runs/*.json` - one valid and three invalid fixtures.

## Canonical social post (input)
Required fields include `post_id`, `source_draft_packet_id`, `lane` (must be
`pre_alpha_general_process`), `content_type`, `subtype`, `title`, `body`,
`source_references_used`, `safety_flags`, `allowed_output_use`, `approval_state`
(only `operator_review_required` or `platform_dry_run_ready`; never publish-ready),
`public_postable=false`, `live_posting_enabled=false`.

`safety_flags` must keep `public_postable`, `live_posting_enabled`,
`artifact_backed` false and `no_financial_advice`, `no_signal_language`,
`no_execution_language` true.

## Platform capability registry
Six platforms: `x`, `linkedin`, `telegram`, `facebook_page`, `instagram`,
`tiktok`. Each entry records supported text modes, supported media types, a
placeholder text-length policy, media requirements, and hard safety posture:
`live_api_status="disabled"`, `credential_required_for_live=true`,
`credential_read_allowed_now=false`, `scheduling_allowed_now=false`,
`replies_or_dms_allowed_now=false`, `scraping_allowed_now=false`,
`official_docs_verified=false`.

Instagram and TikTok require media (text-only posts fail closed there).

## Dry-run renderer (output)
For each platform the renderer returns a payload with `dry_run=true`,
`platform_id`, `post_id`, `payload_preview`, `warnings`, `blocking_errors`,
`render_status` (`rendered` or `blocked`), `constraint_source`,
`requires_operator_approval=true`, `not_public_postable=true`,
`live_posting_enabled=false`, `credential_accessed=false`,
`network_accessed=false`, and a `mock_endpoint_name` (mock URI only).

## Fail-closed behavior
A payload is `blocked` when any of these hold:
- the canonical post fails safety validation (lane, approval state, safety flags,
  forbidden market/signal language, implied alpha output);
- the post carries media unsupported by that platform;
- a media-required platform receives a text-only post;
- the platform id is unknown.

Over-length text is a warning, not a block (length limits are placeholders).

## Boundary restatement
This task adds adapter CONTRACTS and a dry-run renderer only. No live posting,
no platform/provider API clients, no credentials, no network, no scheduling, no
replies/DMs, no scraping. Approval is required before any later publish step,
which is out of scope here. Artifact-backed Capital Chronicle content remains
blocked until real approved alpha artifacts exist.
