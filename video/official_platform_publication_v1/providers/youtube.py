"""YouTube videos/Shorts Data API v3 shadow adapter."""

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


class YouTubeAdapter(OfficialProviderAdapter):
    supported_surfaces = frozenset(
        {Surface.YOUTUBE_NORMAL_VIDEO, Surface.YOUTUBE_SHORTS}
    )
    alternate_audio_capability = "ACCOUNT_GATED_STUDIO_CAPABILITY"

    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        return {
            "identity_kind": "YOUTUBE_CHANNEL_ID",
            "required_identity": binding.expected_identity_id,
            "oauth_scopes": [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.force-ssl",
            ],
            "api_project_audit_required_for_non_private_uploads": True,
            "alternate_audio": self.alternate_audio_capability,
            "live_write_authority": False,
        }

    def prepare(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
        attempt_id: str,
    ) -> ProviderPlan:
        item = media_artifact(package)
        meta = metadata(package)
        locale = binding.destination_locale
        privacy = binding.desired_publication_mode.casefold()
        body = {
            "snippet": {
                "title": meta["title"],
                "description": meta["description"],
                "categoryId": "25",
                "defaultLanguage": locale,
            },
            "localizations": {
                locale: {"title": meta["title"], "description": meta["description"]}
            },
            "status": {"privacyStatus": privacy},
        }
        requests = (
            ProviderRequest(
                operation="identity_readiness",
                method="GET",
                endpoint="https://www.googleapis.com/youtube/v3/channels",
                mutation=False,
                query={"part": "id,snippet", "mine": True},
                official_contract="channels.list",
            ),
            ProviderRequest(
                operation="initiate_resumable_video_upload",
                method="POST",
                endpoint="https://www.googleapis.com/upload/youtube/v3/videos",
                mutation=True,
                query={"part": "snippet,status,localizations", "uploadType": "resumable"},
                body=body,
                media_artifact=str(item["path"]),
                official_contract="videos.insert",
            ),
            ProviderRequest(
                operation="transfer_video_bytes",
                method="PUT",
                endpoint="{provider_returned_resumable_upload_uri}",
                mutation=True,
                headers={"Content-Type": "video/mp4", "Content-Length": item["size_bytes"]},
                media_artifact=str(item["path"]),
                official_contract="videos.insert resumable media upload",
            ),
            ProviderRequest(
                operation="insert_timed_caption_track",
                method="POST",
                endpoint="https://www.googleapis.com/upload/youtube/v3/captions",
                mutation=True,
                query={"part": "snippet", "uploadType": "multipart"},
                body={
                    "snippet": {
                        "videoId": "{video_id}",
                        "language": locale,
                        "name": f"Capital Chronicle {locale}",
                        "isDraft": False,
                    }
                },
                media_artifact=str(package["artifacts"]["caption_srt"]["path"]),
                official_contract="captions.insert",
            ),
            ProviderRequest(
                operation="processing_and_publication_readback",
                method="GET",
                endpoint="https://www.googleapis.com/youtube/v3/videos",
                mutation=False,
                query={
                    "part": "snippet,status,processingDetails,contentDetails,localizations",
                    "id": "{video_id}",
                },
                official_contract="videos.list",
            ),
            ProviderRequest(
                operation="caption_track_readback",
                method="GET",
                endpoint="https://www.googleapis.com/youtube/v3/captions",
                mutation=False,
                query={"part": "snippet", "videoId": "{video_id}"},
                official_contract="captions.list",
            ),
            ProviderRequest(
                operation="caption_track_content_readback",
                method="GET",
                endpoint="https://www.googleapis.com/youtube/v3/captions/{caption_id}",
                mutation=False,
                query={"tfmt": "srt"},
                official_contract="captions.download",
            ),
        )
        notes = [
            "ONE_VIDEO_ID_PER_EDITORIAL_PRODUCT_WHERE_PRACTICAL",
            "LOCALIZED_METADATA_SUPPORTED_BY_BCP47_LOCALIZATIONS",
            "TIMED_CAPTION_UPLOAD_SUPPORTED",
            "ALTERNATE_AUDIO_ACCOUNT_GATED_STUDIO_CAPABILITY_NO_VERIFIED_DATA_API_UPLOAD",
        ]
        if binding.surface is Surface.YOUTUBE_SHORTS:
            notes.append(
                "NO_SEPARATE_SHORTS_API_FLAG_CLASSIFICATION_IS_PRODUCT_BEHAVIOR_FROM_MEDIA"
            )
        return ProviderPlan(
            provider=Platform.YOUTUBE,
            surface=binding.surface,
            attempt_id=attempt_id,
            package_id=binding.package_id,
            destination_locale=locale,
            requests=requests,
            capability_notes=tuple(notes),
        )

    def localized_metadata_update_request(
        self,
        video_id: str,
        default_language: str,
        localized_metadata: Mapping[str, Mapping[str, str]],
    ) -> ProviderRequest:
        return ProviderRequest(
            operation="update_localized_metadata",
            method="PUT",
            endpoint="https://www.googleapis.com/youtube/v3/videos",
            mutation=True,
            query={"part": "snippet,localizations"},
            body={
                "id": video_id,
                "snippet": {"defaultLanguage": default_language},
                "localizations": dict(localized_metadata),
            },
            official_contract="videos.update",
        )

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        snippet = readback.get("snippet", {})
        status = readback.get("status", {})
        processing = readback.get("processingDetails", {})
        captions = readback.get("captionTracks", [])
        expected_privacy = attempt.binding.desired_publication_mode.casefold()
        checks: dict[str, bool | str] = {
            "provider_object_id_present": bool(readback.get("id")),
            "destination_channel_matches": snippet.get("channelId")
            == attempt.binding.expected_identity_id,
            "title_matches": snippet.get("title") == attempt.package["metadata"]["title"],
            "upload_processed": status.get("uploadStatus") == "processed",
            "processing_succeeded": processing.get("processingStatus") == "succeeded",
            "privacy_matches": status.get("privacyStatus") == expected_privacy,
            "timed_caption_track_present": any(
                item.get("language") == attempt.binding.destination_locale
                and item.get("status") == "serving"
                for item in captions
            ),
        }
        unresolved: list[str] = []
        if attempt.binding.surface is Surface.YOUTUBE_SHORTS:
            checks["shorts_api_classification"] = "NOT_EXPOSED_BY_YOUTUBE_DATA_API"
            unresolved.append("shorts_feed_classification_requires_later_public_product_readback")
        matched = all(value is True for value in checks.values() if isinstance(value, bool))
        return ReconciliationResult(
            matched=matched,
            provider_object_id=str(readback.get("id")) if readback.get("id") else None,
            checks=checks,
            unresolved=tuple(unresolved),
        )
