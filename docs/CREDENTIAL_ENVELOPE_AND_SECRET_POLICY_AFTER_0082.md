# Credential Envelope and Secret Policy Design - After TASK_CONTENTOPS_0082

LOCAL ONLY | ADVISORY ONLY | LEAST PRIVILEGE REQUIRED | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK
NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING | NO LIVE METRICS
HUMAN (OPERATOR) APPROVAL REQUIRED

This layer designs the credential envelope and secret-handling policy for
future supervised platform integrations without accessing or reading real
credentials or environment variables.

## Security & Redaction Policies
- Sockets, network, environment variables, credentials, and platform SDKs remain
  completely disabled/blocked.
- Credentials must never be stored inside the repository or raw logs.
- Active credential value fields (`credential_value_present`,
  `credential_value_stored_in_repo`, `credential_value_logged`,
  `credential_accessed_by_repo`) must require `false` to pass validation.
- All credential loading must use external environment variable strings or vault
  managers outside the repository during runtime (to be developed in later phases).
- Redaction policy defines regex patterns for typical secret shapes (e.g. OpenAI
  keys, Telegram bot tokens, and HTTP Bearer tokens) to safely wipe them from
  audit payloads before they are persisted, failing validation if unredacted secret
  patterns remain in audit logs.

## Platform Credential Envelopes

### X
- **Verification Status**: `not_verified`
- **Source**: `local_placeholder_until_0081_official_docs_verified`
- **Is Placeholder**: Yes
- **Credential Kind**: `oauth2_user_context` (Advisory Placeholder)
- **Environment Variables**: `CC_X_CLIENT_ID`, `CC_X_CLIENT_SECRET` (Advisory Placeholder)
- **Required Scopes**: `tweet.read`, `tweet.write`, `users.read`, `offline.access` (Advisory Placeholder)
- **Least Privilege Notes**: Authorized only to publish tweets to first-party accounts.

### LinkedIn
- **Verification Status**: `not_verified`
- **Source**: `local_placeholder_until_0081_official_docs_verified`
- **Is Placeholder**: Yes
- **Credential Kind**: `oauth2_user_context` (Advisory Placeholder)
- **Environment Variables**: `CC_LI_CLIENT_ID`, `CC_LI_CLIENT_SECRET` (Advisory Placeholder)
- **Required Scopes**: `w_member_social`, `w_organization_social` (Advisory Placeholder)
- **Least Privilege Notes**: Only authorized to publish posts to the authenticated user's profile and company feed.

### Telegram
- **Verification Status**: `partially_verified` (Operator-supplied documentation verified)
- **Source**: `operator_supplied_docs_verified`
- **Is Placeholder**: No
- **Credential Kind**: `bot_token` (Verified requirement)
- **Environment Variables**: `CC_TG_BOT_TOKEN` (Verified requirement)
- **Required Scopes**: `can_post_messages`, `can_edit_messages` (Verified requirements)
- **Least Privilege Notes**: Bot is authorized as channel admin to post text/photos to a designated public/private channel feed.

### Facebook Page
- **Verification Status**: `not_verified`
- **Source**: `local_placeholder_until_0081_official_docs_verified`
- **Is Placeholder**: Yes
- **Credential Kind**: `page_access_token` (Advisory Placeholder)
- **Environment Variables**: `CC_FB_PAGE_TOKEN` (Advisory Placeholder)
- **Required Scopes**: `pages_manage_posts`, `pages_read_engagement` (Advisory Placeholder)
- **Least Privilege Notes**: Page-scoped access; only authorized to publish feed posts.

### Instagram
- **Verification Status**: `not_verified`
- **Source**: `local_placeholder_until_0081_official_docs_verified`
- **Is Placeholder**: Yes
- **Credential Kind**: `user_access_token` (Advisory Placeholder)
- **Environment Variables**: `CC_IG_USER_TOKEN` (Advisory Placeholder)
- **Required Scopes**: `instagram_basic`, `instagram_content_publish` (Advisory Placeholder)
- **Least Privilege Notes**: Restricted to Professional/Business Account publishing.

### TikTok
- **Verification Status**: `not_verified`
- **Source**: `local_placeholder_until_0081_official_docs_verified`
- **Is Placeholder**: Yes
- **Credential Kind**: `oauth2_user_context` (Advisory Placeholder)
- **Environment Variables**: `CC_TT_CLIENT_KEY`, `CC_TT_CLIENT_SECRET` (Advisory Placeholder)
- **Required Scopes**: `video.publish`, `video.upload` (Advisory Placeholder)
- **Least Privilege Notes**: Restricted to sandbox/test account direct video posting.

## Rotation and Revocation Checklists
1. **Rotation required before live**: Yes, keys must be rotated every 90 days. User tokens expire and must be refreshed via official platform OAuth mechanisms.
2. **Revocation procedure required before live**: Yes, there must be a clear sequence to deactivate tokens via the developer console immediately on suspected leak.
3. **Leak response steps**: deauthorize developer application, revoke active tokens, roll secret keys, enable kill switch, perform post-mortem audit.

## Components
- `schemas/credential_envelope_record.schema.json`
- `schemas/credential_policy_pack.schema.json`
- `schemas/credential_redaction_policy.schema.json`
- `schemas/credential_rotation_checklist.schema.json`
- `live_contentops/credential_envelope_policy.py`
- `fixtures/credential_policy/*.json`

