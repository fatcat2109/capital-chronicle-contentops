"""Deterministic, local-only conformance for V2 production evidence adapters.

The harness consumes exact Git objects already present in a local repository.
It never fetches, writes upstream state, publishes, dispatches, or mutates
authority, editorial, scheduler, DQR, permission, or ranking configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import production_evidence_adapters_batch_v1 as production_batch
from live_contentops import production_evidence_adapters_wave2_v1 as production_wave2
from live_contentops import production_evidence_adapters_wave3_v1 as production_wave3
from live_contentops import production_adapter_contract_coverage_v1 as contract_coverage
from live_contentops import schema_aware_evidence_extraction_v1 as extraction


SCHEMA_VERSION = "contentops.production_adapter_conformance_result.v1"
HARNESS_VERSION = "contentops.production_adapter_conformance.v1.0.0"
UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
DECISION_CUTOFF_UTC = "2026-07-19T12:00:00Z"


@dataclass(frozen=True)
class ProductionAdapterSpecV1:
    adapter_id: str
    artifact_family: str
    artifact_path: str
    artifact_schema_version: str
    extractor_id: str
    selector: Mapping[str, str]
    feature_targets: tuple[str, ...]
    modality: contracts.EvidenceModality
    numeric: bool
    nonnumeric: bool
    candidate_id: str
    story_id: str
    evidence_scope: contracts.EvidenceScope = contracts.EvidenceScope.FEATURE_SPECIFIC
    extractor_version: str = "v1"
    verifier_id: str = "contentops.exact_git_artifact_verifier"
    verifier_version: str = "v1"
    expected_git_blob_sha1: str | None = None
    expected_byte_sha256: str | None = None
    pinned_producer_commit: str | None = None


PRODUCTION_ADAPTERS_V1: tuple[ProductionAdapterSpecV1, ...] = (
    ProductionAdapterSpecV1(
        "bls_series_observation_v1", "bls_public_data_api",
        "data/archive/official_sources/bls_public_data_api/bls_cpi_live_20260531_132121_1fcff5e55d1b/raw_response.json",
        "external.bls_public_data_response.v1", "contentops.bls_series_observation_extractor",
        {"series_id": "CUUR0000SA0", "year": "2026", "period": "M04"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, False, "conformance:candidate:bls-cpi", "conformance:story:bls-cpi",
    ),
    ProductionAdapterSpecV1(
        "us_treasury_auction_announcement_v1", "us_treasury_fiscaldata_auction_announcements",
        "data/audit/data_sufficiency/task_calendar_event_spine_batch_a1_treasury_auctions_live_capture/raw_archive/req1_treasury_auctions_recent_announcements.json",
        "external.us_treasury_auction_announcement_response.v1", "contentops.treasury_auction_announcement_extractor",
        {"cusip": "912810UU0", "announcement_date": "2026-06-04"},
        ("evidence_completeness", "policy_significance"), contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        True, True, "conformance:candidate:treasury-auction", "conformance:story:treasury-auction",
    ),
    ProductionAdapterSpecV1(
        "nyfed_reference_rate_v1", "nyfed_reference_rates",
        "data/audit/data_sufficiency/task_300aa_304z/raw_archive/nyfed_reference_rates/batch_e_nyfed_reference_rates_20260606T154423Z_a0793ac6/raw_response.bin",
        "external.nyfed_reference_rates_response.v1", "contentops.nyfed_reference_rate_extractor",
        {"rate_type": "SOFR", "effective_date": "2026-06-04"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.MARKET_SNAPSHOT,
        True, False, "conformance:candidate:nyfed-sofr", "conformance:story:nyfed-sofr",
    ),
    ProductionAdapterSpecV1(
        "newsroom_candidate_pool_v1", "governed_newsroom_candidate_pool",
        "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json",
        "capital_chronicle.newsroom_candidate_pool.v1", "contentops.newsroom_candidate_extractor",
        {"candidate_id": "cc-candidate-120438cc800db7f941be"},
        ("authority_readiness", "evidence_completeness", "material_delta"),
        contracts.EvidenceModality.CROSS_SOURCE_RECONCILIATION, True, True,
        "conformance:candidate:newsroom", "conformance:story:newsroom",
        contracts.EvidenceScope.CANDIDATE_WIDE,
    ),
)


PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1: tuple[ProductionAdapterSpecV1, ...] = (
    ProductionAdapterSpecV1(
        "us_treasury_daily_yield_curve_atom_v1", "us_treasury_daily_yield_curve",
        production_batch.TREASURY_PATH, production_batch.TREASURY_SCHEMA,
        production_batch.TREASURY_EXTRACTOR_ID,
        {"record_date": "1991-03-14", "maturity": "BC_10YEAR"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, False, "conformance:candidate:treasury-yield", "conformance:story:treasury-yield",
        verifier_id=production_batch.VERIFIER_ID, verifier_version=production_batch.VERIFIER_VERSION,
        expected_git_blob_sha1=production_batch.PINNED_ARTIFACTS[production_batch.TREASURY_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_batch.PINNED_ARTIFACTS[production_batch.TREASURY_EXTRACTOR_ID]["byte_sha256"],
    ),
    ProductionAdapterSpecV1(
        "cftc_legacy_futures_only_cot_v1", "cftc_legacy_futures_only_cot",
        production_batch.CFTC_PATH, production_batch.CFTC_SCHEMA,
        production_batch.CFTC_EXTRACTOR_ID,
        {"contract_market_code": "001602", "report_date": "2026-06-02"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, True, "conformance:candidate:cftc-cot", "conformance:story:cftc-cot",
        verifier_id=production_batch.VERIFIER_ID, verifier_version=production_batch.VERIFIER_VERSION,
        expected_git_blob_sha1=production_batch.PINNED_ARTIFACTS[production_batch.CFTC_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_batch.PINNED_ARTIFACTS[production_batch.CFTC_EXTRACTOR_ID]["byte_sha256"],
    ),
    ProductionAdapterSpecV1(
        "federal_reserve_h41_zip_structure_v1", "federal_reserve_h41",
        production_batch.H41_PATH, production_batch.H41_SCHEMA,
        production_batch.H41_EXTRACTOR_ID, {"dataset_id": "H41"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        False, True, "conformance:candidate:fed-h41", "conformance:story:fed-h41",
        verifier_id=production_batch.VERIFIER_ID, verifier_version=production_batch.VERIFIER_VERSION,
        expected_git_blob_sha1=production_batch.PINNED_ARTIFACTS[production_batch.H41_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_batch.PINNED_ARTIFACTS[production_batch.H41_EXTRACTOR_ID]["byte_sha256"],
    ),
)


PRODUCTION_ADAPTER_WAVE2_V1: tuple[ProductionAdapterSpecV1, ...] = (
    ProductionAdapterSpecV1(
        "us_treasury_debt_to_penny_v1", "us_treasury_fiscaldata_debt_to_penny",
        production_wave2.TREASURY_PATH, production_wave2.TREASURY_SCHEMA,
        production_wave2.TREASURY_EXTRACTOR_ID, {"record_date": "2026-06-01"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, False, "conformance:candidate:treasury-debt", "conformance:story:treasury-debt",
        verifier_id=production_wave2.VERIFIER_ID, verifier_version=production_wave2.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave2.PINNED_ARTIFACTS[production_wave2.TREASURY_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave2.PINNED_ARTIFACTS[production_wave2.TREASURY_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave2.PINNED_ARTIFACTS[production_wave2.TREASURY_EXTRACTOR_ID]["producer_commit"],
        extractor_version=production_wave2.EXTRACTOR_VERSION,
    ),
    ProductionAdapterSpecV1(
        "bls_unemployment_series_v1", "bls_public_unemployment_series",
        production_wave2.BLS_PATH, production_wave2.BLS_SCHEMA,
        production_wave2.BLS_EXTRACTOR_ID, {"series_id": "LNS14000000", "year": "2026", "period": "M05"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, False, "conformance:candidate:bls-unemployment", "conformance:story:bls-unemployment",
        verifier_id=production_wave2.VERIFIER_ID, verifier_version=production_wave2.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave2.PINNED_ARTIFACTS[production_wave2.BLS_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave2.PINNED_ARTIFACTS[production_wave2.BLS_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave2.PINNED_ARTIFACTS[production_wave2.BLS_EXTRACTOR_ID]["producer_commit"],
        extractor_version=production_wave2.EXTRACTOR_VERSION,
    ),
    ProductionAdapterSpecV1(
        "federal_reserve_fomc_calendar_html_v1", "federal_reserve_fomc_calendar",
        production_wave2.FOMC_PATH, production_wave2.FOMC_SCHEMA,
        production_wave2.FOMC_EXTRACTOR_ID, {"year": "2026", "month": "January", "meeting_dates": "27-28"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        False, True, "conformance:candidate:fomc-calendar", "conformance:story:fomc-calendar",
        verifier_id=production_wave2.VERIFIER_ID, verifier_version=production_wave2.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave2.PINNED_ARTIFACTS[production_wave2.FOMC_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave2.PINNED_ARTIFACTS[production_wave2.FOMC_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave2.PINNED_ARTIFACTS[production_wave2.FOMC_EXTRACTOR_ID]["producer_commit"],
        extractor_version=production_wave2.EXTRACTOR_VERSION,
    ),
)


PRODUCTION_ADAPTER_WAVE3_V1: tuple[ProductionAdapterSpecV1, ...] = (
    ProductionAdapterSpecV1(
        "us_treasury_tic_official_html_v1", "us_treasury_international_capital_portal",
        production_wave3.TIC_PATH, production_wave3.TIC_SCHEMA,
        production_wave3.TIC_EXTRACTOR_ID, {"canonical_url": "https://home.treasury.gov/data/treasury-international-capital-tic-system"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        False, True, "conformance:candidate:treasury-tic", "conformance:story:treasury-tic",
        verifier_id=production_wave3.VERIFIER_ID, verifier_version=production_wave3.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave3.PINNED_ARTIFACTS[production_wave3.TIC_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave3.PINNED_ARTIFACTS[production_wave3.TIC_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave3.PINNED_ARTIFACTS[production_wave3.TIC_EXTRACTOR_ID]["producer_commit"],
    ),
    ProductionAdapterSpecV1(
        "usgs_earthquake_geojson_v1", "usgs_earthquake_event",
        production_wave3.USGS_PATH, production_wave3.USGS_SCHEMA,
        production_wave3.USGS_EXTRACTOR_ID, {"event_id": "aka2026nmtsmu"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.NUMERIC_TIME_SERIES,
        True, True, "conformance:candidate:usgs-earthquake", "conformance:story:usgs-earthquake",
        verifier_id=production_wave3.VERIFIER_ID, verifier_version=production_wave3.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave3.PINNED_ARTIFACTS[production_wave3.USGS_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave3.PINNED_ARTIFACTS[production_wave3.USGS_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave3.PINNED_ARTIFACTS[production_wave3.USGS_EXTRACTOR_ID]["producer_commit"],
    ),
    ProductionAdapterSpecV1(
        "fhfa_hpi_official_html_v1", "fhfa_house_price_index_page",
        production_wave3.FHFA_PATH, production_wave3.FHFA_SCHEMA,
        production_wave3.FHFA_EXTRACTOR_ID, {"canonical_url": "https://www.fhfa.gov/data/hpi"},
        ("evidence_completeness", "freshness"), contracts.EvidenceModality.OFFICIAL_DOCUMENT,
        False, True, "conformance:candidate:fhfa-hpi", "conformance:story:fhfa-hpi",
        verifier_id=production_wave3.VERIFIER_ID, verifier_version=production_wave3.VERIFIER_VERSION,
        expected_git_blob_sha1=production_wave3.PINNED_ARTIFACTS[production_wave3.FHFA_EXTRACTOR_ID]["git_blob_sha1"],
        expected_byte_sha256=production_wave3.PINNED_ARTIFACTS[production_wave3.FHFA_EXTRACTOR_ID]["byte_sha256"],
        pinned_producer_commit=production_wave3.PINNED_ARTIFACTS[production_wave3.FHFA_EXTRACTOR_ID]["producer_commit"],
    ),
)


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.suffix == ".git" else ["git", "-C", str(repository)]


def _git_bytes(repository: Path, commit: str, path: str) -> bytes:
    try:
        return subprocess.run(
            [*_git_prefix(repository), "show", f"{commit}:{path}"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise ValueError("conformance_artifact_resolution_failed") from error


def _git_commit_time(repository: Path, commit: str) -> str:
    try:
        value = subprocess.run(
            [*_git_prefix(repository), "show", "-s", "--format=%cI", commit], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ValueError("conformance_commit_time_unavailable") from error
    return contracts.parse_utc(value, field_name="git_commit_time").isoformat().replace("+00:00", "Z")


def _verify_commit_ancestry(repository: Path, commit: str, branch_authority_ref: str) -> None:
    """Reject a producer commit before consuming bytes unless the fetched ref contains it."""
    prefix = _git_prefix(repository)
    try:
        branch_head = subprocess.run(
            [*prefix, "rev-parse", "--verify", branch_authority_ref], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ValueError("conformance_branch_authority_ref_unavailable") from error
    ancestry = subprocess.run(
        [*prefix, "merge-base", "--is-ancestor", commit, branch_head],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if ancestry.returncode != 0:
        raise ValueError("committed_artifact_not_reachable_from_observed_branch")


def _artifact_contract(consumed: bytes, spec: ProductionAdapterSpecV1, commit_time: str, shape_contract: str) -> tuple[str, str]:
    if spec.extractor_id != "contentops.newsroom_candidate_extractor":
        return commit_time, shape_contract
    try:
        artifact = json.loads(consumed)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("conformance_internal_artifact_json_invalid") from error
    return str(artifact.get("cutoff_time_utc", "")), str(artifact.get("producer_version", ""))


def _probe_reason_codes(
    *, record: contracts.ExtractedEvidenceRecordV1,
    expected_evidence_refs: Sequence[str] | None,
    claimed_authority_state: str | None,
    claimed_permission_state: str | None,
    claimed_roles: Sequence[contracts.EvidenceRole] | None,
    aggregation_input_refs: Sequence[str] | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if claimed_authority_state is not None and claimed_authority_state != record.authority_state and contracts.AUTHORITY_STATE_RANK.get(claimed_authority_state, -1) >= contracts.AUTHORITY_STATE_RANK.get(record.authority_state, -1):
        reasons.append("caller_authority_upgrade_forbidden")
    if claimed_permission_state is not None and claimed_permission_state != record.permission_state and contracts.PERMISSION_STATE_RANK.get(claimed_permission_state, -1) >= contracts.PERMISSION_STATE_RANK.get(record.permission_state, -1):
        reasons.append("caller_permission_upgrade_forbidden")
    if claimed_roles is not None and any(role not in record.evidence_roles for role in claimed_roles):
        reasons.append("caller_evidence_role_addition_forbidden")
    if expected_evidence_refs is not None and set(expected_evidence_refs) != {record.evidence_ref}:
        reasons.append("arbitrary_or_incomplete_evidence_ref_set")
    if aggregation_input_refs is not None and set(aggregation_input_refs) != {record.evidence_ref}:
        reasons.append("feature_aggregation_exact_set_mismatch")
    return tuple(dict.fromkeys(reasons))


def run_adapter_conformance(
    spec: ProductionAdapterSpecV1,
    *,
    repo_root: str | Path,
    upstream_git_repository: str | Path,
    upstream_commit: str,
    branch_authority_ref: str = "refs/remotes/origin/main",
    decision_cutoff_utc: str = DECISION_CUTOFF_UTC,
    expected_evidence_refs: Sequence[str] | None = None,
    claimed_authority_state: str | None = None,
    claimed_permission_state: str | None = None,
    claimed_roles: Sequence[contracts.EvidenceRole] | None = None,
    aggregation_input_refs: Sequence[str] | None = None,
) -> Mapping[str, Any]:
    """Conform one adapter without network access or repository writes."""
    root, upstream = Path(repo_root).resolve(), Path(upstream_git_repository).resolve()
    verifier_registry = adapters.load_trusted_verifier_registry(root)
    extractor_registry = extraction.load_extractor_registry(root)
    coverage_result = contract_coverage.validate_registry_contract_coverage(extractor_registry)
    extractor = extractor_registry.resolve(spec.extractor_id, spec.extractor_version)
    if extractor is None or not extractor.enabled:
        raise ValueError("conformance_extractor_unavailable")
    _verify_commit_ancestry(upstream, upstream_commit, branch_authority_ref)
    consumed = _git_bytes(upstream, upstream_commit, spec.artifact_path)
    artifact_cutoff, producer_version = _artifact_contract(
        consumed, spec, _git_commit_time(upstream, upstream_commit), extractor.shape_contract_id,
    )
    if spec.verifier_id == production_batch.VERIFIER_ID:
        receipt = production_batch.build_production_git_artifact_receipt(
            git_repository=upstream, registry=verifier_registry, commit=upstream_commit,
            artifact_path=spec.artifact_path, artifact_schema_version=spec.artifact_schema_version,
            producer_version=producer_version, artifact_cutoff_utc=artifact_cutoff,
            verification_time_utc=decision_cutoff_utc, branch_authority_ref=branch_authority_ref,
            expected_git_blob_sha1=spec.expected_git_blob_sha1,
            expected_byte_sha256=spec.expected_byte_sha256,
        )
    elif spec.verifier_id == production_wave2.VERIFIER_ID:
        receipt = production_wave2.build_wave2_git_artifact_receipt(
            git_repository=upstream, registry=verifier_registry, commit=upstream_commit,
            artifact_path=spec.artifact_path, artifact_schema_version=spec.artifact_schema_version,
            producer_version=producer_version, artifact_cutoff_utc=artifact_cutoff,
            verification_time_utc=decision_cutoff_utc, branch_authority_ref=branch_authority_ref,
            expected_git_blob_sha1=spec.expected_git_blob_sha1,
            expected_byte_sha256=spec.expected_byte_sha256,
        )
    elif spec.verifier_id == production_wave3.VERIFIER_ID:
        receipt = production_wave3.build_wave3_git_artifact_receipt(
            git_repository=upstream, registry=verifier_registry, commit=upstream_commit,
            artifact_path=spec.artifact_path, artifact_schema_version=spec.artifact_schema_version,
            producer_version=producer_version, artifact_cutoff_utc=artifact_cutoff,
            verification_time_utc=decision_cutoff_utc, branch_authority_ref=branch_authority_ref,
            expected_git_blob_sha1=spec.expected_git_blob_sha1,
            expected_byte_sha256=spec.expected_byte_sha256,
        )
    else:
        receipt = adapters.build_local_git_artifact_receipt(
            git_repository=upstream, repository_identity=UPSTREAM_REPOSITORY,
            branch=UPSTREAM_BRANCH, commit=upstream_commit, artifact_path=spec.artifact_path,
            artifact_schema_version=spec.artifact_schema_version, producer_version=producer_version,
            artifact_cutoff_utc=artifact_cutoff, evidence_refs=(),
            source_authority_class="official_public_data", registry=verifier_registry,
            verification_time_utc=decision_cutoff_utc, branch_authority_ref=branch_authority_ref,
        )
    if spec.extractor_id in {
        production_batch.TREASURY_EXTRACTOR_ID,
        production_batch.CFTC_EXTRACTOR_ID,
        production_batch.H41_EXTRACTOR_ID,
    }:
        record, feature_values = production_batch.extract_production_artifact_evidence(
            consumed, receipt=receipt, registry=extractor_registry,
            extractor_id=spec.extractor_id, extractor_version=spec.extractor_version,
            selector=spec.selector, feature_targets=spec.feature_targets,
            decision_cutoff_utc=decision_cutoff_utc, evidence_scope=spec.evidence_scope,
            repo_root=root,
        )
    elif spec.extractor_id in {
        production_wave2.TREASURY_EXTRACTOR_ID,
        production_wave2.BLS_EXTRACTOR_ID,
        production_wave2.FOMC_EXTRACTOR_ID,
    }:
        record, feature_values = production_wave2.extract_wave2_artifact_evidence(
            consumed, receipt=receipt, registry=extractor_registry,
            extractor_id=spec.extractor_id, extractor_version=spec.extractor_version,
            selector=spec.selector, feature_targets=spec.feature_targets,
            decision_cutoff_utc=decision_cutoff_utc, evidence_scope=spec.evidence_scope,
        )
    elif spec.extractor_id in {
        production_wave3.TIC_EXTRACTOR_ID,
        production_wave3.USGS_EXTRACTOR_ID,
        production_wave3.FHFA_EXTRACTOR_ID,
    }:
        record, feature_values = production_wave3.extract_wave3_artifact_evidence(
            consumed, receipt=receipt, registry=extractor_registry,
            extractor_id=spec.extractor_id, extractor_version=spec.extractor_version,
            selector=spec.selector, feature_targets=spec.feature_targets,
            decision_cutoff_utc=decision_cutoff_utc, evidence_scope=spec.evidence_scope,
        )
    else:
        record, feature_values = extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=extractor_registry,
            extractor_id=spec.extractor_id, extractor_version=spec.extractor_version,
            selector=spec.selector, feature_targets=spec.feature_targets,
            decision_cutoff_utc=decision_cutoff_utc, evidence_scope=spec.evidence_scope,
        )
    probe_reasons = _probe_reason_codes(
        record=record, expected_evidence_refs=expected_evidence_refs,
        claimed_authority_state=claimed_authority_state,
        claimed_permission_state=claimed_permission_state, claimed_roles=claimed_roles,
        aggregation_input_refs=aggregation_input_refs,
    )
    context = contracts.EvidenceDecisionContextV1(
        verifier_registry, (receipt,), decision_cutoff_utc,
        extractor_registry, (record,), tuple(feature_values), (),
    )
    context_blockers = context.validate()
    binding = adapters.build_receipt_backed_evidence_binding(
        context, evidence_ref=record.evidence_ref, evidence_roles=record.evidence_roles,
        evidence_scope=record.evidence_scope, authority_state=record.authority_state,
        permission_state=record.permission_state, target_feature_ids=record.feature_targets,
        as_of_utc=artifact_cutoff,
    )
    relationship = contracts.EventRelationship.NEW_PHASE if contracts.EvidenceRole.NEW_PHASE in record.evidence_roles else contracts.EventRelationship.INITIAL_EVENT
    candidate_draft = core.LearningCandidateV2(
        candidate_id=spec.candidate_id, story_id=spec.story_id,
        cluster_id=f"conformance:cluster:{spec.artifact_family}",
        update_chain_id=f"conformance:chain:{spec.artifact_family}",
        source_relationship=relationship, evidence_state="SCHEMA_EXTRACTED_FROM_EXACT_COMMITTED_BYTES",
        authority_state="BLOCKED", authority_ready=False, reporting_allowed=False,
        authority_blockers=("candidate_authority_not_yet_derived",),
        history_identity_match=False, update_chain_continuity=relationship == contracts.EventRelationship.NEW_PHASE,
        distinct_new_event_ref=record.evidence_ref if relationship == contracts.EventRelationship.NEW_PHASE else None,
        material_reader_contribution=True,
        feature_inputs=tuple(core.FeatureInputV1(
            row.feature_id, True, row.availability, row.value,
            unavailable_reason=row.reason_code if row.value is None else None,
            evidence_refs=(record.evidence_ref,), evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT,),
            evidence_scope=record.evidence_scope,
        ) for row in feature_values),
        evidence_refs=(record.evidence_ref,), governed_evidence_bindings=(binding,),
        capabilities=contracts.CapabilityDimensionsV1(
            evidence_modalities=(spec.modality,), temporal_characters=(contracts.TemporalCharacter.POINT_IN_TIME,),
            story_modes=(contracts.StoryMode.DATA_RELEASE,), source_family_ids=(spec.artifact_family,),
            source_authority_classes=("official_public_data",),
            numeric_evidence_present=spec.numeric, nonnumeric_evidence_present=spec.nonnumeric,
        ), evidence_context=context,
    )
    derived_authority = core.derive_candidate_authority_v1(candidate_draft, context)
    candidate = replace(
        candidate_draft, authority_state=derived_authority.authority_state,
        authority_ready=derived_authority.authority_ready,
        reporting_allowed=derived_authority.reporting_allowed,
        authority_blockers=derived_authority.authority_blockers,
    )
    candidate_blockers = core.validate_candidate_collection(
        (candidate,), adapters.load_foundation_config(root), evidence_context=context,
    )
    decision = core.build_learning_decision_v2(
        candidates=(candidate,), history=contracts.PublishedContentHistoryV1("conformance:history:none"),
        gaps=contracts.ContentGapSetV1("conformance:gaps:none"),
        observations=contracts.PerformanceObservationSetV1("conformance:observations:none"),
        config=adapters.load_foundation_config(root),
        input_bindings={"receipt": receipt.logical_hash, "extraction": record.extraction_logical_hash},
        logical_time_basis="production-adapter-conformance-v1",
        decision_cutoff_utc=decision_cutoff_utc, evidence_context=context,
    )
    outcome = decision.outcome_matrix[0]
    checks = {
        "exact_git_receipt": not receipt.validate(),
        "historical_ancestry": receipt.producer_commit_reachable_from_branch,
        "registry_membership": extractor.enabled and not verifier_registry.validate() and not extractor_registry.validate(),
        "registry_contract_coverage": coverage_result["status"] == "PASS",
        "shape_and_schema": record.artifact_schema_verified and record.producer_version_verified,
        "byte_derived_evidence_ref": record.evidence_ref.startswith("extracted:"),
        "point_in_time": not context_blockers,
        "derived_authority_permission_roles": not probe_reasons,
        "scope_feature_consistency": set(record.feature_targets) == set(spec.feature_targets),
        "derived_or_unavailable_features": all(row.value is not None or row.reason_code for row in feature_values),
        "exact_evidence_set": not probe_reasons,
        "candidate_authority_consistency": not candidate_blockers,
        "no_publication": "NO_PUBLICATION" in str(outcome["publication_disposition"]),
        "no_external_mutation": True,
    }
    reasons = tuple(dict.fromkeys((*probe_reasons, *context_blockers, *candidate_blockers)))
    passed = all(checks.values()) and not reasons
    return {
        "schema_version": SCHEMA_VERSION, "harness_version": HARNESS_VERSION,
        "adapter_id": spec.adapter_id, "artifact_family": spec.artifact_family,
        "status": "PASS" if passed else "REJECTED", "reason_codes": list(reasons),
        "upstream": {"repository": UPSTREAM_REPOSITORY, "branch": UPSTREAM_BRANCH,
                     "commit": upstream_commit, "producer_commit": upstream_commit,
                     "branch_authority_ref": branch_authority_ref, "path": spec.artifact_path,
                     "branch_head_observed": receipt.branch_head_observed,
                     "commit_reachable_from_branch": receipt.producer_commit_reachable_from_branch,
                     "git_blob_sha1": receipt.git_blob_sha1, "byte_sha256": receipt.consumed_byte_sha256},
        "receipt_id": receipt.receipt_id, "extractor_id": record.extractor_id,
        "extractor_version": record.extractor_version, "evidence_ref": record.evidence_ref,
        "authority_state": record.authority_state, "permission_state": record.permission_state,
        "evidence_roles": [role.value for role in record.evidence_roles],
        "evidence_scope": record.evidence_scope.value,
        "timestamps": {
            "observed_at_utc": record.observed_at_utc,
            "known_at_utc": record.known_at_utc,
            "published_at_utc": record.published_at_utc,
            "revision_at_utc": record.revision_at_utc,
            "artifact_cutoff_utc": record.cutoff_utc,
        },
        "feature_results": contracts.primitive(feature_values), "checks": checks,
        "publication_disposition": outcome["publication_disposition"],
        "publication_authority_granted": False, "numeric_truth_granted": False,
        "writes_performed": 0,
    }


def run_four_adapter_conformance(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
    upstream_commit: str, branch_authority_ref: str = "refs/remotes/origin/main",
) -> Mapping[str, Any]:
    results = [run_adapter_conformance(
        spec, repo_root=repo_root, upstream_git_repository=upstream_git_repository,
        upstream_commit=upstream_commit, branch_authority_ref=branch_authority_ref,
    ) for spec in PRODUCTION_ADAPTERS_V1]
    return {
        "schema_version": "contentops.production_adapter_conformance_set.v1",
        "harness_version": HARNESS_VERSION, "upstream_commit": upstream_commit,
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "adapter_count": len(results), "results": results,
        "network_calls": 0, "writes_performed": 0, "publication_authority_granted": False,
    }


def run_treasury_cftc_h41_adapter_conformance(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
    upstream_commit: str = production_batch.UPSTREAM_PINNED_COMMIT,
    branch_authority_ref: str = "refs/remotes/origin/main",
) -> Mapping[str, Any]:
    results = [run_adapter_conformance(
        spec, repo_root=repo_root, upstream_git_repository=upstream_git_repository,
        upstream_commit=upstream_commit, branch_authority_ref=branch_authority_ref,
    ) for spec in PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1]
    return {
        "schema_version": "contentops.production_adapter_conformance_set.v1",
        "harness_version": HARNESS_VERSION, "upstream_commit": upstream_commit,
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "adapter_count": len(results), "results": results,
        "network_calls": 0, "writes_performed": 0,
        "publication_authority_granted": False, "numeric_truth_granted": False,
    }


def run_wave2_adapter_conformance(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
    branch_authority_ref: str = "refs/remotes/origin/main",
    pinned_commit_override: str | None = None,
) -> Mapping[str, Any]:
    """Run wave 2 with historical pins and the actual fetched branch ref."""
    results = [run_adapter_conformance(
        spec, repo_root=repo_root, upstream_git_repository=upstream_git_repository,
        upstream_commit=pinned_commit_override or str(spec.pinned_producer_commit),
        branch_authority_ref=branch_authority_ref,
    ) for spec in PRODUCTION_ADAPTER_WAVE2_V1]
    observed = sorted({row["upstream"]["branch_head_observed"] for row in results})
    return {
        "schema_version": "contentops.production_adapter_conformance_set.v1",
        "harness_version": HARNESS_VERSION,
        "branch_authority_ref": branch_authority_ref,
        "observed_branch_heads": observed,
        "producer_commits": [row["upstream"]["producer_commit"] for row in results],
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "adapter_count": len(results), "results": results,
        "network_calls": 0, "writes_performed": 0,
        "publication_authority_granted": False, "numeric_truth_granted": False,
    }


def run_wave3_adapter_conformance(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
    branch_authority_ref: str = "refs/remotes/origin/main",
) -> Mapping[str, Any]:
    """Run Wave 3 from each historical producer pin against the fetched branch."""
    results = [run_adapter_conformance(
        spec, repo_root=repo_root, upstream_git_repository=upstream_git_repository,
        upstream_commit=str(spec.pinned_producer_commit), branch_authority_ref=branch_authority_ref,
    ) for spec in PRODUCTION_ADAPTER_WAVE3_V1]
    return {
        "schema_version": "contentops.production_adapter_conformance_set.v1",
        "harness_version": HARNESS_VERSION, "branch_authority_ref": branch_authority_ref,
        "observed_branch_heads": sorted({row["upstream"]["branch_head_observed"] for row in results}),
        "producer_commits": [row["upstream"]["producer_commit"] for row in results],
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "adapter_count": len(results), "results": results,
        "network_calls": 0, "writes_performed": 0,
        "publication_authority_granted": False, "numeric_truth_granted": False,
    }
