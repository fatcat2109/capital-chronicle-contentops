"""Official platform docs registry for Multi-Platform Live Foundation Batch A.

Local deterministic registry. No import-time env reads, no network, no live writes.
All rows keep live_write_eligible false for this task.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_A_DOCS_CREDENTIALS_BINDINGS_AND_READONLY_PROBES_V0"
DOCS_SNAPSHOT_ID = "batch_a_official_docs_snapshot_2026_06_23"
DOCS_CHECKED_AT = "2026-06-23T07:09:32Z"


@dataclass(frozen=True)
class PlatformDocsRow:
    platform_id: str
    docs_snapshot_id: str
    docs_checked_at: str
    docs_source_type: str
    official_docs_url: str
    api_available: bool
    api_write_available: bool
    manual_publish_supported: bool
    browser_assisted_supported: bool
    required_app_review: bool
    required_oauth: bool
    required_scopes: tuple[str, ...]
    required_account_roles: tuple[str, ...]
    supported_payloads: tuple[str, ...]
    media_upload_model: str
    rate_limit_notes: str
    paid_plan_notes: str
    restrictions: tuple[str, ...]
    unknowns: tuple[str, ...]
    re_ground_required_before_live: bool
    docs_status: str
    live_write_eligible: bool = False


def build_platform_docs_registry() -> tuple[PlatformDocsRow, ...]:
    """Return current official-doc grounded platform registry."""
    return (
        PlatformDocsRow(
            platform_id='telegram_remote_operator',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://core.telegram.org/bots/api',
            api_available=True,
            api_write_available=False,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=False,
            required_oauth=False,
            required_scopes=(),
            required_account_roles=('operator_chat_member_or_chat_id',),
            supported_payloads=('operator_review_message',),
            media_upload_model='none',
            rate_limit_notes='no write in this task',
            paid_plan_notes='free Bot API; bounded by Telegram limits',
            restrictions=('not public destination', 'sendMessage forbidden in this task'),
            unknowns=('operator inbox identity must be confirmed manually',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='telegram_channel_destination',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://core.telegram.org/bots/api',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=False,
            required_oauth=False,
            required_scopes=(),
            required_account_roles=('bot admin in channel',),
            supported_payloads=('text', 'photo', 'document_after_future_gate'),
            media_upload_model='Bot API multipart/file_id/URL after future gate',
            rate_limit_notes='Telegram Bot API limits apply',
            paid_plan_notes='free Bot API; no paid plan noted',
            restrictions=('sendMessage/sendPhoto/sendDocument forbidden in this task',),
            unknowns=('channel membership/admin must be verified',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='x_profile',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://docs.x.com/x-api/introduction',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('tweet.read', 'users.read', 'offline.access', 'tweet.write_future_only'),
            required_account_roles=('developer account', 'app access tier', 'request/spend budget'),
            supported_payloads=('short_text', 'thread_after_future_gate'),
            media_upload_model='media upload requires separate media flow after future gate',
            rate_limit_notes='plan-specific request limits',
            paid_plan_notes='paid access/spend or project plan may be required; budget must be configured before probes',
            restrictions=('paid/budget/scope unclear blocks live write',),
            unknowns=('exact account and access tier must be confirmed',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='linkedin_member_profile',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('openid', 'profile', 'email', 'w_member_social_future_only'),
            required_account_roles=('member token', 'app product access'),
            supported_payloads=('professional_post_after_future_gate',),
            media_upload_model='UGC/posts media constraints after future gate',
            rate_limit_notes='LinkedIn API throttles apply',
            paid_plan_notes='app/product approval may be required',
            restrictions=('write scope forbidden in this task',),
            unknowns=('member URN/account binding must be confirmed',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='linkedin_organization_page',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('r_organization_social', 'w_organization_social_future_only'),
            required_account_roles=('organization admin/role', 'app product access'),
            supported_payloads=('organization_post_after_future_gate',),
            media_upload_model='UGC/posts media constraints after future gate',
            rate_limit_notes='LinkedIn API throttles apply',
            paid_plan_notes='Marketing API access/app review may be required',
            restrictions=('organization role proof required',),
            unknowns=('org URN/page role must be confirmed',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='substack_newsletter',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_docs_fetch_blocked_403',
            official_docs_url='https://support.substack.com/',
            api_available=False,
            api_write_available=False,
            manual_publish_supported=True,
            browser_assisted_supported=True,
            required_app_review=False,
            required_oauth=False,
            required_scopes=(),
            required_account_roles=('publication owner/editor manual login',),
            supported_payloads=('markdown_export', 'manual_browser_assisted_lab'),
            media_upload_model='manual upload/export only',
            rate_limit_notes='manual publishing only',
            paid_plan_notes='Substack official write API not verified',
            restrictions=('no official write API verified', 'browser-assisted only as lab/manual fallback'),
            unknowns=('official docs inaccessible via fetch; re-ground before live',),
            re_ground_required_before_live=True,
            docs_status='docs_unverified',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='threads_profile',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://developers.facebook.com/docs/threads/overview',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('threads_basic', 'threads_content_publish_future_only'),
            required_account_roles=('Threads profile', 'Meta app review as needed'),
            supported_payloads=('short_text_after_future_gate', 'media_after_future_gate'),
            media_upload_model='container publish model after future gate',
            rate_limit_notes='Meta/Threads limits apply',
            paid_plan_notes='app review/permissions may be required',
            restrictions=('Meta app/scope constraints unresolved for this repo',),
            unknowns=('profile binding and scopes must be proven',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='instagram_professional_account',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('instagram_business_basic', 'instagram_content_publish_future_only'),
            required_account_roles=('Instagram professional/business account',),
            supported_payloads=('caption_asset_packet', 'carousel_after_future_gate'),
            media_upload_model='media container then publish after future gate',
            rate_limit_notes='Meta/Instagram limits apply',
            paid_plan_notes='app review/permissions may be required',
            restrictions=('requires eligible professional account and public media URL constraints',),
            unknowns=('asset/media constraints must be proven',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='facebook_page',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://developers.facebook.com/docs/pages-api/posts',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('pages_show_list', 'pages_read_engagement', 'pages_manage_posts_future_only'),
            required_account_roles=('Facebook Page admin/task access',),
            supported_payloads=('page_post_after_future_gate',),
            media_upload_model='Graph API photo/video/link models after future gate',
            rate_limit_notes='Graph API limits apply',
            paid_plan_notes='app review/page permissions may be required',
            restrictions=('page role and permission proof required',),
            unknowns=('page binding must be confirmed',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='tiktok_account',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://developers.tiktok.com/doc/content-posting-api-get-started',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('user.info.basic', 'video.publish_future_only', 'video.upload_future_only'),
            required_account_roles=('TikTok developer app', 'account authorization'),
            supported_payloads=('video_metadata_packet',),
            media_upload_model='init upload/post endpoint after future gate',
            rate_limit_notes='TikTok limits apply',
            paid_plan_notes='app audit/review and scopes may be required',
            restrictions=('video upload/publish forbidden in this task',),
            unknowns=('app audit, upload constraints, account binding must be proven',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
        PlatformDocsRow(
            platform_id='youtube_channel',
            docs_snapshot_id=DOCS_SNAPSHOT_ID,
            docs_checked_at=DOCS_CHECKED_AT,
            docs_source_type='official_live_fetch_ok',
            official_docs_url='https://developers.google.com/youtube/v3/docs/videos/insert',
            api_available=True,
            api_write_available=True,
            manual_publish_supported=False,
            browser_assisted_supported=False,
            required_app_review=True,
            required_oauth=True,
            required_scopes=('youtube.readonly', 'youtube.upload_future_only'),
            required_account_roles=('Google OAuth', 'YouTube channel'),
            supported_payloads=('video_metadata_packet',),
            media_upload_model='resumable upload after future gate',
            rate_limit_notes='YouTube quota costs apply',
            paid_plan_notes='Google OAuth consent/quota required',
            restrictions=('upload forbidden in this task', 'quota budget required'),
            unknowns=('channel binding and quota must be proven',),
            re_ground_required_before_live=True,
            docs_status='official_docs_checked',
            live_write_eligible=False,
        ),
    )


def registry_by_platform_id() -> dict[str, PlatformDocsRow]:
    return {row.platform_id: row for row in build_platform_docs_registry()}


def to_packet() -> dict[str, Any]:
    rows = [asdict(row) for row in build_platform_docs_registry()]
    return {
        "task_label": TASK_LABEL,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "docs_snapshot_id": DOCS_SNAPSHOT_ID,
        "live_write_eligible": False,
        "platform_count": len(rows),
        "rows": rows,
    }


def docs_block_live_write(platform_id: str) -> bool:
    row = registry_by_platform_id()[platform_id]
    return row.docs_status == "docs_unverified" or row.re_ground_required_before_live or not row.live_write_eligible
