"""Deterministic in-memory provider used only for zero-network shadow proof."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .control_plane import PublicationControlPlane, UnknownWriteRetryError
from .models import PublicationAttempt, PublicationState, Surface


class DeterministicFakeProvider:
    """Simulate documented response fields without an HTTP client or credentials."""

    is_fake_provider = True

    @staticmethod
    def _object_id(attempt: PublicationAttempt) -> str:
        prefix = {
            Surface.YOUTUBE_NORMAL_VIDEO: "ytv",
            Surface.YOUTUBE_SHORTS: "yts",
            Surface.TIKTOK: "tt",
            Surface.INSTAGRAM_REELS: "igr",
            Surface.INSTAGRAM_STORIES: "igs",
            Surface.FACEBOOK_REELS: "fbr",
        }[attempt.binding.surface]
        suffix = hashlib.sha256(attempt.attempt_id.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}_{suffix}"

    def execute(
        self,
        plane: PublicationControlPlane,
        attempt: PublicationAttempt,
        *,
        ambiguous_after_transfer: bool = False,
        readback_discovers_object: bool = True,
    ) -> dict[str, Any]:
        if attempt.state is not PublicationState.WRITE_AUTHORITY_REQUIRED:
            raise RuntimeError("Fake execution requires a prepared, live-write-blocked attempt")
        object_id = self._object_id(attempt)
        attempt.provider_refs.update(self._initial_refs(attempt, object_id))
        attempt.record("CONTROLLED_FAKE_PROVIDER_EXECUTION_STARTED", network_calls=0)
        plane.transition(
            attempt,
            PublicationState.INITIATED,
            "FAKE_PROVIDER_INITIATED",
            provider_refs=dict(attempt.provider_refs),
        )

        if ambiguous_after_transfer:
            plane.transition(
                attempt,
                PublicationState.UNKNOWN_WRITE,
                "FAKE_PROVIDER_ACCEPTED_MEDIA_CLIENT_RECEIVED_AMBIGUOUS_TIMEOUT",
                accepted_by_fake_provider=True,
            )
            blind_retry_blocked = False
            try:
                plane.assert_retry_allowed(attempt)
            except UnknownWriteRetryError:
                blind_retry_blocked = True
                attempt.record("BLIND_RETRY_BLOCKED_PENDING_READBACK")
            readback = (
                self._published_readback(attempt, object_id)
                if readback_discovers_object
                else self._missing_readback(attempt)
            )
            result = plane.reconcile(attempt, readback)
            return {
                "blind_retry_blocked": blind_retry_blocked,
                "readback_discovered_operation": result.matched,
                "readback_discovered_object": bool(result.provider_object_id),
                "reconciliation_matched": result.matched,
                "receipt": attempt.to_receipt(),
            }

        plane.transition(
            attempt,
            PublicationState.MEDIA_TRANSFERRED,
            "FAKE_MEDIA_TRANSFER_COMPLETED",
        )
        plane.transition(
            attempt,
            PublicationState.PROCESSING,
            "FAKE_PROVIDER_PROCESSING_OBSERVED",
            processing=self._processing_readback(attempt, object_id),
        )
        if attempt.binding.surface is Surface.TIKTOK:
            plane.transition(
                attempt,
                PublicationState.DRAFT_DELIVERED_TO_CREATOR,
                "FAKE_PROVIDER_REPORTED_SEND_TO_USER_INBOX_AWAITING_READBACK",
                public_post=False,
                creator_finalization_required=True,
            )
        else:
            plane.transition(
                attempt,
                PublicationState.PUBLISHED_UNCONFIRMED,
                "FAKE_PROVIDER_REPORTED_PUBLISH_SUCCESS_AWAITING_READBACK",
            )
        result = plane.reconcile(attempt, self._published_readback(attempt, object_id))
        return {
            "blind_retry_blocked": False,
            "readback_discovered_operation": result.matched,
            "readback_discovered_object": bool(result.provider_object_id),
            "reconciliation_matched": result.matched,
            "receipt": attempt.to_receipt(),
        }

    @staticmethod
    def _initial_refs(attempt: PublicationAttempt, object_id: str) -> dict[str, str]:
        if attempt.binding.surface is Surface.TIKTOK:
            return {"publish_id": f"v_pub_file~v2.{object_id}"}
        if attempt.binding.surface in {Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES}:
            return {"container_id": f"container_{object_id}", "provider_object_id": object_id}
        return {"provider_object_id": object_id}

    @staticmethod
    def _processing_readback(
        attempt: PublicationAttempt, object_id: str
    ) -> Mapping[str, Any]:
        surface = attempt.binding.surface
        if surface in {Surface.YOUTUBE_NORMAL_VIDEO, Surface.YOUTUBE_SHORTS}:
            return {
                "id": object_id,
                "status": {"uploadStatus": "uploaded"},
                "processingDetails": {
                    "processingStatus": "processing",
                    "processingProgress": {"partsTotal": 100, "partsProcessed": 42},
                },
            }
        if surface is Surface.TIKTOK:
            return {"status": "PROCESSING_UPLOAD", "uploaded_bytes": 11050655}
        if surface in {Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES}:
            return {
                "id": f"container_{object_id}",
                "status_code": "IN_PROGRESS",
                "status": "Media upload is processing.",
            }
        return {
            "id": object_id,
            "status": {
                "video_status": "processing",
                "processing_progress": 42,
                "uploading_phase": {"status": "complete"},
                "processing_phase": {"status": "in_progress"},
                "publishing_phase": {"status": "not_started"},
            },
        }

    @staticmethod
    def _published_readback(
        attempt: PublicationAttempt, object_id: str
    ) -> Mapping[str, Any]:
        binding = attempt.binding
        meta = attempt.package["metadata"]
        surface = binding.surface
        if surface in {Surface.YOUTUBE_NORMAL_VIDEO, Surface.YOUTUBE_SHORTS}:
            return {
                "id": object_id,
                "snippet": {
                    "channelId": binding.expected_identity_id,
                    "title": meta["title"],
                    "description": meta["description"],
                    "defaultLanguage": binding.destination_locale,
                },
                "status": {
                    "uploadStatus": "processed",
                    "privacyStatus": binding.desired_publication_mode.casefold(),
                },
                "processingDetails": {"processingStatus": "succeeded"},
                "contentDetails": {"caption": "true"},
                "localizations": {
                    binding.destination_locale: {
                        "title": meta["title"],
                        "description": meta["description"],
                    }
                },
                "captionTracks": [
                    {"language": binding.destination_locale, "status": "serving"}
                ],
            }
        if surface is Surface.TIKTOK:
            return {
                "identity": {
                    "open_id": binding.expected_identity_id,
                    "display_name": binding.expected_public_handle,
                },
                "status": {
                    "status": "SEND_TO_USER_INBOX",
                    "publicaly_available_post_id": [],
                },
            }
        if surface in {Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES}:
            media: dict[str, Any] = {
                "id": object_id,
                "media_type": "VIDEO",
                "media_product_type": (
                    "REELS" if surface is Surface.INSTAGRAM_REELS else "STORY"
                ),
                "owner": {"id": binding.expected_identity_id},
                "username": binding.expected_public_handle.lstrip("@"),
            }
            if surface is Surface.INSTAGRAM_REELS:
                media["caption"] = str(meta.get("social_copy") or meta["description"])
                media["permalink"] = f"https://www.instagram.com/reel/{object_id}/"
            return {
                "container": {
                    "id": f"container_{object_id}",
                    "status_code": "FINISHED",
                    "status": "Finished: Media has been uploaded and it is ready to be published.",
                },
                "media": media,
            }
        description = str(meta.get("social_copy") or meta["description"])
        return {
            "id": object_id,
            "title": meta["title"],
            "description": description,
            "from": {"id": binding.expected_identity_id, "name": binding.expected_public_handle},
            "permalink_url": f"https://www.facebook.com/reel/{object_id}",
            "status": {
                "video_status": "ready",
                "uploading_phase": {"status": "complete"},
                "processing_phase": {"status": "complete"},
                "publishing_phase": {"status": "complete"},
            },
        }

    @staticmethod
    def _missing_readback(attempt: PublicationAttempt) -> Mapping[str, Any]:
        if attempt.binding.surface is Surface.FACEBOOK_REELS:
            return {
                "status": {
                    "video_status": "processing",
                    "uploading_phase": {"status": "complete"},
                    "processing_phase": {"status": "in_progress"},
                    "publishing_phase": {"status": "not_started"},
                }
            }
        return {}
