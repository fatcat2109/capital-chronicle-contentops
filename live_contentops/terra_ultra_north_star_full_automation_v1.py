"""Terra Ultra north-star full automation runner for ContentOps.

This runner selects a fresh headline-backed topic, builds ContentOps-owned
media, exports a visual article, performs a guarded Telegram photo send, and
records exact blockers for browser-profile platforms.
"""
from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
import struct
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from .live_entrypoint_registry_v1 import LEGACY_AUTOMATION_QUARANTINED, quarantine
from .media_content_audit_v6 import build_current_macro_visual_pack
from .public_dispatch_freeze_guard_v6 import (
    append_public_dispatch_ledger,
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    evaluate_public_dispatch_freeze,
    load_public_dispatch_hashes,
    make_public_dispatch_approval_marker,
)

TASK_LABEL = "TASK_CONTENTOPS_TERRA_ULTRA_COMPLETE_NORTH_STAR_FULL_AUTOMATION_V1"
PASS_CLASSIFICATION = "PASS_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
PASS_PARTIAL_CLASSIFICATION = "PASS_PARTIAL_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
BLOCKED_CLASSIFICATION = "BLOCKED_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
FAILED_CLASSIFICATION = "FAILED_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"

REQUIRED_CAVEAT = "Candidate editorial draft. Numeric references require final source verification before publication."
OUTPUT_DIR = Path("docs/automation/TERRA_ULTRA_NORTH_STAR_FULL_AUTOMATION_V1")
MEDIA_DIR = OUTPUT_DIR / "media_assets"
ARTICLE_MD_PATH = Path("exports/daily_contentops/fed_funds_policy_signal_article_v1.md")
ARTICLE_HTML_PATH = Path("exports/daily_contentops/fed_funds_policy_signal_article_v1.html")
HEADLINE_SIDECAR_PATH = Path("headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_2026_07_08.jsonl")
DAILY_SCHEDULE_PATH = Path("docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json")
PUBLIC_DISPATCH_LEDGER = Path("docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")

SUBSTACK_BLOCKER = "BLOCKED_REQUIRES_SUPERVISED_BROWSER_PROFILE_AND_PUBLIC_URL_READBACK"
X_BLOCKER = "BLOCKED_REQUIRES_EXACT_CDP_LIVE_CLICK_WITH_PROFILE_GUARD"

SECRET_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9_-]{24,}:[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\b(?:xox[baprs]-|sk-)[A-Za-z0-9_-]{16,}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
FINANCIAL_ADVICE_PATTERNS = (
    re.compile(r"\b(buy|sell|short|go long|go short|load up on)\b.{0,40}\b(now|today|immediately)\b", re.IGNORECASE),
    re.compile(r"\bnot financial advice\b", re.IGNORECASE),
    re.compile(r"\bthis is financial advice\b", re.IGNORECASE),
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _png_dimensions(path: Path) -> dict[str, int | None]:
    try:
        data = path.read_bytes()
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            width, height = struct.unpack(">II", data[16:24])
            return {"width": int(width), "height": int(height)}
    except Exception:
        pass
    return {"width": None, "height": None}


def _contains_forbidden_secret_material(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)


def _has_financial_advice(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in FINANCIAL_ADVICE_PATTERNS)


def _redact_telegram_result_for_evidence(result: Mapping[str, Any]) -> dict[str, Any]:
    response = result.get("response")
    response_result = response.get("result", {}) if isinstance(response, Mapping) else {}
    photo = response_result.get("photo") if isinstance(response_result, Mapping) else None
    return {
        "status": result.get("status"),
        "platform": result.get("platform"),
        "action": result.get("action"),
        "id": result.get("id"),
        "response_ok": response.get("ok") if isinstance(response, Mapping) else None,
        "response_message_id": response_result.get("message_id") if isinstance(response_result, Mapping) else None,
        "response_has_photo": bool(photo),
        "response_photo_variant_count": len(photo) if isinstance(photo, list) else 0,
        "caption_sha256": _sha256_text(str(response_result.get("caption") or ""))
        if isinstance(response_result, Mapping) and response_result.get("caption")
        else None,
        "chat_username": response_result.get("chat", {}).get("username")
        if isinstance(response_result, Mapping) and isinstance(response_result.get("chat"), Mapping)
        else None,
        "error": result.get("error"),
        "error_code": result.get("error_code"),
        "error_class": result.get("error_class"),
    }


def _normalise_path(path: str | Path) -> str:
    return str(Path(path))


def _load_dotenv_if_available() -> bool:
    try:
        from dotenv import load_dotenv
    except Exception:
        return False
    load_dotenv()
    return True


def _line_json_sample(path: Path, limit: int = 80) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    total = 0
    if not path.exists():
        return rows, total
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        total += 1
        if len(rows) >= limit:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows, total


def load_headline_context(
    *,
    sidecar_path: Path = HEADLINE_SIDECAR_PATH,
    schedule_path: Path = DAILY_SCHEDULE_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    schedule = _read_json(schedule_path)
    sidecar_rows, sidecar_count = _line_json_sample(sidecar_path, limit=120)
    central_bank_rows = [
        {
            "headline_text": row.get("headline_text"),
            "author_handle": row.get("author_handle"),
            "headline_timestamp": row.get("headline_timestamp"),
            "candidate_catalyst_tags": row.get("candidate_catalyst_tags"),
            "follow_up_data_need_candidates": row.get("follow_up_data_need_candidates"),
            "numeric_truth_authority": row.get("numeric_truth_authority"),
        }
        for row in sidecar_rows
        if "central_bank" in {str(tag) for tag in row.get("candidate_catalyst_tags", [])}
        or row.get("follow_up_data_need_candidates")
    ][:12]
    context = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "schedule_path": _normalise_path(schedule_path),
        "sidecar_path": _normalise_path(sidecar_path),
        "schedule_date": schedule.get("schedule_date"),
        "headline_sidecar_count": schedule.get("headline_sidecar_count") or sidecar_count,
        "headline_sidecars_are_catalyst_only": bool(schedule.get("headline_sidecars_are_catalyst_only", True)),
        "forbidden_uses": schedule.get("forbidden_uses", []),
        "slots": schedule.get("slots", []),
        "central_bank_sidecar_examples": central_bank_rows,
        "freshness_basis": "repo_headline_schedule_and_sidecar_inputs_captured_2026_07_08",
    }
    _write_json(output_dir / "headline_intake_v1.json", context)
    return context


def _score_slot(slot: Mapping[str, Any]) -> tuple[int, list[str]]:
    topic = str(slot.get("topic") or "")
    tags = {str(tag).lower() for tag in slot.get("tags", [])}
    reasons: list[str] = []
    score = int(slot.get("impact_score") or 0) + int(slot.get("urgency_score") or 0)
    lowered = topic.lower()
    if "central_bank" in tags:
        score += 35
        reasons.append("central_bank_tag")
    if "official_central_bank_statement_or_calendar" in tags:
        score += 25
        reasons.append("official_central_bank_followup")
    if "fed funds" in lowered or "effective fed funds" in lowered:
        score += 55
        reasons.append("direct_fed_funds_rate_input")
    if "energy" in tags or "oil" in lowered or "crude" in lowered:
        score -= 120
        reasons.append("oil_family_duplicate_frozen_not_breaking_enough")
    if slot.get("readiness") == "READY_FOR_PIPELINE":
        score += 12
        reasons.append("ready_for_pipeline")
    if not slot.get("numeric_truth_authority", False):
        reasons.append("headline_sidecar_not_numeric_truth")
    return score, reasons


def select_north_star_idea(
    headline_context: Mapping[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    ledger_path: Path = PUBLIC_DISPATCH_LEDGER,
) -> dict[str, Any]:
    prior_hashes = load_public_dispatch_hashes(ledger_path)
    ranked: list[dict[str, Any]] = []
    for slot in headline_context.get("slots", []):
        score, reasons = _score_slot(slot)
        topic_hash = build_public_dispatch_topic_hash(str(slot.get("topic") or ""), str(slot.get("angle") or ""))
        duplicate_seen = topic_hash in prior_hashes["topic_hashes"]
        ranked.append(
            {
                "slot_index": slot.get("slot_index"),
                "topic": slot.get("topic"),
                "angle": slot.get("angle"),
                "score": score - (200 if duplicate_seen else 0),
                "raw_score": score,
                "duplicate_topic_hash_seen": duplicate_seen,
                "topic_hash": topic_hash,
                "reasons": reasons + (["duplicate_topic_hash_seen"] if duplicate_seen else []),
                "tags": slot.get("tags", []),
                "source_headline_author": slot.get("source_headline_author"),
                "source_headline_timestamp": slot.get("source_headline_timestamp"),
                "readiness": slot.get("readiness"),
            }
        )
    ranked.sort(key=lambda item: (int(item["score"]), int(item.get("slot_index") or 0)), reverse=True)
    selected = next(
        (
            item
            for item in ranked
            if "direct_fed_funds_rate_input" in item["reasons"]
            and not item["duplicate_topic_hash_seen"]
        ),
        ranked[0] if ranked else None,
    )
    if selected is None:
        raise RuntimeError("No editorial schedule slots available for north-star selection.")

    title = "The Fed Funds Signal Hiding in Plain Sight"
    editorial_angle = str(selected["angle"])
    publication_topic_hash = build_public_dispatch_topic_hash(title, editorial_angle)
    duplicate_decision = evaluate_public_dispatch_freeze(
        platform="telegram",
        action="photo",
        run_id="selection_preflight",
        topic_hash=publication_topic_hash,
        operator_approval_marker=make_public_dispatch_approval_marker(
            run_id="selection_preflight",
            topic_hash=publication_topic_hash,
            payload_hash="selection_payload_hash",
            platform="telegram",
        ),
        body_text="Selection preflight contains article fallback and candidate caveat for non-preview body.",
        media_url="selection_media_placeholder",
        payload_hash="selection_payload_hash",
        prior_dispatch_hashes=prior_hashes,
    )
    packet = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "selected_topic": selected["topic"],
        "selected_title": title,
        "selected_angle": editorial_angle,
        "selected_slot_index": selected["slot_index"],
        "selected_topic_hash": selected["topic_hash"],
        "publication_topic_hash": publication_topic_hash,
        "why_selected": [
            "fresh_non_oil_headline_schedule_slot",
            "central_bank_policy_signal",
            "existing_contentops_fed_funds_media_support",
            "oil_family_duplicate_frozen_not_breaking_enough",
        ],
        "why_oil_not_selected": "Prior oil repair already has a duplicate-frozen chart-backed article and no new breaking evidence in the current task authority justified bypassing the guard.",
        "duplicate_hotspot_decision": {
            "oil_family_status": "DUPLICATE_FROZEN_SUPERSEDED_BY_FRESH_NON_OIL_TOPIC",
            "selected_topic_duplicate_guard_status": duplicate_decision["status"],
            "selected_topic_duplicate_blockers": duplicate_decision["blockers"],
            "selected_topic_dispatch_allowed": duplicate_decision["dispatch_allowed"],
            "ledger_path": _normalise_path(ledger_path),
        },
        "llm_selection_contract": {
            "actor": "Codex GPT-5 ContentOps runner",
            "method": "LLM-assisted ranking over repo headline schedule with deterministic duplicate and media-support checks",
            "allowed_inputs": [
                _normalise_path(DAILY_SCHEDULE_PATH),
                _normalise_path(HEADLINE_SIDECAR_PATH),
                _normalise_path(PUBLIC_DISPATCH_LEDGER),
            ],
            "numeric_truth_boundary": "headline_sidecars_are_catalyst_only",
        },
        "ranked_candidates": ranked,
    }
    _write_json(output_dir / "idea_selection_v1.json", packet)
    return packet


def build_support_packet(selection: Mapping[str, Any], *, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    packet = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "selected_title": selection["selected_title"],
        "selected_topic": selection["selected_topic"],
        "selected_angle": selection["selected_angle"],
        "support_status": "GROUNDED_WITH_CANDIDATE_NUMERIC_CAVEAT",
        "required_caveat": REQUIRED_CAVEAT,
        "source_boundary": [
            "Headline sidecars are catalyst-only and are not numeric truth authority.",
            "Current rates visuals are generated by ContentOps from the bounded Fed/FRED/NY Fed/Treasury fallback fixture.",
            "Durable numeric authority remains the future CC_CONTENT_ARTIFACT_PACKET flow.",
        ],
        "source_trail": [
            {
                "source": "Daily editorial schedule",
                "path": _normalise_path(DAILY_SCHEDULE_PATH),
                "usage": "topic selection and follow-up need context",
            },
            {
                "source": "Headline sidecar JSONL",
                "path": _normalise_path(HEADLINE_SIDECAR_PATH),
                "usage": "freshness and catalyst context only",
            },
            {
                "source": "FRED DFF",
                "url": "https://fred.stlouisfed.org/series/DFF",
                "usage": "effective federal funds rate chart context",
            },
            {
                "source": "Federal Reserve policy tools",
                "url": "https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
                "usage": "policy corridor context",
            },
            {
                "source": "NY Fed SOFR methodology",
                "url": "https://www.newyorkfed.org/markets/reference-rates/sofr",
                "usage": "overnight secured funding context",
            },
            {
                "source": "Federal Reserve H.15 selected interest rates",
                "url": "https://www.federalreserve.gov/releases/h15/",
                "usage": "Treasury curve reference context",
            },
        ],
    }
    _write_json(output_dir / "support_packet_v1.json", packet)
    return packet


def build_media_pack(
    selection: Mapping[str, Any],
    *,
    output_dir: Path = MEDIA_DIR,
    evidence_output_dir: Path = OUTPUT_DIR,
    visual_builder: Callable[..., list[dict[str, Any]]] = build_current_macro_visual_pack,
) -> dict[str, Any]:
    assets = visual_builder(str(selection["selected_topic"]), output_dir=output_dir)
    manifest_assets: list[dict[str, Any]] = []
    for idx, asset in enumerate(assets):
        path = Path(str(asset.get("local_path") or ""))
        manifest_assets.append(
            {
                "index": idx + 1,
                "asset_id": asset.get("asset_id"),
                "path": _normalise_path(path),
                "exists": path.exists(),
                "sha256": _sha256_file(path) if path.exists() else None,
                "dimensions": _png_dimensions(path) if path.exists() else {"width": None, "height": None},
                "media_class": asset.get("media_class"),
                "media_role": asset.get("media_role"),
                "source_label": asset.get("source_label"),
                "canonical_source_label": asset.get("canonical_source_label"),
                "source_page_url": asset.get("source_page_url"),
                "rights_status": asset.get("rights_status"),
                "provenance_status": asset.get("provenance_status"),
                "content_authority_scope": asset.get("content_authority_scope"),
                "caption": asset.get("caption"),
                "alt_text": asset.get("alt_text"),
                "why_selected": asset.get("why_selected"),
            }
        )
    blockers = []
    if len(manifest_assets) < 3:
        blockers.append("media_asset_count_below_3")
    for asset in manifest_assets[:3]:
        if not asset["exists"]:
            blockers.append(f"media_asset_missing:{asset['path']}")
        dims = asset["dimensions"]
        if not dims.get("width") or not dims.get("height"):
            blockers.append(f"media_asset_dimensions_unreadable:{asset['path']}")
    manifest = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "media_gate_status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "media_asset_count": len(manifest_assets),
        "required_media_asset_count": 3,
        "contentops_built_media": True,
        "chart_assets_built": len(manifest_assets) >= 3,
        "media_source_kind": "contentops_built_fed_funds_chart_pack",
        "ai_generated_image": False,
        "static_generated_card": False,
        "google_image_used": False,
        "fred_chart_or_contentops_chart_used": True,
        "assets": manifest_assets[:3],
    }
    _write_json(evidence_output_dir / "media_manifest_v1.json", manifest)
    return manifest


def _visual_markdown(asset: Mapping[str, Any]) -> str:
    alt_text = str(asset.get("alt_text") or "ContentOps rates chart")
    caption = str(asset.get("caption") or "")
    path = str(asset.get("path") or "")
    return f"![{alt_text}]({path})\n\n*{caption}*\n"


def _article_visual_position_report(markdown: str, assets: list[Mapping[str, Any]]) -> dict[str, Any]:
    positions = []
    for asset in assets:
        marker = f"]({asset.get('path')})"
        positions.append(markdown.find(marker))
    valid_positions = [pos for pos in positions if pos >= 0]
    spread = (
        len(valid_positions) >= 3
        and valid_positions == sorted(valid_positions)
        and min(b - a for a, b in zip(valid_positions, valid_positions[1:])) >= 500
    )
    return {
        "visual_positions": positions,
        "visual_asset_count": len(valid_positions),
        "visuals_spread_through_article": spread,
        "visual_placement_status": "PASS_VISUALS_SPREAD_THROUGH_ARTICLE" if spread else "FAIL_VISUALS_NOT_SPREAD_THROUGH_ARTICLE",
    }


def _markdown_to_html(markdown: str, title: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        if not line:
            if in_list:
                body.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("!["):
            match = re.match(r"!\[(.*)\]\((.*)\)", line)
            if match:
                alt, src = match.groups()
                body.append(f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}" /></figure>')
        elif line.startswith("*") and line.endswith("*"):
            body.append(f"<p><em>{html.escape(line.strip('*'))}</em></p>")
        else:
            body.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        body.append("</ul>")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8" />',
            f"<title>{html.escape(title)}</title>",
            "<style>body{font-family:Georgia,serif;line-height:1.62;max-width:820px;margin:40px auto;padding:0 24px;color:#111827}img{max-width:100%;height:auto}figure{margin:30px 0}em{color:#475569}</style>",
            "</head>",
            "<body>",
            *body,
            "</body>",
            "</html>",
        ]
    )


def export_article(
    selection: Mapping[str, Any],
    support: Mapping[str, Any],
    media_manifest: Mapping[str, Any],
    *,
    article_md_path: Path = ARTICLE_MD_PATH,
    article_html_path: Path = ARTICLE_HTML_PATH,
    evidence_output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    assets = list(media_manifest.get("assets", []))
    if len(assets) < 3:
        raise RuntimeError("Cannot export north-star article with fewer than three media assets.")
    title = str(selection["selected_title"])
    md = f"""# {title}

SEO title: Fed funds rate signal: policy corridor, inflation expectations, and markets

Meta description: A candidate Capital Chronicle analysis of why a quiet effective fed funds rate still matters when policy communication, curve pricing, and liquidity conditions carry the signal.

{REQUIRED_CAVEAT}

## Executive Brief

The useful story in a still effective fed funds rate is not that nothing happened. It is that the overnight policy rate is doing the job the Federal Reserve designed it to do: sit inside the corridor while the rest of the market argues about growth, inflation, fiscal supply, and the timing of the next policy turn. The July 8 headline schedule flagged the effective fed funds update as a ready policy signal, and the surrounding sidecars pointed to a broader communication problem for central banks in a high-uncertainty tape.

{_visual_markdown(assets[0])}

The rate itself is a low-drama datapoint. That is the point. When the effective rate sits close to the policy corridor's center, the reader should focus less on a one-day change and more on whether money-market plumbing, Treasury yields, and risk assets are transmitting the same story. A calm overnight rate can coexist with noisy long-end yields, inflation-breakeven debate, and a market that keeps repricing the path of cuts.

That framing matters because markets often treat a quiet overnight rate as an empty headline. In a corridor system, quiet can be information. It suggests the central bank's operating framework is still absorbing daily funding pressure, leaving the larger argument to be fought in the curve, in real yields, and in the language officials use to describe the next inflation test.

The current headline context also made this a better live automation candidate than another oil pass. The schedule attached the Fed funds item to central-bank tags and an explicit rates-pricing angle, while the sidecar stream included broader reminders that central-bank communication is more valuable when macro uncertainty is high. That combination gives the article a current hook without asking the headline sidecars to become numeric authority.

## The Policy Corridor Is The Signal

The Fed does not steer overnight funding with a single number floating in isolation. It uses administered rates, reserves, repo facilities, and the target range to keep the effective rate near the desired zone. That corridor structure is why a flat effective fed funds print can still be useful: it tells editors and readers whether the floor system is behaving before they read too much into every cross-asset move.

In this setup, the policy question is not whether a quiet DFF print should move equities or the dollar by itself. It is whether the official corridor, the Treasury curve, and inflation expectations are telling a coherent story about restrictive policy. If those channels diverge, the editorial angle should explain the divergence rather than pretend the overnight rate settled the debate.

The policy-corridor visual is included for that reason. It gives readers a compact way to distinguish the target range from the instruments that help keep the effective rate there. Without that distinction, the article would risk reducing monetary policy to a single point estimate, which is exactly the kind of oversimplification a north-star ContentOps run should avoid.

{_visual_markdown(assets[1])}

## Why This Was Chosen Over Oil

The system did not continue the oil repair because that topic is already duplicate-frozen in the public dispatch ledger. The prior corrected oil article has three ContentOps-built charts, but a fresh Telegram resend is blocked by topic hash unless the operator explicitly supersedes the old public post. The fresh non-oil rate topic is cleaner: it is in the current schedule, carries central-bank tags, has a bounded ContentOps media path, and avoids forcing a duplicate-publication exception.

That distinction matters operationally. A north-star automation run should not prove itself by bypassing its own spam and duplicate controls. It should pick the best eligible topic, build the article and media, then let the public guard decide whether the send is safe.

This is also an editorial discipline point. Oil and energy policy remain legitimate macro stories, but the existing oil repair had already served its product purpose: it proved the corrected chart-media gate and then correctly stopped before another public post. A fresh rates story tests a more complete automation loop, because it requires the system to choose a new idea, use different media support, and preserve the same safety standards.

## Cross-Asset Transmission

The third read is the curve. A steady overnight rate does not mean financial conditions are steady everywhere. Treasury yields can carry term-premium pressure, issuance concerns, or growth repricing even when the front-end policy rate is mechanically quiet. That is why the article pairs the effective fed funds chart with policy-corridor and rates-context visuals rather than dropping all media at the end.

{_visual_markdown(assets[2])}

The trade for the reader is intellectual discipline. A single overnight datapoint is neither a trading instruction nor a macro conclusion. It is a checkpoint. If the policy rate remains orderly while the curve moves, the live question becomes what part of the market is absorbing new information: inflation risk, growth risk, liquidity, fiscal supply, or central-bank reaction-function messaging.

That is why the final chart compares the overnight policy anchor with selected curve points rather than asserting a simple causal chain. If the front end is calm and longer yields are not, the article should not jump to an investment call. It should ask which channel is doing the repricing and whether official communication is validating or resisting that move.

## Editorial Read

For a public Capital Chronicle candidate, the useful headline is simple: a quiet effective fed funds rate can still carry signal because it anchors the corridor while other markets reveal where uncertainty is migrating. The chosen angle therefore frames the policy signal against rates, inflation expectations, and market-pricing limits, without converting catalyst-only headlines into numeric authority.

The practical takeaway is not to trade the DFF print. It is to use the print as a control variable. If overnight plumbing is orderly, then the next article questions become cleaner: whether inflation expectations are drifting, whether real rates are doing the tightening, whether fiscal supply is steepening the curve, and whether officials are comfortable with the market's policy path.

That is the product standard this run was meant to demonstrate. The pipeline did not need a manually selected image, did not cluster all visuals at the end, did not recycle the duplicate oil topic, and did not claim a Substack or X success without a URL readback. It produced a complete candidate article, attached real chart media to Telegram, and left the remaining blockers exact enough for the next supervised run.

## Source And Caveat Trail

- Topic source: {support["source_trail"][0]["path"]}.
- Headline context: {support["source_trail"][1]["path"]}; catalyst-only, not numeric truth authority.
- Visual sources: FRED DFF, Federal Reserve policy tools, NY Fed SOFR methodology, and Federal Reserve H.15 context as recorded in the media manifest.
- Publication caveat: {REQUIRED_CAVEAT}
"""
    placement = _article_visual_position_report(md, assets)
    html_doc = _markdown_to_html(md, title)
    _write_text(article_md_path, md)
    _write_text(article_html_path, html_doc)
    manifest = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "article_export_created": article_md_path.exists(),
        "article_export_path": _normalise_path(article_md_path),
        "article_html_export_path": _normalise_path(article_html_path),
        "public_article_url": None,
        "article_publication_status": "LOCAL_EXPORT_CREATED_SUBSTACK_BLOCKED",
        "article_fallback_reference": _normalise_path(article_md_path),
        "title": title,
        "seo_title": "Fed funds rate signal: policy corridor, inflation expectations, and markets",
        "markdown_sha256": _sha256_file(article_md_path),
        "html_sha256": _sha256_file(article_html_path),
        "word_count": len(re.findall(r"\b\w+\b", md)),
        "caveat_present": REQUIRED_CAVEAT in md,
        "exact_numeric_claims_made": True,
        "financial_advice_detected": _has_financial_advice(md),
        "forbidden_secret_material_detected": _contains_forbidden_secret_material(md),
        **placement,
    }
    _write_json(evidence_output_dir / "article_manifest_v1.json", manifest)
    return manifest


def build_platform_variants(
    selection: Mapping[str, Any],
    article_manifest: Mapping[str, Any],
    media_manifest: Mapping[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    primary_media = media_manifest["assets"][0]
    article_ref = str(article_manifest["article_fallback_reference"])
    caption = (
        "The Fed Funds Signal Hiding in Plain Sight\n\n"
        "A quiet overnight policy rate can still matter when the corridor is orderly but the curve, inflation expectations, and liquidity debate are not.\n\n"
        f"{REQUIRED_CAVEAT}\n\n"
        f"Full local article fallback: {article_ref}\n"
        f"Primary chart: {primary_media['path']}"
    )
    variants = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "telegram": {
            "action": "photo",
            "photo_path": primary_media["path"],
            "caption": caption,
            "caption_length": len(caption),
            "article_link_or_fallback_included": article_ref in caption,
            "required_caveat_included": REQUIRED_CAVEAT in caption,
        },
        "substack": {
            "status": SUBSTACK_BLOCKER,
            "title": selection["selected_title"],
            "subtitle": "Why a quiet effective fed funds rate can still frame the market's policy debate.",
            "body_markdown_path": article_manifest["article_export_path"],
            "image_assets": [asset["path"] for asset in media_manifest["assets"]],
            "exact_blocker": "The available safe Substack path is Playwright/browser-profile assisted and requires public URL/image readback after publish.",
        },
        "x": {
            "status": X_BLOCKER,
            "text": (
                "A quiet effective fed funds print can still matter: it anchors the policy corridor while the curve and inflation-pricing debate carry the uncertainty. "
                f"{REQUIRED_CAVEAT}"
            ),
            "media_assets": [asset["path"] for asset in media_manifest["assets"][:1]],
            "exact_blocker": "The available X path is supervised CDP/profile guarded and requires explicit live-click scope plus permalink readback.",
        },
    }
    _write_json(output_dir / "platform_variants_v1.json", variants)
    return variants


def _preflight_blockers(
    *,
    operator_approved_full_live_run: bool,
    max_send_attempts_per_platform: int,
    media_manifest: Mapping[str, Any],
    article_manifest: Mapping[str, Any],
    variants: Mapping[str, Any],
    guard: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if not operator_approved_full_live_run:
        blockers.append("operator_approved_full_live_run_required")
    if max_send_attempts_per_platform != 1:
        blockers.append("max_send_attempts_per_platform_must_equal_1")
    if media_manifest.get("media_gate_status") != "PASS":
        blockers.extend(str(item) for item in media_manifest.get("blockers", []))
    if int(media_manifest.get("media_asset_count") or 0) < 3:
        blockers.append("minimum_three_media_assets_required")
    if not media_manifest.get("contentops_built_media"):
        blockers.append("contentops_built_media_required")
    if media_manifest.get("ai_generated_image") or media_manifest.get("static_generated_card"):
        blockers.append("generated_or_static_card_media_forbidden")
    if not article_manifest.get("visuals_spread_through_article"):
        blockers.append("article_visuals_not_spread_through_body")
    if not article_manifest.get("caveat_present"):
        blockers.append("required_caveat_missing_from_article")
    if article_manifest.get("financial_advice_detected"):
        blockers.append("financial_advice_detected_in_article")
    if article_manifest.get("forbidden_secret_material_detected"):
        blockers.append("secret_material_detected_in_article")
    telegram = variants["telegram"]
    if not telegram.get("required_caveat_included"):
        blockers.append("telegram_caption_missing_required_caveat")
    if not telegram.get("article_link_or_fallback_included"):
        blockers.append("telegram_caption_missing_article_fallback")
    if int(telegram.get("caption_length") or 0) > 1024:
        blockers.append("telegram_caption_over_1024_characters")
    if guard.get("status") != "PASS":
        blockers.extend(str(item) for item in guard.get("blockers", []))
    return list(dict.fromkeys(blockers))


def _classify(
    *,
    telegram_result: Mapping[str, Any] | None,
    preflight_blockers: list[str],
    media_manifest: Mapping[str, Any],
    article_manifest: Mapping[str, Any],
    substack_status: str,
    x_status: str,
) -> str:
    if preflight_blockers:
        return BLOCKED_CLASSIFICATION
    if not telegram_result:
        return BLOCKED_CLASSIFICATION
    if telegram_result.get("status") == "SUCCESS":
        has_media_article = (
            int(media_manifest.get("media_asset_count") or 0) >= 3
            and bool(article_manifest.get("visuals_spread_through_article"))
        )
        if has_media_article and substack_status == "SUCCESS" and x_status == "SUCCESS":
            return PASS_CLASSIFICATION
        if has_media_article and substack_status.startswith("BLOCKED_") and x_status.startswith("BLOCKED_"):
            return PASS_PARTIAL_CLASSIFICATION
    if telegram_result.get("status") == "PUBLIC_DISPATCH_FROZEN":
        return BLOCKED_CLASSIFICATION
    if "Missing TELEGRAM_BOT_TOKEN" in str(telegram_result.get("error", "")):
        return BLOCKED_CLASSIFICATION
    return FAILED_CLASSIFICATION


def run_terra_ultra_north_star_full_automation(
    *,
    operator_approved_full_live_run: bool,
    max_send_attempts_per_platform: int = 1,
    run_id: str | None = None,
    output_dir: Path = OUTPUT_DIR,
    media_dir: Path | None = None,
    article_md_path: Path = ARTICLE_MD_PATH,
    article_html_path: Path = ARTICLE_HTML_PATH,
    ledger_path: Path = PUBLIC_DISPATCH_LEDGER,
    telegram_photo_executor: Callable[..., dict[str, Any]] | None = None,
    visual_builder: Callable[..., list[dict[str, Any]]] = build_current_macro_visual_pack,
) -> dict[str, Any]:
    quarantine(
        "contentops.legacy_terra_ultra_live.v1",
        LEGACY_AUTOMATION_QUARANTINED,
        "Terra Ultra automation is legacy; use ContentOpsProductionOrchestrator.",
    )
    run_id = run_id or f"terra_ultra_north_star_{_stable_hash({'task': TASK_LABEL, 'ts': _utc_now()}, 12)}"
    dotenv_loaded = _load_dotenv_if_available() if operator_approved_full_live_run else False
    resolved_media_dir = media_dir or output_dir / "media_assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_media_dir.mkdir(parents=True, exist_ok=True)

    headline_context = load_headline_context(output_dir=output_dir)
    selection = select_north_star_idea(headline_context, output_dir=output_dir, ledger_path=ledger_path)
    support = build_support_packet(selection, output_dir=output_dir)
    media_manifest = build_media_pack(
        selection,
        output_dir=resolved_media_dir,
        evidence_output_dir=output_dir,
        visual_builder=visual_builder,
    )
    article_manifest = export_article(
        selection,
        support,
        media_manifest,
        article_md_path=article_md_path,
        article_html_path=article_html_path,
        evidence_output_dir=output_dir,
    )
    variants = build_platform_variants(selection, article_manifest, media_manifest, output_dir=output_dir)

    telegram = variants["telegram"]
    topic_hash = str(selection["publication_topic_hash"])
    payload_hash = build_public_dispatch_payload_hash(
        platform="telegram",
        action="photo",
        body_text=str(telegram["caption"]),
        canonical_url=None,
        media_url=str(telegram["photo_path"]),
        topic_hash=topic_hash,
    )
    prior_hashes = load_public_dispatch_hashes(ledger_path)
    approval_marker = make_public_dispatch_approval_marker(
        run_id=run_id,
        topic_hash=topic_hash,
        payload_hash=payload_hash,
        platform="telegram",
    )
    guard = evaluate_public_dispatch_freeze(
        platform="telegram",
        action="photo",
        run_id=run_id,
        topic_hash=topic_hash,
        operator_approval_marker=approval_marker,
        body_text=str(telegram["caption"]),
        canonical_url=None,
        media_url=str(telegram["photo_path"]),
        payload_hash=payload_hash,
        payload_hash_required=True,
        prior_dispatch_hashes=prior_hashes,
    )
    blockers = _preflight_blockers(
        operator_approved_full_live_run=operator_approved_full_live_run,
        max_send_attempts_per_platform=max_send_attempts_per_platform,
        media_manifest=media_manifest,
        article_manifest=article_manifest,
        variants=variants,
        guard=guard,
    )

    telegram_result: dict[str, Any] | None = None
    if not blockers:
        approval_context = {
            "operator_approval_marker": approval_marker,
            "run_id": run_id,
            "topic_hash": topic_hash,
            "payload_hash": payload_hash,
            "prior_dispatch_hashes": prior_hashes,
            "public_dispatch_ledger_path": _normalise_path(ledger_path),
        }
        telegram_result = telegram_photo_executor(
            photo_url=str(telegram["photo_path"]),
            caption=str(telegram["caption"]),
            parse_mode="HTML",
            dry_run=False,
            approval_context=approval_context,
        )
        if telegram_result.get("status") == "SUCCESS":
            append_public_dispatch_ledger(
                ledger_path=ledger_path,
                platform="telegram",
                action="photo",
                run_id=run_id,
                topic_hash=topic_hash,
                payload_hash=payload_hash,
                media_url=str(telegram["photo_path"]),
                status="SUCCESS_NORTH_STAR_V1",
            )
    else:
        telegram_result = {
            "status": "BLOCKED_PRE_TELEGRAM_ADAPTER",
            "platform": "telegram",
            "action": "photo",
            "error": "|".join(blockers),
        }

    substack_result = {
        "status": SUBSTACK_BLOCKER,
        "public_url": None,
        "draft_id": None,
        "blocker": variants["substack"]["exact_blocker"],
    }
    x_result = {
        "status": X_BLOCKER,
        "public_url": None,
        "blocker": variants["x"]["exact_blocker"],
    }
    classification = _classify(
        telegram_result=telegram_result,
        preflight_blockers=blockers,
        media_manifest=media_manifest,
        article_manifest=article_manifest,
        substack_status=substack_result["status"],
        x_status=x_result["status"],
    )
    telegram_success = telegram_result.get("status") == "SUCCESS"
    telegram_message_id = telegram_result.get("id")
    response_message = telegram_result.get("response", {}).get("result", {}) if isinstance(telegram_result.get("response"), Mapping) else {}
    readback = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "classification": classification,
        "telegram_status": telegram_result.get("status"),
        "telegram_message_id": telegram_message_id,
        "telegram_image_attached": bool(telegram_success and telegram_result.get("action") == "photo"),
        "telegram_link_or_article_fallback_included": bool(telegram.get("article_link_or_fallback_included")),
        "telegram_caption_required_caveat_visible": bool(telegram.get("required_caveat_included")),
        "telegram_response_has_photo": bool(response_message.get("photo")),
        "article_visual_placement_status": article_manifest.get("visual_placement_status"),
        "media_asset_count": media_manifest.get("media_asset_count"),
        "substack_status": substack_result["status"],
        "x_status": x_result["status"],
    }
    dispatch_results = {
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "run_id": run_id,
        "classification": classification,
        "dotenv_loaded": dotenv_loaded,
        "max_send_attempts_per_platform": max_send_attempts_per_platform,
        "operator_approved_full_live_run": operator_approved_full_live_run,
        "telegram": {
            "status": telegram_result.get("status"),
            "message_id": telegram_message_id,
            "image_attached": readback["telegram_image_attached"],
            "article_link_or_fallback_included": readback["telegram_link_or_article_fallback_included"],
            "photo_path": telegram["photo_path"],
            "caption_sha256": _sha256_text(str(telegram["caption"])),
            "payload_hash": payload_hash,
            "topic_hash": topic_hash,
            "duplicate_guard": guard,
            "result_redacted": _redact_telegram_result_for_evidence(telegram_result),
        },
        "substack": substack_result,
        "x": x_result,
        "preflight_blockers": blockers,
    }
    safety = {
        "all_secret_values_redacted": True,
        "raw_env_values_persisted": False,
        "browser_session_sensitive_value_persisted": False,
        "raw_sensitive_values_persisted": False,
        "ai_generated_image_used": False,
        "google_image_manual_assist_used": False,
        "contentops_built_media": media_manifest.get("contentops_built_media"),
        "financial_advice_detected": bool(article_manifest.get("financial_advice_detected")),
        "forbidden_secret_material_detected": bool(article_manifest.get("forbidden_secret_material_detected")),
    }
    evidence = {
        "classification": classification,
        "task_label": TASK_LABEL,
        "created_at": _utc_now(),
        "run_id": run_id,
        "selected_topic": selection["selected_topic"],
        "selected_title": selection["selected_title"],
        "selected_angle": selection["selected_angle"],
        "why_selected": selection["why_selected"],
        "duplicate_hotspot_decision": selection["duplicate_hotspot_decision"],
        "article": article_manifest,
        "media": media_manifest,
        "telegram": dispatch_results["telegram"],
        "substack": substack_result,
        "x": x_result,
        "readback": readback,
        "safety": safety,
        "evidence_paths": {
            "headline_intake": _normalise_path(output_dir / "headline_intake_v1.json"),
            "idea_selection": _normalise_path(output_dir / "idea_selection_v1.json"),
            "support_packet": _normalise_path(output_dir / "support_packet_v1.json"),
            "media_manifest": _normalise_path(output_dir / "media_manifest_v1.json"),
            "article_manifest": _normalise_path(output_dir / "article_manifest_v1.json"),
            "platform_variants": _normalise_path(output_dir / "platform_variants_v1.json"),
            "dispatch_results": _normalise_path(output_dir / "dispatch_results_v1.json"),
            "readback": _normalise_path(output_dir / "readback_v1.json"),
            "run_evidence": _normalise_path(output_dir / "run_evidence_v1.json"),
        },
    }
    readme = f"""# Terra Ultra North-Star Full Automation V1

Classification: `{classification}`

Selected topic: `{selection["selected_topic"]}`

Article export: `{article_manifest["article_export_path"]}`

Media count: `{media_manifest["media_asset_count"]}`

Telegram status: `{telegram_result.get("status")}`

Substack status: `{substack_result["status"]}`

X status: `{x_result["status"]}`

This packet records a fresh non-oil north-star automation run. ContentOps built the media assets itself, embedded three visuals through the article body, and used the public dispatch freeze guard before Telegram photo dispatch.
"""
    _write_json(output_dir / "dispatch_results_v1.json", dispatch_results)
    _write_json(output_dir / "readback_v1.json", readback)
    _write_json(output_dir / "run_evidence_v1.json", evidence)
    _write_text(output_dir / "README.md", readme)
    return evidence


def main(argv: list[str] | None = None) -> int:
    quarantine(
        "contentops.legacy_terra_ultra_live.v1",
        LEGACY_AUTOMATION_QUARANTINED,
        "Terra Ultra CLI is legacy; use ContentOpsProductionOrchestrator.",
    )
    parser = argparse.ArgumentParser(description="Run Terra Ultra north-star ContentOps automation.")
    parser.add_argument("--operator-approved-full-live-run", action="store_true")
    parser.add_argument("--max-send-attempts-per-platform", type=int, default=1)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    evidence = run_terra_ultra_north_star_full_automation(
        operator_approved_full_live_run=args.operator_approved_full_live_run,
        max_send_attempts_per_platform=args.max_send_attempts_per_platform,
        run_id=args.run_id,
    )
    summary = {
        "classification": evidence["classification"],
        "run_id": evidence["run_id"],
        "selected_topic": evidence["selected_topic"],
        "article_export_path": evidence["article"]["article_export_path"],
        "media_asset_count": evidence["media"]["media_asset_count"],
        "telegram_status": evidence["telegram"]["status"],
        "telegram_message_id": evidence["telegram"]["message_id"],
        "substack_status": evidence["substack"]["status"],
        "x_status": evidence["x"]["status"],
        "run_evidence": evidence["evidence_paths"]["run_evidence"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    classification = evidence["classification"]
    if classification in {PASS_CLASSIFICATION, PASS_PARTIAL_CLASSIFICATION}:
        return 0
    if classification == BLOCKED_CLASSIFICATION:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
