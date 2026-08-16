from __future__ import annotations

import json
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
    DestinationBinding,
    Platform,
    PublicationContractError,
    PublicationState,
    Surface,
    assert_no_secret_serialization,
    load_publication_package,
)
from video.official_platform_publication_v1.providers import (
    FacebookReelsAdapter,
    InstagramAdapter,
    TikTokDirectPostAdapter,
    YouTubeAdapter,
)
from video.official_platform_publication_v1.providers.tiktok import (
    TIKTOK_AUTOMATION_ELIGIBILITY,
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
        Surface.TIKTOK: TikTokDirectPostAdapter(),
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
        AdapterCapabilityState.PRODUCT_POLICY_BLOCKED
        if surface is Surface.TIKTOK
        else AdapterCapabilityState.ACCOUNT_SETUP_REQUIRED
    )
    return DestinationBinding(
        platform=platform,
        surface=surface,
        destination_identity_kind=f"{platform.value}_IDENTITY_ID",
        expected_identity_id=f"{platform.value.casefold()}_shadow_id",
        expected_public_handle="Capital Chronicle",
        destination_locale=locale,
        package_id=package_id,
        desired_publication_mode="PUBLIC",
        adapter_capability_state=capability or default_capability,
        publication_intent_version=intent,
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
    with pytest.raises(PublicationContractError, match="Secret-bearing"):
        assert_no_secret_serialization({"access_token": "do-not-store"})

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
        "en",
        {"es": {"title": "Título", "description": "Descripción"}},
    )
    assert update.official_contract == "videos.update"
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


def test_tiktok_autonomous_internal_model_is_product_policy_blocked() -> None:
    package = _package("SHORT_9_16")
    invalid = _binding(
        Surface.TIKTOK,
        str(package["package_id"]),
        capability=AdapterCapabilityState.READY_FOR_FUTURE_LIVE_CANARY,
    )
    with pytest.raises(PublicationContractError, match="PRODUCT_POLICY_BLOCKED"):
        PublicationControlPlane(_adapters()).prepare(package, invalid)

    valid = _binding(Surface.TIKTOK, str(package["package_id"]))
    attempt = PublicationControlPlane(_adapters()).prepare(package, valid)
    assert TIKTOK_AUTOMATION_ELIGIBILITY in attempt.plan.capability_notes
    assert any("EXPRESS_CONSENT_REQUIRED" in note for note in attempt.plan.capability_notes)


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
    assert all(value == 0 for value in report["operations"].values())


def test_publication_control_plane_has_no_v1_scheduler_browser_or_render_execution() -> None:
    source_root = REPO / "video" / "official_platform_publication_v1"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")
    ).casefold()
    assert "import live_contentops" not in source
    assert "subprocess" not in source
    assert "selenium" not in source
    assert "playwright" not in source
    assert "remotion render" not in source
    assert "ffmpeg" not in source
