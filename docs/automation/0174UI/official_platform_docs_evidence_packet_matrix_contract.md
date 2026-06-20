# 0174UI Official Platform Docs Evidence Matrix Contract

- task_label: `TASK_CONTENTOPS_0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V0`
- matrix_version: `0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V1`
- source_baseline_commit: `dc997aa68df523539dd6f4df6b77d792d3961e14`
- packet_id: `official_platform_docs_evidence_matrix_packet_984d175d07fb07e2416f564f`
- packet_hash: `984d175d07fb07e2416f564f19ee97ae5be5b6c84538621277a83f68e6200e74`
- next_required_gate: `TASK_CONTENTOPS_0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V0`

## Docs Evidence Grounding Matrix

| Platform ID | Priority Tier | Role | Docs Status | Auth Summary | Endpoint Family | Key Caveats |
|---|---|---|---|---|---|---|
| `x` | `primary_now` | `primary_distribution` | `partial_docs_grounded` | OAuth 2.0 Authorization Code Flow with PKCE | v2/tweets POST/GET | 17 tweets per 24 hours on Free tier; paywall spend tier caveats |
| `telegram_remote_operator` | `primary_now` | `remote_operator_review` | `docs_grounded` | Bot Token API Authentication | getMe, getUpdates, Webhooks, sendMessage | No commercial spend quota; standard Bot API rate limits |
| `telegram_channel_destination` | `primary_now` | `controlled_channel_distribution` | `docs_grounded` | Bot Token API Authentication | sendMessage, sendPhoto | Standard Bot API limits (30 messages/second max) |
| `substack_newsletter` | `primary_now` | `owned_long_form` | `manual_export_no_api` | None (Manual Markdown Export) | None (No API Supported) | Manual copy/paste workflow |
| `linkedin` | `secondary_next` | `professional_credibility` | `partial_docs_grounded` | OAuth 2.0 Authorization Code Flow | ugcPosts, shares API | Standard member rate limits |
| `threads` | `expansion_later` | `expansion_distribution` | `partial_docs_grounded` | OAuth 2.0 Meta App Authorization | Threads API publishing endpoint | 250 posts per 24 hours per user |
| `instagram` | `expansion_later` | `expansion_distribution` | `partial_docs_grounded` | Instagram Graph API via Facebook Login | media containers and media publish endpoints | Container creation limit (25 per 24h rolling) |
| `facebook_page` | `expansion_later` | `expansion_distribution` | `partial_docs_grounded` | Page Access Token via OAuth 2.0 | Pages API feed endpoint | Facebook Page rate limit system |
| `tiktok` | `video_later` | `later_video_distribution` | `partial_docs_grounded` | OAuth 2.0 Three-Legged Authorization | Content Posting API upload endpoints | TikTok Posting quota limitations |
| `youtube` | `video_later` | `later_video_distribution` | `partial_docs_grounded` | Google OAuth 2.0 with client id | YouTube Data API v3 videos.insert | Daily API upload quota consumes 1600 units out of 10000 units |

## Required Distinctions & Caveats

- **X / Twitter**: Paywalled API tiers. Free tier is write-only and highly rate-limited (17 tweets/24h).
- **Telegram**: Bots are chat-scoped and require chat_id values. Bot cannot message arbitrary users.
- **Substack**: Grounded as `manual_export_no_api` (no official programmatic publish API exists).
- **LinkedIn**: Member profile shares (`w_member_social`) separate from organization page administration.
- **Meta (Threads, Instagram, Facebook)**: Standard Meta OAuth and App Review apply. Media URL visibility is required.
- **TikTok & YouTube**: High quota constraints (e.g. videos.insert consumes 1600 units) and video uploads metadata only.

## Safety Enforcements

- All live read/write/API actions remain false.
- No credentials or environment secrets are loaded.
- Inputting an unofficial domain fails closed.
- U9 Audit family: `platform_docs_evidence_future`.

## Packet Summary Metrics

```json
{
  "blocked_missing_docs_platforms": [],
  "credential_hydrated_count": 0,
  "env_read_count": 0,
  "grounded_count": 2,
  "live_read_allowed_count": 0,
  "live_write_allowed_count": 0,
  "manual_export_no_api_platforms": [
    "substack_newsletter"
  ],
  "official_doc_ref_count": 10,
  "official_domain_count": 7,
  "platform_api_called_count": 0,
  "rows_count": 10
}
```
