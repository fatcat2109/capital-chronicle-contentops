"""Facebook Page Reels Publishing API shadow adapter."""

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


class FacebookReelsAdapter(OfficialProviderAdapter):
    supported_surfaces = frozenset({Surface.FACEBOOK_REELS})

    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        return {
            "identity_kind": "FACEBOOK_PAGE_ID",
            "required_identity": binding.expected_identity_id,
            "required_permissions": [
                "pages_show_list",
                "pages_read_engagement",
                "pages_manage_posts",
            ],
            "graph_version": "RUNTIME_CONFIG_REQUIRED_REVERIFY_AT_LIVE_CANARY",
            "page_access_required": True,
            "reels_principal": "FACEBOOK_PAGE_ACCESS_TOKEN",
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
        requests = (
            ProviderRequest(
                operation="page_identity_readiness",
                method="GET",
                endpoint="https://graph.facebook.com/{api_version}/{page_id}",
                mutation=False,
                query={"fields": "id,name,tasks"},
                official_contract="Facebook Page identity/readiness",
            ),
            ProviderRequest(
                operation="initialize_reel_upload",
                method="POST",
                endpoint="https://graph.facebook.com/{api_version}/me/video_reels",
                mutation=True,
                query={"upload_phase": "start"},
                official_contract="Page Reels upload_phase=start",
            ),
            ProviderRequest(
                operation="transfer_reel_bytes",
                method="POST",
                endpoint="{provider_returned_upload_url}",
                mutation=True,
                headers={
                    "offset": 0,
                    "file_size": media["size_bytes"],
                    "Content-Type": "application/octet-stream",
                },
                media_artifact=str(media["path"]),
                official_contract="rupload.facebook.com video upload",
            ),
            ProviderRequest(
                operation="upload_processing_status_readback",
                method="GET",
                endpoint="https://graph.facebook.com/{api_version}/{video_id}",
                mutation=False,
                query={"fields": "status"},
                official_contract="Facebook Reel status readback",
            ),
            ProviderRequest(
                operation="finish_and_publish_reel",
                method="POST",
                endpoint="https://graph.facebook.com/{api_version}/me/video_reels",
                mutation=True,
                query={
                    "video_id": "{video_id}",
                    "upload_phase": "finish",
                    "video_state": "PUBLISHED",
                    "title": meta["title"],
                    "description": str(meta.get("social_copy") or meta["description"]),
                },
                official_contract="Page Reels upload_phase=finish",
            ),
            ProviderRequest(
                operation="published_reel_readback",
                method="GET",
                endpoint="https://graph.facebook.com/{api_version}/{video_id}",
                mutation=False,
                query={"fields": "id,title,description,from,permalink_url,status"},
                official_contract="Facebook Video readback",
            ),
        )
        return ProviderPlan(
            provider=Platform.FACEBOOK,
            surface=binding.surface,
            attempt_id=attempt_id,
            package_id=binding.package_id,
            destination_locale=binding.destination_locale,
            requests=requests,
            capability_notes=(
                "PAGE_REELS_INITIALIZE_UPLOAD_FINISH_STATUS_CONTRACT",
                "PAGE_IDENTITY_PREFLIGHT_IS_SEPARATE_FROM_ME_VIDEO_REELS_PAGE_TOKEN_PRINCIPAL",
                "VIDEO_STATE_PUBLISHED_IS_A_LIVE_MUTATION_AND_REMAINS_HARD_BLOCKED",
                "NO_OFFICIAL_TIMED_CAPTION_LOCALIZED_METADATA_OR_ALTERNATE_AUDIO_TRANSPORT_IN_REVIEWED_REELS_FLOW",
            ),
        )

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        status = readback.get("status", {})
        phases = (
            status.get("uploading_phase", {}).get("status"),
            status.get("processing_phase", {}).get("status"),
            status.get("publishing_phase", {}).get("status"),
        )
        checks: dict[str, bool | str] = {
            "provider_object_id_present": bool(readback.get("id")),
            "destination_page_matches": readback.get("from", {}).get("id")
            == attempt.binding.expected_identity_id,
            "title_matches": readback.get("title") == attempt.package["metadata"]["title"],
            "description_matches": readback.get("description")
            == str(
                attempt.package["metadata"].get("social_copy")
                or attempt.package["metadata"]["description"]
            ),
            "all_phases_complete": phases == ("complete", "complete", "complete"),
            "video_ready": status.get("video_status") == "ready",
            "public_permalink_present": bool(readback.get("permalink_url")),
        }
        matched = all(value is True for value in checks.values() if isinstance(value, bool))
        unresolved = tuple(
            name for name, value in checks.items() if isinstance(value, bool) and not value
        )
        return ReconciliationResult(
            matched=matched,
            provider_object_id=str(readback.get("id")) if readback.get("id") else None,
            checks=checks,
            unresolved=unresolved,
        )
