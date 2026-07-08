"""Public dispatch freeze and duplicate guard for ContentOps V6.

This module is intentionally deterministic and credential-free. It gates live
public sends before any platform adapter reads credentials or opens a network
request.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

APPROVAL_STATUS_APPROVED = "APPROVED_FOR_PUBLIC_DISPATCH"
GUARD_STATUS_PASS = "PASS"
GUARD_STATUS_BLOCKED = "PUBLIC_DISPATCH_FROZEN"
DEFAULT_PUBLIC_DISPATCH_LEDGER = Path(
    "docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl"
)

_PUBLIC_URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+")
_GENERIC_TELEGRAM_LINK_RE = re.compile(
    r"\b(read|see)\s+(the\s+)?(full\s+)?(editorial\s+analysis|article|brief|post|story|more)\b",
    re.IGNORECASE,
)


def _normalise_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _stable_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def clean_public_url(url: str | None) -> str | None:
    raw = str(url or "").strip().rstrip(".,;:")
    if not raw:
        return None
    raw = raw.split("#", 1)[0]
    base, separator, query = raw.partition("?")
    match = re.match(r"^(https?)://([^/]+)(.*)$", base, flags=re.IGNORECASE)
    if match:
        scheme, host, path = match.groups()
        base = f"{scheme.lower()}://{host.lower()}{path.rstrip('/')}"
    if not separator:
        return base
    kept_parts = []
    for part in query.split("&"):
        key = part.split("=", 1)[0].lower()
        if key.startswith("utm_") or key in {"fbclid", "gclid"}:
            continue
        if part:
            kept_parts.append(part)
    return base + (f"?{'&'.join(kept_parts)}" if kept_parts else "")


def build_public_dispatch_topic_hash(topic: str, editorial_angle: str | None = None) -> str:
    return _stable_hash(
        {
            "topic": _normalise_space(topic).lower(),
            "editorial_angle": _normalise_space(editorial_angle).lower(),
        }
    )


def build_public_dispatch_payload_hash(
    *,
    platform: str,
    action: str,
    body_text: str,
    canonical_url: str | None = None,
    media_url: str | None = None,
    topic_hash: str | None = None,
) -> str:
    return _stable_hash(
        {
            "platform": str(platform or "").lower(),
            "action": str(action or "").lower(),
            "body_text": _normalise_space(body_text),
            "canonical_url": clean_public_url(canonical_url),
            "media_url": clean_public_url(media_url) or _normalise_space(media_url),
            "topic_hash": topic_hash or "",
        }
    )


def build_public_dispatch_identity_hashes(
    *,
    platform: str,
    canonical_url: str | None = None,
    media_url: str | None = None,
    topic_hash: str | None = None,
) -> dict[str, str]:
    identities: dict[str, str] = {}
    platform_id = str(platform or "").lower()
    clean_url = clean_public_url(canonical_url)
    clean_media = clean_public_url(media_url) or _normalise_space(media_url)
    if clean_url:
        identities["canonical_url_hash"] = _stable_hash({"platform": platform_id, "canonical_url": clean_url})
    if clean_media:
        identities["media_url_hash"] = _stable_hash({"platform": platform_id, "media_url": clean_media})
    if topic_hash:
        identities["topic_hash"] = str(topic_hash)
    return identities


def make_public_dispatch_approval_marker(
    *,
    run_id: str,
    topic_hash: str,
    payload_hash: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    marker: dict[str, Any] = {
        "approval_status": APPROVAL_STATUS_APPROVED,
        "approved_public_dispatch": True,
        "run_id": run_id,
        "topic_hash": topic_hash,
    }
    if payload_hash:
        marker["payload_hash"] = payload_hash
        if platform:
            marker["approved_payload_hashes"] = {str(platform).lower(): payload_hash}
    return marker


def _as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, Mapping):
        vals: set[str] = set()
        for item in value.values():
            vals.update(_as_set(item))
        return vals
    if isinstance(value, Iterable):
        return {str(item) for item in value if str(item or "").strip()}
    return {str(value)}


def _marker_payload_hashes(marker: Mapping[str, Any], platform: str) -> set[str]:
    hashes: set[str] = set()
    for key in ("payload_hash", "approved_payload_hash"):
        hashes.update(_as_set(marker.get(key)))
    for key in ("payload_hashes", "approved_payload_hashes"):
        value = marker.get(key)
        if isinstance(value, Mapping):
            hashes.update(_as_set(value.get(platform)))
            hashes.update(_as_set(value.get("all")))
        else:
            hashes.update(_as_set(value))
    return hashes


def _merge_prior_hashes(target: dict[str, set[str]], source: Mapping[str, Any]) -> None:
    field_map = {
        "payload_hash": "payload_hashes",
        "payload_hashes": "payload_hashes",
        "canonical_url_hash": "canonical_url_hashes",
        "canonical_url_hashes": "canonical_url_hashes",
        "media_url_hash": "media_url_hashes",
        "media_url_hashes": "media_url_hashes",
        "topic_hash": "topic_hashes",
        "topic_hashes": "topic_hashes",
    }
    for source_key, target_key in field_map.items():
        target.setdefault(target_key, set()).update(_as_set(source.get(source_key)))
    if source.get("canonical_url"):
        identity = build_public_dispatch_identity_hashes(
            platform=str(source.get("platform") or "telegram"),
            canonical_url=str(source.get("canonical_url")),
        )
        target.setdefault("canonical_url_hashes", set()).update(_as_set(identity.get("canonical_url_hash")))
    if source.get("media_url"):
        identity = build_public_dispatch_identity_hashes(
            platform=str(source.get("platform") or "telegram"),
            media_url=str(source.get("media_url")),
        )
        target.setdefault("media_url_hashes", set()).update(_as_set(identity.get("media_url_hash")))
    if source.get("topic_hint") and not source.get("topic_hash"):
        target.setdefault("topic_hashes", set()).add(
            build_public_dispatch_topic_hash(str(source.get("topic_hint")))
        )


def normalise_prior_dispatch_hashes(prior_dispatch_hashes: Any) -> dict[str, set[str]]:
    hashes: dict[str, set[str]] = {
        "payload_hashes": set(),
        "canonical_url_hashes": set(),
        "media_url_hashes": set(),
        "topic_hashes": set(),
    }
    if isinstance(prior_dispatch_hashes, Mapping):
        _merge_prior_hashes(hashes, prior_dispatch_hashes)
    elif isinstance(prior_dispatch_hashes, Iterable) and not isinstance(prior_dispatch_hashes, (str, bytes)):
        for item in prior_dispatch_hashes:
            if isinstance(item, Mapping):
                _merge_prior_hashes(hashes, item)
    return hashes


def load_public_dispatch_hashes(
    ledger_path: str | Path | None = DEFAULT_PUBLIC_DISPATCH_LEDGER,
) -> dict[str, set[str]]:
    if not ledger_path:
        return normalise_prior_dispatch_hashes(None)
    path = Path(ledger_path)
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return normalise_prior_dispatch_hashes(rows)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return normalise_prior_dispatch_hashes(rows)


def append_public_dispatch_ledger(
    *,
    ledger_path: str | Path | None,
    platform: str,
    action: str,
    run_id: str,
    topic_hash: str,
    payload_hash: str,
    canonical_url: str | None = None,
    media_url: str | None = None,
    status: str = "SUCCESS",
) -> None:
    if not ledger_path:
        return
    path = Path(ledger_path)
    identity_hashes = build_public_dispatch_identity_hashes(
        platform=platform,
        canonical_url=canonical_url,
        media_url=media_url,
        topic_hash=topic_hash,
    )
    record = {
        "record_type": "public_dispatch_payload",
        "platform": platform,
        "action": action,
        "run_id": run_id,
        "topic_hash": topic_hash,
        "payload_hash": payload_hash,
        "canonical_url": clean_public_url(canonical_url),
        "media_url": media_url,
        "status": status,
        **identity_hashes,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def is_telegram_preview_only_body(body_text: str, canonical_url: str | None = None) -> bool:
    body = str(body_text or "").strip()
    if not body:
        return True
    without_urls = _PUBLIC_URL_RE.sub("", body)
    if canonical_url:
        clean_url = clean_public_url(canonical_url)
        if clean_url:
            without_urls = without_urls.replace(clean_url, "")
    generic_removed = _GENERIC_TELEGRAM_LINK_RE.sub("", without_urls)
    generic_removed = re.sub(r"[:\-|.,;()\[\]\s]+", " ", generic_removed).strip()
    if not generic_removed:
        return True
    if _GENERIC_TELEGRAM_LINK_RE.search(body):
        word_count = len(re.findall(r"[A-Za-z0-9]+", generic_removed))
        return len(generic_removed) < 80 or word_count < 12
    return False


def evaluate_public_dispatch_freeze(
    *,
    platform: str,
    action: str,
    run_id: str | None,
    topic_hash: str | None,
    operator_approval_marker: Mapping[str, Any] | None,
    body_text: str = "",
    canonical_url: str | None = None,
    media_url: str | None = None,
    payload_hash: str | None = None,
    payload_hash_required: bool = True,
    prior_dispatch_hashes: Any = None,
    canonical_packet_status: str | None = None,
    duplicate_check: bool = True,
) -> dict[str, Any]:
    platform_id = str(platform or "").lower()
    action_id = str(action or "").lower()
    blockers: list[str] = []
    marker = operator_approval_marker if isinstance(operator_approval_marker, Mapping) else None

    if str(canonical_packet_status or "").upper() in {"BLOCKED", "FAILED", "VALIDATION_FAILED"}:
        blockers.append(f"canonical_packet_status:{canonical_packet_status}")

    if not marker:
        blockers.append("operator_approval_marker_missing")
    else:
        status = marker.get("approval_status") or marker.get("operator_approval_status")
        if status != APPROVAL_STATUS_APPROVED:
            blockers.append("operator_approval_status_not_approved")
        marker_run_id = marker.get("run_id") or marker.get("approved_run_id")
        if not run_id:
            blockers.append("run_id_missing")
        elif marker_run_id != run_id:
            blockers.append("operator_approval_run_id_mismatch")
        marker_topic_hash = marker.get("topic_hash") or marker.get("approved_topic_hash")
        if not topic_hash:
            blockers.append("topic_hash_missing")
        elif marker_topic_hash != topic_hash:
            blockers.append("operator_approval_topic_hash_mismatch")
        if payload_hash_required:
            approved_hashes = _marker_payload_hashes(marker, platform_id)
            if not payload_hash:
                blockers.append("payload_hash_missing")
            elif payload_hash not in approved_hashes:
                blockers.append("operator_approval_payload_hash_mismatch")

    if platform_id == "telegram" and action_id in {"post", "photo"}:
        if is_telegram_preview_only_body(body_text, canonical_url):
            blockers.append("telegram_preview_only_body")

    identity_hashes = build_public_dispatch_identity_hashes(
        platform=platform_id,
        canonical_url=canonical_url,
        media_url=media_url,
        topic_hash=topic_hash,
    )
    prior_hashes = normalise_prior_dispatch_hashes(prior_dispatch_hashes)
    if marker:
        _merge_prior_hashes(
            prior_hashes,
            {
                "payload_hashes": marker.get("known_duplicate_payload_hashes"),
                "canonical_url_hashes": marker.get("known_duplicate_canonical_url_hashes"),
                "media_url_hashes": marker.get("known_duplicate_media_url_hashes"),
                "topic_hashes": marker.get("known_duplicate_topic_hashes"),
            },
        )
    if duplicate_check:
        if payload_hash and payload_hash in prior_hashes["payload_hashes"]:
            blockers.append("duplicate_payload_hash")
        if identity_hashes.get("canonical_url_hash") in prior_hashes["canonical_url_hashes"]:
            blockers.append("duplicate_canonical_url_hash")
        if identity_hashes.get("media_url_hash") in prior_hashes["media_url_hashes"]:
            blockers.append("duplicate_media_url_hash")
        if identity_hashes.get("topic_hash") in prior_hashes["topic_hashes"]:
            blockers.append("duplicate_topic_hash")

    return {
        "status": GUARD_STATUS_PASS if not blockers else GUARD_STATUS_BLOCKED,
        "dispatch_allowed": not blockers,
        "platform": platform_id,
        "action": action_id,
        "run_id": run_id,
        "topic_hash": topic_hash,
        "payload_hash": payload_hash,
        "payload_hash_required": payload_hash_required,
        "approval_marker_present": bool(marker),
        "identity_hashes": identity_hashes,
        "blockers": list(dict.fromkeys(blockers)),
    }
