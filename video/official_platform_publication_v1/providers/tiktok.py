"""TikTok Content Posting API Upload-to-TikTok draft adapter."""

from __future__ import annotations

from typing import Any, Mapping

from ..models import (
    AdapterCapabilityState,
    DeliveryIntent,
    DestinationBinding,
    Platform,
    ProviderPlan,
    ProviderRequest,
    PublicationAttempt,
    PublicationContractError,
    ReconciliationResult,
    Surface,
    media_artifact,
)
from .base import OfficialProviderAdapter


TIKTOK_DRAFT_DELIVERY_SEMANTICS = (
    "SEND_TO_USER_INBOX_IS_DRAFT_DELIVERY_CREATOR_FINALIZATION_REQUIRED"
)


class TikTokUploadDraftAdapter(OfficialProviderAdapter):
    """Plan Upload API draft delivery; this is deliberately not Direct Post."""

    supported_surfaces = frozenset({Surface.TIKTOK})

    def validate_destination(self, binding: DestinationBinding) -> None:
        super().validate_destination(binding)
        if binding.delivery_intent is not DeliveryIntent.DRAFT_DELIVERY:
            raise PublicationContractError(
                "TikTok canonical transport requires DRAFT_DELIVERY intent"
            )
        if (
            binding.adapter_capability_state
            is not AdapterCapabilityState.PRODUCTION_REVIEW_REQUIRED
        ):
            raise PublicationContractError(
                "TikTok draft upload remains PRODUCTION_REVIEW_REQUIRED"
            )

    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        return {
            "identity_kind": "TIKTOK_OPEN_ID",
            "required_identity": binding.expected_identity_id,
            "oauth_scopes": ["video.upload"],
            "identity_read_scope": "user.info.basic",
            "upload_contract": "UPLOAD_TO_TIKTOK_DRAFT",
            "creator_finalization_required": True,
            "direct_post": False,
            "public_post_confirmed_by_draft_delivery": False,
            "sandbox_oauth_bootstrap": "HISTORICAL_PROVEN_NOT_REVERIFIED_THIS_TASK",
            "production_eligibility": "PRODUCTION_REVIEW_REQUIRED",
            "live_write_authority": False,
        }

    def prepare(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
        attempt_id: str,
    ) -> ProviderPlan:
        media = media_artifact(package)
        requests = (
            ProviderRequest(
                operation="readonly_creator_identity_preflight",
                method="GET",
                endpoint="https://open.tiktokapis.com/v2/user/info/",
                mutation=False,
                query={"fields": "open_id,display_name"},
                official_contract="user.info.basic",
            ),
            ProviderRequest(
                operation="initialize_upload_to_tiktok_draft",
                method="POST",
                endpoint="https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                mutation=True,
                body={
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": media["size_bytes"],
                        "chunk_size": media["size_bytes"],
                        "total_chunk_count": 1,
                    }
                },
                official_contract="post/publish/inbox/video/init scope=video.upload",
            ),
            ProviderRequest(
                operation="transfer_video_bytes_to_provider_upload_url",
                method="PUT",
                endpoint="{provider_returned_upload_url}",
                mutation=True,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": media["size_bytes"],
                    "Content-Range": f"bytes 0-{int(media['size_bytes']) - 1}/{media['size_bytes']}",
                },
                media_artifact=str(media["path"]),
                official_contract="Content Posting API Upload media transfer",
            ),
            ProviderRequest(
                operation="draft_delivery_status_readback",
                method="POST",
                endpoint="https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                mutation=False,
                body={"publish_id": "{publish_id}"},
                official_contract="post/publish/status/fetch scope=video.upload",
            ),
        )
        return ProviderPlan(
            provider=Platform.TIKTOK,
            surface=binding.surface,
            attempt_id=attempt_id,
            package_id=binding.package_id,
            destination_locale=binding.destination_locale,
            requests=requests,
            capability_notes=(
                "UPLOAD_TO_TIKTOK_DRAFT_NOT_DIRECT_POST",
                TIKTOK_DRAFT_DELIVERY_SEMANTICS,
                "PUBLIC_POST_FALSE_UNTIL_CREATOR_FINALIZES_AND_PUBLIC_ID_IS_OBSERVED",
                "VIDEO_QUERY_IS_OPTIONAL_AND_ONLY_VALID_AFTER_A_PUBLIC_VIDEO_ID_EXISTS",
                "NO_OFFICIAL_TIMED_CAPTION_LOCALIZED_METADATA_OR_ALTERNATE_AUDIO_TRANSPORT",
            ),
        )

    @staticmethod
    def public_video_query_request_after_status(
        status_readback: Mapping[str, Any],
    ) -> ProviderRequest:
        public_ids = status_readback.get("publicaly_available_post_id", [])
        provider_object_id = str(public_ids[0]) if public_ids else ""
        if (
            status_readback.get("status") != "PUBLISH_COMPLETE"
            or not provider_object_id.strip()
        ):
            raise PublicationContractError(
                "TikTok video.query requires PUBLISH_COMPLETE and an observed public video ID"
            )
        return ProviderRequest(
            operation="optional_public_video_readback_after_creator_finalization",
            method="POST",
            endpoint="https://open.tiktokapis.com/v2/video/query/",
            mutation=False,
            query={
                "fields": (
                    "id,create_time,share_url,video_description,duration,"
                    "height,width,title"
                )
            },
            body={"filters": {"video_ids": [provider_object_id]}},
            official_contract="video.query scope=video.list after public ID",
        )

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        identity = readback.get("identity", {})
        status = readback.get("status", {})
        public_ids = status.get("publicaly_available_post_id", [])
        checks: dict[str, bool | str] = {
            "creator_identity_matches": identity.get("open_id")
            == attempt.binding.expected_identity_id,
            "draft_delivered_to_creator_inbox": status.get("status")
            == "SEND_TO_USER_INBOX",
            "direct_post_used": "FALSE",
            "public_post_confirmed": "FALSE",
            "public_video_id_absent_at_draft_delivery": not public_ids,
            "creator_finalization": "REQUIRED",
        }
        matched = all(
            value is True for value in checks.values() if isinstance(value, bool)
        )
        return ReconciliationResult(
            matched=matched,
            provider_object_id=None,
            checks=checks,
            unresolved=(
                "creator_must_open_tiktok_inbox_edit_and_complete_post",
                "public_post_readback_not_established_by_draft_delivery",
            ),
        )

    @staticmethod
    def reconcile_public_video_after_creator_finalization(
        status_readback: Mapping[str, Any],
        video_query_readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        """Optionally strengthen truth only after creator finalization produced a public ID."""

        public_ids = status_readback.get("publicaly_available_post_id", [])
        public_id = str(public_ids[0]) if public_ids else None
        videos = video_query_readback.get("videos", [])
        video = videos[0] if len(videos) == 1 else {}
        checks: dict[str, bool | str] = {
            "publish_complete_after_creator_finalization": status_readback.get("status")
            == "PUBLISH_COMPLETE",
            "public_video_id_present": bool(public_id),
            "video_query_returned_exact_public_id": bool(public_id)
            and str(video.get("id", "")) == public_id,
            "video_query_ownership_contract": (
                "PROVIDER_VERIFIES_REQUESTED_VIDEO_BELONGS_TO_AUTHORIZED_USER"
            ),
        }
        matched = all(
            value is True for value in checks.values() if isinstance(value, bool)
        )
        return ReconciliationResult(
            matched=matched,
            provider_object_id=public_id if matched else None,
            checks=checks,
            unresolved=() if matched else ("public_post_readback_not_established",),
        )
