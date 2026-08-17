"""Run the six-surface deterministic shadow publication closed loop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .control_plane import PublicationControlPlane, WriteAuthorityError
from .fake_provider import DeterministicFakeProvider
from .models import (
    AdapterCapabilityState,
    DeliveryIntent,
    DestinationBinding,
    InstagramLoginVariant,
    Platform,
    Surface,
    load_publication_package,
)
from .providers import (
    FacebookReelsAdapter,
    InstagramAdapter,
    TikTokUploadDraftAdapter,
    YouTubeAdapter,
)


def adapter_registry() -> dict[Surface, Any]:
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


def _binding(surface: Surface, package_id: str, *, intent: str = "v1") -> DestinationBinding:
    values: dict[Surface, tuple[Platform, str, str, str, AdapterCapabilityState]] = {
        Surface.YOUTUBE_NORMAL_VIDEO: (
            Platform.YOUTUBE,
            "YOUTUBE_CHANNEL_ID",
            "UC_CAPITAL_CHRONICLE_SHADOW",
            "@CapitalChronicle",
            AdapterCapabilityState.APP_REVIEW_REQUIRED,
        ),
        Surface.YOUTUBE_SHORTS: (
            Platform.YOUTUBE,
            "YOUTUBE_CHANNEL_ID",
            "UC_CAPITAL_CHRONICLE_SHADOW",
            "@CapitalChronicle",
            AdapterCapabilityState.APP_REVIEW_REQUIRED,
        ),
        Surface.TIKTOK: (
            Platform.TIKTOK,
            "TIKTOK_OPEN_ID",
            "tiktok_open_id_shadow",
            "jimpham.cc",
            AdapterCapabilityState.PRODUCTION_REVIEW_REQUIRED,
        ),
        Surface.INSTAGRAM_REELS: (
            Platform.INSTAGRAM,
            "INSTAGRAM_PROFESSIONAL_ACCOUNT_ID",
            "ig_capital_chronicle_shadow",
            "@capitalchronicle",
            AdapterCapabilityState.ACCOUNT_SETUP_REQUIRED,
        ),
        Surface.INSTAGRAM_STORIES: (
            Platform.INSTAGRAM,
            "INSTAGRAM_BUSINESS_ACCOUNT_ID",
            "ig_capital_chronicle_shadow",
            "@capitalchronicle",
            AdapterCapabilityState.ACCOUNT_SETUP_REQUIRED,
        ),
        Surface.FACEBOOK_REELS: (
            Platform.FACEBOOK,
            "FACEBOOK_PAGE_ID",
            "fb_capital_chronicle_shadow",
            "Capital Chronicle",
            AdapterCapabilityState.ACCOUNT_SETUP_REQUIRED,
        ),
    }
    platform, identity_kind, identity_id, handle, state = values[surface]
    instagram_variant = None
    if surface is Surface.INSTAGRAM_REELS:
        instagram_variant = InstagramLoginVariant.INSTAGRAM_LOGIN
    elif surface is Surface.INSTAGRAM_STORIES:
        instagram_variant = InstagramLoginVariant.FACEBOOK_LOGIN
    return DestinationBinding(
        platform=platform,
        surface=surface,
        destination_identity_kind=identity_kind,
        expected_identity_id=identity_id,
        expected_public_handle=handle,
        destination_locale="en",
        package_id=package_id,
        delivery_intent=(
            DeliveryIntent.DRAFT_DELIVERY
            if surface is Surface.TIKTOK
            else DeliveryIntent.PUBLICATION
        ),
        desired_publication_mode=(None if surface is Surface.TIKTOK else "PUBLIC"),
        adapter_capability_state=state,
        instagram_login_variant=instagram_variant,
        provider_intent_version=intent,
    )


def run_shadow_demo(
    *, longform_package_path: Path, short_package_path: Path, output_root: Path
) -> dict[str, Any]:
    longform = load_publication_package(longform_package_path)
    short = load_publication_package(short_package_path)
    adapters = adapter_registry()
    plane = PublicationControlPlane(adapters)
    fake = DeterministicFakeProvider()
    output_root.mkdir(parents=True, exist_ok=True)

    packages = {
        Surface.YOUTUBE_NORMAL_VIDEO: longform,
        Surface.YOUTUBE_SHORTS: short,
        Surface.TIKTOK: short,
        Surface.INSTAGRAM_REELS: short,
        Surface.INSTAGRAM_STORIES: short,
        Surface.FACEBOOK_REELS: short,
    }
    traces: list[dict[str, Any]] = []
    for surface, package in packages.items():
        binding = _binding(surface, str(package["package_id"]))
        attempt = plane.prepare(package, binding)
        live_gate_blocked = False
        try:
            plane.block_real_provider_mutation(attempt)
        except WriteAuthorityError:
            live_gate_blocked = True
            attempt.record("LIVE_WRITE_AUTHORITY_PROOF_PASS")
        result = fake.execute(plane, attempt)
        receipt_path = output_root / f"{surface.value.casefold()}.receipt.json"
        receipt_path.write_text(
            json.dumps(result["receipt"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        traces.append(
            {
                "surface": surface.value,
                "package_id": package["package_id"],
                "attempt_id": attempt.attempt_id,
                "provider_object_id": attempt.reconciliation.provider_object_id,
                "public_post_confirmed": (
                    False if surface is Surface.TIKTOK else True
                ),
                "creator_finalization_required": surface is Surface.TIKTOK,
                "live_write_gate_blocked": live_gate_blocked,
                "fake_network_calls": 0,
                "final_state": attempt.state.value,
                "reconciliation_matched": result["reconciliation_matched"],
                "receipt": str(receipt_path.resolve()),
            }
        )

    unknown_binding = _binding(
        Surface.FACEBOOK_REELS,
        str(short["package_id"]),
        intent="unknown-write-recovery-v1",
    )
    unknown_attempt = plane.prepare(short, unknown_binding)
    recovered = fake.execute(
        plane,
        unknown_attempt,
        ambiguous_after_transfer=True,
        readback_discovers_object=True,
    )

    negative_binding = _binding(
        Surface.FACEBOOK_REELS,
        str(short["package_id"]),
        intent="unknown-write-negative-v1",
    )
    negative_attempt = plane.prepare(short, negative_binding)
    unresolved = fake.execute(
        plane,
        negative_attempt,
        ambiguous_after_transfer=True,
        readback_discovers_object=False,
    )

    report = {
        "schema": "contentops.v2.official_publication_shadow_demo.v1",
        "result": (
            "PASS_SHADOW_PUBLICATION_CLOSED_LOOP"
            if all(
                trace["live_write_gate_blocked"]
                and trace["final_state"] == "READBACK_CONFIRMED"
                and trace["reconciliation_matched"]
                for trace in traces
            )
            and recovered["blind_retry_blocked"]
            and recovered["receipt"]["state"] == "READBACK_CONFIRMED"
            and unresolved["blind_retry_blocked"]
            and unresolved["receipt"]["state"] == "UNKNOWN_WRITE"
            else "FAIL_SHADOW_PUBLICATION_CLOSED_LOOP"
        ),
        "real_packages": {
            "longform_manifest": str(longform_package_path.resolve()),
            "longform_package_id": longform["package_id"],
            "short_manifest": str(short_package_path.resolve()),
            "short_package_id": short["package_id"],
        },
        "surface_traces": traces,
        "unknown_write": {
            "positive_recovery": recovered,
            "unresolved_negative": unresolved,
        },
        "operations": {
            "real_provider_writes": 0,
            "private_unlisted_draft_writes": 0,
            "browser_actions": 0,
            "credential_reads": 0,
            "v1_mutations": 0,
            "scheduler_mutations": 0,
            "remotion_renders": 0,
            "localized_picture_renders": 0,
            "audio_generations": 0,
            "max_calls": 0,
            "ultra_calls": 0,
        },
    }
    report_path = output_root / "shadow_demo_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--longform-package", required=True, type=Path)
    parser.add_argument("--short-package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = run_shadow_demo(
        longform_package_path=args.longform_package,
        short_package_path=args.short_package,
        output_root=args.output_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS_SHADOW_PUBLICATION_CLOSED_LOOP" else 1


if __name__ == "__main__":
    raise SystemExit(main())
