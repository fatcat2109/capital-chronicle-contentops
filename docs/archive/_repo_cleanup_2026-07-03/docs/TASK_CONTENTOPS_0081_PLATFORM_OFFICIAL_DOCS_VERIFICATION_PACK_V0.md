# TASK_CONTENTOPS_0081_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0

## Task scope
Create a repo-local advisory official-docs verification pack for future platform
integrations: X, LinkedIn, Telegram, Facebook Page, Instagram, and TikTok. This
is advisory/verification preparation only; no runtime platform integrations,
no SDK clients, no credential reads, no network, no posting, no scheduling, no
scraping, no replies/DMs, no metrics fetching.

## Files created/changed
- Created: schemas/platform_official_docs_verification_record.schema.json
- Created: schemas/platform_official_docs_verification_pack.schema.json
- Created: live_contentops/platform_official_docs_verification.py
- Created: fixtures/platform_official_docs/valid_not_verified_pack.json
- Created: fixtures/platform_official_docs/valid_partially_verified_pack_with_operator_supplied_sources.json
- Created: fixtures/platform_official_docs/invalid_live_enabled.json
- Created: fixtures/platform_official_docs/invalid_network_accessed.json
- Created: fixtures/platform_official_docs/invalid_docs_runtime_authority_true.json
- Created: fixtures/platform_official_docs/invalid_verified_without_sources.json
- Created: tests/test_platform_official_docs_verification.py
- Created: docs/PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_AFTER_0081.md
- Created: docs/TASK_CONTENTOPS_0081_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0.md (this report)

## What it does
- Verification records + pack schemas define advisory metadata fields representing what must be verified from official platform documentation (endpoints, media upload chunking limits, dev quotas, OAuth scopes, and rate limits) before any live integration can begin.
- Platform official-docs verification module provides deterministic `validate_record`, `validate_pack`, and `validate_pack_file` validators.
- All safety checks fail closed: validation fails if `docs_runtime_authority`, `network_accessed_by_repo`, `credential_accessed_by_repo`, or `live_posting_enabled` are anything other than `false`.
- Baseline fixture represents zero operator docs supplied (all 6 platforms set to `not_verified` with explicit unknowns and blockers).
- Partially verified fixture represents operator-supplied documentation for Telegram Bot API channel-posting, with all other 5 platforms remaining `not_verified`.

## Strategic status / explicit unknowns per platform
- **X**: `not_verified`. Explicit unknowns: write payload / endpoint structure, oauth2 lifespan, basic tier 24h upload limit pricing, `made_with_ai` tweet labels.
- **LinkedIn**: `not_verified`. Explicit unknowns: member vs organization posting review process, community management permissions, multi-image slides/carousels registering requirements.
- **Telegram**: `partially_verified` (using operator-supplied docs). sendMessage / sendPhoto payload shapes, administrator permission requirements, and bot token security are mapped. Metrics API remains unknown.
- **Facebook Page**: `not_verified`. Explicit unknowns: long-lived page token generation, page managed permissions app review requirement, feed insights fetch schemas.
- **Instagram**: `not_verified`. Explicit unknowns: professional vs business linked account requirements, public unauthenticated media container URL constraints, container publishing rate limits.
- **TikTok**: `not_verified`. Explicit unknowns: video upload chunking init payload, slideshow image count restrictions, sandbox vs production app-audit verification gate.

## What remains disabled
Live posting; platform API clients / transports / SDKs; credential/env reads;
network; scheduling; autonomous replies/DMs; scraping; live metrics; public-
postable/publish-ready content; real alpha artifact access; Capital Chronicle
core repo reads/writes.

## Validation run
- python -m pytest -q: 447 passed (was 439; +8 new).
- python -m pytest -q tests/test_platform_official_docs_verification.py: 8 passed.
- alpha-wait-state-summary: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS;
  public_content_allowed_now=false (wait-state preserved).
- git diff --check: clean.
- Suspicious scan over changed files: clean. No non-schema http(s) links. No
  functional network/credential/scheduler/SDK code.

## Next task
TASK_CONTENTOPS_0082_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0
