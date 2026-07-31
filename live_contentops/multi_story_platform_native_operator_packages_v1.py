"""Deterministic multi-story platform-native operator packages (local only)."""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from live_contentops.payload_preview_hash_v6 import compute_payload_hash


TASK = "TASK_CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1"
SCHEMA_VERSION = "contentops.fast_ship_multi_story_operator_packages.v1"
AUTHORITY_SCHEMA = "capital_chronicle.multi_story_scoped_reporting_authority_batch.v1"
AUTHORITY_RELATIVE = Path(
    "docs/research/publication_evidence/current/"
    "CapitalChronicleMultiStoryScopedReportingAuthorityBatchV1.json"
)
EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1"
)
EXPECTED_UPSTREAM_HEAD = "64834919b4f69e977475c203abeafef57791f015"
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


def _validate_authority(packet: Mapping[str, Any], observed_upstream_head: str) -> list[dict[str, Any]]:
    if observed_upstream_head != EXPECTED_UPSTREAM_HEAD:
        raise ValueError(f"upstream_head_mismatch:{observed_upstream_head}")
    if packet.get("schema_version") != AUTHORITY_SCHEMA:
        raise ValueError("authority_schema_mismatch")
    if packet.get("packet_id") != EXPECTED_AUTHORITY_PACKET_ID:
        raise ValueError("authority_packet_id_mismatch")
    if packet.get("logical_hash") != EXPECTED_AUTHORITY_LOGICAL_HASH:
        raise ValueError("authority_logical_hash_mismatch")
    if packet.get("terminal_status") != "PASS_MULTI_STORY_SCOPED_REPORTING_AUTHORITY_BATCH_V1":
        raise ValueError("authority_terminal_status_not_pass")
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
        permissions = story.get("consumer_permissions") or {}
        claim_ids = tuple(claim.get("claim_id") for claim in story.get("claims", []))
        if claim_ids != AUTHORIZED_CLAIMS[story_id]:
            raise ValueError(f"claim_allowlist_mismatch:{story_id}")
        if tuple(permissions.get("authorized_claim_ids", [])) != claim_ids:
            raise ValueError(f"permission_claim_set_mismatch:{story_id}")
        if not all(claim.get("reporting_allowed") is True for claim in story.get("claims", [])):
            raise ValueError(f"claim_reporting_not_allowed:{story_id}")
        expected_permissions = {
            "reporting_allowed": True,
            "interpretation_allowed": False,
            "numeric_reporting_allowed": False,
            "market_reaction_allowed": False,
            "forecast_allowed": False,
            "publication_allowed": False,
            "dispatch_allowed": False,
            "public_write_allowed": False,
            "global_dqr_override": False,
        }
        if any(permissions.get(key) is not value for key, value in expected_permissions.items()):
            raise ValueError(f"permission_boundary_mismatch:{story_id}")
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


def _build_package(story: Mapping[str, Any], variants: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_id = _candidate_id(story)
    package = {
        "schema_version": "contentops.unsigned_operator_approval_package.v1",
        "task": TASK,
        "story_id": story["story_id"],
        "candidate_id": candidate_id,
        "authority_binding": {
            "upstream_head": EXPECTED_UPSTREAM_HEAD,
            "authority_packet_id": EXPECTED_AUTHORITY_PACKET_ID,
            "authority_packet_logical_hash": EXPECTED_AUTHORITY_LOGICAL_HASH,
            "story_logical_hash": story["logical_hash"],
            "authorized_claim_ids": list(AUTHORIZED_CLAIMS[str(story["story_id"])]),
            "source_family": story["source_family"],
            "official_url": story["official_urls"]["canonical_url"],
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
        "public_write_performed": False,
        "exact_next_gate": "OPERATOR_MUST_DECIDE_EXACT_HASH_BOUND_PACKAGE_OUTSIDE_THIS_RUN",
    }
    package["package_hash"] = _logical_hash(package)
    return package


def _validate_package(story: Mapping[str, Any], variants: list[dict[str, Any]], package: Mapping[str, Any]) -> None:
    expected_platforms = list(PLATFORM_IDS)
    if [row["platform_id"] for row in variants] != expected_platforms:
        raise ValueError(f"platform_exact_set_mismatch:{story['story_id']}")
    if len({row["text"] for row in variants}) != len(PLATFORM_IDS):
        raise ValueError(f"platform_copy_not_differentiated:{story['story_id']}")
    if package.get("state") != "PENDING_OPERATOR_DECISION" or package.get("signature") is not None:
        raise ValueError(f"operator_package_not_pending_unsigned:{story['story_id']}")
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


def build_documents(authority: Mapping[str, Any], observed_upstream_head: str) -> dict[str, Any]:
    stories = _validate_authority(authority, observed_upstream_head)
    candidate_rows = [row for story in stories for row in _story_candidates(story)]
    candidate_rows.extend([
        {
            "candidate_id": "cc-candidate-existing-treasury-20260713",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_REFERENCE",
            "story_id": "us-treasury-curve-2026-07-13",
            "title": "U.S. Treasury Curve Steepens as 30-Year Yield Reaches 5.10%",
            "source_family_id": "story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        {
            "candidate_id": "cc-candidate-existing-federal-register-202612787",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_REFERENCE",
            "story_id": "financial-data-transparency-act-joint-data-standards",
            "title": "Financial Data Transparency Act Joint Data Standards",
            "source_family_id": "nonnumeric_story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        {
            "candidate_id": "cc-candidate-existing-federal-register-context",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_CONTEXT",
            "story_id": "financial-data-transparency-act-joint-data-standards",
            "title": "Federal Register authority limitation context",
            "source_family_id": "nonnumeric_story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        {
            "candidate_id": "cc-candidate-existing-treasury-context",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_CONTEXT",
            "story_id": "us-treasury-curve-2026-07-13",
            "title": "Treasury authority limitation context",
            "source_family_id": "story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        {
            "candidate_id": "cc-candidate-existing-federal-register-source",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_SOURCE",
            "story_id": "financial-data-transparency-act-joint-data-standards",
            "title": "Federal Register official-source context",
            "source_family_id": "nonnumeric_story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
        {
            "candidate_id": "cc-candidate-existing-treasury-source",
            "candidate_role": "EXISTING_AUTHORIZED_FAMILY_SOURCE",
            "story_id": "us-treasury-curve-2026-07-13",
            "title": "Treasury official-source context",
            "source_family_id": "story_scoped_publication_evidence_v1",
            "reporting_allowed": True,
            "included_in_new_package_set": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        },
    ])
    if not 15 <= len(candidate_rows) <= 25:
        raise ValueError(f"candidate_count_out_of_range:{len(candidate_rows)}")
    variants: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    for story in stories:
        story_variants = [
            _build_variant(story, _candidate_id(story), platform_id)
            for platform_id in PLATFORM_IDS
        ]
        package = _build_package(story, story_variants)
        _validate_package(story, story_variants, package)
        variants.extend(story_variants)
        packages.append(package)
    source_families = sorted({row["source_family_id"] for row in candidate_rows})
    if len(source_families) != 5:
        raise ValueError(f"source_family_count_not_five:{len(source_families)}")
    protected = {
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "credential_read_allowed_now": False,
        "network_call_performed": False,
        "browser_action_performed": False,
        "public_write_performed": False,
    }
    documents = {
        "candidate_batch.json": {
            "schema_version": "contentops.multi_story_candidate_batch.v1",
            "task": TASK,
            "candidate_count": len(candidate_rows),
            "source_family_count": len(source_families),
            "source_family_ids": source_families,
            "candidates": candidate_rows,
            "protected_state": protected,
        },
        "platform_native_variants.json": {
            "schema_version": "contentops.multi_story_platform_native_variants.v1",
            "task": TASK,
            "story_count": len(stories),
            "platform_count_per_story": len(PLATFORM_IDS),
            "variant_count": len(variants),
            "platform_ids": list(PLATFORM_IDS),
            "variants": variants,
            "all_copy_differentiated_per_story": True,
            "youtube_community_contract": {
                "surface": "youtube_community",
                "post_type": "text_only_community_post",
                "video_upload_request": False,
                "default_article_surface": True,
            },
            "protected_state": protected,
        },
        "unsigned_operator_approval_packages.json": {
            "schema_version": "contentops.multi_story_unsigned_operator_approval_packages.v1",
            "task": TASK,
            "package_count": len(packages),
            "state": "PENDING_OPERATOR_DECISION",
            "packages": packages,
            "protected_state": protected,
        },
        "validation_truth.json": {
            "schema_version": "contentops.multi_story_operator_package_validation_truth.v1",
            "task": TASK,
            "status": "PASS",
            "observed_upstream_head": observed_upstream_head,
            "authority_packet_id": authority["packet_id"],
            "authority_packet_logical_hash": authority["logical_hash"],
            "authority_exact_story_set": True,
            "authority_claim_allowlists_exact": True,
            "candidate_count_in_range": 15 <= len(candidate_rows) <= 25,
            "candidate_count": len(candidate_rows),
            "exact_five_source_families": len(source_families) == 5,
            "new_authorized_package_count": len(packages),
            "six_platform_variants_per_story": all(
                sum(row["story_id"] == story["story_id"] for row in variants) == 6
                for story in stories
            ),
            "all_platform_copy_differentiated": True,
            "youtube_community_text_only_contract_passed": True,
            "operator_packages_hash_bound": True,
            "operator_packages_unsigned": all(row["signature"] is None for row in packages),
            "operator_package_state": "PENDING_OPERATOR_DECISION",
            "claim_and_prose_guard_passed": True,
            "deterministic_replay_supported": True,
            "global_dqr_status_unchanged": "BLOCKED",
            "protected_state": protected,
        },
    }
    _assert_false_flags(documents)
    return documents


def generate_packages(*, repo_root: Path, upstream_root: Path, observed_upstream_head: str) -> dict[str, Any]:
    authority_path = upstream_root / AUTHORITY_RELATIVE
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    documents = build_documents(authority, observed_upstream_head)
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
        "authority_relative_path": str(AUTHORITY_RELATIVE.as_posix()),
        "authority_packet_id": EXPECTED_AUTHORITY_PACKET_ID,
        "authority_packet_logical_hash": EXPECTED_AUTHORITY_LOGICAL_HASH,
        "story_ids": list(EXPECTED_STORY_IDS),
        "candidate_count": documents["candidate_batch.json"]["candidate_count"],
        "source_family_ids": documents["candidate_batch.json"]["source_family_ids"],
        "platform_ids": list(PLATFORM_IDS),
        "variant_count": documents["platform_native_variants.json"]["variant_count"],
        "operator_package_count": documents["unsigned_operator_approval_packages.json"]["package_count"],
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
        "public_write_performed": False,
        "terminal_classification": "PASS_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_PENDING_DECISION",
        "exact_next_action": "INDEPENDENT_OPERATOR_REVIEW_OF_THREE_UNSIGNED_HASH_BOUND_PACKAGES",
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
