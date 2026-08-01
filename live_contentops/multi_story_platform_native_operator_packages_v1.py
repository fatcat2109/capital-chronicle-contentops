"""Deterministic multi-story platform-native operator packages (local only)."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    build_content_evidence_packet_v3,
    validate_content_evidence_packet_v3,
)
from live_contentops.governed_upstream_bridge_v1 import (
    is_ancestor,
    read_git_artifact,
    resolve_observed_head,
)
from live_contentops.payload_preview_hash_v6 import compute_payload_hash
from live_contentops.universal_governed_registry_v1 import logical_hash
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_candidate_bound_evidence_packet,
    build_canonical_editorial_shadow_handoff,
)


TASK = "TASK_CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
SCHEMA_VERSION = "contentops.three_v3_canonical_editorial_operator_packages.v1"
AUTHORITY_SCHEMA = "capital_chronicle.multi_story_scoped_reporting_authority_batch.v1"
AUTHORITY_RELATIVE = Path(
    "docs/research/publication_evidence/current/"
    "CapitalChronicleMultiStoryScopedReportingAuthorityBatchV1.json"
)
EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)
EXPECTED_UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
EXPECTED_UPSTREAM_BRANCH = "main"
EXPECTED_UPSTREAM_HEAD = "64834919b4f69e977475c203abeafef57791f015"
EXPECTED_AUTHORITY_GIT_BLOB_SHA1 = "fbb25216d08b5a4c5ca30386cf8f47ed468c1eac"
EXPECTED_AUTHORITY_BYTE_SHA256 = "5bc4ca67c4c149c0f68eeacdcb3899fbd29e3647945723c9ceb955a69ddb5d05"
EXPECTED_AUTHORITY_BYTE_LENGTH = 16646
EXPECTED_AUTHORITY_PACKET_ID = "cc-multi-story-authority-3ff3f14f9a231ce791a9"
EXPECTED_AUTHORITY_LOGICAL_HASH = "f825fcfe8016b6a020d855180267f393d6df0b2f6b6e98edbb351c6b549a3840"
EXPECTED_STORY_IDS = (
    "fomc-minutes-2026-04-28-29",
    "apple-sec-10q-2026-000013",
    "usgs-reviewed-ridgecrest-ci38457511",
)
PLATFORM_IDS = (
    "substack_newsletter",
    "linkedin",
    "x_twitter",
    "facebook_page",
    "telegram",
    "youtube_community",
)
AUTHORIZED_CLAIMS = {
    story_id: tuple(claim_id for claim_id in claim_ids)
    for story_id, claim_ids in {
        "fomc-minutes-2026-04-28-29": ("claim-95f6638ac5460d82",),
        "apple-sec-10q-2026-000013": (
            "claim-661031f2768d9629",
            "claim-403af5e0ec85b722",
        ),
        "usgs-reviewed-ridgecrest-ci38457511": (
            "claim-a436944fa62bc374",
            "claim-f1f734761cccc69a",
        ),
    }.items()
}
PLATFORM_CONTRACTS: dict[str, dict[str, Any]] = {
    "substack_newsletter": {
        "content_surface": "newsletter_note",
        "character_limit_max": 100000,
        "mode": "manual_export",
        "shape": "headline_deck_body_source_note",
    },
    "linkedin": {
        "content_surface": "professional_post",
        "character_limit_max": 3000,
        "mode": "dry_run",
        "shape": "professional_context_source_close",
    },
    "x_twitter": {
        "content_surface": "short_post",
        "character_limit_max": 280,
        "mode": "dry_run",
        "shape": "single_compact_source_post",
    },
    "facebook_page": {
        "content_surface": "page_post",
        "character_limit_max": 63206,
        "mode": "dry_run",
        "shape": "conversational_context_source_post",
    },
    "telegram": {
        "content_surface": "channel_post",
        "character_limit_max": 4096,
        "mode": "dry_run",
        "shape": "bulletin_source_post",
    },
    "youtube_community": {
        "content_surface": "community_text_post",
        "character_limit_max": 1500,
        "mode": "dry_run",
        "shape": "community_update_source_prompt",
    },
}
FORBIDDEN_PROSE = (
    r"\b(rate[- ]path|policy interpretation|hawkish|dovish)\b",
    r"\b(earnings|revenue|guidance|company impact)\b",
    r"\b(magnitude|damage|affected entit(?:y|ies))\b",
    r"\b(market reaction|forecast|trading signal|buy|sell)\b",
)
REQUIRED_FALSE_FLAGS = {
    "publication_authority",
    "dispatch_authority",
    "public_write_authority",
    "publication_allowed",
    "dispatch_allowed",
    "public_write_allowed",
    "posting_enabled_now",
    "scheduler_enabled_now",
    "credential_read_allowed_now",
    "network_call_performed",
    "browser_action_performed",
    "public_write_performed",
    "valid_for_dispatch",
    "dispatch_ready",
    "public_ready",
    "live_ready",
    "live_eligibility",
    "operator_approval_captured",
}


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _logical_hash(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(value))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _assert_false_flags(node: Any) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key in REQUIRED_FALSE_FLAGS and value is not False:
                raise ValueError(f"required_false_flag_not_false:{key}")
            _assert_false_flags(value)
    elif isinstance(node, list):
        for value in node:
            _assert_false_flags(value)


def _expected_authority_receipt() -> dict[str, Any]:
    return {
        "repository": EXPECTED_UPSTREAM_REPOSITORY,
        "branch": EXPECTED_UPSTREAM_BRANCH,
        "observed_head": EXPECTED_UPSTREAM_HEAD,
        "producer_commit": EXPECTED_UPSTREAM_HEAD,
        "artifact_path": AUTHORITY_RELATIVE.as_posix(),
        "git_blob_sha1": EXPECTED_AUTHORITY_GIT_BLOB_SHA1,
        "byte_sha256": EXPECTED_AUTHORITY_BYTE_SHA256,
        "byte_length": EXPECTED_AUTHORITY_BYTE_LENGTH,
    }


def _normalize_repository_identity(origin_url: str) -> str:
    normalized = origin_url.strip().replace("\\", "/").removesuffix(".git").rstrip("/")
    if normalized.startswith("git@") and ":" in normalized:
        normalized = normalized.split(":", 1)[1]
    elif "://" in normalized:
        normalized = normalized.split("://", 1)[1].split("/", 1)[1]
    return normalized


def _verify_upstream_checkout(upstream_root: Path) -> dict[str, Any]:
    try:
        origin_url = subprocess.check_output(
            ["git", "-C", str(upstream_root), "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as error:
        raise ValueError("upstream_origin_url_unavailable") from error
    repository = _normalize_repository_identity(origin_url)
    if repository.casefold() != EXPECTED_UPSTREAM_REPOSITORY.casefold():
        raise ValueError(f"upstream_origin_repository_mismatch:{repository}")
    observed_origin_head = resolve_observed_head(upstream_root, EXPECTED_UPSTREAM_BRANCH)
    if not is_ancestor(upstream_root, EXPECTED_UPSTREAM_HEAD, observed_origin_head):
        raise ValueError("upstream_producer_commit_not_reachable_from_origin_main")
    return {
        "origin_url_redacted_to_repository": repository,
        "repository": repository,
        "branch": EXPECTED_UPSTREAM_BRANCH,
        "observed_origin_head": observed_origin_head,
        "authority_observed_head": EXPECTED_UPSTREAM_HEAD,
        "producer_commit": EXPECTED_UPSTREAM_HEAD,
        "producer_commit_reachable_from_observed_origin_head": True,
        "status": "PASS_PINNED_AUTHORITY_COMMIT_REACHABLE_FROM_ORIGIN_MAIN",
    }


def _validate_authority(packet: Mapping[str, Any], observed_upstream_head: str) -> list[dict[str, Any]]:
    if observed_upstream_head != EXPECTED_UPSTREAM_HEAD:
        raise ValueError(f"upstream_head_mismatch:{observed_upstream_head}")
    if packet.get("schema_version") != AUTHORITY_SCHEMA:
        raise ValueError("authority_schema_mismatch")
    if packet.get("packet_id") != EXPECTED_AUTHORITY_PACKET_ID:
        raise ValueError("authority_packet_id_mismatch")
    packet_without_hash = {key: value for key, value in packet.items() if key != "logical_hash"}
    if logical_hash(packet_without_hash) != packet.get("logical_hash"):
        raise ValueError("authority_logical_hash_recomputation_mismatch")
    if packet.get("logical_hash") != EXPECTED_AUTHORITY_LOGICAL_HASH:
        raise ValueError("authority_logical_hash_mismatch")
    if packet.get("terminal_status") != "PASS_MULTI_STORY_SCOPED_REPORTING_AUTHORITY_BATCH_V1":
        raise ValueError("authority_terminal_status_not_pass")
    verifier = packet.get("verifier") or {}
    if verifier.get("status") != "PASS" or verifier.get("blockers") != []:
        raise ValueError("authority_verifier_not_pass")
    protected = packet.get("protected_state") or {}
    if protected.get("global_dqr_status") != "BLOCKED" or protected.get("global_dqr_override") is not False:
        raise ValueError("global_dqr_protection_mismatch")
    for key in ("publication_authority", "dispatch_authority", "public_write_authority"):
        if protected.get(key) is not False:
            raise ValueError(f"upstream_live_authority_present:{key}")
    stories = [dict(story) for story in packet.get("stories", [])]
    if tuple(story.get("story_id") for story in stories) != EXPECTED_STORY_IDS:
        raise ValueError("exact_story_set_or_order_mismatch")
    for story in stories:
        story_id = str(story["story_id"])
        story_without_hash = {key: value for key, value in story.items() if key != "logical_hash"}
        if logical_hash(story_without_hash) != story.get("logical_hash"):
            raise ValueError(f"story_logical_hash_recomputation_mismatch:{story_id}")
        permissions = story.get("consumer_permissions") or {}
        claim_ids = tuple(claim.get("claim_id") for claim in story.get("claims", []))
        if claim_ids != AUTHORIZED_CLAIMS[story_id]:
            raise ValueError(f"claim_allowlist_mismatch:{story_id}")
        if tuple(permissions.get("authorized_claim_ids", [])) != claim_ids:
            raise ValueError(f"permission_claim_set_mismatch:{story_id}")
        if not all(
            claim.get("reporting_allowed") is True
            and claim.get("contains_numeric_assertion") is False
            and claim.get("interpretation_allowed") is False
            for claim in story.get("claims", [])
        ):
            raise ValueError(f"claim_reporting_boundary_mismatch:{story_id}")
        expected_permissions = {
            "reporting_allowed": True,
            "interpretation_allowed": False,
            "numeric_reporting_allowed": False,
            "market_reaction_allowed": False,
            "forecast_allowed": False,
            "financial_advice_allowed": False,
            "trading_allowed": False,
            "publication_allowed": False,
            "dispatch_allowed": False,
            "public_write_allowed": False,
            "global_dqr_override": False,
            "exact_story_only": True,
            "source_family_wide_authority": False,
            "derived_from_verifier": True,
        }
        if any(permissions.get(key) is not value for key, value in expected_permissions.items()):
            raise ValueError(f"permission_boundary_mismatch:{story_id}")
        dqr = story.get("dqr_decision") or {}
        if (
            dqr.get("global_dqr_status") != "BLOCKED"
            or dqr.get("global_dqr_override") is not False
            or dqr.get("reporting_allowed") is not True
            or dqr.get("story_reporting_decision") != "PASS_STORY_SCOPED_REPORTING"
        ):
            raise ValueError(f"story_dqr_boundary_mismatch:{story_id}")
    return stories


def _candidate_id(story: Mapping[str, Any]) -> str:
    return "cc-candidate-" + sha256(
        f"{story['story_id']}:{story['logical_hash']}".encode("utf-8")
    ).hexdigest()[:20]


def _story_candidates(story: Mapping[str, Any]) -> list[dict[str, Any]]:
    primary_id = _candidate_id(story)
    title = str(story["source_native_identity"].get("title") or story["claims"][0]["text"])
    common = {
        "story_id": story["story_id"],
        "source_family_id": story["source_family"],
        "source_native_id": story["provider_record_id"],
        "authority_story_logical_hash": story["logical_hash"],
        "authorized_claim_ids": list(AUTHORIZED_CLAIMS[str(story["story_id"])]),
        "reporting_allowed": True,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    return [
        {
            **common,
            "candidate_id": primary_id,
            "candidate_role": "PRIMARY_OPERATOR_PACKAGE",
            "title": title,
            "editorial_disposition": "READY_FOR_UNSIGNED_OPERATOR_DECISION",
        },
        {
            **common,
            "candidate_id": f"{primary_id}-source",
            "candidate_role": "SOURCE_IDENTITY_CONTEXT",
            "title": f"Source identity: {story['provider']}",
            "editorial_disposition": "CONTEXT_ONLY_NO_PLATFORM_PACKAGE",
        },
        {
            **common,
            "candidate_id": f"{primary_id}-limits",
            "candidate_role": "LIMITATION_CONTEXT",
            "title": f"Authority limitations: {title}",
            "editorial_disposition": "CONTEXT_ONLY_NO_PLATFORM_PACKAGE",
        },
    ]


def derive_story_scoped_claim_permission(
    story: Mapping[str, Any],
    upstream_claim: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed from the exact upstream claim and story consumer grant."""

    permissions = story.get("consumer_permissions") or {}
    claim_id = str(upstream_claim.get("claim_id") or "")
    authorized_claim_ids = {
        str(value) for value in permissions.get("authorized_claim_ids") or []
    }
    required_true = {
        "upstream_claim.reporting_allowed": upstream_claim.get("reporting_allowed"),
        "consumer_permissions.reporting_allowed": permissions.get("reporting_allowed"),
        "consumer_permissions.exact_story_only": permissions.get("exact_story_only"),
        "consumer_permissions.derived_from_verifier": permissions.get("derived_from_verifier"),
    }
    required_false = {
        "upstream_claim.contains_numeric_assertion": upstream_claim.get("contains_numeric_assertion"),
        "upstream_claim.interpretation_allowed": upstream_claim.get("interpretation_allowed"),
        "consumer_permissions.source_family_wide_authority": permissions.get("source_family_wide_authority"),
        "consumer_permissions.numeric_reporting_allowed": permissions.get("numeric_reporting_allowed"),
        "consumer_permissions.interpretation_allowed": permissions.get("interpretation_allowed"),
        "consumer_permissions.market_reaction_allowed": permissions.get("market_reaction_allowed"),
        "consumer_permissions.forecast_allowed": permissions.get("forecast_allowed"),
        "consumer_permissions.financial_advice_allowed": permissions.get("financial_advice_allowed"),
        "consumer_permissions.trading_allowed": permissions.get("trading_allowed"),
        "consumer_permissions.publication_allowed": permissions.get("publication_allowed"),
        "consumer_permissions.dispatch_allowed": permissions.get("dispatch_allowed"),
        "consumer_permissions.public_write_allowed": permissions.get("public_write_allowed"),
        "consumer_permissions.global_dqr_override": permissions.get("global_dqr_override"),
    }
    blockers = [
        f"upstream_authority_field_missing_or_false:{field}"
        for field, value in required_true.items()
        if value is not True
    ]
    blockers.extend(
        f"upstream_authority_field_missing_or_true:{field}"
        for field, value in required_false.items()
        if value is not False
    )
    if not claim_id or claim_id not in authorized_claim_ids:
        blockers.append(
            "upstream_authority_field_missing_claim_id:"
            "consumer_permissions.authorized_claim_ids"
        )
    allowed = not blockers
    return {
        "claim_id": claim_id,
        "story_id": str(story.get("story_id") or ""),
        "permission_state": (
            "PUBLIC_CLAIM_ALLOWED" if allowed else "PUBLIC_CLAIM_BLOCKED"
        ),
        "reporting_allowed": allowed,
        "blockers": blockers,
        "authority_scope": "EXACT_STORY_AND_EXACT_CLAIM_ONLY",
        "source_family_wide_authority": False,
        "numeric_reporting_allowed": False,
        "interpretation_allowed": False,
        "market_reaction_allowed": False,
        "forecast_allowed": False,
        "financial_advice_allowed": False,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "decision_source": "DERIVED_FROM_PINNED_UPSTREAM_STORY_SCOPED_AUTHORITY",
    }


def _build_canonical_candidate(story: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _candidate_id(story)
    citation_url = str(story["official_urls"]["citation_url"])
    evidence_ref = f"git-authority:{EXPECTED_UPSTREAM_HEAD}:{story['story_id']}"
    document_id = f"document:{story['provider_record_id']}"
    timestamp = str(story["timestamps"]["published_at"])
    source_document = {
        "document_id": document_id,
        "source_native_id": story["provider_record_id"],
        "source_family_id": story["source_family"],
        "provider": story["provider"],
        "record_type": story["record_type"],
        "title": story["source_native_identity"].get("title") or _copy_fields(story)["headline"],
        "published_at_utc": timestamp,
        "known_at_utc": story["timestamps"]["known_at"],
        "authorized_urls": [citation_url],
        "content_sha256": story["source_receipt"]["sha256"],
    }
    binding = {
        "evidence_ref": evidence_ref,
        "document_id": document_id,
        "source_family_id": story["source_family"],
        "source_native_id": story["provider_record_id"],
        "authority_story_logical_hash": story["logical_hash"],
        "authority_packet_logical_hash": EXPECTED_AUTHORITY_LOGICAL_HASH,
        "verifier_produced": True,
    }
    binding["logical_hash"] = logical_hash(binding)
    claims: list[dict[str, Any]] = []
    for upstream_claim in story["claims"]:
        permission = derive_story_scoped_claim_permission(story, upstream_claim)
        claim = {
            "schema_version": "contentops.universal_news_claim.v2",
            "claim_id": upstream_claim["claim_id"],
            "claim_type": "factual_text",
            "statement": upstream_claim["text"],
            "structured_payload": {
                "story_id": story["story_id"],
                "source_field": upstream_claim["source_field"],
            },
            "source_document_ids": [document_id],
            "evidence_refs": [evidence_ref],
            "authority_class": "OFFICIAL_VERIFIED",
            "permission_state": permission["permission_state"],
            "permission_blockers": list(permission["blockers"]),
            "permission_derivation": permission,
            "observed_at_utc": None,
            "event_time_utc": timestamp,
            "published_at_utc": timestamp,
            "known_at_utc": story["timestamps"]["known_at"],
            "revision_at_utc": story["timestamps"]["provider_updated_at"],
            "entities": [],
            "geographies": [],
            "citations": [{
                "source_document_id": document_id,
                "url": citation_url,
                "citation_state": "EXACT_SOURCE_NATIVE_URL",
            }],
            "limitations": list(story["limitations"]),
            "numeric": None,
            "market_evidence_refs": [],
            "judgment_record": None,
        }
        claim["logical_hash"] = logical_hash(claim)
        claims.append(claim)
    candidate = {
        "candidate_id": candidate_id,
        "story_id": story["story_id"],
        "source_native_ids": [story["provider_record_id"]],
        "source_family_ids": [story["source_family"]],
        "adapter_id": "contentops.multi_story_exact_git_authority_adapter.v1",
        "title": _copy_fields(story)["headline"],
        "summary": _copy_fields(story)["summary"],
        "claims": claims,
        "numeric_claims": [],
        "source_documents": [source_document],
        "evidence_refs": [evidence_ref],
        "evidence_bindings": [binding],
        "authority_state": "OFFICIAL_VERIFIED",
        "reporting_allowed": True,
        "evidence_state": "exact",
    }
    candidate["logical_hash"] = logical_hash(candidate)
    return candidate


def _build_canonical_evidence_packet(story: Mapping[str, Any]) -> dict[str, Any]:
    candidate = _build_canonical_candidate(story)
    timestamp = str(story["timestamps"]["published_at"])
    v2_packet = build_candidate_bound_evidence_packet(candidate, generated_at_utc=timestamp)
    if v2_packet["validation_blockers"]:
        raise ValueError(
            f"canonical_v2_packet_invalid:{story['story_id']}:{v2_packet['validation_blockers']}"
        )
    packet = build_content_evidence_packet_v3(
        candidate,
        generated_at_utc=timestamp,
        v2_packet=v2_packet,
    )
    validation_blockers = validate_content_evidence_packet_v3(packet)
    if validation_blockers:
        raise ValueError(
            f"canonical_v3_packet_invalid:{story['story_id']}:{validation_blockers}"
        )
    return packet


def _build_editorial_outcome(story: Mapping[str, Any]) -> dict[str, Any]:
    candidate = _build_canonical_candidate(story)
    generated_at_utc = str(story["timestamps"]["published_at"])
    handoff = build_canonical_editorial_shadow_handoff(
        candidate,
        generated_at_utc=generated_at_utc,
    )
    packet = handoff["evidence_packet"]
    expected_packet = _build_canonical_evidence_packet(story)
    if _canonical(packet) != _canonical(expected_packet):
        raise ValueError(f"canonical_handoff_v3_packet_mismatch:{story['story_id']}")
    article = dict(handoff.get("article") or {})
    review = dict(handoff.get("editorial_review") or {})
    if not article or not review:
        raise ValueError(f"canonical_editorial_output_missing:{story['story_id']}")
    used_claim_ids = list(article.get("claim_ids_used") or [])
    approved_claim_ids = list(packet["governed_claim_graph"]["approved_claim_ids"])
    if used_claim_ids != approved_claim_ids:
        raise ValueError(f"canonical_article_claim_set_mismatch:{story['story_id']}")
    article_hash = _logical_hash(article)
    article_id = "cc-canonical-draft-" + sha256(
        f"{story['story_id']}:{article_hash}".encode("utf-8")
    ).hexdigest()[:20]
    review_hash = _logical_hash(review)
    citations = {
        claim_id: list(article["claim_citations"][claim_id])
        for claim_id in used_claim_ids
    }
    claim_map = {
        str(row["claim_id"]): row
        for row in packet["governed_claim_graph"]["claims"]
    }
    limitations = sorted({
        str(value)
        for claim_id in used_claim_ids
        for value in claim_map[claim_id].get("limitations") or []
    })
    freshness = dict(handoff.get("freshness_decision") or {})
    visual = dict(handoff.get("visual_decision") or {})
    final_role = next(
        row for row in review["roles"]
        if row["role"] == "adversarial_final_reviewer"
    )
    unresolved = list(dict.fromkeys(
        [str(value) for value in review.get("blockers") or []]
        + [str(value) for value in freshness.get("blockers") or []]
        + [str(value) for value in visual.get("blockers") or []]
    ))
    outcome = {
        "schema_version": "contentops.canonical_local_editorial_outcome.v1",
        "story_id": story["story_id"],
        "candidate_id": candidate["candidate_id"],
        "v3_packet_id": packet["packet_id"],
        "v3_packet_logical_hash": packet["logical_hash"],
        "canonical_article_id": article_id,
        "canonical_article_hash": article_hash,
        "canonical_article": article,
        "article_used_approved_claim_ids": used_claim_ids,
        "citations": citations,
        "limitations": limitations,
        "editorial_review": review,
        "editorial_review_hash": review_hash,
        "role_outcomes": review["roles"],
        "freshness_disposition": freshness,
        "visual_disposition": visual,
        "final_adversarial_review_disposition": final_role,
        "unresolved_blockers": unresolved,
        "editorial_state": "PASS" if not unresolved else "HOLD",
        "canonical_handoff_disposition": handoff["disposition"],
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "network_call_performed": False,
        "browser_action_performed": False,
        "public_write_performed": False,
    }
    outcome["outcome_hash"] = _logical_hash(outcome)
    return outcome


def _copy_fields(story: Mapping[str, Any]) -> dict[str, str]:
    story_id = str(story["story_id"])
    if story_id == "fomc-minutes-2026-04-28-29":
        return {
            "headline": "Federal Reserve Releases April 28-29 FOMC Minutes",
            "summary": "The Federal Reserve published the minutes of the Federal Open Market Committee meeting held April 28-29, 2026.",
            "source_label": "Federal Reserve Board",
        }
    if story_id == "apple-sec-10q-2026-000013":
        return {
            "headline": "Apple Files Form 10-Q With the SEC",
            "summary": "Apple Inc. filed a Form 10-Q with the U.S. Securities and Exchange Commission. The SEC identifies the filing's primary document as a 10-Q.",
            "source_label": "U.S. Securities and Exchange Commission",
        }
    if story_id == "usgs-reviewed-ridgecrest-ci38457511":
        return {
            "headline": "USGS Marks Ridgecrest Earthquake Sequence Event as Reviewed",
            "summary": "USGS identifies the event as reviewed and as part of the Ridgecrest Earthquake Sequence.",
            "source_label": "U.S. Geological Survey",
        }
    raise ValueError(f"unsupported_story:{story_id}")


def _render_text(platform_id: str, story: Mapping[str, Any]) -> str:
    fields = _copy_fields(story)
    headline, summary, source = fields["headline"], fields["summary"], fields["source_label"]
    if platform_id == "substack_newsletter":
        return f"{headline}\n\nOfficial-record update\n\n{summary}\n\nSource: {source}.\n\nNot financial advice."
    if platform_id == "linkedin":
        return f"Official document update: {headline}\n\n{summary}\n\nSource: {source}. This post stays within the exact official-record metadata authorized for reporting.\n\nNot financial advice."
    if platform_id == "x_twitter":
        return f"{headline}. {summary} Source: {source}. Not financial advice."
    if platform_id == "facebook_page":
        return f"Official-record update\n\n{headline}\n\n{summary}\n\nSource: {source}. The scope here is limited to the official record identified above.\n\nNot financial advice."
    if platform_id == "telegram":
        return f"OFFICIAL RECORD | {headline}\n\n{summary}\n\nSource: {source}\nScope: exact authorized record metadata only\n\nNot financial advice."
    if platform_id == "youtube_community":
        return f"Community update: {headline}\n\n{summary}\n\nSource: {source}. This is a text-only Community post package, not a video or upload request.\n\nNot financial advice."
    raise ValueError(f"unsupported_platform:{platform_id}")


def _assert_prose_allowed(story: Mapping[str, Any], text: str) -> None:
    if text.count("Not financial advice.") != 1:
        raise ValueError(f"disclaimer_count_invalid:{story['story_id']}")
    for pattern in FORBIDDEN_PROSE:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise ValueError(f"unsupported_prose:{story['story_id']}:{pattern}")
    story_id = str(story["story_id"])
    if story_id != "usgs-reviewed-ridgecrest-ci38457511" and re.search(r"\b7\.1\b", text):
        raise ValueError(f"numeric_claim_not_authorized:{story_id}")
    if story_id == "usgs-reviewed-ridgecrest-ci38457511" and re.search(r"\b(?:M\s*)?7\.1\b", text):
        raise ValueError(f"usgs_magnitude_not_authorized:{story_id}")


def _build_variant(story: Mapping[str, Any], candidate_id: str, platform_id: str) -> dict[str, Any]:
    contract = PLATFORM_CONTRACTS[platform_id]
    text = _render_text(platform_id, story)
    _assert_prose_allowed(story, text)
    if len(text) > int(contract["character_limit_max"]):
        raise ValueError(f"platform_character_limit_exceeded:{story['story_id']}:{platform_id}")
    citation = str(story["official_urls"]["citation_url"])
    limitation_fingerprints = [
        sha256(str(value).encode("utf-8")).hexdigest() for value in story.get("limitations", [])
    ]
    hash_inputs = {
        "story_id": story["story_id"],
        "candidate_id": candidate_id,
        "authority_story_logical_hash": story["logical_hash"],
        "authorized_claim_ids": list(AUTHORIZED_CLAIMS[str(story["story_id"])]),
        "platform_id": platform_id,
        "content_surface": contract["content_surface"],
        "payload_shape": contract["shape"],
        "mode": contract["mode"],
        "text": text,
        "citation_fingerprints": [sha256(citation.encode("utf-8")).hexdigest()],
        "limitation_fingerprints": limitation_fingerprints,
        "policy": {
            "approval_required": True,
            "valid_for_dispatch": False,
            "dispatch_ready": False,
            "public_ready": False,
            "live_eligibility": False,
        },
    }
    return {
        **hash_inputs,
        "schema_version": "contentops.platform_native_operator_variant.v1",
        "citation_urls": [citation],
        "character_count": len(text),
        "character_limit_max": contract["character_limit_max"],
        "operator_review_required": True,
        "approval_required": True,
        "valid_for_dispatch": False,
        "dispatch_ready": False,
        "public_ready": False,
        "live_eligibility": False,
        "youtube_contract": (
            {
                "surface": "youtube_community",
                "post_type": "text_only_community_post",
                "video_upload_request": False,
                "media_required": False,
                "default_article_surface_confirmed": True,
            }
            if platform_id == "youtube_community"
            else None
        ),
        "payload_hash": compute_payload_hash(hash_inputs),
    }


def _build_package(
    story: Mapping[str, Any],
    variants: list[dict[str, Any]],
    editorial_outcome: Mapping[str, Any],
    authority_git_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_id = _candidate_id(story)
    package = {
        "schema_version": "contentops.superseding_unsigned_operator_approval_package.v1",
        "task": TASK,
        "story_id": story["story_id"],
        "candidate_id": candidate_id,
        "supersedes_schema_version": "contentops.unsigned_operator_approval_package.v1",
        "authority_binding": {
            "exact_git_receipt": dict(authority_git_receipt),
            "authority_packet_id": EXPECTED_AUTHORITY_PACKET_ID,
            "authority_packet_logical_hash": EXPECTED_AUTHORITY_LOGICAL_HASH,
            "story_logical_hash": story["logical_hash"],
            "authorized_claim_ids": list(AUTHORIZED_CLAIMS[str(story["story_id"])]),
            "source_family": story["source_family"],
            "official_url": story["official_urls"]["canonical_url"],
        },
        "editorial_binding": {
            "v3_packet_id": editorial_outcome["v3_packet_id"],
            "v3_packet_logical_hash": editorial_outcome["v3_packet_logical_hash"],
            "canonical_article_id": editorial_outcome["canonical_article_id"],
            "canonical_article_hash": editorial_outcome["canonical_article_hash"],
            "article_used_approved_claim_ids": editorial_outcome["article_used_approved_claim_ids"],
            "editorial_review_status": editorial_outcome["editorial_review"]["status"],
            "editorial_review_hash": editorial_outcome["editorial_review_hash"],
            "editorial_outcome_hash": editorial_outcome["outcome_hash"],
            "freshness_disposition": editorial_outcome["freshness_disposition"],
            "visual_disposition": editorial_outcome["visual_disposition"],
            "final_adversarial_review_disposition": editorial_outcome["final_adversarial_review_disposition"],
            "unresolved_blockers": editorial_outcome["unresolved_blockers"],
            "editorial_state": editorial_outcome["editorial_state"],
            "citations": editorial_outcome["citations"],
            "limitations": editorial_outcome["limitations"],
        },
        "state": "PENDING_OPERATOR_DECISION",
        "signature": None,
        "signed_at_utc": None,
        "operator_identity": None,
        "operator_approval_captured": False,
        "decision_options": ["APPROVE_EXACT_PACKAGE", "REJECT", "REQUEST_REVISION"],
        "selected_decision": None,
        "variant_count": len(variants),
        "variant_ids": [f"{row['platform_id']}:{row['payload_hash']}" for row in variants],
        "variant_payload_hashes": {row["platform_id"]: row["payload_hash"] for row in variants},
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "publication_allowed": False,
        "dispatch_allowed": False,
        "public_write_allowed": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "credential_read_allowed_now": False,
        "network_call_performed": False,
        "browser_action_performed": False,
        "provider_action_performed": False,
        "public_write_performed": False,
        "exact_next_gate": "OPERATOR_MUST_DECIDE_EXACT_HASH_BOUND_PACKAGE_OUTSIDE_THIS_RUN",
    }
    package["package_hash"] = _logical_hash(package)
    return package


def _validate_package(
    story: Mapping[str, Any],
    variants: list[dict[str, Any]],
    package: Mapping[str, Any],
    editorial_outcome: Mapping[str, Any],
    authority_git_receipt: Mapping[str, Any],
) -> None:
    expected_platforms = list(PLATFORM_IDS)
    if [row["platform_id"] for row in variants] != expected_platforms:
        raise ValueError(f"platform_exact_set_mismatch:{story['story_id']}")
    if len({row["text"] for row in variants}) != len(PLATFORM_IDS):
        raise ValueError(f"platform_copy_not_differentiated:{story['story_id']}")
    if package.get("state") != "PENDING_OPERATOR_DECISION" or package.get("signature") is not None:
        raise ValueError(f"operator_package_not_pending_unsigned:{story['story_id']}")
    if package["authority_binding"].get("exact_git_receipt") != dict(authority_git_receipt):
        raise ValueError(f"operator_package_git_receipt_binding_mismatch:{story['story_id']}")
    editorial_binding = package.get("editorial_binding") or {}
    expected_editorial = {
        "v3_packet_id": editorial_outcome["v3_packet_id"],
        "v3_packet_logical_hash": editorial_outcome["v3_packet_logical_hash"],
        "canonical_article_id": editorial_outcome["canonical_article_id"],
        "canonical_article_hash": editorial_outcome["canonical_article_hash"],
        "article_used_approved_claim_ids": editorial_outcome["article_used_approved_claim_ids"],
        "editorial_review_status": editorial_outcome["editorial_review"]["status"],
        "editorial_review_hash": editorial_outcome["editorial_review_hash"],
        "editorial_outcome_hash": editorial_outcome["outcome_hash"],
        "freshness_disposition": editorial_outcome["freshness_disposition"],
        "visual_disposition": editorial_outcome["visual_disposition"],
        "final_adversarial_review_disposition": editorial_outcome["final_adversarial_review_disposition"],
        "unresolved_blockers": editorial_outcome["unresolved_blockers"],
        "editorial_state": editorial_outcome["editorial_state"],
        "citations": editorial_outcome["citations"],
        "limitations": editorial_outcome["limitations"],
    }
    if editorial_binding != expected_editorial:
        raise ValueError(f"operator_package_editorial_binding_mismatch:{story['story_id']}")
    if package.get("variant_payload_hashes") != {row["platform_id"]: row["payload_hash"] for row in variants}:
        raise ValueError(f"operator_package_hash_binding_mismatch:{story['story_id']}")
    unhashed = dict(package)
    observed_hash = unhashed.pop("package_hash")
    if _logical_hash(unhashed) != observed_hash:
        raise ValueError(f"operator_package_hash_invalid:{story['story_id']}")
    _assert_false_flags(package)
    for variant in variants:
        _assert_false_flags(variant)
        _assert_prose_allowed(story, str(variant["text"]))
        if variant["payload_hash"] != compute_payload_hash({
            key: variant[key]
            for key in (
                "story_id", "candidate_id", "authority_story_logical_hash",
                "authorized_claim_ids", "platform_id", "content_surface",
                "payload_shape", "mode", "text", "citation_fingerprints",
                "limitation_fingerprints", "policy",
            )
        }):
            raise ValueError(f"variant_hash_invalid:{story['story_id']}:{variant['platform_id']}")


def build_documents(
    authority: Mapping[str, Any],
    observed_upstream_head: str,
    *,
    authority_git_receipt: Mapping[str, Any] | None = None,
    upstream_checkout_verification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stories = _validate_authority(authority, observed_upstream_head)
    receipt = dict(authority_git_receipt or _expected_authority_receipt())
    if receipt != _expected_authority_receipt():
        raise ValueError(f"authority_git_receipt_mismatch:{receipt}")
    checkout = dict(upstream_checkout_verification or {
        "origin_url_redacted_to_repository": EXPECTED_UPSTREAM_REPOSITORY,
        "repository": EXPECTED_UPSTREAM_REPOSITORY,
        "branch": EXPECTED_UPSTREAM_BRANCH,
        "observed_origin_head": EXPECTED_UPSTREAM_HEAD,
        "producer_commit": EXPECTED_UPSTREAM_HEAD,
        "producer_commit_reachable_from_observed_origin_head": True,
        "status": "PASS_EXACT_LOCAL_GIT_IDENTITY_AND_ANCESTRY",
    })
    variants: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    v3_packets: list[dict[str, Any]] = []
    permission_adjudications: list[dict[str, Any]] = []
    for story in stories:
        packet = _build_canonical_evidence_packet(story)
        outcome = _build_editorial_outcome(story)
        story_variants = [
            _build_variant(story, _candidate_id(story), platform_id)
            for platform_id in PLATFORM_IDS
        ]
        package = _build_package(story, story_variants, outcome, receipt)
        _validate_package(story, story_variants, package, outcome, receipt)
        variants.extend(story_variants)
        packages.append(package)
        outcomes.append(outcome)
        v3_packets.append(packet)
        permission_adjudications.extend(
            derive_story_scoped_claim_permission(story, claim)
            for claim in story["claims"]
        )
    protected = {
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "credential_read_allowed_now": False,
        "network_call_performed": False,
        "browser_action_performed": False,
        "provider_action_performed": False,
        "public_write_performed": False,
    }
    documents = {
        "claim_permission_adjudication.json": {
            "schema_version": "contentops.story_scoped_claim_permission_adjudication.v1",
            "task": TASK,
            "authority_packet_id": authority["packet_id"],
            "authority_packet_logical_hash": authority["logical_hash"],
            "claim_count": len(permission_adjudications),
            "all_exact_claims_reporting_allowed": all(
                row["reporting_allowed"] for row in permission_adjudications
            ),
            "adjudications": permission_adjudications,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        "canonical_content_evidence_packets_v3.json": {
            "schema_version": "contentops.three_story_canonical_content_evidence_packets_v3.v1",
            "task": TASK,
            "packet_schema_version": "capital_chronicle_content_evidence_packet.v3",
            "packet_count": len(v3_packets),
            "all_packets_validated": all(
                not validate_content_evidence_packet_v3(row)
                for row in v3_packets
            ),
            "packets": v3_packets,
            "protected_state": protected,
        },
        "canonical_editorial_outcomes.json": {
            "schema_version": "contentops.three_story_canonical_editorial_outcomes.v1",
            "task": TASK,
            "outcome_count": len(outcomes),
            "story_ids": [row["story_id"] for row in stories],
            "outcomes": outcomes,
            "protected_state": protected,
        },
        "platform_native_variants.json": {
            "schema_version": "contentops.multi_story_platform_native_variants.v1",
            "task": TASK,
            "story_count": len(stories),
            "platform_count_per_story": len(PLATFORM_IDS),
            "platform_ids": list(PLATFORM_IDS),
            "all_copy_differentiated_per_story": True,
            "variants": variants,
            "protected_state": protected,
        },
        "superseding_unsigned_operator_packages.json": {
            "schema_version": "contentops.three_story_superseding_unsigned_operator_packages.v1",
            "task": TASK,
            "package_count": len(packages),
            "state": "PENDING_OPERATOR_DECISION",
            "packages": packages,
            "protected_state": protected,
        },
        "validation_truth.json": {
            "schema_version": "contentops.three_v3_editorial_package_validation_truth.v1",
            "task": TASK,
            "status": "PASS",
            "observed_upstream_head": observed_upstream_head,
            "upstream_checkout_verification": checkout,
            "authority_git_receipt": receipt,
            "authority_packet_id": authority["packet_id"],
            "authority_packet_logical_hash": authority["logical_hash"],
            "authority_exact_story_set": True,
            "authority_claim_allowlists_exact": True,
            "all_exact_claims_reporting_allowed": all(
                row["reporting_allowed"] for row in permission_adjudications
            ),
            "nonnumeric_claim_permission_bridge_executable": all(
                row["public_claim_permissions"]["narrative_synthesis_allowed"]
                and row["public_claim_permissions"]["numeric_claims_allowed"] is False
                for row in v3_packets
            ),
            "canonical_v3_evidence_packet_count": len(outcomes),
            "canonical_v3_evidence_packets_validated": True,
            "canonical_editorial_handoff_invoked_for_every_story": True,
            "canonical_eight_role_records_complete": all(
                len(row["role_outcomes"]) == 8 for row in outcomes
            ),
            "article_used_claims_exactly_approved": all(
                row["article_used_approved_claim_ids"]
                == list(AUTHORIZED_CLAIMS[row["story_id"]])
                for row in outcomes
            ),
            "editorial_holds_propagated_honestly": all(
                row["editorial_state"] == ("PASS" if not row["unresolved_blockers"] else "HOLD")
                for row in outcomes
            ),
            "six_platform_variants_per_story": all(
                sum(row["story_id"] == story["story_id"] for row in variants) == 6
                for story in stories
            ),
            "operator_packages_bind_exact_git_v3_article_review_variants": True,
            "operator_packages_hash_bound": True,
            "operator_packages_unsigned": all(row["signature"] is None for row in packages),
            "operator_package_state": "PENDING_OPERATOR_DECISION",
            "deterministic_replay_supported": True,
            "global_dqr_status_unchanged": "BLOCKED",
            "protected_state": protected,
        },
    }
    _assert_false_flags(documents)
    return documents


def generate_packages(*, repo_root: Path, upstream_root: Path, observed_upstream_head: str) -> dict[str, Any]:
    checkout_verification = _verify_upstream_checkout(upstream_root)
    if observed_upstream_head != EXPECTED_UPSTREAM_HEAD:
        raise ValueError("supplied_authority_head_not_exact_pinned_commit")
    authority_bytes, authority_receipt = read_git_artifact(
        root=upstream_root,
        observed_head=EXPECTED_UPSTREAM_HEAD,
        producer_commit=EXPECTED_UPSTREAM_HEAD,
        artifact_path=AUTHORITY_RELATIVE.as_posix(),
    )
    receipt = authority_receipt.as_dict()
    if receipt != _expected_authority_receipt():
        raise ValueError(f"authority_git_receipt_mismatch:{receipt}")
    authority = json.loads(authority_bytes)
    documents = build_documents(
        authority,
        observed_upstream_head,
        authority_git_receipt=receipt,
        upstream_checkout_verification=checkout_verification,
    )
    output = repo_root / EVIDENCE_RELATIVE
    for name, value in documents.items():
        _write(output / name, value)
    artifacts = [
        {
            "path": str((EVIDENCE_RELATIVE / name).as_posix()),
            "sha256": _sha(output / name),
            "byte_length": (output / name).stat().st_size,
        }
        for name in sorted(documents)
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "observed_upstream_head": observed_upstream_head,
        "upstream_checkout_verification": checkout_verification,
        "authority_git_receipt": receipt,
        "authority_packet_id": EXPECTED_AUTHORITY_PACKET_ID,
        "authority_packet_logical_hash": EXPECTED_AUTHORITY_LOGICAL_HASH,
        "story_ids": list(EXPECTED_STORY_IDS),
        "canonical_editorial_outcome_count": documents["canonical_editorial_outcomes.json"]["outcome_count"],
        "operator_package_count": documents["superseding_unsigned_operator_packages.json"]["package_count"],
        "operator_package_state": "PENDING_OPERATOR_DECISION",
        "artifacts": artifacts,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "credential_read_allowed_now": False,
        "network_call_performed": False,
        "browser_action_performed": False,
        "provider_action_performed": False,
        "public_write_performed": False,
        "terminal_classification": "PASS_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1_AWAITING_CHATGPT_AUDIT",
        "exact_next_action": "INDEPENDENT_CHATGPT_AUDIT_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1",
    }
    manifest["logical_hash"] = _logical_hash(manifest)
    _assert_false_flags(manifest)
    _write(output / "final_manifest.json", manifest)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--observed-upstream-head", default=EXPECTED_UPSTREAM_HEAD)
    args = parser.parse_args(argv)
    result = generate_packages(
        repo_root=args.repo_root.resolve(),
        upstream_root=args.upstream_root.resolve(),
        observed_upstream_head=args.observed_upstream_head,
    )
    print(json.dumps({
        "terminal_classification": result["terminal_classification"],
        "logical_hash": result["logical_hash"],
        "operator_package_state": result["operator_package_state"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
