from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from video.official_platform_publication_v1.control_plane import (
    PublicationControlPlane,
    UnknownWriteRetryError,
    WriteAuthorityError,
)
from video.official_platform_publication_v1.fake_provider import DeterministicFakeProvider
from video.official_platform_publication_v1.models import (
    AdapterCapabilityState,
    DeliveryIntent,
    DestinationBinding,
    InstagramLoginVariant,
    Platform,
    PublicationContractError,
    PublicationState,
    Surface,
    assert_no_secret_serialization,
    deterministic_attempt_id,
    load_publication_package,
)
from video.official_platform_publication_v1.providers import (
    FacebookReelsAdapter,
    InstagramAdapter,
    TikTokUploadDraftAdapter,
    YouTubeAdapter,
)
from video.official_platform_publication_v1.providers.tiktok import (
    TIKTOK_DRAFT_DELIVERY_SEMANTICS,
)
from video.official_platform_publication_v1.shadow_demo import run_shadow_demo


REPO = Path(__file__).resolve().parents[1]


def _package(format_kind: str, *, locale: str = "en") -> dict[str, object]:
    package_id = "pkg_" + ("1" if format_kind == "LONGFORM_16_9" else "2") * 64
    return {
        "schema": "contentops.v2.platform_neutral_publication_package.v1",
        "source_story_id": "fixture_story",
        "source_film_id": "fixture_film",
        "format": format_kind,
        "language": locale,
        "artifacts": {
            "clean_video": {
                "path": f"C:/shadow/{format_kind}.{locale}.mp4",
                "sha256": "a" * 64,
                "size_bytes": 1000,
            },
            "burned_caption_video": None,
            "audio": {
                "path": f"C:/shadow/audio.{locale}.wav",
                "sha256": "b" * 64,
                "size_bytes": 200,
            },
            "caption_json": {
                "path": f"C:/shadow/captions.{locale}.json",
                "sha256": "c" * 64,
                "size_bytes": 100,
            },
            "caption_srt": {
                "path": f"C:/shadow/captions.{locale}.srt",
                "sha256": "d" * 64,
                "size_bytes": 100,
            },
            "caption_vtt": {
                "path": f"C:/shadow/captions.{locale}.vtt",
                "sha256": "e" * 64,
                "size_bytes": 100,
            },
        },
        "metadata": {
            "title": "Shadow title",
            "description": "Shadow description",
            "social_copy": "Shadow social copy",
            "hashtags": ["#CapitalChronicle"],
        },
        "chapters": [],
        "rights_provenance_refs": ["rights"],
        "factual_evidence_refs": ["evidence"],
        "intended_future_surfaces": [],
        "generation_version": "fixture-v1",
        "hard_boundaries": {
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "scheduler_mutation_authority": False,
            "allow_4k": False,
        },
        "package_id": package_id,
        "transport": None,
        "publication_state": "PACKAGE_ONLY_ZERO_PUBLIC_WRITE",
    }


def _adapters() -> dict[Surface, object]:
    youtube = YouTubeAdapter()
    instagram = InstagramAdapter()
    return {
        Surface.YOUTUBE_NORMAL_VIDEO: youtube,
        Surface.YOUTUBE_SHORTS: youtube,
        Surface.TIKTOK: TikTokUploadDraftAdapter(),
        Surface.INSTAGRAM_REELS: instagram,
        Surface.INSTAGRAM_STORIES: instagram,
        Surface.FACEBOOK_REELS: FacebookReelsAdapter(),
    }


def _binding(
    surface: Surface,
    package_id: str,
    *,
    locale: str = "en",
    intent: str = "v1",
    capability: AdapterCapabilityState | None = None,
) -> DestinationBinding:
    platform = {
        Surface.YOUTUBE_NORMAL_VIDEO: Platform.YOUTUBE,
        Surface.YOUTUBE_SHORTS: Platform.YOUTUBE,
        Surface.TIKTOK: Platform.TIKTOK,
        Surface.INSTAGRAM_REELS: Platform.INSTAGRAM,
        Surface.INSTAGRAM_STORIES: Platform.INSTAGRAM,
        Surface.FACEBOOK_REELS: Platform.FACEBOOK,
    }[surface]
    default_capability = (
        AdapterCapabilityState.PRODUCTION_REVIEW_REQUIRED
        if surface is Surface.TIKTOK
        else AdapterCapabilityState.ACCOUNT_SETUP_REQUIRED
    )
    instagram_variant = (
        InstagramLoginVariant.INSTAGRAM_LOGIN
        if surface in {Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES}
        else None
    )
    return DestinationBinding(
        platform=platform,
        surface=surface,
        destination_identity_kind=f"{platform.value}_IDENTITY_ID",
        expected_identity_id=f"{platform.value.casefold()}_shadow_id",
        expected_public_handle="Capital Chronicle",
        destination_locale=locale,
        package_id=package_id,
        delivery_intent=(
            DeliveryIntent.DRAFT_DELIVERY
            if surface is Surface.TIKTOK
            else DeliveryIntent.PUBLICATION
        ),
        desired_publication_mode=(None if surface is Surface.TIKTOK else "PUBLIC"),
        adapter_capability_state=capability or default_capability,
        instagram_login_variant=instagram_variant,
        provider_intent_version=intent,
    )


def test_real_package_contract_compatibility_loader(tmp_path: Path) -> None:
    package = _package("SHORT_9_16")
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    loaded = load_publication_package(path)

    assert loaded["package_id"] == package["package_id"]
    assert loaded["hard_boundaries"]["video_public_write_authority"] is False


@pytest.mark.parametrize(
    ("surface", "format_kind"),
    [
        (Surface.YOUTUBE_NORMAL_VIDEO, "LONGFORM_16_9"),
        (Surface.YOUTUBE_SHORTS, "SHORT_9_16"),
        (Surface.TIKTOK, "SHORT_9_16"),
        (Surface.INSTAGRAM_REELS, "SHORT_9_16"),
        (Surface.INSTAGRAM_STORIES, "SHORT_9_16"),
        (Surface.FACEBOOK_REELS, "SHORT_9_16"),
    ],
)
def test_destination_binding_and_provider_plan_cover_all_surfaces(
    surface: Surface, format_kind: str
) -> None:
    package = _package(format_kind)
    binding = _binding(surface, str(package["package_id"]))
    attempt = PublicationControlPlane(_adapters()).prepare(package, binding)

    assert attempt.state is PublicationState.WRITE_AUTHORITY_REQUIRED
    assert attempt.plan.surface is surface
    assert any(request.mutation for request in attempt.plan.requests)
    assert any(not request.mutation for request in attempt.plan.requests)
    assert attempt.plan.destination_locale == "en"


def test_destination_locale_must_select_exact_package_language() -> None:
    package = _package("SHORT_9_16", locale="es")
    binding = _binding(Surface.INSTAGRAM_REELS, str(package["package_id"]), locale="en")
    with pytest.raises(PublicationContractError, match="exactly select"):
        PublicationControlPlane(_adapters()).prepare(package, binding)


def test_no_secret_serialization_and_request_plans_contain_no_credentials() -> None:
    for key in ("access_token", "refresh_token", "client_secret"):
        with pytest.raises(PublicationContractError, match="Secret-bearing"):
            assert_no_secret_serialization({key: "do-not-store"})

    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    for surface in (
        Surface.YOUTUBE_SHORTS,
        Surface.TIKTOK,
        Surface.INSTAGRAM_REELS,
        Surface.INSTAGRAM_STORIES,
        Surface.FACEBOOK_REELS,
    ):
        attempt = plane.prepare(package, _binding(surface, str(package["package_id"])))
        serialized = json.dumps(attempt.to_receipt()).casefold()
        assert "access_token" not in serialized
        assert "authorization" not in serialized
        assert "client_secret" not in serialized


def test_live_provider_mutation_is_compile_time_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("V2_VIDEO_WRITE_AUTHORITY", "true")
    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    attempt = plane.prepare(
        package, _binding(Surface.YOUTUBE_SHORTS, str(package["package_id"]))
    )

    with pytest.raises(WriteAuthorityError, match="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY"):
        plane.block_real_provider_mutation(attempt)

    assert attempt.state is PublicationState.WRITE_AUTHORITY_REQUIRED


def test_official_request_shapes_and_youtube_single_video_localization() -> None:
    longform = _package("LONGFORM_16_9")
    youtube = YouTubeAdapter()
    attempt = PublicationControlPlane(_adapters()).prepare(
        longform,
        _binding(Surface.YOUTUBE_NORMAL_VIDEO, str(longform["package_id"])),
    )
    operations = {request.operation: request for request in attempt.plan.requests}
    assert operations["initiate_resumable_video_upload"].official_contract == "videos.insert"
    assert operations["insert_timed_caption_track"].official_contract == "captions.insert"
    assert operations["caption_track_readback"].official_contract == "captions.list"
    assert operations["caption_track_content_readback"].official_contract == "captions.download"
    assert operations["processing_and_publication_readback"].official_contract == "videos.list"
    update = youtube.localized_metadata_update_request(
        "video-id",
        {"es": {"title": "Título", "description": "Descripción"}},
    )
    assert update.official_contract == "videos.update part=localizations"
    assert update.query == {"part": "localizations"}
    assert set(update.body) == {"id", "localizations"}
    assert update.body["localizations"]["es"]["title"] == "Título"
    assert youtube.alternate_audio_capability == "ACCOUNT_GATED_STUDIO_CAPABILITY"

    short = _package("SHORT_9_16")
    instagram = PublicationControlPlane(_adapters()).prepare(
        short, _binding(Surface.INSTAGRAM_STORIES, str(short["package_id"]))
    )
    container = next(
        item for item in instagram.plan.requests if item.operation == "create_media_container"
    )
    assert container.body["media_type"] == "STORIES"
    assert "caption" not in container.body
    resumable = InstagramAdapter().resumable_upload_contract(
        short,
        _binding(Surface.INSTAGRAM_STORIES, str(short["package_id"])),
    )
    assert resumable[0].body == {"media_type": "STORIES", "upload_type": "resumable"}
    assert resumable[1].endpoint == "{official_provider_upload_uri_for_ig_container}"

    facebook = PublicationControlPlane(_adapters()).prepare(
        short, _binding(Surface.FACEBOOK_REELS, str(short["package_id"]))
    )
    assert {request.official_contract for request in facebook.plan.requests} >= {
        "Page Reels upload_phase=start",
        "rupload.facebook.com video upload",
        "Page Reels upload_phase=finish",
        "Facebook Reel status readback",
    }
    reel_start = next(
        item for item in facebook.plan.requests if item.operation == "initialize_reel_upload"
    )
    reel_finish = next(
        item for item in facebook.plan.requests if item.operation == "finish_and_publish_reel"
    )
    assert reel_start.endpoint.endswith("/{api_version}/me/video_reels")
    assert reel_finish.endpoint.endswith("/{api_version}/me/video_reels")


def test_tiktok_is_upload_draft_not_direct_post() -> None:
    package = _package("SHORT_9_16")
    invalid = _binding(
        Surface.TIKTOK,
        str(package["package_id"]),
        capability=AdapterCapabilityState.PRODUCT_POLICY_BLOCKED,
    )
    with pytest.raises(PublicationContractError, match="PRODUCTION_REVIEW_REQUIRED"):
        PublicationControlPlane(_adapters()).prepare(package, invalid)

    valid = _binding(Surface.TIKTOK, str(package["package_id"]))
    attempt = PublicationControlPlane(_adapters()).prepare(package, valid)
    operations = {request.operation: request for request in attempt.plan.requests}
    init = operations["initialize_upload_to_tiktok_draft"]
    assert init.endpoint.endswith("/v2/post/publish/inbox/video/init/")
    assert init.body == {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": 1000,
            "chunk_size": 1000,
            "total_chunk_count": 1,
        }
    }
    assert "post_info" not in init.body
    transfer = operations["transfer_video_bytes_to_provider_upload_url"]
    assert transfer.method == "PUT"
    assert transfer.endpoint == "{provider_returned_upload_url}"
    assert transfer.headers == {
        "Content-Type": "video/mp4",
        "Content-Length": 1000,
        "Content-Range": "bytes 0-999/1000",
    }
    status = operations["draft_delivery_status_readback"]
    assert status.endpoint.endswith("/v2/post/publish/status/fetch/")
    assert status.body == {"publish_id": "{publish_id}"}
    assert TIKTOK_DRAFT_DELIVERY_SEMANTICS in attempt.plan.capability_notes
    assert attempt.binding.delivery_intent is DeliveryIntent.DRAFT_DELIVERY
    assert attempt.binding.desired_publication_mode is None
    readiness = TikTokUploadDraftAdapter().identity_readiness(valid)
    assert readiness["identity_kind"] == "TIKTOK_OPEN_ID"
    assert readiness["production_eligibility"] == "PRODUCTION_REVIEW_REQUIRED"
    assert "creator_username" not in readiness
    serialized_plan = json.dumps(attempt.plan.to_dict())
    assert "video.publish" not in serialized_plan
    assert "/v2/post/publish/video/init/" not in serialized_plan
    query = TikTokUploadDraftAdapter.public_video_query_request_after_status(
        {
            "status": "PUBLISH_COMPLETE",
            "publicaly_available_post_id": ["public-id"],
        }
    )
    assert query.endpoint.endswith("/v2/video/query/")
    with pytest.raises(PublicationContractError, match="public video ID"):
        TikTokUploadDraftAdapter.public_video_query_request_after_status(
            {"status": "SEND_TO_USER_INBOX", "publicaly_available_post_id": []}
        )


def test_tiktok_creator_finalization_can_optionally_strengthen_public_readback() -> None:
    result = TikTokUploadDraftAdapter.reconcile_public_video_after_creator_finalization(
        {
            "status": "PUBLISH_COMPLETE",
            "publicaly_available_post_id": ["public-video-id"],
        },
        {
            "videos": [
                {
                    "id": "public-video-id",
                    "title": "Creator-finalized title",
                    "duration": 58,
                    "width": 1080,
                    "height": 1920,
                    "share_url": "https://www.tiktok.com/example",
                }
            ]
        },
    )
    assert result.matched is True
    assert result.provider_object_id == "public-video-id"


def test_tiktok_ambiguous_draft_acceptance_blocks_retry_then_reconciles() -> None:
    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    attempt = plane.prepare(
        package, _binding(Surface.TIKTOK, str(package["package_id"]))
    )
    result = DeterministicFakeProvider().execute(
        plane,
        attempt,
        ambiguous_after_transfer=True,
        readback_discovers_object=True,
    )
    assert result["blind_retry_blocked"] is True
    assert attempt.state is PublicationState.READBACK_CONFIRMED
    assert attempt.reconciliation.provider_object_id is None
    assert attempt.reconciliation.checks["draft_delivered_to_creator_inbox"] is True


def test_instagram_login_variants_are_explicit_and_do_not_cross_contracts() -> None:
    package = _package("SHORT_9_16")
    adapter = InstagramAdapter()
    plane = PublicationControlPlane(_adapters())
    instagram_login = _binding(Surface.INSTAGRAM_REELS, str(package["package_id"]))
    facebook_login = replace(
        instagram_login,
        instagram_login_variant=InstagramLoginVariant.FACEBOOK_LOGIN,
        provider_intent_version="facebook-login-v1",
    )

    direct_plan = plane.prepare(package, instagram_login).plan
    facebook_plan = plane.prepare(package, facebook_login).plan
    assert all(
        request.endpoint.startswith("https://graph.instagram.com")
        or request.endpoint.startswith("{official_provider_upload_uri")
        for request in direct_plan.requests
    )
    assert all(
        request.endpoint.startswith("https://graph.facebook.com")
        for request in facebook_plan.requests
    )
    direct_readiness = adapter.identity_readiness(instagram_login)
    facebook_readiness = adapter.identity_readiness(facebook_login)
    assert direct_readiness["principal"] == (
        "INSTAGRAM_USER_ACCESS_TOKEN_NO_FACEBOOK_PAGE_DEPENDENCY"
    )
    assert direct_readiness["facebook_page_dependency"] is False
    assert direct_readiness["permissions"] == [
        "instagram_business_basic",
        "instagram_business_content_publish",
    ]
    assert facebook_readiness["facebook_page_dependency"] is True
    assert facebook_readiness["permissions"] == [
        "pages_show_list",
        "instagram_basic",
        "instagram_content_publish",
        "pages_read_engagement",
    ]

    for surface in (Surface.INSTAGRAM_REELS, Surface.INSTAGRAM_STORIES):
        direct_binding = _binding(surface, str(package["package_id"]))
        page_binding = replace(
            direct_binding,
            instagram_login_variant=InstagramLoginVariant.FACEBOOK_LOGIN,
            provider_intent_version=f"{surface.value}-facebook-login-v1",
        )
        direct = plane.prepare(package, direct_binding).plan
        page = plane.prepare(package, page_binding).plan
        assert all(
            request.endpoint.startswith("https://graph.instagram.com")
            for request in direct.requests
        )
        assert all(
            request.endpoint.startswith("https://graph.facebook.com")
            for request in page.requests
        )


def test_instagram_story_readback_does_not_require_permalink() -> None:
    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    attempt = plane.prepare(
        package,
        _binding(Surface.INSTAGRAM_STORIES, str(package["package_id"])),
    )
    result = DeterministicFakeProvider().execute(plane, attempt)
    assert result["reconciliation_matched"] is True
    assert attempt.reconciliation.checks["story_permalink_requirement"] == "NOT_REQUIRED"
    assert "story_permalink_not_required_or_guaranteed" in attempt.reconciliation.unresolved


def test_state_machine_reconciles_success_and_blocks_blind_unknown_retry() -> None:
    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    fake = DeterministicFakeProvider()

    success = plane.prepare(
        package, _binding(Surface.FACEBOOK_REELS, str(package["package_id"]))
    )
    result = fake.execute(plane, success)
    assert result["reconciliation_matched"] is True
    assert success.state is PublicationState.READBACK_CONFIRMED

    ambiguous = plane.prepare(
        package,
        _binding(
            Surface.FACEBOOK_REELS,
            str(package["package_id"]),
            intent="ambiguous-v1",
        ),
    )
    recovered = fake.execute(
        plane,
        ambiguous,
        ambiguous_after_transfer=True,
        readback_discovers_object=True,
    )
    assert recovered["blind_retry_blocked"] is True
    assert ambiguous.state is PublicationState.READBACK_CONFIRMED

    unresolved_attempt = plane.prepare(
        package,
        _binding(
            Surface.FACEBOOK_REELS,
            str(package["package_id"]),
            intent="unresolved-v1",
        ),
    )
    unresolved = fake.execute(
        plane,
        unresolved_attempt,
        ambiguous_after_transfer=True,
        readback_discovers_object=False,
    )
    assert unresolved["blind_retry_blocked"] is True
    assert unresolved_attempt.state is PublicationState.UNKNOWN_WRITE
    with pytest.raises(UnknownWriteRetryError):
        plane.assert_retry_allowed(unresolved_attempt)


def test_attempt_identity_is_deterministic_and_intent_sensitive() -> None:
    package = _package("SHORT_9_16")
    plane = PublicationControlPlane(_adapters())
    binding = _binding(Surface.YOUTUBE_SHORTS, str(package["package_id"]))
    first = plane.prepare(package, binding)
    second = plane.prepare(package, binding)
    changed = plane.prepare(
        package,
        _binding(
            Surface.YOUTUBE_SHORTS,
            str(package["package_id"]),
            intent="v2",
        ),
    )
    assert first.attempt_id == second.attempt_id
    assert first.attempt_id != changed.attempt_id

    instagram = _binding(Surface.INSTAGRAM_REELS, str(package["package_id"]))
    instagram_changed = replace(
        instagram,
        instagram_login_variant=InstagramLoginVariant.FACEBOOK_LOGIN,
    )
    assert plane.prepare(package, instagram).attempt_id != plane.prepare(
        package, instagram_changed
    ).attempt_id

    draft = _binding(Surface.TIKTOK, str(package["package_id"]))
    publication = replace(
        draft,
        delivery_intent=DeliveryIntent.PUBLICATION,
        desired_publication_mode="PUBLIC",
    )
    assert deterministic_attempt_id(draft) != deterministic_attempt_id(publication)


def test_complete_six_surface_shadow_demo_and_zero_mutation_counters(tmp_path: Path) -> None:
    longform_path = tmp_path / "longform.json"
    short_path = tmp_path / "short.json"
    longform_path.write_text(json.dumps(_package("LONGFORM_16_9")), encoding="utf-8")
    short_path.write_text(json.dumps(_package("SHORT_9_16")), encoding="utf-8")

    report = run_shadow_demo(
        longform_package_path=longform_path,
        short_package_path=short_path,
        output_root=tmp_path / "shadow",
    )

    assert report["result"] == "PASS_SHADOW_PUBLICATION_CLOSED_LOOP"
    assert len(report["surface_traces"]) == 6
    assert {trace["final_state"] for trace in report["surface_traces"]} == {
        "READBACK_CONFIRMED"
    }
    assert report["unknown_write"]["positive_recovery"]["blind_retry_blocked"] is True
    assert report["unknown_write"]["unresolved_negative"]["receipt"]["state"] == "UNKNOWN_WRITE"
    tiktok = next(
        trace for trace in report["surface_traces"] if trace["surface"] == "TIKTOK"
    )
    assert tiktok["public_post_confirmed"] is False
    assert tiktok["creator_finalization_required"] is True
    assert tiktok["provider_object_id"] is None
    tiktok_receipt = json.loads(Path(tiktok["receipt"]).read_text(encoding="utf-8"))
    assert "PUBLISHED_UNCONFIRMED" not in {
        event["state"] for event in tiktok_receipt["history"]
    }
    assert any(
        event["state"] == "DRAFT_DELIVERED_TO_CREATOR"
        for event in tiktok_receipt["history"]
    )
    assert all(value == 0 for value in report["operations"].values())


def test_publication_control_plane_has_no_v1_scheduler_browser_or_render_execution() -> None:
    source_root = REPO / "video" / "official_platform_publication_v1"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")
    ).casefold()
    assert "live_contentops" not in source
    assert "win32cred" not in source
    assert "credential manager" not in source
    assert "daily_app" not in source
    assert "newsroom_assignment_scheduler" not in source
    assert "scheduler_mutation_authority" in source
    assert "subprocess" not in source
    assert "selenium" not in source
    assert "playwright" not in source
    assert "remotion render" not in source
    assert "ffmpeg" not in source
