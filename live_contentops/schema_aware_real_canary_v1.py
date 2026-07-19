"""Portable real-editorial canary using exact Git receipts and byte extraction."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import schema_aware_evidence_extraction_v1 as extraction


TASK_LABEL = "TASK_CONTENTOPS_SCHEMA_AWARE_EVIDENCE_EXTRACTION_AND_PORTABLE_REAL_CANARY_V1"
TERMINAL_CLASSIFICATION = "PASS_SCHEMA_AWARE_EVIDENCE_EXTRACTION_AND_PORTABLE_REAL_CANARY_V1_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_SCHEMA_AWARE_EVIDENCE_EXTRACTION_AND_PORTABLE_REAL_CANARY_V1"
STARTING_SHA = "2dae15f5d0cc294a247572a50bdfef8da6fc2684"
UPSTREAM_HEAD = "48ec657bb66758b444b12ef7467ab2687d200c6a"
UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
DECISION_CUTOFF_UTC = "2026-07-19T02:30:00Z"
EVIDENCE_ROOT = "docs/automation/CONTENTOPS_SCHEMA_AWARE_EVIDENCE_EXTRACTION_AND_PORTABLE_REAL_CANARY_V1"


REAL_EDITORIAL_ARTIFACTS: tuple[Mapping[str, Any], ...] = (
    {
        "artifact_family": "bls_public_data_api",
        "editorial_class": "official_numeric_macroeconomic_data",
        "story_id": "real-canary-v2:story:cpi-index-april-2026",
        "candidate_id": "real-canary-v2:candidate:cpi-index-april-2026",
        "path": "data/archive/official_sources/bls_public_data_api/bls_cpi_live_20260531_132121_1fcff5e55d1b/raw_response.json",
        "artifact_schema_version": "external.bls_public_data_response.v1",
        "extractor_id": "contentops.bls_series_observation_extractor",
        "selector": {"series_id": "CUUR0000SA0", "year": "2026", "period": "M04"},
        "feature_targets": ("evidence_completeness", "freshness"),
        "modality": contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        "numeric": True,
        "nonnumeric": False,
    },
    {
        "artifact_family": "us_treasury_fiscaldata_auction_announcements",
        "editorial_class": "official_action_auction_announcement",
        "story_id": "real-canary-v2:story:treasury-30y-reopening-announcement",
        "candidate_id": "real-canary-v2:candidate:treasury-30y-reopening-announcement",
        "path": "data/audit/data_sufficiency/task_calendar_event_spine_batch_a1_treasury_auctions_live_capture/raw_archive/req1_treasury_auctions_recent_announcements.json",
        "artifact_schema_version": "external.us_treasury_auction_announcement_response.v1",
        "extractor_id": "contentops.treasury_auction_announcement_extractor",
        "selector": {"cusip": "912810UU0", "announcement_date": "2026-06-04"},
        "feature_targets": ("evidence_completeness", "policy_significance"),
        "modality": contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        "numeric": True,
        "nonnumeric": True,
    },
    {
        "artifact_family": "nyfed_reference_rates",
        "editorial_class": "market_rates_observation",
        "story_id": "real-canary-v2:story:sofr-june-4-2026",
        "candidate_id": "real-canary-v2:candidate:sofr-june-4-2026",
        "path": "data/audit/data_sufficiency/task_300aa_304z/raw_archive/nyfed_reference_rates/batch_e_nyfed_reference_rates_20260606T154423Z_a0793ac6/raw_response.bin",
        "artifact_schema_version": "external.nyfed_reference_rates_response.v1",
        "extractor_id": "contentops.nyfed_reference_rate_extractor",
        "selector": {"rate_type": "SOFR", "effective_date": "2026-06-04"},
        "feature_targets": ("evidence_completeness", "freshness"),
        "modality": contracts.EvidenceModality.MARKET_SNAPSHOT,
        "numeric": True,
        "nonnumeric": False,
    },
)


def _git_bytes(repository: Path, commit: str, path: str) -> bytes:
    prefix = ["git", "--git-dir", str(repository)] if repository.suffix == ".git" else ["git", "-C", str(repository)]
    try:
        return subprocess.run([*prefix, "show", f"{commit}:{path}"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    except subprocess.CalledProcessError as error:
        raise ValueError(f"real_editorial_artifact_unavailable:{path}") from error


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.suffix == ".git" else ["git", "-C", str(repository)]


def run_schema_aware_real_canary(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
    upstream_commit: str = UPSTREAM_HEAD,
    branch_authority_ref: str | None = "refs/remotes/read-only-upstream/main",
) -> Mapping[str, Any]:
    root, upstream = Path(repo_root).resolve(), Path(upstream_git_repository).resolve()
    verifier_registry = adapters.load_trusted_verifier_registry(root)
    extractor_registry = extraction.load_extractor_registry(root)
    commit_time = subprocess.run(
        [*_git_prefix(upstream), "show", "-s", "--format=%cI", upstream_commit],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip().replace("+00:00", "Z")

    receipts = []
    extracted_records = []
    extracted_features = []
    consumed_by_path: dict[str, bytes] = {}
    for spec in REAL_EDITORIAL_ARTIFACTS:
        path = str(spec["path"])
        consumed = _git_bytes(upstream, upstream_commit, path)
        consumed_by_path[path] = consumed
        extractor = extractor_registry.resolve(str(spec["extractor_id"]), "v1")
        if extractor is None:
            raise ValueError("real_canary_extractor_missing")
        receipt = adapters.build_local_git_artifact_receipt(
            git_repository=upstream, repository_identity=UPSTREAM_REPOSITORY,
            branch=UPSTREAM_BRANCH, commit=upstream_commit, artifact_path=path,
            artifact_schema_version=str(spec["artifact_schema_version"]),
            producer_version=extractor.shape_contract_id,
            artifact_cutoff_utc=commit_time, evidence_refs=(),
            source_authority_class="official_public_data", registry=verifier_registry,
            verification_time_utc=DECISION_CUTOFF_UTC,
            branch_authority_ref=branch_authority_ref,
        )
        record, values = extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=extractor_registry,
            extractor_id=extractor.extractor_id, extractor_version=extractor.extractor_version,
            selector=spec["selector"], feature_targets=spec["feature_targets"],
            decision_cutoff_utc=DECISION_CUTOFF_UTC,
        )
        receipts.append(receipt)
        extracted_records.append(record)
        extracted_features.extend(values)

    context = contracts.EvidenceDecisionContextV1(
        verifier_registry, tuple(receipts), DECISION_CUTOFF_UTC,
        extractor_registry, tuple(extracted_records), tuple(extracted_features),
    )
    blockers = context.validate()
    if blockers:
        raise ValueError("real_canary_context_invalid:" + ",".join(blockers))

    candidates = []
    inventory = []
    for spec, receipt, record in zip(REAL_EDITORIAL_ARTIFACTS, receipts, extracted_records, strict=True):
        feature_values = [row for row in extracted_features if record.evidence_ref in row.evidence_refs]
        binding = adapters.build_receipt_backed_evidence_binding(
            context, evidence_ref=record.evidence_ref,
            evidence_roles=record.evidence_roles, evidence_scope=record.evidence_scope,
            authority_state=record.authority_state, permission_state=record.permission_state,
            target_feature_ids=record.feature_targets, as_of_utc=receipt.artifact_cutoff_utc,
            reason_codes=("real_editorial_extracted_evidence_no_publication_authority",),
        )
        inputs = tuple(core.FeatureInputV1(
            row.feature_id, True, row.availability, row.value,
            evidence_refs=(record.evidence_ref,), evidence_scope=record.evidence_scope,
        ) for row in feature_values)
        capabilities = contracts.CapabilityDimensionsV1(
            evidence_modalities=(spec["modality"],),
            temporal_characters=(contracts.TemporalCharacter.POINT_IN_TIME,),
            story_modes=(contracts.StoryMode.DATA_RELEASE if spec["editorial_class"] == "official_numeric_macroeconomic_data" else contracts.StoryMode.MARKET_MOVE if spec["editorial_class"] == "market_rates_observation" else contracts.StoryMode.STRAIGHT_NEWS,),
            source_family_ids=(str(spec["artifact_family"]),),
            source_authority_classes=("official_public_data",),
            numeric_evidence_present=bool(spec["numeric"]),
            nonnumeric_evidence_present=bool(spec["nonnumeric"]),
        )
        candidates.append(core.LearningCandidateV2(
            candidate_id=str(spec["candidate_id"]), story_id=str(spec["story_id"]),
            cluster_id="real-canary-v2:cluster:" + str(spec["artifact_family"]),
            update_chain_id="real-canary-v2:chain:" + str(spec["artifact_family"]),
            source_relationship=contracts.EventRelationship.INITIAL_EVENT,
            evidence_state="SCHEMA_EXTRACTED_FROM_EXACT_COMMITTED_BYTES",
            authority_state="OFFICIAL_CONTEXT_NO_PUBLICATION_AUTHORITY",
            authority_ready=False, reporting_allowed=False,
            authority_blockers=("real_canary_no_publication_authority",),
            history_identity_match=False, material_reader_contribution=True,
            feature_inputs=inputs, evidence_refs=(record.evidence_ref,),
            governed_evidence_bindings=(binding,), capabilities=capabilities,
            evidence_context=context,
        ))
        inventory.append({
            "artifact_family": spec["artifact_family"], "editorial_class": spec["editorial_class"],
            "story_id": spec["story_id"], "repository": receipt.repository, "branch": receipt.branch,
            "pinned_commit": receipt.producer_commit, "branch_head_observed": receipt.branch_head_observed,
            "ancestry_verified": receipt.producer_commit_reachable_from_branch,
            "path": receipt.artifact_path, "git_blob_sha1": receipt.git_blob_sha1,
            "byte_sha256": receipt.consumed_byte_sha256, "receipt_id": receipt.receipt_id,
            "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
            "record_selector": record.record_selector, "record_key": record.record_key,
            "extracted_record_hash": record.extracted_record_hash, "evidence_ref": record.evidence_ref,
            "schema_authority": record.schema_authority, "artifact_schema_verified": record.artifact_schema_verified,
            "feature_values": contracts.primitive(feature_values),
            "internal_timestamps": {name: getattr(record, name) for name in ("observed_at_utc", "known_at_utc", "published_at_utc", "revision_at_utc")},
            "numeric": spec["numeric"], "nonnumeric": spec["nonnumeric"],
            "real_editorial_artifact": True, "synthetic": False, "internal_access_contract": False,
        })

    decision = core.build_learning_decision_v2(
        candidates=tuple(candidates), history=contracts.PublishedContentHistoryV1("real-canary-v2:history:none"),
        gaps=contracts.ContentGapSetV1("real-canary-v2:gaps:none"),
        observations=contracts.PerformanceObservationSetV1("real-canary-v2:observations:none"),
        config=adapters.load_foundation_config(root),
        input_bindings={
            "upstream_commit": upstream_commit,
            "verifier_registry": verifier_registry.registry_logical_hash,
            "extractor_registry": extractor_registry.registry_logical_hash,
            **{f"receipt:{index}": receipt.logical_hash for index, receipt in enumerate(receipts)},
            **{f"extraction:{index}": record.extraction_logical_hash for index, record in enumerate(extracted_records)},
        },
        logical_time_basis="schema-aware-real-editorial-canary-v1",
        decision_cutoff_utc=DECISION_CUTOFF_UTC, evidence_context=context,
    )
    decision_rows = []
    for ranking in decision.ranking_rows:
        decision_rows.append({
            "candidate_id": ranking.candidate_id, "story_id": ranking.story_id,
            "publication_disposition": ranking.publication_disposition, "score": ranking.score,
            "features": contracts.primitive(ranking.features),
        })
    coverage = {
        "distinct_story_count": len({row["story_id"] for row in REAL_EDITORIAL_ARTIFACTS}),
        "distinct_artifact_family_count": len({row["artifact_family"] for row in REAL_EDITORIAL_ARTIFACTS}),
        "distinct_editorial_class_count": len({row["editorial_class"] for row in REAL_EDITORIAL_ARTIFACTS}),
        "distinct_modality_count": len({row["modality"] for row in REAL_EDITORIAL_ARTIFACTS}),
        "numeric_present": any(row["numeric"] for row in REAL_EDITORIAL_ARTIFACTS),
        "nonnumeric_present": any(row["nonnumeric"] for row in REAL_EDITORIAL_ARTIFACTS),
        "internal_access_contracts_counted": 0, "synthetic_artifacts_counted": 0,
        "public_writes": 0,
    }
    passed = bool(
        coverage["distinct_story_count"] >= 3 and coverage["distinct_artifact_family_count"] >= 3
        and coverage["distinct_editorial_class_count"] >= 3 and coverage["distinct_modality_count"] >= 2
        and coverage["numeric_present"] and coverage["nonnumeric_present"]
        and all(row["publication_disposition"].startswith("NO_PUBLICATION") for row in decision_rows)
        and all(item["evidence_ref"].startswith("extracted:") for item in inventory)
    )
    return {
        "schema_version": "contentops.schema_aware_real_editorial_canary.v1",
        "status": "PASS" if passed else "FAIL", "upstream_head": upstream_commit,
        "decision_cutoff_utc": DECISION_CUTOFF_UTC,
        "verifier_registry_logical_hash": verifier_registry.registry_logical_hash,
        "extractor_registry_logical_hash": extractor_registry.registry_logical_hash,
        "artifact_inventory": inventory, "coverage": coverage,
        "extracted_evidence_records": contracts.primitive(extracted_records),
        "extracted_feature_values": contracts.primitive(extracted_features),
        "decision": contracts.primitive(decision), "decision_rows": decision_rows,
        "abstentions": [contracts.primitive(row) for row in extracted_features if row.availability not in {contracts.AvailabilityState.AVAILABLE, contracts.AvailabilityState.EXPLICIT_ZERO}],
        "publication_authority_granted": False,
    }
