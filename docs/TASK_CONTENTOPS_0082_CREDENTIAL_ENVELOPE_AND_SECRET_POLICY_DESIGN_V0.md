# TASK_CONTENTOPS_0082_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0

## Task scope
Design the credential envelope and secret-handling policy for future supervised
platform integrations without reading or using any real credentials. This task
is local-only design + validation. It must not add credential loading, env
reads, platform clients, network calls, live posting, scheduling, scraping,
replies/DMs, or metrics fetching.

## Files created/changed
- Created: schemas/credential_envelope_record.schema.json
- Created: schemas/credential_policy_pack.schema.json
- Created: schemas/credential_redaction_policy.schema.json
- Created: schemas/credential_rotation_checklist.schema.json
- Created: live_contentops/credential_envelope_policy.py
- Created: fixtures/credential_policy/valid_credential_policy_pack.json
- Created: fixtures/credential_policy/valid_credential_envelopes_all_platforms.json
- Created: fixtures/credential_policy/valid_redaction_test_cases.json
- Created: fixtures/credential_policy/invalid_live_use_allowed_now.json
- Created: fixtures/credential_policy/invalid_env_read_performed.json
- Created: fixtures/credential_policy/invalid_credential_value_present.json
- Created: fixtures/credential_policy/invalid_unredacted_secret.json
- Created: fixtures/credential_policy/invalid_docs_runtime_authority_true.json
- Created: tests/test_credential_envelope_policy.py
- Created: docs/CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_AFTER_0082.md
- Created: docs/TASK_CONTENTOPS_0082_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0.md (this report)

## What it does
- Credential envelopes define uppercase environment variable conventions as strings only (e.g. `CC_TG_BOT_TOKEN`, `CC_X_CLIENT_SECRET`), Least Privilege policies, scopes, and storage rules.
- Redaction policy defines secret patterns (regex) for typical token shapes, replacement values, and block rules.
- Policy validators (`validate_record`, `validate_policy_pack`, `validate_redaction_policy`, `validate_rotation_checklist`) fail closed if `live_use_allowed_now`, `credential_value_present`, `credential_value_stored_in_repo`, `credential_value_logged`, `credential_accessed_by_repo`, `env_read_performed`, or `network_accessed` are true.
- Redactor tests (`test_redaction_patterns_and_helpers`) prove that synthetic fake secret-like strings are correctly identified and replaced with `[REDACTED_SECRET]` and blocked if unredacted.

## Platform credential envelopes & rotation status
- **X**: `CC_X_CLIENT_ID` / `CC_X_CLIENT_SECRET` (OAuth2 user context). Scopes: tweet.read, tweet.write, users.read, offline.access. Rotation required every 90 days.
- **LinkedIn**: `CC_LI_CLIENT_ID` / `CC_LI_CLIENT_SECRET` (OAuth2 user context). Scopes: w_member_social, w_organization_social. Rotation required every 90 days.
- **Telegram**: `CC_TG_BOT_TOKEN` (bot_token). Scopes: can_post_messages, can_edit_messages. Rotation required every 90 days.
- **Facebook Page**: `CC_FB_PAGE_TOKEN` (page_access_token). Scopes: pages_manage_posts, pages_read_engagement. Rotation required every 90 days.
- **Instagram**: `CC_IG_USER_TOKEN` (user_access_token). Scopes: instagram_basic, instagram_content_publish. Rotation required every 90 days.
- **TikTok**: `CC_TT_CLIENT_KEY` / `CC_TT_CLIENT_SECRET` (OAuth2 user context). Scopes: video.publish, video.upload. Rotation required every 90 days.

## What remains disabled
Live posting; platform API clients / SDKs; real credential loading / reading / keyring access; environment variable reading / parsing of .env; network; scheduling; autonomous replies/DMs; scraping; live metrics; public-postable/publish-ready content; real alpha artifact access; Capital Chronicle core repo reads/writes.

## Validation run
- python -m pytest -q: 457 passed (was 447; +10 new).
- python -m pytest -q tests/test_credential_envelope_policy.py: 10 passed.
- alpha-wait-state-summary: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS;
  public_content_allowed_now=false (wait-state preserved).
- git diff --check: clean.
- Suspicious scan over changed files: clean. No non-schema http(s) links. No real credentials or unredacted fake keys in valid fixtures/docs (only synthetic fake test strings in negative fixtures).

## Next task
TASK_CONTENTOPS_0083_TELEGRAM_SUPERVISED_LIVE_PILOT_DESIGN_GATE_V0
