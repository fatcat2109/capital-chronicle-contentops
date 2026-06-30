"""V6 Substack manual export + canonical article studio packet builder.

Deterministic, local-only, fixture-only. No network, no provider calls,
no browser sessions, no credential/env reads, and no live publishing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_AND_ARTICLE_STUDIO_ON_CANONICAL_V5_DASHBOARD_HEAVY_BATCH_V0"
SAMPLE_SCOPE = "sample_fixture_only"
EXPORT_STATUS = "ready_for_manual_review"
APPROVAL_STATUS = "pending"
HASH_ALGORITHM = "sha256_json_v6"

FORBIDDEN_SECRET_PATTERNS = (
    r"https://discord(?:app)?\.com/api/webhooks/",
    r"sk-[A-Za-z0-9]",
    r"xox[baprs]-",
    r"ghp_[A-Za-z0-9]",
    r"bearer\s+[A-Za-z0-9._-]{12,}",
    r"cookie\s*[:=]",
    r"localstorage\s*[:=]",
    r"sessionstorage\s*[:=]",
)
FORBIDDEN_PUBLICATION_CLAIMS = (
    "published on substack",
    "publicly published",
    "live on substack",
    "substack url:",
)
FORBIDDEN_FAKE_MATERIAL = (
    "fake citation",
    "invented citation",
    "fabricated citation",
    "fake url",
    "invented url",
    "fabricated url",
    "fabricated numbers",
    "fake numbers",
)
FORBIDDEN_FINANCIAL_ADVICE_PHRASES = (
    "financial advice",
    "trading signal",
    "signal service",
    "price target",
    "target price",
)
FORBIDDEN_FINANCIAL_ADVICE_WORDS = {"buy", "sell", "hold", "entry", "exit"}


class SubstackExportError(ValueError):
    """Raised when a packet cannot be safely converted to manual export."""


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [s for item in value.values() for s in _walk_strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _walk_strings(item)]
    return []


def _assert_safe_text(text: str) -> None:
    lower = text.lower()
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise SubstackExportError("forbidden_secret_or_session_material")
    for phrase in FORBIDDEN_PUBLICATION_CLAIMS:
        if phrase in lower:
            raise SubstackExportError(f"forbidden_publication_claim:{phrase}")
    for phrase in FORBIDDEN_FAKE_MATERIAL:
        if phrase in lower:
            raise SubstackExportError(f"forbidden_fake_material:{phrase}")
    for phrase in FORBIDDEN_FINANCIAL_ADVICE_PHRASES:
        if phrase in lower:
            raise SubstackExportError(f"forbidden_financial_advice:{phrase}")
    words = set(re.findall(r"\b[a-z]+\b", lower))
    if words & FORBIDDEN_FINANCIAL_ADVICE_WORDS:
        raise SubstackExportError(f"forbidden_financial_advice_word:{sorted(words & FORBIDDEN_FINANCIAL_ADVICE_WORDS)[0]}")


def _assert_packet_safe(packet: Mapping[str, Any]) -> None:
    for text in _walk_strings(packet):
        _assert_safe_text(text)


def _require_mapping(packet: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = packet.get(key)
    if not isinstance(value, Mapping):
        raise SubstackExportError(f"missing_required_mapping:{key}")
    return value


def _require_str(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubstackExportError(f"missing_required_string:{key}")
    return value


def build_article_body_markdown(article: Mapping[str, Any]) -> str:
    title = _require_str(article, "title")
    subtitle = _require_str(article, "subtitle")
    intro = _require_str(article, "intro")
    thesis = _require_str(article, "thesis")
    conclusion = _require_str(article, "conclusion")
    sections = article.get("sections")
    if not isinstance(sections, list) or not sections:
        raise SubstackExportError("missing_required_sections")

    lines = [f"# {title}", "", f"_{subtitle}_", "", "## Thesis", thesis, "", "## Briefing", intro]
    for section in sections:
        if not isinstance(section, Mapping):
            raise SubstackExportError("invalid_section")
        lines.extend(["", f"## {_require_str(section, 'title')}", _require_str(section, "body")])
    lines.extend([
        "",
        "## Operator conclusion",
        conclusion,
        "",
        "---",
        "Manual copy only. Substack API not used. Live publish disabled. No runtime proof.",
    ])
    return "\n".join(lines)


def build_substack_manual_export_packet(source_packet: Mapping[str, Any]) -> dict[str, Any]:
    _assert_packet_safe(source_packet)
    article = _require_mapping(source_packet, "canonical_article_draft")
    seo = _require_mapping(source_packet, "seo_packet")
    grounding = _require_mapping(source_packet, "research_grounding_packet")

    source_packet_id = _require_str(source_packet, "packet_id")
    source_hash = _require_str(article, "canonical_payload_hash")
    title = _require_str(article, "title")
    subtitle = _require_str(article, "subtitle")
    slug = _require_str(article, "slug_candidate")
    body = build_article_body_markdown(article)
    title_alternatives = seo.get("title_alternatives", [])
    seo_title = title_alternatives[0] if title_alternatives and isinstance(title_alternatives[0], str) else title
    seo_description = _require_str(seo, "meta_description")

    manual_copy_payload = {
        "target": "substack_manual_copy",
        "copy_mode": "manual copy only",
        "title": title,
        "subtitle": subtitle,
        "body_markdown": body,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "slug_candidate": slug,
        "operator_instructions": "Review in V5, then manually copy into Substack only if an operator separately approves outside this packet.",
        "safety_labels": [
            SAMPLE_SCOPE,
            "manual copy only",
            "Substack API not used",
            "live publish disabled",
            "no runtime proof",
        ],
    }
    exact_payload_hash = _stable_hash(manual_copy_payload)
    export_packet_id = f"substack_manual_export_{exact_payload_hash[:16]}"

    packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "export_packet_id": export_packet_id,
        "source_article_packet_id": source_packet_id,
        "source_canonical_hash": source_hash,
        "article_title": title,
        "article_subtitle": subtitle,
        "article_body_markdown": body,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "canonical_slug_candidate": slug,
        "manual_copy_payload": manual_copy_payload,
        "exact_payload_hash": exact_payload_hash,
        "hash_algorithm": HASH_ALGORITHM,
        "export_status": EXPORT_STATUS,
        "approval_status": APPROVAL_STATUS,
        "live_publish_allowed": False,
        "live_publish_performed": False,
        "provider_call_made": False,
        "network_call_made": False,
        "browser_session_used": False,
        "raw_secret_values_serialized": False,
        "env_lines_serialized": False,
        "sample_scope": SAMPLE_SCOPE,
        "grounding_state": {
            "no_invented_citations": grounding.get("no_invented_citations") is True,
            "no_invented_urls": grounding.get("no_invented_urls") is True,
            "no_fabricated_market_numbers": grounding.get("no_fabricated_market_numbers") is True,
            "no_claims_of_live_public_publication": grounding.get("no_claims_of_live_public_publication") is True,
            "required_human_review_items": grounding.get("required_human_review_items", []),
        },
        "blockers": ["live_publish_disabled", "operator_approval_pending"],
        "warnings": ["sample_fixture_only", "manual_copy_only_no_substack_api", "no_runtime_proof"],
        "recommended_next_task": "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_APPROVAL_AND_EXPORT_EVIDENCE_HARDENING_V0",
    }
    _assert_packet_safe(packet)
    return packet


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V6 Substack manual export packet from committed article packet.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = build_substack_manual_export_packet(load_json(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
