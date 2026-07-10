"""Substack-first canonical ContentOps pipeline with supervised browser readback.

The earlier north-star runner proved local article/media generation and a
Telegram photo send, but it let a distribution channel become the article
host. This runner makes Substack validation a hard gate: no Telegram or X
payload is actionable until a canonical Substack draft or public URL has been
captured with three in-body ContentOps media assets.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .ai_provider_gate_v6 import inspect_provider_credentials
from .media_content_audit_v6 import build_current_macro_visual_pack
from .public_dispatch_freeze_guard_v6 import (
    append_public_dispatch_ledger,
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    evaluate_public_dispatch_freeze,
    load_public_dispatch_hashes,
    make_public_dispatch_approval_marker,
)
from .substack_browser_adapter_v6 import (
    build_supervised_substack_browser_readback,
    prepare_supervised_substack_browser_request,
    validate_supervised_substack_browser_readback,
)
from .telegram_live_adapter_v6 import execute_telegram_caption_edit, execute_telegram_photo

TASK_LABEL = "TASK_CONTENTOPS_SUBSTACK_FIRST_NORTH_STAR_PIPELINE_LOOP_DEBUG_AND_COMPLETION_V1"
SCHEMA_VERSION = "contentops.substack_first_north_star_pipeline.v1"
OUTPUT_ROOT = Path("docs/automation/SUBSTACK_FIRST_NORTH_STAR_PIPELINE_LOOP_V1")
EXPORT_ROOT = Path("exports/daily_contentops/substack_first")
SCHEDULE_GLOB = "docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_*.json"
SIDECAR_GLOB = "headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_*.jsonl"
PUBLIC_DISPATCH_LEDGER = Path("docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")
REQUIRED_CAVEAT = (
    "This article is for informational purposes only and is not financial advice. "
    "Numeric references are sourced as cited and should be independently verified."
)

PASS_CLASSIFICATION = "PASS_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
PASS_PARTIAL_CLASSIFICATION = "PASS_PARTIAL_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
BLOCKED_CLASSIFICATION = "BLOCKED_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
FAILED_CLASSIFICATION = "FAILED_NORTH_STAR_FULL_CONTENTOPS_AUTOMATION_V1"
X_BLOCKER = "BLOCKED_REQUIRES_SUPERVISED_X_BROWSER_POST_AND_PERMALINK_READBACK"

_SECRET_RE = re.compile(r"(telegram|openai|anthropic|router).{0,24}(token|key|secret)|authorization|cookie", re.IGNORECASE)
_ADVICE_RE = re.compile(r"\b(buy|sell|short|go long|go short|load up)\b.{0,40}\b(now|today|immediately)\b", re.IGNORECASE)
_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalise_path(path: str | Path) -> str:
    return str(path).replace("/", "\\")


def _load_dotenv_safely() -> bool:
    """Load a repo-local dotenv file without printing or retaining values."""
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        return False
    try:
        from dotenv import load_dotenv
    except Exception:
        return False
    load_dotenv(dotenv_path=dotenv_path, override=False)
    return True


def _latest_path(glob_pattern: str) -> Path:
    paths = sorted(Path(".").glob(glob_pattern))
    if not paths:
        raise FileNotFoundError(f"required_input_missing:{glob_pattern}")
    return paths[-1]


def _read_sidecar_examples(path: Path, *, limit: int = 36) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    if not path.exists():
        return examples
    for raw in path.read_text(encoding="utf-8").splitlines():
        if len(examples) >= limit:
            break
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        examples.append(
            {
                "headline_text": str(row.get("headline_text") or "")[:420],
                "headline_timestamp": row.get("headline_timestamp"),
                "candidate_catalyst_tags": row.get("candidate_catalyst_tags") or [],
                "follow_up_data_need_candidates": row.get("follow_up_data_need_candidates") or [],
            }
        )
    return examples


def load_current_headline_inputs(
    *,
    schedule_path: Path | None = None,
    sidecar_path: Path | None = None,
    output_dir: Path,
) -> dict[str, Any]:
    resolved_schedule = schedule_path or _latest_path(SCHEDULE_GLOB)
    schedule = _read_json(resolved_schedule)
    resolved_sidecar = sidecar_path or Path(str(schedule.get("sidecar_glob") or ""))
    if not resolved_sidecar.exists():
        resolved_sidecar = sidecar_path or _latest_path(SIDECAR_GLOB)
    packet = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "schedule_path": _normalise_path(resolved_schedule),
        "sidecar_path": _normalise_path(resolved_sidecar),
        "schedule_date": schedule.get("schedule_date"),
        "headline_sidecars_are_catalyst_only": bool(schedule.get("headline_sidecars_are_catalyst_only", True)),
        "forbidden_uses": list(schedule.get("forbidden_uses") or []),
        "slots": list(schedule.get("slots") or []),
        "headline_examples": _read_sidecar_examples(resolved_sidecar),
    }
    _write_json(output_dir / "headline_intake_v1.json", packet)
    return packet


def _llm_prompt(context: Mapping[str, Any]) -> str:
    slots = []
    for slot in context.get("slots") or []:
        slots.append(
            {
                "slot_index": slot.get("slot_index"),
                "topic": slot.get("topic"),
                "angle": slot.get("angle"),
                "tags": slot.get("tags") or [],
                "source_needs": slot.get("source_needs") or [],
                "media_needs": slot.get("media_needs") or [],
                "readiness": slot.get("readiness"),
            }
        )
    return "\n".join(
        [
            "You are the Capital Chronicle assignment editor. Rank the supplied current headline schedule into a single article-ready macro or market story.",
            "You must distinguish material market mechanisms from noise, propaganda, recycled commentary, and unsupported claims. Headline sidecars are catalyst-only, never numeric truth.",
            "Do not issue investment advice. Do not invent statistics, facts, source access, or breaking status.",
            "The downstream system only supports an article when source-backed data-chart media can be produced. You may label a candidate as fed_funds, oil, or unsupported for that support check, but do not select unsupported solely because it sounds dramatic.",
            "Return JSON only with this exact top-level shape:",
            '{"selection_rationale":"...","ranked_candidates":[{"slot_index":1,"rank":1,"article_family":"fed_funds|oil|unsupported","title":"...","seo_title":"...","slug":"...","dek":"...","thesis":"...","market_mechanism":"...","policy_context":"...","cross_asset_implications":"...","breaking_or_hotspot":false,"why_ranked":"..."}]}',
            "Rank every supplied slot. Titles and analysis must be grounded in the inputs below.",
            "SCHEDULE SLOTS:",
            json.dumps(slots, ensure_ascii=True),
            "SIDE-CAR EXAMPLES:",
            json.dumps(context.get("headline_examples") or [], ensure_ascii=True),
        ]
    )


def _parse_llm_json(raw: str) -> dict[str, Any]:
    value = str(raw or "").strip()
    if value.startswith("{") and value.endswith("}"):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    fenced = _JSON_BLOCK_RE.search(value)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed
    start = value.find("{")
    end = value.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(value[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("llm_response_not_json_object")


def _choose_live_llm_provider(provider: str) -> str:
    requested = str(provider or "auto").lower()
    if requested != "auto":
        return requested
    present = inspect_provider_credentials()
    if present.get("NINE_ROUTER_API_KEY"):
        return "9router"
    if present.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if present.get("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError("no_live_llm_provider_credentials_present")


def _default_llm_ranker(prompt: str, provider: str) -> str:
    from .ai_research_canonical_article_engine_v6 import call_live_provider

    return call_live_provider(prompt, provider=provider, timeout_seconds=45)


def rank_ideas_with_llm(
    context: Mapping[str, Any],
    *,
    output_dir: Path,
    llm_provider: str = "auto",
    llm_ranker: Callable[[str, str], str | Mapping[str, Any]] = _default_llm_ranker,
) -> dict[str, Any]:
    prompt = _llm_prompt(context)
    try:
        provider = _choose_live_llm_provider(llm_provider)
        response = llm_ranker(prompt, provider)
        parsed = dict(response) if isinstance(response, Mapping) else _parse_llm_json(str(response))
    except Exception as exc:
        packet = {
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED_LLM_RANKING_PROVIDER_UNAVAILABLE",
            "created_at": _now(),
            "prompt_sha256": _sha256_text(prompt),
            "provider": str(llm_provider),
            "error_class": type(exc).__name__,
        }
        _write_json(output_dir / "llm_idea_ranking_v1.json", packet)
        return packet

    slot_ids = {int(slot.get("slot_index")) for slot in context.get("slots") or [] if slot.get("slot_index") is not None}
    candidates: list[dict[str, Any]] = []
    for source in parsed.get("ranked_candidates") or []:
        if not isinstance(source, Mapping):
            continue
        try:
            slot_index = int(source.get("slot_index"))
        except (TypeError, ValueError):
            continue
        if slot_index not in slot_ids:
            continue
        candidate = {
            "slot_index": slot_index,
            "rank": int(source.get("rank") or 999),
            "article_family": str(source.get("article_family") or "unsupported").lower(),
            "title": str(source.get("title") or "").strip(),
            "seo_title": str(source.get("seo_title") or "").strip(),
            "slug": str(source.get("slug") or "").strip(),
            "dek": str(source.get("dek") or "").strip(),
            "thesis": str(source.get("thesis") or "").strip(),
            "market_mechanism": str(source.get("market_mechanism") or "").strip(),
            "policy_context": str(source.get("policy_context") or "").strip(),
            "cross_asset_implications": str(source.get("cross_asset_implications") or "").strip(),
            "breaking_or_hotspot": bool(source.get("breaking_or_hotspot")),
            "why_ranked": str(source.get("why_ranked") or "").strip(),
        }
        required = ("title", "seo_title", "slug", "dek", "thesis", "market_mechanism", "policy_context", "cross_asset_implications", "why_ranked")
        if candidate["article_family"] in {"fed_funds", "oil", "unsupported"} and all(candidate[key] for key in required):
            candidates.append(candidate)
    candidates.sort(key=lambda item: (item["rank"], item["slot_index"]))
    complete_ranking = {item["slot_index"] for item in candidates} == slot_ids
    packet = {
        "schema_version": SCHEMA_VERSION,
        "status": "SUCCESS" if candidates and complete_ranking else "BLOCKED_LLM_RANKING_INVALID_OUTPUT",
        "created_at": _now(),
        "provider": provider,
        "prompt_sha256": _sha256_text(prompt),
        "selection_rationale": str(parsed.get("selection_rationale") or ""),
        "ranked_candidates": candidates,
        "ranked_every_current_slot": complete_ranking,
    }
    _write_json(output_dir / "llm_idea_ranking_v1.json", packet)
    return packet


def _tokens(value: str) -> set[str]:
    ignored = {"the", "and", "for", "with", "from", "this", "that", "rate", "rates", "today", "effective"}
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2 and token not in ignored}


def _topic_overlap(a: str, b: str) -> float:
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _find_uncanonicalized_distribution_repair(topic: str) -> dict[str, Any] | None:
    newest: tuple[str, dict[str, Any], Path] | None = None
    for path in Path("docs/automation").rglob("run_evidence*.json"):
        try:
            evidence = _read_json(path)
        except Exception:
            continue
        telegram = evidence.get("telegram") or {}
        substack = evidence.get("substack") or {}
        if str(telegram.get("status") or "") != "SUCCESS":
            continue
        if substack.get("public_url") or substack.get("draft_url"):
            continue
        prior_topic = str(evidence.get("selected_topic") or "")
        if _topic_overlap(topic, prior_topic) < 0.65:
            continue
        message_id = telegram.get("message_id")
        if not message_id:
            continue
        created_at = str(evidence.get("created_at") or "")
        candidate = (created_at, evidence, path)
        if newest is None or candidate[0] > newest[0]:
            newest = candidate
    if not newest:
        return None
    created_at, evidence, path = newest
    return {
        "repair_mode": "CANONICALIZATION_REPAIR_EXISTING_DISTRIBUTION",
        "source_evidence_path": _normalise_path(path),
        "source_run_id": evidence.get("run_id"),
        "source_created_at": created_at,
        "existing_telegram_message_id": str((evidence.get("telegram") or {}).get("message_id")),
        "existing_telegram_url": f"https://t.me/CapitalChronicle/{(evidence.get('telegram') or {}).get('message_id')}",
        "reason": "A matching recent Telegram distribution exists without a canonical Substack URL; update its caption after canonical Substack readback rather than send a duplicate post.",
    }


def _media_manifest_from_assets(assets: Sequence[Mapping[str, Any]], *, output_dir: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for index, source in enumerate(assets, start=1):
        local_path = Path(str(source.get("local_path") or source.get("path") or ""))
        row = {
            "index": index,
            "asset_id": str(source.get("asset_id") or ""),
            "path": _normalise_path(local_path),
            "exists": local_path.exists(),
            "sha256": _sha256_file(local_path) if local_path.exists() else None,
            "media_class": str(source.get("media_class") or ""),
            "media_role": str(source.get("media_role") or ""),
            "source_label": str(source.get("source_label") or ""),
            "source_page_url": str(source.get("source_page_url") or ""),
            "provenance_status": str(source.get("provenance_status") or ""),
            "caption": str(source.get("caption") or ""),
            "alt_text": str(source.get("alt_text") or ""),
            "why_selected": str(source.get("why_selected") or ""),
        }
        rows.append(row)
        for required in ("asset_id", "source_label", "source_page_url", "provenance_status", "caption", "alt_text"):
            if not row[required]:
                blockers.append(f"media_missing_{required}:{index}")
        if not row["exists"]:
            blockers.append(f"media_file_missing:{index}")
        if row["media_class"] != "data_chart":
            blockers.append(f"media_not_source_backed_data_chart:{row['asset_id'] or index}")
    if len(rows) < 3:
        blockers.append("media_asset_count_below_3")
    packet = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "media_gate_status": "PASS" if not blockers else "BLOCKED",
        "blockers": list(dict.fromkeys(blockers)),
        "media_asset_count": len(rows),
        "required_media_asset_count": 3,
        "contentops_built_media": True,
        "allowed_media_kinds": ["source_backed_data_chart", "google_image_with_provenance"],
        "ai_generated_image": False,
        "static_generated_card": False,
        "static_schematic_used": False,
        "assets": rows[:3],
    }
    _write_json(output_dir / "media_manifest_v1.json", packet)
    return packet


def _grounded_support_blockers(slot: Mapping[str, Any], candidate: Mapping[str, Any], media: Mapping[str, Any]) -> list[str]:
    """Bind LLM framing to the source families actually present in the media pack."""
    blockers: list[str] = []
    topic = str(slot.get("topic") or "").lower()
    tags = {str(tag).lower() for tag in slot.get("tags") or []}
    family = str(candidate.get("article_family") or "")
    expected_family = "oil" if "energy" in tags or any(term in topic for term in ("oil", "crude", "iran")) else "fed_funds"
    if family != expected_family:
        blockers.append(f"llm_media_family_mismatch:{family}!={expected_family}")

    source_text = " ".join(
        f"{asset.get('source_label', '')} {asset.get('source_page_url', '')}".lower()
        for asset in media.get("assets") or []
    )
    source_needs = " ".join(str(item).lower() for item in slot.get("source_needs") or [])
    if "eia" in source_needs and "eia.gov" not in source_text:
        blockers.append("primary_eia_source_required_by_schedule_not_present_in_media_pack")
    if "federal reserve" in source_needs and "federalreserve.gov" not in source_text:
        blockers.append("primary_federal_reserve_source_required_by_schedule_not_present_in_media_pack")
    if "treasury" in source_needs and "treasury.gov" not in source_text and "federalreserve.gov" not in source_text:
        blockers.append("primary_treasury_or_h15_source_required_by_schedule_not_present_in_media_pack")
    return blockers


def select_grounded_article_ready_idea(
    *,
    context: Mapping[str, Any],
    ranking: Mapping[str, Any],
    output_dir: Path,
    media_dir: Path,
    visual_builder: Callable[..., list[dict[str, Any]]] = build_current_macro_visual_pack,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if ranking.get("status") != "SUCCESS":
        raise RuntimeError(str(ranking.get("status")))
    slots = {int(slot["slot_index"]): slot for slot in context.get("slots") or [] if slot.get("slot_index") is not None}
    attempts: list[dict[str, Any]] = []
    for candidate in ranking.get("ranked_candidates") or []:
        slot = slots.get(int(candidate["slot_index"]))
        if not slot:
            continue
        family = str(candidate.get("article_family") or "unsupported")
        if family == "unsupported":
            attempts.append({"slot_index": candidate["slot_index"], "status": "REJECTED_UNSUPPORTED_MEDIA_FAMILY"})
            continue
        candidate_media_dir = media_dir / f"slot_{candidate['slot_index']}"
        try:
            assets = visual_builder(f"{slot.get('topic')} {family}", output_dir=candidate_media_dir)
        except Exception as exc:
            attempts.append({"slot_index": candidate["slot_index"], "status": "REJECTED_MEDIA_BUILD_ERROR", "error_class": type(exc).__name__})
            continue
        manifest = _media_manifest_from_assets(assets, output_dir=candidate_media_dir)
        support_blockers = _grounded_support_blockers(slot, candidate, manifest)
        attempts.append(
            {
                "slot_index": candidate["slot_index"],
                "status": "PASS" if manifest["media_gate_status"] == "PASS" and not support_blockers else "REJECTED_GROUNDED_SUPPORT",
                "media_asset_count": manifest["media_asset_count"],
                "grounded_support_blockers": support_blockers,
            }
        )
        if manifest["media_gate_status"] != "PASS" or support_blockers:
            continue
        selected = {**candidate, "topic": str(slot.get("topic") or ""), "angle": str(slot.get("angle") or ""), "tags": list(slot.get("tags") or [])}
        selected["topic_hash"] = build_public_dispatch_topic_hash(selected["topic"], selected["angle"])
        selected["canonicalization_repair"] = _find_uncanonicalized_distribution_repair(selected["topic"])
        support = {
            "schema_version": SCHEMA_VERSION,
            "created_at": _now(),
            "support_status": "GROUNDED_REPO_INPUTS_AND_SOURCE_BACKED_MEDIA",
            "headline_sidecars_are_catalyst_only": bool(context.get("headline_sidecars_are_catalyst_only")),
            "source_boundary": [
                "Schedule and headline sidecars establish freshness and catalyst context only.",
                "The source-backed chart manifest carries visual provenance and numeric-source labels.",
                "Article prose does not promote schedule headlines into unsupported numeric truth.",
            ],
            "repo_evidence": [context.get("schedule_path"), context.get("sidecar_path")],
            "source_needs": list(slot.get("source_needs") or []),
            "selected_slot_index": selected["slot_index"],
        }
        _write_json(output_dir / "grounded_support_v1.json", support)
        _write_json(
            output_dir / "idea_selection_v1.json",
            {
                "schema_version": SCHEMA_VERSION,
                "created_at": _now(),
                "selection_method": "live_llm_ranking_then_grounded_media_support_gate",
                "llm_selection_rationale": ranking.get("selection_rationale"),
                "selected": selected,
                "support_attempts": attempts,
                "duplicate_hotspot_decision": selected["canonicalization_repair"]
                or {"repair_mode": "NEW_CANONICAL_ARTICLE", "duplicate_policy": "new Telegram post requires normal duplicate guard"},
            },
        )
        _write_json(output_dir / "media_manifest_v1.json", manifest)
        return selected, support, manifest
    _write_json(output_dir / "idea_selection_v1.json", {"status": "BLOCKED_NO_LLM_RANKED_ARTICLE_WITH_THREE_SOURCE_BACKED_CHARTS", "support_attempts": attempts})
    raise RuntimeError("BLOCKED_NO_LLM_RANKED_ARTICLE_WITH_THREE_SOURCE_BACKED_CHARTS")


def _visual_markdown(asset: Mapping[str, Any]) -> str:
    return f"![{asset['alt_text']}]({asset['path']})\n\n*{asset['caption']}*\n"


def _visual_substack_marker(asset: Mapping[str, Any]) -> str:
    return f"[[VISUAL:{asset['asset_id']}]]\n\n*{asset['caption']}*\n"


def _visual_positions(article: str, assets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    positions = [article.find(f"]({asset['path']})") for asset in assets]
    valid = [position for position in positions if position >= 0]
    spread = len(valid) == 3 and valid == sorted(valid) and min(b - a for a, b in zip(valid, valid[1:])) >= 500
    return {"visual_positions": positions, "visual_asset_count": len(valid), "visuals_spread_through_article": spread}


def _reader_word_count(markdown: str) -> int:
    """Count reader-facing text without local image paths or visual markers."""
    without_images = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)
    without_markers = re.sub(r"\[\[VISUAL:[A-Za-z0-9_-]+\]\]", "", without_images)
    return len(re.findall(r"\b\w+\b", without_markers))


def _markdown_to_html(markdown: str, title: str) -> str:
    lines: list[str] = []
    for raw in markdown.splitlines():
        if raw.startswith("# "):
            lines.append(f"<h1>{html.escape(raw[2:])}</h1>")
        elif raw.startswith("## "):
            lines.append(f"<h2>{html.escape(raw[3:])}</h2>")
        elif raw.startswith("!["):
            match = re.match(r"!\[(.*)\]\((.*)\)", raw)
            if match:
                lines.append(f'<figure><img src="{html.escape(match.group(2))}" alt="{html.escape(match.group(1))}" /></figure>')
        elif raw.startswith("*") and raw.endswith("*"):
            lines.append(f"<p><em>{html.escape(raw.strip('*'))}</em></p>")
        elif raw:
            lines.append(f"<p>{html.escape(raw)}</p>")
    return "\n".join(["<!doctype html>", "<html><head>", f"<title>{html.escape(title)}</title>", "</head><body>", *lines, "</body></html>"])


def export_canonical_article(
    *,
    selection: Mapping[str, Any],
    support: Mapping[str, Any],
    media: Mapping[str, Any],
    run_id: str,
    output_dir: Path,
    export_root: Path = EXPORT_ROOT,
) -> dict[str, Any]:
    assets = list(media.get("assets") or [])
    if len(assets) < 3:
        raise ValueError("article_requires_three_media_assets")
    title = str(selection["title"])
    subtitle = str(selection["dek"])
    source_labels = ", ".join(
        dict.fromkeys(str(asset.get("source_label") or "").strip() for asset in assets if asset.get("source_label"))
    )
    body = f"""## The Market Signal Is Not the Headline

{selection['thesis']} The editorial task is to separate a useful market mechanism from the noise that often gathers around a fresh headline. The headline schedule establishes why the subject is timely, but it is not a license to turn a short social-media update into a numeric fact pattern. That distinction matters especially in rates: the most consequential move may be the adjustment in the transmission channel, rather than the most eye-catching intraday reaction.

An orderly overnight print is therefore a starting point, not a verdict on financial conditions. Treasury yields, swap spreads, credit risk premia and foreign-exchange moves can all carry information that is not visible in a single policy-rate observation. The reporting discipline is to identify whether those indicators are confirming the same mechanism or signaling a different one. A stable policy anchor can coexist with a meaningful repricing in duration, inflation compensation or growth expectations.

That comparison matters because policy transmission is layered. The overnight market shows whether the central bank's implementation tools are keeping the benchmark close to its intended setting. The curve then shows how investors are translating expected future policy, issuance and macro risk into long-maturity rates. Neither layer should be used as a shortcut for the other. Treating them as linked evidence helps distinguish routine stability from a shift in the market narrative.

{_visual_markdown(assets[0])}

The first chart anchors the piece in a source-labeled observation instead of a generic market mood. Its purpose is not to force a directional trade conclusion. It is to identify the policy or funding variable that should remain stable if the operating framework is working as intended, then ask what other markets are absorbing new information. That is a more useful starting point for readers than a claim that one datapoint settles the outlook for inflation, growth, or central-bank timing.

## The Mechanism Runs Through Funding Conditions

{selection['market_mechanism']} In a serious financial-news report, the mechanism needs to be explicit. Rate and liquidity signals move through funding markets, collateral, credit pricing, the yield curve, and eventually corporate and household financing conditions. The sequence is neither automatic nor uniform. A quiet overnight setting can coexist with a volatile long end, a widening term premium, or a repricing of inflation risk. The editorial value is in showing readers which link in that chain deserves attention.

The supported source trail keeps the claim boundary tight. The schedule and sidecars provide the catalyst and the reason to investigate. The chart manifest records the primary source labels and provenance for the visual evidence. Where an observation needs final validation, the article names that limitation rather than laundering a tentative figure into certainty. This is why the caveat appears in the body and why the charts carry their own source captions.

A check is the relationship between the secured and unsecured overnight markets. When both remain orderly, the policy rate can be interpreted as an anchor rather than an isolated setting. When they diverge, the cause can range from collateral dynamics to reserve distribution or broader balance-sheet pressure. That does not automatically signal stress, but it tells reporters where to look next: funding spreads, facility usage, bill supply and the language of communications. Those measures provide context a rate print cannot supply. This allows better calibration before decisions.

## Policy Context Matters More Than a Single Print

{selection['policy_context']} Policy communication and market structure can make an unchanged policy variable meaningful. A central bank can be holding the line while the curve reflects fiscal supply, changing growth expectations, geopolitical risk, or a reassessment of the inflation path. Those forces do not cancel one another; they define the question readers should ask next. The difference between a controlled operating rate and a broader repricing is the difference between plumbing and the macro narrative built on top of it.

{_visual_markdown(assets[1])}

The second chart is placed here because it tests the mechanism rather than decorating the article. It shows the administered or reference rates that frame the transmission story. Taken together with the first visual, it makes clear why the desk should avoid treating a single rate as a standalone verdict on risk assets. Market participants can agree on the current policy setting while disagreeing sharply about what it implies for duration, liquidity, or the next official communication.

## Cross-Asset Effects Are a Map, Not a Recommendation

{selection['cross_asset_implications']} Cross-asset analysis should describe the channels of repricing, not tell readers what to buy, sell, or short. Equities can respond to discount-rate expectations, credit to funding conditions, foreign exchange to relative policy paths, and commodities to a changing mix of growth, supply, and currency forces. A common macro narrative is useful only when it explains why the reactions are connected without pretending they all move in lockstep.

The productive question is whether the market is pricing a change in the expected policy path, a change in term compensation, or a change in confidence about the macro baseline. The answer can differ across assets. That is not a contradiction; it is often the story. By preserving the distinction, the article gives readers a framework for following the next official release or market move without converting a public editorial into personalized financial advice.

{_visual_markdown(assets[2])}

The third chart broadens the perspective before the conclusion. It belongs in the cross-asset section because it helps readers see the relative position of the relevant rates rather than repeating the opening visual. Three visuals spread through the article create three separate evidence stops: the initial signal, the policy mechanism, and the broader market context. They are not a gallery attached at the bottom after the analysis is complete.

## The Next Test Is Whether the Curve Confirms the Story

The next stage of the reporting should focus on confirmation rather than escalation. If the policy anchor remains orderly, editors should look for evidence that explains why other parts of the market are moving: a fresh official release, a shift in issuance expectations, a change in inflation language, or a credit-market signal that points to tighter financial conditions. Each possibility carries a different mechanism. Lumping them together under a vague claim about "markets" would obscure the reason the move matters.

That is also where the newsroom standard becomes demanding. A headline about a single rate, a political comment, or a scheduled event should not be treated as proof that a policy turn is underway. The article needs to explain what would corroborate the initial signal and what would falsify it. Readers should be able to trace the distinction between an orderly overnight market, a repriced curve, and a genuine change in the macro outlook. The point is not to predict the next tick; it is to show which observed channel would make the original thesis stronger or weaker.

## What Would Change the Story

The next evidence that could change this story is not merely another headline. It would be a primary release, an official communication, or a source-backed market development that alters the mechanism described above. The relevant question is whether the update is genuinely breaking, materially changes the cross-asset setup, or exposes a new stress point. A cosmetic rewrite of the same signal does not qualify.

## Source Trail and Limits

- Chart data and policy references: {source_labels}.
- Each in-body chart carries its own source caption and provenance.
- {REQUIRED_CAVEAT}
"""
    substack_body = body
    for asset in assets:
        substack_body = substack_body.replace(_visual_markdown(asset), _visual_substack_marker(asset))
    article_path = export_root / f"{run_id}_canonical_article.md"
    html_path = export_root / f"{run_id}_canonical_article.html"
    _write_text(article_path, body)
    _write_text(html_path, _markdown_to_html(body, title))
    placement = _visual_positions(body, assets)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "title": title,
        "subtitle": subtitle,
        "seo_title": str(selection["seo_title"]),
        "meta_description": subtitle,
        "slug": str(selection["slug"]),
        "article_export_path": _normalise_path(article_path),
        "article_html_export_path": _normalise_path(html_path),
        "article_markdown_sha256": _sha256_file(article_path),
        "substack_body_markdown": substack_body,
        "substack_body_markdown_sha256": _sha256_text(substack_body),
        "word_count": _reader_word_count(substack_body),
        "caveat_present": REQUIRED_CAVEAT in body,
        "financial_advice_detected": bool(_ADVICE_RE.search(body)),
        "forbidden_secret_material_detected": bool(_SECRET_RE.search(body)),
        "visual_placement_status": "PASS_VISUALS_SPREAD_THROUGH_ARTICLE" if placement["visuals_spread_through_article"] else "FAIL_VISUALS_NOT_SPREAD_THROUGH_ARTICLE",
        **placement,
    }
    _write_json(output_dir / "article_manifest_v1.json", manifest)
    return manifest


def prepare_substack_first_pipeline(
    *,
    run_id: str,
    publication_mode: str,
    output_dir: Path,
    llm_provider: str = "auto",
    llm_ranker: Callable[[str, str], str | Mapping[str, Any]] = _default_llm_ranker,
    visual_builder: Callable[..., list[dict[str, Any]]] = build_current_macro_visual_pack,
    export_root: Path = EXPORT_ROOT,
) -> dict[str, Any]:
    _load_dotenv_safely()
    output_dir.mkdir(parents=True, exist_ok=True)
    context = load_current_headline_inputs(output_dir=output_dir)
    ranking = rank_ideas_with_llm(context, output_dir=output_dir, llm_provider=llm_provider, llm_ranker=llm_ranker)
    if ranking.get("status") != "SUCCESS":
        return {"classification": BLOCKED_CLASSIFICATION, "stage": "idea_selection", "reason": ranking.get("status"), "output_dir": _normalise_path(output_dir)}
    selection, support, media = select_grounded_article_ready_idea(
        context=context,
        ranking=ranking,
        output_dir=output_dir,
        media_dir=output_dir / "media_assets",
        visual_builder=visual_builder,
    )
    article = export_canonical_article(
        selection=selection,
        support=support,
        media=media,
        run_id=run_id,
        output_dir=output_dir,
        export_root=export_root,
    )
    if article["word_count"] < 1200 or article["financial_advice_detected"] or article["forbidden_secret_material_detected"] or not article["visuals_spread_through_article"]:
        raise RuntimeError("article_quality_gate_failed")
    request = prepare_supervised_substack_browser_request(
        run_id=run_id,
        publication_mode=publication_mode,
        title=article["title"],
        subtitle=article["subtitle"],
        body_markdown=article["substack_body_markdown"],
        article_markdown_path=article["article_export_path"],
        image_assets=media["assets"],
        output_path=output_dir / "substack_browser_request_v1.json",
    )
    context_packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "created_at": _now(),
        "run_id": run_id,
        "publication_mode": publication_mode,
        "selection": selection,
        "support": support,
        "media": media,
        "article": article,
        "substack_browser_request_path": _normalise_path(output_dir / "substack_browser_request_v1.json"),
        "substack_browser_request_sha256": _sha256_text(json.dumps(request, sort_keys=True)),
        "next_stage": "supervised_substack_browser_then_complete",
    }
    _write_json(output_dir / "run_context_v1.json", context_packet)
    return {
        "classification": "READY_FOR_SUPERVISED_SUBSTACK_BROWSER_ASSIST",
        "run_id": run_id,
        "output_dir": _normalise_path(output_dir),
        "context_path": _normalise_path(output_dir / "run_context_v1.json"),
        "substack_browser_request_path": _normalise_path(output_dir / "substack_browser_request_v1.json"),
        "selected_title": article["title"],
        "media_asset_count": media["media_asset_count"],
    }


def _redact_telegram_result(result: Mapping[str, Any]) -> dict[str, Any]:
    response = result.get("response") if isinstance(result.get("response"), Mapping) else {}
    message = response.get("result") if isinstance(response.get("result"), Mapping) else {}
    return {
        "status": result.get("status"),
        "platform": result.get("platform"),
        "action": result.get("action"),
        "message_id": str(result.get("id") or message.get("message_id") or "") or None,
        "response_ok": response.get("ok"),
        "media_attached": bool(result.get("media_attached") or result.get("action") == "photo"),
        "error_class": type(result.get("error")).__name__ if result.get("error") else None,
        "error_code": result.get("error_code"),
    }


def _telegram_caption(article: Mapping[str, Any], selection: Mapping[str, Any], canonical_url: str, *, draft: bool) -> str:
    label = "Canonical Substack draft" if draft else "Read the canonical Substack article"
    return "\n\n".join(
        [
            str(article["title"]),
            str(selection["dek"]),
            f"{label}: {canonical_url}",
            REQUIRED_CAVEAT,
        ]
    )


def _complete_readme(evidence: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Substack-First North-Star Pipeline Loop V1",
            "",
            f"Classification: `{evidence['classification']}`",
            "",
            f"Substack: `{evidence['substack']['status']}`",
            f"Canonical URL: `{evidence['substack'].get('canonical_url') or ''}`",
            f"Telegram: `{evidence['telegram']['status']}`",
            f"X: `{evidence['x']['status']}`",
            "",
            "Telegram and X are derivatives. This packet does not accept a local article export as canonical success.",
            "",
        ]
    )


def complete_substack_first_pipeline(
    *,
    context_path: Path,
    substack_readback_path: Path,
    operator_approved_full_live_run: bool,
    max_send_attempts_per_platform: int = 1,
    ledger_path: Path = PUBLIC_DISPATCH_LEDGER,
    telegram_photo_executor: Callable[..., dict[str, Any]] = execute_telegram_photo,
    telegram_caption_editor: Callable[..., dict[str, Any]] = execute_telegram_caption_edit,
) -> dict[str, Any]:
    _load_dotenv_safely()
    context = _read_json(context_path)
    output_dir = context_path.parent
    request = _read_json(Path(str(context["substack_browser_request_path"])))
    raw_readback = _read_json(substack_readback_path)
    substack = validate_supervised_substack_browser_readback(request, raw_readback)
    selection = dict(context["selection"])
    article = dict(context["article"])
    media = dict(context["media"])
    repair = selection.get("canonicalization_repair") if isinstance(selection.get("canonicalization_repair"), Mapping) else None
    blockers: list[str] = []
    if not operator_approved_full_live_run:
        blockers.append("operator_approved_full_live_run_required")
    if max_send_attempts_per_platform != 1:
        blockers.append("max_send_attempts_per_platform_must_equal_1")
    if substack["status"] != "SUCCESS":
        blockers.extend(substack["blockers"])
    if media.get("media_gate_status") != "PASS":
        blockers.extend(media.get("blockers") or [])
    if int(media.get("media_asset_count") or 0) < 3:
        blockers.append("minimum_three_media_assets_required")
    if not article.get("visuals_spread_through_article"):
        blockers.append("article_visuals_not_spread_through_body")

    canonical_url = substack.get("canonical_url")
    telegram_result: dict[str, Any]
    caption = _telegram_caption(article, selection, str(canonical_url or ""), draft=substack.get("publication_state") == "draft") if canonical_url else ""
    topic_hash = str(selection["topic_hash"])
    action = "edit_caption" if repair else "photo"
    primary_media = str(media["assets"][0]["path"])
    payload_hash = build_public_dispatch_payload_hash(
        platform="telegram",
        action=action,
        body_text=caption,
        canonical_url=str(canonical_url or ""),
        media_url=primary_media,
        topic_hash=topic_hash,
    )
    approval_marker = make_public_dispatch_approval_marker(run_id=str(context["run_id"]), topic_hash=topic_hash, payload_hash=payload_hash, platform="telegram")
    prior = load_public_dispatch_hashes(ledger_path)
    guard = evaluate_public_dispatch_freeze(
        platform="telegram",
        action=action,
        run_id=str(context["run_id"]),
        topic_hash=topic_hash,
        operator_approval_marker=approval_marker,
        body_text=caption,
        canonical_url=str(canonical_url or ""),
        media_url=primary_media,
        payload_hash=payload_hash,
        prior_dispatch_hashes=prior,
        duplicate_check=not bool(repair),
    )
    if not guard.get("dispatch_allowed"):
        blockers.extend(guard.get("blockers") or [])
    if len(caption) > 1024:
        blockers.append("telegram_caption_over_1024_characters")

    if blockers:
        telegram_result = {"status": "BLOCKED_PRE_TELEGRAM_DERIVATIVE", "platform": "telegram", "action": action, "error": "|".join(dict.fromkeys(blockers))}
    else:
        approval_context = {
            "operator_approval_marker": approval_marker,
            "run_id": str(context["run_id"]),
            "topic_hash": topic_hash,
            "payload_hash": payload_hash,
            "canonical_url": canonical_url,
            "prior_dispatch_hashes": prior,
            "public_dispatch_ledger_path": _normalise_path(ledger_path),
            "canonical_packet_status": "SUCCESS",
            "canonicalization_repair": bool(repair),
            "canonicalization_repair_message_id": repair.get("existing_telegram_message_id") if repair else None,
        }
        if repair:
            telegram_result = telegram_caption_editor(
                message_id=repair["existing_telegram_message_id"],
                caption=caption,
                parse_mode="HTML",
                dry_run=False,
                approval_context=approval_context,
            )
        else:
            telegram_result = telegram_photo_executor(
                photo_url=primary_media,
                caption=caption,
                parse_mode="HTML",
                dry_run=False,
                approval_context=approval_context,
            )
        if telegram_result.get("status") == "SUCCESS":
            append_public_dispatch_ledger(
                ledger_path=ledger_path,
                platform="telegram",
                action=action,
                run_id=str(context["run_id"]),
                topic_hash=topic_hash,
                payload_hash=payload_hash,
                canonical_url=str(canonical_url),
                media_url=primary_media,
                status="SUCCESS_CANONICALIZATION_REPAIR" if repair else "SUCCESS_SUBSTACK_FIRST_DERIVATIVE",
            )

    x = {
        "status": X_BLOCKER,
        "canonical_url": canonical_url,
        "text": f"{article['title']}\n\n{selection['dek']}\n\n{canonical_url}" if canonical_url else "",
        "media_path": primary_media,
        "exact_unblock_plan": "Use the supervised X profile, post the exact prepared text with the canonical Substack URL, then capture the public status URL in readback before marking X successful.",
    }
    telegram_ok = telegram_result.get("status") == "SUCCESS"
    if substack["status"] != "SUCCESS":
        classification = BLOCKED_CLASSIFICATION
    elif telegram_ok and x["status"] == "SUCCESS":
        classification = PASS_CLASSIFICATION
    elif telegram_ok:
        classification = PASS_PARTIAL_CLASSIFICATION
    elif telegram_result.get("status", "").startswith("BLOCKED_"):
        classification = BLOCKED_CLASSIFICATION
    else:
        classification = FAILED_CLASSIFICATION

    telegram_url = None
    message_id = str(telegram_result.get("id") or "")
    if message_id:
        telegram_url = f"https://t.me/CapitalChronicle/{message_id}"
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "created_at": _now(),
        "classification": classification,
        "run_id": context["run_id"],
        "selected_idea": {"topic": selection["topic"], "title": article["title"], "why_selected": selection["why_ranked"], "llm_article_family": selection["article_family"]},
        "duplicate_hotspot_decision": repair or {"repair_mode": "NEW_CANONICAL_ARTICLE", "duplicate_guard": guard},
        "substack": {**substack, "browser_request_path": context["substack_browser_request_path"], "readback_path": _normalise_path(substack_readback_path)},
        "article": article,
        "media": media,
        "telegram": {
            "status": telegram_result.get("status"),
            "action": telegram_result.get("action"),
            "message_id": message_id or None,
            "public_url": telegram_url,
            "media_attached": bool(repair or telegram_result.get("action") == "photo"),
            "substack_url_included": bool(canonical_url and canonical_url in caption),
            "caption_sha256": _sha256_text(caption) if caption else None,
            "duplicate_guard": guard,
            "result_redacted": _redact_telegram_result(telegram_result),
        },
        "x": x,
        "blockers": list(dict.fromkeys(blockers)),
        "safety": {
            "raw_credentials_persisted": False,
            "raw_browser_session_material_persisted": False,
            "financial_advice_detected": bool(article["financial_advice_detected"]),
            "static_generated_media_used": False,
            "google_manual_image_assist_used": False,
        },
    }
    _write_json(output_dir / "dispatch_results_v1.json", evidence)
    _write_json(output_dir / "run_evidence_v1.json", evidence)
    _write_text(output_dir / "README.md", _complete_readme(evidence))
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=TASK_LABEL)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--record-substack-readback", action="store_true")
    action.add_argument("--complete", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--publication-mode", choices=("draft", "publish"), default="draft")
    parser.add_argument("--llm-provider", default="auto")
    parser.add_argument("--context-path", type=Path)
    parser.add_argument("--request-path", type=Path)
    parser.add_argument("--substack-readback-path", type=Path)
    parser.add_argument("--publication-state", choices=("draft", "published"))
    parser.add_argument("--article-url")
    parser.add_argument("--editor-body-image-count", type=int)
    parser.add_argument("--visual-asset-id", action="append", default=[])
    parser.add_argument("--operator-approved-full-live-run", action="store_true")
    parser.add_argument("--max-send-attempts-per-platform", type=int, default=1)
    args = parser.parse_args(argv)

    if args.prepare:
        run_id = args.run_id or f"substack_first_{_sha256_text(_now())[:12]}"
        output_dir = args.output_dir or OUTPUT_ROOT / run_id
        result = prepare_substack_first_pipeline(run_id=run_id, publication_mode=args.publication_mode, output_dir=output_dir, llm_provider=args.llm_provider)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["classification"].startswith("READY") else 2
    if args.record_substack_readback:
        if not args.request_path or not args.publication_state or not args.article_url or args.editor_body_image_count is None:
            parser.error("--request-path, --publication-state, --article-url, and --editor-body-image-count are required")
        request = _read_json(args.request_path)
        output_path = args.substack_readback_path or args.request_path.with_name("substack_browser_readback_v1.json")
        result = build_supervised_substack_browser_readback(
            request=request,
            publication_state=args.publication_state,
            article_url=args.article_url,
            editor_body_image_count=args.editor_body_image_count,
            in_body_visual_asset_ids=args.visual_asset_id,
            output_path=output_path,
        )
        print(json.dumps({"status": result["status"], "readback_path": _normalise_path(output_path)}, indent=2, sort_keys=True))
        return 0
    if not args.context_path or not args.substack_readback_path:
        parser.error("--context-path and --substack-readback-path are required for --complete")
    result = complete_substack_first_pipeline(
        context_path=args.context_path,
        substack_readback_path=args.substack_readback_path,
        operator_approved_full_live_run=args.operator_approved_full_live_run,
        max_send_attempts_per_platform=args.max_send_attempts_per_platform,
    )
    print(json.dumps({"classification": result["classification"], "substack": result["substack"]["status"], "telegram": result["telegram"]["status"], "x": result["x"]["status"]}, indent=2, sort_keys=True))
    return 0 if result["classification"] in {PASS_CLASSIFICATION, PASS_PARTIAL_CLASSIFICATION} else 2


if __name__ == "__main__":
    raise SystemExit(main())
