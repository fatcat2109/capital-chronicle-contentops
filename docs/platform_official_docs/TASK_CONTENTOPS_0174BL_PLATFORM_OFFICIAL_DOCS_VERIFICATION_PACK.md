# Platform Official Docs Verification Pack — TASK_CONTENTOPS_0174BL

LOCAL ONLY | ADVISORY ONLY | EVIDENCE BASE REQUIRED | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK
NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING | NO LIVE METRICS
HUMAN (OPERATOR) APPROVAL REQUIRED

Baseline commit: `7998154e43b95342cce4d43b798b3db7ed2d9da5`
Task: `TASK_CONTENTOPS_0174BL_GROUNDED_PLATFORM_CAPABILITY_REGISTRY_AND_COMPILER_ALIGNMENT_V2`

This pack is the grounded, official-documentation evidence base behind the v2
platform capability registry (`live_contentops/scd_platform_capability_registry_v2.py`).
It records, per platform, the official publishing documentation reviewed at build
time so each capability profile can cite a real source. It extends the prior
`PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_AFTER_0081.md` baseline with the three
platforms added in v2 (Threads, Substack newsletter, generic manual) and a strict
official-domain allowlist.

## Advisory Status Invariants

- This pack is advisory only and never becomes or grants runtime authority:
  `runtime_authority` must stay `false` and `advisory_only` must stay `true`.
- Repository-side live posting remains disabled. Every capability profile keeps
  all twelve `*_now` / readiness flags `false`
  (`live_api_enabled_now`, `platform_api_allowed_now`, `credential_read_allowed_now`,
  `credentials_requested_now`, `posting_enabled_now`, `scheduler_enabled_now`,
  `autonomous_replies_enabled_now`, `dms_enabled_now`, `scraping_enabled_now`,
  `public_ready`, `live_ready`, `dispatch_ready`).
- Sockets, network, environment variables, credentials, and platform SDKs remain
  completely disabled/blocked. Credential slot names are recorded as future-only
  symbols; credential values are never present, read, requested, logged, or committed.
- Official doc URLs are validated against a strict domain allowlist
  (`OFFICIAL_DOC_DOMAIN_ALLOWLIST`). A source whose URL is off-allowlist is BLOCKED;
  a source older than 365 days (relative to the build date) is flagged
  REVIEW_REQUIRED (stale), never silently trusted.

## Official Domain Allowlist

Only these domains count as official documentation sources for v2:

- `core.telegram.org`
- `docs.x.com`, `developer.x.com`
- `learn.microsoft.com` (LinkedIn marketing/community-management docs)
- `developers.facebook.com` (Facebook Page, Instagram, Threads)
- `developers.tiktok.com`
- `substack.com`, `support.substack.com`

## Verification Checklist per Platform

### Telegram
- **Status**: `partially_verified` (operator-supplied baseline carried from 0081)
- **Live risk**: `medium_first_future_candidate` (first future supervised candidate)
- **Official Docs**: Telegram Bot API Reference (`core.telegram.org/bots/api`).
- **Documented publish capability (future only)**: channel message + media posting.
- **Admin / access**: bot must be a channel administrator with `can_post_messages`.
- **Credentials (future slot only)**: single bot credential slot via @BotFather; no OAuth flow.
- **Metrics**: no native Bot API metrics; views/subscribers are manual-only context.
- **Current repo allowed state**: `future_live_gate_required`.

### X (Twitter)
- **Status**: `not_verified`
- **Live risk**: `high_policy_cost_access_sensitive`
- **Official Docs**: X API — Create Post (`docs.x.com/x-api/posts/creation-of-a-post`).
- **Documented publish capability (future only)**: post creation + chunked media upload.
- **Access / cost**: paid developer tier required for write access; write caps apply.
- **Credentials (future slot only)**: OAuth 2.0 app credential slot.
- **Disclosure fields**: `made_with_ai`, `reply_settings`, `media_disclosure`, `paid_partnership`.
- **Current repo allowed state**: `future_live_gate_required`.

### LinkedIn
- **Status**: `not_verified`
- **Live risk**: `high_restricted_permissions`
- **Official Docs**: Microsoft Learn — LinkedIn Posts API
  (`learn.microsoft.com/.../linkedin/marketing/community-management/shares/posts-api`).
- **Documented publish capability (future only)**: member and organization share posting.
- **Access / review**: Community Management API requires full app review / business verification.
- **Posting identity modes**: `member`, `organization`.
- **Credentials (future slot only)**: OAuth 2.0 member + org credential slot.
- **Current repo allowed state**: `future_live_gate_required`.

### Facebook Page
- **Status**: `not_verified`
- **Live risk**: `high_meta_app_review_identity`
- **Official Docs**: Meta Graph API — Page Posts (`developers.facebook.com/docs/pages-api/posts`).
- **Documented publish capability (future only)**: page feed posting + media id attach.
- **Access / review**: Meta app review + business verification; page access token required.
- **Current repo allowed state**: `future_live_gate_required`.

### Instagram
- **Status**: `not_verified`
- **Live risk**: `high_meta_app_review_media_constraints`
- **Official Docs**: Instagram Platform — Content Publishing
  (`developers.facebook.com/docs/instagram-platform/content-publishing`).
- **Documented publish capability (future only)**: media container then media publish flow.
- **Constraints**: professional/business account linked to a Facebook Page; public media URL required.
- **Access / review**: Meta app review + business verification.
- **Current repo allowed state**: `future_live_gate_required`.

### Threads
- **Status**: `not_verified` (NEW in v2)
- **Live risk**: `high_access_and_permissions`
- **Official Docs**: Threads API (`developers.facebook.com/docs/threads`).
- **Documented publish capability (future only)**: thread create + media attach flow.
- **Access / review**: Meta app review; access still maturing.
- **Current repo allowed state**: `future_live_gate_required`.

### TikTok
- **Status**: `not_verified`
- **Live risk**: `very_high_audit_and_creator_control` (last priority, high friction)
- **Official Docs**: TikTok Content Posting API — Get Started
  (`developers.tiktok.com/doc/content-posting-api-get-started`).
- **Documented publish capability (future only)**: content init + publish-status flow.
- **Access / review**: developer app audit required; sandbox is private-only until production.
- **Future priority**: `last_priority_high_friction`.
- **Current repo allowed state**: `future_live_gate_required`.

### Substack Newsletter
- **Status**: `not_verified` (NEW in v2)
- **Live risk**: `high_write_api_unknown_manual_only`
- **Official Docs**: Substack Support (`support.substack.com`).
- **Documented publish capability**: no verified stable public write/publish API.
- **Disposition**: manual export only; public publishing capability unknown.
- **Current repo allowed state**: `manual_export_only` (no future live gate claimed).

### Generic Manual
- **Status**: `not_applicable_manual` (NEW in v2)
- **Live risk**: `low_manual_only`
- **Official Docs**: none — manual operator workflow advisory only (no API by design).
- **Disposition**: manual export only; no platform capability of any kind.
- **Current repo allowed state**: `manual_export_only`.

## Components

- `live_contentops/scd_platform_capability_registry_v2.py` — validators + builders + registry.
- `schemas/scd_platform_official_doc_source.schema.json`
- `schemas/scd_platform_official_docs_verification_pack.schema.json`
- `schemas/scd_platform_capability_profile_v2.schema.json`
- `schemas/scd_platform_credential_slot_policy.schema.json`
- `schemas/scd_platform_live_gate_checklist.schema.json`
- `schemas/scd_platform_dry_run_payload_policy_matrix.schema.json`
- `schemas/scd_platform_registry_compiler_alignment_report.schema.json`
- `schemas/scd_platform_publish_readiness_alignment_report.schema.json`
- `schemas/scd_platform_redacted_audit_alignment_report.schema.json`
- `fixtures/scd_platform_capability_registry_v2/*.json`
- `tests/test_scd_platform_capability_registry_v2.py`
