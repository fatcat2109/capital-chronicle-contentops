"""Deterministic read-only ContentOps performance-learning contract."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Sequence
from live_contentops import manual_publish_record_metrics_ledger_contract as ledger

TASK_LABEL = "TASK_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_V1"
MODEL_VERSION = "contentops.performance_learning.v1"
DOC_REL_DIR = Path("docs") / "automation" / "CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_V1"
PACKET_FILENAME = "contentops_performance_learning_v1_packet.json"
RUNBOOK_FILENAME = "contentops_performance_learning_v1.md"
AUTHORITY_MANUAL_OPERATOR_ENTRY = "manual_operator_entry"
COLLECTION_OPERATOR_ATTESTED_MANUAL_ENTRY = "operator_attested_manual_entry"
COLLECTION_RECORDED_REVIEW_ONLY = "recorded_review_only"
RETROSPECTIVE_INCONCLUSIVE = "INCONCLUSIVE_INSUFFICIENT_COHORT"
RETROSPECTIVE_DESCRIPTIVE = "DESCRIPTIVE_REVIEW_ONLY"
OPERATOR_REVIEW_REQUIRED = "OPERATOR_REVIEW_REQUIRED"
MINIMUM_DISTINCT_IDENTITIES = 3
FORBIDDEN_LEARNING_EFFECTS = ("claim_values", "source_authority", "public_use_permissions", "dqr", "exact_proxy_context_labels", "factual_conclusions", "risk_language", "citation_requirements", "scheduler_scores", "writer_guidance", "platform_defaults", "editorial_artifact_mutation")

@dataclass(frozen=True)
class ContentOpsContentIdentityV1:
    identity_id: str; evidence_packet_id: str; evidence_packet_schema_version: str; story_cluster_id: str; candidate_id: str; assignment_decision_id: str; content_item_id: str; article_version_id: str; headline_variant_id: str; visual_bundle_id: str; platform_variant_id: str; platform_id: str; publication_window_id: str; experiment_id: str; canonical_url_hash: str; platform_post_id_hash: str; platform_url_hash: str; identity_status: str; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ContentOpsPerformanceSnapshotV1:
    snapshot_id: str; content_identity_id: str; content_item_id: str; platform_variant_id: str; platform_id: str; platform_post_id_hash: str; collected_at_epoch: int; observed_at_epoch: int; age_since_publication_seconds: int; metric_name: str; metric_value: float; metric_definition: str; metric_scope: str; denominator: str | None; authority_class: str; collection_method: str; collection_status: str; known_limitations: tuple[str, ...]; source_response_hash: str; source_manual_publish_record_id: str; source_manual_metrics_record_id: str; source_payload_hash: str; operator_attested: bool; api_verified: bool; scraped: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ContentOpsContentRetrospectiveV1:
    retrospective_id: str; input_snapshot_ids: tuple[str, ...]; cohort_definition: str; platform_id: str; sample_size: int; distinct_content_identity_count: int; method_version: str; retrospective_status: str; confidence_class: str; summary: str; recommended_learning_action: str; known_limitations: tuple[str, ...]; forbidden_effects_checked: tuple[str, ...]; operator_status: str; can_update_scheduler: bool; can_update_writer_guidance: bool; can_update_platform_defaults: bool; can_auto_generate_content: bool; can_auto_publish: bool; can_dispatch: bool; public_postable: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ContentOpsIdeaCandidateV1:
    idea_candidate_id: str; source_retrospective_id: str; source_snapshot_ids: tuple[str, ...]; candidate_type: str; hypothesis: str; recommended_observation_action: str; confidence_class: str; required_human_review: bool; operator_status: str; can_create_editorial_brief: bool; can_auto_generate_content: bool; can_update_scheduler: bool; can_update_writer_guidance: bool; can_update_platform_defaults: bool; can_auto_publish: bool; can_dispatch: bool; public_postable: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]

@dataclass(frozen=True)
class PerformanceLearningPacketV1:
    packet_id: str; identities: tuple[ContentOpsContentIdentityV1, ...]; snapshots: tuple[ContentOpsPerformanceSnapshotV1, ...]; retrospectives: tuple[ContentOpsContentRetrospectiveV1, ...]; idea_candidates: tuple[ContentOpsIdeaCandidateV1, ...]; packet_hash: str; packet_hash_algorithm: str; all_records_manual_only: bool; all_learning_review_only: bool; no_collection_performed: bool; no_api_verification: bool; no_scraping: bool; no_automatic_editorial_mutation: bool; no_auto_publish: bool; no_dispatch: bool; no_public_claim_authorized: bool; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]; next_required_gate: str

def _asdict(v: Any) -> Any:
    if hasattr(v, "__dataclass_fields__"): return asdict(v)
    if isinstance(v, tuple): return [_asdict(x) for x in v]
    if isinstance(v, list): return [_asdict(x) for x in v]
    if isinstance(v, dict): return {str(k): _asdict(x) for k, x in v.items()}
    return v

def _json(v: Any) -> str: return json.dumps(_asdict(v), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
def _digest(v: Any) -> str: return sha256(_json(v).encode("utf-8")).hexdigest()
def _hash(v: str) -> str: return sha256(str(v).encode("utf-8")).hexdigest()
def _unique(v: Sequence[Any]) -> tuple[str, ...]: return tuple(dict.fromkeys(str(x) for x in v if x not in (None, "")))
def _missing(**v: str) -> tuple[str, ...]: return tuple(f"missing_{k}" for k, x in v.items() if not str(x or "").strip())

def safety_flags() -> dict[str, bool]:
    disabled = ("platform_api_called", "provider_api_called", "metrics_api_verified", "metrics_scraped", "credential_hydrated", "env_read", "network_performed", "browser_session_used", "scheduler_enabled", "scheduler_mutated", "llm_provider_called", "scraping_performed", "automatic_editorial_mutation", "can_auto_generate_content", "can_auto_publish", "can_dispatch", "public_postable", "public_claim_authorized", "dqr_cleared", "publication_authority_granted", "ingestion_repo_mutated")
    return {**{x: False for x in disabled}, "manual_metrics_only": True, "operator_attested_only": True, "append_only": True, "human_review_required": True, "learning_firewall_enforced": True}

def build_content_identity(*, evidence_packet_id: str, story_cluster_id: str, candidate_id: str, assignment_decision_id: str, content_item_id: str, article_version_id: str, headline_variant_id: str, visual_bundle_id: str, platform_variant_id: str, platform_id: str, publication_window_id: str, experiment_id: str, canonical_url_reference: str, platform_post_reference: str, platform_url_reference: str, evidence_refs: tuple[str, ...] = ()) -> ContentOpsContentIdentityV1:
    b = _missing(evidence_packet_id=evidence_packet_id, story_cluster_id=story_cluster_id, candidate_id=candidate_id, assignment_decision_id=assignment_decision_id, content_item_id=content_item_id, article_version_id=article_version_id, headline_variant_id=headline_variant_id, visual_bundle_id=visual_bundle_id, platform_variant_id=platform_variant_id, platform_id=platform_id, publication_window_id=publication_window_id, experiment_id=experiment_id, canonical_url_reference=canonical_url_reference, platform_post_reference=platform_post_reference, platform_url_reference=platform_url_reference)
    m = {"packet": evidence_packet_id, "cluster": story_cluster_id, "candidate": candidate_id, "assignment": assignment_decision_id, "content": content_item_id, "article": article_version_id, "headline": headline_variant_id, "visual": visual_bundle_id, "platform_variant": platform_variant_id, "platform": platform_id, "window": publication_window_id, "experiment": experiment_id, "canonical": _hash(canonical_url_reference), "post": _hash(platform_post_reference), "url": _hash(platform_url_reference), "blocked": b}
    return ContentOpsContentIdentityV1("content_identity_"+_digest(m)[:24], evidence_packet_id, "capital_chronicle_content_evidence_packet.v2", story_cluster_id, candidate_id, assignment_decision_id, content_item_id, article_version_id, headline_variant_id, visual_bundle_id, platform_variant_id, platform_id, publication_window_id, experiment_id, m["canonical"], m["post"], m["url"], "VALID" if not b else "BLOCKED", _unique((*evidence_refs, "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/capital_chronicle_content_evidence_packet_v2.schema.json")), safety_flags(), b)

def _snapshot_blockers(identity: ContentOpsContentIdentityV1, publish: ledger.ManualPublishRecord, metrics: ledger.ManualMetricsRecord, metric_name: str) -> tuple[str, ...]:
    b = list(_missing(identity_id=identity.identity_id, metric_name=metric_name, manual_publish_record_id=publish.manual_publish_record_id, manual_metrics_record_id=metrics.manual_metrics_record_id, source_payload_hash=publish.source_payload_hash))
    if identity.identity_status != "VALID": b.append("content_identity_invalid")
    if identity.platform_id != publish.platform_id: b.append("identity_publish_platform_mismatch")
    if metrics.source_manual_publish_record_id != publish.manual_publish_record_id: b.append("manual_metrics_publish_record_mismatch")
    if metrics.source_payload_hash != publish.source_payload_hash: b.append("manual_metrics_payload_hash_mismatch")
    if metrics.platform_id != publish.platform_id: b.append("manual_metrics_platform_mismatch")
    if metrics.metric_values_are_operator_attested is not True: b.append("manual_metric_not_operator_attested")
    if metrics.metric_values_are_api_verified is not False: b.append("api_verified_metric_rejected")
    if metrics.metric_values_are_scraped is not False: b.append("scraped_metric_rejected")
    if metrics.metric_source_class not in {ledger.METRIC_SOURCE_OPERATOR, ledger.METRIC_SOURCE_PLATFORM_UI}: b.append("unsupported_manual_metric_source_class")
    if metrics.metric_observed_at_epoch < publish.manually_published_at_epoch: b.append("metric_observed_before_publication")
    if metrics.metric_recorded_at_epoch < metrics.metric_observed_at_epoch: b.append("metric_recorded_before_observation")
    return _unique(b)

def build_performance_snapshot(*, identity: ContentOpsContentIdentityV1, publish_record: ledger.ManualPublishRecord, metrics_record: ledger.ManualMetricsRecord, metric_name: str, metric_definition: str, metric_scope: str, denominator: str | None = None, known_limitations: tuple[str, ...] = ()) -> ContentOpsPerformanceSnapshotV1:
    b = list(_snapshot_blockers(identity, publish_record, metrics_record, metric_name)); value = metrics_record.metrics.get(metric_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0: b.append("metric_value_invalid"); value = 0.0
    age = metrics_record.metric_observed_at_epoch - publish_record.manually_published_at_epoch
    if age < 0: b.append("metric_age_invalid"); age = 0
    b = _unique(b); m = {"identity": identity.identity_id, "publish": publish_record.manual_publish_record_id, "metrics": metrics_record.manual_metrics_record_id, "metric": metric_name, "value": value, "observed": metrics_record.metric_observed_at_epoch, "collected": metrics_record.metric_recorded_at_epoch, "blocked": b}
    return ContentOpsPerformanceSnapshotV1("performance_snapshot_"+_digest(m)[:24], identity.identity_id, identity.content_item_id, identity.platform_variant_id, identity.platform_id, identity.platform_post_id_hash, metrics_record.metric_recorded_at_epoch, metrics_record.metric_observed_at_epoch, age, metric_name, float(value), metric_definition, metric_scope, denominator, AUTHORITY_MANUAL_OPERATOR_ENTRY, COLLECTION_OPERATOR_ATTESTED_MANUAL_ENTRY, COLLECTION_RECORDED_REVIEW_ONLY if not b else "BLOCKED", _unique(("Operator-attested manual metric entry; not verified platform analytics.", "No API or scraper collection was performed.", *known_limitations)), metrics_record.metric_url_hash, publish_record.manual_publish_record_id, metrics_record.manual_metrics_record_id, publish_record.source_payload_hash, metrics_record.metric_values_are_operator_attested, metrics_record.metric_values_are_api_verified, metrics_record.metric_values_are_scraped, _unique((*identity.evidence_refs, *publish_record.evidence_refs, *metrics_record.evidence_refs)), safety_flags(), b)

def append_snapshot(existing_snapshots: Sequence[ContentOpsPerformanceSnapshotV1], snapshot: ContentOpsPerformanceSnapshotV1) -> tuple[ContentOpsPerformanceSnapshotV1, ...]:
    for old in existing_snapshots:
        if old.snapshot_id == snapshot.snapshot_id:
            if _json(old) != _json(snapshot): raise ValueError("append_only_snapshot_collision")
            return tuple(existing_snapshots)
    return (*existing_snapshots, snapshot)

def build_content_retrospective(snapshots: Sequence[ContentOpsPerformanceSnapshotV1], *, cohort_definition: str) -> ContentOpsContentRetrospectiveV1:
    b: list[str] = []; platforms = {s.platform_id for s in snapshots}
    if not snapshots: b.append("retrospective_requires_snapshots")
    if len(platforms) > 1: b.append("mixed_platform_cohort_rejected")
    if not str(cohort_definition or "").strip(): b.append("missing_cohort_definition")
    for s in snapshots:
        if s.collection_status != COLLECTION_RECORDED_REVIEW_ONLY: b.append("blocked_snapshot_in_cohort")
        if s.authority_class != AUTHORITY_MANUAL_OPERATOR_ENTRY: b.append("non_manual_authority_snapshot_rejected")
        if s.api_verified or s.scraped or not s.operator_attested: b.append("snapshot_manual_provenance_invalid")
    identities = len({s.content_identity_id for s in snapshots}); insufficient = identities < MINIMUM_DISTINCT_IDENTITIES
    status, confidence = (RETROSPECTIVE_INCONCLUSIVE, "insufficient_manual_sample") if insufficient else (RETROSPECTIVE_DESCRIPTIVE, "low_manual_descriptive")
    summary = "The governed cohort is too small for a comparative performance conclusion." if insufficient else "Manual observations are descriptive only; they do not establish platform truth or causal effect."
    action = "Collect operator-attested observations across at least three distinct content identities before evaluating a packaging hypothesis." if insufficient else "Present the bounded descriptive cohort to an operator for optional future-hypothesis review."
    b = _unique(b); m = {"snapshots": [s.snapshot_id for s in snapshots], "cohort": cohort_definition, "status": status, "blocked": b}; refs = _unique(tuple(ref for s in snapshots for ref in s.evidence_refs))
    return ContentOpsContentRetrospectiveV1("content_retrospective_"+_digest(m)[:24], tuple(s.snapshot_id for s in snapshots), cohort_definition, next(iter(platforms)) if len(platforms) == 1 else "unknown", len(snapshots), identities, MODEL_VERSION, "BLOCKED" if b else status, "blocked" if b else confidence, summary, "No action; resolve blocked input provenance." if b else action, ("Metrics are manual operator entries, not official platform analytics.", "The cohort is descriptive and may be confounded by topic, timing, and audience growth.", "No causal or public performance conclusion is permitted."), FORBIDDEN_LEARNING_EFFECTS, OPERATOR_REVIEW_REQUIRED, False, False, False, False, False, False, False, refs, safety_flags(), b)

def build_idea_candidate(retrospective: ContentOpsContentRetrospectiveV1) -> ContentOpsIdeaCandidateV1:
    b = list(retrospective.blocked_reasons)
    if retrospective.operator_status != OPERATOR_REVIEW_REQUIRED: b.append("operator_review_requirement_missing")
    if retrospective.forbidden_effects_checked != FORBIDDEN_LEARNING_EFFECTS: b.append("learning_firewall_check_incomplete")
    b = _unique(b)
    if retrospective.retrospective_status == RETROSPECTIVE_INCONCLUSIVE: kind, hypothesis = "observation_plan", "Collect more comparable manual observations before proposing any content packaging change."
    elif retrospective.retrospective_status == RETROSPECTIVE_DESCRIPTIVE: kind, hypothesis = "review_hypothesis", "An operator may review the descriptive cohort for a future, separately governed packaging hypothesis."
    else: kind, hypothesis = "blocked", "No learning candidate is available until source snapshot blockers are resolved."
    m = {"retrospective": retrospective.retrospective_id, "kind": kind, "hypothesis": hypothesis, "blocked": b}
    return ContentOpsIdeaCandidateV1("performance_idea_candidate_"+_digest(m)[:24], retrospective.retrospective_id, retrospective.input_snapshot_ids, kind, hypothesis, retrospective.recommended_learning_action, "blocked" if b else retrospective.confidence_class, True, OPERATOR_REVIEW_REQUIRED, False, False, False, False, False, False, False, False, retrospective.evidence_refs, safety_flags(), b)

def build_contract_packet() -> PerformanceLearningPacketV1:
    prior = ledger.build_contract_packet(); publish, metrics = prior.manual_publish_records[0], prior.manual_metrics_records[0]
    identity = build_content_identity(evidence_packet_id="cc-evidence-fixture-v2", story_cluster_id="cluster-fixture-performance-v1", candidate_id="candidate-fixture-performance-v1", assignment_decision_id="assignment-fixture-performance-v1", content_item_id="content-fixture-performance-v1", article_version_id="article-v1-fixture-performance-v1", headline_variant_id="headline-v1-fixture-performance-v1", visual_bundle_id="visual-fixture-performance-v1", platform_variant_id="platform-variant-fixture-performance-v1", platform_id=publish.platform_id, publication_window_id="window-fixture-performance-v1", experiment_id="experiment-fixture-performance-v1", canonical_url_reference="https://capitalchronicle.example/canonical-fixture", platform_post_reference="platform-post-fixture", platform_url_reference="https://capitalchronicle.example/platform-fixture", evidence_refs=("docs/automation/0174UC/manual_publish_record_metrics_ledger_contract_packet.json",))
    snapshot = build_performance_snapshot(identity=identity, publish_record=publish, metrics_record=metrics, metric_name="impressions", metric_definition="Operator-recorded displayed impression count.", metric_scope="single manually recorded post observation", known_limitations=("Fixture only; it is not a live collection or performance claim.",))
    retrospective = build_content_retrospective((snapshot,), cohort_definition="fixture single-post manual-observation cohort"); idea = build_idea_candidate(retrospective)
    draft = {"identities": (identity,), "snapshots": (snapshot,), "retrospectives": (retrospective,), "idea_candidates": (idea,), "all_records_manual_only": True, "all_learning_review_only": True, "no_collection_performed": True, "no_api_verification": True, "no_scraping": True, "no_automatic_editorial_mutation": True, "no_auto_publish": True, "no_dispatch": True, "no_public_claim_authorized": True, "evidence_refs": _unique((*identity.evidence_refs, *snapshot.evidence_refs, *retrospective.evidence_refs, *idea.evidence_refs)), "safety_flags": safety_flags(), "blocked_reasons": (), "next_required_gate": "INDEPENDENT_AUDIT_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_V1"}
    h = _digest(draft); return PerformanceLearningPacketV1("performance_learning_packet_"+h[:24], packet_hash=h, packet_hash_algorithm="sha256", **draft)

def render_runbook(packet: PerformanceLearningPacketV1) -> str:
    return "\n".join(("# ContentOps Cross-Platform Performance Intelligence V1", "", f"- task_label: `{TASK_LABEL}`", f"- model_version: `{MODEL_VERSION}`", f"- packet_id: `{packet.packet_id}`", f"- packet_hash: `{packet.packet_hash}`", "", "## Scope", "", "- Deterministic local contract; not a platform performance collector.", "- Metrics remain operator-attested manual entries with explicit limitations.", "- Retrospectives are descriptive or inconclusive and preserve source snapshot IDs.", "- Idea candidates require operator review and cannot create a brief or dispatch.", "", "## Learning firewall", "", "- No claim, authority, permission, DQR, risk-language, citation, scheduler, writer-guidance, platform-default, or editorial-artifact effect is allowed.", "- No platform API, network, browser, environment, credential, scraper, scheduler, or LLM behavior exists in this module.", "", "## Next required gate", "", f"`{packet.next_required_gate}`", ""))

def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve(); allowed = (root / DOC_REL_DIR).resolve(); out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed: raise ValueError("artifact_writer_refuses_paths_outside_contentops_performance_learning_v1")
    out.mkdir(parents=True, exist_ok=True); packet = build_contract_packet(); p, r = out / PACKET_FILENAME, out / RUNBOOK_FILENAME
    p.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n"); r.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(p), "runbook_path": str(r)}
def contract_checksum() -> str: return build_contract_packet().packet_hash
