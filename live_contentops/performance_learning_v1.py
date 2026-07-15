"""Deterministic local replay of released ContentOps publication evidence.

No API, browser, network, credential, environment, scraper, LLM, scheduler,
publishing, or dispatch behavior is permitted. Missing analytics stay null and
UNAVAILABLE; they are never converted into zero values.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Sequence

from live_contentops import manual_publish_record_metrics_ledger_contract as ledger

TASK_LABEL = "TASK_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_AND_CONTENT_IDEA_LOOP_V1_COMPLETION"
MODEL_VERSION = "contentops.performance_learning.v1.real_evidence_replay"
DOC_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_V1"
PACKET_FILENAME = "contentops_performance_learning_v1_packet.json"
RUNBOOK_FILENAME = "contentops_performance_learning_v1.md"
RELEASE_REL_DIR = Path("docs") / "automation" / "DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1" / "contentops_database_publication_live_20260714_1"
POOL_REL_PATH = Path("docs") / "automation" / "CONTENTOPS_NEWSROOM_AND_TIER1_FINAL_ACCEPTANCE_GAP_CLOSURE_V3" / "contentops_newsroom_tier1_final_gap_closure_v3_20260714_1" / "newsroom_candidate_pool_upstream_bound_v3.json"
SEED_REL_PATH = Path("docs") / "automation" / "CONTENTOPS_NEWSROOM_AND_TIER1_FINAL_ACCEPTANCE_GAP_CLOSURE_V3" / "contentops_newsroom_tier1_final_gap_closure_v3_20260714_1" / "historical_publication_seed_v1_0.json"
PINNED_UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
PINNED_UPSTREAM_BRANCH = "main"
PINNED_UPSTREAM_COMMIT = "0cd7f5545169389204d5f62fdf5a74a73394411b"
AUTHORITY_MANUAL_OPERATOR_ENTRY = "manual_operator_entry"
AUTHORITY_UNAVAILABLE = "unavailable_committed_evidence"
COLLECTION_OPERATOR_ATTESTED_MANUAL_ENTRY = "operator_attested_manual_entry"
COLLECTION_RECORDED_REVIEW_ONLY = "recorded_review_only"
COLLECTION_UNAVAILABLE = "UNAVAILABLE"
RETROSPECTIVE_INCONCLUSIVE = "INCONCLUSIVE_INSUFFICIENT_COHORT"
RETROSPECTIVE_DESCRIPTIVE = "DESCRIPTIVE_REVIEW_ONLY"
RETROSPECTIVE_UNAVAILABLE = "NO_PERFORMANCE_CONCLUSION_UNAVAILABLE_METRICS"
IDEA_NO_IDEA = "no_idea"
TERMINAL_NO_IDEA = "PASS_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_AND_CONTENT_IDEA_LOOP_V1_NO_IDEA_ALREADY_PUBLISHED_CLUSTER"
OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
MINIMUM_DISTINCT_IDENTITIES = 3
FORBIDDEN_LEARNING_EFFECTS = (
    "claim_values", "source_authority", "public_use_permissions", "dqr",
    "exact_proxy_context_labels", "factual_conclusions", "risk_language",
    "citation_requirements", "scheduler_scores", "writer_guidance",
    "platform_defaults", "editorial_artifact_mutation",
)


@dataclass(frozen=True)
class ContentOpsContentIdentityV1:
    identity_id: str; evidence_packet_id: str; evidence_packet_schema_version: str; story_cluster_id: str; candidate_id: str; assignment_decision_id: str; content_item_id: str; article_version_id: str; headline_variant_id: str; visual_bundle_id: str; platform_variant_id: str; platform_id: str; publication_window_id: str; experiment_id: str; canonical_url_hash: str; platform_post_id_hash: str; platform_url_hash: str; identity_status: str; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ContentOpsPerformanceSnapshotV1:
    snapshot_id: str; content_identity_id: str; content_item_id: str; platform_variant_id: str; platform_id: str; platform_post_id_hash: str; collected_at_epoch: int | None; observed_at_epoch: int | None; age_since_publication_seconds: int | None; metric_name: str; metric_value: float | None; metric_definition: str; metric_scope: str; denominator: str | None; authority_class: str; collection_method: str; collection_status: str; known_limitations: tuple[str, ...]; source_response_hash: str | None; source_manual_publish_record_id: str | None; source_manual_metrics_record_id: str | None; source_payload_hash: str | None; operator_attested: bool; api_verified: bool; scraped: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ContentOpsContentRetrospectiveV1:
    retrospective_id: str; input_snapshot_ids: tuple[str, ...]; cohort_definition: str; platform_id: str; sample_size: int; distinct_content_identity_count: int; available_metric_count: int; method_version: str; retrospective_status: str; confidence_class: str; summary: str; recommended_learning_action: str; known_limitations: tuple[str, ...]; forbidden_effects_checked: tuple[str, ...]; operator_status: str; can_update_scheduler: bool; can_update_writer_guidance: bool; can_update_platform_defaults: bool; can_auto_generate_content: bool; can_auto_publish: bool; can_dispatch: bool; public_postable: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ContentOpsIdeaCandidateV1:
    idea_candidate_id: str; source_retrospective_id: str; source_snapshot_ids: tuple[str, ...]; candidate_type: str; hypothesis: str; recommended_observation_action: str; confidence_class: str; required_human_review: bool; operator_status: str; can_create_editorial_brief: bool; can_auto_generate_content: bool; can_update_scheduler: bool; can_update_writer_guidance: bool; can_update_platform_defaults: bool; can_auto_publish: bool; can_dispatch: bool; public_postable: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PerformanceLearningPacketV1:
    packet_id: str; identities: tuple[ContentOpsContentIdentityV1, ...]; snapshots: tuple[ContentOpsPerformanceSnapshotV1, ...]; retrospectives: tuple[ContentOpsContentRetrospectiveV1, ...]; idea_candidates: tuple[ContentOpsIdeaCandidateV1, ...]; source_bindings: dict[str, Any]; terminal_classification: str; packet_hash: str; packet_hash_algorithm: str; all_records_manual_only: bool; all_learning_review_only: bool; no_collection_performed: bool; no_api_verification: bool; no_scraping: bool; no_automatic_editorial_mutation: bool; no_auto_publish: bool; no_dispatch: bool; no_public_claim_authorized: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]; next_required_gate: str


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"): return asdict(value)
    if isinstance(value, tuple): return [_asdict(item) for item in value]
    if isinstance(value, list): return [_asdict(item) for item in value]
    if isinstance(value, dict): return {str(key): _asdict(item) for key, item in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_asdict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(value: Any) -> str: return sha256(_json(value).encode("utf-8")).hexdigest()
def _hash(value: str) -> str: return sha256(str(value).encode("utf-8")).hexdigest()
def _unique(values: Sequence[Any]) -> tuple[str, ...]: return tuple(dict.fromkeys(str(value) for value in values if value not in (None, "")))
def _missing(**values: str) -> tuple[str, ...]: return tuple(f"missing_{key}" for key, value in values.items() if not str(value or "").strip())
def _module_root() -> Path: return Path(__file__).resolve().parents[1]


def _read_json(root: Path, relative_path: Path) -> dict[str, Any]:
    try:
        return json.loads((root / relative_path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        raise ValueError(f"missing_committed_evidence:{relative_path.as_posix()}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid_committed_evidence_json:{relative_path.as_posix()}") from error


def safety_flags() -> dict[str, bool]:
    disabled = ("platform_api_called", "provider_api_called", "metrics_api_verified", "metrics_scraped", "credential_hydrated", "env_read", "network_performed", "browser_session_used", "scheduler_enabled", "scheduler_mutated", "llm_provider_called", "scraping_performed", "automatic_editorial_mutation", "can_auto_generate_content", "can_auto_publish", "can_dispatch", "public_postable", "public_claim_authorized", "dqr_cleared", "publication_authority_granted", "ingestion_repo_mutated")
    return {**{name: False for name in disabled}, "manual_metrics_only": True, "operator_attested_only": True, "append_only": True, "human_review_required": True, "learning_firewall_enforced": True}


def build_content_identity(*, evidence_packet_id: str, story_cluster_id: str, candidate_id: str, assignment_decision_id: str, content_item_id: str, article_version_id: str, headline_variant_id: str, visual_bundle_id: str, platform_variant_id: str, platform_id: str, publication_window_id: str, experiment_id: str, canonical_url_reference: str, platform_post_reference: str, platform_url_reference: str, evidence_refs: tuple[str, ...] = ()) -> ContentOpsContentIdentityV1:
    blocked = _missing(evidence_packet_id=evidence_packet_id, story_cluster_id=story_cluster_id, candidate_id=candidate_id, assignment_decision_id=assignment_decision_id, content_item_id=content_item_id, article_version_id=article_version_id, headline_variant_id=headline_variant_id, visual_bundle_id=visual_bundle_id, platform_variant_id=platform_variant_id, platform_id=platform_id, publication_window_id=publication_window_id, experiment_id=experiment_id, canonical_url_reference=canonical_url_reference, platform_post_reference=platform_post_reference, platform_url_reference=platform_url_reference)
    material = {"packet": evidence_packet_id, "cluster": story_cluster_id, "candidate": candidate_id, "assignment": assignment_decision_id, "content": content_item_id, "article": article_version_id, "headline": headline_variant_id, "visual": visual_bundle_id, "platform_variant": platform_variant_id, "platform": platform_id, "window": publication_window_id, "experiment": experiment_id, "canonical": _hash(canonical_url_reference), "post": _hash(platform_post_reference), "url": _hash(platform_url_reference), "blocked": blocked}
    return ContentOpsContentIdentityV1("content_identity_" + _digest(material)[:24], evidence_packet_id, "capital_chronicle_content_evidence_packet.v2", story_cluster_id, candidate_id, assignment_decision_id, content_item_id, article_version_id, headline_variant_id, visual_bundle_id, platform_variant_id, platform_id, publication_window_id, experiment_id, material["canonical"], material["post"], material["url"], "VALID" if not blocked else "BLOCKED", _unique(evidence_refs), safety_flags(), blocked)


def _snapshot_blockers(identity: ContentOpsContentIdentityV1, publish: ledger.ManualPublishRecord, metrics: ledger.ManualMetricsRecord, metric_name: str) -> tuple[str, ...]:
    blocked = list(_missing(identity_id=identity.identity_id, metric_name=metric_name, manual_publish_record_id=publish.manual_publish_record_id, manual_metrics_record_id=metrics.manual_metrics_record_id, source_payload_hash=publish.source_payload_hash))
    if identity.identity_status != "VALID": blocked.append("content_identity_invalid")
    if identity.platform_id != publish.platform_id: blocked.append("identity_publish_platform_mismatch")
    if metrics.source_manual_publish_record_id != publish.manual_publish_record_id: blocked.append("manual_metrics_publish_record_mismatch")
    if metrics.source_payload_hash != publish.source_payload_hash: blocked.append("manual_metrics_payload_hash_mismatch")
    if metrics.platform_id != publish.platform_id: blocked.append("manual_metrics_platform_mismatch")
    if metrics.metric_values_are_operator_attested is not True: blocked.append("manual_metric_not_operator_attested")
    if metrics.metric_values_are_api_verified is not False: blocked.append("api_verified_metric_rejected")
    if metrics.metric_values_are_scraped is not False: blocked.append("scraped_metric_rejected")
    if metrics.metric_source_class not in {ledger.METRIC_SOURCE_OPERATOR, ledger.METRIC_SOURCE_PLATFORM_UI}: blocked.append("unsupported_manual_metric_source_class")
    if metrics.metric_observed_at_epoch < publish.manually_published_at_epoch: blocked.append("metric_observed_before_publication")
    if metrics.metric_recorded_at_epoch < metrics.metric_observed_at_epoch: blocked.append("metric_recorded_before_observation")
    return _unique(blocked)


def build_performance_snapshot(*, identity: ContentOpsContentIdentityV1, publish_record: ledger.ManualPublishRecord, metrics_record: ledger.ManualMetricsRecord, metric_name: str, metric_definition: str, metric_scope: str, denominator: str | None = None, known_limitations: tuple[str, ...] = ()) -> ContentOpsPerformanceSnapshotV1:
    blocked = list(_snapshot_blockers(identity, publish_record, metrics_record, metric_name))
    value = metrics_record.metrics.get(metric_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        blocked.append("metric_value_invalid"); value = None
    age = metrics_record.metric_observed_at_epoch - publish_record.manually_published_at_epoch
    if age < 0: blocked.append("metric_age_invalid"); age = None
    blocked_tuple = _unique(blocked)
    material = {"identity": identity.identity_id, "publish": publish_record.manual_publish_record_id, "metrics": metrics_record.manual_metrics_record_id, "metric": metric_name, "value": value, "observed": metrics_record.metric_observed_at_epoch, "collected": metrics_record.metric_recorded_at_epoch, "blocked": blocked_tuple}
    return ContentOpsPerformanceSnapshotV1("performance_snapshot_" + _digest(material)[:24], identity.identity_id, identity.content_item_id, identity.platform_variant_id, identity.platform_id, identity.platform_post_id_hash, metrics_record.metric_recorded_at_epoch, metrics_record.metric_observed_at_epoch, age, metric_name, float(value) if value is not None else None, metric_definition, metric_scope, denominator, AUTHORITY_MANUAL_OPERATOR_ENTRY, COLLECTION_OPERATOR_ATTESTED_MANUAL_ENTRY, COLLECTION_RECORDED_REVIEW_ONLY if not blocked_tuple else "BLOCKED", _unique(("Operator-attested manual metric entry; not verified platform analytics.", "No API or scraper collection was performed.", *known_limitations)), metrics_record.metric_url_hash, publish_record.manual_publish_record_id, metrics_record.manual_metrics_record_id, publish_record.source_payload_hash, metrics_record.metric_values_are_operator_attested, metrics_record.metric_values_are_api_verified, metrics_record.metric_values_are_scraped, _unique((*identity.evidence_refs, *publish_record.evidence_refs, *metrics_record.evidence_refs)), safety_flags(), blocked_tuple)


def build_unavailable_snapshot(*, identity: ContentOpsContentIdentityV1, source_payload_hash: str | None, metric_name: str = "impressions") -> ContentOpsPerformanceSnapshotV1:
    material = {"identity": identity.identity_id, "metric": metric_name, "payload": source_payload_hash, "status": COLLECTION_UNAVAILABLE}
    return ContentOpsPerformanceSnapshotV1("performance_snapshot_" + _digest(material)[:24], identity.identity_id, identity.content_item_id, identity.platform_variant_id, identity.platform_id, identity.platform_post_id_hash, None, None, None, metric_name, None, "Platform-displayed impression count, if later manually attested.", "single published destination; no analytics observation is present in committed evidence", None, AUTHORITY_UNAVAILABLE, "committed_evidence_no_metric_record", COLLECTION_UNAVAILABLE, ("No operator-attested performance metric was present in the committed release evidence.", "No API, browser, scraper, credential, or network collection was performed.", "Null means unavailable; it does not mean zero performance."), None, None, None, source_payload_hash, False, False, False, identity.evidence_refs, safety_flags(), ())


def append_snapshot(existing_snapshots: Sequence[ContentOpsPerformanceSnapshotV1], snapshot: ContentOpsPerformanceSnapshotV1) -> tuple[ContentOpsPerformanceSnapshotV1, ...]:
    for old in existing_snapshots:
        if old.snapshot_id == snapshot.snapshot_id:
            if _json(old) != _json(snapshot): raise ValueError("append_only_snapshot_collision")
            return tuple(existing_snapshots)
    return (*existing_snapshots, snapshot)


def build_content_retrospective(snapshots: Sequence[ContentOpsPerformanceSnapshotV1], *, cohort_definition: str,
                                allow_cross_platform: bool = False) -> ContentOpsContentRetrospectiveV1:
    blocked: list[str] = []
    platforms = {snapshot.platform_id for snapshot in snapshots}
    if not snapshots: blocked.append("retrospective_requires_snapshots")
    if len(platforms) > 1 and not allow_cross_platform: blocked.append("mixed_platform_cohort_rejected")
    if not str(cohort_definition or "").strip(): blocked.append("missing_cohort_definition")
    for snapshot in snapshots:
        if snapshot.collection_status not in {COLLECTION_RECORDED_REVIEW_ONLY, COLLECTION_UNAVAILABLE}: blocked.append("blocked_snapshot_in_cohort")
        if snapshot.collection_status == COLLECTION_RECORDED_REVIEW_ONLY and (snapshot.authority_class != AUTHORITY_MANUAL_OPERATOR_ENTRY or snapshot.api_verified or snapshot.scraped or not snapshot.operator_attested): blocked.append("snapshot_manual_provenance_invalid")
    blocked_tuple = _unique(blocked)
    identities = len({snapshot.content_identity_id for snapshot in snapshots})
    available = sum(snapshot.metric_value is not None for snapshot in snapshots)
    if available == 0:
        status, confidence = RETROSPECTIVE_UNAVAILABLE, "no_metrics_available"
        summary, action = "No platform-performance conclusion is available because committed evidence contains no operator-attested metric values.", "Do not infer performance. If an operator later records comparable manual metrics, append them as new observations."
    elif identities < MINIMUM_DISTINCT_IDENTITIES:
        status, confidence = RETROSPECTIVE_INCONCLUSIVE, "insufficient_manual_sample"
        summary, action = "The governed cohort is too small for a comparative performance conclusion.", "Collect operator-attested observations across at least three distinct content identities before evaluating a packaging hypothesis."
    else:
        status, confidence = RETROSPECTIVE_DESCRIPTIVE, "low_manual_descriptive"
        summary, action = "Manual observations are descriptive only; they do not establish platform truth or causal effect.", "Present the bounded descriptive cohort to an operator for optional future-hypothesis review."
    refs = _unique(tuple(ref for snapshot in snapshots for ref in snapshot.evidence_refs))
    material = {"snapshots": [snapshot.snapshot_id for snapshot in snapshots], "cohort": cohort_definition, "status": status, "blocked": blocked_tuple}
    return ContentOpsContentRetrospectiveV1("content_retrospective_" + _digest(material)[:24], tuple(snapshot.snapshot_id for snapshot in snapshots), cohort_definition, "cross_platform", len(snapshots), identities, available, MODEL_VERSION, "BLOCKED" if blocked_tuple else status, "blocked" if blocked_tuple else confidence, summary, "No action; resolve blocked input provenance." if blocked_tuple else action, ("Metrics are manual operator entries only when present; no official platform analytics were collected.", "The cohort may be confounded by topic, timing, and audience growth.", "No causal or public performance conclusion is permitted."), FORBIDDEN_LEARNING_EFFECTS, OPERATOR_REVIEW_REQUIRED, False, False, False, False, False, False, False, refs, safety_flags(), blocked_tuple)


def build_idea_candidate(retrospective: ContentOpsContentRetrospectiveV1, *, candidate_is_already_published: bool = False) -> ContentOpsIdeaCandidateV1:
    blocked = list(retrospective.blocked_reasons)
    if retrospective.operator_status != OPERATOR_REVIEW_REQUIRED: blocked.append("operator_review_requirement_missing")
    if retrospective.forbidden_effects_checked != FORBIDDEN_LEARNING_EFFECTS: blocked.append("learning_firewall_check_incomplete")
    blocked_tuple = _unique(blocked)
    if candidate_is_already_published:
        kind, hypothesis, action, confidence = IDEA_NO_IDEA, "No idea candidate was generated: the only eligible candidate is already represented by the accepted published cluster.", "Require separately governed material-update, correction, contradiction, or new-phase evidence before considering a new idea.", "high_identity_match"
    elif retrospective.retrospective_status == RETROSPECTIVE_UNAVAILABLE:
        kind, hypothesis, action, confidence = IDEA_NO_IDEA, "No idea candidate was generated because no performance metric value is available in committed evidence.", "Do not create filler ideas; wait for a distinct governed candidate with a real contribution.", "no_metrics_available"
    elif retrospective.retrospective_status == RETROSPECTIVE_INCONCLUSIVE:
        kind, hypothesis, action, confidence = "observation_plan", "Collect more comparable manual observations before proposing any content packaging change.", retrospective.recommended_learning_action, retrospective.confidence_class
    elif retrospective.retrospective_status == RETROSPECTIVE_DESCRIPTIVE:
        kind, hypothesis, action, confidence = "review_hypothesis", "An operator may review the descriptive cohort for a future, separately governed packaging hypothesis.", retrospective.recommended_learning_action, retrospective.confidence_class
    else:
        kind, hypothesis, action, confidence = "blocked", "No learning candidate is available until source snapshot blockers are resolved.", retrospective.recommended_learning_action, "blocked"
    material = {"retrospective": retrospective.retrospective_id, "kind": kind, "hypothesis": hypothesis, "blocked": blocked_tuple}
    return ContentOpsIdeaCandidateV1("performance_idea_candidate_" + _digest(material)[:24], retrospective.retrospective_id, retrospective.input_snapshot_ids, kind, hypothesis, action, "blocked" if blocked_tuple else confidence, True, OPERATOR_REVIEW_REQUIRED, False, False, False, False, False, False, False, False, retrospective.evidence_refs, safety_flags(), blocked_tuple)


def _published_destination_identities(root: Path) -> tuple[tuple[ContentOpsContentIdentityV1, ...], tuple[ContentOpsPerformanceSnapshotV1, ...], dict[str, Any]]:
    manifest, matrix = _read_json(root, RELEASE_REL_DIR / "article_manifest_v1.json"), _read_json(root, RELEASE_REL_DIR / "final_platform_matrix_v1.json")
    pool, seed = _read_json(root, POOL_REL_PATH), _read_json(root, SEED_REL_PATH)
    publications, eligible = seed.get("publications", []), pool.get("eligible_candidates", [])
    if len(publications) != 1: raise ValueError("historical_seed_requires_exactly_one_publication")
    if len(eligible) != 1: raise ValueError("candidate_pool_requires_exactly_one_eligible_candidate")
    publication, candidate = publications[0], eligible[0]
    for field in ("candidate_id", "cluster_id", "story_id", "update_chain_id"):
        if candidate.get(field) != publication.get(field): raise ValueError(f"published_candidate_lineage_mismatch:{field}")
    if candidate.get("eligible") is not True or candidate.get("blockers"): raise ValueError("candidate_pool_eligible_candidate_not_usable")
    published = {name: row for name, row in matrix.get("destinations", {}).items() if row.get("status") == "SUCCESS"}
    if len(published) != 9: raise ValueError(f"release_requires_nine_published_destinations:{len(published)}")
    canonical_url = str(matrix.get("canonical_substack_url") or publication.get("canonical_url") or "")
    article_version = str(publication.get("accepted_public_body_sha256") or "")
    if not canonical_url or not article_version: raise ValueError("accepted_release_identity_missing")
    refs = ((RELEASE_REL_DIR / "final_platform_matrix_v1.json").as_posix(), (RELEASE_REL_DIR / "article_manifest_v1.json").as_posix(), POOL_REL_PATH.as_posix(), SEED_REL_PATH.as_posix())
    identities, snapshots = [], []
    for platform_id, destination in sorted(published.items()):
        post_id = str(destination.get("id") or "")
        if not post_id: raise ValueError(f"published_destination_missing_id:{platform_id}")
        payload_hash = str(destination.get("payload_sha256") or article_version)
        identity = build_content_identity(evidence_packet_id="cc-publication-73ff151c3d3094741b6c", story_cluster_id=str(candidate["cluster_id"]), candidate_id=str(candidate["candidate_id"]), assignment_decision_id=str(candidate.get("source_packet_id") or "cc-publication-73ff151c3d3094741b6c"), content_item_id="contentops-v1-0-treasury-publication-20260714", article_version_id=article_version, headline_variant_id=_hash(str(manifest.get("title") or "")), visual_bundle_id=str(destination.get("media_sha256") or "no_media_bundle"), platform_variant_id=f"{platform_id}:{payload_hash}", platform_id=platform_id, publication_window_id=str(matrix.get("run_id") or ""), experiment_id="historical_release_replay_no_experiment", canonical_url_reference=canonical_url, platform_post_reference=post_id, platform_url_reference=str(destination.get("public_url") or f"{platform_id}:published:{post_id}"), evidence_refs=refs)
        identities.append(identity); snapshots.append(build_unavailable_snapshot(identity=identity, source_payload_hash=payload_hash))
    bindings = {"release_run_id": matrix.get("run_id"), "release_tag": publication.get("release_tag"), "release_commit_sha": seed.get("source", {}).get("release_commit_sha"), "accepted_public_body_sha256": article_version, "canonical_url": canonical_url, "candidate_id": candidate.get("candidate_id"), "cluster_id": candidate.get("cluster_id"), "story_id": candidate.get("story_id"), "update_chain_id": candidate.get("update_chain_id"), "upstream_repository": PINNED_UPSTREAM_REPOSITORY, "upstream_branch": PINNED_UPSTREAM_BRANCH, "upstream_commit_sha": PINNED_UPSTREAM_COMMIT, "pool_replay_artifact": POOL_REL_PATH.as_posix(), "published_destination_count": len(published)}
    return tuple(identities), tuple(snapshots), bindings


def build_contract_packet(repo_root: str | Path | None = None) -> PerformanceLearningPacketV1:
    identities, snapshots, bindings = _published_destination_identities(_module_root() if repo_root is None else Path(repo_root).resolve())
    retrospective = build_content_retrospective(
        snapshots,
        cohort_definition="accepted v1.0 Treasury release: one unavailable-metric snapshot for each of nine published destinations",
        allow_cross_platform=True,
    )
    idea = build_idea_candidate(retrospective, candidate_is_already_published=True)
    draft = {"identities": identities, "snapshots": snapshots, "retrospectives": (retrospective,), "idea_candidates": (idea,), "source_bindings": bindings, "terminal_classification": TERMINAL_NO_IDEA, "all_records_manual_only": True, "all_learning_review_only": True, "no_collection_performed": True, "no_api_verification": True, "no_scraping": True, "no_automatic_editorial_mutation": True, "no_auto_publish": True, "no_dispatch": True, "no_public_claim_authorized": True, "evidence_refs": _unique(tuple(ref for identity in identities for ref in identity.evidence_refs)), "safety_flags": safety_flags(), "blocked_reasons": (), "next_required_gate": "INDEPENDENT_AUDIT_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_AND_CONTENT_IDEA_LOOP_V1"}
    packet_hash = _digest(draft)
    return PerformanceLearningPacketV1("performance_learning_packet_" + packet_hash[:24], packet_hash=packet_hash, packet_hash_algorithm="sha256", **draft)


def render_runbook(packet: PerformanceLearningPacketV1) -> str:
    return "\n".join(("# ContentOps Cross-Platform Performance Intelligence and Content Idea Loop V1", "", f"- task_label: `{TASK_LABEL}`", f"- model_version: `{MODEL_VERSION}`", f"- packet_id: `{packet.packet_id}`", f"- packet_hash: `{packet.packet_hash}`", f"- terminal_classification: `{packet.terminal_classification}`", "", "## Evidence boundary", "", "- The replay binds the accepted Treasury release to its nine successful published destinations.", "- The only eligible pool candidate is bound to the same historical v1.0 cluster.", "- No analytics value exists in committed evidence: every snapshot has `metric_value: null` and `collection_status: UNAVAILABLE`.", "- Null is unavailable, not zero; no collection or external capability was used.", "", "## No-idea decision", "", "- No distinct contribution supports a new idea because the only eligible candidate is already published.", "- A future idea requires separately governed material-update, correction, contradiction, or new-phase evidence.", "", "## Learning firewall", "", "- Performance evidence cannot alter claims, source authority, permissions, DQR, labels, citations, risk language, scheduler scores, guidance, defaults, or editorial artifacts.", "- No automatic brief, generation, publication, or dispatch is enabled.", "", "## Next required gate", "", f"`{packet.next_required_gate}`", ""))


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root, output = Path(repo_root).resolve(), None
    allowed = (root / DOC_REL_DIR).resolve()
    output = allowed if output_dir is None else Path(output_dir).resolve()
    if output != allowed: raise ValueError("artifact_writer_refuses_paths_outside_contentops_performance_learning_v1")
    output.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path, runbook_path = output / PACKET_FILENAME, output / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


def contract_checksum() -> str: return build_contract_packet().packet_hash


# Real-content retrospective and governed idea/assignment replay.  This layer is
# additive: the accepted V1 publication identity and UNAVAILABLE metric contract
# above remain unchanged.
REAL_LOOP_TASK_LABEL = "TASK_CONTENTOPS_REAL_CONTENT_RETROSPECTIVE_GAP_IDEA_AND_ASSIGNMENT_LOOP_V1"
REAL_LOOP_MODEL_VERSION = "contentops.real_content_idea_assignment_loop.v1"
REAL_LOOP_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_REAL_CONTENT_RETROSPECTIVE_GAP_IDEA_AND_ASSIGNMENT_LOOP_V1"
ARTICLE_REL_PATH = RELEASE_REL_DIR / "canonical_article.md"
NATIVE_PAYLOADS_REL_PATH = RELEASE_REL_DIR / "native_payloads_v1.json"
MANIFEST_REL_PATH = RELEASE_REL_DIR / "article_manifest_v1.json"
MATRIX_REL_PATH = RELEASE_REL_DIR / "final_platform_matrix_v1.json"
REAL_LOOP_FILENAMES = {
    "retrospective": "published_content_retrospective_v1.json",
    "derivative_comparison": "derivative_content_comparison_v1.json",
    "coverage_gaps": "coverage_gap_report_v1.json",
    "generated_ideas": "generated_ideas_v1.json",
    "rejected_ideas": "rejected_ideas_v1.json",
    "backlog": "governed_idea_backlog_v1.json",
    "briefs": "editorial_briefs_v1.json",
    "assignment": "assignment_replay_v1.json",
    "manifest": "real_content_idea_loop_manifest_v1.json",
}
REAL_LOOP_TERMINAL = "PASS_REAL_CONTENT_RETROSPECTIVE_GAP_IDEA_AND_ASSIGNMENT_LOOP_INTERNAL_ASSIGNMENT_ONLY"


def _read_text(root: Path, relative_path: Path) -> str:
    try:
        return (root / relative_path).read_text(encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise ValueError(f"missing_committed_evidence:{relative_path.as_posix()}") from error


def _normalized_sha256(text: str) -> str:
    return sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _payload_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("full_text"), str):
        return str(payload["full_text"])
    return str(payload.get("text") or "")


def _contains_any(text: str, needles: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def build_real_content_idea_loop(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Replay real published content into a governed, internal-only assignment.

    This function performs no collection and grants no new factual, publication,
    DQR, scheduling, or dispatch authority.  Candidate IDs and claim IDs are
    copied verbatim from committed bridge-read evidence.
    """
    root = _module_root() if repo_root is None else Path(repo_root).resolve()
    article = _read_text(root, ARTICLE_REL_PATH)
    manifest = _read_json(root, MANIFEST_REL_PATH)
    payloads = _read_json(root, NATIVE_PAYLOADS_REL_PATH)
    matrix = _read_json(root, MATRIX_REL_PATH)
    pool = _read_json(root, POOL_REL_PATH)
    article_sha = _normalized_sha256(article)
    declared_article_sha = str(manifest.get("article_markdown_sha256") or "")
    embedded_published_body = str(manifest.get("substack_body_markdown") or "")
    embedded_published_body_sha = _normalized_sha256(embedded_published_body)
    declared_published_body_sha = str(manifest.get("substack_body_markdown_sha256") or "")
    if embedded_published_body_sha != declared_published_body_sha:
        raise ValueError("embedded_published_body_hash_mismatch")
    article_export_hash_matches_manifest = article_sha == declared_article_sha
    if not article.strip() or len(article.split()) < 500:
        raise ValueError("canonical_article_body_not_substantive")

    successes = {key for key, value in matrix.get("destinations", {}).items() if value.get("status") == "SUCCESS"}
    expected_payload_platforms = successes - {"substack"}
    missing_payloads = sorted(expected_payload_platforms - set(payloads))
    if missing_payloads:
        raise ValueError("missing_native_payloads:" + ",".join(missing_payloads))

    section_checks = {
        "current_signal": ("30-year par yield reached 5.10%", "36 basis points"),
        "market_mechanism": ("term premium", "duration supply"),
        "policy_context": ("expected policy path", "30-year sector"),
        "cross_asset_boundary": ("without separate market data", "does not infer moves in other assets"),
        "confirmation_and_limits": ("What Would Confirm or Challenge", "signal would be challenged"),
        "sources_and_method": ("Sources and Method", "Daily Treasury Par Yield Curve Rates"),
    }
    article_coverage = {name: _contains_any(article, needles) for name, needles in section_checks.items()}
    if not all(article_coverage.values()):
        raise ValueError("canonical_article_required_section_missing")

    derivative_rows = []
    for platform_id in sorted(expected_payload_platforms):
        payload = payloads[platform_id]
        text = _payload_text(payload)
        if not text.strip():
            raise ValueError(f"empty_native_payload:{platform_id}")
        coverage = {name: _contains_any(text, needles) for name, needles in section_checks.items()}
        derivative_rows.append({
            "platform_id": platform_id,
            "format": payload.get("format"),
            "payload_text_sha256": _normalized_sha256(text),
            "character_count": len(text),
            "coverage": coverage,
            "covered_section_count": sum(coverage.values()),
            "omitted_sections": [name for name, present in coverage.items() if not present],
            "hard_truncation_used": bool(payload.get("hard_truncation_used", False)),
            "public_destination_status": matrix["destinations"][platform_id]["status"],
        })

    claim_ids = tuple(str(value) for value in manifest.get("claim_ids_used", []))
    if len(claim_ids) != 4 or any(not value for value in claim_ids):
        raise ValueError("published_article_claim_lineage_incomplete")
    eligible = list(pool.get("eligible_candidates", []))
    rejected = list(pool.get("rejected_candidates", []))
    if len(eligible) != 1 or len(rejected) != 2:
        raise ValueError("governed_pool_expected_three_mechanisms")
    published_candidate = eligible[0]
    published_binding = build_contract_packet(root).source_bindings
    if published_candidate.get("candidate_id") != published_binding.get("candidate_id") or published_candidate.get("cluster_id") != published_binding.get("cluster_id"):
        raise ValueError("published_cluster_identity_mismatch")

    retrospective = {
        "schema_version": "contentops.published_content_retrospective.v1",
        "retrospective_id": "real_retrospective_" + _digest({"article": article_sha, "payloads": derivative_rows})[:24],
        "article_path": ARTICLE_REL_PATH.as_posix(),
        "article_sha256": article_sha,
        "declared_article_export_sha256": declared_article_sha,
        "article_export_hash_matches_manifest": article_export_hash_matches_manifest,
        "embedded_published_body_sha256": declared_published_body_sha,
        "article_word_count_read": len(article.split()),
        "article_claim_ids": list(claim_ids),
        "article_coverage": article_coverage,
        "published_candidate_id": published_candidate["candidate_id"],
        "published_cluster_id": published_candidate["cluster_id"],
        "successful_destination_count": len(successes),
        "native_derivative_count_examined": len(derivative_rows),
        "metric_status": COLLECTION_UNAVAILABLE,
        "performance_conclusion": None,
        "content_findings": [
            "The canonical article explains the signal, mechanism, policy context, cross-asset boundary, and falsifiable confirmation conditions.",
            "Short derivatives consistently retain the current signal; mechanism and confirmation coverage varies by platform format.",
            "No platform-performance winner or causal packaging conclusion is permitted because committed metrics remain unavailable.",
        ],
        "evidence_refs": [ARTICLE_REL_PATH.as_posix(), MANIFEST_REL_PATH.as_posix(), NATIVE_PAYLOADS_REL_PATH.as_posix(), MATRIX_REL_PATH.as_posix()],
    }
    comparison = {
        "schema_version": "contentops.derivative_content_comparison.v1",
        "comparison_id": "derivative_comparison_" + _digest(derivative_rows)[:24],
        "canonical_article_sha256": article_sha,
        "rows": derivative_rows,
        "comparison_basis": "literal content coverage only; not performance",
        "metric_status": COLLECTION_UNAVAILABLE,
    }
    gap_report = {
        "schema_version": "contentops.coverage_gap_report.v1",
        "gap_report_id": "coverage_gap_" + _digest({"article": article_sha, "rows": derivative_rows})[:24],
        "gaps": [
            {
                "gap_id": "gap_confirmation_follow_up_" + article_sha[:16],
                "mechanism": "confirmation_or_challenge_follow_up",
                "source_article_section": "What Would Confirm or Challenge the Signal",
                "finding": "The article names subsequent official curve closes, Treasury auctions, and CPI as evidence needed to confirm or challenge the signal; the current packet ends at the July 13 close.",
                "required_claim_ids": list(claim_ids),
                "required_new_authority": ["fresh_exact_official_curve_claims", "story_scoped_reporting_authority", "citation_mapping"],
                "publication_ready": False,
            },
            {
                "gap_id": "gap_derivative_confirmation_" + article_sha[:16],
                "mechanism": "derivative_content_depth",
                "finding": "Confirmation and limits are absent from most single-post derivatives and preserved most fully in ordered thread formats.",
                "affected_platforms": [row["platform_id"] for row in derivative_rows if not row["coverage"]["confirmation_and_limits"]],
                "publication_ready": False,
            },
        ],
        "performance_basis_used": False,
    }

    generated_id = "governed_idea_" + _digest({"gap": gap_report["gaps"][0], "candidate": published_candidate["candidate_id"]})[:24]
    generated = [{
        "idea_id": generated_id,
        "mechanism": "published_content_confirmation_gap",
        "title": "Recheck whether the July 13 Treasury curve signal was confirmed or challenged",
        "source_candidate_id": published_candidate["candidate_id"],
        "source_cluster_id": published_candidate["cluster_id"],
        "source_claim_ids": list(claim_ids),
        "source_gap_id": gap_report["gaps"][0]["gap_id"],
        "status": "ASSIGNABLE_FOR_EVIDENCE_REFRESH_ONLY",
        "duplicate_published_cluster_suppressed": True,
        "new_article_authorized": False,
        "required_human_review": True,
    }]
    rejected_ideas = []
    for candidate in sorted(rejected, key=lambda item: str(item.get("candidate_id"))):
        blockers = list(candidate.get("blockers", []))
        disposition = "HOLD_AUTHORITY_GAP" if "real_regime_undetermined" in blockers else "REJECT_NOT_REPORTABLE"
        rejected_ideas.append({
            "idea_id": "governed_idea_" + _digest({"candidate": candidate.get("candidate_id"), "blockers": blockers})[:24],
            "mechanism": candidate.get("story_family"),
            "title": candidate.get("title"),
            "source_candidate_id": candidate.get("candidate_id"),
            "source_cluster_id": candidate.get("cluster_id"),
            "status": disposition,
            "blockers": blockers,
            "reporting_allowed": candidate.get("claim_permissions", {}).get("reporting_allowed") is True,
            "numeric_claims": list(candidate.get("numeric_claims", [])),
            "required_human_review": True,
        })
    backlog = {
        "schema_version": "contentops.governed_idea_backlog.v1",
        "examined_idea_count": 3,
        "records": [*generated, *rejected_ideas],
        "ranking_policy": "authority_then_contribution; no performance score",
        "ranked_assignable_idea_ids": [generated_id],
    }
    brief_id = "editorial_brief_" + _digest(generated[0])[:24]
    briefs = [{
        "brief_id": brief_id,
        "idea_id": generated_id,
        "brief_type": "EVIDENCE_REFRESH_AND_RETROSPECTIVE_FOLLOW_UP",
        "research_question": "Do fresh official curve closes and governed auction/CPI evidence confirm or challenge the July 13 configuration?",
        "required_existing_claim_ids": list(claim_ids),
        "required_new_evidence": gap_report["gaps"][0]["required_new_authority"],
        "must_preserve": ["official-close timestamp boundary", "no cross-asset inference without separate claims", "not financial advice"],
        "can_draft_article": False,
        "can_publish": False,
        "can_dispatch": False,
    }]
    assignment = {
        "schema_version": "contentops.internal_assignment_replay.v1",
        "assignment_id": "internal_assignment_" + _digest({"brief": brief_id, "idea": generated_id})[:24],
        "idea_id": generated_id,
        "brief_id": brief_id,
        "assignment_status": "INTERNAL_RESEARCH_ASSIGNMENT_CREATED",
        "assignee_role": "operator_selected_researcher",
        "public_write_performed": False,
        "scheduler_mutated": False,
        "publication_authority_granted": False,
        "next_gate": "OPERATOR_REVIEW_AND_FRESH_STORY_SCOPED_EVIDENCE",
    }
    artifacts = {
        "retrospective": retrospective,
        "derivative_comparison": comparison,
        "coverage_gaps": gap_report,
        "generated_ideas": {"schema_version": "contentops.generated_ideas.v1", "records": generated},
        "rejected_ideas": {"schema_version": "contentops.rejected_ideas.v1", "records": rejected_ideas},
        "backlog": backlog,
        "briefs": {"schema_version": "contentops.editorial_briefs.v1", "records": briefs},
        "assignment": assignment,
    }
    artifact_hashes = {key: _digest(value) for key, value in artifacts.items()}
    run_manifest = {
        "schema_version": "contentops.real_content_idea_loop_manifest.v1",
        "task_label": REAL_LOOP_TASK_LABEL,
        "model_version": REAL_LOOP_MODEL_VERSION,
        "terminal_classification": REAL_LOOP_TERMINAL,
        "pinned_upstream": {"repository": PINNED_UPSTREAM_REPOSITORY, "branch": PINNED_UPSTREAM_BRANCH, "commit_sha": PINNED_UPSTREAM_COMMIT, "pool_artifact_sha256": "e4f60146f9e870e5cc87bf30caa3ec51a930e3442458b95a42cdb5863b6bff5c"},
        "artifact_hashes": artifact_hashes,
        "real_article_body_read": True,
        "real_article_export_hash_matches_manifest": article_export_hash_matches_manifest,
        "real_native_payloads_read": True,
        "examined_idea_count": 3,
        "internal_assignment_count": 1,
        "metric_values_available": False,
        "performance_claim_made": False,
        "public_write_performed": False,
        "upstream_repository_mutated": False,
        "task_4_started": False,
    }
    artifacts["manifest"] = run_manifest
    return artifacts


def write_real_content_idea_loop_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / REAL_LOOP_REL_DIR).resolve()
    output = allowed if output_dir is None else Path(output_dir).resolve()
    if output != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_real_content_idea_loop")
    artifacts = build_real_content_idea_loop(root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, filename in REAL_LOOP_FILENAMES.items():
        path = output / filename
        path.write_text(json.dumps(artifacts[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        paths[key] = str(path)
    return {"artifacts": artifacts, "paths": paths}


# Adaptive newsroom learning loop.  Task 3 artifacts are accepted as an
# internal retrospective/idea baseline, but their stale article export is never
# accepted as the content body for learning.  Final public readback is the only
# body authority for the Treasury release.
ADAPTIVE_TASK_LABEL = "TASK_CONTENTOPS_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1"
ADAPTIVE_MODEL_VERSION = "contentops.adaptive_newsroom_learning_loop.v1"
ADAPTIVE_TERMINAL = "PASS_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1_AWAITING_CHATGPT_AUDIT"
ADAPTIVE_NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1"
ADAPTIVE_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1"
TASK3_REL_DIR = REAL_LOOP_REL_DIR
UPSTREAM_POOL_ARTIFACT_PATH = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
UPSTREAM_POOL_COMMIT = "9bff5453a118486740ccc8957fcabd3c139fb3d2"
UPSTREAM_POOL_BLOB_SHA1 = "e4f60146e26d5f52dec91f92a345e81d0fb1cc8d"
UPSTREAM_POOL_FILE_SHA256 = "a92cdff58c6f4ecc5b68e774d2a6e7ed94db346f47ae636337510c1e37b192be"
UPSTREAM_POOL_LOGICAL_HASH = "f385e6914bf6870bafd374906d9e708081297e0e6bd9a6a0c84b228f6f8f244b"
UPSTREAM_POOL_ID = "cc-newsroom-pool-f385e6914bf6870bafd3"
TREASURY_CANONICAL_SLUG = "treasury-yield-curve-edges-wider"
TREASURY_CANONICAL_URL = "https://capitalchronicle.substack.com/p/treasury-yield-curve-edges-wider"
TREASURY_STALE_ARTICLE_EXPORT_SHA256 = "0f4e8fe6c6e6ba6999082c5f7663aa6d1414d9ecd1a0e2900c61618999981b95"
TREASURY_STALE_DECLARED_EXPORT_SHA256 = "3379415581f7cdf00aefb0afb2aa5815906abbaf8871f473e681dfc15f97152f"
TREASURY_HISTORICAL_MANIFEST_BODY_SHA256 = "bf4376efc326d0702772244eceb1744cf037cdfa9801973ddc8d8d35a0c20f11"
TREASURY_PRE_FINAL_REPAIR_BODY_SHA256 = "d61ca814f953e39fdc10873cd4e05e561e1ca634d38a8f4f3029aeb16e1623ea"
TREASURY_FINAL_ACCEPTED_BODY_SHA256 = "05b3520f1d6e4201d16e9daeac42992bde12e9f60a09f0e13bfeb95406788ecc"
LEARNING_OUTCOMES = (
    "material_update", "confirmation", "contradiction", "correction",
    "new_phase", "evergreen_refresh", "packaging_gap", "duplicate",
    "filler", "insufficient_authority",
)
ADAPTIVE_FORBIDDEN_EFFECTS = (
    "canonical_scheduler_policy", "canonical_editorial_policy", "factual_claims",
    "dqr", "permissions", "source_authority", "exact_proxy_context_labels",
    "risk_language", "citations", "automatic_assignment", "publication",
    "dispatch",
)
ADAPTIVE_FILENAMES = {
    "decision": "contentops_learning_decision_v1.json",
    "replay": "adaptive_newsroom_shadow_replay_v1.json",
    "manifest": "adaptive_newsroom_learning_loop_manifest_v1.json",
    "runbook": "adaptive_newsroom_learning_loop_v1.md",
}


@dataclass(frozen=True)
class ContentOpsLearningDecisionV1:
    schema_version: str
    learning_decision_id: str
    input_content_ids: tuple[str, ...]
    input_snapshot_ids: tuple[str, ...]
    input_gap_ids: tuple[str, ...]
    input_idea_ids: tuple[str, ...]
    cohort_definition: str
    sample_size: int
    distinct_content_count: int
    method_version: str
    feature_availability: dict[str, bool]
    feature_values: dict[str, Any]
    penalties: dict[str, float]
    ranking_reasons: tuple[str, ...]
    confidence: str
    detected_outcomes: tuple[str, ...]
    proposed_ranking_prior_changes: tuple[dict[str, Any], ...]
    proposed_publication_window_changes: tuple[dict[str, Any], ...]
    proposed_headline_changes: tuple[dict[str, Any], ...]
    proposed_visual_changes: tuple[dict[str, Any], ...]
    proposed_format_changes: tuple[dict[str, Any], ...]
    selected_brief_ids: tuple[str, ...]
    no_publication_decisions: tuple[dict[str, Any], ...]
    forbidden_effects_checked: tuple[str, ...]
    operator_state: str
    logical_hash: str
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]


def adaptive_safety_flags() -> dict[str, bool]:
    return {
        "shadow_mode": True,
        "operator_review_required": True,
        "learning_firewall_enforced": True,
        "final_public_body_authority_enforced": True,
        "metrics_unavailable_preserved_as_null": True,
        "network_performed": False,
        "browser_session_used": False,
        "credential_accessed": False,
        "live_metric_collection_performed": False,
        "scheduler_mutated": False,
        "editorial_policy_mutated": False,
        "claim_mutated": False,
        "dqr_mutated": False,
        "permission_mutated": False,
        "source_authority_mutated": False,
        "labels_mutated": False,
        "risk_language_mutated": False,
        "citations_mutated": False,
        "automatic_assignment_created": False,
        "public_interaction_performed": False,
        "publication_performed": False,
        "dispatch_performed": False,
        "upstream_repository_mutated": False,
    }


def normalize_treasury_learning_authority(
    repo_root: str | Path | None = None,
    *,
    observed_body_sha256: str | None = None,
) -> dict[str, Any]:
    """Return the one accepted Treasury learning body or fail closed.

    Historical/stale hashes remain inspectable lineage.  None means that the
    caller asks the committed final-readback authority to select the body; any
    explicit non-final hash is rejected rather than silently normalized.
    """
    root = _module_root() if repo_root is None else Path(repo_root).resolve()
    manifest = _read_json(root, MANIFEST_REL_PATH)
    readback_path = RELEASE_REL_DIR / "substack_browser_readback_v1.json"
    readback = _read_json(root, readback_path)
    run_evidence_text = _read_text(root, RELEASE_REL_DIR / "run_evidence_v1.json")
    article_sha = _normalized_sha256(_read_text(root, ARTICLE_REL_PATH))
    embedded_sha = _normalized_sha256(str(manifest.get("substack_body_markdown") or ""))
    if article_sha != TREASURY_STALE_ARTICLE_EXPORT_SHA256:
        raise ValueError("unexpected_treasury_article_export_lineage")
    if embedded_sha != TREASURY_HISTORICAL_MANIFEST_BODY_SHA256:
        raise ValueError("unexpected_treasury_historical_manifest_body_lineage")
    if str(readback.get("body_markdown_sha256") or "") != TREASURY_FINAL_ACCEPTED_BODY_SHA256:
        raise ValueError("final_treasury_public_readback_hash_mismatch")
    if TREASURY_PRE_FINAL_REPAIR_BODY_SHA256 not in run_evidence_text:
        raise ValueError("pre_final_repair_body_authority_missing")
    if TREASURY_FINAL_ACCEPTED_BODY_SHA256 not in run_evidence_text:
        raise ValueError("final_repair_body_authority_missing")
    if observed_body_sha256 is not None and observed_body_sha256 != TREASURY_FINAL_ACCEPTED_BODY_SHA256:
        raise ValueError("stale_treasury_body_rejected_for_learning")
    return {
        "canonical_slug": TREASURY_CANONICAL_SLUG,
        "canonical_url": TREASURY_CANONICAL_URL,
        "learning_body_sha256": TREASURY_FINAL_ACCEPTED_BODY_SHA256,
        "learning_body_status": "FINAL_ACCEPTED_PUBLIC_BODY",
        "stale_article_export": {
            "actual_sha256": article_sha,
            "declared_sha256": str(manifest.get("article_markdown_sha256") or ""),
            "accepted_for_learning": False,
        },
        "historical_embedded_manifest_body": {
            "sha256": embedded_sha,
            "accepted_for_learning": False,
        },
        "pre_final_repair_public_body": {
            "sha256": TREASURY_PRE_FINAL_REPAIR_BODY_SHA256,
            "accepted_for_learning": False,
        },
        "final_public_body": {
            "sha256": TREASURY_FINAL_ACCEPTED_BODY_SHA256,
            "accepted_for_learning": True,
            "readback_status": readback.get("status"),
        },
        "stale_body_fallback_allowed": False,
        "evidence_refs": [
            ARTICLE_REL_PATH.as_posix(),
            MANIFEST_REL_PATH.as_posix(),
            (RELEASE_REL_DIR / "run_evidence_v1.json").as_posix(),
            readback_path.as_posix(),
        ],
    }


def _latest_pool_binding(pool: dict[str, Any]) -> dict[str, Any]:
    if pool.get("logical_hash") != UPSTREAM_POOL_LOGICAL_HASH:
        raise ValueError("latest_upstream_pool_logical_hash_mismatch")
    if pool.get("pool_id") != UPSTREAM_POOL_ID:
        raise ValueError("latest_upstream_pool_id_mismatch")
    counts = pool.get("counts", {})
    if counts != {"clusters": 3, "eligible": 1, "inputs": 3, "rejected": 2}:
        raise ValueError("latest_upstream_pool_count_mismatch")
    return {
        "repository": PINNED_UPSTREAM_REPOSITORY,
        "branch": PINNED_UPSTREAM_BRANCH,
        "commit_sha": UPSTREAM_POOL_COMMIT,
        "artifact_path": UPSTREAM_POOL_ARTIFACT_PATH,
        "git_blob_sha1": UPSTREAM_POOL_BLOB_SHA1,
        "file_sha256": UPSTREAM_POOL_FILE_SHA256,
        "pool_id": pool["pool_id"],
        "pool_logical_hash": pool["logical_hash"],
        "producer_version": pool.get("producer_version"),
        "status": pool.get("status"),
        "read_only": True,
    }


def classify_adaptive_outcomes(
    candidate: dict[str, Any],
    *,
    published_candidate_ids: set[str],
    published_cluster_ids: set[str],
    packaging_gap_present: bool,
) -> dict[str, bool]:
    """Classify all governed Task 4 outcomes without inventing authority."""
    candidate_id = str(candidate.get("candidate_id") or "")
    cluster_id = str(candidate.get("cluster_id") or "")
    relationship = str(candidate.get("relationship") or "").lower()
    permissions = candidate.get("claim_permissions", {})
    authorized = bool(
        candidate.get("eligible") is True
        and permissions.get("reporting_allowed") is True
        and not candidate.get("blockers")
    )
    duplicate = candidate_id in published_candidate_ids or cluster_id in published_cluster_ids
    material_update = authorized and relationship == "material_update" and not duplicate
    confirmation = authorized and relationship == "confirmation" and not duplicate
    contradiction = authorized and relationship == "contradiction" and not duplicate
    correction = authorized and relationship == "correction" and not duplicate
    new_phase = relationship == "new_phase"
    evergreen_refresh = duplicate and packaging_gap_present
    filler = authorized and duplicate and not packaging_gap_present
    return {
        "material_update": material_update,
        "confirmation": confirmation,
        "contradiction": contradiction,
        "correction": correction,
        "new_phase": new_phase,
        "evergreen_refresh": evergreen_refresh,
        "packaging_gap": packaging_gap_present and duplicate,
        "duplicate": duplicate,
        "filler": filler,
        "insufficient_authority": not authorized,
    }


def _candidate_shadow_record(
    candidate: dict[str, Any],
    outcomes: dict[str, bool],
    *,
    metric_available: bool,
    selected_brief_id: str | None,
) -> dict[str, Any]:
    freshness = candidate.get("freshness", {})
    age, maximum = freshness.get("age_hours"), freshness.get("max_age_hours")
    freshness_value = None
    if isinstance(age, (int, float)) and isinstance(maximum, (int, float)) and maximum > 0:
        freshness_value = round(max(0.0, 1.0 - float(age) / float(maximum)), 6)
    authority_value = 0.0 if outcomes["insufficient_authority"] else 1.0
    contribution_value = 0.45 if outcomes["packaging_gap"] else (0.1 if outcomes["insufficient_authority"] else 0.25)
    feature_values = {
        "authority": authority_value,
        "freshness": freshness_value,
        "distinct_contribution": contribution_value,
        "material_update": 1.0 if outcomes["material_update"] else 0.0,
        "packaging_gap": 1.0 if outcomes["packaging_gap"] else 0.0,
        "novelty": 0.0 if outcomes["duplicate"] else 0.5,
        "performance_metric": None,
    }
    penalties = {
        "duplicate": 60.0 if outcomes["duplicate"] else 0.0,
        "insufficient_authority": 100.0 if outcomes["insufficient_authority"] else 0.0,
        "filler": 25.0 if outcomes["filler"] else 0.0,
        "unavailable_metrics": 15.0 if not metric_available else 0.0,
    }
    score = max(0.0, round(
        100.0 * authority_value
        + 30.0 * contribution_value
        + 20.0 * feature_values["packaging_gap"]
        + 10.0 * feature_values["novelty"]
        - sum(penalties.values()),
        3,
    ))
    reasons = []
    if outcomes["packaging_gap"]:
        reasons.append("accepted Task 3 confirmation/limits packaging gap supports internal evidence refresh")
    if outcomes["duplicate"]:
        reasons.append("published candidate or cluster match blocks a new article")
    if outcomes["insufficient_authority"]:
        reasons.append("story-scoped reporting authority is absent")
    if not metric_available:
        reasons.append("performance metrics are unavailable; no performance prior is learned")
    if outcomes["new_phase"] and outcomes["duplicate"]:
        reasons.append("declared new_phase does not override exact published identity")
    return {
        "candidate_id": candidate.get("candidate_id"),
        "cluster_id": candidate.get("cluster_id"),
        "story_id": candidate.get("story_id"),
        "update_chain_id": candidate.get("update_chain_id"),
        "source_idea_id": candidate.get("source_idea_id"),
        "outcomes": outcomes,
        "feature_availability": {
            "authority": True,
            "freshness": freshness_value is not None,
            "distinct_contribution": True,
            "material_update": True,
            "packaging": True,
            "performance_metric": metric_available,
        },
        "feature_values": feature_values,
        "penalties": penalties,
        "shadow_score": score,
        "ranking_reasons": reasons,
        "selected_brief_id": selected_brief_id,
        "publication_selected": False,
    }


def build_learning_decision(
    *,
    input_content_ids: Sequence[str],
    input_snapshot_ids: Sequence[str],
    input_gap_ids: Sequence[str],
    input_idea_ids: Sequence[str],
    candidate_records: Sequence[dict[str, Any]],
    selected_brief_ids: Sequence[str],
    evidence_refs: Sequence[str],
) -> ContentOpsLearningDecisionV1:
    detected = tuple(name for name in LEARNING_OUTCOMES if any(record["outcomes"].get(name) for record in candidate_records))
    sample_size = len(input_snapshot_ids)
    metric_available = any(record["feature_availability"]["performance_metric"] for record in candidate_records)
    feature_availability = {
        "content_identity": bool(input_content_ids),
        "performance_snapshots": bool(input_snapshot_ids),
        "performance_metric_values": metric_available,
        "coverage_gaps": bool(input_gap_ids),
        "governed_ideas": bool(input_idea_ids),
        "candidate_authority": True,
        "derivative_packaging": True,
    }
    proposals = {
        "ranking": ({
            "proposal": "add evidence-refresh contribution as an operator-review shadow feature",
            "numeric_prior_delta": None,
            "reason": "Task 3 found a real confirmation gap, but no performance value exists.",
        },),
        "window": ({
            "proposal": "retain existing publication-window priors",
            "numeric_prior_delta": None,
            "reason": "No comparable timing metrics are available.",
        },),
        "headline": ({
            "proposal": "review confirm-or-challenge framing after fresh authority exists",
            "automatic_change": False,
        },),
        "visual": ({
            "proposal": "review an exact-official before/after curve comparison",
            "automatic_change": False,
        },),
        "format": ({
            "proposal": "preserve confirmation conditions and limits in ordered platform payloads",
            "automatic_change": False,
        },),
    }
    no_publication = tuple({
        "candidate_id": record["candidate_id"],
        "decision": "NO_PUBLICATION",
        "reasons": record["ranking_reasons"],
    } for record in candidate_records)
    combined_penalties = {
        name: round(sum(float(record["penalties"].get(name, 0.0)) for record in candidate_records), 3)
        for name in ("duplicate", "insufficient_authority", "filler", "unavailable_metrics")
    }
    ranking_reasons = _unique(tuple(reason for record in candidate_records for reason in record["ranking_reasons"]))
    draft = {
        "schema_version": "contentops.learning_decision.v1",
        "input_content_ids": _unique(input_content_ids),
        "input_snapshot_ids": _unique(input_snapshot_ids),
        "input_gap_ids": _unique(input_gap_ids),
        "input_idea_ids": _unique(input_idea_ids),
        "cohort_definition": "accepted final Treasury publication, nine unavailable-metric destination snapshots, Task 3 gaps, and the latest three-candidate governed upstream pool",
        "sample_size": sample_size,
        "distinct_content_count": len(set(input_content_ids)),
        "method_version": ADAPTIVE_MODEL_VERSION,
        "feature_availability": feature_availability,
        "feature_values": {record["candidate_id"]: record["feature_values"] for record in candidate_records},
        "penalties": combined_penalties,
        "ranking_reasons": ranking_reasons,
        "confidence": "BOUNDED_CONTENT_AND_AUTHORITY_ONLY_NO_PERFORMANCE_METRICS",
        "detected_outcomes": detected,
        "proposed_ranking_prior_changes": proposals["ranking"],
        "proposed_publication_window_changes": proposals["window"],
        "proposed_headline_changes": proposals["headline"],
        "proposed_visual_changes": proposals["visual"],
        "proposed_format_changes": proposals["format"],
        "selected_brief_ids": _unique(selected_brief_ids),
        "no_publication_decisions": no_publication,
        "forbidden_effects_checked": ADAPTIVE_FORBIDDEN_EFFECTS,
        "operator_state": "OPERATOR_REVIEW_REQUIRED_SHADOW_ONLY",
        "evidence_refs": _unique(evidence_refs),
        "safety_flags": adaptive_safety_flags(),
    }
    logical_hash = _digest(draft)
    return ContentOpsLearningDecisionV1(
        learning_decision_id="learning_decision_" + logical_hash[:24],
        logical_hash=logical_hash,
        **draft,
    )


def build_adaptive_newsroom_learning_loop(
    repo_root: str | Path | None = None,
    *,
    candidate_pool: dict[str, Any] | None = None,
    observed_treasury_body_sha256: str | None = None,
) -> dict[str, Any]:
    """Run a deterministic, reusable shadow loop with no policy mutation."""
    root = _module_root() if repo_root is None else Path(repo_root).resolve()
    authority = normalize_treasury_learning_authority(
        root, observed_body_sha256=observed_treasury_body_sha256
    )
    pool = candidate_pool if candidate_pool is not None else _read_json(root, POOL_REL_PATH)
    upstream_binding = _latest_pool_binding(pool)
    performance_packet = build_contract_packet(root)
    gap_packet = _read_json(root, TASK3_REL_DIR / REAL_LOOP_FILENAMES["coverage_gaps"])
    idea_packet = _read_json(root, TASK3_REL_DIR / REAL_LOOP_FILENAMES["generated_ideas"])
    brief_packet = _read_json(root, TASK3_REL_DIR / REAL_LOOP_FILENAMES["briefs"])
    comparison = _read_json(root, TASK3_REL_DIR / REAL_LOOP_FILENAMES["derivative_comparison"])
    gaps = list(gap_packet.get("gaps", []))
    ideas = list(idea_packet.get("records", []))
    briefs = list(brief_packet.get("records", []))
    if len(gaps) != 2 or len(ideas) != 1 or len(briefs) != 1:
        raise ValueError("accepted_task3_baseline_shape_mismatch")
    if comparison.get("metric_status") != COLLECTION_UNAVAILABLE:
        raise ValueError("unexpected_task3_metric_authority")
    packaging_gap_present = any(gap.get("mechanism") == "derivative_content_depth" for gap in gaps)
    published_ids = {str(performance_packet.source_bindings["candidate_id"])}
    published_clusters = {str(performance_packet.source_bindings["cluster_id"])}
    candidates = [*pool.get("eligible_candidates", []), *pool.get("rejected_candidates", [])]
    if len(candidates) != 3:
        raise ValueError("adaptive_shadow_loop_requires_three_governed_candidates")
    source_idea_id = str(ideas[0]["idea_id"])
    selected_brief_id = str(briefs[0]["brief_id"])
    records = []
    for candidate in candidates:
        copied = dict(candidate)
        if str(candidate.get("candidate_id")) in published_ids:
            copied["source_idea_id"] = source_idea_id
        outcomes = classify_adaptive_outcomes(
            copied,
            published_candidate_ids=published_ids,
            published_cluster_ids=published_clusters,
            packaging_gap_present=packaging_gap_present,
        )
        records.append(_candidate_shadow_record(
            copied,
            outcomes,
            metric_available=False,
            selected_brief_id=selected_brief_id if outcomes["evergreen_refresh"] else None,
        ))
    records.sort(key=lambda record: (-record["shadow_score"], str(record["candidate_id"])))
    for rank, record in enumerate(records, start=1):
        record["shadow_rank"] = rank
    refs = [
        *authority["evidence_refs"],
        POOL_REL_PATH.as_posix(),
        (TASK3_REL_DIR / REAL_LOOP_FILENAMES["coverage_gaps"]).as_posix(),
        (TASK3_REL_DIR / REAL_LOOP_FILENAMES["generated_ideas"]).as_posix(),
        (TASK3_REL_DIR / REAL_LOOP_FILENAMES["briefs"]).as_posix(),
        (TASK3_REL_DIR / REAL_LOOP_FILENAMES["derivative_comparison"]).as_posix(),
        f"{PINNED_UPSTREAM_REPOSITORY}@{UPSTREAM_POOL_COMMIT}:{UPSTREAM_POOL_ARTIFACT_PATH}",
    ]
    decision = build_learning_decision(
        input_content_ids=("contentops-v1-0-treasury-publication-20260714",),
        input_snapshot_ids=tuple(snapshot.snapshot_id for snapshot in performance_packet.snapshots),
        input_gap_ids=tuple(str(gap["gap_id"]) for gap in gaps),
        input_idea_ids=(source_idea_id,),
        candidate_records=records,
        selected_brief_ids=(selected_brief_id,),
        evidence_refs=refs,
    )
    outcome_matrix = [{
        "outcome": name,
        "detected": any(record["outcomes"][name] for record in records),
        "candidate_ids": [record["candidate_id"] for record in records if record["outcomes"][name]],
    } for name in LEARNING_OUTCOMES]
    replay = {
        "schema_version": "contentops.adaptive_newsroom_shadow_replay.v1",
        "task_label": ADAPTIVE_TASK_LABEL,
        "model_version": ADAPTIVE_MODEL_VERSION,
        "treasury_authority": authority,
        "upstream_candidate_pool_binding": upstream_binding,
        "accepted_task3_baseline": {
            "status": "ACCEPTED_INTERNAL_ONLY_RETROSPECTIVE_IDEA_ASSIGNMENT_BASELINE",
            "gap_ids": [gap["gap_id"] for gap in gaps],
            "idea_ids": [source_idea_id],
            "brief_ids": [selected_brief_id],
            "stale_article_body_reused": False,
        },
        "metric_state": {
            "snapshot_count": len(performance_packet.snapshots),
            "available_metric_value_count": sum(snapshot.metric_value is not None for snapshot in performance_packet.snapshots),
            "status": COLLECTION_UNAVAILABLE,
            "null_means_zero": False,
        },
        "derivative_packaging": {
            "comparison_id": comparison.get("comparison_id"),
            "row_count": len(comparison.get("rows", [])),
            "comparison_basis": comparison.get("comparison_basis"),
            "performance_basis_used": False,
        },
        "outcome_detection_matrix": outcome_matrix,
        "candidate_records": records,
        "selected_brief_ids": [selected_brief_id],
        "publication_decisions": [
            {"candidate_id": record["candidate_id"], "decision": "NO_PUBLICATION"}
            for record in records
        ],
        "canonical_scheduler_mutated": False,
        "canonical_editorial_policy_mutated": False,
        "operator_review_required": True,
        "safety_flags": adaptive_safety_flags(),
    }
    decision_dict = _asdict(decision)
    artifact_hashes = {
        "decision": _digest(decision_dict),
        "replay": _digest(replay),
    }
    manifest = {
        "schema_version": "contentops.adaptive_newsroom_learning_loop_manifest.v1",
        "task_label": ADAPTIVE_TASK_LABEL,
        "model_version": ADAPTIVE_MODEL_VERSION,
        "terminal_classification": ADAPTIVE_TERMINAL,
        "next_action": ADAPTIVE_NEXT_ACTION,
        "learning_decision_id": decision.learning_decision_id,
        "learning_decision_logical_hash": decision.logical_hash,
        "artifact_hashes": artifact_hashes,
        "upstream_candidate_pool_binding": upstream_binding,
        "final_public_body_sha256": TREASURY_FINAL_ACCEPTED_BODY_SHA256,
        "stale_body_learning_blocked": True,
        "candidate_count": len(records),
        "selected_brief_count": len(decision.selected_brief_ids),
        "publication_count": 0,
        "policy_mutation_count": 0,
        "safety_flags": adaptive_safety_flags(),
    }
    return {"decision": decision_dict, "replay": replay, "manifest": manifest}


def render_adaptive_runbook(artifacts: dict[str, Any]) -> str:
    manifest, decision = artifacts["manifest"], artifacts["decision"]
    return "\n".join((
        "# ContentOps Adaptive Newsroom Learning Loop V1",
        "",
        f"- terminal_classification: `{manifest['terminal_classification']}`",
        f"- learning_decision_id: `{decision['learning_decision_id']}`",
        f"- logical_hash: `{decision['logical_hash']}`",
        f"- next_action: `{manifest['next_action']}`",
        "",
        "## Authority normalization",
        "",
        f"- Canonical URL: `{TREASURY_CANONICAL_URL}`.",
        f"- Final accepted learning body: `{TREASURY_FINAL_ACCEPTED_BODY_SHA256}`.",
        "- The article export, historical embedded manifest body, and pre-final-repair body are explicit stale lineage and are never learning inputs.",
        "",
        "## Shadow decision",
        "",
        "- The replay consumes one accepted content identity, nine unavailable-metric snapshots, two Task 3 gaps, one governed idea, one internal brief, and three pinned upstream candidates.",
        "- Feature values, penalties, ranking reasons, outcome detections, selected briefs, and no-publication decisions are inspectable.",
        "- No performance winner, timing prior, or causal packaging effect is claimed.",
        "",
        "## Feedback firewall",
        "",
        "- All proposals are operator-review hypotheses only.",
        "- Scheduler/editorial policy, facts, DQR, permissions, authority, labels, risk language, citations, publication, and dispatch remain unchanged.",
        "",
    ))


def write_adaptive_newsroom_learning_artifacts(
    repo_root: str | Path = ".",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / ADAPTIVE_REL_DIR).resolve()
    output = allowed if output_dir is None else Path(output_dir).resolve()
    if output != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_adaptive_newsroom_learning_loop")
    artifacts = build_adaptive_newsroom_learning_loop(root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key in ("decision", "replay", "manifest"):
        path = output / ADAPTIVE_FILENAMES[key]
        path.write_text(
            json.dumps(artifacts[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        paths[key] = str(path)
    runbook_path = output / ADAPTIVE_FILENAMES["runbook"]
    runbook_path.write_text(render_adaptive_runbook(artifacts), encoding="utf-8", newline="\n")
    paths["runbook"] = str(runbook_path)
    return {"artifacts": artifacts, "paths": paths}


def main() -> int:
    result = write_adaptive_newsroom_learning_artifacts(_module_root())
    print(json.dumps({"terminal_classification": result["artifacts"]["manifest"]["terminal_classification"], "paths": result["paths"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
