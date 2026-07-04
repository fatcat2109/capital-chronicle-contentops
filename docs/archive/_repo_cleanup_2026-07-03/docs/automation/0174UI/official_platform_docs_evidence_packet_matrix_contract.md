# 0174UI Official Platform Docs Evidence Matrix Contract

- task_label: `TASK_CONTENTOPS_0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V0`
- matrix_version: `0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V1`
- source_baseline_commit: `c868675cbeeabf97092e1c3229583dfc54596e6b`
- packet_id: `official_platform_docs_evidence_matrix_packet_64b4c2456c9c15cb0e92e163`
- packet_hash: `64b4c2456c9c15cb0e92e163ee56212755d3c4e6023dddfc324b2ed5c8aac1bf`
- next_required_gate: `TASK_CONTENTOPS_0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V0`

## Docs Evidence Grounding Matrix

| Platform ID | Role | Docs Status | Claims Status | Strength | Auth Summary | Endpoint Family | Key Caveats |
|---|---|---|---|---|---|---|---|
| `x` | `primary_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | OAuth 2.0 Authorization Code Flow with PKCE | v2/tweets POST/GET | X API is pay-per-use / credit-based pricing; rate limits are endpoint-specific and commonly use 15-minute windows |
| `telegram_remote_operator` | `remote_operator_review` | `docs_grounded` | `supported_by_cited_doc` | `strong` | Bot Token API Authentication | getMe, getUpdates, Webhooks, sendMessage | No commercial spend quota; standard Bot API rate limits |
| `telegram_channel_destination` | `controlled_channel_distribution` | `docs_grounded` | `supported_by_cited_doc` | `strong` | Bot Token API Authentication | sendMessage, sendPhoto | Rate limit caveat requiring platform-rate task |
| `substack_newsletter` | `owned_long_form` | `manual_export_no_api` | `not_verified_current_docs` | `weak` | None (Manual Markdown Export) | None (No API Supported) | Manual copy/paste workflow |
| `linkedin` | `professional_credibility` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | OAuth 2.0 Authorization Code Flow | ugcPosts, shares API | Standard member rate limits |
| `threads` | `expansion_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | OAuth 2.0 Meta App Authorization | Threads API publishing endpoint | 250 posts per 24 hours per user |
| `instagram` | `expansion_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | Instagram Graph API via Facebook Login | media containers and media publish endpoints | Container creation limit (25 per 24h rolling) |
| `facebook_page` | `expansion_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | Page Access Token via OAuth 2.0 | Pages API feed endpoint | Facebook Page rate limit system |
| `tiktok` | `later_video_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | OAuth 2.0 Three-Legged Authorization | Content Posting API upload endpoints | TikTok Posting quota limitations |
| `youtube` | `later_video_distribution` | `partial_docs_grounded` | `supported_by_cited_doc` | `strong` | Google OAuth 2.0 with client id | YouTube Data API v3 videos.insert | videos.insert supports media upload; quota impact: 100 calls per day; quota cost: 1 unit in the Video Uploads quota bucket |

## Required Distinctions & Caveats

- **X / Twitter**: Paywalled API tiers. Rate limits are endpoint-specific and commonly use 15-minute windows. Pricing is pay-per-use / credit-based.
- **Telegram**: Bots are chat-scoped and require chat_id values. Character limit (4096) directly proven. 30 msg/sec limit removed and downgraded.
- **Substack**: Grounded as `manual_export_no_api` with `weak` evidence strength (no approved API doc found).
- **LinkedIn**: Member profile shares separate from organization page administration.
- **Meta (Threads, Instagram, Facebook)**: Standard Meta OAuth and App Review apply. Media URL visibility is required.
- **TikTok & YouTube**: High quota constraints (YouTube videos.insert cost 1 unit in Video Uploads bucket with 100 calls limit) and video uploads metadata only.

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
  "official_doc_ref_count": 11,
  "official_domain_count": 7,
  "platform_api_called_count": 0,
  "rows_count": 10
}
```
