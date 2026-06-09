# Platform Official Docs Verification Pack - After TASK_CONTENTOPS_0081

LOCAL ONLY | ADVISORY ONLY | EVIDENCE BASE REQUIRED | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK
NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING | NO LIVE METRICS
HUMAN (OPERATOR) APPROVAL REQUIRED

This verification pack is a local advisory guide listing the official platform-doc
questions that must be verified before any live/API work can be considered on
each platform.

## Advisory Status Invariants
- This pack is advisory only and never becomes or grants runtime authority:
  `docs_runtime_authority` must stay false.
- Repository-side live posting remains disabled: `live_posting_enabled` must
  stay false.
- Sockets, network, environment variables, credentials, and platform SDKs remain
  completely disabled/blocked.

## Verification Checklist per Platform

### X
- **Status**: `not_verified`
- **Official Docs to Check**: X API v2 Direct Publishing / Media Uploads.
- **Write Endpoints**: `/2/tweets` (POST). Must confirm payload structure and support for `made_with_ai` labels or explicit media attachment.
- **Media Upload**: `/1.1/media/upload.json` (POST) to upload images/videos chunked, obtaining a `media_id` before tweeting. Must check file size limits (5MB for images, 15MB/512MB for videos).
- **Access & App Review**: Developer Account (Free/Basic/Pro). Basic tier ($100/mo) is required for write access; Free tier is limited to read-only/testing or deactivated.
- **Rate Limits & Pricing**: Write rate limit: 17 tweets per 24 hours on Basic tier. pro tier has higher limits.
- **Security & Credentials**: OAuth 2.0 User Context (Authorization Code Flow with PKCE) or OAuth 1.0a (User Context). Requires Client ID/Secret or Access Token/Secret.
- **Analytics/Metrics API**: Tweet metrics (`impression_count`, `like_count`, `retweet_count`) available via `/2/tweets?ids=...&tweet.fields=public_metrics`.

### LinkedIn
- **Status**: `not_verified`
- **Official Docs to Check**: LinkedIn Developer Portal - Share on LinkedIn & Community Management API.
- **Write Endpoints**: `/v2/shares` or `/v2/ugcPosts` (POST). Must map post shapes.
- **Member vs Organization**: Share as a member (`urn:li:person:...`) vs organization/page (`urn:li:organization:...`). Organizational shares require distinct permissions and the page admin role.
- **Access & App Review**: Requires a LinkedIn Developer Application with "Share on LinkedIn" and/or "Community Management API" products added. "Community Management" requires full App Review/Business Verification before active use.
- **Media/Document Shapes**: Images, multi-image posts, video uploads, or PDF documents (slides/carousels). Requires separate media upload initialization `/v2/assets?action=registerUpload`.
- **Rate Limits**: Spaced daily limits on posting endpoints to prevent spam.
- **Security & Credentials**: OAuth 2.0. Member posting requires Authorization Code Flow; organization posting requires organization admin scopes (`w_member_social`, `w_organization_social`).

### Telegram
- **Status**: `partially_verified` (Operator-supplied baseline verified)
- **Official Docs to Check**: Telegram Bot API Reference (`core.telegram.org/bots/api`).
- **Write Endpoints**: `sendMessage` for text, `sendPhoto` for image media.
- **Admin Requirements**: Bot must be added to the channel as an Administrator with the `can_post_messages` permission.
- **Payload Shapes**: `chat_id` parameter can be a public channel username (e.g. `@channelusername`) or private numeric ID.
- **Media Upload**: Supports direct URL/multipart-form upload. Limits: 10MB photo; 50MB video for standard bots.
- **Rate Limits**: 30 messages per second across all chats; 20 messages per minute per group.
- **Security & Credentials**: Single Bot Token obtained via @BotFather. No OAuth 2.0 flow required.
- **Analytics/Metrics**: No native Bot API metrics endpoint; post views and subscriber count are manual-only placeholder context.



### Facebook Page
- **Status**: `not_verified`
- **Official Docs to Check**: Meta Graph API - Page Feed Publishing.
- **Write Endpoints**: `/{page-id}/feed` (POST).
- **Access & App Review**: Meta App Review and Business Verification are required before the app can go live with public users/pages. Developer mode allows posting only to pages owned by the app developers/testers.
- **Identity & Page Tokens**: Page Access Token required (`pages_manage_posts`, `pages_read_engagement`). Generated from a long-lived User Access Token via `/{page-id}?fields=access_token`.
- **Media Upload**: `/{page-id}/photos` or `/{page-id}/videos` (POST). Must obtain ID to attach to post.
- **Analytics/Metrics**: `/{post-id}/insights?metric=post_impressions,post_engagements` (GET).

### Instagram
- **Status**: `not_verified`
- **Official Docs to Check**: Instagram Graph API - Content Publishing API.
- **Write Endpoints**: `/{instagram-business-account-id}/media` (POST) to containerize, then `/{instagram-business-account-id}/media_publish` (POST) to release.
- **Account Constraints**: Requires an Instagram Professional/Business Account linked to a Facebook Page. Personal and Creator accounts have different API limitations.
- **Media Hosting**: Requires a public, unauthenticated media URL (image or video hosted on a public server) for Meta to fetch during containerization.
- **Access & App Review**: Meta App Review + Business Verification required.
- **Rate Limits**: 25 posts per 24 hours per account.
- **Analytics/Metrics**: `/{instagram-media-id}/insights?metric=impressions,reach,saved,video_views`.

### TikTok
- **Status**: `not_verified`
- **Official Docs to Check**: TikTok for Developers - Content Posting API.
- **Write Endpoints**: `/v2/post/publish/video/init/` (POST) for video; `/v2/post/publish/content/init/` (POST) for images.
- **Access & App Review**: App audit required. The app must go through TikTok's Developer App Review before moving from "Sandbox" to "Production".
- **Sandbox Restrictions**: In sandbox/unaudited mode, posts are limited to approved creator sandbox accounts, and can only be posted as "private-only" (invisible to public).
- **Format Requirements**: Video: MP4/WebM, minimum 3 seconds, maximum 60 minutes. Photo: JPG/PNG, up to 35 images in a slideshow.
- **Security & Credentials**: OAuth 2.0 with scopes `video.publish` or `video.upload`.

## Components
- `schemas/platform_official_docs_verification_record.schema.json`
- `schemas/platform_official_docs_verification_pack.schema.json`
- `live_contentops/platform_official_docs_verification.py`
- `fixtures/platform_official_docs/*.json`
