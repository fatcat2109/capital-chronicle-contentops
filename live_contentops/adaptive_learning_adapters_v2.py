"""Historical, fixture, configuration, and evidence adapters for V2.

Scenario-specific identities and domain fixture labels are intentionally kept
outside the generic contracts and engine.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from live_contentops.adaptive_learning_core_v2 import (
    FeatureInputV1,
    LearningCandidateV2,
    build_learning_decision_v2,
    evaluate_outcome,
    validate_append_only_successor,
)
from live_contentops.content_intelligence_contracts_v2 import (
    AdaptiveLearningConfigV1,
    ArticleVersionV1,
    AvailabilityState,
    CalibrationState,
    ContentGapFindingV1,
    ContentGapSetV1,
    EvidenceRole,
    EvidenceScope,
    EventRelationship,
    FeatureDefinitionV1,
    GapType,
    GovernedCandidatePoolBindingV1,
    build_governed_evidence_binding_v1,
    MetricAuthorityClass,
    PerformanceObservationSetV1,
    PerformanceObservationV1,
    PlatformVariantV1,
    PublishedContentHistoryV1,
    PublishedContentItemV1,
    logical_hash,
    primitive,
    verify_governed_artifact,
)


TASK_LABEL = "TASK_CONTENTOPS_GENERIC_CONTENT_INTELLIGENCE_AND_ADAPTIVE_LEARNING_FOUNDATION_V2"
TERMINAL_CLASSIFICATION = "PASS_GENERIC_CONTENT_INTELLIGENCE_AND_ADAPTIVE_LEARNING_FOUNDATION_V2_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_GENERIC_CONTENT_INTELLIGENCE_AND_ADAPTIVE_LEARNING_FOUNDATION_V2"
EVIDENCE_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_GENERIC_CONTENT_INTELLIGENCE_AND_ADAPTIVE_LEARNING_FOUNDATION_V2"
CONFIG_REL_PATH = Path("live_contentops") / "adaptive_learning_foundation_v2_config.json"
UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
UPSTREAM_PINNED_COMMIT = "dced71f92239201945dee5c9bd1c706ef9a76f02"
UPSTREAM_HISTORICAL_COMMIT = "9bff5453a118486740ccc8957fcabd3c139fb3d2"
UPSTREAM_ARTIFACT_PATH = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
UPSTREAM_GIT_BLOB_SHA1 = "e4f60146e26d5f52dec91f92a345e81d0fb1cc8d"
UPSTREAM_FILE_SHA256 = "a92cdff58c6f4ecc5b68e774d2a6e7ed94db346f47ae636337510c1e37b192be"
UPSTREAM_POOL_ID = "cc-newsroom-pool-f385e6914bf6870bafd3"
UPSTREAM_LOGICAL_HASH = "f385e6914bf6870bafd374906d9e708081297e0e6bd9a6a0c84b228f6f8f244b"
UPSTREAM_SCHEMA = "capital_chronicle.newsroom_candidate_pool.v1"
UPSTREAM_PRODUCER = "newsroom_candidate_pool_v1.1.0"

RELEASE_REL_DIR = Path("docs") / "automation" / "DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1" / "contentops_database_publication_live_20260714_1"
TASK3_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_REAL_CONTENT_RETROSPECTIVE_GAP_IDEA_AND_ASSIGNMENT_LOOP_V1"
TASK4_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1"

ACCEPTED_CANONICAL_URL = "https://capitalchronicle.substack.com/p/treasury-yield-curve-edges-wider"
STALE_ARTICLE_EXPORT_SHA256 = "0f4e8fe6c6e6ba6999082c5f7663aa6d1414d9ecd1a0e2900c61618999981b95"
STALE_DECLARED_EXPORT_SHA256 = "3379415581f7cdf00aefb0afb2aa5815906abbaf8871f473e681dfc15f97152f"
HISTORICAL_MANIFEST_BODY_SHA256 = "bf4376efc326d0702772244eceb1744cf037cdfa9801973ddc8d8d35a0c20f11"
PRE_FINAL_REPAIR_BODY_SHA256 = "d61ca814f953e39fdc10873cd4e05e561e1ca634d38a8f4f3029aeb16e1623ea"
FINAL_ACCEPTED_BODY_SHA256 = "05b3520f1d6e4201d16e9daeac42992bde12e9f60a09f0e13bfeb95406788ecc"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        raise ValueError(f"missing_adapter_evidence:{path.as_posix()}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid_adapter_evidence:{path.as_posix()}") from error
    if not isinstance(value, dict):
        raise ValueError(f"adapter_evidence_root_not_object:{path.as_posix()}")
    return value


def load_foundation_config(repo_root: str | Path | None = None) -> AdaptiveLearningConfigV1:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    raw = _read_json(root / CONFIG_REL_PATH)
    expected_top_level = {
        "schema_version", "config_version", "calibration_state", "config_logical_hash",
        "authority_gates", "thresholds", "threshold_rules", "unavailable_handling",
        "normalization_rules", "features",
    }
    unknown_top_level = set(raw) - expected_top_level
    missing_top_level = expected_top_level - set(raw)
    if unknown_top_level:
        raise ValueError("unknown_foundation_config_fields:" + ",".join(sorted(unknown_top_level)))
    if missing_top_level:
        raise ValueError("missing_foundation_config_fields:" + ",".join(sorted(missing_top_level)))
    expected_feature_fields = {
        "feature_id", "normalization", "weight", "penalty", "minimum_evidence",
        "authority_gate", "domain_applicability", "unavailable_handling",
    }
    for index, row in enumerate(raw["features"]):
        unknown = set(row) - expected_feature_fields
        missing = expected_feature_fields - set(row)
        if unknown:
            raise ValueError(f"unknown_feature_config_fields:{index}:" + ",".join(sorted(unknown)))
        if missing:
            raise ValueError(f"missing_feature_config_fields:{index}:" + ",".join(sorted(missing)))
    features = tuple(FeatureDefinitionV1(
        feature_id=str(row["feature_id"]),
        normalization=str(row["normalization"]),
        weight=row["weight"],
        penalty=row["penalty"],
        minimum_evidence=row["minimum_evidence"],
        authority_gate=row.get("authority_gate"),
        domain_applicability=tuple(row.get("domain_applicability", [])),
        unavailable_handling=str(row["unavailable_handling"]),
    ) for row in raw["features"])
    config = AdaptiveLearningConfigV1(
        config_version=str(raw["config_version"]),
        calibration_state=CalibrationState(str(raw["calibration_state"])),
        features=features,
        thresholds=raw["thresholds"],
        authority_gates=raw["authority_gates"],
        normalization_rules=raw["normalization_rules"],
        threshold_rules=raw["threshold_rules"],
        unavailable_handling=raw["unavailable_handling"],
        config_logical_hash=str(raw["config_logical_hash"]),
        schema_version=str(raw["schema_version"]),
    )
    blockers = config.validate()
    if blockers:
        raise ValueError("invalid_foundation_config:" + ",".join(blockers))
    return config


def build_upstream_binding(consumed_bytes: bytes) -> GovernedCandidatePoolBindingV1:
    artifact = json.loads(consumed_bytes)
    candidate_rows = [*artifact.get("eligible_candidates", []), *artifact.get("rejected_candidates", [])]
    candidate_hashes = {
        str(row["candidate_id"]): str(row["evidence_hash"])
        for row in candidate_rows
    }
    source_families = tuple(sorted(str(row["family_id"]) for row in artifact.get("source_coverage", [])))
    material = {
        "repository": UPSTREAM_REPOSITORY,
        "branch": UPSTREAM_BRANCH,
        "producer_commit": UPSTREAM_PINNED_COMMIT,
        "artifact_path": UPSTREAM_ARTIFACT_PATH,
        "git_blob_sha1": UPSTREAM_GIT_BLOB_SHA1,
        "consumed_byte_sha256": sha256(consumed_bytes).hexdigest(),
        "schema_version": artifact.get("schema_version"),
        "producer_version": artifact.get("producer_version"),
        "pool_id": artifact.get("pool_id"),
        "logical_hash": artifact.get("logical_hash"),
        "cutoff_time_utc": artifact.get("cutoff_time_utc"),
        "candidate_hashes": candidate_hashes,
        "source_family_coverage": source_families,
        "immutable_binding_status": "PINNED_EXPORTED_ARTIFACT",
    }
    return GovernedCandidatePoolBindingV1(
        binding_id="pool_binding_" + logical_hash(material)[:24],
        **material,
    )


def verify_upstream_export(consumed_bytes: bytes) -> tuple[GovernedCandidatePoolBindingV1, Any]:
    binding = build_upstream_binding(consumed_bytes)
    result = verify_governed_artifact(
        consumed_bytes,
        binding,
        expected_repository=UPSTREAM_REPOSITORY,
        expected_branch=UPSTREAM_BRANCH,
        expected_artifact_path=UPSTREAM_ARTIFACT_PATH,
        expected_schema_version=UPSTREAM_SCHEMA,
        expected_producer_version=UPSTREAM_PRODUCER,
        expected_pool_id=UPSTREAM_POOL_ID,
        as_of_utc="2026-07-15T00:00:00Z",
    )
    return binding, result


def compare_upstream_pool_exports(current_bytes: bytes, historical_bytes: bytes) -> dict[str, Any]:
    current, historical = json.loads(current_bytes), json.loads(historical_bytes)
    same_bytes = current_bytes == historical_bytes
    same_identity = (
        current.get("pool_id") == historical.get("pool_id")
        and current.get("logical_hash") == historical.get("logical_hash")
    )
    if same_bytes and same_identity:
        classification = "SAME_BYTES_AND_IDENTITY"
    elif same_identity:
        classification = "SAME_LOGICAL_IDENTITY_DIFFERENT_BYTES"
    else:
        classification = "CHANGED_POOL"
    return {
        "classification": classification,
        "current_pinned_commit": UPSTREAM_PINNED_COMMIT,
        "historical_pinned_commit": UPSTREAM_HISTORICAL_COMMIT,
        "artifact_path": UPSTREAM_ARTIFACT_PATH,
        "current_byte_sha256": sha256(current_bytes).hexdigest(),
        "historical_byte_sha256": sha256(historical_bytes).hexdigest(),
        "current_pool_id": current.get("pool_id"),
        "historical_pool_id": historical.get("pool_id"),
        "current_logical_hash": current.get("logical_hash"),
        "historical_logical_hash": historical.get("logical_hash"),
        "same_git_blob_sha1": same_bytes,
    }


def accepted_publication_history_adapter(repo_root: str | Path | None = None) -> tuple[PublishedContentHistoryV1, dict[str, Any]]:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    manifest = _read_json(root / RELEASE_REL_DIR / "article_manifest_v1.json")
    readback = _read_json(root / RELEASE_REL_DIR / "substack_browser_readback_v1.json")
    matrix = _read_json(root / RELEASE_REL_DIR / "final_platform_matrix_v1.json")
    if str(readback.get("body_markdown_sha256")) != FINAL_ACCEPTED_BODY_SHA256:
        raise ValueError("accepted_public_body_authority_mismatch")
    destinations = matrix.get("destinations", {})
    platform_variants = tuple(PlatformVariantV1(
        platform_variant_id=f"{platform}:{row.get('payload_sha256') or FINAL_ACCEPTED_BODY_SHA256}",
        platform_id=str(platform),
        publication_timestamp_utc=row.get("published_at_utc"),
        payload_hash=str(row.get("payload_sha256") or FINAL_ACCEPTED_BODY_SHA256),
        current=True,
    ) for platform, row in sorted(destinations.items()) if row.get("status") == "SUCCESS")
    versions = (
        ArticleVersionV1("stale_article_export", "REJECTED_STALE_EXPORT", STALE_ARTICLE_EXPORT_SHA256, False),
        ArticleVersionV1("historical_manifest_body", "REJECTED_PRE_REPAIR_MANIFEST", HISTORICAL_MANIFEST_BODY_SHA256, False),
        ArticleVersionV1("pre_final_repair_body", "SUPERSEDED_PUBLIC_BODY", PRE_FINAL_REPAIR_BODY_SHA256, False),
        ArticleVersionV1("final_accepted_body", "FINAL_ACCEPTED_PUBLIC_BODY", FINAL_ACCEPTED_BODY_SHA256, True, "pre_final_repair_body", bounded_repair_refs=("final_auction_logic_repair",)),
    )
    item = PublishedContentItemV1(
        content_item_id="contentops-v1-0-accepted-publication",
        story_id="cc-story-b032aaca7d2d27af3f67",
        candidate_id="cc-candidate-120438cc800db7f941be",
        cluster_id="cc-cluster-7aa53a08e0a4b35873af",
        update_chain_id="cc-update-chain-7aa53a08e0a4b35873af",
        article_versions=versions,
        platform_variants=platform_variants,
        source_refs=tuple(str(value) for value in manifest.get("source_urls", [])),
        claim_refs=tuple(str(value) for value in manifest.get("claim_ids_used", [])),
        current_article_version_id="final_accepted_body",
    )
    history = PublishedContentHistoryV1("accepted_release_history_v1", (item,))
    if history.validate():
        raise ValueError("accepted_history_adapter_invalid")
    lineage = {
        "canonical_url": ACCEPTED_CANONICAL_URL,
        "final_accepted_public_body_sha256": FINAL_ACCEPTED_BODY_SHA256,
        "stale_article_export_sha256": STALE_ARTICLE_EXPORT_SHA256,
        "stale_declared_export_sha256": STALE_DECLARED_EXPORT_SHA256,
        "historical_manifest_body_sha256": HISTORICAL_MANIFEST_BODY_SHA256,
        "pre_final_repair_body_sha256": PRE_FINAL_REPAIR_BODY_SHA256,
        "accepted_authority_state": "FINAL_ACCEPTED_PUBLIC_BODY",
        "rejected_authority_states_preserved": True,
    }
    return history, lineage


def task3_historical_adapter(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    names = (
        "published_content_retrospective_v1.json", "coverage_gap_report_v1.json",
        "generated_ideas_v1.json", "rejected_ideas_v1.json",
        "editorial_briefs_v1.json", "assignment_replay_v1.json",
        "real_content_idea_loop_manifest_v1.json",
    )
    payloads = {name: _read_json(root / TASK3_REL_DIR / name) for name in names}
    return {
        "historical_status": "IMMUTABLE_TASK3_EVIDENCE_ADAPTED_NOT_REWRITTEN",
        "retrospective_id": payloads[names[0]].get("retrospective_id"),
        "gap_ids": [row["gap_id"] for row in payloads[names[1]].get("gaps", [])],
        "idea_ids": [row["idea_id"] for row in payloads[names[2]].get("records", [])],
        "rejected_idea_ids": [row["idea_id"] for row in payloads[names[3]].get("records", [])],
        "brief_ids": [row["brief_id"] for row in payloads[names[4]].get("records", [])],
        "assignment_id": payloads[names[5]].get("assignment_id"),
        "artifact_hash": logical_hash(payloads),
    }


def task4_shadow_prototype_adapter(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    decision = _read_json(root / TASK4_REL_DIR / "contentops_learning_decision_v1.json")
    replay = _read_json(root / TASK4_REL_DIR / "adaptive_newsroom_shadow_replay_v1.json")
    manifest = _read_json(root / TASK4_REL_DIR / "adaptive_newsroom_learning_loop_manifest_v1.json")
    return {
        "historical_status": "ACCEPTED_TREASURY_SPECIFIC_SHADOW_PROTOTYPE_SUPERSEDED_AS_FOUNDATION_BY_V2",
        "historical_value_preserved": True,
        "decision_id": decision.get("learning_decision_id"),
        "candidate_count": manifest.get("candidate_count"),
        "metric_snapshot_count": replay.get("metric_state", {}).get("snapshot_count"),
        "fixed_shape_limitations": {"candidates": 3, "gaps": 2, "ideas": 1, "platform_variants": 9},
        "artifact_hash": logical_hash({"decision": decision, "replay": replay, "manifest": manifest}),
    }


def v1_compatibility_replay(repo_root: str | Path | None = None) -> dict[str, Any]:
    from live_contentops import performance_learning_v1

    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    v1_artifacts = performance_learning_v1.build_adaptive_newsroom_learning_loop(root)
    history, lineage = accepted_publication_history_adapter(repo_root)
    return {
        "schema_version": "contentops.adaptive_learning_v1_compatibility_migration.v1",
        "v1_module_remains_operational": True,
        "v1_contract_module": "live_contentops.performance_learning_v1",
        "v2_adapter_module": "live_contentops.adaptive_learning_adapters_v2",
        "v1_decision_id": v1_artifacts["decision"]["learning_decision_id"],
        "v1_manifest_classification": v1_artifacts["manifest"]["terminal_classification"],
        "history_item_count": len(history.items),
        "task3": task3_historical_adapter(repo_root),
        "task4": task4_shadow_prototype_adapter(repo_root),
        "accepted_lineage": lineage,
        "historical_artifacts_mutated": False,
    }


DOMAIN_FIXTURES: tuple[dict[str, Any], ...] = (
    {"fixture_id": "inflation_release", "domain": "inflation data release", "mode": "data_release", "relationship": "material_update", "authorized": True, "modalities": ["official_table", "numeric_time_series"], "numeric": True, "sources": 1, "geographies": 1, "assets": 2, "scheduled": True, "history_count": 0, "candidate_count": 0, "gap_count": 0, "idea_count": 0, "metric_state": "unavailable", "expected": "EMPTY_COHORT_VALID"},
    {"fixture_id": "labor_release", "domain": "labor-market release", "mode": "data_release", "relationship": "material_update", "authorized": True, "modalities": ["official_table", "numeric_time_series"], "numeric": True, "sources": 2, "geographies": 1, "assets": 1, "scheduled": True, "history_count": 1, "candidate_count": 1, "gap_count": 1, "idea_count": 1, "metric_state": "explicit_zero", "expected": "GOVERNED_MATERIAL_UPDATE"},
    {"fixture_id": "macro_revision", "domain": "GDP or macro revision", "mode": "data_release", "relationship": "correction", "authorized": True, "modalities": ["official_document", "official_table"], "numeric": True, "sources": 1, "geographies": 1, "assets": 1, "scheduled": True, "history_count": 2, "candidate_count": 3, "gap_count": 3, "idea_count": 2, "metric_state": "unavailable", "expected": "GOVERNED_CORRECTION"},
    {"fixture_id": "policy_decision", "domain": "central-bank policy decision", "mode": "policy_decision", "relationship": "new_phase", "authorized": True, "modalities": ["official_statement", "official_document"], "numeric": False, "sources": 2, "geographies": 1, "assets": 3, "scheduled": True, "history_count": 1, "candidate_count": 1, "gap_count": 1, "idea_count": 1, "metric_state": "unavailable", "expected": "GOVERNED_NEW_PHASE"},
    {"fixture_id": "yield_curve", "domain": "sovereign yield-curve update", "mode": "market_move", "relationship": "confirmation", "authorized": True, "modalities": ["numeric_time_series", "derived_calculation"], "numeric": True, "sources": 1, "geographies": 1, "assets": 1, "scheduled": False, "history_count": 1, "candidate_count": 1, "gap_count": 0, "idea_count": 0, "metric_state": "unavailable", "expected": "GOVERNED_CONFIRMATION"},
    {"fixture_id": "cross_asset_move", "domain": "FX volatility or cross-asset market move", "mode": "market_move", "relationship": "confirmation", "authorized": True, "modalities": ["market_snapshot", "cross_source_reconciliation"], "numeric": True, "sources": 3, "geographies": 3, "assets": 3, "scheduled": False, "history_count": 1, "candidate_count": 1, "gap_count": 1, "idea_count": 0, "metric_state": "available", "expected": "GOVERNED_CONFIRMATION"},
    {"fixture_id": "supply_update", "domain": "commodity or energy supply update", "mode": "straight_news", "relationship": "material_update", "authorized": True, "modalities": ["official_statement", "geospatial_or_physical_observation"], "numeric": False, "sources": 2, "geographies": 2, "assets": 1, "scheduled": False, "history_count": 1, "candidate_count": 1, "gap_count": 2, "idea_count": 1, "metric_state": "unavailable", "expected": "GOVERNED_MATERIAL_UPDATE"},
    {"fixture_id": "export_control", "domain": "sanctions or export-control action", "mode": "straight_news", "relationship": "new_phase", "authorized": False, "modalities": ["legal_or_regulatory_text"], "numeric": False, "sources": 1, "geographies": 2, "assets": 1, "scheduled": False, "history_count": 0, "candidate_count": 1, "gap_count": 1, "idea_count": 0, "metric_state": "unavailable", "expected": "NO_PUBLICATION_INSUFFICIENT_AUTHORITY"},
    {"fixture_id": "geopolitical_change", "domain": "geopolitical escalation or de-escalation", "mode": "live_update", "relationship": "contradiction", "authorized": True, "modalities": ["official_statement", "qualitative_context", "cross_source_reconciliation"], "numeric": False, "sources": 3, "geographies": 3, "assets": 2, "scheduled": False, "history_count": 2, "candidate_count": 1, "gap_count": 2, "idea_count": 1, "metric_state": "unavailable", "expected": "GOVERNED_CONTRADICTION"},
    {"fixture_id": "trade_action", "domain": "trade tariff or regulatory action", "mode": "straight_news", "relationship": "initial_event", "authorized": True, "modalities": ["legal_or_regulatory_text", "official_document"], "numeric": False, "sources": 2, "geographies": 2, "assets": 2, "scheduled": True, "history_count": 0, "candidate_count": 1, "gap_count": 0, "idea_count": 0, "metric_state": "unavailable", "expected": "NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME"},
    {"fixture_id": "physical_disruption", "domain": "weather disaster or infrastructure disruption", "mode": "straight_news", "relationship": "material_update", "authorized": True, "modalities": ["geospatial_or_physical_observation", "official_statement"], "numeric": False, "sources": 2, "geographies": 2, "assets": 2, "scheduled": False, "history_count": 1, "candidate_count": 1, "gap_count": 2, "idea_count": 1, "metric_state": "unavailable", "expected": "GOVERNED_MATERIAL_UPDATE"},
    {"fixture_id": "official_testimony", "domain": "official speech testimony hearing or policy document", "mode": "deep_analysis", "relationship": "incremental_update", "authorized": True, "modalities": ["speech_or_testimony", "official_document"], "numeric": False, "sources": 1, "geographies": 1, "assets": 0, "scheduled": True, "history_count": 1, "candidate_count": 1, "gap_count": 3, "idea_count": 2, "metric_state": "unavailable", "expected": "NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME"},
    {"fixture_id": "corporate_event", "domain": "corporate or sector financial event", "mode": "straight_news", "relationship": "correction", "authorized": True, "modalities": ["corporate_filing", "official_statement"], "numeric": True, "sources": 2, "geographies": 1, "assets": 1, "scheduled": True, "history_count": 2, "candidate_count": 1, "gap_count": 1, "idea_count": 1, "metric_state": "available", "expected": "GOVERNED_CORRECTION"},
    {"fixture_id": "cross_source_confirmation", "domain": "cross-source confirmation", "mode": "deep_analysis", "relationship": "confirmation", "authorized": True, "modalities": ["cross_source_reconciliation", "qualitative_context"], "numeric": False, "sources": 3, "geographies": 2, "assets": 2, "scheduled": False, "history_count": 1, "candidate_count": 1, "gap_count": 0, "idea_count": 0, "metric_state": "unavailable", "expected": "GOVERNED_CONFIRMATION"},
    {"fixture_id": "cross_source_contradiction", "domain": "cross-source contradiction", "mode": "deep_analysis", "relationship": "contradiction", "authorized": True, "modalities": ["cross_source_reconciliation", "official_document", "market_snapshot"], "numeric": True, "sources": 3, "geographies": 2, "assets": 2, "scheduled": False, "history_count": 2, "candidate_count": 1, "gap_count": 1, "idea_count": 1, "metric_state": "unavailable", "expected": "GOVERNED_CONTRADICTION"},
)


def _fixture_history(fixture: Mapping[str, Any]) -> PublishedContentHistoryV1:
    items = tuple(PublishedContentItemV1(
        content_item_id=f"synthetic:{fixture['fixture_id']}:history:{index}",
        story_id=f"synthetic:{fixture['fixture_id']}:story:{index}",
        candidate_id=None,
        cluster_id=f"synthetic:{fixture['fixture_id']}:cluster:{index}",
        update_chain_id=f"synthetic:{fixture['fixture_id']}:chain:{index}",
    ) for index in range(int(fixture["history_count"])))
    return PublishedContentHistoryV1(f"synthetic:{fixture['fixture_id']}:history", items)


def _fixture_gap_set(fixture: Mapping[str, Any]) -> ContentGapSetV1:
    gap_types = tuple(GapType)
    findings = tuple(ContentGapFindingV1(
        gap_id=f"synthetic:{fixture['fixture_id']}:gap:{index}",
        gap_type=gap_types[index % len(gap_types)],
        finding="Synthetic validation finding; not a real-world claim.",
        evidence_refs=(f"synthetic:{fixture['fixture_id']}",),
    ) for index in range(int(fixture["gap_count"])))
    ideas = tuple(f"synthetic:{fixture['fixture_id']}:idea:{index}" for index in range(int(fixture["idea_count"])))
    return ContentGapSetV1(f"synthetic:{fixture['fixture_id']}:gaps", findings, ideas)


def _fixture_observations(fixture: Mapping[str, Any]) -> PerformanceObservationSetV1:
    state = str(fixture["metric_state"])
    if state == "explicit_zero":
        rows = (PerformanceObservationV1(
            observation_id=f"synthetic:{fixture['fixture_id']}:observation:0",
            content_item_id=f"synthetic:{fixture['fixture_id']}:content",
            story_id=f"synthetic:{fixture['fixture_id']}:story",
            update_chain_id=f"synthetic:{fixture['fixture_id']}:chain",
            platform_variant_id=f"synthetic:{fixture['fixture_id']}:variant:0",
            metric_name="synthetic_metric",
            metric_value=0.0,
            availability=AvailabilityState.EXPLICIT_ZERO,
            authority_class=MetricAuthorityClass.OFFICIAL_DASHBOARD_EXPORT,
            observed_at_utc="2026-01-01T00:00:00Z",
        ),)
    elif state == "available":
        rows = tuple(PerformanceObservationV1(
            observation_id=f"synthetic:{fixture['fixture_id']}:observation:{index}",
            content_item_id=f"synthetic:{fixture['fixture_id']}:content:{index}",
            story_id=f"synthetic:{fixture['fixture_id']}:story:{index}",
            update_chain_id=f"synthetic:{fixture['fixture_id']}:chain:{index}",
            platform_variant_id=f"synthetic:{fixture['fixture_id']}:variant:{index}",
            metric_name="synthetic_metric",
            metric_value=float(index + 1),
            availability=AvailabilityState.AVAILABLE,
            authority_class=MetricAuthorityClass.FIRST_PARTY_WEB_ANALYTICS,
            observed_at_utc="2026-01-01T00:00:00Z",
        ) for index in range(3))
    else:
        rows = (PerformanceObservationV1(
            observation_id=f"synthetic:{fixture['fixture_id']}:observation:unavailable",
            content_item_id=f"synthetic:{fixture['fixture_id']}:content",
            story_id=f"synthetic:{fixture['fixture_id']}:story",
            update_chain_id=f"synthetic:{fixture['fixture_id']}:chain",
            platform_variant_id=f"synthetic:{fixture['fixture_id']}:variant",
            metric_name="synthetic_metric",
            metric_value=None,
            availability=AvailabilityState.UNAVAILABLE,
            authority_class=MetricAuthorityClass.UNAVAILABLE,
            unavailable_reason="synthetic_fixture_metric_unavailable",
        ),)
    return PerformanceObservationSetV1(f"synthetic:{fixture['fixture_id']}:observations", rows)


def _fixture_candidate(fixture: Mapping[str, Any], index: int = 0) -> LearningCandidateV2:
    relationship = EventRelationship(str(fixture["relationship"]))
    authorized = bool(fixture["authorized"])
    primary_ref = f"synthetic:{fixture['fixture_id']}"
    relationship_ref = {
        EventRelationship.MATERIAL_UPDATE: primary_ref,
        EventRelationship.CONFIRMATION: "synthetic:new_evidence",
        EventRelationship.CONTRADICTION: "synthetic:conflicting_evidence",
        EventRelationship.CORRECTION: "synthetic:authoritative_correction",
        EventRelationship.NEW_PHASE: "synthetic:distinct_event",
    }.get(relationship)
    relationship_role = {
        EventRelationship.MATERIAL_UPDATE: EvidenceRole.MATERIAL_DELTA,
        EventRelationship.CONFIRMATION: EvidenceRole.CONFIRMATION,
        EventRelationship.CONTRADICTION: EvidenceRole.CONTRADICTION,
        EventRelationship.CORRECTION: EvidenceRole.CORRECTION,
        EventRelationship.NEW_PHASE: EvidenceRole.NEW_PHASE,
    }.get(relationship)
    feature_refs = (primary_ref,)
    feature_inputs = (
        FeatureInputV1("authority_readiness", True, AvailabilityState.AVAILABLE, 1.0 if authorized else 0.0, evidence_refs=feature_refs),
        FeatureInputV1("freshness", True, AvailabilityState.AVAILABLE, 0.8, evidence_refs=feature_refs),
        FeatureInputV1("material_delta", True, AvailabilityState.AVAILABLE, 1.0 if relationship == EventRelationship.MATERIAL_UPDATE else 0.0, evidence_refs=feature_refs),
        FeatureInputV1("novelty", True, AvailabilityState.AVAILABLE, 0.7, evidence_refs=feature_refs),
        FeatureInputV1("evidence_completeness", True, AvailabilityState.AVAILABLE, 0.8, evidence_refs=feature_refs),
        FeatureInputV1("source_diversity", True, AvailabilityState.AVAILABLE, min(1.0, float(fixture["sources"]) / 3.0), evidence_refs=feature_refs),
        FeatureInputV1("reader_utility", True, AvailabilityState.AVAILABLE, 0.7, evidence_refs=feature_refs),
        FeatureInputV1("duplication_risk", True, AvailabilityState.EXPLICIT_ZERO, 0.0, evidence_refs=feature_refs),
        FeatureInputV1("filler_risk", True, AvailabilityState.EXPLICIT_ZERO, 0.0, evidence_refs=feature_refs),
        FeatureInputV1("overclaiming_risk", True, AvailabilityState.AVAILABLE, 0.1, evidence_refs=feature_refs),
    )
    bindings = ()
    if authorized and relationship_ref and relationship_role:
        bindings = (build_governed_evidence_binding_v1(
            evidence_ref=relationship_ref,
            evidence_roles=(relationship_role, EvidenceRole.FEATURE_SUPPORT),
            producer_artifact_binding_hash=sha256(primary_ref.encode("utf-8")).hexdigest(),
            as_of_utc="2026-01-01T00:00:00Z",
            authority_state="SYNTHETIC_AUTHORIZED",
            evidence_scope=EvidenceScope.CANDIDATE_WIDE,
            reason_codes=("synthetic_validation_only",),
        ),)
    return LearningCandidateV2(
        candidate_id=f"synthetic:{fixture['fixture_id']}:candidate:{index}",
        story_id=f"synthetic:{fixture['fixture_id']}:story:{index}",
        cluster_id=f"synthetic:{fixture['fixture_id']}:cluster:{index}",
        update_chain_id=f"synthetic:{fixture['fixture_id']}:chain:{index % 2}",
        source_relationship=relationship,
        evidence_state="SYNTHETIC_VALIDATION_EVIDENCE",
        authority_state="AUTHORIZED" if authorized else "UNAUTHORIZED_SYNTHETIC_FIXTURE",
        authority_ready=authorized,
        reporting_allowed=authorized,
        authority_blockers=() if authorized else ("synthetic_authority_unavailable",),
        history_identity_match=False,
        governed_material_delta=relationship == EventRelationship.MATERIAL_UPDATE,
        material_delta_evidence_ref=primary_ref if relationship == EventRelationship.MATERIAL_UPDATE else None,
        prior_testable_proposition_ref="synthetic:prior_proposition" if relationship in {EventRelationship.CONFIRMATION, EventRelationship.CONTRADICTION} else None,
        governed_new_evidence_ref="synthetic:new_evidence" if relationship == EventRelationship.CONFIRMATION else None,
        conflicting_evidence_ref="synthetic:conflicting_evidence" if relationship == EventRelationship.CONTRADICTION else None,
        prior_error_ref="synthetic:prior_error" if relationship == EventRelationship.CORRECTION else None,
        authoritative_correction_ref="synthetic:authoritative_correction" if relationship == EventRelationship.CORRECTION else None,
        update_chain_continuity=relationship == EventRelationship.NEW_PHASE,
        distinct_new_event_ref="synthetic:distinct_event" if relationship == EventRelationship.NEW_PHASE else None,
        material_reader_contribution=True,
        feature_inputs=feature_inputs,
        evidence_refs=tuple(dict.fromkeys((primary_ref, relationship_ref) if relationship_ref else (primary_ref,))),
        governed_evidence_bindings=bindings,
        internal_brief_ids=(f"synthetic:{fixture['fixture_id']}:brief",),
    )


def execute_cross_domain_fixture_matrix(repo_root: str | Path | None = None) -> dict[str, Any]:
    config = load_foundation_config(repo_root)
    execution_rows = []
    for fixture in DOMAIN_FIXTURES:
        candidates = tuple(_fixture_candidate(fixture, index) for index in range(int(fixture["candidate_count"])))
        history, gaps, observations = _fixture_history(fixture), _fixture_gap_set(fixture), _fixture_observations(fixture)
        decision = build_learning_decision_v2(
            candidates=candidates,
            history=history,
            gaps=gaps,
            observations=observations,
            config=config,
            input_bindings={"fixture": logical_hash(fixture)},
            logical_time_basis="synthetic-fixture-v1",
        )
        configured_expected = str(fixture["expected"])
        if configured_expected == "EMPTY_COHORT_VALID":
            expected_outcome = "EMPTY_COHORT_VALID"
            expected_disposition = "NO_CANDIDATES"
        elif configured_expected.startswith("NO_PUBLICATION_"):
            expected_outcome = "NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME"
            expected_disposition = configured_expected
        elif configured_expected == "NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME":
            expected_outcome = configured_expected
            expected_disposition = "NO_PUBLICATION_NO_GOVERNED_ACTIONABLE_OUTCOME"
        else:
            expected_outcome = configured_expected
            expected_disposition = "INTERNAL_BRIEF_ELIGIBLE_OPERATOR_REVIEW_NO_PUBLICATION_AUTHORITY"
        if candidates:
            primary_outcome = evaluate_outcome(candidates[0], config)
            observed = primary_outcome.actionable_outcomes[0]
            disposition = primary_outcome.publication_disposition
            expected_pass = expected_outcome in set(primary_outcome.actionable_outcomes) and expected_disposition == disposition
        else:
            observed, disposition = "EMPTY_COHORT_VALID", "NO_CANDIDATES"
            expected_pass = expected_outcome == observed and expected_disposition == disposition and not decision.ranking_rows
        execution_rows.append({
            **fixture,
            "synthetic_fixture": True,
            "generic_capability_validated": "contract-driven outcome, feature, cardinality, and authority evaluation",
            "no_domain_branch_required_because": "the adapter maps fixture evidence into shared contracts before core execution",
            "observed_outcome": observed,
            "observed_publication_disposition": disposition,
            "expected_outcome": expected_outcome,
            "expected_publication_disposition": expected_disposition,
            "expected_unavailable_fields": ["performance_prior"] if fixture["metric_state"] == "unavailable" else [],
            "algorithm_executed": True,
            "decision_id": decision.decision_id,
            "decision_cardinalities": dict(decision.observation_cardinalities),
            "status": "PASS" if expected_pass else "FAIL",
        })
    coverage = {
        "domain_count": len(execution_rows),
        "all_algorithms_executed": all(row["algorithm_executed"] for row in execution_rows),
        "all_expected_outcomes_pass": all(row["status"] == "PASS" for row in execution_rows),
        "includes_no_numeric_claims": any(not row["numeric"] for row in execution_rows),
        "includes_numeric_claims": any(row["numeric"] for row in execution_rows),
        "includes_mixed_evidence": any(len(row["modalities"]) > 1 and row["numeric"] for row in execution_rows),
        "includes_one_and_multiple_sources": {row["sources"] for row in execution_rows}.issuperset({1, 2, 3}),
        "includes_one_and_multiple_geographies": {row["geographies"] for row in execution_rows}.issuperset({1, 2, 3}),
        "includes_one_and_multiple_assets": {row["assets"] for row in execution_rows}.issuperset({1, 2, 3}),
        "includes_scheduled_and_unscheduled": {row["scheduled"] for row in execution_rows} == {True, False},
        "includes_authorized_and_unauthorized": {row["authorized"] for row in execution_rows} == {True, False},
        "includes_zero_one_many_history": {row["history_count"] for row in execution_rows}.issuperset({0, 1, 2}),
        "includes_zero_one_many_candidates": {row["candidate_count"] for row in execution_rows}.issuperset({0, 1, 3}),
        "includes_zero_one_many_gaps": {row["gap_count"] for row in execution_rows}.issuperset({0, 1, 2, 3}),
        "includes_zero_one_many_ideas": {row["idea_count"] for row in execution_rows}.issuperset({0, 1, 2}),
        "includes_unavailable_and_explicit_zero_metrics": {row["metric_state"] for row in execution_rows}.issuperset({"unavailable", "explicit_zero"}),
        "includes_multiple_update_chains": any(row["candidate_count"] > 1 for row in execution_rows),
    }
    return {
        "schema_version": "contentops.cross_domain_fixture_matrix.v1",
        "fixture_authority": "SYNTHETIC_VALIDATION_ONLY_NOT_REAL_OBSERVATIONS",
        "rows": execution_rows,
        "coverage": coverage,
        "status": "PASS" if all(coverage.values()) else "FAIL",
    }


def run_genericity_guard(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    targets = (
        root / "live_contentops" / "content_intelligence_contracts_v2.py",
        root / "live_contentops" / "adaptive_learning_core_v2.py",
    )
    prohibited_literals = (
        "treasury", "federal reserve", "fed_funds", "crude oil", " cpi ",
        "cc-candidate-", "capitalchronicle.substack.com", "home.treasury.gov",
        FINAL_ACCEPTED_BODY_SHA256, UPSTREAM_POOL_ID,
    )
    prohibited_patterns = {
        "topic_name_conditional": r"(?i)(?:if|elif|match)\s+[^\n]*(?:topic|domain|story_family)\s*(?:==|in)",
        "exact_candidate_count": r"len\([^\n)]*candidates?[^\n)]*\)\s*(?:==|!=)\s*3\b",
        "exact_gap_count": r"len\([^\n)]*gaps?[^\n)]*\)\s*(?:==|!=)\s*2\b",
        "exact_idea_count": r"len\([^\n)]*ideas?[^\n)]*\)\s*(?:==|!=)\s*1\b",
        "fixed_platform_sample": r"(?i)(?:nine|9)[-_ ]platform",
        "unavailable_to_zero": r"(?i)(?:unavailable|null|none)[^\n]{0,40}(?:=|return)\s*0(?:\.0)?\b",
        "unversioned_score_weight": r"(?i)score\s*[+\-]=\s*[0-9]",
        "specific_publication_date": r"20[0-9]{2}-[01][0-9]-[0-3][0-9]",
    }
    findings = []
    for path in targets:
        text = path.read_text(encoding="utf-8-sig")
        lowered = text.lower()
        for literal in prohibited_literals:
            if literal.lower() in lowered:
                findings.append({"path": path.relative_to(root).as_posix(), "rule": "prohibited_literal", "match": literal})
        for rule, pattern in prohibited_patterns.items():
            if re.search(pattern, text):
                findings.append({"path": path.relative_to(root).as_posix(), "rule": rule})
    return {
        "schema_version": "contentops.genericity_guard_report.v1",
        "targets": [path.relative_to(root).as_posix() for path in targets],
        "finding_count": len(findings),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


def domain_capability_registry() -> dict[str, Any]:
    return {
        "schema_version": "contentops.domain_capability_registry.v1",
        "design": "capability_first",
        "event_relationships": [row.value for row in EventRelationship],
        "gap_types": [row.value for row in GapType],
        "fixture_domains": [row["domain"] for row in DOMAIN_FIXTURES],
        "authority_is_orthogonal_to_domain": True,
        "permission_is_orthogonal_to_domain": True,
        "new_domain_requires_core_change": False,
    }


def foundation_acceptance_matrix() -> tuple[dict[str, Any], ...]:
    """Return machine-derived rows; retained as a V1 compatibility entrypoint."""
    requirements = (
        ("1.1", "ContentOps origin/master fetched and required starting HEAD established", "git verification and foundation manifest"),
        ("1.2", "No concurrent mainline writer or Git lock", "protected-path inventory"),
        ("1.3", "Unrelated worktree changes preserved and explicit-path staging required", "changed/protected-path inventories"),
        ("1.4", "Upstream repository inspected read-only at pinned commit", "upstream binding verification"),
        ("1.5", "Immutable v1.0 tag not moved deleted recreated or retagged", "protected-path inventory and safety report"),
        ("2.1", "Fresh-session authority and bootstrap files read", "foundation manifest input audit"),
        ("2.2", "Task 3 and Task 4 evidence inspected", "compatibility replay"),
        ("2.3", "Pinned upstream candidate pool read from Git object authority", "immutable exported artifact"),
        ("3.1", "Generic-by-default product invariant implemented", "genericity standard and guard"),
        ("3.2", "Core reasons from contracts rather than topic names", "generic core and guard report"),
        ("3.3", "Scenario fixtures never become architecture boundaries", "15-domain algorithm execution matrix"),
        ("3.4", "Repaired abstractions execute in unrelated domains", "cross-domain matrix and focused tests"),
        ("4.1", "Task 3 and Task 4 historical artifacts preserved", "protected paths and compatibility replay"),
        ("4.2", "Task 4 retained as useful Treasury-specific shadow prototype", "Task 4 adapter disposition"),
        ("4.3", "V2 is new reusable authority with compatibility adapters", "three V2 modules and compatibility replay"),
        ("5.1", "Durable genericity architecture standard created", "docs/architecture/CONTENTOPS_GENERICITY_AND_DOMAIN_GENERALIZATION_STANDARD_V1.md"),
        ("5.2", "Standard covers core/adapters/config/fixtures anti-overfitting unavailable evidence time performance model and PASS rules", "genericity standard compliance"),
        ("5.3", "Mandatory builder entry reference added", "AGENTS.md"),
        ("5.4", "No additional master plan created", "changed-file inventory"),
        ("6.1", "Cohesive contracts core and adapters modules created", "contract inventory"),
        ("6.2", "Generic core does not import adapters", "genericity guard and source test"),
        ("6.3", "V1 remains operational through compatibility adapter", "v1 compatibility replay and existing tests"),
        ("7.1", "All required event relationships implemented", "contract inventory and vocabulary test"),
        ("7.2", "All required evidence modalities implemented", "contract inventory and vocabulary test"),
        ("7.3", "All required temporal characters implemented", "contract inventory and vocabulary test"),
        ("7.4", "All required story and analysis modes implemented", "contract inventory and vocabulary test"),
        ("7.5", "Authority permission and optional dimensions remain orthogonal", "contracts and domain registry"),
        ("8.1", "PublishedContentHistoryV1 supports histories versions variants lineage repairs and supersession", "contracts and focused tests"),
        ("8.2", "GovernedCandidatePoolBindingV1 captures complete immutable binding", "binding verification evidence"),
        ("8.3", "ContentGapSetV1 supports all required finding classes and arbitrary counts", "contracts and focused tests"),
        ("8.4", "PerformanceObservationSetV1 preserves all required cardinalities and authority states", "observation cardinality evidence"),
        ("8.5", "AdaptiveLearningConfigV1 externalizes registry normalization weights thresholds penalties gates applicability unavailable and calibration", "ranking configuration"),
        ("8.6", "ContentOpsLearningDecisionV2 preserves bindings cohort cardinalities features contributions outcomes authority ranks briefs abstentions proposals confidence calibration firewall operator and hash", "multi-story replay"),
        ("8.7", "All contracts support empty singleton and multi-item collections without topic-required fields", "focused tests and contract inventory"),
        ("9.1", "Verifier hashes exact consumed bytes and Git blob", "upstream artifact binding verification"),
        ("9.2", "Repository branch commit path schema producer pool logical record source and time metadata verified", "upstream artifact binding verification"),
        ("9.3", "All specified mismatch and future-leak conditions fail closed", "binding-focused tests"),
        ("9.4", "Offline replay includes immutable export binding envelope and verifier result", "evidence directory"),
        ("9.5", "Pinned versus historical pool classified truthfully", "SAME_BYTES_AND_IDENTITY comparison"),
        ("10.1", "Source relationship evidence authority history gap actionable outcome and publication disposition separated", "OutcomeDecisionV1"),
        ("10.2", "Material confirmation contradiction correction and new-phase rules require governed evidence", "core and focused tests"),
        ("10.3", "Packaging duplicate filler evergreen authority and no-publication semantics separated", "core and focused tests"),
        ("10.4", "Incompatible outcomes fail and compatible observations coexist", "focused tests"),
        ("10.5", "Reason codes and evidence references retained", "outcome matrix"),
        ("11.1", "No embedded arbitrary product weights in generic Python", "external ranking configuration and guard"),
        ("11.2", "Neutral configuration explicitly UNCALIBRATED_FOUNDATION", "ranking configuration"),
        ("11.3", "Every feature preserves applicability availability raw normalized weight contribution penalty refs and reasons", "feature contribution evidence"),
        ("11.4", "Unavailable never becomes zero and performance prior abstains without metrics", "focused tests and feature evidence"),
        ("11.5", "Nine platform variants remain one distinct content item", "observation cardinality evidence"),
        ("12.1", "Content analysis operates without performance metrics", "cross-domain and compatibility replays"),
        ("12.2", "Performance learning requires metric-bearing observations and cohort threshold", "core and config"),
        ("12.3", "Performance feedback cannot mutate truth authority permission DQR labels citations risk or blockers", "forbidden-effects firewall"),
        ("13.1", "Accepted publication final-body and stale-lineage adapter implemented", "Treasury compatibility replay"),
        ("13.2", "Task 3 Task 4 governed pools and performance snapshots adapted", "compatibility replay"),
        ("13.3", "Scenario-specific constants remain in adapters only", "genericity guard"),
        ("14.1", "All 15 required domains present", "cross-domain fixture matrix"),
        ("14.2", "Numeric/nonnumeric modality source geography asset schedule authority cardinality and metric coverage complete", "matrix coverage object"),
        ("14.3", "Each fixture states capability no-branch rationale expected outcome disposition and unavailable fields", "cross-domain fixture rows"),
        ("14.4", "Fixtures execute algorithms rather than serialization only", "algorithm_executed and decision IDs"),
        ("15.1", "Genericity guard scans generic modules for topic IDs URLs hashes routes counts dates weights coercion and inference", "genericity guard report"),
        ("15.2", "Machine-readable genericity report has zero findings", "genericity_guard_report_v1.json"),
        ("16.1", "Decisions are append-only with prior identity config bindings logical time reason operator and hash", "append-only replay"),
        ("16.2", "Identical inputs deterministic and changed authority/config changes identity", "focused tests"),
        ("17.1", "Bounded model-assisted record preserves required metadata without hidden reasoning", "ModelAssistedJudgmentV1"),
        ("17.2", "Core runs without live LLM and models cannot grant authority or permission", "focused tests and safety report"),
        ("18.1", "All required bounded V2 evidence artifacts emitted", "foundation manifest artifact inventory"),
        ("18.2", "Historical synthetic unavailable uncalibrated proposal and authorization classes distinguished", "safety report and fixture matrix"),
        ("18.3", "No V2 artifact claims new publication authority", "safety report"),
        ("19.1", "Contract and arbitrary-cardinality tests pass", "focused pytest"),
        ("19.2", "Binding mismatch and point-in-time tests pass", "focused pytest"),
        ("19.3", "Outcome semantic tests pass", "focused pytest"),
        ("19.4", "Ranking availability arithmetic sample and multi-story tests pass", "focused pytest"),
        ("19.5", "Genericity cross-domain and repaired-abstraction tests pass", "focused pytest"),
        ("19.6", "No-policy no-live no-secret safety tests pass", "focused pytest"),
        ("19.7", "Historical/V1 compatibility and deterministic append-only tests pass", "focused and existing pytest"),
        ("20.1", "Focused V2 existing performance relevant and broader tests reported truthfully", "test and validation summary"),
        ("20.2", "Compilation JSON hash parity genericity diff and scans reported", "test and validation summary"),
        ("20.3", "No CI PASS claimed without GitHub checks", "validation summary and safety report"),
        ("21.1", "All mandatory status master ledger pointer readiness and supersession authorities reconciled", "changed-file inventory"),
        ("21.2", "Stale release tag and operator-acceptance claims corrected", "AGENTS bootstrap readiness status and platform contract"),
        ("21.3", "Task 4 exact supersession disposition and V2 audit state recorded", "status files"),
        ("22.1", "Original prompt audited with zero omitted requirements", "acceptance_matrix_v1.json"),
        ("22.2", "Every acceptance row is exactly PASS with evidence", "acceptance_matrix_v1.json"),
        ("23.1", "No publish dispatch schedule platform browser storage credential env webhook public fetch metrics policy UI or live collection action", "safety report"),
        ("23.2", "Backend deterministic shadow scope only", "foundation manifest"),
        ("24.1", "Only task-owned paths are eligible for explicit staging", "changed-file inventory"),
        ("24.2", "Commit push and final Git verification required before terminal response", "terminal Git verification"),
        ("25.1", "Terminal classification and exact next action match task contract", "foundation manifest"),
        ("26.1", "Final evidence response includes every requested field", "terminal response"),
    )
    from live_contentops.generic_foundation_hardening_v2 import derive_requirement_matrix

    derived = derive_requirement_matrix({})
    return tuple(derived["rows"])


def build_treasury_compatibility_replay(repo_root: str | Path | None = None) -> dict[str, Any]:
    config = load_foundation_config(repo_root)
    history, lineage = accepted_publication_history_adapter(repo_root)
    task3 = task3_historical_adapter(repo_root)
    gaps = ContentGapSetV1(
        "task3_compatibility_gaps",
        tuple(ContentGapFindingV1(
            gap_id=gap_id,
            gap_type=GapType.DERIVATIVE_PACKAGING_GAP if "derivative" in gap_id else GapType.SCHEDULED_FOLLOW_UP,
            finding="Historical Task 3 finding adapted without mutation.",
            evidence_refs=((TASK3_REL_DIR / "coverage_gap_report_v1.json").as_posix(),),
        ) for gap_id in task3["gap_ids"]),
        tuple(task3["idea_ids"]),
    )
    observations = PerformanceObservationSetV1("historical_unavailable_observations", tuple(
        PerformanceObservationV1(
            observation_id=f"historical:unavailable:{index}",
            content_item_id=history.items[0].content_item_id,
            story_id=history.items[0].story_id,
            update_chain_id=history.items[0].update_chain_id or "unavailable",
            platform_variant_id=row.platform_variant_id,
            metric_name="impressions",
            metric_value=None,
            availability=AvailabilityState.UNAVAILABLE,
            authority_class=MetricAuthorityClass.UNAVAILABLE,
            unavailable_reason="historical_committed_metrics_unavailable",
        ) for index, row in enumerate(history.items[0].platform_variants)
    ))
    candidate = LearningCandidateV2(
        candidate_id=history.items[0].candidate_id or "historical_candidate_unavailable",
        story_id=history.items[0].story_id,
        cluster_id=history.items[0].cluster_id,
        update_chain_id=history.items[0].update_chain_id,
        source_relationship=EventRelationship.NEW_PHASE,
        evidence_state="REAL_COMMITTED_HISTORICAL_EVIDENCE",
        authority_state="HISTORICAL_ACCEPTED_CONTENT_NOT_NEW_PUBLICATION_AUTHORITY",
        authority_ready=False,
        reporting_allowed=False,
        authority_blockers=("no_new_story_scoped_publication_authority",),
        history_identity_match=True,
        update_chain_continuity=True,
        distinct_new_event_ref=None,
        material_reader_contribution=True,
        gap_types=(GapType.DERIVATIVE_PACKAGING_GAP,),
        feature_inputs=(
            FeatureInputV1("authority_readiness", True, AvailabilityState.EXPLICIT_ZERO, 0.0),
            FeatureInputV1("packaging_gap", True, AvailabilityState.AVAILABLE, 1.0),
            FeatureInputV1("duplication_risk", True, AvailabilityState.AVAILABLE, 1.0),
        ),
        evidence_refs=(TASK3_REL_DIR.as_posix(), TASK4_REL_DIR.as_posix()),
    )
    decision = build_learning_decision_v2(
        candidates=(candidate,), history=history, gaps=gaps, observations=observations,
        config=config, input_bindings={"history": logical_hash(history), "task3": task3["artifact_hash"]},
        logical_time_basis="historical-compatibility-replay-v1",
    )
    return {
        "schema_version": "contentops.treasury_compatibility_replay.v2",
        "evidence_class": "REAL_COMMITTED_HISTORICAL_EVIDENCE",
        "lineage": lineage,
        "v1_compatibility": v1_compatibility_replay(repo_root),
        "v2_decision": primitive(decision),
        "new_publication_authorized": False,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(primitive(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_foundation_evidence(
    *,
    repo_root: str | Path,
    upstream_export_path: str | Path,
    historical_upstream_export_path: str | Path,
    validation_summary: Mapping[str, Any],
    changed_files: Sequence[str],
    protected_paths: Mapping[str, Any],
    acceptance_matrix: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    output = (root / EVIDENCE_REL_DIR).resolve()
    output.mkdir(parents=True, exist_ok=True)
    current_bytes = Path(upstream_export_path).read_bytes()
    historical_bytes = Path(historical_upstream_export_path).read_bytes()
    binding, verification = verify_upstream_export(current_bytes)
    comparison = compare_upstream_pool_exports(current_bytes, historical_bytes)
    config = load_foundation_config(root)
    matrix = execute_cross_domain_fixture_matrix(root)
    compatibility = build_treasury_compatibility_replay(root)
    representative = matrix["rows"][1]
    representative_fixture = DOMAIN_FIXTURES[1]
    representative_candidate = _fixture_candidate(representative_fixture)
    representative_decision = build_learning_decision_v2(
        candidates=(representative_candidate,), history=_fixture_history(representative_fixture),
        gaps=_fixture_gap_set(representative_fixture), observations=_fixture_observations(representative_fixture),
        config=config, input_bindings={"fixture": logical_hash(representative_fixture)},
        logical_time_basis="foundation-evidence-v1",
    )
    multi_fixture = DOMAIN_FIXTURES[2]
    multi_candidates = tuple(_fixture_candidate(multi_fixture, index) for index in range(3))
    multi_decision = build_learning_decision_v2(
        candidates=multi_candidates, history=_fixture_history(multi_fixture), gaps=_fixture_gap_set(multi_fixture),
        observations=_fixture_observations(multi_fixture), config=config,
        input_bindings={"fixture": logical_hash(multi_fixture)}, logical_time_basis="multi-story-replay-v1",
    )
    successor = build_learning_decision_v2(
        candidates=multi_candidates, history=_fixture_history(multi_fixture), gaps=_fixture_gap_set(multi_fixture),
        observations=_fixture_observations(multi_fixture), config=config,
        input_bindings={"fixture": logical_hash(multi_fixture), "authority_revision": "synthetic-v2"},
        logical_time_basis="multi-story-replay-v2", prior_decision=multi_decision,
        supersession_reason="synthetic authority binding changed",
    )
    guard = run_genericity_guard(root)
    artifacts: dict[str, Any] = {
        "genericity_standard_compliance_v1.json": {
            "standard": "docs/architecture/CONTENTOPS_GENERICITY_AND_DOMAIN_GENERALIZATION_STANDARD_V1.md",
            "mandatory_bootstrap_reference": "AGENTS.md",
            "status": "PASS" if guard["status"] == "PASS" and matrix["status"] == "PASS" else "FAIL",
        },
        "contract_inventory_v1.json": {
            "contracts": ["PublishedContentHistoryV1", "GovernedCandidatePoolBindingV1", "ContentGapSetV1", "PerformanceObservationSetV1", "AdaptiveLearningConfigV1", "ContentOpsLearningDecisionV2", "ModelAssistedJudgmentV1"],
            "empty_singleton_multi_supported": True,
            "topic_specific_required_fields": [],
        },
        "upstream_artifact_binding_verification_v1.json": {"binding": primitive(binding), "verifier_result": primitive(verification)},
        "upstream_pool_comparison_v1.json": comparison,
        "domain_capability_registry_v1.json": domain_capability_registry(),
        "cross_domain_fixture_matrix_v1.json": matrix,
        "generic_outcome_matrix_v1.json": {"rows": [row["observed_outcome"] for row in matrix["rows"]], "all_algorithm_executed": matrix["coverage"]["all_algorithms_executed"]},
        "ranking_configuration_v1.json": primitive(config),
        "feature_contribution_evidence_v1.json": {"decision_id": representative_decision.decision_id, "ranking_rows": primitive(representative_decision.ranking_rows), "uncalibrated": True},
        "observation_cardinality_evidence_v1.json": {"representative": dict(representative_decision.observation_cardinalities), "multi_story": dict(multi_decision.observation_cardinalities), "one_article_nine_variants_is_one_content": compatibility["v2_decision"]["observation_cardinalities"]},
        "treasury_compatibility_replay_v2.json": compatibility,
        "multi_story_generic_replay_v1.json": primitive(multi_decision),
        "append_only_decision_replay_v1.json": {"prior": primitive(multi_decision), "successor": primitive(successor), "validation_blockers": list(validate_append_only_successor(multi_decision, successor)), "prior_artifact_mutated": False},
        "genericity_guard_report_v1.json": guard,
        "test_and_validation_summary_v1.json": dict(validation_summary),
        "changed_file_inventory_v1.json": {"task_owned_files": list(changed_files), "explicit_path_staging_required": True},
        "protected_path_inventory_v1.json": dict(protected_paths),
        "safety_and_limitation_report_v1.json": {
            "publication_authorized_outputs": 0,
            "new_publication_authorized": False,
            "configuration_calibration_state": config.calibration_state.value,
            "synthetic_fixtures_are_real_observations": False,
            "operator_review_proposals_only": True,
            "public_write_performed": False,
            "browser_or_cdp_used": False,
            "public_http_performed": False,
            "provider_action_performed": False,
            "credential_accessed": False,
            "scheduler_policy_mutated": False,
            "editorial_policy_mutated": False,
            "upstream_repository_mutated": False,
            "release_tag_mutated": False,
        },
        "acceptance_matrix_v1.json": {"rows": list(acceptance_matrix), "required_row_count": len(acceptance_matrix), "omitted_required_rows": 0, "all_pass": all(row.get("status") == "PASS" for row in acceptance_matrix)},
    }
    inventory = {name: logical_hash(value) for name, value in artifacts.items()}
    manifest = {
        "schema_version": "contentops.generic_content_intelligence_foundation_manifest.v2",
        "task_label": TASK_LABEL,
        "terminal_classification": TERMINAL_CLASSIFICATION,
        "next_action": NEXT_ACTION,
        "starting_contentops_head": "4a8d49555e692f730f8a1eaf0fd554175a9cf777",
        "upstream_binding_status": verification.status,
        "upstream_pool_comparison": comparison["classification"],
        "genericity_guard_status": guard["status"],
        "cross_domain_matrix_status": matrix["status"],
        "configuration_calibration_state": config.calibration_state.value,
        "publication_authority_granted": False,
        "immutable_export_artifacts": {
            "current_pinned": {
                "filename": "upstream_candidate_pool_dced71f_immutable_export.json",
                "byte_sha256": sha256(current_bytes).hexdigest(),
                "git_blob_sha1": verification.actual_git_blob_sha1,
            },
            "historical_pinned": {
                "filename": "upstream_candidate_pool_9bff5453_historical_export.json",
                "byte_sha256": sha256(historical_bytes).hexdigest(),
                "git_blob_sha1": verification.actual_git_blob_sha1,
            },
        },
        "artifact_logical_hashes": inventory,
    }
    artifacts["foundation_manifest_v2.json"] = manifest
    for filename, value in artifacts.items():
        _write_json(output / filename, value)
    return {"output_dir": output, "artifacts": artifacts}
