"""Prepare-only integration of evidence, freshness, visual, and editorial gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .cc_evidence_bridge_v2 import build_evidence_packet_from_cc_root, validate_evidence_packet
from .editorial_review_orchestrator_v2 import run_editorial_review
from .editorial_visual_research_v2 import GoogleImageSearchGroundingProvider, evaluate_visual_composition
from .freshness_market_state_v2 import evaluate_freshness
from .source_capability_registry_v2 import load_source_capability_registry, resolve_story_capabilities


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _default_reviewer(_role: str, _context: Mapping[str, Any]) -> dict[str, Any]:
    return {"decision": "PASS", "publication_authority": False, "review_scope": "fixture_or_local_structured_review"}


def _load_evidence_packet(
    *,
    capital_chronicle_root: str | Path | None,
    evidence_packet_path: str | Path | None,
    as_of_utc: str | None,
) -> dict[str, Any]:
    if bool(capital_chronicle_root) == bool(evidence_packet_path):
        raise ValueError("exactly_one_evidence_input_required")
    return (
        build_evidence_packet_from_cc_root(capital_chronicle_root, as_of_utc=as_of_utc)
        if capital_chronicle_root
        else json.loads(Path(str(evidence_packet_path)).read_text(encoding="utf-8"))
    )


def evaluate_assignment_readiness(packet: Mapping[str, Any]) -> dict[str, Any]:
    rejection_reasons = list(packet.get("blockers") or [])
    if not packet.get("headlines"):
        rejection_reasons.append("no_governed_headline_candidates")
    if not any(row.get("source_url") for row in (packet.get("official_source_documents") or [])):
        rejection_reasons.append("no_public_official_source_url")
    if not any(row.get("public_claim_allowed") for row in (packet.get("events") or [])):
        rejection_reasons.append("no_event_with_public_claim_permission")
    if not any(row.get("public_claim_allowed") for row in (packet.get("numeric_claims") or [])):
        rejection_reasons.append("no_numeric_claim_with_public_claim_permission")
    return {
        "schema_version": "contentops.generic_assignment_readiness.v1",
        "decision": "PASS" if not rejection_reasons else "BLOCK",
        "selected_story": None,
        "candidate_count": len(packet.get("headlines") or []),
        "rejection_reasons": list(dict.fromkeys(rejection_reasons)),
        "selection_method": "governed_packet_only_no_topic_fallback",
    }


def run_generic_database_preflight(
    *,
    output_dir: Path,
    capital_chronicle_root: str | Path | None = None,
    evidence_packet_path: str | Path | None = None,
    as_of_utc: str | None = None,
) -> dict[str, Any]:
    packet = _load_evidence_packet(
        capital_chronicle_root=capital_chronicle_root,
        evidence_packet_path=evidence_packet_path,
        as_of_utc=as_of_utc,
    )
    packet["validation_blockers"] = validate_evidence_packet(packet)
    assignment = evaluate_assignment_readiness(packet)
    blockers = list(assignment["rejection_reasons"])
    blockers.extend(packet["validation_blockers"])
    result = {
        "schema_version": "contentops.generic_database_preflight.v1",
        "classification": (
            "PASS_GENERIC_DATABASE_PREFLIGHT"
            if not blockers
            else "BLOCKED_GENERIC_DATABASE_PREFLIGHT"
        ),
        "publication_eligible": not blockers,
        "public_write_performed": False,
        "browser_or_cdp_used": False,
        "platform_adapter_called": False,
        "video_or_tiktok_adapter_called": False,
        "assignment_decision_path": str(output_dir / "generic_assignment_readiness_v1.json"),
        "evidence_packet_path": str(output_dir / "capital_chronicle_content_evidence_packet_v2.json"),
        "blockers": list(dict.fromkeys(blockers)),
    }
    _write(output_dir / "capital_chronicle_content_evidence_packet_v2.json", packet)
    _write(output_dir / "generic_assignment_readiness_v1.json", assignment)
    _write(output_dir / "generic_database_preflight_result_v1.json", result)
    return result


def run_generic_prepare_only(
    *,
    output_dir: Path,
    story_request: Mapping[str, Any],
    capital_chronicle_root: str | Path | None = None,
    evidence_packet_path: str | Path | None = None,
    as_of_utc: str | None = None,
    structured_reviewer=_default_reviewer,
) -> dict[str, Any]:
    packet = _load_evidence_packet(
        capital_chronicle_root=capital_chronicle_root,
        evidence_packet_path=evidence_packet_path,
        as_of_utc=as_of_utc,
    )
    packet["validation_blockers"] = validate_evidence_packet(packet)
    capabilities = resolve_story_capabilities(story_request, load_source_capability_registry())
    freshness = evaluate_freshness(packet, story_request)
    visual_assets = list(story_request.get("visual_assets") or [])
    visual = evaluate_visual_composition(
        visual_assets,
        editorial_exception=story_request.get("visual_editorial_exception"),
        story_type=str(story_request.get("story_type") or ""),
    )
    article = dict(story_request.get("article_candidate") or {})
    editorial = run_editorial_review(
        request=story_request,
        packet=packet,
        article=article,
        freshness_decision=freshness,
        visual_decision=visual,
        structured_reviewer=structured_reviewer,
    )
    google_request = GoogleImageSearchGroundingProvider().build_request(str(story_request.get("visual_research_query") or story_request.get("title") or ""))
    blockers = []
    for row in (capabilities, freshness, visual, editorial):
        if row.get("status") == "BLOCK" or row.get("decision") == "BLOCK":
            blockers.extend(row.get("blockers") or [])
    result = {
        "schema_version": "contentops.generic_evidence_freshness_visual_editorial_fabric.v2",
        "classification": "PASS_GENERIC_PREPARE_ONLY" if not blockers else "PASS_GENERIC_FABRIC_FAIL_CLOSED_REHEARSAL",
        "publication_eligible": not blockers,
        "public_write_performed": False,
        "browser_or_cdp_used": False,
        "platform_adapter_called": False,
        "video_or_tiktok_adapter_called": False,
        "evidence_packet_path": str(output_dir / "capital_chronicle_content_evidence_packet_v2.json"),
        "freshness_decision_path": str(output_dir / "freshness_market_state_decision_v2.json"),
        "visual_decision_path": str(output_dir / "visual_composition_decision_v2.json"),
        "editorial_review_path": str(output_dir / "editorial_review_orchestrator_v2.json"),
        "capabilities": capabilities,
        "blockers": list(dict.fromkeys(blockers)),
    }
    _write(output_dir / "capital_chronicle_content_evidence_packet_v2.json", packet)
    _write(output_dir / "freshness_market_state_decision_v2.json", freshness)
    _write(output_dir / "visual_composition_decision_v2.json", visual)
    _write(output_dir / "editorial_review_orchestrator_v2.json", editorial)
    _write(output_dir / "google_visual_discovery_request_rehearsal_v2.json", google_request)
    _write(output_dir / "generic_fabric_prepare_only_result_v2.json", result)
    return result
