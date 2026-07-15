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
