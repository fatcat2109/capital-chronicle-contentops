"""Narrow Cloudinary host for governed V1 delivery-only media.

Cloudinary is storage/transport only.  This module never selects article media,
changes editorial bytes, or grants publication authority.  A returned URL becomes
eligible only after the exact remote bytes match the approved local SHA-256.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.media_manifest_authority_v1 import (
    SCHEMA_VERSION as DELIVERY_MANIFEST_SCHEMA_VERSION,
    image_metadata_from_bytes,
    image_metadata_from_file,
    read_public_image_bytes,
    sha256_bytes,
    sha256_file,
)


PROVIDER = "cloudinary"
PROVIDER_CONTRACT_VERSION = "contentops.cloudinary_delivery_media.v1"
REQUIRED_ENV_VAR_NAMES = (
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)
READY = "CLOUDINARY_DELIVERY_MEDIA_READY"
NOT_REQUIRED = "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED"


def credential_presence(environment: Mapping[str, str] | None = None) -> dict[str, bool]:
    """Return names and booleans only; credential values never leave this module."""
    source = environment if environment is not None else os.environ
    return {name: bool(str(source.get(name) or "").strip()) for name in REQUIRED_ENV_VAR_NAMES}


def deterministic_cloudinary_public_id(*, work_item_id: str, asset_sha256: str) -> str:
    """Bind one stable provider object to the immutable work item and asset bytes."""
    safe_work_item = re.sub(r"[^a-z0-9_-]+", "-", str(work_item_id).casefold()).strip("-")
    digest = str(asset_sha256).casefold()
    if not safe_work_item or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("cloudinary_delivery_identity_inputs_invalid")
    return f"capital_chronicle/v1/delivery_only/{safe_work_item}/{digest}"


def deterministic_cloudinary_delivery_url(
    *, cloud_name: str, public_id: str, mime_type: str
) -> str:
    """Return the versionless URL for the immutable deterministic provider object."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", cloud_name):
        raise ValueError("cloudinary_cloud_name_invalid")
    extension_by_mime = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    extension = extension_by_mime.get(str(mime_type or "").casefold())
    if not extension:
        raise ValueError("cloudinary_delivery_mime_type_unsupported")
    encoded_id = urllib.parse.quote(str(public_id), safe="/_-")
    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{encoded_id}.{extension}"


def _multipart_body(
    *, fields: Mapping[str, str], file_path: Path, mime_type: str, boundary: str
) -> bytes:
    rows: list[bytes] = []
    for name in sorted(fields):
        rows.extend(
            (
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
                str(fields[name]).encode("utf-8"),
                b"\r\n",
            )
        )
    rows.extend(
        (
            f"--{boundary}\r\n".encode("ascii"),
            (
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
                f"Content-Type: {mime_type}\r\n\r\n"
            ).encode("utf-8"),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("ascii"),
        )
    )
    return b"".join(rows)


def _upload_asset(
    *,
    cloud_name: str,
    api_key: str,
    api_secret: str,
    public_id: str,
    file_path: Path,
    mime_type: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", cloud_name):
        raise ValueError("cloudinary_cloud_name_invalid")
    boundary = "----ContentOpsCloudinaryV1" + sha256_bytes(public_id.encode("utf-8"))[:20]
    body = _multipart_body(
        fields={
            "overwrite": "false",
            "public_id": public_id,
            "unique_filename": "false",
            "use_filename": "false",
        },
        file_path=file_path,
        mime_type=mime_type,
        boundary=boundary,
    )
    token = base64.b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "CapitalChronicleContentOps/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return dict(payload)


def _verify_remote_object(
    *,
    public_url: str,
    expected_sha256: str,
    expected_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(str(public_url or ""))
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        return {"status": "BLOCKED_CLOUDINARY_PUBLIC_URL_INVALID"}
    try:
        remote_bytes = read_public_image_bytes(public_url)
        remote_metadata = image_metadata_from_bytes(remote_bytes)
    except Exception as exc:
        return {
            "status": "BLOCKED_CLOUDINARY_HOSTED_MEDIA_UNREADABLE",
            "safe_error_classification": type(exc).__name__,
        }
    remote_sha256 = sha256_bytes(remote_bytes)
    blockers: list[str] = []
    if remote_sha256 != expected_sha256:
        blockers.append("cloudinary_remote_sha256_mismatch")
    if str(remote_metadata.get("mime_type") or "") != str(expected_metadata.get("mime_type") or ""):
        blockers.append("cloudinary_remote_mime_type_mismatch")
    if int(remote_metadata.get("width") or 0) != int(expected_metadata.get("width") or 0):
        blockers.append("cloudinary_remote_width_mismatch")
    if int(remote_metadata.get("height") or 0) != int(expected_metadata.get("height") or 0):
        blockers.append("cloudinary_remote_height_mismatch")
    return {
        "status": "PASS" if not blockers else "BLOCKED_CLOUDINARY_HOSTED_MEDIA_MISMATCH",
        "blockers": blockers,
        "remote_sha256": remote_sha256,
        "remote_metadata": remote_metadata,
    }


def _validated_local_asset(asset: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    row = dict(asset)
    asset_id = str(row.get("asset_id") or "delivery_only")
    path = Path(str(row.get("absolute_local_source_path") or row.get("local_path") or row.get("path") or ""))
    blockers: list[str] = []
    if str(row.get("media_role") or "") != "delivery_only":
        blockers.append(f"delivery_media_role_invalid:{asset_id}")
    if row.get("article_inclusion") is not False:
        blockers.append(f"delivery_media_article_inclusion_not_false:{asset_id}")
    if row.get("canonical_article_media") is not False:
        blockers.append(f"delivery_media_canonical_article_media_not_false:{asset_id}")
    if row.get("delivery_only") is not True:
        blockers.append(f"delivery_only_flag_missing:{asset_id}")
    if not str(row.get("provenance_status") or "").startswith("VERIFIED_"):
        blockers.append(f"delivery_media_provenance_not_verified:{asset_id}")
    if not str(row.get("rights_basis") or ""):
        blockers.append(f"delivery_media_rights_basis_missing:{asset_id}")
    if not path.is_absolute() or not path.is_file():
        blockers.append(f"delivery_media_local_file_missing:{asset_id}")
        return None, blockers
    try:
        actual_sha256 = sha256_file(path)
        metadata = image_metadata_from_file(path)
    except Exception as exc:
        blockers.append(f"delivery_media_local_image_invalid:{asset_id}:{type(exc).__name__}")
        return None, blockers
    declared_sha256 = str(row.get("sha256") or "").casefold()
    if not re.fullmatch(r"[0-9a-f]{64}", declared_sha256):
        blockers.append(f"delivery_media_declared_sha256_invalid:{asset_id}")
    elif declared_sha256 != actual_sha256:
        blockers.append(f"delivery_media_declared_sha256_mismatch:{asset_id}")
    for key in ("width", "height"):
        declared = int(row.get(key) or 0)
        if declared and declared != int(metadata.get(key) or 0):
            blockers.append(f"delivery_media_declared_{key}_mismatch:{asset_id}")
    declared_mime = str(row.get("mime_type") or "")
    if declared_mime and declared_mime != str(metadata.get("mime_type") or ""):
        blockers.append(f"delivery_media_declared_mime_type_mismatch:{asset_id}")
    return {
        **row,
        "asset_id": asset_id,
        "absolute_local_source_path": str(path.resolve()),
        "sha256": actual_sha256,
        **metadata,
    }, blockers


def prepare_cloudinary_delivery_media(
    *,
    work_item_id: str,
    delivery_only_assets: Sequence[Mapping[str, Any]],
    existing_manifest: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Upload or reuse exact delivery-only bytes and return a governed manifest."""
    if not delivery_only_assets:
        return {
            "status": NOT_REQUIRED,
            "provider_calls": 0,
            "credential_presence": credential_presence(environment),
        }
    source = environment if environment is not None else os.environ
    presence = credential_presence(source)
    missing = [name for name, present in presence.items() if not present]
    if missing:
        return {
            "status": "BLOCKED_CLOUDINARY_CREDENTIALS_MISSING",
            "missing_environment_variable_names": missing,
            "credential_presence": presence,
            "provider_calls": 0,
        }
    cloud_name = str(source.get("CLOUDINARY_CLOUD_NAME") or "").strip()
    api_key = str(source.get("CLOUDINARY_API_KEY") or "").strip()
    api_secret = str(source.get("CLOUDINARY_API_SECRET") or "").strip()
    previous = {
        str(row.get("media_asset_id") or ""): dict(row)
        for row in ((existing_manifest or {}).get("assets") or [])
        if isinstance(row, Mapping)
    }
    prepared: list[dict[str, Any]] = []
    provider_calls = 0
    reused_count = 0
    blockers: list[str] = []
    for raw in delivery_only_assets:
        local, local_blockers = _validated_local_asset(raw)
        blockers.extend(local_blockers)
        if local is None or local_blockers:
            continue
        asset_id = str(local["asset_id"])
        public_id = deterministic_cloudinary_public_id(
            work_item_id=work_item_id, asset_sha256=str(local["sha256"])
        )
        prior = previous.get(asset_id, {})
        public_url = ""
        provider_asset_id = None
        reused = False
        if (
            str(prior.get("provider") or "") == PROVIDER
            and str(prior.get("provider_public_id") or "") == public_id
            and str(prior.get("sha256") or "") == str(local["sha256"])
            and str(prior.get("verified_public_delivery_url") or "").startswith("https://")
        ):
            public_url = str(prior["verified_public_delivery_url"])
            provider_asset_id = prior.get("provider_asset_id")
            reused = True
        else:
            candidate_url = deterministic_cloudinary_delivery_url(
                cloud_name=cloud_name,
                public_id=public_id,
                mime_type=str(local["mime_type"]),
            )
            candidate_verification = _verify_remote_object(
                public_url=candidate_url,
                expected_sha256=str(local["sha256"]),
                expected_metadata=local,
            )
            if candidate_verification.get("status") == "PASS":
                public_url = candidate_url
                reused = True
            elif candidate_verification.get("status") == "BLOCKED_CLOUDINARY_HOSTED_MEDIA_MISMATCH":
                blockers.extend(
                    [f"{value}:{asset_id}" for value in candidate_verification.get("blockers") or []]
                    or [f"cloudinary_deterministic_object_mismatch:{asset_id}"]
                )
                continue
        if not public_url:
            try:
                upload = _upload_asset(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    public_id=public_id,
                    file_path=Path(str(local["absolute_local_source_path"])),
                    mime_type=str(local["mime_type"]),
                )
                provider_calls += 1
            except Exception as exc:
                blockers.append(f"cloudinary_upload_failed:{asset_id}:{type(exc).__name__}")
                continue
            if str(upload.get("public_id") or "") != public_id:
                blockers.append(f"cloudinary_public_id_mismatch:{asset_id}")
                continue
            public_url = str(upload.get("secure_url") or "")
            provider_asset_id = upload.get("asset_id")
        verification = _verify_remote_object(
            public_url=public_url,
            expected_sha256=str(local["sha256"]),
            expected_metadata=local,
        )
        if verification.get("status") != "PASS":
            blockers.extend(
                [f"{value}:{asset_id}" for value in verification.get("blockers") or []]
                or [f"{verification.get('status')}:{asset_id}"]
            )
            continue
        if reused:
            reused_count += 1
        prepared.append(
            {
                "media_asset_id": asset_id,
                "media_role": "delivery_only",
                "article_inclusion": False,
                "canonical_article_media": False,
                "delivery_only": True,
                "absolute_local_source_path": str(local["absolute_local_source_path"]),
                "sha256": str(local["sha256"]),
                "declared_sha256": str(raw.get("sha256") or ""),
                "mime_type": str(local["mime_type"]),
                "width": int(local["width"]),
                "height": int(local["height"]),
                "source_provenance": {
                    "status": raw.get("provenance_status"),
                    "rights_basis": raw.get("rights_basis"),
                    "source_label": raw.get("source_label"),
                    "source_page_url": raw.get("source_page_url"),
                    "caption": raw.get("caption"),
                },
                "verified_public_delivery_url": public_url,
                "public_delivery_sha256": str(verification["remote_sha256"]),
                "local_public_hash_continuity": True,
                "provider": PROVIDER,
                "provider_contract_version": PROVIDER_CONTRACT_VERSION,
                "provider_public_id": public_id,
                "provider_asset_id": provider_asset_id,
                "provider_object_reused": reused,
            }
        )
    if blockers or len(prepared) != len(delivery_only_assets):
        return {
            "status": "BLOCKED_CLOUDINARY_DELIVERY_MEDIA_PREPARATION",
            "blockers": list(dict.fromkeys(blockers or ["delivery_media_preparation_incomplete"])),
            "credential_presence": presence,
            "provider_calls": provider_calls,
            "verified_asset_count": len(prepared),
        }
    manifest = {
        "schema_version": DELIVERY_MANIFEST_SCHEMA_VERSION,
        "provider_contract_version": PROVIDER_CONTRACT_VERSION,
        "provider": PROVIDER,
        "authority": "approved_delivery_only_media_hash_binding_not_article_media",
        "run_id": work_item_id,
        "status": "PASS",
        "blockers": [],
        "assets": prepared,
        "selected_primary_media_asset_id": prepared[0]["media_asset_id"],
        "selected_primary_media_sha256": prepared[0]["sha256"],
        "article_media_authority": False,
        "publication_authority": False,
    }
    return {
        "status": READY,
        "manifest": manifest,
        "credential_presence": presence,
        "provider_calls": provider_calls,
        "reused_asset_count": reused_count,
        "verified_asset_count": len(prepared),
    }
