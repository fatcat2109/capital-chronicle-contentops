from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageDraw

from live_contentops.newsroom_assignment_scheduler_v1 import (
    ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
    classify_evidence_friction,
    select_first_viable_rolling_x_cluster,
)
from live_contentops.tier1_editorial_quality_v1 import remove_repeated_conclusion
from live_contentops.visual_asset_discovery_v1 import (
    build_openverse_provider,
    build_wikimedia_commons_provider,
    discover_and_rank_assets,
    validate_asset_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ARTICLE = ROOT / "docs" / "automation" / (
    "DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1"
) / "contentops_database_publication_live_20260714_1" / "article_manifest_v1.json"


def _ranking_image(*, vertical: bool) -> bytes:
    image = Image.new("RGB", (120, 80), "black")
    draw = ImageDraw.Draw(image)
    if vertical:
        draw.rectangle((60, 0, 120, 80), fill="white")
    else:
        draw.rectangle((0, 40, 120, 80), fill="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_real_provider_contracts_resolve_original_rights_and_rank_multiple_sources() -> None:
    intent = {
        "visual_intent": "INFRASTRUCTURE_CONTEXT",
        "queries": ["Strait Hormuz tanker traffic documentary photograph"],
    }

    def commons_json(_url: str):
        return {
            "query": {"pages": [{
                "title": "File:Oil tanker in the Strait of Hormuz.jpg",
                "canonicalurl": "https://commons.wikimedia.org/wiki/File:Oil_tanker_Hormuz.jpg",
                "imageinfo": [{
                    "url": "https://upload.wikimedia.org/original-hormuz.jpg",
                    "thumburl": "https://upload.wikimedia.org/thumb-hormuz.jpg",
                    "width": 2400,
                    "height": 1600,
                    "sha1": "a" * 40,
                    "extmetadata": {
                        "LicenseShortName": {"value": "CC BY-SA 4.0"},
                        "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
                        "UsageTerms": {"value": "Creative Commons Attribution-Share Alike 4.0"},
                        "Artist": {"value": "Documentary Photographer"},
                        "ImageDescription": {"value": "Oil tanker traffic in the Strait of Hormuz"},
                    },
                }],
            }]},
        }

    def openverse_json(_url: str):
        return {"results": [{
            "id": "openverse-hormuz-1",
            "title": "Tanker traffic near the Strait of Hormuz",
            "creator": "Open photographer",
            "provider": "flickr",
            "url": "https://images.example/original-tanker.jpg",
            "thumbnail": "https://images.example/thumb-tanker.jpg",
            "foreign_landing_url": "https://images.example/source/tanker",
            "license": "by",
            "license_version": "4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "width": 1800,
            "height": 1200,
            "attribution": "Open photographer / CC BY 4.0",
            "tags": [{"name": "oil tanker"}, {"name": "shipping"}],
        }]}

    commons = build_wikimedia_commons_provider(
        json_fetcher=commons_json,
        bytes_fetcher=lambda _url: _ranking_image(vertical=True),
        candidates_per_query=3,
    )
    openverse = build_openverse_provider(
        json_fetcher=openverse_json,
        bytes_fetcher=lambda _url: _ranking_image(vertical=False),
        candidates_per_query=3,
    )
    result = discover_and_rank_assets(
        {"intents": [intent]}, providers=[commons, openverse], maximum_selected=2
    )

    assert result["candidate_count"] == 2
    assert result["eligible_count"] == 2
    assert result["selected_count"] == 2
    assert {row["discovery_provider"] for row in result["selected_assets"]} == {
        "wikimedia_commons", "openverse"
    }
    assert all(row["source_page_url"].startswith("https://") for row in result["selected_assets"])
    assert all(row["original_asset_url"].startswith("https://") for row in result["selected_assets"])
    assert all(row["rights_status"] == "OPEN_LICENSED" for row in result["selected_assets"])
    assert all(row["perceptual_hash_basis"] == "DISCOVERY_THUMBNAIL_NOT_DELIVERY_ASSET" for row in result["selected_assets"])


def test_unknown_rights_and_thumbnail_delivery_are_rejected() -> None:
    base = {
        "visual_intent": "LOCATION_CONTEXT",
        "discovery_provider": "openverse",
        "query": "shipping route",
        "source_page_url": "https://example.org/source",
        "original_asset_url": "https://example.org/image.jpg",
        "discovery_thumbnail_url": "https://example.org/thumb.jpg",
        "creator_publisher": "Creator",
        "reuse_basis": "Unknown",
        "attribution": "Creator",
        "width": 1600,
        "height": 900,
        "content_hash": "source-sha256:" + "b" * 64,
        "perceptual_hash": "0123456789abcdef",
        "documentary_generated_classification": "DOCUMENTARY",
        "rights_status": "UNKNOWN",
    }
    assert "rights_not_verified_reusable" in validate_asset_candidate(base)["blockers"]
    thumbnail = {
        **base,
        "rights_status": "PUBLIC_DOMAIN",
        "reuse_basis": "Public domain",
        "original_asset_url": base["discovery_thumbnail_url"],
    }
    assert "search_result_thumbnail_not_original_asset" in validate_asset_candidate(thumbnail)["blockers"]


def _assignment(*, story_type_text: str = "Agency publishes a routine notice") -> dict:
    return {
        "schema_version": ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
        "decision": "SELECT_STORY",
        "ranked_clusters": [{
            "cluster_id": "cluster-1",
            "rank": 1,
            "headline_ids": ["headline-1"],
            "leaf_cluster_ids": ["leaf-1"],
            "article_mode": "breaking",
            "resolved_article_mode": "BREAKING_BRIEF",
            "leaf_summaries": [story_type_text],
        }],
    }


def _ordinary_blocked_receipt(request: dict) -> dict:
    document = {
        "document_id": "document-1",
        "title": "Agency publishes a routine notice for regulated firms",
        "publisher": "Reuters",
        "source_identity": "reuters.com",
        "source_authority_class": "reputable_secondary_source",
        "source_url": "https://example.org/routine-notice",
        "canonical_content_text": "Agency publishes a routine notice for regulated firms.",
        "public_claim_allowed": True,
    }
    return {
        "status": "BLOCKED",
        "cluster_id": request["cluster_id"],
        "headline_ids": request["headline_ids"],
        "provided_evidence_capabilities": [],
        "evidence_documents": [document],
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS",
            "risk_tier": "ORDINARY",
            "core_factual_proposition": document["title"],
            "source_title": document["title"],
            "publisher": "Reuters",
            "source_url": document["source_url"],
            "evidence_document_id": document["document_id"],
            "source_authority_class": "reputable_secondary_source",
        },
        "blockers": ["required_evidence_capability_missing:official_document"],
        "capital_chronicle_authority_verified": False,
        "numeric_evidence_required": False,
    }


def test_valid_ordinary_packet_removes_duplicate_capability_and_dossier_ceremony() -> None:
    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(),
        acquire_evidence=_ordinary_blocked_receipt,
        story_type_by_cluster={"cluster-1": "regulatory_fiscal_event"},
    )
    attempt = result["rank_attempts"][0]

    assert result["status"] == "SUCCESS"
    assert attempt["blockers"] == []
    assert "supported_claims_missing" in attempt["ordinary_policy_ceremony_reductions"]
    assert any(
        value.startswith("required_evidence_capability_missing:")
        for value in attempt["ordinary_policy_ceremony_reductions"]
    )


def test_ordinary_packet_cannot_reduce_friction_when_source_binding_is_spoofed() -> None:
    def mismatched_receipt(request: dict) -> dict:
        receipt = _ordinary_blocked_receipt(request)
        receipt["minimum_trustworthy_evidence_packet"]["source_url"] = (
            "https://example.org/a-different-document"
        )
        return receipt

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(),
        acquire_evidence=mismatched_receipt,
        story_type_by_cluster={"cluster-1": "regulatory_fiscal_event"},
    )
    attempt = result["rank_attempts"][0]

    assert result["status"] == "NO_PUBLICATION"
    assert attempt["ordinary_policy_ceremony_reductions"] == []
    assert "supported_claims_missing" in attempt["blockers"]
    assert attempt["evidence_friction_taxonomy"][
        "ordinary_minimum_packet_directly_bound"
    ] is False


def test_enhanced_risk_never_uses_ordinary_ceremony_reduction() -> None:
    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(
            story_type_text="Military forces allegedly attacked a tanker in a disputed channel"
        ),
        acquire_evidence=_ordinary_blocked_receipt,
        story_type_by_cluster={"cluster-1": "geopolitical_event"},
    )
    attempt = result["rank_attempts"][0]

    assert result["status"] == "NO_PUBLICATION"
    assert attempt["ordinary_policy_ceremony_reductions"] == []
    assert attempt["evidence_friction_taxonomy"]["counts"]["FACTUAL_OR_RISK_BLOCK"] >= 1


def test_evidence_friction_taxonomy_distinguishes_data_from_ceremony() -> None:
    receipt = _ordinary_blocked_receipt({"cluster_id": "cluster-1", "headline_ids": ["headline-1"]})
    taxonomy = classify_evidence_friction(
        [
            "official_source_evidence_unavailable:HTTPError",
            "required_evidence_capability_missing:official_document",
        ],
        receipt=receipt,
    )
    by_code = {row["blocker"]: row["category"] for row in taxonomy["rows"]}
    assert by_code["official_source_evidence_unavailable:HTTPError"] == "DATA_NOT_AVAILABLE"
    assert by_code["required_evidence_capability_missing:official_document"] == "POLICY_CEREMONY_BLOCK"


def test_treasury_repeated_conclusion_is_removed_without_semantic_review() -> None:
    article = json.loads(GOLDEN_ARTICLE.read_text(encoding="utf-8"))
    result = remove_repeated_conclusion(article["substack_body_markdown"])

    assert result["removed_count"] == 1
    assert result["semantic_review_calls"] == 0
    assert "The boundary is equally important." in result["body_markdown"]
    assert "Confirmation would be several official sessions" not in result["body_markdown"]
    assert "## Sources and Method" in result["body_markdown"]
