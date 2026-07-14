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


def _public_documents(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row["document_id"]): row
        for row in packet.get("official_source_documents") or []
        if row.get("document_id") and row.get("public_claim_allowed") is True
    }


def _authorized_urls(
    *,
    claim_ids: Sequence[str],
    document_ids: Sequence[str],
    claims: Mapping[str, Mapping[str, Any]],
    documents: Mapping[str, Mapping[str, Any]],
    citations: Mapping[str, Any],
) -> set[str]:
    urls: set[str] = set()
    for claim_id in claim_ids:
        urls.update(str(value) for value in citations.get(claim_id) or [] if str(value))
        source_url = (claims.get(claim_id) or {}).get("source_url")
        if source_url:
            urls.add(str(source_url))
    for document_id in document_ids:
        document = documents.get(document_id) or {}
        urls.update(str(document.get(field)) for field in ("source_url", "data_url") if document.get(field))
    return urls


def build_content_unit_claim_graph(*, article: Mapping[str, Any], packet: Mapping[str, Any], unit_mappings: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """Map every rendered unit and fail closed on implicit or unbound factual authority."""
    mappings = {str(row["content_unit_id"]): dict(row) for row in unit_mappings if row.get("content_unit_id")}
    claims = _public_claims(packet)
    documents = _public_documents(packet)
    citations = packet.get("citation_map") or {}
    governed_mode = str((packet.get("governed_contract") or {}).get("mode") or "")
    blockers: list[str] = []
    units: list[dict[str, Any]] = []
    for index, text in enumerate(_article_sentences(article), 1):
        unit_id = f"sentence-{index:03d}"
        mapping = mappings.get(unit_id)
        if mapping is None:
            blockers.append(f"content_unit_mapping_missing:{unit_id}")
            mapping = {"content_unit_type": "", "claim_ids": [], "document_ids": [], "source_urls": []}
        kind = str(mapping.get("content_unit_type") or "")
        claim_ids = [str(value) for value in mapping.get("claim_ids") or []]
        document_ids = [str(value) for value in mapping.get("document_ids") or []]
        source_urls = [str(value) for value in mapping.get("source_urls") or [] if str(value)]
        factual = kind in FACTUAL_UNIT_TYPES
        if kind not in CONTENT_UNIT_TYPES:
            blockers.append(f"content_unit_type_invalid:{unit_id}")
        if factual and not claim_ids and not document_ids:
            blockers.append(f"factual_content_unit_authority_required:{unit_id}")
        if factual and not source_urls:
            blockers.append(f"factual_content_unit_source_urls_required:{unit_id}")
        for field in ("authority_class", "exact_proxy_context", "inference_class", "citation_rendering", "public_use_allowed"):
            if factual and field not in mapping:
                blockers.append(f"factual_content_unit_explicit_{field}_required:{unit_id}")
        for claim_id in claim_ids:
            if claim_id not in claims:
                blockers.append(f"content_unit_unapproved_claim:{unit_id}:{claim_id}")
            if not citations.get(claim_id):
                blockers.append(f"content_unit_claim_missing_citation:{unit_id}:{claim_id}")
        for document_id in document_ids:
            if document_id not in documents:
                blockers.append(f"content_unit_unapproved_document:{unit_id}:{document_id}")
        authorized_urls = _authorized_urls(
            claim_ids=claim_ids,
            document_ids=document_ids,
            claims=claims,
            documents=documents,
            citations=citations,
        )
        for source_url in source_urls:
            if source_url not in authorized_urls:
                blockers.append(f"content_unit_source_url_not_authorized:{unit_id}:{source_url}")
        authority_class = str(mapping.get("authority_class") or "")
        allowed_authorities = {governed_mode}
        allowed_authorities.update(str((claims.get(claim_id) or {}).get("source_authority") or "") for claim_id in claim_ids)
        allowed_authorities.update(str((claims.get(claim_id) or {}).get("authority_scope") or "") for claim_id in claim_ids)
        allowed_authorities.discard("")
        if factual and authority_class not in allowed_authorities:
            blockers.append(f"content_unit_authority_class_mismatch:{unit_id}")
        exact_proxy_context = str(mapping.get("exact_proxy_context") or "")
        allowed_contexts = {
            str((claims.get(claim_id) or {}).get(field) or "")
            for claim_id in claim_ids
            for field in ("source_authority", "authority_scope")
        }
        allowed_contexts.discard("")
        if factual and claim_ids and exact_proxy_context not in allowed_contexts:
            blockers.append(f"content_unit_exact_proxy_context_mismatch:{unit_id}")
        observation_time = mapping.get("observation_time_utc")
        known_at = mapping.get("known_at_utc")
        if factual and claim_ids:
            if not observation_time:
                blockers.append(f"factual_content_unit_observation_time_required:{unit_id}")
            if not known_at:
                blockers.append(f"factual_content_unit_known_at_required:{unit_id}")
            claim_observations = {str((claims.get(claim_id) or {}).get("observation_time_utc") or "") for claim_id in claim_ids}
            claim_known_at = {str((claims.get(claim_id) or {}).get("known_at_utc") or (claims.get(claim_id) or {}).get("ingestion_time_utc") or "") for claim_id in claim_ids}
            if observation_time and str(observation_time) not in claim_observations:
                blockers.append(f"content_unit_observation_time_mismatch:{unit_id}")
            if known_at and str(known_at) not in claim_known_at:
                blockers.append(f"content_unit_known_at_mismatch:{unit_id}")
        explicit_public_use = mapping.get("public_use_allowed") is True
        upstream_public_use = all(claim_id in claims for claim_id in claim_ids) and all(document_id in documents for document_id in document_ids)
        if factual and not explicit_public_use:
            blockers.append(f"factual_content_unit_public_use_not_allowed:{unit_id}")
        units.append({
            "content_unit_id": unit_id,
            "text_hash": _hash(text),
            "content_unit_type": kind,
            "claim_ids": claim_ids,
            "document_ids": document_ids,
            "source_urls": source_urls,
            "authorized_source_urls": sorted(authorized_urls),
            "authority_class": authority_class,
            "exact_proxy_context": exact_proxy_context,
            "observation_time_utc": observation_time,
            "known_at_utc": known_at,
            "inference_class": str(mapping.get("inference_class") or ""),
            "calculation_reference": mapping.get("calculation_reference"),
            "citation_rendering": str(mapping.get("citation_rendering") or ""),
            "public_use_allowed": explicit_public_use and upstream_public_use,
        })
    rendered_ids = {row["content_unit_id"] for row in units}
    blockers.extend(f"content_unit_mapping_not_rendered:{unit_id}" for unit_id in sorted(set(mappings) - rendered_ids))
    rendered = _rendered_article_body(article)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not blockers else "BLOCK",
        "rendered_body_sha256": _content_hash(rendered),
        "content_unit_count": len(units),
        "content_units": units,
        "blockers": list(dict.fromkeys(blockers)),
        "publication_authority": False,
    }


def _stage_title_body(content: Any, fallback_title: str) -> tuple[str, str]:
    if isinstance(content, Mapping):
        title = str(content.get("title") or fallback_title)
        body_value = content.get("rendered_body", content.get("body_markdown", content))
        body = body_value if isinstance(body_value, str) else json.dumps(body_value, sort_keys=True, separators=(",", ":"), default=str)
        return title, body
    return fallback_title, str(content)


def build_revision_chain(*, article: Mapping[str, Any], claim_graph: Mapping[str, Any], stages: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """Validate continuous, decision-bound v0-v8 content and logical evidence."""
    supplied = {str(row["stage_id"]): dict(row) for row in stages if row.get("stage_id")}
    blockers: list[str] = []
    records: list[dict[str, Any]] = []
    previous_output_hash: str | None = None
    final_title_hash = _content_hash(str(article.get("title") or ""))
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
        input_content = source.get("input_content")
        output_content = source.get("output_content")
        input_hash = _content_hash(input_content) if input_present else ""
        output_hash = _content_hash(output_content) if output_present else ""
        input_title, input_body = _stage_title_body(input_content, str(article.get("title") or ""))
        output_title, output_body = _stage_title_body(output_content, str(article.get("title") or ""))
        input_title_hash, output_title_hash = _content_hash(input_title), _content_hash(output_title)
        input_body_hash, output_body_hash = _content_hash(input_body), _content_hash(output_body)
        if source.get("input_content_sha256") not in {None, input_hash}:
            blockers.append(f"revision_stage_input_hash_mismatch:{stage_id}")
        if source.get("output_content_sha256") not in {None, output_hash}:
            blockers.append(f"revision_stage_output_hash_mismatch:{stage_id}")
        if previous_output_hash is not None and input_hash != previous_output_hash:
            blockers.append(f"revision_stage_previous_output_link_broken:{stage_id}")
        structured_diff = [dict(value) for value in source.get("structured_diff") or [] if isinstance(value, Mapping)]
        changed = input_title_hash != output_title_hash or input_body_hash != output_body_hash
        if decision == "PASS_NO_CHANGE" and changed:
            blockers.append(f"revision_stage_pass_no_change_hash_mismatch:{stage_id}")
        if decision == "REVISE" and (not changed or not structured_diff):
            blockers.append(f"revision_stage_revise_requires_change_and_diff:{stage_id}")
        unresolved = [str(value) for value in source.get("unresolved_issues") or []]
        if unresolved:
            blockers.append(f"revision_stage_unresolved_material_issues:{stage_id}")
        for field in ("issues_addressed", "issues_introduced", "model_or_rule_version", "deterministic_timestamp_utc"):
            if field not in source:
                blockers.append(f"revision_stage_{field}_missing:{stage_id}")
        record_core = {
            "stage_id": stage_id,
            "role": role,
            "input_content_ref": str(source.get("input_content_ref") or "embedded_input_content"),
            "output_content_ref": str(source.get("output_content_ref") or "embedded_output_content"),
            "input_content_sha256": input_hash,
            "output_content_sha256": output_hash,
            "input_title_sha256": input_title_hash,
            "output_title_sha256": output_title_hash,
            "input_rendered_body_sha256": input_body_hash,
            "output_rendered_body_sha256": output_body_hash,
            "model_or_rule_version": str(source.get("model_or_rule_version") or ""),
            "deterministic_timestamp_utc": str(source.get("deterministic_timestamp_utc") or ""),
            "decision": decision,
            "structured_diff": structured_diff,
            "issues_addressed": [str(value) for value in source.get("issues_addressed") or []],
            "issues_introduced": [str(value) for value in source.get("issues_introduced") or []],
            "unresolved_issues": unresolved,
        }
        supplied_logical_hash = source.get("stage_logical_hash")
        logical_hash = _hash(record_core)
        if supplied_logical_hash not in {None, logical_hash}:
            blockers.append(f"revision_stage_logical_hash_mismatch:{stage_id}")
        records.append({**record_core, "stage_logical_hash": logical_hash})
        previous_output_hash = output_hash
    if records:
        if records[-1]["output_title_sha256"] != final_title_hash:
            blockers.append("revision_chain_final_title_hash_mismatch")
        if records[-1]["output_rendered_body_sha256"] != final_body_hash:
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
        "final_output_hash": records[-1]["output_rendered_body_sha256"] if records else "",
        "final_title_sha256": final_title_hash,
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
