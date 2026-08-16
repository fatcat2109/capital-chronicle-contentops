"""TikTok Content Posting API Direct Post shadow adapter."""

from __future__ import annotations

from typing import Any, Mapping

from ..models import (
    AdapterCapabilityState,
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
from .base import OfficialProviderAdapter, metadata


TIKTOK_AUTOMATION_ELIGIBILITY = (
    "OFFICIAL_API_NOT_ELIGIBLE_FOR_THIS_INTERNAL_AUTOMATION_MODEL"
)


class TikTokDirectPostAdapter(OfficialProviderAdapter):
    supported_surfaces = frozenset({Surface.TIKTOK})

    def validate_destination(self, binding: DestinationBinding) -> None:
        super().validate_destination(binding)
        if binding.adapter_capability_state is not AdapterCapabilityState.PRODUCT_POLICY_BLOCKED:
            raise PublicationContractError(
                "TikTok autonomous readiness must fail closed as PRODUCT_POLICY_BLOCKED"
            )

    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        return {
            "identity_kind": "TIKTOK_CREATOR_USERNAME",
            "required_identity": binding.expected_identity_id,
            "oauth_scopes": ["video.publish"],
            "creator_info_required_at_post_time": True,
            "editable_privacy_and_metadata_ui_required": True,
            "express_creator_consent_required": True,
            "public_visibility_audit_required": True,
            "automation_eligibility": TIKTOK_AUTOMATION_ELIGIBILITY,
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
        caption = " ".join(
            [str(meta.get("social_copy") or meta["description"]), *meta.get("hashtags", [])]
        ).strip()
        privacy = {
            "PUBLIC": "PUBLIC_TO_EVERYONE",
            "PRIVATE": "SELF_ONLY",
            "UNLISTED": "SELF_ONLY",
        }[binding.desired_publication_mode]
        requests = (
            ProviderRequest(
                operation="creator_identity_privacy_duration_readiness",
                method="POST",
                endpoint="https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
                mutation=False,
                official_contract="creator_info/query",
            ),
            ProviderRequest(
                operation="initialize_direct_post",
                method="POST",
                endpoint="https://open.tiktokapis.com/v2/post/publish/video/init/",
                mutation=True,
                body={
                    "post_info": {
                        "title": caption,
                        "privacy_level": privacy,
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000,
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": media["size_bytes"],
                        "chunk_size": media["size_bytes"],
                        "total_chunk_count": 1,
                    },
                },
                official_contract="post/publish/video/init",
            ),
            ProviderRequest(
                operation="transfer_video_bytes",
                method="PUT",
                endpoint="{provider_returned_upload_url}",
                mutation=True,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": media["size_bytes"],
                    "Content-Range": f"bytes 0-{int(media['size_bytes']) - 1}/{media['size_bytes']}",
                },
                media_artifact=str(media["path"]),
                official_contract="Content Posting API media transfer",
            ),
            ProviderRequest(
                operation="publish_status_readback",
                method="POST",
                endpoint="https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                mutation=False,
                body={"publish_id": "{publish_id}"},
                official_contract="post/publish/status/fetch",
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
                TIKTOK_AUTOMATION_ELIGIBILITY,
                "TECHNICAL_DIRECT_POST_CONTRACT_ONLY_NOT_AUTONOMOUS_LIVE_READINESS",
                "CREATOR_INFO_CURRENT_PRIVACY_OPTIONS_EDITABLE_METADATA_AND_EXPRESS_CONSENT_REQUIRED",
                "PULL_FROM_URL_REQUIRES_VERIFIED_DOMAIN_AND_IS_PREFERRED_FOR_SERVER_MEDIA",
                "NO_OFFICIAL_TIMED_CAPTION_LOCALIZED_METADATA_OR_ALTERNATE_AUDIO_TRANSPORT",
            ),
        )

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        creator = readback.get("creator_info", {})
        status = readback.get("status", {})
        video = readback.get("video", {})
        public_ids = status.get("publicaly_available_post_id", [])
        provider_object_id = str(public_ids[0]) if public_ids else None
        checks: dict[str, bool | str] = {
            "creator_identity_matches": creator.get("creator_username")
            == attempt.binding.expected_identity_id,
            "publish_complete": status.get("status") == "PUBLISH_COMPLETE",
            "public_post_id_present": bool(provider_object_id),
            "video_id_matches_status": str(video.get("id", "")) == (provider_object_id or ""),
            "caption_matches": video.get("title")
            == " ".join(
                [
                    str(
                        attempt.package["metadata"].get("social_copy")
                        or attempt.package["metadata"]["description"]
                    ),
                    *attempt.package["metadata"].get("hashtags", []),
                ]
            ).strip(),
            "policy_eligibility": TIKTOK_AUTOMATION_ELIGIBILITY,
        }
        matched = all(value is True for value in checks.values() if isinstance(value, bool))
        return ReconciliationResult(
            matched=matched,
            provider_object_id=provider_object_id,
            checks=checks,
            unresolved=("autonomous_internal_publication_product_policy_blocked",),
        )
