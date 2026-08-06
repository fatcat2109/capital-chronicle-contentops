"""Diversified governed evaluation corpus for CORE V0 closure (Work Package D).

TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1 — ``SHADOW_ONLY``.

This module *indexes* existing committed governed artifacts into one reviewable
evaluation cohort. It originates no news fact, claim, numeric value, source,
permission, or Capital Chronicle analysis: every case points at an exact committed
artifact path and the identifiers already inside it, and every case is re-validated
through the canonical contract validators at load time.

Historical governed material is used as an *evaluation corpus* only. Original
timestamps are carried through unchanged and each case is stamped
``historical_evaluation_material`` so nothing here can be presented as current news.

Nine domain families are represented. Because the governed permission surface is
narrow by design — most committed candidates are ``CONTEXT_ONLY`` — several families
are represented by truthfully blocked cases. That is a real capability report, not a
gap being hidden: a blocked case is as much a product outcome as a selected one.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    validate_content_evidence_packet_v3,
)

SCHEMA_VERSION = "contentops.core_v0_evaluation_corpus.v1"
TASK_LABEL = "TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1"

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The nine domain families the final product must serve. Every family must resolve to
#: at least one case — eligible or truthfully blocked.
DOMAIN_FAMILIES = (
    "us_equities_or_big_tech",
    "sector_or_industry",
    "politics_or_policy",
    "economic_release",
    "regulation_or_law",
    "geopolitics_trade_or_supply_chain",
    "rates_or_credit",
    "fx_commodity_energy_or_materials",
    "capital_chronicle_analysis",
)

#: Lane identifiers reused from the accepted CORE V0 composition.
LANE_NEWSROOM = "newsroom"
LANE_CAPITAL_CHRONICLE = "capital_chronicle"

_NUMERIC_PACKET = (
    "docs/automation/CONTENTOPS_VERIFIER_DERIVED_PERMISSION_GENERIC_CLAIM_PACKET_AND_"
    "CROSS_DOMAIN_EDITORIAL_SHADOW_V1/generic_v3_claim_packet_and_editorial_outcome.json"
)
_REGULATION_PACKET = (
    "docs/automation/CONTENTOPS_NONNUMERIC_STORY_AUTHORITY_CONSUMPTION_AND_FIRST_"
    "EDITORIAL_SHADOW_DRAFT_V1/generic_v3_claim_packet_and_editorial_outcome.json"
)
_TEXT_PACKET_BATCH = (
    "docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_"
    "PACKAGES_V1/canonical_content_evidence_packets_v3.json"
)
_CANDIDATE_POOL = (
    "docs/automation/CONTENTOPS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_"
    "CROSS_DOMAIN_ASSIGNMENT_CANARY_V1/cross_domain_candidate_pool.json"
)
_MEDIA_MANIFEST = (
    "docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/"
    "contentops_database_publication_live_20260714_1/media_manifest_v1.json"
)
#: The v2 packet is the committed authority for the *prior* observation values that make
#: a two-point comparison chart possible without inventing a series.
_PRIOR_OBSERVATION_PACKET = (
    "docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/"
    "contentops_database_publication_live_20260714_1/"
    "capital_chronicle_content_evidence_packet_v2.json"
)


class EvaluationCorpusError(RuntimeError):
    """Fail-closed evaluation corpus error."""


def _load(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise EvaluationCorpusError(f"governed_artifact_missing:{path}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationCorpusError(f"governed_artifact_not_valid_json:{path}") from exc


def _packet_from(document: Any, packet_id: str | None = None) -> Mapping[str, Any]:
    """Extract one governed v3 packet from any committed carrier shape."""
    if isinstance(document, Mapping) and "evidence_packet" in document:
        return document["evidence_packet"]
    if isinstance(document, Mapping) and "packets" in document:
        for packet in document["packets"]:
            if packet_id is None or str(packet.get("packet_id")) == packet_id:
                return packet
        raise EvaluationCorpusError(f"packet_not_found:{packet_id}")
    if isinstance(document, Mapping) and "packet_id" in document:
        return document
    raise EvaluationCorpusError("artifact_is_not_a_governed_packet_carrier")


# ---------------------------------------------------------------------------
# Case descriptors — each binds an exact committed artifact
# ---------------------------------------------------------------------------

#: Every case is declared against an exact committed artifact and identifier already
#: present in that artifact. ``expected_disposition`` records what the governed gates
#: are expected to produce; the loader verifies the packet still validates, and the
#: pipeline — never this table — decides the real outcome.
_CASE_DESCRIPTORS: tuple[dict[str, Any], ...] = (
    {
        "case_id": "case-economic-release-ust-newsroom",
        "lane": LANE_NEWSROOM,
        "domain_family": "economic_release",
        "sector": "government_bonds",
        "entities": ("U.S. Department of the Treasury",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "numeric_official_release",
        "visual_type": "chart_and_document_excerpt",
        "update_chain": "ust-daily-par-yield-curve-newsroom",
        "artifact_path": _CANDIDATE_POOL,
        "candidate_id": "cc-candidate-120438cc800db7f941be",
        "newsroom_candidate": True,
        "story_type": "data_release",
        "expected_disposition": "ELIGIBLE_CANDIDATE",
        "chart_capable": True,
        "visual_capable": True,
        "notes": (
            "The one governed candidate with reporting_allowed and no blockers. Runs "
            "through the accepted newsroom candidate->V3 adapter."
        ),
    },
    {
        "case_id": "case-rates-ust-curve",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "rates_or_credit",
        "sector": "government_bonds",
        "entities": ("U.S. Department of the Treasury",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "numeric_official_record",
        "visual_type": "chart_and_document_excerpt",
        "update_chain": "ust-daily-par-yield-curve",
        "artifact_path": _NUMERIC_PACKET,
        "packet_id": "cc-evidence-89c27e1ccc5feb1fedad",
        "story_type": "data_release",
        "expected_disposition": "ELIGIBLE_CANDIDATE",
        "chart_capable": True,
        "visual_capable": True,
        "notes": "Only governed packet exposing authorized numeric values with ALLOW.",
    },
    {
        "case_id": "case-regulation-joint-rule",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "regulation_or_law",
        "sector": "financial_regulation",
        "entities": ("OCC", "FDIC", "SEC", "CFTC", "FHFA", "CFPB", "NCUA"),
        "geography": "US",
        "source_family": "nonnumeric_story_scoped_publication_evidence_v1",
        "content_mode": "official_rule_text",
        "visual_type": "text_only",
        "update_chain": "interagency-joint-final-rule",
        "artifact_path": _REGULATION_PACKET,
        "packet_id": "cc-evidence-72fcb1a517bd01ec91d3",
        "story_type": "official_action",
        "expected_disposition": "ELIGIBLE_CANDIDATE",
        "chart_capable": False,
        "visual_capable": False,
        "notes": "Text-only regulation story; no authorized visual asset exists.",
    },
    {
        "case_id": "case-politics-fomc-minutes",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "politics_or_policy",
        "sector": "monetary_policy",
        "entities": ("Federal Open Market Committee",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "official_document_metadata",
        "visual_type": "text_only",
        "update_chain": "fomc-minutes",
        "artifact_path": _TEXT_PACKET_BATCH,
        "packet_id": "cc-evidence-4f0722ced0269d254a4d",
        "story_type": "official_action",
        "expected_disposition": "ELIGIBLE_CANDIDATE",
        "chart_capable": False,
        "visual_capable": False,
        "notes": "Factual-text metadata only; numeric reporting is not authorized.",
    },
    {
        "case_id": "case-us-equities-apple-10q",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "us_equities_or_big_tech",
        "sector": "information_technology",
        "entities": ("Apple Inc.",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "official_filing_metadata",
        "visual_type": "text_only",
        "update_chain": "apple-sec-10q",
        "artifact_path": _TEXT_PACKET_BATCH,
        "packet_id": "cc-evidence-9ef5cc971d4341756ad5",
        "story_type": "official_action",
        "expected_disposition": "ELIGIBLE_CANDIDATE",
        "chart_capable": False,
        "visual_capable": False,
        "notes": "Filing-existence metadata only; no earnings or guidance authority.",
    },
    {
        "case_id": "case-sector-usgs-ridgecrest",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "sector_or_industry",
        "sector": "infrastructure_and_natural_hazard",
        "entities": ("United States Geological Survey",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "official_event_metadata",
        "visual_type": "text_only",
        "update_chain": "usgs-ridgecrest-sequence",
        "artifact_path": _TEXT_PACKET_BATCH,
        "packet_id": "cc-evidence-8ec7ffdf16b18b6254ae",
        "story_type": "official_action",
        "expected_disposition": "HISTORICAL_NOT_CURRENT",
        "chart_capable": False,
        "visual_capable": False,
        "notes": (
            "2019 Ridgecrest sequence. Retained with original timestamps as historical "
            "evaluation material; must never be presented as current news."
        ),
    },
    {
        "case_id": "case-capital-chronicle-duplicate-replay",
        "lane": LANE_CAPITAL_CHRONICLE,
        "domain_family": "capital_chronicle_analysis",
        "sector": "government_bonds",
        "entities": ("U.S. Department of the Treasury",),
        "geography": "US",
        "source_family": "story_scoped_publication_evidence_v1",
        "content_mode": "numeric_official_record",
        "visual_type": "chart_and_document_excerpt",
        "update_chain": "ust-daily-par-yield-curve",
        "artifact_path": _NUMERIC_PACKET,
        "packet_id": "cc-evidence-89c27e1ccc5feb1fedad",
        "story_type": "data_release",
        "expected_disposition": "DUPLICATE_OR_LOW_DELTA",
        "chart_capable": True,
        "visual_capable": True,
        "notes": (
            "Exact same governed packet and update chain as case-rates-ust-curve. "
            "Deterministic duplicate suppression must hold it with no new delta."
        ),
    },
    {
        "case_id": "case-geopolitics-ofac-context-only",
        "lane": LANE_NEWSROOM,
        "domain_family": "geopolitics_trade_or_supply_chain",
        "sector": "sanctions_and_trade",
        "entities": ("Office of Foreign Assets Control",),
        "geography": "global",
        "source_family": "dbh2_ofac_official_entity_snapshot",
        "content_mode": "official_entity_snapshot",
        "visual_type": "text_only",
        "update_chain": "ofac-entity-snapshot",
        "artifact_path": _CANDIDATE_POOL,
        "candidate_id": "cc-candidate-59959c3226dbf8385373",
        "story_type": "geopolitical_event",
        "expected_disposition": "PERMISSION_BLOCKED",
        "chart_capable": False,
        "visual_capable": False,
        "notes": "Source family ceiling is CONTEXT_ONLY; reporting permission not granted.",
    },
    {
        "case_id": "case-economic-release-federal-register",
        "lane": LANE_NEWSROOM,
        "domain_family": "economic_release",
        "sector": "federal_rulemaking",
        "entities": ("Securities and Exchange Commission",),
        "geography": "US",
        "source_family": "dbh2_federal_register_official_document",
        "content_mode": "official_document_metadata",
        "visual_type": "text_only",
        "update_chain": "federal-register-document",
        "artifact_path": _CANDIDATE_POOL,
        "candidate_id": "cc-candidate-a312eb8a6efe8d24273d",
        "story_type": "official_action",
        "expected_disposition": "EVIDENCE_BLOCKED",
        "chart_capable": False,
        "visual_capable": False,
        "notes": "context_only_evidence blocker present on the governed candidate.",
    },
    {
        "case_id": "case-commodity-visual-rights-blocked",
        "lane": LANE_NEWSROOM,
        "domain_family": "fx_commodity_energy_or_materials",
        "sector": "energy",
        "entities": ("U.S. Energy Information Administration",),
        "geography": "global",
        "source_family": "dbh2_usgs_official_physical_event",
        "content_mode": "context_visual_only",
        "visual_type": "unreviewed_search_image",
        "update_chain": "energy-context-visual",
        "artifact_path": _CANDIDATE_POOL,
        "candidate_id": "cc-candidate-1874a9b2785116220298",
        "story_type": "supply_chain_event",
        "expected_disposition": "VISUAL_RIGHTS_BLOCKED",
        "chart_capable": False,
        "visual_capable": False,
        "visual_rights_probe": True,
        "notes": (
            "Carries an unreviewed search image whose rights status is "
            "operator_review_required_search_image. The visual gate must block it."
        ),
    },
)

#: The one committed asset whose rights status is explicitly unreviewed. Used as the
#: negative visual-rights probe; it is never attached to a passing package.
UNREVIEWED_ASSET = {
    "asset_id": "img_generic_fallback",
    "rights_status": "operator_review_required_search_image",
    "source_page_url": (
        "https://upload.wikimedia.org/wikipedia/commons/3/3a/PIIGS_Mk.png"
    ),
    "manifest_path": "docs/automation/V6_MEDIA_SYSTEM/downloads/img_generic_fallback.json",
    "operator_review_required": True,
    "blocked_reason": "REUSE_RIGHTS_UNVERIFIED_OPERATOR_REVIEW_REQUIRED",
}


def load_governed_visual_assets(repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Load the committed rights/provenance-bound visual assets.

    Every asset is verified byte-exact against the ``sha256`` recorded in its committed
    manifest. A drifted or missing file fails closed rather than being silently skipped.
    """
    from hashlib import sha256

    root = Path(repo_root or REPO_ROOT)
    manifest = _load(root / _MEDIA_MANIFEST)
    assets: list[dict[str, Any]] = []
    for asset in manifest.get("assets") or []:
        relative = str(asset.get("path") or "").replace("\\", "/")
        path = root / relative
        if not path.is_file():
            raise EvaluationCorpusError(f"governed_visual_asset_missing:{relative}")
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != asset.get("sha256"):
            raise EvaluationCorpusError(
                f"governed_visual_asset_hash_mismatch:{asset.get('asset_id')}"
            )
        row = dict(asset)
        row["verified_content_sha256"] = digest
        row["verified_local_path"] = relative
        row["byte_length"] = path.stat().st_size
        assets.append(row)
    if not assets:
        raise EvaluationCorpusError("governed_visual_manifest_contains_no_assets")
    return assets


def load_authorized_prior_observations(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load committed prior-observation values for the authorized numeric claims.

    These are the only committed values that give an authorized metric a *second* time
    point, which is what makes a truthful comparison chart possible. Nothing is
    interpolated, extended, or forecast.
    """
    root = Path(repo_root or REPO_ROOT)
    packet = _load(root / _PRIOR_OBSERVATION_PACKET)
    priors: dict[str, dict[str, Any]] = {}
    for claim in packet.get("numeric_claims") or []:
        claim_id = str(claim.get("claim_id"))
        if claim.get("prior_value") is None or not claim.get("prior_observation_date"):
            continue
        priors[claim_id] = {
            "claim_id": claim_id,
            "metric": claim.get("metric"),
            "unit": claim.get("unit"),
            "prior_observation_date": claim.get("prior_observation_date"),
            "prior_value": claim.get("prior_value"),
            "current_value": claim.get("value"),
            "observation_time_utc": claim.get("observation_time_utc"),
            "change_basis_points": claim.get("change_basis_points"),
            "authority_scope": claim.get("authority_scope"),
            "llm_numeric_authority": claim.get("llm_numeric_authority"),
            "public_claim_allowed": claim.get("public_claim_allowed"),
            "source_packet_id": packet.get("packet_id"),
            "source_artifact_path": _PRIOR_OBSERVATION_PACKET,
        }
    if not priors:
        raise EvaluationCorpusError("no_committed_prior_observations_available")
    return priors


def build_evaluation_corpus(repo_root: Path | None = None) -> dict[str, Any]:
    """Index committed governed artifacts into one validated evaluation cohort.

    Each case is resolved to its exact committed artifact and re-validated through the
    canonical contract validator. Nothing is synthesized: if a referenced artifact is
    missing or no longer validates, the corpus fails closed.
    """
    root = Path(repo_root or REPO_ROOT)
    cases: list[dict[str, Any]] = []
    for descriptor in _CASE_DESCRIPTORS:
        artifact_path = str(descriptor["artifact_path"])
        document = _load(root / artifact_path)
        case = {
            key: (list(value) if isinstance(value, tuple) else value)
            for key, value in descriptor.items()
        }
        case["schema_version"] = SCHEMA_VERSION
        case["artifact_path"] = artifact_path
        case["material_class"] = "historical_evaluation_material"
        case["presented_as_current_news"] = False

        if descriptor.get("packet_id"):
            packet = _packet_from(document, str(descriptor["packet_id"]))
            blockers = validate_content_evidence_packet_v3(packet)
            if blockers:
                raise EvaluationCorpusError(
                    f"corpus_packet_invalid:{descriptor['case_id']}:{sorted(blockers)}"
                )
            graph = packet.get("governed_claim_graph") or {}
            case["packet_logical_hash"] = packet.get("logical_hash")
            case["as_of_utc"] = packet.get("as_of_utc")
            case["generated_at_utc"] = packet.get("generated_at_utc")
            case["authorized_claim_ids"] = list(graph.get("approved_claim_ids") or [])
            case["authorized_claim_count"] = len(case["authorized_claim_ids"])
            case["permission_decision"] = (
                packet.get("generic_claim_permissions") or {}
            ).get("decision")
            case["numeric_claim_count"] = len(packet.get("numeric_claims") or [])
        else:
            candidate_id = str(descriptor["candidate_id"])
            candidates = document.get("candidates") or []
            candidate = next(
                (row for row in candidates if str(row.get("candidate_id")) == candidate_id),
                None,
            )
            if candidate is None:
                raise EvaluationCorpusError(f"corpus_candidate_missing:{candidate_id}")
            case["candidate_logical_hash"] = candidate.get("logical_hash")
            case["known_at_utc"] = candidate.get("known_at_utc")
            case["published_at_utc"] = candidate.get("published_at_utc")
            case["reporting_allowed"] = bool(candidate.get("reporting_allowed"))
            case["authority_state"] = candidate.get("authority_state")
            case["governed_blockers"] = list(candidate.get("blockers") or [])
            case["evidence_requirement_profile_id"] = candidate.get(
                "evidence_requirement_profile_id"
            )
            case["authorized_claim_ids"] = [
                str(row.get("claim_id")) for row in candidate.get("claims") or []
            ]
            case["authorized_claim_count"] = len(case["authorized_claim_ids"])
            case["numeric_claim_count"] = len(candidate.get("numeric_claims") or [])
            if descriptor.get("newsroom_candidate"):
                # Validate the adapted V3 packet now so a corpus case can never claim
                # eligibility the canonical contract would reject at run time.
                from live_contentops.dual_lane_core_v0_shadow_demo_runner_v1 import (
                    _newsroom_v3_packet,
                )

                packet, _ = _newsroom_v3_packet(candidate)
                blockers = validate_content_evidence_packet_v3(packet)
                if blockers:
                    raise EvaluationCorpusError(
                        f"corpus_newsroom_packet_invalid:{descriptor['case_id']}:{sorted(blockers)}"
                    )
                case["packet_logical_hash"] = packet.get("logical_hash")
                case["as_of_utc"] = packet.get("as_of_utc")
                case["permission_decision"] = (
                    packet.get("generic_claim_permissions") or {}
                ).get("decision")
        cases.append(case)

    covered = {case["domain_family"] for case in cases}
    missing = [family for family in DOMAIN_FAMILIES if family not in covered]
    if missing:
        raise EvaluationCorpusError(f"domain_family_not_represented:{sorted(missing)}")

    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "corpus_origin": "INDEXED_FROM_EXACT_COMMITTED_GOVERNED_ARTIFACTS",
        "fabricated_content": False,
        "material_class": "historical_evaluation_material",
        "historical_material_disclosure": (
            "Cases retain their original governed timestamps and are evaluation material "
            "only. No case is presented as current news."
        ),
        "domain_families": list(DOMAIN_FAMILIES),
        "domain_family_count": len(DOMAIN_FAMILIES),
        "case_count": len(cases),
        "cases": cases,
        "unreviewed_visual_asset_probe": dict(UNREVIEWED_ASSET),
        "governed_artifact_paths": sorted({case["artifact_path"] for case in cases}),
    }


def corpus_domain_coverage(corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Report which domain families are represented and by which cases."""
    by_family: dict[str, list[str]] = {family: [] for family in DOMAIN_FAMILIES}
    for case in corpus.get("cases") or []:
        by_family.setdefault(str(case.get("domain_family")), []).append(
            str(case.get("case_id"))
        )
    return {
        "families_required": len(DOMAIN_FAMILIES),
        "families_represented": sum(1 for rows in by_family.values() if rows),
        "all_families_represented": all(by_family.get(f) for f in DOMAIN_FAMILIES),
        "cases_by_family": {key: sorted(value) for key, value in sorted(by_family.items())},
    }
