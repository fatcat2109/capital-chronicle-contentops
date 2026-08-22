"""Deterministic derivative-media authority for ContentOps publication runs."""
from __future__ import annotations

import hashlib
import io
import mimetypes
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.delivery_media_manifest.v1"
MIN_CHART_WIDTH = 800
MIN_CHART_HEIGHT = 400
MAX_IMAGE_BYTES = 20 * 1024 * 1024
PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM = 0.93

_DISPLAY_PUNCTUATION_FALLBACK = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
)

_CHART_TITLES = {
    "primary": "Effective Fed Funds Rate Inside the Policy Corridor",
    "policy_corridor": "Federal Reserve Administered Rates and Effective Fed Funds",
    "sofr_context": "Rates Context: Overnight Policy Rate vs Treasury Curve Points",
}
_ARTICLE_SECTIONS = {
    "primary": "lede_and_current_policy_signal",
    "policy_corridor": "policy_transmission_mechanism",
    "sofr_context": "cross_asset_and_treasury_curve_context",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def original_substack_media_url(value: str) -> str:
    decoded = urllib.parse.unquote(str(value or ""))
    match = re.search(r"https://substack-post-media\.s3\.amazonaws\.com/public/images/[^?#\s]+", decoded)
    return match.group(0) if match else str(value or "")


def read_public_image_bytes(url: str, *, timeout_seconds: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "CapitalChronicleContentOps/6.0"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        content_type = str(response.headers.get("Content-Type") or "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError("public_media_url_is_not_image")
        value = response.read(MAX_IMAGE_BYTES + 1)
    if len(value) > MAX_IMAGE_BYTES:
        raise ValueError("public_media_exceeds_size_limit")
    return value


def image_metadata_from_bytes(value: bytes) -> dict[str, Any]:
    from PIL import Image

    image = Image.open(io.BytesIO(value))
    image.load()
    mime = Image.MIME.get(image.format or "") or "application/octet-stream"
    return {"mime_type": mime, "width": int(image.width), "height": int(image.height)}


def image_metadata_from_file(path: str | Path) -> dict[str, Any]:
    from PIL import Image

    target = Path(path)
    image = Image.open(target)
    image.load()
    mime = Image.MIME.get(image.format or "") or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return {"mime_type": mime, "width": int(image.width), "height": int(image.height)}


def _delivery_card_fonts() -> tuple[Any, Any, str, bool]:
    """Prefer repository-established Arial; retain a deterministic glyph-safe fallback."""
    from PIL import ImageFont

    candidates = (
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arial.ttf"),
        ("arial.ttf", "arial.ttf"),
        ("DejaVuSans.ttf", "DejaVuSans.ttf"),
    )
    for font_path, label in candidates:
        try:
            return (
                ImageFont.truetype(font_path, 34),
                ImageFont.truetype(font_path, 24),
                label,
                True,
            )
        except OSError:
            continue
    return ImageFont.load_default(), ImageFont.load_default(), "PIL_DEFAULT_ASCII_SAFE", False


def _glyph_safe_display_text(value: str, *, unicode_font_loaded: bool) -> str:
    source = " ".join(str(value or "").split())
    if unicode_font_loaded:
        return source
    punctuation_safe = source.translate(_DISPLAY_PUNCTUATION_FALLBACK)
    return (
        unicodedata.normalize("NFKD", punctuation_safe)
        .encode("ascii", errors="ignore")
        .decode("ascii")
    )


def _reader_facing_source_date(value: str | None) -> str | None:
    """Render a source date for readers without leaking a machine timestamp onto the card."""
    source = str(value or "").strip()
    if not source:
        return None
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(source.replace("Z", "+00:00"))
    except ValueError:
        # A source may already provide a reader-facing date instead of an ISO timestamp.
        return source
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def build_delivery_only_editorial_card(
    *,
    output_path: str | Path,
    title: str,
    source_label: str,
    source_page_url: str,
    published_at: str | None = None,
) -> dict[str, Any]:
    """Render a rights-safe delivery card that is never canonical article media.

    The card contains metadata and editorial packaging only: no synthetic documentary
    imagery, invented numbers, or claim-bearing chart. Capital Chronicle owns the rendered
    layout bytes; the source remains attributed and is not claimed as owned.
    """
    from PIL import Image, ImageDraw

    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1350, 1080), "#07111f")
    draw = ImageDraw.Draw(image)
    font, small, font_identity, unicode_font_loaded = _delivery_card_fonts()
    source_title = " ".join(str(title or "").split())
    display_title = _glyph_safe_display_text(
        source_title, unicode_font_loaded=unicode_font_loaded
    )

    def lines(value: str, width: int) -> list[str]:
        words = " ".join(str(value or "").split()).split()
        rows: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > width and current:
                rows.append(current)
                current = word
            else:
                current = candidate
        if current:
            rows.append(current)
        return rows

    draw.rectangle((72, 72, 1278, 1008), outline="#e0b85a", width=4)
    draw.text((110, 118), "CAPITAL CHRONICLE", fill="#e0b85a", font=small)
    draw.text((110, 174), "NEWSROOM BRIEF", fill="#94a3b8", font=small)
    y = 280
    for row in lines(display_title, 50)[:7]:
        draw.text((110, y), row, fill="#f8fafc", font=font)
        y += 58
    source_date = _reader_facing_source_date(published_at)
    source_text = f"Source: {source_label}"
    if source_date:
        source_text += f" | {source_date}"
    draw.text((110, 875), source_text[:92], fill="#cbd5e1", font=small)
    draw.text((110, 930), "Read the full brief on Capital Chronicle", fill="#e0b85a", font=small)
    image.save(target, format="PNG", optimize=True)
    metadata = image_metadata_from_file(target)
    return {
        "asset_id": "delivery_only_editorial_card",
        "media_role": "delivery_only",
        "path": str(target),
        "local_path": str(target),
        "absolute_local_source_path": str(target),
        "sha256": sha256_file(target),
        "caption": "Capital Chronicle delivery card for the governed article.",
        "alt_text": f"Capital Chronicle newsroom brief: {' '.join(title.split())}",
        "source_title": source_title,
        "display_title": display_title,
        "display_font_identity": font_identity,
        "unicode_font_loaded": unicode_font_loaded,
        "display_fallback_applied": display_title != source_title,
        "display_replacement_glyph_present": any(
            marker in display_title for marker in ("\ufffd", "\u25a1", "\u25a0")
        ),
        "source_label": str(source_label),
        "source_page_url": str(source_page_url),
        "source_published_at": str(published_at or "") or None,
        "reader_facing_source_date": source_date,
        "reader_facing_cta": "Read the full brief on Capital Chronicle",
        "provenance_status": "VERIFIED_SOURCE_METADATA_CONTENTOPS_RENDER",
        "rights_basis": "CONTENTOPS_OWNED_LAYOUT_SOURCE_METADATA_ONLY",
        "article_inclusion": False,
        "canonical_article_media": False,
        "delivery_only": True,
        "generated_documentary_imagery": False,
        **metadata,
    }


def visual_similarity_to_local_file(value: bytes, local_path: str | Path) -> float:
    from PIL import Image, ImageChops, ImageFilter, ImageStat

    reference = Image.open(Path(local_path)).convert("RGB").resize((96, 64))
    rendered = Image.open(io.BytesIO(value)).convert("RGB").resize((96, 64))
    rgb_difference = ImageChops.difference(reference, rendered)
    grayscale_difference = ImageChops.difference(reference.convert("L"), rendered.convert("L"))
    edge_difference = ImageChops.difference(
        reference.convert("L").filter(ImageFilter.FIND_EDGES),
        rendered.convert("L").filter(ImageFilter.FIND_EDGES),
    )
    rgb_error = sum(float(item) for item in ImageStat.Stat(rgb_difference).mean) / (3.0 * 255.0)
    grayscale_error = float(ImageStat.Stat(grayscale_difference).mean[0]) / 255.0
    edge_error = float(ImageStat.Stat(edge_difference).mean[0]) / 255.0
    return round(max(0.0, 1.0 - (0.50 * rgb_error + 0.20 * grayscale_error + 0.30 * edge_error)), 4)


def validate_chart_media_object(media: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    path = Path(str(media.get("absolute_local_source_path") or ""))
    if not path.is_absolute() or not path.is_file():
        blockers.append("absolute_local_source_path_required")
    if str(media.get("media_role") or "") != "primary_chart":
        blockers.append("primary_chart_role_required")
    width = int(media.get("width") or 0)
    height = int(media.get("height") or 0)
    if width < MIN_CHART_WIDTH or height < MIN_CHART_HEIGHT:
        blockers.append("chart_dimensions_below_threshold")
    if width and height and 0.90 <= width / height <= 1.10:
        blockers.append("square_branding_or_avatar_rejected")
    if not str(media.get("sha256") or ""):
        blockers.append("media_sha256_required")
    if not str(media.get("verified_public_delivery_url") or ""):
        blockers.append("verified_public_delivery_url_required")
    if media.get("local_public_hash_continuity") is not True:
        blockers.append("local_public_hash_continuity_required")
    return blockers


def validate_delivery_media_object(media: Mapping[str, Any]) -> list[str]:
    """Validate either an article chart or an explicitly delivery-only asset."""
    if str(media.get("media_role") or "") == "primary_chart":
        return validate_chart_media_object(media)
    blockers: list[str] = []
    path = Path(str(media.get("absolute_local_source_path") or ""))
    if not path.is_absolute() or not path.is_file():
        blockers.append("absolute_local_source_path_required")
    if str(media.get("media_role") or "") != "delivery_only":
        blockers.append("delivery_media_role_invalid")
    if int(media.get("width") or 0) < MIN_CHART_WIDTH or int(media.get("height") or 0) < MIN_CHART_HEIGHT:
        blockers.append("delivery_media_dimensions_below_threshold")
    if not str(media.get("sha256") or ""):
        blockers.append("media_sha256_required")
    if not str(media.get("verified_public_delivery_url") or ""):
        blockers.append("verified_public_delivery_url_required")
    if media.get("local_public_hash_continuity") is not True:
        blockers.append("local_public_hash_continuity_required")
    return blockers


def build_delivery_media_manifest(
    *,
    media_packet: Mapping[str, Any],
    public_image_urls: Sequence[str],
    run_id: str,
    remote_bytes_by_url: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    """Bind each approved local chart to an exact public object by SHA-256."""
    remote_objects: list[dict[str, Any]] = []
    for supplied_url in public_image_urls:
        original_url = original_substack_media_url(supplied_url)
        try:
            value = bytes((remote_bytes_by_url or {}).get(original_url) or read_public_image_bytes(original_url))
            metadata = image_metadata_from_bytes(value)
            remote_objects.append(
                {
                    "supplied_url": supplied_url,
                    "original_url": original_url,
                    "sha256": sha256_bytes(value),
                    **metadata,
                }
            )
        except Exception as exc:
            remote_objects.append(
                {
                    "supplied_url": supplied_url,
                    "original_url": original_url,
                    "sha256": None,
                    "error_class": type(exc).__name__,
                }
            )

    assets: list[dict[str, Any]] = []
    blockers: list[str] = []
    for source in media_packet.get("assets") or []:
        source_path = Path(str(source.get("path") or source.get("local_path") or "")).resolve()
        local_exists = source_path.is_file()
        local_sha = sha256_file(source_path) if local_exists else None
        declared_sha = str(source.get("sha256") or "") or None
        metadata = image_metadata_from_file(source_path) if local_exists else {"mime_type": None, "width": 0, "height": 0}
        public_match = next((item for item in remote_objects if local_sha and item.get("sha256") == local_sha), None)
        asset_id = str(source.get("asset_id") or "")
        row = {
            "media_asset_id": asset_id,
            "media_role": str(source.get("media_role") or ""),
            "absolute_local_source_path": str(source_path),
            "sha256": local_sha,
            "declared_sha256": declared_sha,
            "mime_type": metadata.get("mime_type"),
            "width": metadata.get("width"),
            "height": metadata.get("height"),
            "source_provenance": {
                "status": source.get("provenance_status"),
                "source_label": source.get("source_label"),
                "source_page_url": source.get("source_page_url"),
                "caption": source.get("caption"),
            },
            "chart_title": str(source.get("chart_title") or _CHART_TITLES.get(asset_id) or source.get("caption") or ""),
            "alt_text": str(source.get("alt_text") or ""),
            "canonical_article_section_association": str(
                source.get("canonical_article_section_association") or _ARTICLE_SECTIONS.get(asset_id) or asset_id
            ),
            "verified_public_delivery_url": public_match.get("original_url") if public_match else None,
            "public_delivery_sha256": public_match.get("sha256") if public_match else None,
            "local_public_hash_continuity": bool(public_match and local_sha == public_match.get("sha256")),
        }
        assets.append(row)
        if not local_exists:
            blockers.append(f"media_file_missing:{asset_id}")
        if declared_sha and local_sha != declared_sha:
            blockers.append(f"declared_local_hash_mismatch:{asset_id}")
        if not public_match:
            blockers.append(f"public_object_hash_match_missing:{asset_id}")

    primary = next((asset for asset in assets if asset.get("media_role") == "primary_chart"), None)
    if primary is None:
        primary = next((asset for asset in assets if asset.get("media_role") == "delivery_only"), None)
    if not primary:
        blockers.append("primary_chart_missing")
    else:
        blockers.extend(validate_delivery_media_object(primary))
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "authority": "approved_media_manifest_hash_binding_not_substack_dom_selection",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": list(dict.fromkeys(blockers)),
        "minimum_chart_dimensions": {"width": MIN_CHART_WIDTH, "height": MIN_CHART_HEIGHT},
        "assets": assets,
        "selected_primary_media_asset_id": primary.get("media_asset_id") if primary else None,
        "selected_primary_media_sha256": primary.get("sha256") if primary else None,
        "remote_objects_audited": remote_objects,
    }


def select_primary_chart(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("status") != "PASS":
        raise ValueError("delivery_media_manifest_not_pass")
    primary = next((dict(asset) for asset in manifest.get("assets") or [] if asset.get("media_role") == "primary_chart"), None)
    if not primary or validate_chart_media_object(primary):
        raise ValueError("approved_primary_chart_not_available")
    return primary


def select_primary_delivery_media(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("status") != "PASS":
        raise ValueError("delivery_media_manifest_not_pass")
    selected_id = str(manifest.get("selected_primary_media_asset_id") or "")
    primary = next(
        (dict(asset) for asset in manifest.get("assets") or []
         if str(asset.get("media_asset_id") or "") == selected_id),
        None,
    )
    if not primary or validate_delivery_media_object(primary):
        raise ValueError("approved_delivery_media_not_available")
    return primary
