"""CORE V0 platform visual adaptation.

TASK_CONTENTOPS_CORE_V0_PORTFOLIO_SELECTION_AND_PLATFORM_VISUAL_ADAPTATION_CORRECTION_V1
— ``SHADOW_ONLY``.

One canonical adaptation path, not nine independent adapters: every destination resolves a
platform spec from a single table and runs through the same deterministic derivative
builder.

Adaptation is deliberately conservative:

* charts and document excerpts are **contain-fitted onto a padded canvas**, never cropped,
  so axes, legends, uncertainty labels, and source notes cannot be cut off;
* only committed rights-cleared assets and already-authorized deterministic graphics are
  used — no external provider, image search, network call, or model call;
* an official-document excerpt is never restyled into event imagery; it is padded and
  scaled only, and its rights/provenance reference travels with the derivative;
* a destination that requires a visual and has no compatible rights-cleared source fails
  closed rather than receiving a fabricated image.

Derivatives are byte-deterministic: the encoder is pinned and no timestamp, random seed, or
wall-clock value enters the output.
"""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "contentops.core_v0_platform_visual_adaptation.v1"

#: Generator identity recorded on every derivative this module produces.
DERIVATIVE_GENERATOR = "contentops.core_v0_platform_visual_adapter.v1"
DERIVATIVE_GENERATOR_VERSION = "1.0.0"

#: Modalities whose informational content must survive intact. These are never cropped.
LABEL_CRITICAL_MODALITIES = frozenset({"chart", "document_excerpt"})

#: Rights statuses accepted without operator review, mirroring the visual policy.
CLEARED_RIGHTS_STATUSES = frozenset(
    {"public_domain", "official_press_reuse", "licensed", "capital_chronicle_owned"}
)

#: One canonical spec per destination. ``derivative_role`` states what the image is for;
#: ``requires_visual`` marks a destination that fails closed without one.
PLATFORM_VISUAL_SPECS: dict[str, dict[str, Any]] = {
    "instagram_business": {
        "aspect_ratio": "4:5",
        "width": 1080,
        "height": 1350,
        "derivative_role": "feed_portrait_primary",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 6,
        "text_density_limit_pct": 20,
        "requires_visual": True,
    },
    "linkedin": {
        "aspect_ratio": "1.91:1",
        "width": 1200,
        "height": 628,
        "derivative_role": "landscape_feed_card",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 5,
        "text_density_limit_pct": 30,
        "requires_visual": False,
    },
    "substack_newsletter": {
        "aspect_ratio": "3:2",
        "width": 1456,
        "height": 971,
        "derivative_role": "newsletter_chart_figure",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 4,
        "text_density_limit_pct": 40,
        "requires_visual": False,
    },
    "x_twitter": {
        "aspect_ratio": "16:9",
        "width": 1200,
        "height": 675,
        "derivative_role": "landscape_summary_card",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 5,
        "text_density_limit_pct": 25,
        "requires_visual": False,
    },
    "facebook_page": {
        "aspect_ratio": "1.91:1",
        "width": 1200,
        "height": 628,
        "derivative_role": "landscape_feed_card",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 5,
        "text_density_limit_pct": 30,
        "requires_visual": False,
    },
    "telegram": {
        "aspect_ratio": "16:9",
        "width": 1280,
        "height": 720,
        "derivative_role": "channel_preview_image",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 4,
        "text_density_limit_pct": 35,
        "requires_visual": False,
    },
    "discord": {
        "aspect_ratio": "16:9",
        "width": 1280,
        "height": 720,
        "derivative_role": "embed_preview_image",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 4,
        "text_density_limit_pct": 35,
        "requires_visual": False,
    },
    "youtube_community": {
        "aspect_ratio": "1:1",
        "width": 1080,
        "height": 1080,
        "derivative_role": "community_square_image",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 6,
        "text_density_limit_pct": 25,
        "requires_visual": False,
    },
    "threads": {
        "aspect_ratio": "4:5",
        "width": 1080,
        "height": 1350,
        "derivative_role": "feed_portrait_secondary",
        "fit_strategy": "CONTAIN_WITH_PADDING_NO_CROP",
        "safe_area_pct": 6,
        "text_density_limit_pct": 20,
        "requires_visual": False,
    },
}

#: Neutral padding colour. Opaque and content-free: it adds no editorial signal.
PADDING_RGBA = (255, 255, 255, 255)


class PlatformVisualAdaptationError(RuntimeError):
    """Fail-closed platform visual adaptation error."""


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()


def _slug(text: str, *, limit: int = 64) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in str(text).lower())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:limit].rstrip("-") or "asset"


def asset_is_rights_cleared(asset: Mapping[str, Any]) -> bool:
    """A source may only be adapted when its committed rights status is cleared."""
    return str(asset.get("rights_status") or "") in CLEARED_RIGHTS_STATUSES


def select_source_asset(
    *,
    platform_id: str,
    assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Pick the source asset for one destination, deterministically.

    Chart-bearing destinations prefer the primary quantitative chart so the adapted image
    carries the quantitative content; everything else takes the lead contextual asset.
    Only rights-cleared assets are ever considered.
    """
    cleared = [dict(asset) for asset in assets if asset_is_rights_cleared(asset)]
    if not cleared:
        return None
    preferred_roles = (
        ("primary_quantitative_chart", "lead_contextual", "document_excerpt")
        if platform_id in {"substack_newsletter", "linkedin", "telegram", "discord"}
        else ("lead_contextual", "primary_quantitative_chart", "document_excerpt")
    )
    for role in preferred_roles:
        matches = sorted(
            (row for row in cleared if str(row.get("role")) == role),
            key=lambda row: str(row.get("asset_id")),
        )
        if matches:
            return matches[0]
    return sorted(cleared, key=lambda row: str(row.get("asset_id")))[0]


def _contain_fit(
    source_width: int, source_height: int, target_width: int, target_height: int, safe_pct: int
) -> dict[str, Any]:
    """Compute a contain-fit box inside the safe area — no cropping, ever."""
    inset_x = round(target_width * safe_pct / 100)
    inset_y = round(target_height * safe_pct / 100)
    usable_width = target_width - 2 * inset_x
    usable_height = target_height - 2 * inset_y
    if usable_width <= 0 or usable_height <= 0:
        raise PlatformVisualAdaptationError("safe_area_leaves_no_usable_canvas")
    scale = min(usable_width / source_width, usable_height / source_height)
    scaled_width = max(1, int(source_width * scale))
    scaled_height = max(1, int(source_height * scale))
    return {
        "scale": round(scale, 8),
        "scaled_width": scaled_width,
        "scaled_height": scaled_height,
        "paste_x": inset_x + (usable_width - scaled_width) // 2,
        "paste_y": inset_y + (usable_height - scaled_height) // 2,
        "safe_area_inset_px": {"x": inset_x, "y": inset_y},
        "usable_area_px": {"width": usable_width, "height": usable_height},
        "pixels_cropped": 0,
    }


def build_platform_visual_binding(
    *,
    platform_id: str,
    asset: Mapping[str, Any],
    repo_root: Path,
    output_dir: Path,
    caption: str,
    source_note: str,
    chart_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce one deterministic derivative and its full adaptation binding.

    The source is scaled to fit inside the destination's safe area and centred on a padded
    canvas. Because the fit is *contain*, no source pixel is discarded: chart axes,
    legends, uncertainty labels, and source notes present in the source survive intact.
    """
    from PIL import Image

    spec = PLATFORM_VISUAL_SPECS.get(platform_id)
    if spec is None:
        raise PlatformVisualAdaptationError(f"unknown_platform_visual_spec:{platform_id}")
    if not asset_is_rights_cleared(asset):
        raise PlatformVisualAdaptationError(
            f"source_asset_rights_not_cleared:{asset.get('asset_id')}"
        )

    relative = str(asset.get("verified_local_path") or asset.get("path") or "")
    source_path = Path(repo_root) / relative
    if not source_path.is_file():
        raise PlatformVisualAdaptationError(f"source_asset_missing:{relative}")
    source_bytes = source_path.read_bytes()
    source_hash = sha256(source_bytes).hexdigest()
    declared = str(asset.get("sha256") or asset.get("verified_content_sha256") or "")
    if declared and declared != source_hash:
        raise PlatformVisualAdaptationError(
            f"source_asset_hash_mismatch:{asset.get('asset_id')}"
        )

    modality = str(asset.get("modality") or "")
    with Image.open(source_path) as handle:
        source = handle.convert("RGBA")
        source_width, source_height = source.size
        fit = _contain_fit(
            source_width, source_height, spec["width"], spec["height"], spec["safe_area_pct"]
        )
        canvas = Image.new("RGBA", (spec["width"], spec["height"]), PADDING_RGBA)
        resized = source.resize(
            (fit["scaled_width"], fit["scaled_height"]), Image.LANCZOS
        )
        canvas.paste(resized, (fit["paste_x"], fit["paste_y"]), resized)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{_slug(str(asset.get('asset_id')))}__{_slug(platform_id)}"
        f"__{spec['width']}x{spec['height']}.png"
    )
    derivative_path = output_dir / filename
    # Pinned encoder settings: no timestamp or metadata chunk enters the file, so repeated
    # runs are byte-identical.
    canvas.save(derivative_path, format="PNG", optimize=False, compress_level=6)
    derivative_bytes = derivative_path.read_bytes()

    binding = {
        "schema_version": SCHEMA_VERSION,
        "platform_id": platform_id,
        "source_asset_id": asset.get("asset_id"),
        "source_asset_sha256": source_hash,
        "source_local_path": relative,
        "source_modality": modality,
        "derivative_role": spec["derivative_role"],
        "target_aspect_ratio": spec["aspect_ratio"],
        "target_width": spec["width"],
        "target_height": spec["height"],
        "crop_fit_or_padding_strategy": spec["fit_strategy"],
        "crop_applied": False,
        "pixels_cropped": fit["pixels_cropped"],
        "scale_factor": fit["scale"],
        "scaled_width": fit["scaled_width"],
        "scaled_height": fit["scaled_height"],
        "safe_area": {
            "safe_area_pct": spec["safe_area_pct"],
            "inset_px": fit["safe_area_inset_px"],
            "usable_area_px": fit["usable_area_px"],
            "content_paste_origin_px": {"x": fit["paste_x"], "y": fit["paste_y"]},
        },
        "text_density_limit_pct": spec["text_density_limit_pct"],
        "filename": filename,
        "relative_path": str(Path(derivative_path).name),
        "mime_type": "image/png",
        "caption": caption,
        "alt_text": asset.get("alt_text"),
        "rights_provenance_reference": {
            "rights_status": asset.get("rights_status"),
            "publisher": asset.get("publisher"),
            "source_page_url": asset.get("source_page_url"),
            "publication_date": asset.get("publication_date"),
            "source_asset_sha256": source_hash,
        },
        "source_note": source_note,
        "source_note_preservation_rule": (
            "SOURCE_NOTE_TRAVELS_WITH_DERIVATIVE_AND_IS_NEVER_CROPPED_AWAY"
        ),
        "chart_label_preservation_rule": (
            "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED"
            if modality in LABEL_CRITICAL_MODALITIES
            else "NOT_APPLICABLE_NON_CHART_SOURCE"
        ),
        "chart_manifest_id": (chart_manifest or {}).get("chart_id"),
        "chart_manifest_sha256": (chart_manifest or {}).get("chart_sha256"),
        "derivative_generator": DERIVATIVE_GENERATOR,
        "derivative_generator_version": DERIVATIVE_GENERATOR_VERSION,
        "derivative_sha256": sha256(derivative_bytes).hexdigest(),
        "derivative_byte_length": len(derivative_bytes),
        "depicts_real_scene_as_photograph": False,
        "source_transformed_into_event_imagery": False,
        "external_provider_used": False,
        "image_search_performed": False,
        "network_call_performed": False,
        "model_call_performed": False,
        "operating_mode": "SHADOW_ONLY",
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "public_write_performed": False,
    }
    binding["binding_logical_hash"] = _logical_hash(
        {k: v for k, v in binding.items() if k != "binding_logical_hash"}
    )
    return binding


def adapt_package_visuals(
    *,
    platform_ids: Sequence[str],
    assets: Sequence[Mapping[str, Any]],
    repo_root: Path,
    output_dir: Path,
    caption: str,
    source_note: str,
    chart_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapt one package's bound visual across every destination on one canonical path.

    Destinations with no rights-cleared compatible source are reported explicitly: a
    visual-required destination is blocked, and an optional one is recorded as text-only.
    Nothing is fabricated to fill a slot.
    """
    bindings: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    text_only: list[dict[str, Any]] = []

    for platform_id in platform_ids:
        spec = PLATFORM_VISUAL_SPECS.get(platform_id)
        if spec is None:
            raise PlatformVisualAdaptationError(
                f"unknown_platform_visual_spec:{platform_id}"
            )
        source = select_source_asset(platform_id=platform_id, assets=assets)
        if source is None:
            row = {
                "platform_id": platform_id,
                "reason": "NO_RIGHTS_CLEARED_COMPATIBLE_VISUAL_ASSET",
                "image_fabricated_to_satisfy_platform": False,
                "derivative_produced": False,
            }
            if spec["requires_visual"]:
                blocked.append({**row, "outcome": "BLOCKED_VISUAL_REQUIRED_FAIL_CLOSED"})
            else:
                text_only.append({**row, "outcome": "TEXT_ONLY_NO_DERIVATIVE_REQUIRED"})
            continue
        bindings.append(
            build_platform_visual_binding(
                platform_id=platform_id,
                asset=source,
                repo_root=repo_root,
                output_dir=output_dir,
                caption=caption,
                source_note=source_note,
                chart_manifest=chart_manifest,
            )
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": DERIVATIVE_GENERATOR,
        "adapter_version": DERIVATIVE_GENERATOR_VERSION,
        "single_canonical_adaptation_path": True,
        "destination_count": len(platform_ids),
        "adapted_count": len(bindings),
        "blocked_count": len(blocked),
        "text_only_count": len(text_only),
        "explicit_outcome_count": len(bindings) + len(blocked) + len(text_only),
        "all_destinations_have_explicit_outcome": (
            len(bindings) + len(blocked) + len(text_only) == len(platform_ids)
        ),
        "bindings": bindings,
        "blocked_destinations": blocked,
        "text_only_destinations": text_only,
        "derivative_hashes": {
            str(row["platform_id"]): row["derivative_sha256"] for row in bindings
        },
        "external_provider_used": False,
        "network_call_performed": False,
        "model_call_performed": False,
        "operating_mode": "SHADOW_ONLY",
    }
