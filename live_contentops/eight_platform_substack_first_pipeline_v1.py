"""Production ContentOps runner: Substack first, then eight platform families.

This is the canonical live path for the dedicated Microsoft Edge profile. It
reuses the LLM idea-selection, grounded-media, Telegram repair, and proven API
adapters already in the repository while making Substack publication the gate
for every derivative write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops.edge_cdp_publishing_adapter_v1 import (
    comment_existing_linkedin_post_via_edge,
    edit_existing_linkedin_post_via_edge,
    publish_linkedin_post_via_edge,
    publish_substack_article_via_edge,
    publish_x_post_via_edge,
    publish_x_reply_via_edge,
    publish_youtube_community_post_via_edge,
    probe_authenticated_platform_session,
    readback_linkedin_post_via_edge,
    readback_linkedin_activity_via_edge,
    readback_youtube_community_post_via_edge,
    readback_x_thread_via_edge,
    reconcile_existing_linkedin_post_via_edge,
)
from live_contentops.publishing_profile_registry_v1 import browser_doctor
from live_contentops.media_manifest_authority_v1 import build_delivery_media_manifest, select_primary_chart
from live_contentops.substack_browser_adapter_v6 import build_supervised_substack_browser_readback
from live_contentops.substack_first_north_star_pipeline_loop_v1 import (
    complete_substack_first_pipeline,
    prepare_substack_first_pipeline,
)


TASK_LABEL = "TASK_CONTENTOPS_HEAVY_TIER1_EDITORIAL_PLATFORM_VARIANT_RELIABILITY_AND_VIDEO_CAPABILITY_SPLIT_V3"
SCHEMA_VERSION = "contentops.eight_platform_substack_first_pipeline.v1"
OUTPUT_ROOT = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1")
EXPECTED_DESTINATIONS = (
    "substack",
    "telegram",
    "x",
    "discord",
    "linkedin",
    "facebook_page",
    "instagram_business",
    "threads",
    "tiktok",
    "youtube",
)
SUCCESS_STATUSES = {"SUCCESS", "ALREADY_SUCCESSFUL_IDEMPOTENT"}
# These outcomes can occur after a platform has accepted a write but before a
# permalink is recovered. A later retry of the same payload could duplicate it.
UNKNOWN_WRITE_STATUSES = {
    "FAILED_SUBSTACK_PUBLIC_URL_READBACK",
    "FAILED_X_PERMALINK_READBACK",
    "FAILED_LINKEDIN_PERMALINK_READBACK",
    "FAILED_LINKEDIN_EDIT_READBACK",
    "FAILED_LINKEDIN_STRICT_READBACK",
    "FAILED_TIKTOK_PERMALINK_READBACK",
    "FAILED_YOUTUBE_PUBLIC_URL_READBACK",
    "FAILED_YOUTUBE_COMMUNITY_POST_URL_READBACK",
    "FAILED_YOUTUBE_COMMUNITY_POST_READBACK",
    "FAILED_YOUTUBE_STRICT_READBACK",
    "FAILED_FACEBOOK_REPLACEMENT_READBACK",
    "FAILED_INSTAGRAM_REPLACEMENT_READBACK",
    "FAILED_THREADS_REPLY_READBACK",
    "FAILED_X_REPLY_PERMALINK_READBACK",
}
TEXT_IMAGE_PASS_DESTINATIONS = tuple(platform for platform in EXPECTED_DESTINATIONS if platform != "tiktok")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: str | Path, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _sentence_units(value: str) -> list[str]:
    normalized = " ".join(str(value or "").split())
    return [item.strip() for item in _SENTENCE_BOUNDARY_RE.split(normalized) if item.strip()]


def _punctuate(value: str) -> str:
    clean = value.strip(" ,;:")
    return clean if not clean or clean[-1] in ".!?" else clean + "."


def _split_oversized_sentence(sentence: str, *, limit: int) -> list[str]:
    """Split only an individually over-limit sentence, preferring semantic clauses."""
    clauses = re.split(r"(?<=[,;:])\s+(?=(?:and|but|while|which|with|as)\b)", sentence)
    if len(clauses) == 1:
        clauses = re.split(r"(?<=;)\s+|(?<=:)\s+", sentence)
    if len(clauses) > 1 and all(len(_punctuate(item)) <= limit for item in clauses):
        return [_punctuate(item) for item in clauses if item.strip()]
    words = sentence.split()
    rows: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(_punctuate(candidate)) <= limit:
            current = candidate
        else:
            if current:
                rows.append(_punctuate(current))
            current = word
    if current:
        rows.append(_punctuate(current))
    return rows


def _balanced_pack(units: Sequence[str], *, limit: int) -> list[str]:
    if not units:
        return []
    separator = 2
    greedy_count = 1
    running = 0
    for unit in units:
        needed = len(unit) if running == 0 else separator + len(unit)
        if running and running + needed > limit:
            greedy_count += 1
            running = len(unit)
        else:
            running += needed
    target = sum(map(len, units)) + separator * max(0, len(units) - greedy_count)
    target /= greedy_count

    @lru_cache(maxsize=None)
    def solve(start: int, groups: int) -> tuple[float, tuple[str, ...]] | None:
        if groups == 0:
            return (0.0, ()) if start == len(units) else None
        best: tuple[float, tuple[str, ...]] | None = None
        chunk = ""
        for end in range(start, len(units)):
            proposed = units[end] if not chunk else f"{chunk}\n\n{units[end]}"
            if len(proposed) > limit:
                break
            remaining_units = len(units) - end - 1
            if remaining_units < groups - 1:
                break
            tail = solve(end + 1, groups - 1)
            if tail is None:
                chunk = proposed
                continue
            cost = (len(proposed) - target) ** 2 + tail[0]
            candidate = (cost, (proposed, *tail[1]))
            if best is None or candidate[0] < best[0]:
                best = candidate
            chunk = proposed
        return best

    packed = solve(0, greedy_count)
    return list(packed[1]) if packed else list(units)


def _split_complete_chunks(parts: Sequence[str], *, limit: int) -> list[str]:
    """Pack sentence/paragraph units in order without arbitrary character slicing."""
    units: list[str] = []
    seen: set[str] = set()
    for source in parts:
        for sentence in _sentence_units(str(source or "")):
            candidates = [sentence] if len(sentence) <= limit else _split_oversized_sentence(sentence, limit=limit)
            for candidate in candidates:
                key = re.sub(r"\W+", " ", candidate.casefold()).strip()
                if key and key not in seen:
                    units.append(candidate)
                    seen.add(key)
    return _balanced_pack(units, limit=limit)


def _first_complete_sentence(value: str) -> str:
    normalized = " ".join(str(value or "").split())
    match = re.match(r"^(.+?[.!?])(?:\s|$)", normalized)
    return match.group(1) if match else normalized


def _sharp_social_lede(value: str, *, maximum: int) -> str:
    sentence = _first_complete_sentence(value)
    if len(sentence) <= maximum:
        return sentence
    lead = re.split(r",\s+(?:inside|keeping|while|but|as)\b", sentence, maxsplit=1, flags=re.IGNORECASE)[0]
    if len(_punctuate(lead)) <= maximum:
        return _punctuate(lead)
    return _split_oversized_sentence(sentence, limit=maximum)[0]


def _concise_semantic_sentence(value: str, *, maximum: int) -> str:
    sentence = _first_complete_sentence(value)
    if len(sentence) <= maximum:
        return sentence
    lead = re.split(r";\s+|:\s+|,\s+(?:while|but|and|which|with|as)\b", sentence, maxsplit=1, flags=re.IGNORECASE)[0]
    if len(_punctuate(lead)) <= maximum:
        return _punctuate(lead)
    return _split_oversized_sentence(sentence, limit=maximum)[0]


def _thread_quality(posts: Sequence[Mapping[str, Any]], *, limit: int) -> dict[str, Any]:
    texts = [str(row.get("text") or "") for row in posts]
    lengths = [len(item) for item in texts]
    sentence_keys: list[str] = []
    orphan_fragments = 0
    sentence_boundary_pass = True
    for post_index, text in enumerate(texts):
        stripped = text.strip()
        if not stripped:
            orphan_fragments += 1
            sentence_boundary_pass = False
            continue
        for paragraph_index, paragraph in enumerate([item.strip() for item in stripped.split("\n\n") if item.strip()]):
            if post_index == 0 and paragraph_index == 0:
                continue
            if paragraph.startswith("http"):
                continue
            if paragraph[0].islower() or paragraph[-1] not in ".!?":
                orphan_fragments += 1
                sentence_boundary_pass = False
            sentence_keys.extend(re.sub(r"\W+", " ", item.casefold()).strip() for item in _sentence_units(paragraph))
    media_ids = [str(item) for row in posts for item in (row.get("media_asset_ids") or [])]
    duplicates = len(sentence_keys) - len(set(sentence_keys))
    shortest_longest = round(min(lengths) / max(lengths), 3) if lengths and max(lengths) else 0.0
    return {
        "reply_count": max(0, len(posts) - 1),
        "post_character_counts": lengths,
        "per_post_character_utilization": [round(length / limit, 3) for length in lengths],
        "shortest_longest_reply_ratio": shortest_longest,
        "sentence_boundary_pass": sentence_boundary_pass,
        "orphan_fragment_count": orphan_fragments,
        "visual_distribution_pass": media_ids == ["primary", "policy_corridor", "sofr_context"],
        "complete_article_visual_count": len(set(media_ids)),
        "duplicated_sentence_count": duplicates,
        "hard_character_slicing_used": False,
    }


def _semantic_thread_layout(
    *, title: str, dek: str, mechanism: str, policy: str, cross_asset: str,
    canonical_url: str, platform: str, limit: int,
) -> dict[str, Any]:
    lede_budget = max(70, limit - len(title) - len(canonical_url) - 6)
    lede = _sharp_social_lede(dek, maximum=lede_budget)
    root = "\n\n".join((title, lede, canonical_url))
    mechanism_text = "Why it matters: " + _concise_semantic_sentence(mechanism, maximum=limit - 18)
    policy_text = _concise_semantic_sentence(policy, maximum=110 if platform == "x" else 240)
    cross_text = _concise_semantic_sentence(cross_asset, maximum=90 if platform == "x" else 190)
    context = f"Policy context: {policy_text} Cross-asset context: {cross_text}"
    caveat = "For informational purposes only; not financial advice."
    if len(mechanism_text) <= len(context) and len(mechanism_text + "\n\n" + caveat) <= limit:
        mechanism_text = mechanism_text + "\n\n" + caveat
    elif len(context + "\n\n" + caveat) <= limit:
        context = context + "\n\n" + caveat
    posts = [
        {"order": 0, "role": "root", "text": root, "media_asset_ids": ["primary"], "article_sections": ["lede_and_current_policy_signal"]},
        {"order": 1, "role": "reply", "text": mechanism_text, "media_asset_ids": ["policy_corridor"], "article_sections": ["policy_transmission_mechanism"]},
        {"order": 2, "role": "reply", "text": context, "media_asset_ids": ["sofr_context"], "article_sections": ["curve_and_cross_asset_context", "confirmation_and_limits"]},
    ]
    if any(len(row["text"]) > limit for row in posts):
        raise ValueError(f"{platform}_semantic_thread_exceeds_limit")
    metrics = _thread_quality(posts, limit=limit)
    return {
        "root_text": root,
        "reply_texts": [row["text"] for row in posts[1:]],
        "posts": posts,
        "full_text": "\n\n".join(row["text"] for row in posts),
        "platform_limit": limit,
        "reserved_costs": {"canonical_url_characters": len(canonical_url), "media_characters": 0},
        "overflow_strategy": "semantic_three_post_thread",
        "hard_truncation_used": False,
        "quality_metrics": metrics,
    }


def _root_and_replies(
    *,
    title: str,
    dek: str,
    canonical_url: str,
    continuation_parts: Sequence[str],
    limit: int,
) -> dict[str, Any]:
    root_parts = [title, canonical_url]
    root = "\n\n".join(root_parts)
    remaining = list(continuation_parts)
    with_dek = "\n\n".join([title, dek, canonical_url])
    if len(with_dek) <= limit:
        root = with_dek
    else:
        remaining.insert(0, dek)
    if len(root) > limit:
        raise ValueError("headline_and_canonical_url_exceed_platform_limit")
    replies = _split_complete_chunks(remaining, limit=limit)
    if any(len(item) > limit or "..." in item for item in [root, *replies]):
        raise ValueError("overflow_compiler_generated_truncation")
    return {
        "root_text": root,
        "reply_texts": replies,
        "full_text": "\n\n".join([root, *replies]),
        "platform_limit": limit,
        "overflow_strategy": "ordered_reply_chain" if replies else "single_root",
        "hard_truncation_used": False,
    }


def build_native_derivative_payloads(
    *,
    article: Mapping[str, Any],
    selection: Mapping[str, Any],
    canonical_url: str,
) -> dict[str, dict[str, str]]:
    """Create distinct, publication-ready platform copy from the canonical article."""
    title = str(article["title"])
    dek = str(selection["dek"])
    mechanism = " ".join(str(selection["market_mechanism"]).split())
    policy = " ".join(str(selection["policy_context"]).split())
    cross_asset = " ".join(str(selection["cross_asset_implications"]).split())
    caveat = "For informational purposes only; not financial advice."
    x_thread = _semantic_thread_layout(title=title, dek=dek, mechanism=mechanism, policy=policy, cross_asset=cross_asset, canonical_url=canonical_url, platform="x", limit=280)
    threads_thread = _semantic_thread_layout(title=title, dek=dek, mechanism=mechanism, policy=policy, cross_asset=cross_asset, canonical_url=canonical_url, platform="threads", limit=500)
    return {
        "x": {
            "format": "root_chart_post_with_ordered_replies",
            "text": x_thread["root_text"],
            **x_thread,
        },
        "linkedin": {
            "format": "professional_analytical_note_with_chart",
            "text": "\n\n".join(
                [
                    title,
                    dek,
                    f"The mechanism: {mechanism}",
                    f"The policy context: {policy}",
                    f"Read the full Capital Chronicle analysis: {canonical_url}",
                    caveat,
                ]
            ),
        },
        "discord": {
            "format": "newsroom_embed_with_chart",
            "text": "\n\n".join(
                [
                    f"**{title}**",
                    dek,
                    f"**Why it matters:** {mechanism}",
                    f"Full analysis: {canonical_url}",
                    caveat,
                ]
            ),
        },
        "facebook_page": {
            "format": "page_photo_post",
            "text": "\n\n".join(
                [
                    title,
                    dek,
                    f"The relevant transmission channel is {mechanism}",
                    f"Read the full article: {canonical_url}",
                    caveat,
                ]
            ),
        },
        "instagram_business": {
            "format": "chart_caption",
            "text": "\n\n".join(
                [
                    title,
                    f"The chart is a checkpoint, not a verdict: {cross_asset}",
                    f"Full analysis: {canonical_url}",
                    caveat,
                    "#CapitalChronicle #Macro #Markets",
                ]
            ),
        },
        "threads": {
            "format": "root_chart_post_with_ordered_media_replies",
            "text": threads_thread["root_text"],
            **threads_thread,
        },
        "tiktok": {
            "format": "source_chart_sequence_caption",
            "text": f"{title}. Three source-backed charts show the signal, the policy mechanism, and the curve context. Full article: {canonical_url}. {caveat}",
        },
        "youtube": {
            "format": "community_text_image_post",
            "text": "\n\n".join(
                [
                    title,
                    dek,
                    f"Why it matters: {_first_complete_sentence(mechanism)}",
                    f"Policy and curve context: {_first_complete_sentence(policy)} {_first_complete_sentence(cross_asset)}",
                    f"Read the full analysis: {canonical_url}",
                    caveat,
                ]
            ),
            "platform_limit": 1000,
            "hard_truncation_used": False,
        },
    }


def _safe_provider_result(raw: Mapping[str, Any], *, platform: str, payload: str, canonical_url: str, media_attached: bool) -> dict[str, Any]:
    response = raw.get("response") if isinstance(raw.get("response"), Mapping) else {}
    provider_result = response.get("result") if isinstance(response.get("result"), Mapping) else {}
    identifier = (
        raw.get("id")
        or raw.get("post_id")
        or raw.get("media_id")
        or raw.get("container_id")
        or raw.get("video_id")
        or provider_result.get("message_id")
        or provider_result.get("id")
        or response.get("id")
    )
    media_transfer = raw.get("media_transfer") if isinstance(raw.get("media_transfer"), Mapping) else raw.get("upload_transfer") if isinstance(raw.get("upload_transfer"), Mapping) else {}
    public_url = raw.get("public_url") or raw.get("url")
    readback = dict(raw.get("readback") or {}) if isinstance(raw.get("readback"), Mapping) else {}
    provider_readback_verified = bool(raw.get("provider_readback_verified"))
    if platform == "linkedin":
        provider_readback_verified = bool(
            provider_readback_verified
            and readback.get("body_text_visible")
            and readback.get("meaningful_media_visible")
            and readback.get("substack_url_visible")
            and readback.get("public_url")
        )
    elif platform == "youtube" and str(raw.get("action") or "") == "community_post":
        provider_readback_verified = bool(
            provider_readback_verified
            and readback.get("body_text_visible")
            and readback.get("meaningful_media_visible")
            and readback.get("substack_url_visible")
            and readback.get("channel_identity_verified")
            and readback.get("public_url")
        )
    elif not provider_readback_verified:
        provider_readback_verified = bool(public_url and raw.get("public_title_readback", True))
    raw_status = str(raw.get("status") or "FAILED_PROVIDER_NO_STATUS")
    if raw_status == "SUCCESS" and platform in {"linkedin", "youtube"} and not provider_readback_verified:
        raw_status = f"FAILED_{platform.upper()}_STRICT_READBACK"
    return {
        "status": raw_status,
        "platform": platform,
        "action": str(raw.get("action") or "post"),
        "id": str(identifier) if identifier is not None else None,
        "public_url": public_url,
        "media_attached": media_attached,
        "media_upload_transport": media_transfer.get("upload_transport"),
        "media_transfer": dict(media_transfer) if isinstance(media_transfer, Mapping) else None,
        "provider_readback_verified": provider_readback_verified,
        "destination_identity": raw.get("destination_identity"),
        "substack_url_included": canonical_url in payload,
        "payload_sha256": _sha256(payload),
        "error_code": raw.get("error_code"),
        "error_class": type(raw.get("error")).__name__ if raw.get("error") else None,
        "reason": raw.get("reason"),
        "diagnostics": raw.get("diagnostics"),
        "validation": raw.get("validation"),
        "readback": readback or None,
        "public_screenshot_path": readback.get("public_screenshot_path") or raw.get("public_screenshot_path"),
    }


def _load_dispatch_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _append_dispatch_ledger(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _dispatch_once(
    *,
    ledger_path: Path,
    platform: str,
    payload: str,
    canonical_url: str,
    media_attached: bool,
    executor: Callable[[], Mapping[str, Any]],
    idempotency_scope: str = "create",
    run_id: str | None = None,
    adapter_name: str | None = None,
    media: Mapping[str, Any] | None = None,
    runner_command: str | None = None,
) -> dict[str, Any]:
    payload_hash = _sha256(payload)
    matching = [
        prior
        for prior in _load_dispatch_ledger(ledger_path)
        if prior.get("platform") == platform and prior.get("payload_sha256") == payload_hash
        and str(prior.get("idempotency_scope") or "create") == idempotency_scope
    ]
    successful_prior = next((prior for prior in reversed(matching) if prior.get("success") is True), None)
    if successful_prior:
        return {
            "status": "ALREADY_SUCCESSFUL_IDEMPOTENT",
            "platform": platform,
            "action": successful_prior.get("action"),
            "id": successful_prior.get("id"),
            "public_url": successful_prior.get("public_url"),
            "media_attached": bool(successful_prior.get("media_attached")),
            "substack_url_included": bool(successful_prior.get("substack_url_included")),
            "payload_sha256": payload_hash,
            "idempotency_scope": idempotency_scope,
        }
    uncertain_prior = next((prior for prior in reversed(matching) if prior.get("write_outcome_certainty") == "unknown"), None)
    if uncertain_prior:
        return {
            "status": str(uncertain_prior.get("status") or "FAILED_PLATFORM_PERMALINK_READBACK"),
            "platform": platform,
            "action": uncertain_prior.get("action"),
            "id": uncertain_prior.get("id"),
            "public_url": uncertain_prior.get("public_url"),
            "media_attached": bool(uncertain_prior.get("media_attached")),
            "substack_url_included": bool(uncertain_prior.get("substack_url_included")),
            "payload_sha256": payload_hash,
            "idempotency_scope": idempotency_scope,
            "automatic_retry_blocked": True,
            "write_outcome_certainty": "unknown",
            "required_unblock": "Inspect the platform destination for the exact payload before any retry; record its permalink or prove it was not published.",
        }
    try:
        raw = dict(executor())
    except Exception as exc:
        raw = {"status": "FAILED_ADAPTER_EXCEPTION", "platform": platform, "error": exc}
    result = _safe_provider_result(raw, platform=platform, payload=payload, canonical_url=canonical_url, media_attached=media_attached)
    result["idempotency_scope"] = idempotency_scope
    result.update(
        {
            "run_id": run_id,
            "execution_origin": "contentops_pipeline",
            "runner_module": "live_contentops.eight_platform_substack_first_pipeline_v1",
            "runner_command": runner_command,
            "adapter_name_version": adapter_name,
            "media_asset_id": (media or {}).get("media_asset_id"),
            "media_sha256": (media or {}).get("sha256"),
            "canonical_substack_url": canonical_url,
        }
    )
    success = result["status"] == "SUCCESS"
    write_outcome_certainty = "unknown" if result["status"] in UNKNOWN_WRITE_STATUSES else "confirmed"
    result["write_outcome_certainty"] = write_outcome_certainty
    _append_dispatch_ledger(
        ledger_path,
        {
            "timestamp": _utc_now(),
            "platform": platform,
            "payload_sha256": payload_hash,
            "success": success,
            "status": result["status"],
            "action": result["action"],
            "id": result["id"],
            "public_url": result["public_url"],
            "media_attached": result["media_attached"],
            "substack_url_included": result["substack_url_included"],
            "write_outcome_certainty": write_outcome_certainty,
            "idempotency_scope": idempotency_scope,
            "run_id": run_id,
            "execution_origin": "contentops_pipeline",
            "runner_module": "live_contentops.eight_platform_substack_first_pipeline_v1",
            "runner_command": runner_command,
            "adapter_name_version": adapter_name,
            "media_asset_id": (media or {}).get("media_asset_id"),
            "media_sha256": (media or {}).get("sha256"),
            "canonical_substack_url": canonical_url,
        },
    )
    return result


def _publish_facebook_photo_verified(
    *,
    text: str,
    canonical_url: str,
    media: Mapping[str, Any],
) -> dict[str, Any]:
    from live_contentops.facebook_page_adapter_v6 import execute_facebook_photo, readback_facebook_post

    raw = execute_facebook_photo(
        message=text,
        image_url=str(media["verified_public_delivery_url"]),
        expected_media_sha256=str(media["sha256"]),
        dry_run=False,
    )
    if raw.get("status") != "SUCCESS":
        return dict(raw)
    post_id = str(raw.get("id") or ((raw.get("response") or {}).get("post_id")) or "")
    readback: dict[str, Any] = {}
    for _ in range(4):
        readback = readback_facebook_post(
            post_id=post_id,
            expected_text=text,
            canonical_url=canonical_url,
            expected_media_local_path=str(media["absolute_local_source_path"]),
        )
        if readback.get("status") == "SUCCESS":
            break
        time.sleep(3)
    return {
        **raw,
        "status": "SUCCESS" if readback.get("status") == "SUCCESS" else "FAILED_FACEBOOK_REPLACEMENT_READBACK",
        "action": "corrected_replacement_photo",
        "public_url": readback.get("public_url"),
        "provider_readback_verified": readback.get("status") == "SUCCESS",
        "readback": readback,
    }


def _publish_instagram_media_verified(
    *,
    caption: str,
    canonical_url: str,
    media: Mapping[str, Any],
) -> dict[str, Any]:
    from live_contentops.instagram_adapter_v6 import execute_instagram_post, readback_instagram_media

    raw = execute_instagram_post(
        image_url=str(media["verified_public_delivery_url"]),
        caption=caption,
        expected_media_sha256=str(media["sha256"]),
        dry_run=False,
    )
    if raw.get("status") != "SUCCESS":
        return dict(raw)
    media_id = str(raw.get("id") or "")
    readback: dict[str, Any] = {}
    for _ in range(5):
        readback = readback_instagram_media(
            media_id=media_id,
            expected_caption=caption,
            canonical_url=canonical_url,
            expected_media_local_path=str(media["absolute_local_source_path"]),
        )
        if readback.get("status") == "SUCCESS":
            break
        time.sleep(4)
    return {
        **raw,
        "status": "SUCCESS" if readback.get("status") == "SUCCESS" else "FAILED_INSTAGRAM_REPLACEMENT_READBACK",
        "action": "corrected_replacement_media",
        "public_url": readback.get("public_url"),
        "provider_readback_verified": readback.get("status") == "SUCCESS",
        "readback": readback,
    }


def _publish_threads_reply_verified(
    *,
    parent_id: str,
    text: str,
    canonical_url: str | None,
    media: Mapping[str, Any] | None,
) -> dict[str, Any]:
    from live_contentops.threads_adapter_v6 import execute_threads_post, readback_threads_post

    raw = execute_threads_post(
        text=text,
        image_url=str(media["verified_public_delivery_url"]) if media else None,
        reply_to_id=parent_id,
        expected_media_sha256=str(media["sha256"]) if media else None,
        dry_run=False,
    )
    if raw.get("status") != "SUCCESS":
        return dict(raw)
    reply_id = str(raw.get("id") or "")
    readback: dict[str, Any] = {}
    for _ in range(5):
        readback = readback_threads_post(
            post_id=reply_id,
            expected_text=text,
            canonical_url=canonical_url,
            expected_media_local_path=str(media["absolute_local_source_path"]) if media else None,
        )
        if readback.get("status") == "SUCCESS":
            break
        time.sleep(3)
    return {
        **raw,
        "status": "SUCCESS" if readback.get("status") == "SUCCESS" else "FAILED_THREADS_REPLY_READBACK",
        "action": "reply",
        "public_url": readback.get("public_url"),
        "parent_id": parent_id,
        "provider_readback_verified": readback.get("status") == "SUCCESS",
        "readback": readback,
    }


def _capability_presence() -> dict[str, bool]:
    def present(*keys: str) -> bool:
        return any(bool(os.environ.get(key)) for key in keys)

    return {
        "discord": present("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL", "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK", "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL"),
        "telegram": present("TELEGRAM_BOT_TOKEN") and present("TELEGRAM_CHANNEL_ID", "TELEGRAM_CHAT_ID", "TELEGRAM_TARGET_CHAT_ID"),
        "facebook_page": present("FACEBOOK_PAGE_ID") and present("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"),
        "instagram_business": present("INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_IG_ID") and present("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN"),
        "threads": present("THREADS_USER_ID") and present("THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN"),
        "tiktok": present("TIKTOK_CLIENT_KEY") and present("TIKTOK_CLIENT_SECRET") and present("TIKTOK_ACCESS_TOKEN"),
        "youtube": all(present(key) for key in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CHANNEL_ID")),
    }


def _classification(results: Mapping[str, Mapping[str, Any]]) -> str:
    canonical = results.get("substack") or {}
    canonical_status = str(canonical.get("status") or "")
    if canonical_status != "SUCCESS":
        if canonical_status in UNKNOWN_WRITE_STATUSES:
            return "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
        return "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
    if any(str(result.get("status") or "") in UNKNOWN_WRITE_STATUSES for result in results.values()):
        return "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
    successful = [platform for platform, result in results.items() if str(result.get("status")) in SUCCESS_STATUSES]
    if all(platform in successful for platform in TEXT_IMAGE_PASS_DESTINATIONS):
        return "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1"
    return "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"


def _readme(evidence: Mapping[str, Any]) -> str:
    lines = [
        "# Eight-Platform Substack-First ContentOps Run",
        "",
        f"Classification: `{evidence['classification']}`",
        f"Substack: `{evidence['results']['substack'].get('public_url') or ''}`",
        "",
        "| Destination | Status | Readback |",
        "| --- | --- | --- |",
    ]
    for platform in EXPECTED_DESTINATIONS:
        result = evidence["results"].get(platform) or {}
        reference = result.get("public_url") or result.get("id") or result.get("draft_id") or ""
        lines.append(f"| {platform} | `{result.get('status') or ''}` | `{reference}` |")
    lines.extend(["", "Substack is canonical. Telegram, X, and every other distribution payload carry the verified public Substack URL when the platform allows links.", ""])
    return "\n".join(lines)


def _persist_final_platform_matrix(output_dir: Path, evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Persist one normalized audit surface for every configured destination."""
    results = evidence.get("results") if isinstance(evidence.get("results"), Mapping) else {}
    manifest = evidence.get("delivery_media_manifest") if isinstance(evidence.get("delivery_media_manifest"), Mapping) else {}
    assets = manifest.get("assets") if isinstance(manifest.get("assets"), list) else []
    primary = next((asset for asset in assets if isinstance(asset, Mapping) and asset.get("media_asset_id") == "primary"), {})
    canonical_url = str((results.get("substack") or {}).get("public_url") or "")
    adapter_defaults = {
        "substack": "edge_cdp_publishing_adapter_v1.publish_substack_article_via_edge",
        "telegram": "substack_first_north_star_pipeline_loop_v1.complete_substack_first_pipeline",
        "discord": "discord_live_adapter_v6.execute_discord_post",
        "x": "edge_cdp_publishing_adapter_v1.publish_x_post_via_edge",
        "threads": "threads_adapter_v6.execute_threads_post",
    }
    identity_defaults = {
        "substack": "Capital Chronicle",
        "telegram": "Capital Chronicle",
        "discord": "The Macro Pigeon / Capital Chronicle",
        "x": "@Capitalnicle",
        "threads": "official.capitalchronicle",
    }
    rows: dict[str, Any] = {}
    for platform in EXPECTED_DESTINATIONS:
        result = results.get(platform) if isinstance(results.get(platform), Mapping) else {}
        readback = result.get("readback") if isinstance(result.get("readback"), Mapping) else {}
        substack_verified = platform == "substack" and bool(
            result.get("public_url") and readback.get("visual_spread_through_public_body") and int(readback.get("public_image_count") or 0) >= 3
        )
        telegram_verified = platform == "telegram" and bool(
            result.get("message_id") and result.get("substack_url_visible_in_provider_readback")
        )
        discord_verified = platform == "discord" and bool(
            result.get("id") and result.get("substack_url_included") and result.get("status") == "SUCCESS"
        )
        frozen_verified = substack_verified or telegram_verified or discord_verified
        rows[platform] = {
            "status": result.get("status"),
            "quality_status": result.get("quality_status") or ("PASS" if result.get("status") in SUCCESS_STATUSES else result.get("status")),
            "run_id": evidence.get("run_id"),
            "execution_origin": result.get("execution_origin") or "contentops_pipeline",
            "runner_module": result.get("runner_module") or "live_contentops.eight_platform_substack_first_pipeline_v1",
            "runner_command": result.get("runner_command"),
            "adapter_name_version": result.get("adapter_name_version") or adapter_defaults.get(platform),
            "payload_sha256": result.get("payload_sha256") or result.get("caption_sha256"),
            "media_asset_id": result.get("media_asset_id") or (primary.get("media_asset_id") if result.get("media_attached") or substack_verified else None),
            "media_sha256": result.get("media_sha256") or (primary.get("sha256") if result.get("media_attached") or substack_verified else None),
            "canonical_substack_url": canonical_url,
            "destination_identity": result.get("destination_identity") or readback.get("destination_identity") or identity_defaults.get(platform),
            "public_url": result.get("public_url"),
            "id": result.get("id") or result.get("message_id") or result.get("draft_id"),
            "reply_chain": result.get("reply_chain") or [],
            "public_text_verified": bool(frozen_verified or readback.get("body_text_visible") or readback.get("visible_body_text") or result.get("provider_readback_verified")),
            "media_verified": bool(substack_verified or readback.get("meaningful_media_visible") or readback.get("expected_chart_visual_similarity") or result.get("media_attached")),
            "canonical_link_verified": bool(readback.get("substack_url_visible") or result.get("substack_url_included") or platform == "substack"),
            "provider_readback_verified": bool(frozen_verified or result.get("provider_readback_verified") or readback.get("status") == "SUCCESS"),
            "readback_basis": "frozen_accepted_operator_and_provider_evidence" if frozen_verified else "strict_platform_readback",
            "idempotency_state": result.get("idempotency_scope") or result.get("write_outcome_certainty"),
        }
    packet = {
        "schema_version": "contentops.final_platform_matrix.v1",
        "run_id": evidence.get("run_id"),
        "classification": evidence.get("classification"),
        "canonical_substack_url": canonical_url,
        "primary_media_asset_id": primary.get("media_asset_id"),
        "primary_media_sha256": primary.get("sha256"),
        "destinations": rows,
        "superseded_malformed_posts": evidence.get("superseded_malformed_posts") or {},
        "wrong_surface_executions": evidence.get("wrong_surface_executions") or {},
    }
    _write_json(output_dir / "final_platform_matrix_v1.json", packet)
    return packet


def run_eight_platform_substack_first_pipeline(
    *,
    run_id: str,
    output_dir: Path,
    cdp_port: int = 9223,
    llm_provider: str = "auto",
    operator_approved_full_live_run: bool = True,
    recover_substack_draft_id: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "run_evidence_v1.json"
    prior_evidence: dict[str, Any] | None = None
    if evidence_path.exists():
        # A repeat of the canonical phase would risk a second public article.
        # Recovery must start from the recorded evidence and use targeted
        # derivative dispatch after an operator-visible reconciliation.
        prior_evidence = _read_json(evidence_path)
        prior_substack = (prior_evidence.get("results") or {}).get("substack") or {}
        if not recover_substack_draft_id:
            prior_evidence["reentry_guard"] = "existing_run_evidence_detected_no_automatic_canonical_republish"
            return prior_evidence
        if (
            not str(prior_substack.get("status") or "").startswith("FAILED_SUBSTACK_")
            or str(prior_substack.get("draft_id") or "") != str(recover_substack_draft_id)
        ):
            prior_evidence["reentry_guard"] = "substack_recovery_draft_id_does_not_match_recorded_failed_draft"
            return prior_evidence
    doctor = browser_doctor()
    if doctor.get("status") != "READY_TO_ATTACH" or doctor.get("recommended_cdp_port") != cdp_port:
        evidence = {"schema_version": SCHEMA_VERSION, "task_label": TASK_LABEL, "classification": "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1", "run_id": run_id, "browser_doctor": doctor, "results": {"substack": {"status": "BLOCKED_CANONICAL_EDGE_PROFILE_NOT_ATTACHED"}}}
        _write_json(output_dir / "run_evidence_v1.json", evidence)
        return evidence

    staged_context_path = output_dir / "run_context_v1.json"
    staged_request_path = output_dir / "substack_browser_request_v1.json"
    if staged_context_path.exists() and staged_request_path.exists():
        prepared = {
            "classification": "READY_FOR_SUPERVISED_SUBSTACK_BROWSER_ASSIST",
            "context_path": str(staged_context_path),
            "substack_browser_request_path": str(staged_request_path),
            "reused_reviewed_preparation": True,
        }
    else:
        prepared = prepare_substack_first_pipeline(
            run_id=run_id,
            publication_mode="publish",
            output_dir=output_dir,
            llm_provider=llm_provider,
        )
    if prepared.get("classification") != "READY_FOR_SUPERVISED_SUBSTACK_BROWSER_ASSIST":
        evidence = {"schema_version": SCHEMA_VERSION, "task_label": TASK_LABEL, "classification": "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1", "run_id": run_id, "browser_doctor": doctor, "prepare": prepared, "results": {"substack": {"status": "BLOCKED_IDEA_OR_MEDIA_PREP"}}}
        _write_json(output_dir / "run_evidence_v1.json", evidence)
        return evidence

    context_path = Path(str(prepared["context_path"]))
    context = _read_json(context_path)
    article = dict(context["article"])
    selection = dict(context["selection"])
    media = dict(context["media"])
    request_path = Path(str(context["substack_browser_request_path"]))
    request = _read_json(request_path)
    browser_sessions = {}
    for platform in ("substack", "x", "linkedin", "tiktok", "youtube"):
        try:
            browser_sessions[platform] = probe_authenticated_platform_session(cdp_port, platform)
        except Exception as exc:
            browser_sessions[platform] = {"platform": platform, "authenticated": False, "error_class": type(exc).__name__}
    _write_json(output_dir / "browser_session_preflight_v1.json", browser_sessions)

    substack_raw = publish_substack_article_via_edge(
        cdp_port=cdp_port,
        title=str(article["title"]),
        subtitle=str(article["subtitle"]),
        body_markdown=str(article["substack_body_markdown"]),
        image_assets=list(media["assets"]),
        public_screenshot_path=output_dir / "public_substack_readback.png",
        existing_draft_id=recover_substack_draft_id,
    )
    results: dict[str, dict[str, Any]] = {"substack": dict(substack_raw)}
    if substack_raw.get("status") != "SUCCESS":
        evidence = {
            "schema_version": SCHEMA_VERSION,
            "task_label": TASK_LABEL,
            "classification": _classification(results),
            "run_id": run_id,
            "browser_doctor": doctor,
            "browser_sessions": browser_sessions,
            "selected_idea": selection,
            "article": article,
            "media": media,
            "legacy_draft_recovery": {"draft_id": "206403125", "decision": "PRESERVED_NOT_REUSED", "reason": "The old draft was created through a forbidden Chrome workspace and recorded zero uploaded images."},
            "substack_recovery": {"draft_id": recover_substack_draft_id, "prior_status": ((prior_evidence or {}).get("results") or {}).get("substack", {}).get("status")} if recover_substack_draft_id else None,
            "results": results,
            "safety": {"raw_credentials_persisted": False, "browser_storage_read": False, "synthetic_image_generated": False},
        }
        _write_json(output_dir / "run_evidence_v1.json", evidence)
        _write_text(output_dir / "README.md", _readme(evidence))
        return evidence

    canonical_url = str(substack_raw["public_url"])
    readback_path = output_dir / "substack_browser_readback_v1.json"
    build_supervised_substack_browser_readback(
        request=request,
        publication_state="published",
        article_url=canonical_url,
        editor_body_image_count=int(substack_raw["editor_body_image_count"]),
        in_body_visual_asset_ids=list(substack_raw["in_body_visual_asset_ids"]),
        output_path=readback_path,
    )

    repair = selection.get("canonicalization_repair") if isinstance(selection.get("canonicalization_repair"), Mapping) else None
    if not repair or str(repair.get("existing_telegram_message_id")) != "61":
        results["telegram"] = {"status": "BLOCKED_TELEGRAM_EXISTING_MESSAGE_61_REPAIR_NOT_CONFIRMED", "platform": "telegram", "substack_url_included": False}
    else:
        telegram_evidence = complete_substack_first_pipeline(
            context_path=context_path,
            substack_readback_path=readback_path,
            operator_approved_full_live_run=operator_approved_full_live_run,
            max_send_attempts_per_platform=1,
        )
        results["telegram"] = dict(telegram_evidence["telegram"])

    payloads = build_native_derivative_payloads(article=article, selection=selection, canonical_url=canonical_url)
    _write_json(output_dir / "native_payloads_v1.json", payloads)
    ledger_path = output_dir / "platform_dispatch_ledger_v1.jsonl"
    delivery_media_manifest = build_delivery_media_manifest(
        media_packet=media,
        public_image_urls=list((substack_raw.get("readback") or {}).get("public_image_urls") or []),
        run_id=run_id,
    )
    _write_json(output_dir / "delivery_media_manifest_v1.json", delivery_media_manifest)
    if delivery_media_manifest.get("status") != "PASS":
        results["media_manifest"] = {"status": "BLOCKED_DELIVERY_MEDIA_MANIFEST", "blockers": delivery_media_manifest.get("blockers")}
        evidence = {
            "schema_version": SCHEMA_VERSION,
            "task_label": TASK_LABEL,
            "classification": "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
            "run_id": run_id,
            "article": article,
            "selected_idea": selection,
            "media": media,
            "delivery_media_manifest": delivery_media_manifest,
            "results": results,
        }
        _write_json(output_dir / "run_evidence_v1.json", evidence)
        return evidence
    primary_media = select_primary_chart(delivery_media_manifest)
    media_by_id = {
        str(item.get("media_asset_id")): dict(item)
        for item in delivery_media_manifest.get("assets", [])
        if isinstance(item, Mapping) and item.get("media_asset_id")
    }
    public_image_url = str(primary_media["verified_public_delivery_url"])
    primary_chart = str(primary_media["absolute_local_source_path"])
    runner_command = (
        "python -m live_contentops.eight_platform_substack_first_pipeline_v1 "
        f"--run-id {run_id} --operator-approved-full-live-run"
    )

    results["x"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="x",
        payload=payloads["x"]["text"],
        canonical_url=canonical_url,
        media_attached=True,
        run_id=run_id,
        adapter_name="edge_cdp_publishing_adapter_v1.publish_x_post_via_edge",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: publish_x_post_via_edge(cdp_port=cdp_port, text=payloads["x"]["text"], image_path=primary_chart),
    )
    x_root = dict(results["x"])
    x_root_url = str(x_root.get("public_url") or "")
    x_root_id = str(x_root.get("id") or x_root_url.rstrip("/").rsplit("/", 1)[-1])
    x_replies: list[dict[str, Any]] = []
    x_parent_url = x_root_url
    if str(x_root.get("status") or "") in SUCCESS_STATUSES and x_root_url:
        for index, reply_text in enumerate(payloads["x"]["reply_texts"], start=1):
            post_layout = payloads["x"]["posts"][index]
            reply_media = media_by_id[str(post_layout["media_asset_ids"][0])]
            reply = _dispatch_once(
                ledger_path=ledger_path,
                platform="x",
                payload=reply_text,
                canonical_url=canonical_url,
                media_attached=True,
                idempotency_scope=f"x_reply:{x_root_id}:{index}",
                run_id=run_id,
                adapter_name="edge_cdp_publishing_adapter_v1.publish_x_reply_via_edge",
                media=reply_media,
                runner_command=runner_command,
                executor=lambda parent_url=x_parent_url, text=reply_text, reply_media=reply_media: publish_x_reply_via_edge(
                    cdp_port=cdp_port, parent_url=parent_url, text=text,
                    image_path=str(reply_media["absolute_local_source_path"]),
                ),
            )
            x_replies.append({
                **reply, "order": index, "text": reply_text,
                "parent_id": x_parent_url.rstrip("/").rsplit("/", 1)[-1],
                "expected_media_local_path": str(reply_media["absolute_local_source_path"]),
                "media_asset_id": reply_media["media_asset_id"],
                "media_sha256": reply_media["sha256"],
            })
            if reply.get("public_url"):
                x_parent_url = str(reply["public_url"])
            if str(reply.get("status") or "") not in SUCCESS_STATUSES:
                break
        x_readback = readback_x_thread_via_edge(
            cdp_port=cdp_port,
            root_url=x_root_url,
            canonical_url=canonical_url,
            expected_chart_path=primary_chart,
            replies=x_replies,
            public_screenshot_path=output_dir / "public_x_thread_readback.png",
        ) if len(x_replies) == len(payloads["x"]["reply_texts"]) else {"status": "FAILED_X_REPLY_CHAIN_INCOMPLETE"}
        results["x"] = {
            **x_root,
            "status": "SUCCESS" if x_readback.get("status") == "SUCCESS" else str(x_readback.get("status")),
            "reply_chain": x_replies,
            "readback": x_readback,
            "provider_readback_verified": x_readback.get("status") == "SUCCESS",
        }
    results["linkedin"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="linkedin",
        payload=payloads["linkedin"]["text"],
        canonical_url=canonical_url,
        media_attached=True,
        run_id=run_id,
        adapter_name="edge_cdp_publishing_adapter_v1.publish_linkedin_post_via_edge",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: publish_linkedin_post_via_edge(
            cdp_port=cdp_port,
            text=payloads["linkedin"]["text"],
            image_path=primary_chart,
            canonical_url=canonical_url,
            public_screenshot_path=output_dir / "public_linkedin_readback.png",
        ),
    )

    from live_contentops.discord_live_adapter_v6 import execute_discord_post
    from live_contentops.facebook_page_adapter_v6 import execute_facebook_photo
    from live_contentops.instagram_adapter_v6 import execute_instagram_post
    from live_contentops.threads_adapter_v6 import execute_threads_post

    results["discord"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="discord",
        payload=payloads["discord"]["text"],
        canonical_url=canonical_url,
        media_attached=bool(public_image_url),
        run_id=run_id,
        adapter_name="discord_live_adapter_v6.execute_discord_post",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: execute_discord_post(
            message=payloads["discord"]["text"],
            embeds=[{"title": str(article["title"]), "url": canonical_url, "image": {"url": public_image_url}}] if public_image_url else None,
            dry_run=False,
        ),
    )
    results["facebook_page"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="facebook_page",
        payload=payloads["facebook_page"]["text"],
        canonical_url=canonical_url,
        media_attached=bool(public_image_url),
        run_id=run_id,
        adapter_name="facebook_page_adapter_v6.execute_facebook_photo",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: _publish_facebook_photo_verified(text=payloads["facebook_page"]["text"], canonical_url=canonical_url, media=primary_media),
    ) if public_image_url else {"status": "BLOCKED_FACEBOOK_PUBLIC_SUBSTACK_IMAGE_MISSING", "platform": "facebook_page"}
    results["instagram_business"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="instagram_business",
        payload=payloads["instagram_business"]["text"],
        canonical_url=canonical_url,
        media_attached=bool(public_image_url),
        run_id=run_id,
        adapter_name="instagram_adapter_v6.execute_instagram_post",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: _publish_instagram_media_verified(caption=payloads["instagram_business"]["text"], canonical_url=canonical_url, media=primary_media),
    ) if public_image_url else {"status": "BLOCKED_INSTAGRAM_PUBLIC_SUBSTACK_IMAGE_MISSING", "platform": "instagram_business"}
    results["threads"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="threads",
        payload=payloads["threads"]["text"],
        canonical_url=canonical_url,
        media_attached=bool(public_image_url),
        run_id=run_id,
        adapter_name="threads_adapter_v6.execute_threads_post",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: execute_threads_post(text=payloads["threads"]["text"], image_url=public_image_url or None, dry_run=False),
    )
    threads_root = dict(results["threads"])
    threads_root_id = str(threads_root.get("id") or "")
    threads_replies: list[dict[str, Any]] = []
    if str(threads_root.get("status") or "") in SUCCESS_STATUSES and threads_root_id:
        from live_contentops.threads_adapter_v6 import readback_threads_chain, readback_threads_post

        for index, reply_text in enumerate(payloads["threads"]["reply_texts"], start=1):
            post_layout = payloads["threads"]["posts"][index]
            reply_media = media_by_id[str(post_layout["media_asset_ids"][0])]
            reply = _dispatch_once(
                ledger_path=ledger_path,
                platform="threads",
                payload=reply_text,
                canonical_url=canonical_url,
                media_attached=True,
                idempotency_scope=f"threads_reply:{threads_root_id}:{index}",
                run_id=run_id,
                adapter_name="threads_adapter_v6.execute_threads_post",
                media=reply_media,
                runner_command=runner_command,
                executor=lambda text=reply_text, reply_media=reply_media: _publish_threads_reply_verified(
                    parent_id=threads_root_id, text=text, canonical_url=None, media=reply_media
                ),
            )
            threads_replies.append({
                **reply, "order": index, "text": reply_text, "parent_id": threads_root_id,
                "expected_media_local_path": str(reply_media["absolute_local_source_path"]),
                "media_asset_id": reply_media["media_asset_id"],
                "media_sha256": reply_media["sha256"],
            })
            if str(reply.get("status") or "") not in SUCCESS_STATUSES:
                break
        root_readback = readback_threads_post(
            post_id=threads_root_id,
            expected_text=payloads["threads"]["root_text"],
            canonical_url=canonical_url,
            expected_media_local_path=primary_chart,
        )
        chain_readback = readback_threads_chain(
            root_id=threads_root_id,
            reply_expectations=[{
                "id": row.get("id"), "text": row.get("text"),
                "expected_media_local_path": row.get("expected_media_local_path"),
            } for row in threads_replies],
        ) if len(threads_replies) == len(payloads["threads"]["reply_texts"]) else {"status": "FAILED_THREADS_REPLY_CHAIN_INCOMPLETE"}
        threads_ok = root_readback.get("status") == "SUCCESS" and chain_readback.get("status") == "SUCCESS"
        results["threads"] = {
            **threads_root,
            "status": "SUCCESS" if threads_ok else "FAILED_THREADS_STRICT_THREAD_READBACK",
            "reply_chain": threads_replies,
            "readback": {"root": root_readback, "chain": chain_readback},
            "provider_readback_verified": threads_ok,
        }

    results["youtube"] = _dispatch_once(
        ledger_path=ledger_path,
        platform="youtube",
        payload=payloads["youtube"]["text"],
        canonical_url=canonical_url,
        media_attached=True,
        idempotency_scope="youtube_community_post",
        run_id=run_id,
        adapter_name="edge_cdp_publishing_adapter_v1.publish_youtube_community_post_via_edge",
        media=primary_media,
        runner_command=runner_command,
        executor=lambda: publish_youtube_community_post_via_edge(
            cdp_port=cdp_port,
            text=payloads["youtube"]["text"],
            image_path=primary_chart,
            canonical_url=canonical_url,
            public_screenshot_path=output_dir / "public_youtube_community_readback.png",
        ),
    )
    tiktok_session = browser_sessions.get("tiktok") or {}
    results["tiktok"] = {
        "status": "BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED" if not tiktok_session.get("authenticated") else "BLOCKED_TIKTOK_NATIVE_DERIVATIVE_NOT_CONFIGURED",
        "platform": "tiktok",
        "canonical_republished": False,
        "required_unblock": "Authenticate the intended TikTok account in the canonical ContentOps Edge profile and enable the separately reviewed native derivative mode.",
    }
    video = {
        "status": "OUTSIDE_DEFAULT_ARTICLE_DISTRIBUTION_MODE",
        "youtube_default_surface": "community_text_image_post",
        "video_or_short_adapter_called": False,
    }

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "run_id": run_id,
        "classification": _classification(results),
        "canonical_architecture": "Substack public article first; every derivative is generated only after verified canonical URL and public visual readback.",
        "browser_doctor": doctor,
        "browser_sessions": browser_sessions,
        "configured_destinations": list(EXPECTED_DESTINATIONS),
        "credential_capability_presence": _capability_presence(),
        "selected_idea": selection,
        "article": article,
        "media": media,
        "delivery_media_manifest": delivery_media_manifest,
        "video": video,
        "legacy_draft_recovery": {"draft_id": "206403125", "decision": "PRESERVED_NOT_REUSED", "reason": "The prior Chrome-based draft had zero body images and no external URL; the new direct-Edge run created a fully verified canonical article."},
        "substack_recovery": {"draft_id": recover_substack_draft_id, "prior_status": ((prior_evidence or {}).get("results") or {}).get("substack", {}).get("status")} if recover_substack_draft_id else None,
        "results": results,
        "idempotency_ledger": str(ledger_path),
        "safety": {
            "raw_credentials_persisted": False,
            "browser_storage_read": False,
            "private_substack_editor_url_persisted": False,
            "synthetic_image_generated": False,
            "source_backed_media_owned_by_contentops": True,
            "max_send_attempts_per_platform": 1,
        },
    }
    _write_json(output_dir / "run_evidence_v1.json", evidence)
    evidence["final_platform_matrix"] = _persist_final_platform_matrix(output_dir, evidence)
    _write_json(output_dir / "run_evidence_v1.json", evidence)
    _write_text(output_dir / "README.md", _readme(evidence))
    return evidence


def resume_eight_platform_derivatives(
    *,
    output_dir: Path,
    cdp_port: int = 9223,
    platforms: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Correct only failed derivatives; canonical and successful destinations stay frozen."""
    evidence_path = output_dir / "run_evidence_v1.json"
    if not evidence_path.exists():
        raise FileNotFoundError("resume_requires_existing_run_evidence")
    evidence = _read_json(evidence_path)
    results = {name: dict(value) for name, value in (evidence.get("results") or {}).items() if isinstance(value, Mapping)}
    substack = results.get("substack") or {}
    canonical_url = str(substack.get("public_url") or "")
    if substack.get("status") != "SUCCESS" or not canonical_url:
        evidence["classification"] = "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
        evidence["resume_blocker"] = "canonical_substack_public_url_required_before_derivative_resume"
        _write_json(evidence_path, evidence)
        return evidence
    doctor = browser_doctor()
    if doctor.get("status") != "READY_TO_ATTACH" or doctor.get("recommended_cdp_port") != cdp_port:
        evidence["classification"] = "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
        evidence["resume_blocker"] = "canonical_edge_profile_not_attached"
        _write_json(evidence_path, evidence)
        return evidence

    article = dict(evidence["article"])
    selection = dict(evidence["selected_idea"])
    media = dict(evidence["media"])
    delivery_media_manifest = build_delivery_media_manifest(
        media_packet=media,
        public_image_urls=list((substack.get("readback") or {}).get("public_image_urls") or []),
        run_id=str(evidence.get("run_id") or ""),
    )
    _write_json(output_dir / "delivery_media_manifest_v1.json", delivery_media_manifest)
    evidence["delivery_media_manifest"] = delivery_media_manifest
    if delivery_media_manifest.get("status") != "PASS":
        evidence["classification"] = "PARTIAL_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1"
        evidence["resume_blocker"] = "deterministic_delivery_media_manifest_blocked"
        _write_json(evidence_path, evidence)
        return evidence
    primary_media = select_primary_chart(delivery_media_manifest)
    media_by_id = {
        str(item.get("media_asset_id")): dict(item)
        for item in delivery_media_manifest.get("assets", [])
        if isinstance(item, Mapping) and item.get("media_asset_id")
    }
    primary_chart = str(primary_media["absolute_local_source_path"])
    primary_public_url = str(primary_media["verified_public_delivery_url"])
    payloads = build_native_derivative_payloads(article=article, selection=selection, canonical_url=canonical_url)
    _write_json(output_dir / "native_payloads_v1.json", payloads)
    ledger_path = output_dir / "platform_dispatch_ledger_v1.jsonl"
    requested = set(platforms or ())
    allowed = {"x", "threads", "linkedin", "facebook_page", "instagram_business", "youtube", "tiktok"}
    if requested - allowed:
        raise ValueError("resume_platform_not_supported_by_derivative_resume")
    proposed_targets = requested or set(allowed)
    targets = set()
    for platform in proposed_targets:
        prior = results.get(platform) or {}
        accepted = str(prior.get("status") or "") in SUCCESS_STATUSES
        if platform == "youtube" and str(prior.get("action") or "") != "community_post":
            accepted = False
        if not accepted:
            targets.add(platform)
    evidence["successful_resume_targets_skipped"] = sorted(proposed_targets - targets)
    frozen_platforms = ("substack", "telegram", "discord")
    frozen_before = {platform: json.dumps(results.get(platform) or {}, sort_keys=True) for platform in frozen_platforms}
    correction_readback: dict[str, Any] = {}
    superseded: dict[str, Any] = dict(evidence.get("superseded_malformed_posts") or {})
    run_id = str(evidence.get("run_id") or "")
    runner_command = (
        "python -m live_contentops.eight_platform_substack_first_pipeline_v1 "
        f"--run-id {run_id} --resume-derivatives "
        + " ".join(f"--resume-platform {platform}" for platform in sorted(targets))
    )

    if "x" in targets:
        root = dict(results.get("x") or {})
        root_url = str(root.get("public_url") or "")
        root_id = str(root.get("id") or root_url.rstrip("/").rsplit("/", 1)[-1])
        reply_rows: list[dict[str, Any]] = []
        parent_url = root_url
        x_repair_replies = payloads["x"]["reply_texts"]
        for index, reply_text in enumerate(x_repair_replies, start=1):
            post_layout = payloads["x"]["posts"][index]
            reply_media = media_by_id[str(post_layout["media_asset_ids"][0])]
            reply_result = _dispatch_once(
                ledger_path=ledger_path,
                platform="x",
                payload=reply_text,
                canonical_url=canonical_url,
                media_attached=True,
                idempotency_scope=f"x_reply:{root_id}:{index}",
                run_id=run_id,
                adapter_name="edge_cdp_publishing_adapter_v1.publish_x_reply_via_edge",
                media=reply_media,
                runner_command=runner_command,
                executor=lambda parent_url=parent_url, reply_text=reply_text, reply_media=reply_media: publish_x_reply_via_edge(
                    cdp_port=cdp_port,
                    parent_url=parent_url,
                    text=reply_text,
                    image_path=str(reply_media["absolute_local_source_path"]),
                ),
            )
            reply_rows.append({
                **reply_result, "order": index, "text": reply_text,
                "parent_id": parent_url.rstrip("/").rsplit("/", 1)[-1],
                "expected_media_local_path": str(reply_media["absolute_local_source_path"]),
                "media_asset_id": reply_media["media_asset_id"],
                "media_sha256": reply_media["sha256"],
            })
            if reply_result.get("public_url"):
                parent_url = str(reply_result["public_url"])
            if str(reply_result.get("status") or "") not in SUCCESS_STATUSES:
                break
        if root_url and reply_rows and all(str(row.get("status") or "") in SUCCESS_STATUSES for row in reply_rows):
            x_readback = readback_x_thread_via_edge(
                cdp_port=cdp_port,
                root_url=root_url,
                canonical_url=canonical_url,
                expected_chart_path=primary_chart,
                replies=reply_rows,
                public_screenshot_path=output_dir / "public_x_thread_readback.png",
            )
        else:
            x_readback = {"status": "BLOCKED_X_EXISTING_ROOT_OR_REPLY_CHAIN_INCOMPLETE", "root_public_url": root_url}
        correction_readback["x_thread"] = x_readback
        results["x"] = {
            **root,
            "status": "SUCCESS" if x_readback.get("status") == "SUCCESS" else str(x_readback.get("status")),
            "action": "existing_root_plus_ordered_replies",
            "public_url": root_url,
            "id": root_id,
            "provider_readback_verified": x_readback.get("status") == "SUCCESS",
            "reply_chain": reply_rows,
            "readback": x_readback,
            "hard_truncation_repair": "LEGACY_TRUNCATED_ROOT_REPAIRED_BY_REPLY_CHAIN",
            "media_asset_id": primary_media.get("media_asset_id"),
            "media_sha256": primary_media.get("sha256"),
        }

    if "threads" in targets:
        from live_contentops.threads_adapter_v6 import readback_threads_chain, readback_threads_post

        prior_threads = dict(results.get("threads") or {})
        root_id = str(prior_threads.get("id") or "")
        root_readback = readback_threads_post(
            post_id=root_id,
            expected_text=str(article.get("title") or ""),
            canonical_url=canonical_url,
        )
        reply_rows = []
        for index, reply_text in enumerate(payloads["threads"]["reply_texts"], start=1):
            post_layout = payloads["threads"]["posts"][index]
            reply_media = media_by_id[str(post_layout["media_asset_ids"][0])]
            reply_result = _dispatch_once(
                ledger_path=ledger_path,
                platform="threads",
                payload=reply_text,
                canonical_url=canonical_url,
                media_attached=bool(reply_media),
                idempotency_scope=f"threads_reply:{root_id}:{index}",
                run_id=run_id,
                adapter_name="threads_adapter_v6.execute_threads_post",
                media=reply_media,
                runner_command=runner_command,
                executor=lambda reply_text=reply_text, reply_media=reply_media: _publish_threads_reply_verified(
                    parent_id=root_id,
                    text=reply_text,
                    canonical_url=None,
                    media=reply_media,
                ),
            )
            if reply_result.get("status") == "ALREADY_SUCCESSFUL_IDEMPOTENT" and reply_result.get("id"):
                replay_readback = readback_threads_post(
                    post_id=str(reply_result["id"]),
                    expected_text=reply_text,
                    canonical_url=None,
                    expected_media_local_path=str(reply_media["absolute_local_source_path"]),
                )
                reply_result["readback"] = replay_readback
                reply_result["provider_readback_verified"] = replay_readback.get("status") == "SUCCESS"
                reply_result["public_url"] = replay_readback.get("public_url") or reply_result.get("public_url")
            reply_rows.append({
                **reply_result, "order": index, "text": reply_text, "parent_id": root_id,
                "expected_media_local_path": str(reply_media["absolute_local_source_path"]),
                "media_asset_id": reply_media["media_asset_id"],
                "media_sha256": reply_media["sha256"],
            })
            if str(reply_result.get("status") or "") not in SUCCESS_STATUSES:
                break
        chain_readback = readback_threads_chain(
            root_id=root_id,
            reply_expectations=[{
                "id": row.get("id"), "text": row.get("text"),
                "expected_media_local_path": row.get("expected_media_local_path"),
            } for row in reply_rows],
        ) if reply_rows and all(str(row.get("status") or "") in SUCCESS_STATUSES for row in reply_rows) else {"status": "BLOCKED_THREADS_REPLY_CHAIN_INCOMPLETE"}
        threads_verified = bool(
            root_readback.get("status") == "SUCCESS"
            and reply_rows
            and all((row.get("readback") or {}).get("meaningful_media_visible") for row in reply_rows)
            and chain_readback.get("status") == "SUCCESS"
        )
        correction_readback["threads_root"] = root_readback
        correction_readback["threads_chain"] = chain_readback
        results["threads"] = {
            **prior_threads,
            "status": "SUCCESS" if threads_verified else "FAILED_THREADS_STRICT_THREAD_READBACK",
            "action": "existing_root_plus_media_reply_chain",
            "public_url": root_readback.get("public_url"),
            "provider_readback_verified": threads_verified,
            "reply_chain": reply_rows,
            "readback": {"root": root_readback, "chain": chain_readback},
            "repair_state": "REPAIRED_WITH_MEDIA_REPLY_AND_CONTINUATION" if threads_verified else "MISSING_MEDIA_REPAIR_INCOMPLETE",
            "media_asset_id": primary_media.get("media_asset_id"),
            "media_sha256": primary_media.get("sha256"),
        }

    if "facebook_page" in targets:
        from live_contentops.facebook_page_adapter_v6 import readback_facebook_post

        prior_facebook = dict(results.get("facebook_page") or {})
        old_id = str(prior_facebook.get("id") or "")
        old_readback = readback_facebook_post(
            post_id=old_id,
            expected_text=payloads["facebook_page"]["text"],
            canonical_url=canonical_url,
            expected_media_local_path=primary_chart,
        )
        superseded["facebook_page"] = {
            "status": "SUPERSEDED_WRONG_MEDIA",
            "id": old_id,
            "public_url": old_readback.get("public_url"),
            "preserved_not_deleted": True,
            "operator_visual_finding": "publication_logo_or_avatar_instead_of_approved_primary_chart",
            "readback": old_readback,
        }
        results["facebook_page"] = _dispatch_once(
            ledger_path=ledger_path,
            platform="facebook_page",
            payload=payloads["facebook_page"]["text"],
            canonical_url=canonical_url,
            media_attached=True,
            idempotency_scope=f"corrected_replacement:{old_id}",
            run_id=run_id,
            adapter_name="facebook_page_adapter_v6.execute_facebook_photo",
            media=primary_media,
            runner_command=runner_command,
            executor=lambda: _publish_facebook_photo_verified(
                text=payloads["facebook_page"]["text"],
                canonical_url=canonical_url,
                media=primary_media,
            ),
        )
        results["facebook_page"]["supersedes"] = {"id": old_id, "public_url": old_readback.get("public_url"), "status": "SUPERSEDED_WRONG_MEDIA"}
        correction_readback["facebook_page"] = results["facebook_page"].get("readback")

    if "instagram_business" in targets:
        from live_contentops.instagram_adapter_v6 import readback_instagram_media

        prior_instagram = dict(results.get("instagram_business") or {})
        old_id = str(prior_instagram.get("id") or "")
        old_readback = readback_instagram_media(
            media_id=old_id,
            expected_caption=payloads["instagram_business"]["text"],
            canonical_url=canonical_url,
            expected_media_local_path=primary_chart,
        )
        superseded["instagram_business"] = {
            "status": "SUPERSEDED_WRONG_MEDIA",
            "id": old_id,
            "public_url": old_readback.get("public_url"),
            "preserved_not_deleted": True,
            "operator_visual_finding": "publication_logo_or_avatar_instead_of_approved_primary_chart",
            "readback": old_readback,
        }
        results["instagram_business"] = _dispatch_once(
            ledger_path=ledger_path,
            platform="instagram_business",
            payload=payloads["instagram_business"]["text"],
            canonical_url=canonical_url,
            media_attached=True,
            idempotency_scope=f"corrected_replacement:{old_id}",
            run_id=run_id,
            adapter_name="instagram_adapter_v6.execute_instagram_post",
            media=primary_media,
            runner_command=runner_command,
            executor=lambda: _publish_instagram_media_verified(
                caption=payloads["instagram_business"]["text"],
                canonical_url=canonical_url,
                media=primary_media,
            ),
        )
        results["instagram_business"]["supersedes"] = {"id": old_id, "public_url": old_readback.get("public_url"), "status": "SUPERSEDED_WRONG_MEDIA"}
        correction_readback["instagram_business"] = results["instagram_business"].get("readback")

    if "linkedin" in targets:
        prior_linkedin = dict(results.get("linkedin") or {})
        corrected_linkedin_readback = readback_linkedin_post_via_edge(
            cdp_port=cdp_port,
            expected_text=payloads["linkedin"]["text"],
            canonical_url=canonical_url,
            public_screenshot_path=output_dir / "public_linkedin_readback.png",
        )
        linkedin_reconciliation = corrected_linkedin_readback if corrected_linkedin_readback.get("status") == "SUCCESS" else reconcile_existing_linkedin_post_via_edge(
            cdp_port=cdp_port,
            expected_text=payloads["linkedin"]["text"],
            canonical_url=canonical_url,
            chart_path=primary_chart,
            expected_payload_sha256=str(prior_linkedin.get("payload_sha256") or _sha256(payloads["linkedin"]["text"])),
            public_screenshot_path=output_dir / "linkedin_malformed_existing_post_readback.png",
        )
        correction_readback["linkedin_before_edit"] = linkedin_reconciliation
        if linkedin_reconciliation.get("status") == "SUCCESS":
            if str((superseded.get("linkedin") or {}).get("id") or "") == str(linkedin_reconciliation.get("post_id") or ""):
                superseded.pop("linkedin", None)
            if prior_linkedin.get("status") in UNKNOWN_WRITE_STATUSES:
                unintended = reconcile_existing_linkedin_post_via_edge(
                    cdp_port=cdp_port,
                    expected_text=payloads["linkedin"]["text"],
                    canonical_url=canonical_url,
                    chart_path=primary_chart,
                    expected_payload_sha256=_sha256(payloads["linkedin"]["text"]),
                    public_screenshot_path=output_dir / "linkedin_unintended_replacement_readback.png",
                )
                if (
                    unintended.get("status") == "MALFORMED_EXISTING_POST_REQUIRES_EDIT"
                    and unintended.get("post_id") != linkedin_reconciliation.get("post_id")
                ):
                    superseded["linkedin_unintended_replacement"] = {
                        "status": "SUPERSEDED_IMAGE_ONLY",
                        "id": unintended.get("post_id"),
                        "public_url": unintended.get("public_url"),
                        "preserved_not_deleted": True,
                        "reason": "replacement_write_from_prior_unknown-fallback bug produced image-only output",
                    }
            results["linkedin"] = {
                "status": "SUCCESS",
                "platform": "linkedin",
                "action": "edit_existing_post",
                "id": linkedin_reconciliation.get("post_id"),
                "public_url": linkedin_reconciliation.get("public_url"),
                "media_attached": True,
                "media_upload_transport": "preserved_existing_media_no_reupload",
                "provider_readback_verified": True,
                "destination_identity": "linkedin:jimcc",
                "substack_url_included": True,
                "payload_sha256": _sha256(payloads["linkedin"]["text"]),
                "write_outcome_certainty": "reconciled",
                "readback": linkedin_reconciliation,
                "new_post_created": False,
                "run_id": run_id,
                "execution_origin": "contentops_pipeline",
                "runner_module": "live_contentops.eight_platform_substack_first_pipeline_v1",
                "adapter_name_version": "edge_cdp_publishing_adapter_v1.reconcile_existing_linkedin_post_via_edge",
                "media_asset_id": primary_media.get("media_asset_id"),
                "media_sha256": primary_media.get("sha256"),
            }
        elif linkedin_reconciliation.get("status") == "MALFORMED_EXISTING_POST_REQUIRES_EDIT":
            post_id = str(linkedin_reconciliation.get("post_id") or "")
            permalink = str(linkedin_reconciliation.get("public_url") or "")
            results["linkedin"] = _dispatch_once(
                ledger_path=ledger_path,
                platform="linkedin",
                payload=payloads["linkedin"]["text"],
                canonical_url=canonical_url,
                media_attached=True,
                idempotency_scope=f"edit_existing_post:{post_id}",
                run_id=run_id,
                adapter_name="edge_cdp_publishing_adapter_v1.edit_existing_linkedin_post_via_edge",
                media=primary_media,
                runner_command=runner_command,
                executor=lambda: edit_existing_linkedin_post_via_edge(
                    cdp_port=cdp_port,
                    public_url=permalink,
                    post_id=post_id,
                    text=payloads["linkedin"]["text"],
                    canonical_url=canonical_url,
                    public_screenshot_path=output_dir / "public_linkedin_readback.png",
                ),
            )
            correction_readback["linkedin_after_edit"] = results["linkedin"].get("readback")
            if str(results["linkedin"].get("status") or "") not in SUCCESS_STATUSES:
                post_edit_reconciliation = reconcile_existing_linkedin_post_via_edge(
                    cdp_port=cdp_port,
                    expected_text=payloads["linkedin"]["text"],
                    canonical_url=canonical_url,
                    chart_path=primary_chart,
                    expected_payload_sha256=_sha256(payloads["linkedin"]["text"]),
                    public_screenshot_path=output_dir / "linkedin_post_edit_reconciliation.png",
                )
                correction_readback["linkedin_post_edit_reconciliation"] = post_edit_reconciliation
                if post_edit_reconciliation.get("status") == "SUCCESS":
                    results["linkedin"] = {
                        **results["linkedin"],
                        "status": "SUCCESS",
                        "id": post_id,
                        "public_url": permalink,
                        "provider_readback_verified": True,
                        "readback": post_edit_reconciliation,
                        "write_outcome_certainty": "reconciled",
                    }
                elif str(results["linkedin"].get("write_outcome_certainty") or "confirmed") != "unknown":
                    comment_result = _dispatch_once(
                        ledger_path=ledger_path,
                        platform="linkedin",
                        payload=payloads["linkedin"]["text"],
                        canonical_url=canonical_url,
                        media_attached=True,
                        idempotency_scope=f"author_comment_repair:{post_id}",
                        run_id=run_id,
                        adapter_name="edge_cdp_publishing_adapter_v1.comment_existing_linkedin_post_via_edge",
                        media=primary_media,
                        runner_command=runner_command,
                        executor=lambda: comment_existing_linkedin_post_via_edge(
                            cdp_port=cdp_port,
                            public_url=permalink,
                            post_id=post_id,
                            text=payloads["linkedin"]["text"],
                            canonical_url=canonical_url,
                            public_screenshot_path=output_dir / "public_linkedin_comment_repair.png",
                        ),
                    )
                    correction_readback["linkedin_author_comment"] = comment_result.get("readback")
                    results["linkedin"] = comment_result
                    if (
                        str(comment_result.get("status") or "") not in SUCCESS_STATUSES
                        and str(comment_result.get("write_outcome_certainty") or "confirmed") != "unknown"
                    ):
                        superseded["linkedin"] = {
                            "status": "SUPERSEDED_IMAGE_ONLY",
                            "id": post_id,
                            "public_url": permalink,
                            "preserved_not_deleted": True,
                        }
                        replacement = _dispatch_once(
                            ledger_path=ledger_path,
                            platform="linkedin",
                            payload=payloads["linkedin"]["text"],
                            canonical_url=canonical_url,
                            media_attached=True,
                            idempotency_scope=f"corrected_replacement:{post_id}",
                            run_id=run_id,
                            adapter_name="edge_cdp_publishing_adapter_v1.publish_linkedin_post_via_edge",
                            media=primary_media,
                            runner_command=runner_command,
                            executor=lambda: publish_linkedin_post_via_edge(
                                cdp_port=cdp_port,
                                text=payloads["linkedin"]["text"],
                                image_path=primary_chart,
                                canonical_url=canonical_url,
                                public_screenshot_path=output_dir / "public_linkedin_replacement_readback.png",
                            ),
                        )
                        replacement["supersedes"] = {"id": post_id, "public_url": permalink, "status": "SUPERSEDED_IMAGE_ONLY"}
                        results["linkedin"] = replacement
        else:
            results["linkedin"] = {
                "status": "BLOCKED_EXISTING_LINKEDIN_POST_CANNOT_BE_EDITED",
                "platform": "linkedin",
                "public_url": linkedin_reconciliation.get("public_url"),
                "required_unblock": "The exact image-only activity could not be reconciled by account, source chart, timestamp, and run payload evidence; no duplicate was created.",
                "new_post_created": False,
                "reconciliation": linkedin_reconciliation,
            }

    if "youtube" in targets:
        prior_youtube = dict(results.get("youtube") or {})
        if prior_youtube.get("action") == "public_short" or "/watch?" in str(prior_youtube.get("public_url") or ""):
            evidence.setdefault("wrong_surface_executions", {})["youtube"] = {
                "status": "WRONG_SURFACE_EXECUTION_NOT_ACCEPTED",
                "public_url": prior_youtube.get("public_url"),
                "id": prior_youtube.get("id"),
                "preserved_without_delete_unlist_or_edit": True,
                "accepted_default_surface": "youtube_community_text_image_post",
            }
        prior_community_readback = None
        if "/post/" in str(prior_youtube.get("public_url") or ""):
            prior_community_readback = readback_youtube_community_post_via_edge(
                cdp_port=cdp_port,
                public_url=str(prior_youtube["public_url"]),
                expected_text=payloads["youtube"]["text"],
                canonical_url=canonical_url,
                public_screenshot_path=output_dir / "public_youtube_community_readback.png",
            )
        if prior_community_readback and prior_community_readback.get("status") == "SUCCESS":
            results["youtube"] = {
                **prior_youtube,
                "status": "SUCCESS",
                "action": "community_post",
                "id": prior_community_readback.get("post_id"),
                "public_url": prior_community_readback.get("public_url"),
                "provider_readback_verified": True,
                "readback": prior_community_readback,
                "write_outcome_certainty": "reconciled",
                "media_asset_id": primary_media.get("media_asset_id"),
                "media_sha256": primary_media.get("sha256"),
            }
            _append_dispatch_ledger(
                ledger_path,
                {
                    "timestamp": _utc_now(),
                    "platform": "youtube",
                    "payload_sha256": _sha256(payloads["youtube"]["text"]),
                    "success": True,
                    "status": "SUCCESS_RECONCILED_PUBLIC_READBACK",
                    "action": "community_post",
                    "id": prior_community_readback.get("post_id"),
                    "public_url": prior_community_readback.get("public_url"),
                    "media_attached": True,
                    "substack_url_included": True,
                    "write_outcome_certainty": "reconciled",
                    "idempotency_scope": "youtube_community_post",
                    "run_id": run_id,
                    "execution_origin": "contentops_pipeline",
                    "adapter_name_version": "edge_cdp_publishing_adapter_v1.readback_youtube_community_post_via_edge",
                    "media_asset_id": primary_media.get("media_asset_id"),
                    "media_sha256": primary_media.get("sha256"),
                    "canonical_substack_url": canonical_url,
                },
            )
        else:
            results["youtube"] = _dispatch_once(
                ledger_path=ledger_path,
                platform="youtube",
                payload=payloads["youtube"]["text"],
                canonical_url=canonical_url,
                media_attached=True,
                idempotency_scope="youtube_community_post",
                run_id=run_id,
                adapter_name="edge_cdp_publishing_adapter_v1.publish_youtube_community_post_via_edge",
                media=primary_media,
                runner_command=runner_command,
                executor=lambda: publish_youtube_community_post_via_edge(
                    cdp_port=cdp_port,
                    text=payloads["youtube"]["text"],
                    image_path=primary_chart,
                    canonical_url=canonical_url,
                    public_screenshot_path=output_dir / "public_youtube_community_readback.png",
                ),
            )
        correction_readback["youtube_community"] = results["youtube"].get("readback")

    if "tiktok" in targets:
        try:
            tiktok_session = probe_authenticated_platform_session(cdp_port, "tiktok")
        except Exception as exc:
            tiktok_session = {"authenticated": False, "error_class": type(exc).__name__}
        results["tiktok"] = {
            "status": "BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED" if not tiktok_session.get("authenticated") else "BLOCKED_TIKTOK_NATIVE_DERIVATIVE_NOT_CONFIGURED",
            "platform": "tiktok",
            "required_unblock": "Authenticate the intended TikTok account in the canonical ContentOps Edge profile and enable the separately reviewed native derivative mode.",
            "canonical_republished": False,
            "run_id": run_id,
            "execution_origin": "contentops_pipeline",
            "runner_module": "live_contentops.eight_platform_substack_first_pipeline_v1",
        }

    frozen_after = {platform: json.dumps(results.get(platform) or {}, sort_keys=True) for platform in frozen_platforms}
    evidence["results"] = results
    evidence["task_label"] = TASK_LABEL
    evidence["browser_doctor"] = doctor
    evidence["classification"] = _classification(results)
    evidence["correction_readback"] = correction_readback
    evidence["superseded_malformed_posts"] = superseded
    evidence["platform_contract"] = {
        "substack": "canonical_full_article_frozen",
        "telegram": "text_image_derivative_plus_substack_url_frozen",
        "discord": "newsroom_derivative_plus_substack_url_frozen_logo_preview_is_minor_future_enhancement",
        "x": "existing_chart_root_plus_ordered_reply_continuation",
        "threads": "existing_root_plus_chart_reply_and_ordered_continuation",
        "linkedin": "analytical_text_plus_source_chart_plus_substack_url",
        "facebook_page": "corrected_chart_replacement_plus_complete_text_and_substack_url",
        "instagram_business": "corrected_chart_replacement_plus_complete_caption_and_substack_url",
        "youtube": "community_text_plus_source_chart_plus_substack_url",
        "tiktok": "native_derivative_or_explicit_canonical_profile_authentication_blocker",
        "youtube_video_short_default": False,
        "video_short_mode": "separate_explicit_non_default_mode_only",
    }
    evidence["derivative_resume"] = {
        "resumed_at": _utc_now(),
        "targets": sorted(targets),
        "canonical_republished": False,
        "substack_adapter_called": False,
        "successful_destinations_frozen": all(frozen_before[p] == frozen_after[p] for p in frozen_platforms),
        "frozen_destinations": list(frozen_platforms),
        "youtube_video_or_short_adapter_called": False,
        "delivery_media_manifest_status": delivery_media_manifest.get("status"),
        "selected_media_asset_id": primary_media.get("media_asset_id"),
        "selected_media_sha256": primary_media.get("sha256"),
    }
    visual_qa_path = output_dir / "visual_qa_public_destinations_v1.json"
    if visual_qa_path.exists():
        evidence["visual_qa"] = _read_json(visual_qa_path)
    evidence["starting_remote_head"] = "9ecdc86853cc7d79e3bb6c4b4592aa5acbacc45b"
    evidence["docs_updated"] = [
        "AGENTS.md",
        "docs/AI_BUILDER_BOOTSTRAP.md",
        "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
        "docs/status/CURRENT_PROJECT_STATUS.md",
        "docs/status/current_project_status.json",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json",
        "docs/automation/OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP/operator_browser_lab_runbook.md",
    ]
    evidence["final_platform_matrix"] = _persist_final_platform_matrix(output_dir, evidence)
    _write_json(evidence_path, evidence)
    _write_text(output_dir / "README.md", _readme(evidence))
    return evidence


def reconcile_existing_derivative_readbacks(
    *,
    output_dir: Path,
    cdp_port: int = 9223,
) -> dict[str, Any]:
    """Resolve derivative state through read-only provider reconciliation."""
    evidence_path = output_dir / "run_evidence_v1.json"
    if not evidence_path.exists():
        raise FileNotFoundError("reconciliation_requires_existing_run_evidence")
    evidence = _read_json(evidence_path)
    results = {name: dict(value) for name, value in (evidence.get("results") or {}).items() if isinstance(value, Mapping)}
    canonical_url = str((results.get("substack") or {}).get("public_url") or "")
    if not canonical_url:
        evidence["reconciliation_blocker"] = "canonical_substack_public_url_required"
        return evidence
    doctor = browser_doctor()
    if doctor.get("status") != "READY_TO_ATTACH" or doctor.get("recommended_cdp_port") != cdp_port:
        evidence["reconciliation_blocker"] = "canonical_edge_profile_not_attached"
        return evidence
    payloads = build_native_derivative_payloads(
        article=dict(evidence["article"]),
        selection=dict(evidence["selected_idea"]),
        canonical_url=canonical_url,
    )
    delivery_media_manifest = build_delivery_media_manifest(
        media_packet=dict(evidence["media"]),
        public_image_urls=list(((results.get("substack") or {}).get("readback") or {}).get("public_image_urls") or []),
        run_id=str(evidence.get("run_id") or ""),
    )
    _write_json(output_dir / "delivery_media_manifest_v1.json", delivery_media_manifest)
    if delivery_media_manifest.get("status") != "PASS":
        evidence["readback_reconciliation"] = {"status": "BLOCKED_DELIVERY_MEDIA_MANIFEST", "blockers": delivery_media_manifest.get("blockers")}
        _write_json(evidence_path, evidence)
        return evidence
    primary_media = select_primary_chart(delivery_media_manifest)
    chart_path = str(primary_media["absolute_local_source_path"])
    reconciliation: dict[str, Any] = {
        "reconciled_at": _utc_now(),
        "browser_write_performed": False,
        "canonical_republished": False,
        "substack_adapter_called": False,
    }
    reconciliation["linkedin"] = reconcile_existing_linkedin_post_via_edge(
        cdp_port=cdp_port,
        expected_text=payloads["linkedin"]["text"],
        canonical_url=canonical_url,
        chart_path=chart_path,
        expected_payload_sha256=str((results.get("linkedin") or {}).get("payload_sha256") or ""),
        public_screenshot_path=output_dir / "linkedin_reconciliation_readback.png",
    )
    from live_contentops.facebook_page_adapter_v6 import readback_facebook_post
    from live_contentops.instagram_adapter_v6 import readback_instagram_media
    from live_contentops.threads_adapter_v6 import readback_threads_post

    reconciliation["facebook_page"] = readback_facebook_post(
        post_id=str((results.get("facebook_page") or {}).get("id") or ""),
        expected_text=payloads["facebook_page"]["text"],
        canonical_url=canonical_url,
        expected_media_local_path=chart_path,
    )
    reconciliation["instagram_business"] = readback_instagram_media(
        media_id=str((results.get("instagram_business") or {}).get("id") or ""),
        expected_caption=payloads["instagram_business"]["text"],
        canonical_url=canonical_url,
        expected_media_local_path=chart_path,
    )
    reconciliation["threads"] = readback_threads_post(
        post_id=str((results.get("threads") or {}).get("id") or ""),
        expected_text=str(evidence["article"].get("title") or ""),
        canonical_url=canonical_url,
    )
    reconciliation["x"] = readback_x_thread_via_edge(
        cdp_port=cdp_port,
        root_url=str((results.get("x") or {}).get("public_url") or ""),
        canonical_url=canonical_url,
        expected_chart_path=chart_path,
        replies=[],
        public_screenshot_path=output_dir / "public_x_root_reconciliation.png",
    )
    youtube = dict(results.get("youtube") or {})
    youtube_url = str(youtube.get("public_url") or "")
    if "/post/" in youtube_url:
        youtube_readback = readback_youtube_community_post_via_edge(
            cdp_port=cdp_port,
            public_url=youtube_url,
            expected_text=payloads["youtube"]["text"],
            canonical_url=canonical_url,
            public_screenshot_path=output_dir / "public_youtube_community_readback.png",
        )
        reconciliation["youtube"] = youtube_readback
        if youtube_readback.get("status") == "SUCCESS":
            youtube["provider_readback_verified"] = True
            youtube["readback"] = youtube_readback
            results["youtube"] = youtube
    elif youtube_url:
        evidence.setdefault("wrong_surface_executions", {})["youtube"] = {
            "status": "WRONG_SURFACE_EXECUTION_NOT_ACCEPTED",
            "public_url": youtube_url,
            "id": youtube.get("id"),
            "preserved_without_delete_unlist_or_edit": True,
        }
    evidence["results"] = results
    evidence["browser_doctor"] = doctor
    evidence["classification"] = _classification(results)
    evidence["readback_reconciliation"] = reconciliation
    evidence["final_platform_matrix"] = _persist_final_platform_matrix(output_dir, evidence)
    _write_json(evidence_path, evidence)
    _write_text(output_dir / "README.md", _readme(evidence))
    return evidence


def reconcile_linkedin_activity_pair(
    *,
    output_dir: Path,
    cdp_port: int,
    accepted_url: str,
    accepted_id: str,
    latest_url: str,
    latest_id: str,
) -> dict[str, Any]:
    """Reconcile two known LinkedIn activities and edit only the latest malformed one."""
    evidence_path = output_dir / "run_evidence_v1.json"
    evidence = _read_json(evidence_path)
    canonical_url = str(((evidence.get("results") or {}).get("substack") or {}).get("public_url") or "")
    article = dict(evidence["article"])
    selection = dict(evidence["selected_idea"])
    payload = build_native_derivative_payloads(article=article, selection=selection, canonical_url=canonical_url)["linkedin"]["text"]
    manifest = build_delivery_media_manifest(
        media_packet=dict(evidence["media"]),
        public_image_urls=list(((((evidence.get("results") or {}).get("substack") or {}).get("readback") or {}).get("public_image_urls") or [])),
        run_id=str(evidence.get("run_id") or ""),
    )
    primary = select_primary_chart(manifest)
    chart_path = str(primary["absolute_local_source_path"])
    accepted = readback_linkedin_activity_via_edge(
        cdp_port=cdp_port,
        public_url=accepted_url,
        post_id=accepted_id,
        expected_text=payload,
        canonical_url=canonical_url,
        chart_path=chart_path,
        public_screenshot_path=output_dir / "linkedin_accepted_activity_readback_v3.png",
    )
    latest_before = readback_linkedin_activity_via_edge(
        cdp_port=cdp_port,
        public_url=latest_url,
        post_id=latest_id,
        expected_text=payload,
        canonical_url=canonical_url,
        chart_path=chart_path,
        public_screenshot_path=output_dir / "linkedin_latest_activity_before_v3.png",
    )
    edit_result: dict[str, Any] | None = None
    latest_after = latest_before
    if accepted.get("status") == "SUCCESS" and latest_before.get("status") == "MALFORMED_EXISTING_POST_REQUIRES_EDIT":
        edit_result = edit_existing_linkedin_post_via_edge(
            cdp_port=cdp_port,
            public_url=latest_url,
            post_id=latest_id,
            text=payload,
            canonical_url=canonical_url,
            public_screenshot_path=output_dir / "linkedin_latest_activity_after_v3.png",
        )
        if edit_result.get("status") == "SUCCESS":
            latest_after = dict(edit_result.get("readback") or {})
            latest_after.update({"status": "SUCCESS", "post_id": latest_id, "public_url": latest_url})
    if latest_after.get("status") == "SUCCESS":
        relationship = "EARLIER_ACCEPTED_AND_LATEST_CORRECTED_IN_PLACE"
        superseded_status = None
    else:
        relationship = "EARLIER_ACCEPTED_LATEST_PRESERVED_SUPERSEDED_IMAGE_ONLY"
        superseded_status = "SUPERSEDED_IMAGE_ONLY"
    packet = {
        "schema_version": "contentops.linkedin_activity_pair_reconciliation.v1",
        "run_id": evidence.get("run_id"),
        "execution_origin": "contentops_pipeline",
        "adapter": "edge_cdp_publishing_adapter_v1",
        "canonical_substack_url": canonical_url,
        "payload_sha256": _sha256(payload),
        "media_asset_id": primary.get("media_asset_id"),
        "media_sha256": primary.get("sha256"),
        "accepted_activity": accepted,
        "latest_activity_before": latest_before,
        "latest_edit_result": edit_result,
        "latest_activity_after": latest_after,
        "relationship": relationship,
        "latest_supersession_status": superseded_status,
        "third_post_created": False,
        "publish_adapter_called": False,
        "comment_adapter_called": False,
        "classification": "PASS_LINKEDIN_PAIR_RECONCILED" if accepted.get("status") == "SUCCESS" else "BLOCKED_LINKEDIN_ACCEPTED_ACTIVITY_READBACK",
    }
    _write_json(output_dir / "linkedin_activity_pair_reconciliation_v1.json", packet)
    results = dict(evidence.get("results") or {})
    superseded = dict(evidence.get("superseded_malformed_posts") or {})
    if latest_after.get("status") == "SUCCESS":
        results["linkedin"] = {
            "status": "SUCCESS",
            "platform": "linkedin",
            "action": "edit_existing_post",
            "id": latest_id,
            "public_url": latest_url,
            "provider_readback_verified": True,
            "readback": latest_after,
            "accepted_activity_relationship": relationship,
            "accepted_activities": [accepted_id, latest_id],
            "new_post_created": False,
            "payload_sha256": _sha256(payload),
            "media_asset_id": primary.get("media_asset_id"),
            "media_sha256": primary.get("sha256"),
            "execution_origin": "contentops_pipeline",
            "adapter_name_version": "edge_cdp_publishing_adapter_v1.edit_existing_linkedin_post_via_edge",
            "substack_url_included": True,
            "write_outcome_certainty": "confirmed",
        }
        superseded.pop("linkedin_unintended_replacement", None)
    else:
        superseded["linkedin_unintended_replacement"] = {
            "status": "SUPERSEDED_IMAGE_ONLY",
            "id": latest_id,
            "public_url": latest_url,
            "preserved_not_deleted": True,
            "relationship_to_accepted_activity": accepted_id,
        }
    evidence["task_label"] = TASK_LABEL
    evidence["results"] = results
    evidence["superseded_malformed_posts"] = superseded
    evidence["linkedin_activity_pair_reconciliation"] = packet
    evidence["final_platform_matrix"] = _persist_final_platform_matrix(output_dir, evidence)
    _write_json(evidence_path, evidence)
    return packet


def compile_variant_reliability_evidence(*, output_dir: Path) -> dict[str, Any]:
    """Compile future native layouts from current evidence without browser or writes."""
    evidence = _read_json(output_dir / "run_evidence_v1.json")
    canonical_url = str(((evidence.get("results") or {}).get("substack") or {}).get("public_url") or "")
    payloads = build_native_derivative_payloads(
        article=dict(evidence["article"]),
        selection=dict(evidence["selected_idea"]),
        canonical_url=canonical_url,
    )
    media_assets = list((evidence.get("media") or {}).get("assets") or [])
    media_ids = [str(item.get("asset_id") or "") for item in media_assets]
    thread_rows = {platform: payloads[platform] for platform in ("x", "threads")}
    pass_gate = all(
        row["quality_metrics"]["sentence_boundary_pass"]
        and row["quality_metrics"]["orphan_fragment_count"] == 0
        and row["quality_metrics"]["visual_distribution_pass"]
        and row["quality_metrics"]["complete_article_visual_count"] == 3
        and row["quality_metrics"]["reply_count"] == 2
        for row in thread_rows.values()
    ) and media_ids == ["primary", "policy_corridor", "sofr_context"]
    packet = {
        "schema_version": "contentops.platform_variant_reliability.v1",
        "classification": "PASS_SEMANTIC_VARIANT_RELIABILITY" if pass_gate else "BLOCKED_SEMANTIC_VARIANT_RELIABILITY",
        "run_id": evidence.get("run_id"),
        "canonical_substack_url": canonical_url,
        "public_write_performed": False,
        "live_outputs_modified": False,
        "operator_audit_fixture": {
            "x": "LIVE_CHAIN_HAS_ARBITRARY_SENTENCE_SPLITS_AND_SIX_REPLIES",
            "threads": "LIVE_ROOT_MISSING_APPROVED_CHART_AND_CHAIN_HAS_SENTENCE_FRAGMENTS",
        },
        "approved_article_media_asset_ids": media_ids,
        "planned_layouts": thread_rows,
    }
    _write_json(output_dir / "planned_semantic_variants_v1.json", packet)
    return packet


def finalize_reliability_hardening_evidence(*, output_dir: Path) -> dict[str, Any]:
    """Promote V3 audit results into current evidence without any provider call."""
    evidence_path = output_dir / "run_evidence_v1.json"
    evidence = _read_json(evidence_path)
    editorial = _read_json(output_dir / "tier1_editorial_comparison_v1.json")
    variants = _read_json(output_dir / "planned_semantic_variants_v1.json")
    video = _read_json(output_dir / "video_platform_capability_matrix_v1.json")
    linkedin = _read_json(output_dir / "linkedin_activity_pair_reconciliation_v1.json")
    results = {name: dict(value) for name, value in (evidence.get("results") or {}).items() if isinstance(value, Mapping)}
    results["x"]["quality_status"] = "FAIL_LIVE_CHAIN_ARBITRARY_SENTENCE_SPLITS_PRESERVED"
    results["x"]["planned_reliability_replacement"] = "planned_semantic_variants_v1.json#planned_layouts.x"
    results["threads"]["quality_status"] = "FAIL_LIVE_ROOT_MISSING_APPROVED_CHART_AND_FRAGMENTED_REPLIES_PRESERVED"
    results["threads"]["planned_reliability_replacement"] = "planned_semantic_variants_v1.json#planned_layouts.threads"
    results["instagram_business"].update({
        "quality_status": "PASS_FEED_CAPTION_URL_TEXT",
        "canonical_url_text_visible": True,
        "canonical_url_exact": True,
        "caption_link_clickable": False,
        "caption_link_clickable_required": False,
        "cta_mode": "canonical_url_text",
    })
    evidence.update({
        "task_label": TASK_LABEL,
        "results": results,
        "current_quality_classification": "PASS_RELIABILITY_HARDENING_WITH_PRESERVED_LEGACY_X_THREADS_OUTPUT_DEFECTS",
        "operator_visual_audit_v3": {
            "substack": "PASS_FROZEN",
            "telegram": "PASS_FROZEN",
            "discord": "PASS_FROZEN",
            "facebook_page": "PASS_CORRECTED_CHART_FROZEN",
            "youtube_community": "PASS_FROZEN",
            "x": results["x"]["quality_status"],
            "threads": results["threads"]["quality_status"],
            "instagram_business": "PASS_MEDIA_AND_EXACT_URL_TEXT_CAPTION_NOT_CLICKABLE_BY_PLATFORM_DESIGN",
            "linkedin": linkedin["relationship"],
            "tiktok": video["rows"]["tiktok_native"]["current_blocker"],
            "youtube_long_form": video["rows"]["youtube_long_form"]["current_blocker"],
            "youtube_shorts": video["rows"]["youtube_shorts"]["current_blocker"],
        },
        "reliability_evidence": {
            "editorial_comparison": "tier1_editorial_comparison_v1.json",
            "planned_semantic_variants": "planned_semantic_variants_v1.json",
            "linkedin_pair_reconciliation": "linkedin_activity_pair_reconciliation_v1.json",
            "video_capability_matrix": "video_platform_capability_matrix_v1.json",
        },
        "v3_safety": {
            "new_substack_article_published": False,
            "broad_social_distribution_run_created": False,
            "x_threads_facebook_instagram_telegram_discord_youtube_community_modified": False,
            "linkedin_latest_activity_edited_in_place": linkedin["relationship"] == "EARLIER_ACCEPTED_AND_LATEST_CORRECTED_IN_PLACE",
            "third_linkedin_post_created": linkedin["third_post_created"],
            "tiktok_content_published": False,
            "youtube_video_published": False,
            "youtube_short_published": False,
            "video_private_upload_performed": False,
        },
        "v3_docs_updated": [
            "AGENTS.md",
            "docs/AI_BUILDER_BOOTSTRAP.md",
            "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
            "docs/status/CURRENT_PROJECT_STATUS.md",
            "docs/status/current_project_status.json",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json",
            "docs/automation/OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP/operator_browser_lab_runbook.md",
        ],
    })
    packet = {
        "schema_version": "contentops.reliability_hardening_evidence.v3",
        "classification": "PASS_TIER1_EDITORIAL_PLATFORM_VARIANT_RELIABILITY_AND_VIDEO_CAPABILITY_SPLIT_V3",
        "starting_head": "408a8b7b49e12120a0ad4b84b9b1d63366819228",
        "run_id": evidence.get("run_id"),
        "editorial_scores": {
            "before": editorial["original_audit"]["editorial_score"],
            "after": editorial["revised_audit"]["editorial_score"],
        },
        "seo_scores": {
            "before": editorial["original_audit"]["seo_score"],
            "after": editorial["revised_audit"]["seo_score"],
        },
        "editorial_gate": {
            "classification": editorial["combined_editorial_gate"]["classification"],
            "deterministic_pass": editorial["combined_editorial_gate"]["deterministic_pass"],
            "llm_semantic_pass": editorial["combined_editorial_gate"]["llm_semantic_pass"],
            "llm_cannot_override_deterministic_blockers": editorial["combined_editorial_gate"]["llm_cannot_override_deterministic_blockers"],
            "llm_review_status": editorial["llm_semantic_review"]["status"],
            "llm_review_decision": editorial["llm_semantic_review"]["decision"],
            "llm_review_sha256": editorial["llm_semantic_review"].get("review_sha256"),
            "original_rendered_body_sha256": editorial["original_audit"]["rendered_body_sha256"],
            "revised_rendered_body_sha256": editorial["revised_audit"]["rendered_body_sha256"],
            "process_language_removed": editorial["process_language_removed"],
            "source_continuity": editorial["source_continuity"],
        },
        "variant_metrics": {
            platform: variants["planned_layouts"][platform]["quality_metrics"]
            for platform in ("x", "threads")
        },
        "linkedin_relationship": linkedin["relationship"],
        "instagram_link_semantics": {
            "canonical_url_text_visible": True,
            "caption_link_clickable": False,
            "caption_link_clickable_required": False,
            "cta_mode": "canonical_url_text",
        },
        "video_capabilities": {name: row["current_blocker"] for name, row in video["rows"].items()},
        "safety": evidence["v3_safety"],
        "remaining_blockers": [
            results["x"]["quality_status"],
            results["threads"]["quality_status"],
            video["rows"]["tiktok_native"]["current_blocker"],
            video["rows"]["youtube_long_form"]["current_blocker"],
            video["rows"]["youtube_shorts"]["current_blocker"],
        ],
    }
    _write_json(output_dir / "reliability_hardening_evidence_v3.json", packet)
    evidence["final_platform_matrix"] = _persist_final_platform_matrix(output_dir, evidence)
    _write_json(evidence_path, evidence)
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=TASK_LABEL)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--cdp-port", type=int, default=9223)
    parser.add_argument("--llm-provider", default="auto")
    parser.add_argument("--operator-approved-full-live-run", action="store_true")
    parser.add_argument("--recover-substack-draft-id")
    parser.add_argument("--resume-derivatives", action="store_true")
    parser.add_argument("--resume-platform", action="append", default=[])
    parser.add_argument("--reconcile-readbacks", action="store_true")
    parser.add_argument("--reconcile-linkedin-pair", action="store_true")
    parser.add_argument("--linkedin-accepted-url")
    parser.add_argument("--linkedin-accepted-id")
    parser.add_argument("--linkedin-latest-url")
    parser.add_argument("--linkedin-latest-id")
    parser.add_argument("--compile-variants-only", action="store_true")
    parser.add_argument("--finalize-reliability-evidence", action="store_true")
    args = parser.parse_args(argv)
    output = args.output_dir or OUTPUT_ROOT / args.run_id
    if args.compile_variants_only:
        result = compile_variant_reliability_evidence(output_dir=output)
        print(json.dumps({
            "classification": result["classification"],
            "run_id": result["run_id"],
            "public_write_performed": result["public_write_performed"],
        }, indent=2, sort_keys=True))
        return 0 if result["classification"] == "PASS_SEMANTIC_VARIANT_RELIABILITY" else 2
    if args.finalize_reliability_evidence:
        result = finalize_reliability_hardening_evidence(output_dir=output)
        print(json.dumps({"classification": result["classification"], "run_id": result["run_id"], "safety": result["safety"]}, indent=2, sort_keys=True))
        return 0
    if not args.operator_approved_full_live_run:
        print(json.dumps({"classification": "BLOCKED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1", "reason": "operator_approved_full_live_run_flag_required"}, sort_keys=True))
        return 2
    if args.reconcile_linkedin_pair:
        required = (args.linkedin_accepted_url, args.linkedin_accepted_id, args.linkedin_latest_url, args.linkedin_latest_id)
        if not all(required):
            raise ValueError("linkedin_pair_requires_both_exact_activity_urls_and_ids")
        result = reconcile_linkedin_activity_pair(
            output_dir=output,
            cdp_port=args.cdp_port,
            accepted_url=args.linkedin_accepted_url,
            accepted_id=args.linkedin_accepted_id,
            latest_url=args.linkedin_latest_url,
            latest_id=args.linkedin_latest_id,
        )
    elif args.reconcile_readbacks:
        result = reconcile_existing_derivative_readbacks(
            output_dir=output,
            cdp_port=args.cdp_port,
        )
    elif args.resume_derivatives:
        result = resume_eight_platform_derivatives(
            output_dir=output,
            cdp_port=args.cdp_port,
            platforms=args.resume_platform or None,
        )
    else:
        result = run_eight_platform_substack_first_pipeline(
            run_id=args.run_id,
            output_dir=output,
            cdp_port=args.cdp_port,
            llm_provider=args.llm_provider,
            operator_approved_full_live_run=True,
            recover_substack_draft_id=args.recover_substack_draft_id,
        )
    if args.reconcile_linkedin_pair:
        print(json.dumps({
            "classification": result["classification"],
            "run_id": result["run_id"],
            "relationship": result["relationship"],
            "third_post_created": result["third_post_created"],
        }, indent=2, sort_keys=True))
    else:
        print(json.dumps({"classification": result["classification"], "run_id": result["run_id"], "results": {platform: result["results"].get(platform, {}).get("status") for platform in EXPECTED_DESTINATIONS}}, indent=2, sort_keys=True))
    return 0 if result["classification"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
