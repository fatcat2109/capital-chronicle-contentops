# TASK_CONTENTOPS_0078_LOCAL_PLATFORM_ADAPTER_CONTRACTS_AND_DRY_RUN_RENDERER_V0

## Task scope
Build local-only platform adapter contracts and a deterministic dry-run renderer
for future supervised social/newsletter publishing readiness. Automation
readiness only: no live posting, platform API clients, credential reads,
scheduling, scraping, replies/DMs, or public-ready content.

## Files created/changed
- Created: schemas/canonical_social_post.schema.json
- Created: schemas/platform_dry_run_payload.schema.json
- Created: live_contentops/platform_adapter_contracts.py (registry + validator + renderer; no external calls)
- Created: fixtures/platform_dry_runs/valid_canonical_social_post.json
- Created: fixtures/platform_dry_runs/invalid_publish_ready_true.json
- Created: fixtures/platform_dry_runs/invalid_signal_language.json
- Created: fixtures/platform_dry_runs/invalid_unsupported_media_for_platform.json
- Created: tests/test_platform_adapter_contracts.py
- Created: docs/PLATFORM_ADAPTER_CONTRACTS_AFTER_0078.md
- Created: docs/TASK_CONTENTOPS_0078_LOCAL_PLATFORM_ADAPTER_CONTRACTS_AND_DRY_RUN_RENDERER_V0.md (this report)

## What it does
- Defines a canonical social post contract and a per-platform dry-run payload
  contract (draft-07 schemas).
- Provides a platform capability registry for x, linkedin, telegram,
  facebook_page, instagram, tiktok, with all live/credential/scheduling/
  replies-DMs/scraping flags disabled and official_docs_verified=false.
- Provides a deterministic renderer that maps a valid canonical post into
  per-platform dry-run previews, failing closed on unsafe content, unsupported
  media, media-required-but-missing, and unknown platforms.
- Reuses the 0076/0077 forbidden-language and alpha-implication scanners as the
  safety gate.
- Records all platform limits as
  constraint_source=local_placeholder_until_0081_official_docs_verification.

## What remains disabled
Live posting; platform/provider/LLM/search API clients; credentials/env reads;
network; scheduling; autonomous replies/DMs; scraping/browser automation;
content generator; public-postable/publish-ready content; real alpha artifact
access; Capital Chronicle core repo reads/writes.

## Validation run
- python -m pytest -q: 408 passed (was 392; +16 new).
- python -m pytest -q tests/test_platform_adapter_contracts.py: 16 passed.
- alpha-wait-state-summary: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS;
  public_content_allowed_now=false (wait-state preserved).
- git diff --check: clean.
- Suspicious scan over changed files: only hit is the module docstring line
  enumerating what it does NOT do ("never posts, schedules, replies...") -
  BENIGN_GUARDRAIL_TEXT. No functional network/credential/API/scheduler code.

## Notes
- The valid fixture summary originally used the word "short", which the 0076
  forbidden-language scanner flags (\bshort\b). It was reworded to "brief" so the
  guardrail stays strict and the safe fixture validates.

## Next task
TASK_CONTENTOPS_0079_LOCAL_APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_CONTRACT_V0
