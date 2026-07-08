"""V6 Live Production Pipeline Runner.

Runs the end-to-end live generation process under Fast Ship Mode:
1. Performs grounded search on news/geopolitical topics.
2. Generates canonical Substack article using Gemini 3.5 Flash via 9router.
3. Generates platform-native variants with threading models (X, Threads) and summaries.
4. Automatically retrieves and downloads matching Google Images.
5. Saves packets cleanly to canonical output locations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from live_contentops.ai_research_canonical_article_engine_v6 import (
    EngineInput,
    run_article_engine,
    validate_article_quality,
)
from live_contentops.editorial_quality_audit_v6 import audit_editorial_quality_packet
from live_contentops.platform_native_variant_generator_live_v6 import (
    generate_live_platform_variants,
    validate_platform_variants,
)
from live_contentops.pipeline_rehearsal_evidence_v6 import (
    DEFAULT_EVIDENCE_PACKET_PATH,
    build_rehearsal_evidence_packet,
    write_rehearsal_evidence,
)
from live_contentops.public_dispatch_freeze_guard_v6 import (
    APPROVAL_STATUS_APPROVED,
    DEFAULT_PUBLIC_DISPATCH_LEDGER,
    append_public_dispatch_ledger,
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    evaluate_public_dispatch_freeze,
    load_public_dispatch_hashes,
)

ARTICLE_OUTPUT_PATH = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
VARIANT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")
DISPATCH_AUDIT_PATH = VARIANT_OUTPUT_DIR / "latest_dispatch_audit.json"
PUBLIC_DISPATCH_LEDGER_PATH = DEFAULT_PUBLIC_DISPATCH_LEDGER
DEFAULT_REHEARSAL_TOPIC = "US recession risks rise as oil volatility spikes"
DEFAULT_REHEARSAL_ANGLE = "Focus on data transparency, geopolitics, and yield curves."
DAILY_SCHEDULE_PATH = Path("docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json")
HEADLINE_SIDECAR_DIR = Path("headline_ingestion/data/intake/headline_sidecars")
REHEARSAL_READY_STATUS = "LIVE_READY_REQUIRES_OPERATOR_GO"
CURRENT_8_PLATFORMS = ("substack", "linkedin", "x", "instagram", "facebook", "telegram", "threads", "discord")


def _load_live_env_if_needed(enabled: bool) -> None:
    if enabled:
        load_dotenv()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_dispatch_audit(payload: dict[str, Any]) -> None:
    DISPATCH_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_AUDIT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stable_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _packet_hash(packet: dict[str, Any]) -> str:
    return _stable_hash(packet)


def _load_json_dict(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _headline_sidecar_inventory(sidecar_dir: str | Path = HEADLINE_SIDECAR_DIR) -> dict[str, Any]:
    root = Path(sidecar_dir)
    paths = sorted(root.glob("*.jsonl"), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    latest_path = paths[0] if paths else None
    latest_count = 0
    latest_captured_at = None
    if latest_path:
        try:
            lines = [line for line in latest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            latest_count = len(lines)
            for line in lines[:25]:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                latest_captured_at = row.get("captured_at_utc") or row.get("headline_timestamp") or row.get("created_at_raw")
                if latest_captured_at:
                    break
        except Exception:
            latest_count = 0
    return {
        "sidecar_dir": str(root),
        "sidecar_file_count": len(paths),
        "latest_sidecar_path": str(latest_path) if latest_path else None,
        "latest_sidecar_count": latest_count,
        "latest_sidecar_captured_at": latest_captured_at,
        "sidecars_available": bool(paths and latest_count),
    }


def select_rehearsal_scheduler_slot(schedule_path: str | Path = DAILY_SCHEDULE_PATH) -> dict[str, Any]:
    schedule = _load_json_dict(schedule_path)
    slots = [slot for slot in schedule.get("slots", []) if isinstance(slot, dict)]
    selected = None
    for slot in slots:
        topic_blob = " ".join([str(slot.get("topic") or ""), " ".join(str(tag) for tag in slot.get("tags") or [])]).lower()
        if slot.get("readiness") != "READY_FOR_PIPELINE":
            continue
        if "energy" in topic_blob or "oil" in topic_blob or "wti" in topic_blob or "crude" in topic_blob:
            selected = slot
            break
    if selected is None and slots:
        selected = slots[0]
    inventory = _headline_sidecar_inventory()
    if selected:
        reason = "ready_energy_slot_from_current_daily_schedule" if selected.get("readiness") == "READY_FOR_PIPELINE" else "first_available_schedule_slot"
        return {
            "daily_schedule_path": str(schedule_path),
            "schedule_date": schedule.get("schedule_date"),
            "headline_sidecar_count": schedule.get("headline_sidecar_count"),
            "headline_sidecars_are_catalyst_only": schedule.get("headline_sidecars_are_catalyst_only"),
            "selected_slot": selected,
            "selected_slot_index": selected.get("slot_index"),
            "selected_topic": selected.get("topic"),
            "selected_angle": selected.get("angle"),
            "selection_reason": reason,
            "duplicate_check_basis": "topic_hash_and_public_duplicate_ledger; canonical_url_absent_in_dry_run",
            **inventory,
        }
    return {
        "daily_schedule_path": str(schedule_path),
        "schedule_date": schedule.get("schedule_date"),
        "headline_sidecar_count": inventory.get("latest_sidecar_count", 0),
        "headline_sidecars_are_catalyst_only": True,
        "selected_slot": None,
        "selected_slot_index": None,
        "selected_topic": DEFAULT_REHEARSAL_TOPIC,
        "selected_angle": DEFAULT_REHEARSAL_ANGLE,
        "selection_reason": "deterministic_fixture_fallback_no_schedule_slot",
        "duplicate_check_basis": "fixture_topic_hash_and_public_duplicate_ledger; canonical_url_absent_in_dry_run",
        **inventory,
    }


def _load_operator_approval_marker(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("operator approval marker must be a JSON object")
    return data


def _result_url(result: dict[str, Any]) -> str | None:
    response = result.get("response") if isinstance(result.get("response"), dict) else {}
    return result.get("public_url") or response.get("public_url") or result.get("url") or response.get("url") or response.get("final_url")


def _normalize_dispatch_result(platform: str, result: dict[str, Any] | None = None, error: Exception | str | None = None) -> dict[str, Any]:
    result = result or {}
    status = str(result.get("status") or ("FAILED" if error else "UNKNOWN")).upper()
    err = str(error or result.get("error") or "").strip()
    ok = status in {"SUCCESS", "OK", "POSTED", "SENT"} and not err
    return {
        "platform": platform,
        "status": status,
        "ok": ok,
        "error_class": None if ok else (result.get("error_class") or (type(error).__name__ if error else "dispatch_failed")),
        "error": err or None,
        "url": _result_url(result),
        "raw": result,
    }


def _blocked_result(platform: str, reason: str) -> dict[str, Any]:
    return {
        "platform": platform,
        "status": "BLOCKED",
        "ok": False,
        "error_class": "missing_payload",
        "error": reason,
        "url": None,
        "raw": {"missing": [reason]},
    }


def _guard_blocked_result(platform: str, guard: dict[str, Any]) -> dict[str, Any]:
    reason = "|".join(str(item) for item in guard.get("blockers", []))
    return {
        "platform": platform,
        "status": "PUBLIC_DISPATCH_FROZEN",
        "ok": False,
        "error_class": "public_dispatch_freeze_guard",
        "error": reason or "public_dispatch_freeze_guard",
        "url": None,
        "raw": {"public_dispatch_freeze_guard": guard},
    }


def _dispatch_summary(results: dict[str, Any]) -> dict[str, Any]:
    flat: list[dict[str, Any]] = []
    for key, value in results.items():
        if isinstance(value, list):
            flat.extend(item for item in value if isinstance(item, dict) and "ok" in item)
        elif isinstance(value, dict) and "ok" in value:
            flat.append(value)
    attempted = [item["platform"] for item in flat]
    return {
        "attempted_platforms": attempted,
        "successful_platforms": [item["platform"] for item in flat if item.get("ok")],
        "failed_platforms": [
            item["platform"]
            for item in flat
            if not item.get("ok") and item.get("status") not in {"BLOCKED", "PUBLIC_DISPATCH_FROZEN"}
        ],
        "blocked_platforms": [
            item["platform"]
            for item in flat
            if item.get("status") in {"BLOCKED", "PUBLIC_DISPATCH_FROZEN"}
        ],
    }


def _quality_gate_status(blockers: list[str]) -> dict[str, Any]:
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
    }


def _rehearsal_payload_specs(
    *,
    variants: dict[str, Any],
    variant_threads: dict[str, Any],
    selected_platforms: tuple[str, ...],
    canonical_url: str | None,
    local_image_path: str | None,
    public_image_url: str | None,
    selected_media: dict[str, Any],
    article_title: str,
    public_dispatch_topic_hash: str,
) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for platform in selected_platforms:
        action = "post"
        body = ""
        media = None
        if platform == "substack":
            action = "article"
            body = str(variants.get("substack") or "")
            media = local_image_path
        elif platform == "linkedin":
            body = _apply_canonical_link(str(variants.get("linkedin") or ""), canonical_url)
            media = local_image_path
        elif platform == "x":
            action = "thread"
            thread = [str(item).strip() for item in variant_threads.get("x", []) if str(item).strip()]
            body = "\n\n".join(thread)
            media = local_image_path
        elif platform == "instagram":
            action = "photo"
            body = _apply_canonical_link(str(variants.get("instagram_caption") or variants.get("telegram") or ""), canonical_url)
            media = selected_media.get("instagram") or local_image_path or public_image_url
        elif platform == "facebook":
            action = "photo" if selected_media.get("facebook") or public_image_url or local_image_path else "post"
            body = _apply_canonical_link(str(variants.get("facebook") or variants.get("linkedin") or ""), canonical_url)
            media = selected_media.get("facebook") or public_image_url or local_image_path
        elif platform == "telegram":
            message = _apply_canonical_link(str(variants.get("telegram") or ""), canonical_url)
            media = local_image_path or selected_media.get("telegram") or public_image_url
            action = "photo" if media else "post"
            body = _fit_telegram_photo_caption(message, canonical_url) if media else message
        elif platform == "threads":
            action = "thread"
            thread = [str(item).strip() for item in variant_threads.get("threads", []) if str(item).strip()]
            body = "\n\n".join(thread)
            media = selected_media.get("threads") or public_image_url or local_image_path
        elif platform == "discord":
            body = _apply_canonical_link(str(variants.get("discord") or ""), canonical_url)
            media = public_image_url or local_image_path
        payload_hash = build_public_dispatch_payload_hash(
            platform=platform,
            action=action,
            body_text=body,
            canonical_url=canonical_url,
            media_url=media,
            topic_hash=public_dispatch_topic_hash,
        )
        specs[platform] = {
            "platform": platform,
            "action": action,
            "body_text": body,
            "body_length": len(body.strip()),
            "canonical_url": canonical_url,
            "media_url": media,
            "article_title": article_title,
            "payload_hash": payload_hash,
        }
    return specs


def _make_rehearsal_approval_marker(
    *,
    run_id: str,
    topic_hash: str,
    payload_hashes: dict[str, str],
    canonical_packet_hash: str,
    platform_variant_packet_hash: str,
) -> dict[str, Any]:
    marker = {
        "approval_status": APPROVAL_STATUS_APPROVED,
        "approved_public_dispatch": True,
        "run_id": run_id,
        "topic_hash": topic_hash,
        "approved_payload_hashes": payload_hashes,
        "canonical_packet_hash": canonical_packet_hash,
        "platform_variant_packet_hash": platform_variant_packet_hash,
        "dry_run": True,
        "public_write": False,
    }
    if payload_hashes.get("telegram"):
        marker["payload_hash"] = payload_hashes["telegram"]
    return marker


def _build_rehearsal_dispatch(
    *,
    run_id: str,
    public_dispatch_topic_hash: str,
    article_packet: dict[str, Any],
    variant_packet: dict[str, Any],
    selected_platforms: tuple[str, ...],
    canonical_url: str | None,
    local_image_path: str | None,
    public_image_url: str | None,
    selected_media: dict[str, Any],
    public_dispatch_ledger_path: str | Path | None,
    quality_gate_result: dict[str, Any],
) -> dict[str, Any]:
    variants = variant_packet.get("variants", {}) if isinstance(variant_packet.get("variants"), dict) else {}
    variant_threads = variant_packet.get("variant_threads", {}) if isinstance(variant_packet.get("variant_threads"), dict) else {}
    article_title = str(article_packet.get("canonical_article_draft", {}).get("title") or "")
    specs = _rehearsal_payload_specs(
        variants=variants,
        variant_threads=variant_threads,
        selected_platforms=selected_platforms,
        canonical_url=canonical_url,
        local_image_path=local_image_path,
        public_image_url=public_image_url,
        selected_media=selected_media,
        article_title=article_title,
        public_dispatch_topic_hash=public_dispatch_topic_hash,
    )
    payload_hashes = {platform: spec["payload_hash"] for platform, spec in specs.items()}
    canonical_packet_hash = _packet_hash(article_packet)
    platform_variant_packet_hash = _packet_hash(variant_packet)
    approval_marker = _make_rehearsal_approval_marker(
        run_id=run_id,
        topic_hash=public_dispatch_topic_hash,
        payload_hashes=payload_hashes,
        canonical_packet_hash=canonical_packet_hash,
        platform_variant_packet_hash=platform_variant_packet_hash,
    )
    prior_hashes = load_public_dispatch_hashes(public_dispatch_ledger_path)
    telegram_spec = specs.get("telegram") or {}
    article_status = str(article_packet.get("status") or article_packet.get("packet_status") or "").upper()
    telegram_guard = evaluate_public_dispatch_freeze(
        platform="telegram",
        action=str(telegram_spec.get("action") or "post"),
        run_id=run_id,
        topic_hash=public_dispatch_topic_hash,
        operator_approval_marker=approval_marker,
        body_text=str(telegram_spec.get("body_text") or ""),
        canonical_url=canonical_url,
        media_url=telegram_spec.get("media_url"),
        payload_hash=telegram_spec.get("payload_hash"),
        payload_hash_required=True,
        prior_dispatch_hashes=prior_hashes,
        canonical_packet_status=article_status if article_status else None,
    )
    dispatch_results: dict[str, Any] = {}
    for platform, spec in specs.items():
        missing = _require_payload(spec.get("body_text"), f"{platform}_payload")
        ok = not missing and quality_gate_result.get("status") == "PASS"
        status = "DRY_RUN_REHEARSAL_READY" if ok else "BLOCKED"
        error = missing
        if platform == "telegram" and not telegram_guard.get("dispatch_allowed"):
            ok = False
            status = "PUBLIC_DISPATCH_FROZEN"
            error = "|".join(telegram_guard.get("blockers", [])) or "public_dispatch_freeze_guard"
        dispatch_results[platform] = {
            "platform": platform,
            "status": status,
            "ok": ok,
            "dry_run": True,
            "public_write": False,
            "live_platform_api_called": False,
            "credential_lookup_performed": False,
            "payload_hash": spec.get("payload_hash"),
            "action": spec.get("action"),
            "body_length": spec.get("body_length"),
            "canonical_url": canonical_url,
            "media_url": spec.get("media_url"),
            "crop_readability_status": "LOCAL_FIXTURE_PRESENT_PUBLIC_CROP_NOT_APPLICABLE_DRY_RUN",
            "url": None,
            "error_class": None if ok else ("public_dispatch_freeze_guard" if platform == "telegram" and status == "PUBLIC_DISPATCH_FROZEN" else "dry_run_rehearsal_blocked"),
            "error": error,
        }
        if platform == "telegram":
            dispatch_results[platform]["telegram_caption_proof"] = {
                "caption_length": spec.get("body_length"),
                "caption_non_empty": bool(str(spec.get("body_text") or "").strip()),
                "photo_requested": bool(spec.get("media_url")),
                "photo_proof_mode": "dry_run_payload_hash_only_no_bot_api_call",
                "public_dispatch_freeze_guard": telegram_guard,
            }
    envelope = {
        "run_id": run_id,
        "topic_hash": public_dispatch_topic_hash,
        "canonical_packet_hash": canonical_packet_hash,
        "platform_variant_packet_hash": platform_variant_packet_hash,
        "per_platform_payload_hash": payload_hashes,
        "telegram_payload_hash": payload_hashes.get("telegram"),
        "duplicate_ledger_result": telegram_guard,
        "quality_gate_result": quality_gate_result,
        "dry_run": True,
        "public_write": False,
        "approval_marker": approval_marker,
    }
    return {
        "dispatch_results": dispatch_results,
        "dispatch_summary": _dispatch_summary(dispatch_results),
        "approval_marker_envelope": envelope,
    }


def _require_payload(value: Any, name: str) -> str | None:
    return None if str(value or "").strip() else f"{name}_missing"


_LINK_TOKEN_RE = re.compile(r"\[\s*link\s*\]", re.IGNORECASE)
_READ_MORE_RE = re.compile(r"\n*[^\n]*\[\s*link\s*\][^\n]*", re.IGNORECASE)
_PUBLIC_URL_RE = re.compile(r"https?://[^\s<>()\[\]\"']+")


def _strip_noncanonical_public_urls(text: str, canonical_url: str | None) -> str:
    canonical_clean = _clean_public_url(canonical_url)

    def replace_url(match: re.Match[str]) -> str:
        raw = match.group(0).rstrip(".,;:")
        trailing = match.group(0)[len(raw):]
        if canonical_clean and _clean_public_url(raw) == canonical_clean:
            return f"{canonical_clean}{trailing}"
        return trailing

    cleaned = _PUBLIC_URL_RE.sub(replace_url, str(text or ""))
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _apply_canonical_link(text: str, url: str | None) -> str:
    """Replace [Link] placeholders with a real clickable URL.

    - If a [Link] token exists and url is set, swap it in-place.
    - If no token exists and url is set, append a clean read-more line.
    - If url is empty, strip any line containing a dead [Link] token so no
      placeholder ships publicly.
    """
    body = str(text or "")
    if not url:
        return _strip_noncanonical_public_urls(_READ_MORE_RE.sub("", body), None).rstrip()
    if _LINK_TOKEN_RE.search(body):
        return _strip_noncanonical_public_urls(_LINK_TOKEN_RE.sub(url, body), url)
    body = _strip_noncanonical_public_urls(body, url)
    if _clean_public_url(url) and _clean_public_url(url) in body:
        return body.rstrip()
    return f"{body.rstrip()}\n\nRead the full editorial analysis: {url}"


def _fit_telegram_photo_caption(text: str, canonical_url: str | None, limit: int = 1024) -> str:
    body = str(text or "").strip()
    if len(body) <= limit:
        return body

    link_line = f"Read the full editorial analysis: {canonical_url}" if canonical_url else ""
    if link_line and link_line in body:
        body = body.replace(link_line, "").strip()
    reserve = len(link_line) + (2 if link_line else 0)
    available = max(0, limit - reserve)
    if available <= 1:
        return link_line[:limit]

    clipped = body[: max(0, available - 1)].rstrip()
    last_break = max(clipped.rfind("\n\n"), clipped.rfind(". "), clipped.rfind("\n"), clipped.rfind(" "))
    if last_break > max(80, available // 2):
        clipped = clipped[:last_break].rstrip()
    clipped = clipped.rstrip(".,;:") + "..."
    if link_line:
        return f"{clipped}\n\n{link_line}"[:limit]
    return clipped[:limit]


def _telegram_photo_delivery_evidence(result: dict[str, Any], expected_media: str | None) -> dict[str, Any]:
    """Return proof that Telegram accepted a visual send as a photo message."""
    raw = result.get("raw") if isinstance(result.get("raw"), dict) else result
    response = raw.get("response") if isinstance(raw.get("response"), dict) else {}
    telegram_result = response.get("result") if isinstance(response.get("result"), dict) else {}
    photos = telegram_result.get("photo") if isinstance(telegram_result.get("photo"), list) else []
    return {
        "expected_media": expected_media,
        "visual_send_requested": bool(expected_media),
        "telegram_action": raw.get("action"),
        "message_id": telegram_result.get("message_id") or raw.get("id"),
        "photo_size_count": len(photos),
        "photo_file_ids_present": bool(photos and all(isinstance(item, dict) and item.get("file_id") for item in photos)),
        "visual_delivery_status": "PASS" if expected_media and raw.get("action") == "photo" and photos else "MISSING_PHOTO_PROOF",
    }


def _is_substack_admin_url(url: str | None) -> bool:
    return bool(url and "/publish/" in url)


def _is_substack_public_url(url: str | None) -> bool:
    return bool(url and "/p/" in url and "/publish/" not in url)


def _clean_public_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.split("?", 1)[0].strip()


def _normalize_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def _feed_text(block: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    value = match.group(1)
    value = re.sub(r"^<!\[CDATA\[|\]\]>$", "", value.strip(), flags=re.DOTALL)
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def resolve_substack_public_url(candidate_url: str | None, title: str) -> str | None:
    """Resolve an admin/publish URL to the public Substack reader URL."""
    clean = _clean_public_url(candidate_url)
    if _is_substack_public_url(clean):
        return clean
    try:
        import urllib.request
        feed_url = "https://capitalchronicle.substack.com/feed"
        req = urllib.request.Request(feed_url, headers={"User-Agent": "CapitalChronicleContentOps/1.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            feed = response.read().decode("utf-8", errors="ignore")
        target_title = _normalize_title(title)
        best_link = None
        best_score = 0
        for item in re.findall(r"<item\b.*?</item>", feed, flags=re.IGNORECASE | re.DOTALL):
            item_title = _normalize_title(_feed_text(item, "title"))
            item_link = _clean_public_url(_feed_text(item, "link"))
            if not _is_substack_public_url(item_link):
                continue
            if item_title == target_title:
                return item_link
            target_tokens = set(target_title.split())
            item_tokens = set(item_title.split())
            score = len(target_tokens & item_tokens)
            if score > best_score:
                best_score = score
                best_link = item_link
        if best_link and best_score >= 4:
            return best_link
    except Exception as exc:
        print(f"[Warning] Failed to resolve Substack public URL from feed: {exc}")
    if _is_substack_admin_url(clean):
        print(f"[Warning] Refusing to use Substack admin URL as public canonical link: {clean}")
        return None
    return clean


def _is_useful_public_image_url(url: str | None) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    lowered = url.lower()
    bad_markers = (
        "subscribe-card",
        "substack-post-office",
        "default-logo",
        "default-light",
        "avatar",
        "w_20,h_20",
        "w_32,h_32",
        "w_36,h_36",
        "w_72,h_72",
        "2500x2500",
    )
    return not any(marker in lowered for marker in bad_markers)


def _is_substack_cdn_image_url(url: str | None) -> bool:
    return bool(url and "substackcdn.com/image/fetch" in url and _is_useful_public_image_url(url))


def _dedupe_urls(urls: list[str | None]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        clean = str(url or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        unique.append(clean)
    return unique


def _instagram_proxy_urls(source_url: str | None) -> list[str]:
    """Build square JPEG transforms for Instagram's strict feed aspect rules."""
    if not source_url or not source_url.startswith(("http://", "https://")):
        return []
    safe_source = urllib.parse.quote(source_url, safe=":/%._-~")
    no_scheme_source = re.sub(r"^https?://", "", source_url)
    safe_no_scheme = urllib.parse.quote(no_scheme_source, safe="/%._-~")
    params = "w=1080&h=1080&fit=contain&bg=white&output=jpg"
    return [
        f"https://images.weserv.nl/?url={safe_source}&{params}",
        f"https://wsrv.nl/?url={safe_no_scheme}&{params}",
    ]


def _source_url_from_substack_cdn(url: str | None) -> str | None:
    if not _is_substack_cdn_image_url(url):
        return None
    encoded_source = str(url).rsplit("/", 1)[-1]
    decoded = urllib.parse.unquote(encoded_source)
    return decoded if decoded.startswith(("http://", "https://")) else None


def _instagram_image_candidates(
    *,
    public_image_url: str | None,
    selected_media: dict[str, Any],
    media_manifest: dict[str, Any],
) -> list[str]:
    source_url = (
        media_manifest.get("news_image_source_url")
        or media_manifest.get("news_image_public_url")
        or _source_url_from_substack_cdn(public_image_url)
    )
    return _dedupe_urls([
        selected_media.get("instagram"),
        media_manifest.get("instagram_safe_image_public_url"),
        *_instagram_proxy_urls(str(source_url) if source_url else None),
        *_instagram_proxy_urls(public_image_url),
        public_image_url,
        str(source_url) if source_url else None,
    ])


def _instagram_media_failure(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "").upper()
    if status == "VALIDATION_FAILED":
        return True
    raw = result.get("raw") if isinstance(result.get("raw"), dict) else result
    error_blob = json.dumps(raw.get("error_response") or raw.get("response") or raw, sort_keys=True, default=str).lower()
    media_markers = (
        "aspect ratio",
        "image_aspect_ratio_unsupported",
        "only photo or video",
        "media download",
        "media type",
        "image url",
    )
    return any(marker in error_blob for marker in media_markers)


def extract_og_image(url: str) -> str | None:
    if not url or "mock-post" in url or _is_substack_admin_url(url):
        return None
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            for tag in re.findall(r"<meta\b[^>]+>", html, flags=re.IGNORECASE):
                if not re.search(r'''(?:property|name)=["'](?:og:image|twitter:image)["']''', tag, flags=re.IGNORECASE):
                    continue
                match = re.search(r'''content=["']([^"']+)["']''', tag, flags=re.IGNORECASE)
                if not match:
                    continue
                img_url = match.group(1)
                # Ignore default Substack/card/avatar images.
                if _is_useful_public_image_url(img_url):
                    print(f"[Info] Extracted public CDN image URL from Substack post: {img_url}")
                    return img_url
    except Exception as e:
        print(f"[Warning] Failed to extract og:image from {url}: {e}")
    return None


def _substack_image_candidates_from_tag(tag: str) -> list[str]:
    import html

    candidates: list[str] = []
    for attr in ("src", "data-src"):
        match = re.search(rf"""{attr}=["']([^"']+)["']""", tag, flags=re.IGNORECASE)
        if match:
            candidates.append(html.unescape(match.group(1)))
    srcset = re.search(r"""srcset=["']([^"']+)["']""", tag, flags=re.IGNORECASE)
    if srcset:
        for part in re.split(r",\s+", html.unescape(srcset.group(1)).strip()):
            candidate = part.strip().split(" ", 1)[0]
            if candidate:
                candidates.append(candidate)
    return candidates


def _canonical_public_image_url(candidate: str) -> str | None:
    clean = str(candidate or "").strip()
    if clean.startswith("//"):
        clean = f"https:{clean}"
    if not _is_useful_public_image_url(clean):
        return None
    source = _source_url_from_substack_cdn(clean) or clean
    canonical = source.split("?", 1)[0]
    lowered = canonical.lower()
    if any(marker in lowered for marker in ("substack-post-office", "default-logo", "avatar")):
        return None
    return canonical


def _html_fragment_text(fragment: str) -> str:
    import html

    cleaned = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment or "", flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return re.sub(r"\s+", " ", html.unescape(cleaned)).strip()


def _normalise_public_heading(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _extract_public_visual_order(page_html: str, canonical_urls: list[str]) -> dict[str, Any]:
    seen_urls: set[str] = set()
    image_events: list[dict[str, Any]] = []
    canonical_set = set(canonical_urls)
    for match in re.finditer(r"<img\b[^>]+>", page_html, flags=re.IGNORECASE | re.DOTALL):
        canonical = next(
            (url for url in (_canonical_public_image_url(candidate) for candidate in _substack_image_candidates_from_tag(match.group(0))) if url),
            None,
        )
        if not canonical or canonical in seen_urls or (canonical_set and canonical not in canonical_set):
            continue
        seen_urls.add(canonical)
        image_events.append({
            "position": match.start(),
            "url": canonical,
            "previous_heading": None,
            "next_heading": None,
        })

    heading_events: list[dict[str, Any]] = []
    for match in re.finditer(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", page_html, flags=re.IGNORECASE | re.DOTALL):
        title = _html_fragment_text(match.group(1))
        if title:
            heading_events.append({
                "position": match.start(),
                "title": title,
                "title_key": _normalise_public_heading(title),
            })

    for image in image_events:
        previous = [heading for heading in heading_events if heading["position"] < image["position"]]
        following = [heading for heading in heading_events if heading["position"] > image["position"]]
        if previous:
            image["previous_heading"] = previous[-1]["title"]
        if following:
            image["next_heading"] = following[0]["title"]

    return {
        "image_events": image_events,
        "heading_events": heading_events,
    }


def _audit_public_visual_placement(
    page_html: str,
    canonical_urls: list[str],
    expected_placements: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    order = _extract_public_visual_order(page_html, canonical_urls)
    image_events = order["image_events"]
    heading_events = order["heading_events"]
    if not expected_placements:
        return {
            "placement_order_status": "SKIPPED_NO_EXPECTED_PLACEMENTS",
            "meets_visual_placement_expectations": True,
            "visual_order_proof": image_events[:10],
            "placement_checks": [],
            "all_images_after_source_trail": False,
        }

    source_heading = next((heading for heading in heading_events if heading["title_key"].startswith("source trail")), None)
    source_pos = source_heading["position"] if source_heading else None
    first_major_heading_pos = heading_events[0]["position"] if heading_events else None
    all_after_source = bool(source_pos is not None and image_events and all(image["position"] > source_pos for image in image_events))
    checks: list[dict[str, Any]] = []
    status = "PASS"
    non_intro_placement_keys = {
        _normalise_public_heading(item.get("placement_after_section"))
        for item in expected_placements
        if _normalise_public_heading(item.get("placement_after_section")) not in {"", "intro"}
    }

    for idx, placement in enumerate(expected_placements):
        asset_id = str(placement.get("asset_id") or f"visual_{idx + 1}")
        placement_key = _normalise_public_heading(placement.get("placement_after_section"))
        image = image_events[idx] if idx < len(image_events) else None
        check = {
            "asset_id": asset_id,
            "placement_after_section": placement.get("placement_after_section"),
            "image_url": image.get("url") if image else None,
            "previous_heading": image.get("previous_heading") if image else None,
            "next_heading": image.get("next_heading") if image else None,
            "passed": False,
            "reason": None,
        }
        if not image:
            check["reason"] = "missing_public_image_for_visual_slot"
            status = "COUNT_MISMATCH"
            checks.append(check)
            continue
        if source_pos is not None and image["position"] > source_pos:
            check["reason"] = "image_after_source_trail"
            status = "PLACEMENT_MISMATCH"
            checks.append(check)
            continue
        if placement_key == "intro":
            previous_key = _normalise_public_heading(image.get("previous_heading"))
            next_key = _normalise_public_heading(image.get("next_heading"))
            late_previous_heading = (
                previous_key.startswith("source trail")
                or previous_key.startswith("discussion")
                or any(
                    key and previous_key and (key == previous_key or key in previous_key or previous_key in key)
                    for key in non_intro_placement_keys
                )
            )
            macro_context = (
                "macro setup" in previous_key
                or "macro setup" in next_key
                or "current oil evidence" in previous_key
                or "current oil evidence" in next_key
            )
            early_context = bool(next_key and not next_key.startswith("discussion") and not next_key.startswith("source trail") and not late_previous_heading)
            if (first_major_heading_pos is None or image["position"] < first_major_heading_pos or macro_context or early_context) and not late_previous_heading:
                check["passed"] = True
            else:
                check["reason"] = "intro_visual_not_near_macro_setup_or_before_later_sections"
                status = "PLACEMENT_MISMATCH"
            checks.append(check)
            continue

        target_heading_index = None
        for heading_idx, heading in enumerate(heading_events):
            title_key = heading["title_key"]
            if placement_key and (placement_key == title_key or placement_key in title_key or title_key in placement_key):
                target_heading_index = heading_idx
                break
        if target_heading_index is None:
            check["reason"] = "target_heading_not_found"
            status = "PLACEMENT_INCONCLUSIVE" if status == "PASS" else status
            checks.append(check)
            continue
        target_heading = heading_events[target_heading_index]
        next_heading = heading_events[target_heading_index + 1] if target_heading_index + 1 < len(heading_events) else None
        before_next_heading = next_heading is None or image["position"] < next_heading["position"]
        if image["position"] > target_heading["position"] and before_next_heading:
            check["passed"] = True
        else:
            check["reason"] = "image_not_within_target_section_range"
            status = "PLACEMENT_MISMATCH"
        checks.append(check)

    if all_after_source:
        status = "PLACEMENT_MISMATCH"
    return {
        "placement_order_status": status,
        "meets_visual_placement_expectations": status == "PASS",
        "visual_order_proof": image_events[:10],
        "placement_checks": checks,
        "all_images_after_source_trail": all_after_source,
    }


def _expected_substack_visual_placements(
    visual_marker_ids: list[str],
    visual_slots: list[dict[str, Any]] | None,
    body_markdown: str | None = None,
) -> list[dict[str, Any]]:
    slots_by_id = {
        str(slot.get("asset_id") or "").strip(): slot
        for slot in (visual_slots or [])
        if isinstance(slot, dict) and str(slot.get("asset_id") or "").strip()
    }
    headings = list(re.finditer(r"(?m)^###\s+(.+)$", body_markdown or ""))
    placements: list[dict[str, Any]] = []
    for marker_id in visual_marker_ids:
        slot = slots_by_id.get(str(marker_id))
        placement_after_section = slot.get("placement_after_section") if slot else None
        if not placement_after_section and body_markdown:
            marker_pos = body_markdown.find(f"[[VISUAL:{marker_id}]]")
            if marker_pos >= 0:
                previous_heading = next((heading for heading in reversed(headings) if heading.start() < marker_pos), None)
                placement_after_section = previous_heading.group(1).strip() if previous_heading else "intro"
        placements.append({
            "asset_id": marker_id,
            "placement_after_section": placement_after_section,
            "editorial_purpose": slot.get("editorial_purpose") if slot else None,
            "placement_source": "visual_slot" if slot and slot.get("placement_after_section") else "marker_heading_inference",
        })
    return placements


def audit_substack_public_visuals(
    url: str | None,
    *,
    expected_visual_count: int = 0,
    expected_placements: list[dict[str, Any]] | None = None,
    retries: int = 3,
    delay_seconds: float = 2.0,
) -> dict[str, Any]:
    """Read the public Substack page and verify useful article images plus body placement."""
    result: dict[str, Any] = {
        "status": "SKIPPED",
        "public_url": url,
        "expected_visual_count": expected_visual_count,
        "expected_placements": expected_placements or [],
        "public_image_count": 0,
        "public_image_urls": [],
        "meets_expected_visual_count": False,
        "meets_visual_placement_expectations": False,
        "placement_order_status": "NOT_EVALUATED",
        "attempts": 0,
    }
    if not url or "mock-post" in url or _is_substack_admin_url(url):
        result["status"] = "SKIPPED_INVALID_PUBLIC_URL"
        return result
    if expected_visual_count <= 0:
        result["status"] = "SKIPPED_NO_EXPECTED_VISUALS"
        return result

    import urllib.request

    for attempt in range(1, retries + 1):
        result["attempts"] = attempt
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                page_html = response.read().decode("utf-8", errors="ignore")

            candidates: list[str] = []
            for tag in re.findall(r"<img\b[^>]+>", page_html, flags=re.IGNORECASE | re.DOTALL):
                candidates.extend(_substack_image_candidates_from_tag(tag))

            canonical_urls: list[str] = []
            seen: set[str] = set()
            for candidate in candidates:
                canonical = _canonical_public_image_url(candidate)
                if not canonical:
                    continue
                if canonical in seen:
                    continue
                seen.add(canonical)
                canonical_urls.append(canonical)

            public_image_count = len(canonical_urls)
            placement_audit = _audit_public_visual_placement(page_html, canonical_urls, expected_placements)
            count_pass = public_image_count >= expected_visual_count
            placement_status = placement_audit.get("placement_order_status")
            status = "PASS" if count_pass else "COUNT_MISMATCH"
            if count_pass and expected_placements and placement_status != "PASS":
                status = str(placement_status or "PLACEMENT_MISMATCH")
            result.update({
                "status": status,
                "public_image_count": public_image_count,
                "public_image_urls": canonical_urls[:10],
                "meets_expected_visual_count": count_pass,
                **placement_audit,
            })
            if (result["meets_expected_visual_count"] and (not expected_placements or result["meets_visual_placement_expectations"])) or attempt == retries:
                return result
        except Exception as exc:
            result.update({"status": "READBACK_FAILED", "error": str(exc)})
        if attempt < retries:
            time.sleep(delay_seconds)
    return result


def run_live_production_pipeline(
    topic: str,
    editorial_angle: str,
    target_audience: str = "general_financial_education",
    live_run: bool = False,
    dispatch_live: bool = False,
    dispatch_rehearsal: bool = False,
    timeout_seconds: int = 420,
    dispatch_platforms: list[str] | tuple[str, ...] | None = None,
    use_latest_headlines: bool = False,
    headline_rehearsal_context: dict[str, Any] | None = None,
    operator_approval_marker: dict[str, Any] | None = None,
    run_id_override: str | None = None,
    public_dispatch_ledger_path: str | Path | None = PUBLIC_DISPATCH_LEDGER_PATH,
) -> dict[str, Any]:
    if dispatch_live and dispatch_rehearsal:
        raise ValueError("dispatch_live_and_dispatch_rehearsal_are_mutually_exclusive")
    _load_live_env_if_needed(live_run or dispatch_live)
    run_id = run_id_override or f"v6_pipeline_{uuid.uuid4().hex[:12]}"
    public_dispatch_topic_hash = build_public_dispatch_topic_hash(topic, editorial_angle)
    print(
        f"[Info] Starting V6 production run {run_id} for topic: '{topic}' "
        f"(live={live_run}, dispatch={dispatch_live}, rehearsal={dispatch_rehearsal})"
    )

    inputs = EngineInput(
        operator_idea=topic,
        target_audience=target_audience,
        editorial_angle=editorial_angle,
        source_context=[],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
        source_notes=f"Live production run on: {topic}"
    )

    if use_latest_headlines:
        try:
            from live_contentops.headline_context_adapter_v6 import inject_headlines_to_input
            inputs = inject_headlines_to_input(inputs)
            print("[Info] Successfully injected latest percolated headlines context into EngineInput.")
        except Exception as exc:
            print(f"[Warning] Failed to inject latest headlines context: {exc}")

    provider_mode = "live_provider_call" if live_run else "dry_run_fixture"

    article_packet = run_article_engine(
        inputs,
        provider_mode=provider_mode,
        live_provider="9router",
        provider_request_budget=2,
        timeout_seconds=timeout_seconds
    )
    editorial_quality_audit = audit_editorial_quality_packet(article_packet, topic=topic)
    article_packet["editorial_quality_audit"] = editorial_quality_audit
    article_packet.setdefault("editorial_review_packet", {})["editorial_acceptance_status"] = editorial_quality_audit["classification"]
    article_packet.setdefault("editorial_review_packet", {})["tier1_editorial_approved"] = editorial_quality_audit["tier1_editorial_approved"]
    if editorial_quality_audit["classification"] != "EDITORIAL_APPROVED":
        warning_label = f"editorial_quality_audit:{editorial_quality_audit['classification']}"
        warnings = article_packet.setdefault("warnings", [])
        if warning_label not in warnings:
            warnings.append(warning_label)

    ARTICLE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(article_packet, f, indent=2, sort_keys=True)
    print(f"[Info] Saved canonical article packet to: {ARTICLE_OUTPUT_PATH}")

    variant_packet = generate_live_platform_variants(
        article_packet_path=ARTICLE_OUTPUT_PATH,
        output_dir=VARIANT_OUTPUT_DIR,
        live_run=live_run,
        timeout_seconds=timeout_seconds,
        dry_run_image_search_isolated=not live_run,
    )
    print(f"[Info] Saved platform variant packet to: {VARIANT_OUTPUT_DIR / 'platform_variant_packet.json'}")

    variants = variant_packet.get("variants", {})
    variant_threads = variant_packet.get("variant_threads", {})
    env_override_allowed = bool(live_run or dispatch_live)
    public_image_url_override = os.environ.get("CONTENTOPS_PUBLIC_IMAGE_URL_OVERRIDE") if env_override_allowed else None
    canonical_url_override = os.environ.get("CONTENTOPS_CANONICAL_URL_OVERRIDE") if env_override_allowed else None
    public_image_url = public_image_url_override or variant_packet.get("public_image_url")
    media_manifest = variant_packet.get("media_manifest") if isinstance(variant_packet.get("media_manifest"), dict) else {}
    selected_media = media_manifest.get("selected_media_by_platform") if isinstance(media_manifest.get("selected_media_by_platform"), dict) else {}
    local_image_path = media_manifest.get("news_image_path") or variant_packet.get("image_path")
    media_assets = media_manifest.get("media_assets") if isinstance(media_manifest.get("media_assets"), list) else None
    canonical_url: str | None = canonical_url_override or None  # populated after Substack publishes
    requested_platforms = tuple(str(item).strip().lower() for item in (dispatch_platforms or []) if str(item).strip())
    selected_platforms = requested_platforms or CURRENT_8_PLATFORMS

    ret = {
        "run_id": run_id,
        "pipeline_status": "GENERATED",
        "article_packet_id": article_packet.get("packet_id"),
        "platform_variant_packet_id": variant_packet.get("platform_variant_packet_id"),
        "image_path": variant_packet.get("image_path"),
        "public_image_url": public_image_url,
        "variant_status": variant_packet.get("variant_status"),
        "timestamp": _utc_now(),
        "timestamp_gmt7": time.strftime("%Y-%m-%dT%H:%M:%S+07:00", time.gmtime(time.time() + 7 * 3600)),
        "dispatch_audit_path": str(DISPATCH_AUDIT_PATH),
        "dispatch_platform_scope": list(selected_platforms),
        "dispatch_idempotency_control": "platform_scope_allowlist",
        "public_dispatch_topic_hash": public_dispatch_topic_hash,
        "public_dispatch_approval_marker_present": operator_approval_marker is not None,
        "public_dispatch_ledger_path": str(public_dispatch_ledger_path) if public_dispatch_ledger_path else None,
        "dry_run": not live_run,
        "dispatch_rehearsal": dispatch_rehearsal,
        "public_write": False if dispatch_rehearsal else None,
        "live_platform_api_called": False if dispatch_rehearsal else None,
        "credential_lookup_performed": False if dispatch_rehearsal else None,
        "headline_rehearsal_context": headline_rehearsal_context or {},
        "media_manifest": media_manifest,
        "media_diversification_audit": media_manifest.get("media_diversification_audit") if isinstance(media_manifest, dict) else None,
        "editorial_acceptance_status": editorial_quality_audit["classification"],
        "tier1_editorial_approved": editorial_quality_audit["tier1_editorial_approved"],
        "editorial_quality_audit": editorial_quality_audit,
    }

    strict_quality_gates = bool(live_run or dispatch_rehearsal)
    article_failures = validate_article_quality(article_packet.get("canonical_article_draft", {})) if strict_quality_gates else []
    variant_failures = validate_platform_variants(variants, variant_threads, live_run=strict_quality_gates) if strict_quality_gates else []
    variant_failures.extend(variant_packet.get("validation_failures") or [])
    qa_gate_failures: list[str] = []
    if (dispatch_live or dispatch_rehearsal) and editorial_quality_audit["classification"] != "EDITORIAL_APPROVED":
        qa_gate_failures.append(f"editorial_quality_gate:{editorial_quality_audit['classification']}")
    media_diversification_audit = media_manifest.get("media_diversification_audit") if isinstance(media_manifest, dict) else None
    if (dispatch_live or dispatch_rehearsal) and isinstance(media_diversification_audit, dict):
        if media_diversification_audit.get("audit_status") == "FAIL":
            qa_gate_failures.append(
                "media_diversification_gate_failed:"
                + "|".join(media_diversification_audit.get("blockers") or ["unknown"])
            )
        if not media_diversification_audit.get("auto_publication_safe", False):
            qa_gate_failures.append("media_rights_operator_review_required")
    article_status = str(article_packet.get("status") or article_packet.get("packet_status") or "").upper()
    if (dispatch_live or dispatch_rehearsal) and article_status in {"BLOCKED", "FAILED", "VALIDATION_FAILED"}:
        qa_gate_failures.append(f"canonical_article_packet_status:{article_status}")
    variant_status = str(variant_packet.get("variant_status") or "").upper()
    if (dispatch_live or dispatch_rehearsal) and variant_status in {"BLOCKED", "FAILED", "VALIDATION_FAILED", "VARIANT_VALIDATION_FAILED"}:
        qa_gate_failures.append(f"variant_packet_status:{variant_status}")
    public_dispatch_gate: dict[str, Any] | None = None
    if dispatch_live:
        public_dispatch_gate = evaluate_public_dispatch_freeze(
            platform="pipeline",
            action="dispatch_live",
            run_id=run_id,
            topic_hash=public_dispatch_topic_hash,
            operator_approval_marker=operator_approval_marker,
            body_text=topic,
            payload_hash_required=False,
            duplicate_check=False,
        )
        ret["public_dispatch_freeze_guard"] = public_dispatch_gate
        if not public_dispatch_gate["dispatch_allowed"]:
            qa_gate_failures.extend(
                f"public_dispatch_freeze_guard:{blocker}"
                for blocker in public_dispatch_gate.get("blockers", [])
            )
    raw_blockers = list(article_packet.get("blockers") or []) + article_failures + variant_failures + qa_gate_failures
    blockers = list(dict.fromkeys(raw_blockers))  # de-dupe while preserving order
    quality_gate_result = _quality_gate_status(blockers)
    ret["quality_gate_result"] = quality_gate_result
    if env_override_allowed and os.environ.get("CONTENTOPS_BYPASS_QUALITY_GATES") == "true":
        print(f"[Warning] CONTENTOPS_BYPASS_QUALITY_GATES ignored for public dispatch safety: {blockers}")
        ret.setdefault("warnings", []).append("quality_gate_bypass_ignored_for_public_dispatch")
    if (dispatch_live or dispatch_rehearsal) and blockers:
        ret.update({
            "pipeline_status": "DISPATCH_BLOCKED" if dispatch_live else "REHEARSAL_BLOCKED",
            "dispatch_live": False,
            "dispatch_rehearsal": bool(dispatch_rehearsal),
            "public_write": False,
            "live_platform_api_called": False,
            "credential_lookup_performed": False,
            "dispatch_blocked": True,
            "dispatch_blockers": blockers,
            "dispatch_summary": {
                "attempted_platforms": [],
                "successful_platforms": [],
                "failed_platforms": [],
                "blocked_platforms": ["pipeline"],
            },
        })
        _write_dispatch_audit(ret)
        return ret

    if dispatch_live:
        print(f"[Info] Starting automated live dispatches for: {', '.join(selected_platforms)}")
        dispatch_results: dict[str, Any] = {}
        public_dispatch_hashes = load_public_dispatch_hashes(public_dispatch_ledger_path)

        if "substack" in selected_platforms:
            try:
                from live_contentops.substack_browser_adapter_v6 import execute_substack_post
                body = variants.get("substack", "")
                missing = _require_payload(body, "substack_body")
                if missing:
                    dispatch_results["substack"] = _blocked_result("substack", missing)
                else:
                    print("[Info] Dispatching to Substack...")
                    visual_marker_ids = re.findall(r"\[\[VISUAL:([a-zA-Z0-9_-]+)\]\]", body or "")
                    visual_slots = article_packet.get("canonical_article_draft", {}).get("visual_slots")
                    expected_visual_placements = _expected_substack_visual_placements(
                        visual_marker_ids,
                        visual_slots if isinstance(visual_slots, list) else None,
                        body,
                    )
                    sub_res = execute_substack_post(
                        title=article_packet.get("canonical_article_draft", {}).get("title", topic),
                        subtitle=article_packet.get("canonical_article_draft", {}).get("subtitle", ""),
                        body_markdown=body,
                        image_path=local_image_path,
                        image_assets=media_assets,
                        dry_run=False
                    )
                    dispatch_results["substack"] = _normalize_dispatch_result("substack", sub_res)
                    # Substack is the canonical long-form home; its URL is the clickable link for every other platform.
                    if dispatch_results["substack"].get("ok"):
                        draft_title = article_packet.get("canonical_article_draft", {}).get("title", topic)
                        raw_canonical_url = (
                            sub_res.get("public_url")
                            or (sub_res.get("response") or {}).get("public_url")
                            or dispatch_results["substack"].get("url")
                            or canonical_url
                        )
                        canonical_url = resolve_substack_public_url(raw_canonical_url, draft_title)
                        if canonical_url:
                            dispatch_results["substack"]["url"] = canonical_url
                        adapter_image = sub_res.get("public_image_url") or (sub_res.get("response") or {}).get("public_image_url")
                        if _is_useful_public_image_url(adapter_image):
                            public_image_url = adapter_image
                        if canonical_url:
                            # Extract CDN image URL from published Substack post HTML
                            extracted_img = extract_og_image(canonical_url)
                            if extracted_img:
                                public_image_url = extracted_img
                            media_upload_results = sub_res.get("media_upload_results") or (sub_res.get("response") or {}).get("media_upload_results") or []
                            uploaded_visual_count = sum(
                                1 for item in media_upload_results
                                if isinstance(item, dict) and item.get("status") == "uploaded"
                            )
                            upload_attempt_count = sum(
                                1 for item in media_upload_results
                                if isinstance(item, dict) and item.get("status") in {"uploaded", "uploaded_unverified"}
                            )
                            public_visual_readback = audit_substack_public_visuals(
                                canonical_url,
                                expected_visual_count=len(visual_marker_ids),
                                expected_placements=expected_visual_placements,
                            )
                            public_readback_confirmed = (
                                public_visual_readback.get("meets_expected_visual_count")
                                and public_visual_readback.get("meets_visual_placement_expectations")
                            )
                            if (
                                len(visual_marker_ids)
                                and (uploaded_visual_count >= len(visual_marker_ids) or upload_attempt_count >= len(visual_marker_ids))
                                and public_readback_confirmed
                            ):
                                placement_status = "PASS"
                            elif (
                                len(visual_marker_ids)
                                and (uploaded_visual_count >= len(visual_marker_ids) or upload_attempt_count >= len(visual_marker_ids))
                                and public_visual_readback.get("meets_expected_visual_count")
                            ):
                                placement_status = f"PUBLIC_PLACEMENT_{public_visual_readback.get('placement_order_status') or 'INCONCLUSIVE'}"
                            else:
                                placement_status = "UPLOAD_MISMATCH"
                            visual_evidence = {
                                "visual_marker_ids": visual_marker_ids,
                                "visual_marker_count": len(visual_marker_ids),
                                "expected_visual_placements": expected_visual_placements,
                                "uploaded_visual_count": uploaded_visual_count,
                                "upload_attempt_count": upload_attempt_count,
                                "media_upload_results": media_upload_results,
                                "public_visual_readback": public_visual_readback,
                                "placement_readback_status": placement_status,
                            }
                            dispatch_results["substack"]["visual_evidence"] = visual_evidence
                            if len(visual_marker_ids) and placement_status != "PASS":
                                dispatch_results["substack"].update({
                                    "ok": False,
                                    "status": "FAILED_VISUAL_PLACEMENT",
                                    "error_class": "substack_visual_placement_failed",
                                    "error": placement_status,
                                })
                            if isinstance(dispatch_results["substack"].get("raw"), dict):
                                dispatch_results["substack"]["raw"]["visual_evidence"] = visual_evidence
                                response = dispatch_results["substack"]["raw"].setdefault("response", {})
                                if isinstance(response, dict):
                                    response["visual_evidence"] = visual_evidence
                    print(f"[Info] Substack dispatch outcome: {dispatch_results['substack']['status']} (URL: {dispatch_results['substack'].get('url')})")
            except Exception as exc:
                print(f"[Warning] Substack dispatch failed: {exc}")
                dispatch_results["substack"] = _normalize_dispatch_result("substack", error=exc)
            time.sleep(5)

        if "linkedin" in selected_platforms:
            try:
                from live_contentops.linkedin_browser_adapter_v6 import execute_linkedin_post
                text = _apply_canonical_link(variants.get("linkedin", ""), canonical_url)
                missing = _require_payload(text, "linkedin_text")
                if missing:
                    dispatch_results["linkedin"] = _blocked_result("linkedin", missing)
                else:
                    print("[Info] Dispatching to LinkedIn...")
                    li_res = execute_linkedin_post(text=text, image_path=local_image_path, dry_run=False)
                    dispatch_results["linkedin"] = _normalize_dispatch_result("linkedin", li_res)
                    print(f"[Info] LinkedIn dispatch outcome: {dispatch_results['linkedin']['status']} (URL: {dispatch_results['linkedin'].get('url')})")
            except Exception as exc:
                print(f"[Warning] LinkedIn dispatch failed: {exc}")
                dispatch_results["linkedin"] = _normalize_dispatch_result("linkedin", error=exc)
            time.sleep(5)

        if "x" in selected_platforms:
            try:
                from live_contentops.x_browser_adapter_v6 import execute_x_post, execute_x_comment
                x_thread = [str(item).strip() for item in variant_threads.get("x", []) if str(item).strip()]
                if not x_thread:
                    dispatch_results["x_post"] = _blocked_result("x_post", "x_thread_missing")
                    dispatch_results["x_replies"] = []
                else:
                    # Append the clickable canonical link as the final tweet in the thread.
                    if canonical_url:
                        x_thread.append(_apply_canonical_link("", canonical_url).strip())
                    print(f"[Info] Dispatching thread of {len(x_thread)} tweets to X...")
                    x_res = execute_x_post(text=x_thread[0], image_url=local_image_path, dry_run=False)
                    dispatch_results["x_post"] = _normalize_dispatch_result("x_post", x_res)
                    print(f"[Info] X initial post outcome: {dispatch_results['x_post']['status']}")

                    comment_results = []
                    if dispatch_results["x_post"].get("ok"):
                        post_url = dispatch_results["x_post"].get("url") or ""
                        tweet_id = post_url.split("/status/")[-1] if "/status/" in post_url else ""
                        target_ref = post_url if post_url else tweet_id
                        for idx, comment_text in enumerate(x_thread[1:], start=1):
                            time.sleep(6)
                            print(f"[Info] Dispatching thread reply {idx}/{len(x_thread) - 1}...")
                            try:
                                rep_res = execute_x_comment(tweet_url_or_id=target_ref, text=comment_text, dry_run=False)
                                comment_results.append(_normalize_dispatch_result(f"x_reply_{idx}", rep_res))
                            except Exception as exc:
                                comment_results.append(_normalize_dispatch_result(f"x_reply_{idx}", error=exc))
                    dispatch_results["x_replies"] = comment_results
            except Exception as exc:
                print(f"[Warning] X thread dispatch failed: {exc}")
                dispatch_results["x"] = _normalize_dispatch_result("x", error=exc)
            time.sleep(5)

        if "instagram" in selected_platforms:
            try:
                from live_contentops.instagram_adapter_v6 import execute_instagram_post
                # Instagram captions can't have clickable links, but include the URL as plain text for copy/paste.
                caption = _apply_canonical_link(variants.get("instagram_caption", variants.get("telegram", "")), canonical_url)
                image_candidates = _instagram_image_candidates(
                    public_image_url=public_image_url,
                    selected_media=selected_media,
                    media_manifest=media_manifest,
                )
                missing = _require_payload(caption, "instagram_caption") or _require_payload(image_candidates[0] if image_candidates else None, "instagram_image_url")
                if missing:
                    dispatch_results["instagram"] = _blocked_result("instagram", missing)
                else:
                    print(f"[Info] Dispatching to Instagram with {len(image_candidates)} image candidate(s)...")
                    last_result: dict[str, Any] | None = None
                    for idx, active_img in enumerate(image_candidates, start=1):
                        if idx > 1:
                            print(f"[Info] Retrying Instagram with fallback image candidate {idx}/{len(image_candidates)}...")
                        ig_res = execute_instagram_post(image_url=active_img, caption=caption, dry_run=False)
                        normalized = _normalize_dispatch_result("instagram", ig_res)
                        normalized["attempted_image_url"] = active_img
                        last_result = normalized
                        if normalized.get("ok") or not _instagram_media_failure(normalized):
                            break
                    dispatch_results["instagram"] = last_result or _blocked_result("instagram", "instagram_image_url_missing")
                    print(f"[Info] Instagram dispatch outcome: {dispatch_results['instagram']['status']}")
            except Exception as exc:
                print(f"[Warning] Instagram dispatch failed: {exc}")
                dispatch_results["instagram"] = _normalize_dispatch_result("instagram", error=exc)
            time.sleep(5)

        if "facebook" in selected_platforms:
            try:
                from live_contentops.facebook_page_adapter_v6 import execute_facebook_photo, execute_facebook_post
                message = _apply_canonical_link(variants.get("facebook", variants.get("linkedin", "")), canonical_url)
                facebook_media = selected_media.get("facebook") or public_image_url
                missing = _require_payload(message, "facebook_message")
                if missing:
                    dispatch_results["facebook"] = _blocked_result("facebook", missing)
                else:
                    print("[Info] Dispatching to Facebook Page...")
                    # Prefer a true photo post over a link preview so the selected chart/image is visible.
                    if facebook_media:
                        fb_res = execute_facebook_photo(message=message, image_url=facebook_media, dry_run=False)
                    else:
                        fb_res = execute_facebook_post(message=message, link=canonical_url, dry_run=False)
                    dispatch_results["facebook"] = _normalize_dispatch_result("facebook", fb_res)
                    print(f"[Info] Facebook dispatch outcome: {dispatch_results['facebook']['status']}")
            except Exception as exc:
                print(f"[Warning] Facebook dispatch failed: {exc}")
                dispatch_results["facebook"] = _normalize_dispatch_result("facebook", error=exc)
            time.sleep(5)

        if "telegram" in selected_platforms:
            try:
                from live_contentops.telegram_live_adapter_v6 import execute_telegram_post, execute_telegram_photo
                message = _apply_canonical_link(variants.get("telegram", ""), canonical_url)
                telegram_media = local_image_path or selected_media.get("telegram") or public_image_url
                telegram_action = "photo" if telegram_media else "post"
                telegram_body = _fit_telegram_photo_caption(message, canonical_url) if telegram_media else message
                telegram_payload_hash = build_public_dispatch_payload_hash(
                    platform="telegram",
                    action=telegram_action,
                    body_text=telegram_body,
                    canonical_url=canonical_url,
                    media_url=telegram_media,
                    topic_hash=public_dispatch_topic_hash,
                )
                telegram_guard = evaluate_public_dispatch_freeze(
                    platform="telegram",
                    action=telegram_action,
                    run_id=run_id,
                    topic_hash=public_dispatch_topic_hash,
                    operator_approval_marker=operator_approval_marker,
                    body_text=telegram_body,
                    canonical_url=canonical_url,
                    media_url=telegram_media,
                    payload_hash=telegram_payload_hash,
                    payload_hash_required=True,
                    prior_dispatch_hashes=public_dispatch_hashes,
                    canonical_packet_status=article_status if article_status else None,
                )
                missing = _require_payload(message, "telegram_message")
                if missing:
                    dispatch_results["telegram"] = _blocked_result("telegram", missing)
                elif not telegram_guard["dispatch_allowed"]:
                    dispatch_results["telegram"] = _guard_blocked_result("telegram", telegram_guard)
                else:
                    print("[Info] Dispatching to Telegram Channel...")
                    approval_context = {
                        "operator_approval_marker": operator_approval_marker,
                        "run_id": run_id,
                        "topic_hash": public_dispatch_topic_hash,
                        "payload_hash": telegram_payload_hash,
                        "canonical_url": canonical_url,
                        "media_url": telegram_media,
                        "prior_dispatch_hashes": public_dispatch_hashes,
                        "canonical_packet_status": article_status if article_status else None,
                        "public_dispatch_ledger_path": str(public_dispatch_ledger_path) if public_dispatch_ledger_path else None,
                    }
                    if telegram_media:
                        tg_res = execute_telegram_photo(
                            photo_url=telegram_media,
                            caption=telegram_body,
                            dry_run=False,
                            approval_context=approval_context,
                        )
                    else:
                        tg_res = execute_telegram_post(
                            message=message,
                            dry_run=False,
                            approval_context=approval_context,
                        )
                    dispatch_results["telegram"] = _normalize_dispatch_result("telegram", tg_res)
                    if telegram_media:
                        telegram_visual_evidence = _telegram_photo_delivery_evidence(
                            dispatch_results["telegram"],
                            telegram_media,
                        )
                        dispatch_results["telegram"]["visual_evidence"] = telegram_visual_evidence
                        if isinstance(dispatch_results["telegram"].get("raw"), dict):
                            dispatch_results["telegram"]["raw"]["visual_evidence"] = telegram_visual_evidence
                        if dispatch_results["telegram"].get("ok") and telegram_visual_evidence["visual_delivery_status"] != "PASS":
                            dispatch_results["telegram"].update({
                                "ok": False,
                                "status": "FAILED_VISUAL_DELIVERY",
                                "error_class": "telegram_visual_delivery_unproven",
                                "error": telegram_visual_evidence["visual_delivery_status"],
                            })
                    if dispatch_results["telegram"].get("ok"):
                        append_public_dispatch_ledger(
                            ledger_path=public_dispatch_ledger_path,
                            platform="telegram",
                            action=telegram_action,
                            run_id=run_id,
                            topic_hash=public_dispatch_topic_hash,
                            payload_hash=telegram_payload_hash,
                            canonical_url=canonical_url,
                            media_url=telegram_media,
                        )
                    print(f"[Info] Telegram dispatch outcome: {dispatch_results['telegram']['status']}")
            except Exception as exc:
                print(f"[Warning] Telegram dispatch failed: {exc}")
                dispatch_results["telegram"] = _normalize_dispatch_result("telegram", error=exc)
            time.sleep(5)

        if "threads" in selected_platforms:
            try:
                from live_contentops.threads_adapter_v6 import execute_threads_post
                threads_sequence = [str(item).strip() for item in variant_threads.get("threads", []) if str(item).strip()]
                if not threads_sequence:
                    dispatch_results["threads"] = _blocked_result("threads", "threads_thread_missing")
                    dispatch_results["threads_replies"] = []
                else:
                    # Append the clickable canonical link as the final reply in the thread.
                    if canonical_url:
                        threads_sequence.append(_apply_canonical_link("", canonical_url).strip())
                    print("[Info] Dispatching to Threads...")
                    threads_media = selected_media.get("threads") or public_image_url
                    threads_res = execute_threads_post(text=threads_sequence[0], image_url=threads_media, dry_run=False)
                    dispatch_results["threads"] = _normalize_dispatch_result("threads", threads_res)
                    thread_reply_results = []
                    parent_id = threads_res.get("id") or threads_res.get("container_id")
                    if dispatch_results["threads"].get("ok") and parent_id:
                        for idx, reply_text in enumerate(threads_sequence[1:], start=1):
                            time.sleep(6)
                            print(f"[Info] Dispatching Threads reply {idx}/{len(threads_sequence) - 1}...")
                            try:
                                thread_reply_results.append(_normalize_dispatch_result(
                                    f"threads_reply_{idx}",
                                    execute_threads_post(text=reply_text, reply_to_id=parent_id, dry_run=False)
                                ))
                            except Exception as exc:
                                thread_reply_results.append(_normalize_dispatch_result(f"threads_reply_{idx}", error=exc))
                    dispatch_results["threads_replies"] = thread_reply_results
                print(f"[Info] Threads dispatch outcome: {dispatch_results['threads'].get('status')}")
            except Exception as exc:
                print(f"[Warning] Threads dispatch failed: {exc}")
                dispatch_results["threads"] = _normalize_dispatch_result("threads", error=exc)
            time.sleep(5)

        if "discord" in selected_platforms:
            try:
                from live_contentops.discord_live_adapter_v6 import execute_discord_post
                message = _apply_canonical_link(variants.get("discord", ""), canonical_url)
                missing = _require_payload(message, "discord_message")
                if missing:
                    dispatch_results["discord"] = _blocked_result("discord", missing)
                else:
                    print("[Info] Dispatching to Discord Channel...")
                    # Rich embed makes the canonical link clickable and renders the hero image inline.
                    discord_embeds = None
                    if canonical_url or public_image_url:
                        embed: dict[str, Any] = {"title": article_packet.get("canonical_article_draft", {}).get("title", topic)}
                        if canonical_url:
                            embed["url"] = canonical_url
                        if public_image_url:
                            embed["image"] = {"url": public_image_url}
                        discord_embeds = [embed]
                    discord_res = execute_discord_post(message=message, embeds=discord_embeds, dry_run=False)
                    dispatch_results["discord"] = _normalize_dispatch_result("discord", discord_res)
                    print(f"[Info] Discord dispatch outcome: {dispatch_results['discord']['status']}")
            except Exception as exc:
                print(f"[Warning] Discord dispatch failed: {exc}")
                dispatch_results["discord"] = _normalize_dispatch_result("discord", error=exc)
            time.sleep(5)

        summary = _dispatch_summary(dispatch_results)
        print("[Info] Automated dispatches complete.")
        ret["dispatch_live"] = True
        ret["dispatch_results"] = dispatch_results
        ret["dispatch_summary"] = summary
        ret["canonical_url"] = canonical_url
        ret["public_image_url"] = public_image_url
        ret["pipeline_status"] = "DISPATCH_COMPLETE" if not summary["failed_platforms"] and not summary["blocked_platforms"] else "DISPATCH_PARTIAL_FAILURE"
        _write_dispatch_audit(ret)

    if dispatch_rehearsal:
        rehearsal = _build_rehearsal_dispatch(
            run_id=run_id,
            public_dispatch_topic_hash=public_dispatch_topic_hash,
            article_packet=article_packet,
            variant_packet=variant_packet,
            selected_platforms=selected_platforms,
            canonical_url=canonical_url,
            local_image_path=local_image_path,
            public_image_url=public_image_url,
            selected_media=selected_media,
            public_dispatch_ledger_path=public_dispatch_ledger_path,
            quality_gate_result=quality_gate_result,
        )
        ret["dispatch_live"] = False
        ret["dispatch_rehearsal"] = True
        ret["dry_run"] = True
        ret["public_write"] = False
        ret["live_platform_api_called"] = False
        ret["credential_lookup_performed"] = False
        ret["dispatch_results"] = rehearsal["dispatch_results"]
        ret["dispatch_summary"] = rehearsal["dispatch_summary"]
        ret["approval_marker_envelope"] = rehearsal["approval_marker_envelope"]
        ret["public_dispatch_approval_marker_envelope"] = rehearsal["approval_marker_envelope"]
        ret["canonical_url"] = canonical_url
        ret["public_image_url"] = public_image_url
        summary = rehearsal["dispatch_summary"]
        if summary["failed_platforms"] or summary["blocked_platforms"]:
            ret["pipeline_status"] = "REHEARSAL_BLOCKED"
            ret["dispatch_blocked"] = True
            ret["dispatch_blockers"] = summary["failed_platforms"] + summary["blocked_platforms"]
        else:
            ret["pipeline_status"] = REHEARSAL_READY_STATUS
            ret["dispatch_blocked"] = False
            ret["dispatch_blockers"] = []
        _write_dispatch_audit(ret)

    return ret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Production Pipeline Runner")
    parser.add_argument("--topic", default=None, help="Topic idea")
    parser.add_argument("--angle", default=None, help="Editorial angle")
    parser.add_argument("--live-run", action="store_true", help="Enable 9router LLM and live searches")
    parser.add_argument("--dispatch-live", action="store_true", help="Enable live posting/publishing to all platforms")
    parser.add_argument("--dispatch-rehearsal", action="store_true", help="Run full dry-run dispatch rehearsal with no public writes")
    parser.add_argument("--select-scheduler-slot", action="store_true", help="Select the current daily schedule slot for rehearsal topic/angle")
    parser.add_argument("--daily-schedule", default=str(DAILY_SCHEDULE_PATH), help="Daily schedule JSON path for scheduler-slot selection")
    parser.add_argument("--target-audience", default="general_financial_education", help="Target audience")
    parser.add_argument("--timeout-seconds", type=int, default=420, help="Provider timeout seconds (default 7 minutes for full-length live generation)")
    parser.add_argument("--run-id", default=None, help="Explicit run id for operator-approved public dispatch")
    parser.add_argument("--operator-approval-marker", default=None, help="Path to explicit public dispatch approval marker JSON")
    parser.add_argument("--public-dispatch-ledger", default=str(PUBLIC_DISPATCH_LEDGER_PATH), help="Duplicate ledger path for public dispatch guard")
    parser.add_argument(
        "--dispatch-platform",
        action="append",
        default=[],
        help="Restrict live dispatch to one platform; repeat for multiple. Defaults to all platforms.",
    )
    parser.add_argument("--write-rehearsal-evidence", action="store_true", help="Write sanitized rehearsal evidence/readback packet")
    parser.add_argument("--rehearsal-evidence-output", default=str(DEFAULT_EVIDENCE_PACKET_PATH), help="Evidence packet output path")
    parser.add_argument("--use-latest-headlines", action="store_true", help="Inject latest percolated headlines from Vol-Impact Percolator as context")
    args = parser.parse_args(argv)

    headline_rehearsal_context: dict[str, Any] = {}
    topic = args.topic
    angle = args.angle
    if args.select_scheduler_slot:
        headline_rehearsal_context = select_rehearsal_scheduler_slot(args.daily_schedule)
        topic = topic or str(headline_rehearsal_context.get("selected_topic") or "")
        angle = angle or str(headline_rehearsal_context.get("selected_angle") or "")
    elif args.dispatch_rehearsal:
        headline_rehearsal_context = {
            "selection_reason": "operator_supplied_topic_or_default_rehearsal_topic",
            **_headline_sidecar_inventory(),
        }
    topic = topic or DEFAULT_REHEARSAL_TOPIC
    angle = angle or DEFAULT_REHEARSAL_ANGLE

    command = ["python", "-m", "live_contentops.live_production_pipeline_runner_v6"]
    command.extend(["--topic", topic, "--angle", angle, "--target-audience", args.target_audience, "--timeout-seconds", str(args.timeout_seconds)])
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.operator_approval_marker:
        command.extend(["--operator-approval-marker", args.operator_approval_marker])
    if args.public_dispatch_ledger:
        command.extend(["--public-dispatch-ledger", args.public_dispatch_ledger])
    if args.live_run:
        command.append("--live-run")
    if args.dispatch_live:
        command.append("--dispatch-live")
    if args.dispatch_rehearsal:
        command.append("--dispatch-rehearsal")
    if args.select_scheduler_slot:
        command.extend(["--select-scheduler-slot", "--daily-schedule", args.daily_schedule])
    if args.use_latest_headlines:
        command.append("--use-latest-headlines")
    for platform in args.dispatch_platform:
        command.extend(["--dispatch-platform", platform])
    if args.write_rehearsal_evidence:
        command.extend(["--write-rehearsal-evidence", "--rehearsal-evidence-output", args.rehearsal_evidence_output])

    operator_approval_marker = _load_operator_approval_marker(args.operator_approval_marker)
    result = run_live_production_pipeline(
        topic=topic,
        editorial_angle=angle,
        target_audience=args.target_audience,
        live_run=args.live_run,
        dispatch_live=args.dispatch_live,
        dispatch_rehearsal=args.dispatch_rehearsal,
        timeout_seconds=args.timeout_seconds,
        dispatch_platforms=args.dispatch_platform,
        use_latest_headlines=args.use_latest_headlines,
        headline_rehearsal_context=headline_rehearsal_context,
        operator_approval_marker=operator_approval_marker,
        run_id_override=args.run_id,
        public_dispatch_ledger_path=args.public_dispatch_ledger,
    )
    if args.write_rehearsal_evidence:
        evidence = build_rehearsal_evidence_packet(result, command=command)
        evidence_path = write_rehearsal_evidence(evidence, args.rehearsal_evidence_output)
        result["rehearsal_evidence_path"] = str(evidence_path)
        result["rehearsal_evidence_packet_id"] = evidence["evidence_packet_id"]
    print(json.dumps(result, indent=2))
    status = str(result.get("pipeline_status") or "")
    summary = result.get("dispatch_summary") or {}
    print(
        "[FinalStatus] "
        + json.dumps(
            {
                "run_id": result.get("run_id"),
                "pipeline_status": status,
                "dispatch_live": bool(result.get("dispatch_live")),
                "dispatch_rehearsal": bool(result.get("dispatch_rehearsal")),
                "public_write": result.get("public_write"),
                "attempted_platforms": summary.get("attempted_platforms", []),
                "successful_platforms": summary.get("successful_platforms", []),
                "failed_platforms": summary.get("failed_platforms", []),
                "blocked_platforms": summary.get("blocked_platforms", []),
                "dispatch_blockers": result.get("dispatch_blockers", []),
            },
            sort_keys=True,
        )
    )
    # A live launch that was blocked or only partially dispatched must fail loudly
    # so the server/dashboard cannot report it as a clean success.
    if status in {"DISPATCH_BLOCKED", "DISPATCH_PARTIAL_FAILURE", "REHEARSAL_BLOCKED"}:
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
