"""Instagram professional-account Reels and Stories shadow adapter."""

from __future__ import annotations

from typing import Any, Mapping

from ..models import (
    DestinationBinding,
    Platform,
    ProviderPlan,
    ProviderRequest,
    PublicationAttempt,
    ReconciliationResult,
    Surface,
    media_artifact,
)
from .base import OfficialProviderAdapter, metadata


class InstagramAdapter(OfficialProviderAdapter):
    supported_surfaces = frozenset(
        {Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES}
    )

    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        return {
            "identity_kind": "INSTAGRAM_PROFESSIONAL_ACCOUNT_ID",
            "required_identity": binding.expected_identity_id,
            "account_requirement": (
                "INSTAGRAM_BUSINESS_ACCOUNT"
                if binding.surface is Surface.INSTAGRAM_STORIES
                else "INSTAGRAM_PROFESSIONAL_ACCOUNT"
            ),
            "instagram_login_scopes": [
                "instagram_business_basic",
                "instagram_business_content_publish",
            ],
            "facebook_login_permissions": [
                "instagram_basic",
                "instagram_content_publish",
                "pages_read_engagement",
            ],
            "graph_version": "RUNTIME_CONFIG_REQUIRED_REVERIFY_AT_LIVE_CANARY",
            "live_write_authority": False,
        }

    def prepare(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
        attempt_id: str,
    ) -> ProviderPlan:
        media = media_artifact(package)
        meta = metadata(package)
        media_type = (
            "REELS" if binding.surface is Surface.INSTAGRAM_REELS else "STORIES"
        )
        body: dict[str, Any] = {
            "media_type": media_type,
            "video_url": f"https://{{verified_media_host}}/{binding.package_id}.mp4",
        }
        if binding.surface is Surface.INSTAGRAM_REELS:
            body.update(
                {
                    "caption": str(meta.get("social_copy") or meta["description"]),
                    "share_to_feed": False,
                }
            )
        requests = (
            ProviderRequest(
                operation="professional_account_identity_readiness",
                method="GET",
                endpoint="https://graph.instagram.com/{api_version}/{ig_user_id}",
                mutation=False,
                query={"fields": "id,username,account_type"},
                official_contract="Instagram professional account readback",
            ),
            ProviderRequest(
                operation="create_media_container",
                method="POST",
                endpoint="https://graph.instagram.com/{api_version}/{ig_user_id}/media",
                mutation=True,
                body=body,
                official_contract="Instagram create video container",
            ),
            ProviderRequest(
                operation="container_processing_readback",
                method="GET",
                endpoint="https://graph.instagram.com/{api_version}/{ig_container_id}",
                mutation=False,
                query={"fields": "status_code,status"},
                official_contract="Instagram container status",
            ),
            ProviderRequest(
                operation="publish_media_container",
                method="POST",
                endpoint="https://graph.instagram.com/{api_version}/{ig_user_id}/media_publish",
                mutation=True,
                body={"creation_id": "{ig_container_id}"},
                official_contract="Instagram media_publish",
            ),
            ProviderRequest(
                operation="published_media_readback",
                method="GET",
                endpoint="https://graph.instagram.com/{api_version}/{ig_media_id}",
                mutation=False,
                query={
                    "fields": "id,caption,media_type,media_product_type,owner,username,permalink"
                },
                official_contract="Instagram media object readback",
            ),
        )
        notes = [
            "VIDEO_URL_REQUIRES_PUBLICLY_FETCHABLE_MEDIA_ON_CONTROLLED_HOST",
            "RESUMABLE_UPLOAD_IS_ALSO_SUPPORTED_VIA_UPLOAD_TYPE_RESUMABLE",
            "NO_OFFICIAL_TIMED_CAPTION_LOCALIZED_METADATA_OR_ALTERNATE_AUDIO_TRANSPORT",
            f"CANONICAL_MEDIA_SHA256_{media['sha256']}",
        ]
        if binding.surface is Surface.INSTAGRAM_STORIES:
            notes.extend(
                [
                    "STORIES_REQUIRE_INSTAGRAM_BUSINESS_ACCOUNT_IN_REVIEWED_FACEBOOK_LOGIN_CONTRACT",
                    "ORDINARY_STORY_CAPTION_NOT_INCLUDED_BECAUSE_NOT_VERIFIED_IN_OFFICIAL_API",
                ]
            )
        return ProviderPlan(
            provider=Platform.INSTAGRAM,
            surface=binding.surface,
            attempt_id=attempt_id,
            package_id=binding.package_id,
            destination_locale=binding.destination_locale,
            requests=requests,
            capability_notes=tuple(notes),
        )

    def resumable_upload_contract(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
    ) -> tuple[ProviderRequest, ProviderRequest]:
        """Build the officially documented resumable alternative without inventing a URI."""

        media = media_artifact(package)
        media_type = (
            "REELS" if binding.surface is Surface.INSTAGRAM_REELS else "STORIES"
        )
        return (
            ProviderRequest(
                operation="create_resumable_media_container",
                method="POST",
                endpoint="https://graph.instagram.com/{api_version}/{ig_user_id}/media",
                mutation=True,
                body={"media_type": media_type, "upload_type": "resumable"},
                official_contract="Instagram create video container resumable upload",
            ),
            ProviderRequest(
                operation="transfer_resumable_video_bytes",
                method="POST",
                endpoint="{official_provider_upload_uri_for_ig_container}",
                mutation=True,
                headers={
                    "offset": 0,
                    "file_size": media["size_bytes"],
                    "Content-Type": "application/octet-stream",
                },
                media_artifact=str(media["path"]),
                official_contract="Instagram resumable media transfer provider URI",
            ),
        )

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        container = readback.get("container", {})
        media = readback.get("media", {})
        expected_product = (
            "REELS" if attempt.binding.surface is Surface.INSTAGRAM_REELS else "STORY"
        )
        checks: dict[str, bool | str] = {
            "container_finished": container.get("status_code") == "FINISHED",
            "provider_object_id_present": bool(media.get("id")),
            "destination_owner_matches": media.get("owner", {}).get("id")
            == attempt.binding.expected_identity_id,
            "media_is_video": media.get("media_type") == "VIDEO",
            "surface_matches": media.get("media_product_type") == expected_product,
            "public_permalink_present": bool(media.get("permalink")),
        }
        if attempt.binding.surface is Surface.INSTAGRAM_REELS:
            checks["caption_matches"] = media.get("caption") == str(
                attempt.package["metadata"].get("social_copy")
                or attempt.package["metadata"]["description"]
            )
        else:
            checks["ordinary_story_caption"] = "NOT_EXPOSED_BY_VERIFIED_API"
        matched = all(value is True for value in checks.values() if isinstance(value, bool))
        return ReconciliationResult(
            matched=matched,
            provider_object_id=str(media.get("id")) if media.get("id") else None,
            checks=checks,
            unresolved=(),
        )
