"""Rights-bound local asset routing for the isolated Tier-2 V2 renderer.

This module can copy governed deterministic assets, request an explicitly
illustrative image through the accepted direct image boundary, or retrieve a
real-entity photo only when reusable rights are explicit. It performs no browser,
CDP, upload, publication, or production-store action.
"""
from __future__ import annotations

import hashlib
import io
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image

from .direct_image_api_v1 import generate_image


ALLOWED_RIGHTS = frozenset(
    {
        "public_domain_us_government",
        "public_domain",
        "cc0",
        "cc_by",
        "cc_by_sa",
    }
)
MAX_PHOTO_BYTES = 15 * 1024 * 1024


class AssetRightsError(RuntimeError):
    """A fail-closed asset rights or provenance error."""


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    media_role: str
    local_path: str
    sha256: str
    source_url: str | None
    asset_url: str | None
    rights_classification: str
    license_url: str | None
    attribution: str | None
    retrieved_at_utc: str
    synthetic: bool
    documentary_authority: bool
    provider: str | None = None
    model: str | None = None
    prompt_hash: str | None = None
    invocation_id: str | None = None
    disclosure: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_https_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise AssetRightsError(f"{label}_must_be_public_https")
    if parsed.query and any(token in parsed.query.lower() for token in ("token=", "sig=", "key=")):
        raise AssetRightsError(f"{label}_appears_signed_or_secret_bearing")
    return value


def _validate_image_bytes(content: bytes) -> tuple[str, int, int]:
    if not content or len(content) > MAX_PHOTO_BYTES:
        raise AssetRightsError("entity_photo_size_out_of_bounds")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            suffix = ".png" if image.format == "PNG" else ".jpg"
    except Exception as exc:
        raise AssetRightsError("entity_photo_invalid_image") from exc
    if width < 320 or height < 320:
        raise AssetRightsError("entity_photo_resolution_too_small")
    return suffix, int(width), int(height)


def stage_governed_asset(
    *,
    asset_id: str,
    source: str | Path,
    expected_sha256: str,
    output_dir: str | Path,
    source_url: str,
    rights_classification: str,
    media_role: str = "factual_visual",
) -> AssetRecord:
    source_path = Path(source).resolve()
    if not source_path.is_file():
        raise AssetRightsError(f"governed_asset_missing:{asset_id}")
    actual = _sha256(source_path)
    if actual != expected_sha256:
        raise AssetRightsError(f"governed_asset_hash_mismatch:{asset_id}")
    if rights_classification not in ALLOWED_RIGHTS | {"capital_chronicle_owned", "capital_chronicle_internal"}:
        raise AssetRightsError(f"governed_asset_rights_unclear:{asset_id}")
    destination = Path(output_dir) / f"{asset_id}-{actual[:12]}{source_path.suffix.lower()}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source_path, destination)
    return AssetRecord(
        asset_id=asset_id,
        media_role=media_role,
        local_path=str(destination),
        sha256=actual,
        source_url=source_url,
        asset_url=None,
        rights_classification=rights_classification,
        license_url=None,
        attribution="Capital Chronicle governed source asset",
        retrieved_at_utc=_now(),
        synthetic=False,
        documentary_authority=True,
    )


PhotoGetter = Callable[[str, float], tuple[bytes, str]]


def _default_photo_get(url: str, timeout: float) -> tuple[bytes, str]:
    request = Request(url, headers={"Accept": "image/*", "User-Agent": "CapitalChronicleAssetResolver/1.0"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is validated above
        final_url = response.geturl()
        return response.read(MAX_PHOTO_BYTES + 1), final_url


def resolve_real_entity_photo(
    request: Mapping[str, Any],
    *,
    output_dir: str | Path,
    get: PhotoGetter | None = None,
    timeout_seconds: float = 30.0,
) -> AssetRecord:
    """Retrieve a real person's photo only with explicit reusable rights metadata."""
    required = ("asset_id", "entity_name", "source_page_url", "asset_url", "rights_classification", "attribution")
    missing = [key for key in required if not str(request.get(key) or "").strip()]
    if missing:
        raise AssetRightsError("entity_photo_missing_metadata:" + ",".join(missing))
    rights = str(request["rights_classification"])
    if rights not in ALLOWED_RIGHTS:
        raise AssetRightsError("entity_photo_rights_unclear")
    source_url = _validate_https_url(str(request["source_page_url"]), "source_page_url")
    asset_url = _validate_https_url(str(request["asset_url"]), "asset_url")
    license_url = str(request.get("license_url") or "").strip() or None
    if rights not in {"public_domain_us_government", "public_domain"} and not license_url:
        raise AssetRightsError("entity_photo_license_url_required")
    if license_url:
        _validate_https_url(license_url, "license_url")
    content, final_url = (get or _default_photo_get)(asset_url, timeout_seconds)
    _validate_https_url(final_url, "final_asset_url")
    if urlparse(final_url).hostname != urlparse(asset_url).hostname:
        raise AssetRightsError("entity_photo_cross_host_redirect_blocked")
    suffix, _width, _height = _validate_image_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    destination = Path(output_dir) / f"{request['asset_id']}-{digest[:12]}{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(content)
    return AssetRecord(
        asset_id=str(request["asset_id"]),
        media_role="real_entity_photo",
        local_path=str(destination),
        sha256=digest,
        source_url=source_url,
        asset_url=asset_url,
        rights_classification=rights,
        license_url=license_url,
        attribution=str(request["attribution"]),
        retrieved_at_utc=_now(),
        synthetic=False,
        documentary_authority=True,
        disclosure=f"Photograph of {request['entity_name']}; rights classified as {rights}.",
    )


def generate_illustrative_asset(
    *,
    asset_id: str,
    prompt: str,
    width: int,
    height: int,
    output_dir: str | Path,
    timeout_seconds: float = 180.0,
) -> tuple[AssetRecord | None, dict[str, Any]]:
    """Request one accepted gpt-5.5 illustration; never retry an ambiguous result."""
    destination = Path(output_dir) / f"{asset_id}.png"
    result = generate_image(
        model="gpt-5.5",
        prompt=prompt,
        width=width,
        height=height,
        output_file=destination,
        timeout_seconds=timeout_seconds,
        max_calls=1,
    )
    evidence = result.to_dict()
    if result.status != "SUCCESS" or not result.output_file or not result.output_sha256:
        return None, evidence
    return (
        AssetRecord(
            asset_id=asset_id,
            media_role="illustrative_enrichment",
            local_path=result.output_file,
            sha256=result.output_sha256,
            source_url=None,
            asset_url=None,
            rights_classification="provider_generated_terms_reviewed_for_v2_proof",
            license_url=None,
            attribution="AI-generated illustration; Capital Chronicle art direction",
            retrieved_at_utc=_now(),
            synthetic=True,
            documentary_authority=False,
            provider=result.provider,
            model=result.effective_model or result.requested_model,
            prompt_hash=result.prompt_hash,
            invocation_id=result.invocation_id,
            disclosure="ILLUSTRATION — not a photograph, event record, or factual evidence.",
        ),
        evidence,
    )
