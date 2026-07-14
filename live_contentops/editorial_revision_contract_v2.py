"""Deterministic claim-graph and revision-chain contracts for editorial V2."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from .tier1_editorial_quality_v1 import rendered_body

SCHEMA_VERSION = "contentops.editorial_revision_contract.v2"
CONTENT_UNIT_TYPES = {"fact", "direct_calculation", "source_attributed_interpretation", "capital_chronicle_inference", "scenario", "limitation", "transition", "non_factual_framing"}
FACTUAL_UNIT_TYPES = {"fact", "direct_calculation", "source_attributed_interpretation", "capital_chronicle_inference", "scenario"}
ALLOWED_DECISIONS = {"PASS_NO_CHANGE", "REVISE", "BLOCK", "ESCALATE_OPERATOR"}
REVISION_STAGES = (
    ("v0_assignment_brief", "assignment_editor"),
    ("v1_evidence_outline", "evidence_planner"),
    ("v2_reporter_draft", "reporter_writer"),
    ("v3_quantitative_edit", "quantitative_editor"),
    ("v4_headline_structure_edit", "headline_editor"),
    ("v5_copy_edit", "copy_editor"),
    ("v6_seo_rendered_page_edit", "seo_editor"),
    ("v7_adversarial_standards_review", "adversarial_final_reviewer"),
    ("v8_final_release_candidate", "release_editor"),
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _content_hash(value: Any) -> str:
    """Hash strings as exact UTF-8 content and structured content canonically."""
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rendered_article_body(article: Mapping[str, Any]) -> str:
    markdown = str(article.get("substack_body_markdown") or article.get("body_markdown") or "")
    return str(article.get("rendered_body") or rendered_body(markdown))


def _article_sentences(article: Mapping[str, Any]) -> list[str]:
    body = _rendered_article_body(article)
    return [value.strip() for value in SENTENCE_RE.split(" ".join(body.split())) if value.strip()]


def _public_claims(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row["claim_id"]): row
        for row in packet.get("numeric_claims") or []
        if row.get("claim_id") and row.get("public_claim_allowed") is True
    }


def build_content_unit_claim_graph(*, article: Mapping[str, Any], packet: Mapping[str, Any], unit_mappings: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """Map each rendered sentence; factual mappings must use public cited claims."""
    mappings = {str(row["content_unit_id"]): dict(row) for row in unit_mappings if row.get("content_unit_id")}
    claims = _public_claims(packet)
    citations = packet.get("citation_map") or {}
    blockers: list[str] = []
    units: list[dict[str, Any]] = []
    for index, text in enumerate(_article_sentences(article), 1):
        unit_id = f"sentence-{index:03d}"
        mapping = mappings.get(unit_id)
        if mapping is None:
            blockers.append(f"content_unit_mapping_missing:{unit_id}")
            mapping = {"content_unit_type": "non_factual_framing", "claim_ids": [], "source_urls": []}
        kind = str(mapping.get("content_unit_type") or "")
        claim_ids = [str(value) for value in mapping.get("claim_ids") or []]
        source_urls = [str(value) for value in mapping.get("source_urls") or [] if str(value)]
        if kind not in CONTENT_UNIT_TYPES:
            blockers.append(f"content_unit_type_invalid:{unit_id}")
        if kind in FACTUAL_UNIT_TYPES and not claim_ids:
            blockers.append(f"factual_content_unit_claims_required:{unit_id}")
        if kind in FACTUAL_UNIT_TYPES and not source_urls:
            blockers.append(f"factual_content_unit_source_urls_required:{unit_id}")
        for claim_id in claim_ids:
            if claim_id not in claims:
                blockers.append(f"content_unit_unapproved_claim:{unit_id}:{claim_id}")
            if not citations.get(claim_id):
                blockers.append(f"content_unit_claim_missing_citation:{unit_id}:{claim_id}")
        units.append({
            "content_unit_id": unit_id,
            "text_hash": _hash(text),
            "content_unit_type": kind,
            "claim_ids": claim_ids,
            "source_urls": source_urls,
            "authority_class": str(mapping.get("authority_class") or "governed_packet"),
            "exact_proxy_context": str(mapping.get("exact_proxy_context") or "exact"),
            "observation_time_utc": mapping.get("observation_time_utc"),
            "known_at_utc": mapping.get("known_at_utc"),
            "inference_class": str(mapping.get("inference_class") or "none"),
            "calculation_reference": mapping.get("calculation_reference"),
            "citation_rendering": str(mapping.get("citation_rendering") or "source_link"),
            "public_use_allowed": all(claim_id in claims for claim_id in claim_ids),
        })
    rendered_ids = {row["content_unit_id"] for row in units}
    blockers.extend(f"content_unit_mapping_not_rendered:{unit_id}" for unit_id in sorted(set(mappings) - rendered_ids))
    markdown = str(article.get("substack_body_markdown") or article.get("body_markdown") or "")
    rendered = str(article.get("rendered_body") or rendered_body(markdown))
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not blockers else "BLOCK",
        "rendered_body_sha256": _content_hash(rendered),
        "content_unit_count": len(units),
        "content_units": units,
        "blockers": list(dict.fromkeys(blockers)),
        "publication_authority": False,
    }


def build_revision_chain(*, article: Mapping[str, Any], claim_graph: Mapping[str, Any], stages: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """Validate the fixed sequence against actual, continuous stage content."""
    supplied = {str(row["stage_id"]): dict(row) for row in stages if row.get("stage_id")}
    blockers: list[str] = []
    records: list[dict[str, Any]] = []
    previous_output_hash: str | None = None
    final_body_hash = _content_hash(_rendered_article_body(article))
    for stage_id, role in REVISION_STAGES:
        source = supplied.get(stage_id, {})
        if not source:
            blockers.append(f"revision_stage_missing:{stage_id}")
        decision = str(source.get("decision") or "")
        if decision not in ALLOWED_DECISIONS:
            blockers.append(f"revision_stage_decision_invalid:{stage_id}")
        if source.get("role") not in {None, role}:
            blockers.append(f"revision_stage_role_invalid:{stage_id}")
        input_present = "input_content" in source
        output_present = "output_content" in source
        if not input_present:
            blockers.append(f"revision_stage_input_content_missing:{stage_id}")
        if not output_present:
            blockers.append(f"revision_stage_output_content_missing:{stage_id}")
        input_hash = _content_hash(source.get("input_content")) if input_present else ""
        output_hash = _content_hash(source.get("output_content")) if output_present else ""
        if source.get("input_content_sha256") not in {None, input_hash}:
            blockers.append(f"revision_stage_input_hash_mismatch:{stage_id}")
        if source.get("output_content_sha256") not in {None, output_hash}:
            blockers.append(f"revision_stage_output_hash_mismatch:{stage_id}")
        if previous_output_hash is not None and input_hash != previous_output_hash:
            blockers.append(f"revision_stage_previous_output_link_broken:{stage_id}")
        record = {
            "stage_id": stage_id,
            "role": role,
            "input_content_sha256": input_hash,
            "output_content_sha256": output_hash,
            "rule_version": str(source.get("rule_version") or SCHEMA_VERSION),
            "decision": decision,
            "changes": [str(value) for value in source.get("changes") or []],
            "unresolved_issues": [str(value) for value in source.get("unresolved_issues") or []],
        }
        records.append(record)
        previous_output_hash = output_hash
    if records and records[-1]["output_content_sha256"] != final_body_hash:
        blockers.append("revision_chain_final_body_hash_mismatch")
    if any(row["decision"] in {"BLOCK", "ESCALATE_OPERATOR"} for row in records):
        blockers.append("revision_chain_contains_nonrelease_decision")
    if claim_graph.get("status") != "PASS":
        blockers.append("revision_chain_claim_graph_not_pass")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not blockers else "BLOCK",
        "revision_stage_count": len(records),
        "stages": records,
        "final_output_hash": previous_output_hash or "",
        "rendered_body_sha256": final_body_hash,
        "blockers": list(dict.fromkeys(blockers)),
        "publication_authority": False,
    }


def build_editorial_revision_contract(
    *,
    article: Mapping[str, Any],
    packet: Mapping[str, Any],
    revision_input: Mapping[str, Any] | None,
    revision_required: bool = True,
) -> dict[str, Any]:
    """Validate mandatory V2 evidence, or emit an explicit compatibility no-op."""
    if not revision_input:
        rendered_hash = _content_hash(_rendered_article_body(article))
        if revision_required:
            blocker = "editorial_revision_v2_required"
            blocked = {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCK",
                "rendered_body_sha256": rendered_hash,
                "blockers": [blocker],
                "publication_authority": False,
            }
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCK",
                "claim_graph": {**blocked, "content_units": []},
                "revision_chain": {**blocked, "stages": []},
                "blockers": [blocker],
                "publication_authority": False,
            }
        not_requested = {
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_REQUESTED",
            "rendered_body_sha256": rendered_hash,
            "blockers": [],
            "publication_authority": False,
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_REQUESTED",
            "claim_graph": {**not_requested, "content_units": []},
            "revision_chain": {**not_requested, "stages": []},
            "blockers": [],
            "publication_authority": False,
        }
    graph = build_content_unit_claim_graph(article=article, packet=packet, unit_mappings=revision_input.get("content_unit_mappings") or [])
    chain = build_revision_chain(article=article, claim_graph=graph, stages=revision_input.get("revision_stages") or [])
    blockers = list(dict.fromkeys([*graph["blockers"], *chain["blockers"]]))
    return {"schema_version": SCHEMA_VERSION, "status": "PASS" if not blockers else "BLOCK", "claim_graph": graph, "revision_chain": chain, "blockers": blockers, "publication_authority": False}
