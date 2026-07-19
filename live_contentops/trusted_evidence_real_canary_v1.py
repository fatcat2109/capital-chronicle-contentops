"""Deterministic, no-write real-artifact canary for the generic V2 learning core."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts


TASK_LABEL = "TASK_CONTENTOPS_TRUSTED_EVIDENCE_VERIFIER_REGISTRY_AND_REAL_MULTI_TOPIC_CANARY_V1"
TERMINAL_CLASSIFICATION = "PASS_TRUSTED_EVIDENCE_VERIFIER_REGISTRY_AND_REAL_MULTI_TOPIC_CANARY_V1_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_TRUSTED_EVIDENCE_VERIFIER_REGISTRY_AND_REAL_MULTI_TOPIC_CANARY_V1"
STARTING_SHA = "96a53eee8beefed9ecf669f930a6436fe4641468"
UPSTREAM_HEAD = "4827ca1e327e3e20275b4422203417f89e12167c"
UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
DECISION_CUTOFF_UTC = "2026-07-19T01:22:00Z"
EVIDENCE_ROOT = "docs/automation/CONTENTOPS_TRUSTED_EVIDENCE_VERIFIER_REGISTRY_AND_REAL_MULTI_TOPIC_CANARY_V1"

REAL_ARTIFACTS: tuple[Mapping[str, Any], ...] = (
    {
        "artifact_family": "official_macro_time_series",
        "topic": "consumer_prices",
        "story_id": "real-canary:story:consumer-prices",
        "candidate_id": "real-canary:candidate:consumer-prices",
        "path": "data/archive/official_sources/bls_public_data_api/bls_cpi_live_20260531_132121_1fcff5e55d1b/raw_response.json",
        "artifact_schema_version": "upstream.bls_public_data_response.v1",
        "producer_version": "bls-public-data-raw-response-v1",
        "source_authority_class": "official_public_data",
        "evidence_ref": "artifact:bls-cpi:CUUR0000SA0:2026-M04",
        "feature_id": "freshness",
        "raw_value": 0.8,
        "authority_state": "OFFICIAL_VERIFIED",
        "permission_state": "CONTEXT_ONLY",
        "modality": contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        "numeric": True,
        "nonnumeric": False,
        "authority_ready": True,
        "reporting_allowed": False,
        "authority_blockers": (),
    },
    {
        "artifact_family": "official_catalyst_access_contract",
        "topic": "official_release_access_policy",
        "story_id": "real-canary:story:official-release-access",
        "candidate_id": "real-canary:candidate:official-release-access",
        "path": "config/data_foundation/HB8_OFFICIAL_CATALYST_SOURCE_ACCESS_CONTRACT_V1.json",
        "artifact_schema_version": "capital_chronicle.official_catalyst_access_contract.v1",
        "producer_version": "hb8-official-catalyst-contract-v1",
        "source_authority_class": "exact_committed_artifact",
        "evidence_ref": "artifact:official-catalyst:hb8-v1",
        "feature_id": "policy_significance",
        "raw_value": 0.7,
        "authority_state": "VERIFIED_GOVERNED",
        "permission_state": "CONTEXT_ONLY",
        "modality": contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        "numeric": False,
        "nonnumeric": True,
        "authority_ready": True,
        "reporting_allowed": False,
        "authority_blockers": (),
    },
    {
        "artifact_family": "governed_newsroom_candidate_pool",
        "topic": "treasury_yield_curve",
        "story_id": "cc-story-b032aaca7d2d27af3f67",
        "candidate_id": "cc-candidate-120438cc800db7f941be",
        "path": "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json",
        "artifact_schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "producer_version": "newsroom_candidate_pool_v1.1.0",
        "source_authority_class": "exact_committed_artifact",
        "evidence_ref": "artifact:newsroom-pool:cc-candidate-120438cc800db7f941be",
        "feature_id": "evidence_completeness",
        "raw_value": 0.9,
        "authority_state": "VERIFIED_GOVERNED",
        "permission_state": "REPORTING_ALLOWED",
        "modality": contracts.EvidenceModality.CROSS_SOURCE_RECONCILIATION,
        "numeric": True,
        "nonnumeric": True,
        "authority_ready": True,
        "reporting_allowed": True,
        "authority_blockers": (),
    },
)


def _git_bytes(git_dir: Path, commit: str, path: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "--git-dir", str(git_dir), "show", f"{commit}:{path}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise ValueError(f"real_canary_artifact_unavailable:{path}") from error


def run_real_multi_topic_canary(
    *, repo_root: str | Path,
    upstream_git_dir: str | Path,
) -> Mapping[str, Any]:
    """Compatibility adapter onto the superseding schema-aware real canary."""
    from live_contentops import schema_aware_real_canary_v1 as schema_aware

    report = dict(schema_aware.run_schema_aware_real_canary(
        repo_root=repo_root, upstream_git_repository=upstream_git_dir,
    ))
    coverage = dict(report["coverage"])
    coverage["distinct_topic_count"] = coverage["distinct_editorial_class_count"]
    report["coverage"] = coverage
    report["artifact_inventory"] = [
        {**row, "commit": row["pinned_commit"]} for row in report["artifact_inventory"]
    ]
    report["decision_rows"] = [
        {
            **row,
            "contributing_features": [
                feature for feature in row["features"]
                if feature.get("contribution") is not None or feature.get("penalty") is not None
            ],
        }
        for row in report["decision_rows"]
    ]
    return report


def _run_legacy_transport_only_canary(
    *, repo_root: str | Path,
    upstream_git_dir: str | Path,
) -> Mapping[str, Any]:
    root, git_dir = Path(repo_root).resolve(), Path(upstream_git_dir).resolve()
    registry = adapters.load_trusted_verifier_registry(root)
    commit_time = subprocess.run(
        ["git", "--git-dir", str(git_dir), "show", "-s", "--format=%cI", UPSTREAM_HEAD],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()
    receipts = tuple(adapters.build_local_git_artifact_receipt(
        git_repository=git_dir,
        repository_identity=UPSTREAM_REPOSITORY,
        branch=UPSTREAM_BRANCH,
        commit=UPSTREAM_HEAD,
        artifact_path=str(spec["path"]),
        artifact_schema_version=str(spec["artifact_schema_version"]),
        producer_version=str(spec["producer_version"]),
        artifact_cutoff_utc=commit_time,
        evidence_refs=(str(spec["evidence_ref"]),),
        source_authority_class=str(spec["source_authority_class"]),
        registry=registry,
        branch_authority_ref="refs/remotes/read-only-upstream/main",
    ) for spec in REAL_ARTIFACTS)
    context = contracts.EvidenceDecisionContextV1(registry, receipts, DECISION_CUTOFF_UTC)
    if context.validate():
        raise ValueError("real_canary_context_invalid:" + ",".join(context.validate()))

    candidates = []
    inventory = []
    for spec, receipt in zip(REAL_ARTIFACTS, receipts, strict=True):
        artifact = json.loads(_git_bytes(git_dir, UPSTREAM_HEAD, str(spec["path"])))
        if not isinstance(artifact, dict):
            raise ValueError("real_canary_artifact_root_not_object")
        feature_id = str(spec["feature_id"])
        binding = adapters.build_receipt_backed_evidence_binding(
            context,
            evidence_ref=str(spec["evidence_ref"]),
            evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT,),
            evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
            authority_state=str(spec["authority_state"]),
            permission_state=str(spec["permission_state"]),
            target_feature_ids=(feature_id,),
            as_of_utc=receipt.artifact_cutoff_utc,
            reason_codes=("real_committed_artifact_canary",),
        )
        modality = spec["modality"]
        capabilities = contracts.CapabilityDimensionsV1(
            evidence_modalities=(modality,),
            temporal_characters=(contracts.TemporalCharacter.POINT_IN_TIME,),
            story_modes=(contracts.StoryMode.DATA_RELEASE if spec["numeric"] else contracts.StoryMode.POLICY_DECISION,),
            source_family_ids=(str(spec["artifact_family"]),),
            source_authority_classes=(str(spec["source_authority_class"]),),
            numeric_evidence_present=bool(spec["numeric"]),
            nonnumeric_evidence_present=bool(spec["nonnumeric"]),
        )
        candidate = core.LearningCandidateV2(
            candidate_id=str(spec["candidate_id"]), story_id=str(spec["story_id"]),
            cluster_id="real-canary:cluster:" + str(spec["topic"]),
            update_chain_id="real-canary:chain:" + str(spec["topic"]),
            source_relationship=contracts.EventRelationship.INITIAL_EVENT,
            evidence_state="REAL_COMMITTED_GIT_BOUND_EVIDENCE",
            authority_state=str(spec["authority_state"]),
            authority_ready=bool(spec["authority_ready"]),
            reporting_allowed=bool(spec["reporting_allowed"]),
            authority_blockers=tuple(spec["authority_blockers"]),
            history_identity_match=False,
            material_reader_contribution=True,
            feature_inputs=(core.FeatureInputV1(
                feature_id, True, contracts.AvailabilityState.AVAILABLE,
                float(spec["raw_value"]), evidence_refs=(str(spec["evidence_ref"]),),
                evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
            ),),
            evidence_refs=(str(spec["evidence_ref"]),),
            governed_evidence_bindings=(binding,),
            capabilities=capabilities,
            evidence_context=context,
        )
        candidates.append(candidate)
        inventory.append({
            "artifact_family": spec["artifact_family"], "topic": spec["topic"],
            "repository": receipt.repository, "branch": receipt.branch,
            "commit": receipt.producer_commit, "path": receipt.artifact_path,
            "git_blob_sha1": receipt.git_blob_sha1,
            "byte_sha256": receipt.consumed_byte_sha256,
            "artifact_logical_hash": receipt.artifact_logical_hash,
            "artifact_schema_version": receipt.artifact_schema_version,
            "receipt_id": receipt.receipt_id, "receipt_logical_hash": receipt.logical_hash,
            "evidence_ref": spec["evidence_ref"], "modality": modality.value,
            "numeric": spec["numeric"], "nonnumeric": spec["nonnumeric"],
            "real_committed_artifact": True, "synthetic": False,
        })

    decision = core.build_learning_decision_v2(
        candidates=tuple(candidates),
        history=contracts.PublishedContentHistoryV1("real-canary:history:none"),
        gaps=contracts.ContentGapSetV1("real-canary:gaps:none"),
        observations=contracts.PerformanceObservationSetV1("real-canary:observations:none"),
        config=adapters.load_foundation_config(root),
        input_bindings={
            "upstream_commit": UPSTREAM_HEAD,
            "verifier_registry": registry.registry_logical_hash,
            **{f"receipt:{index}": receipt.logical_hash for index, receipt in enumerate(receipts)},
        },
        logical_time_basis="real-multi-topic-canary-v1",
        decision_cutoff_utc=DECISION_CUTOFF_UTC,
        evidence_context=context,
    )
    rows = []
    for ranking in decision.ranking_rows:
        contributing = [feature for feature in ranking.features if feature.contribution is not None or feature.penalty is not None]
        rows.append({
            "candidate_id": ranking.candidate_id,
            "story_id": ranking.story_id,
            "publication_disposition": ranking.publication_disposition,
            "score": ranking.score,
            "contributing_features": contracts.primitive(contributing),
        })
    coverage = {
        "distinct_story_count": len({row["story_id"] for row in REAL_ARTIFACTS}),
        "distinct_topic_count": len({row["topic"] for row in REAL_ARTIFACTS}),
        "distinct_artifact_family_count": len({row["artifact_family"] for row in REAL_ARTIFACTS}),
        "distinct_modality_count": len({row["modality"] for row in REAL_ARTIFACTS}),
        "numeric_present": any(row["numeric"] for row in REAL_ARTIFACTS),
        "nonnumeric_present": any(row["nonnumeric"] for row in REAL_ARTIFACTS),
        "synthetic_artifacts_counted": 0,
        "public_writes": 0,
    }
    passed = bool(
        coverage["distinct_story_count"] >= 3
        and coverage["distinct_topic_count"] >= 3
        and coverage["distinct_artifact_family_count"] >= 3
        and coverage["distinct_modality_count"] >= 2
        and coverage["numeric_present"] and coverage["nonnumeric_present"]
        and len(rows) == 3
        and all(row["contributing_features"] for row in rows)
        and all(row["publication_disposition"].startswith(("NO_PUBLICATION", "INTERNAL_BRIEF")) for row in rows)
    )
    return {
        "schema_version": "contentops.real_multi_topic_trusted_evidence_canary.v1",
        "status": "PASS" if passed else "FAIL",
        "upstream_head": UPSTREAM_HEAD,
        "decision_cutoff_utc": DECISION_CUTOFF_UTC,
        "registry_version": registry.registry_version,
        "registry_logical_hash": registry.registry_logical_hash,
        "artifact_inventory": inventory,
        "coverage": coverage,
        "decision": contracts.primitive(decision),
        "decision_rows": rows,
        "publication_authority_granted": False,
        "synthetic_fixture_claim": "NO_SYNTHETIC_ARTIFACT_COUNTED_AS_REAL",
    }
