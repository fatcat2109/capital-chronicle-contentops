"""Internal Alpha artifact intake + content eligibility contract, 0174U8.

Deterministic local-only review contract. No provider/API/network/env/credential,
no DQR/readiness/current-truth promotion, no approval, no dispatch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import capital_chronicle_ingestion_headline_idea_connector_precheck as u7

TASK_LABEL = "TASK_CONTENTOPS_0174U8_INTERNAL_ALPHA_ARTIFACT_INTAKE_AND_CONTENT_ELIGIBILITY_CONTRACT_V0"
MODEL_VERSION = "0174U8_INTERNAL_ALPHA_ARTIFACT_INTAKE_CONTENT_ELIGIBILITY_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "2dcf49901590f3c5dfd8648ef0e77c693a4ee0c2"
DOC_REL_DIR = Path("docs") / "automation" / "0174U8"
PACKET_FILENAME = "internal_alpha_artifact_intake_content_eligibility_contract_packet.json"
RUNBOOK_FILENAME = "internal_alpha_artifact_intake_content_eligibility_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U9_REDACTED_IMMUTABLE_AUDIT_LEDGER_V2_CONTRACT_V0"
HASH_ALGORITHM = "sha256"
ARTIFACT_FAMILIES = ("internal_alpha_report", "forecast_readiness_report", "dqr_summary", "data_sufficiency_summary", "source_registry_snapshot", "field_authority_map_snapshot", "headline_context_packet", "unknown_artifact")
ARTIFACT_ORIGINS = ("contentops_manual_import", "ingestion_connector_context", "future_capital_chronicle_export")
ELIGIBILITY_CLASSES = ("eligible_for_content_idea_only", "eligible_for_editorial_brief_candidate", "blocked_missing_citations", "blocked_missing_limitations", "blocked_readiness_not_ready", "blocked_dqr_unresolved", "blocked_freshness_unknown", "blocked_source_authority_unknown", "blocked_current_truth_risk", "blocked_advice_or_signal_risk", "blocked_unknown_artifact")
SAFETY_FALSE_FLAGS = ("internal_alpha_ready_declared", "dqr_cleared", "readiness_cleared", "current_truth_promoted", "public_claim_authorized", "approval_granted", "dispatch_ready", "public_postable", "live_dispatch_enabled", "llm_provider_called", "provider_api_called", "platform_api_called", "telegram_api_called", "credential_hydrated", "env_read", "network_performed", "scheduler_enabled", "autonomous_posting_allowed", "scraping_performed", "dm_or_reply_automation_allowed", "ingestion_repo_mutated")
ADVICE_SIGNAL_TERMS = ("buy", "sell", "hold", "price target", "trading signal", "signal", "entry point", "exit point", "guaranteed returns", "our model predicts", "financial advice", "recommendation")
READY_STATES = ("ready_for_review", "review_ready", "not_applicable_context_only")
DQR_ALLOWED_STATES = ("context_only_not_cleared", "not_applicable_context_only")
FRESHNESS_ALLOWED_STATES = ("fresh", "current_context", "not_applicable_context_only")
SOURCE_AUTHORITY_ALLOWED_STATES = ("known_context_source", "registered_context_source", "not_applicable_context_only")
CANDIDATE_FAMILY_MAP = {"internal_alpha_readiness_report": "internal_alpha_report", "forecast_readiness_summary": "forecast_readiness_report", "dqr_summary": "dqr_summary", "data_sufficiency_summary": "data_sufficiency_summary", "official_source_catalog": "source_registry_snapshot", "source_family_manifest": "source_registry_snapshot", "candidate_official_source_surface": "source_registry_snapshot", "headline_surface": "headline_context_packet", "freshness_manifest": "internal_alpha_report", "coverage_gap_report": "data_sufficiency_summary"}


@dataclass(frozen=True)
class InternalAlphaArtifactIntakePacket:
    artifact_intake_id: str; source_context_candidate_ids: tuple[str, ...]; artifact_ref: str; artifact_family: str; artifact_origin: str; artifact_hash: str; artifact_hash_algorithm: str; artifact_timestamp_epoch: int; source_repo_ref: str; source_relative_path: str; citation_refs: tuple[str, ...]; limitation_notes: tuple[str, ...]; declared_readiness_state: str; declared_dqr_state: str; declared_freshness_state: str; declared_source_authority_state: str; redaction_required: bool; human_review_required: bool; public_postable: bool; can_create_content_idea: bool; can_create_editorial_brief_candidate: bool; can_support_public_claim: bool; can_clear_dqr: bool; can_clear_readiness: bool; can_create_current_truth: bool; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]; evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ContentEligibilityAssessment:
    assessment_id: str; source_artifact_intake_id: str; artifact_family: str; artifact_hash_match: bool; required_citations_present: bool; limitations_present: bool; readiness_state_allowed: bool; dqr_state_allowed: bool; freshness_state_allowed: bool; source_authority_state_allowed: bool; no_current_truth_promotion: bool; no_dqr_clearance: bool; no_readiness_clearance: bool; no_advice_or_signal_risk: bool; redaction_ready: bool; human_review_required: bool; eligibility_class: str; blocked_reasons: tuple[str, ...]; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]


@dataclass(frozen=True)
class ArtifactBackedContentEligibilityReport:
    report_id: str; source_assessment_ids: tuple[str, ...]; eligible_content_idea_count: int; eligible_editorial_brief_candidate_count: int; blocked_artifact_count: int; content_lane: str; source_requirement_status: str; claim_risk_class: str; approved_for_content_idea: bool; approved_for_editorial_brief_candidate: bool; approved_for_public_claim: bool; approved_for_approval: bool; approved_for_dispatch: bool; readiness_summary: str; dqr_summary: str; freshness_summary: str; source_authority_summary: str; limitation_summary: str; citation_summary: str; blockers_summary: tuple[str, ...]; required_next_operator_actions: tuple[str, ...]; safety_flags: dict[str, bool]; evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactIdeaSeedPacket:
    artifact_idea_seed_id: str; source_report_id: str; source_artifact_intake_ids: tuple[str, ...]; topic_hint: str; context_summary: str; suggested_platform_targets: tuple[str, ...]; content_lane: str; source_requirement_status: str; claim_risk_class: str; required_citation_refs: tuple[str, ...]; required_limitation_notes: tuple[str, ...]; human_review_required: bool; public_postable: bool; can_create_content_idea: bool; can_create_editorial_brief_candidate: bool; can_create_approval: bool; can_dispatch: bool; blocked_reasons: tuple[str, ...]; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"): return asdict(value)
    if isinstance(value, tuple): return [_asdict(v) for v in value]
    if isinstance(value, dict): return {k: _asdict(v) for k, v in value.items()}
    return value


def safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def _has_advice_signal(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in ADVICE_SIGNAL_TERMS)


def _normalize_family(value: str) -> str:
    return value if value in ARTIFACT_FAMILIES else "unknown_artifact"


def _build_intake(*, source_ids: tuple[str, ...], artifact_ref: str, artifact_family: str, artifact_origin: str, artifact_timestamp_epoch: int = 0, source_repo_ref: str = "", source_relative_path: str = "", citation_refs: tuple[str, ...] = (), limitation_notes: tuple[str, ...] = (), declared_readiness_state: str = "not_ready", declared_dqr_state: str = "unresolved", declared_freshness_state: str = "unknown", declared_source_authority_state: str = "unknown", redaction_required: bool = True, evidence_refs: tuple[str, ...] = ()) -> InternalAlphaArtifactIntakePacket:
    family = _normalize_family(artifact_family)
    origin = artifact_origin if artifact_origin in ARTIFACT_ORIGINS else "contentops_manual_import"
    material = {"source_ids": source_ids, "artifact_ref": artifact_ref, "family": family, "origin": origin, "path": source_relative_path, "citations": citation_refs, "limitations": limitation_notes}
    h = _digest(material)
    blockers = []
    if family == "unknown_artifact": blockers.append("unknown_artifact_family")
    return InternalAlphaArtifactIntakePacket("internal_alpha_intake_" + h[:24], source_ids, artifact_ref, family, origin, h, HASH_ALGORITHM, artifact_timestamp_epoch, source_repo_ref, source_relative_path, citation_refs, limitation_notes, declared_readiness_state, declared_dqr_state, declared_freshness_state, declared_source_authority_state, redaction_required, True, False, family != "unknown_artifact", False, False, False, False, False, safety_flags(), tuple(blockers), evidence_refs or ((source_relative_path or artifact_ref),))


def build_intake_from_u7_candidate(candidate: u7.IngestionArtifactContextCandidate) -> InternalAlphaArtifactIntakePacket:
    family = CANDIDATE_FAMILY_MAP.get(candidate.candidate_class, "unknown_artifact")
    citations = tuple(candidate.evidence_refs)
    limits = ("U7 ingestion candidate is context-only.", "Cannot clear DQR/readiness/current truth.")
    return _build_intake(source_ids=(candidate.candidate_id,), artifact_ref=candidate.relative_path, artifact_family=family, artifact_origin="ingestion_connector_context", artifact_timestamp_epoch=candidate.modified_time_epoch, source_repo_ref=candidate.source_repo_path, source_relative_path=candidate.relative_path, citation_refs=citations, limitation_notes=limits, declared_readiness_state="not_applicable_context_only", declared_dqr_state="context_only_not_cleared", declared_freshness_state="not_applicable_context_only", declared_source_authority_state="known_context_source", redaction_required=True, evidence_refs=tuple(candidate.evidence_refs))


def build_intake_from_headline_context_packet(packet: u7.HeadlineIdeaContextPacket) -> InternalAlphaArtifactIntakePacket:
    return _build_intake(source_ids=tuple(packet.source_candidate_ids), artifact_ref=packet.headline_context_packet_id, artifact_family="headline_context_packet", artifact_origin="ingestion_connector_context", citation_refs=tuple(packet.citation_context_refs), limitation_notes=tuple(packet.limitation_notes), declared_readiness_state="not_applicable_context_only", declared_dqr_state="context_only_not_cleared", declared_freshness_state="not_applicable_context_only", declared_source_authority_state="known_context_source", redaction_required=True, evidence_refs=tuple(packet.evidence_refs))


def build_manual_artifact_intake_packet(metadata: dict[str, Any]) -> InternalAlphaArtifactIntakePacket:
    return _build_intake(source_ids=tuple(metadata.get("source_context_candidate_ids", ())), artifact_ref=str(metadata.get("artifact_ref", "manual_artifact")), artifact_family=str(metadata.get("artifact_family", "unknown_artifact")), artifact_origin=str(metadata.get("artifact_origin", "contentops_manual_import")), artifact_timestamp_epoch=int(metadata.get("artifact_timestamp_epoch", 0)), source_repo_ref=str(metadata.get("source_repo_ref", "manual")), source_relative_path=str(metadata.get("source_relative_path", "manual")), citation_refs=tuple(metadata.get("citation_refs", ())), limitation_notes=tuple(metadata.get("limitation_notes", ())), declared_readiness_state=str(metadata.get("declared_readiness_state", "not_ready")), declared_dqr_state=str(metadata.get("declared_dqr_state", "unresolved")), declared_freshness_state=str(metadata.get("declared_freshness_state", "unknown")), declared_source_authority_state=str(metadata.get("declared_source_authority_state", "unknown")), redaction_required=bool(metadata.get("redaction_required", True)), evidence_refs=tuple(metadata.get("evidence_refs", ())))


def assess_content_eligibility(intake: InternalAlphaArtifactIntakePacket, *, context_summary: str = "") -> ContentEligibilityAssessment:
    citations = bool(intake.citation_refs); limits = bool(intake.limitation_notes)
    ready = intake.declared_readiness_state in READY_STATES
    dqr = intake.declared_dqr_state in DQR_ALLOWED_STATES
    fresh = intake.declared_freshness_state in FRESHNESS_ALLOWED_STATES
    auth = intake.declared_source_authority_state in SOURCE_AUTHORITY_ALLOWED_STATES
    no_truth = not (intake.can_create_current_truth or intake.can_support_public_claim)
    no_dqr = not intake.can_clear_dqr; no_ready = not intake.can_clear_readiness
    no_signal = not _has_advice_signal(" ".join((context_summary, intake.artifact_ref, " ".join(intake.limitation_notes))))
    blockers: list[str] = list(intake.blocked_reasons)
    if intake.artifact_family == "unknown_artifact": blockers.append("blocked_unknown_artifact")
    if not citations: blockers.append("blocked_missing_citations")
    if not limits: blockers.append("blocked_missing_limitations")
    if not ready: blockers.append("blocked_readiness_not_ready")
    if not dqr: blockers.append("blocked_dqr_unresolved")
    if not fresh: blockers.append("blocked_freshness_unknown")
    if not auth: blockers.append("blocked_source_authority_unknown")
    if not no_truth: blockers.append("blocked_current_truth_risk")
    if not no_signal: blockers.append("blocked_advice_or_signal_risk")
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        eligibility = next((b for b in blockers if b in ELIGIBILITY_CLASSES), "blocked_unknown_artifact")
    elif intake.artifact_family in {"internal_alpha_report", "forecast_readiness_report", "dqr_summary", "data_sufficiency_summary", "source_registry_snapshot", "field_authority_map_snapshot"} and ready and dqr and fresh and auth:
        eligibility = "eligible_for_editorial_brief_candidate"
    else:
        eligibility = "eligible_for_content_idea_only"
    h = _digest({"intake": intake.artifact_intake_id, "eligibility": eligibility, "blockers": blockers})
    return ContentEligibilityAssessment("content_eligibility_" + h[:24], intake.artifact_intake_id, intake.artifact_family, intake.artifact_hash_algorithm == HASH_ALGORITHM and bool(intake.artifact_hash), citations, limits, ready, dqr, fresh, auth, no_truth, no_dqr, no_ready, no_signal, bool(intake.redaction_required), True, eligibility, tuple(blockers), intake.evidence_refs, safety_flags())


def build_artifact_backed_content_eligibility_report(assessments: tuple[ContentEligibilityAssessment, ...]) -> ArtifactBackedContentEligibilityReport:
    idea = sum(a.eligibility_class in {"eligible_for_content_idea_only", "eligible_for_editorial_brief_candidate"} for a in assessments)
    brief = sum(a.eligibility_class == "eligible_for_editorial_brief_candidate" for a in assessments)
    blocked = len(assessments) - idea
    blockers = tuple(dict.fromkeys(r for a in assessments for r in a.blocked_reasons))
    evidence = tuple(dict.fromkeys(r for a in assessments for r in a.evidence_refs))
    h = _digest({"assessments": [a.assessment_id for a in assessments], "idea": idea, "brief": brief, "blockers": blockers})
    return ArtifactBackedContentEligibilityReport("artifact_content_report_" + h[:24], tuple(a.assessment_id for a in assessments), idea, brief, blocked, "future_artifact_backed" if idea else "unknown_or_blocked", "artifact_required_future_gate" if not idea else "source_provided_context_only", "artifact_backed_claim_requires_packet", idea > 0, brief > 0, False, False, False, "ready_for_review_only_not_internal_alpha_ready", "dqr_not_cleared_context_only", "freshness_context_only", "source_authority_context_only", "limitations_required_and_preserved", "citations_required_and_preserved", blockers, ("human_review_required", "preserve_no_public_claim_boundary", NEXT_HEAVY_BATCH), safety_flags(), evidence)


def build_artifact_idea_seed_packet(report: ArtifactBackedContentEligibilityReport, intakes: tuple[InternalAlphaArtifactIntakePacket, ...], *, topic_hint: str = "internal alpha artifact review") -> ArtifactIdeaSeedPacket:
    citations = tuple(dict.fromkeys(r for i in intakes for r in i.citation_refs))
    limits = tuple(dict.fromkeys(r for i in intakes for r in i.limitation_notes))
    h = _digest({"report": report.report_id, "intakes": [i.artifact_intake_id for i in intakes], "topic": topic_hint})
    return ArtifactIdeaSeedPacket("artifact_idea_seed_" + h[:24], report.report_id, tuple(i.artifact_intake_id for i in intakes), topic_hint, "Review-only internal-alpha artifact context. Not current truth; not public claim.", ("x", "substack_newsletter", "linkedin"), report.content_lane, report.source_requirement_status, report.claim_risk_class, citations, limits, True, False, report.approved_for_content_idea, report.approved_for_editorial_brief_candidate, False, False, report.blockers_summary, report.evidence_refs, safety_flags())


def build_contract_packet() -> dict[str, Any]:
    safe_idea = build_manual_artifact_intake_packet({"artifact_ref": "headline_context_packet_fixture", "artifact_family": "headline_context_packet", "citation_refs": ("u7:headline_context",), "limitation_notes": ("Context only.",), "declared_readiness_state": "not_applicable_context_only", "declared_dqr_state": "context_only_not_cleared", "declared_freshness_state": "not_applicable_context_only", "declared_source_authority_state": "known_context_source", "evidence_refs": ("fixture:u7_headline",)})
    safe_brief = build_manual_artifact_intake_packet({"artifact_ref": "review_ready_artifact_fixture", "artifact_family": "internal_alpha_report", "citation_refs": ("citation:review_artifact",), "limitation_notes": ("Review-only; no current truth.",), "declared_readiness_state": "ready_for_review", "declared_dqr_state": "context_only_not_cleared", "declared_freshness_state": "fresh", "declared_source_authority_state": "known_context_source", "evidence_refs": ("fixture:review_artifact",)})
    blocked = build_manual_artifact_intake_packet({"artifact_ref": "unknown_fixture", "artifact_family": "unknown_artifact"})
    intakes = (safe_idea, safe_brief, blocked)
    assessments = tuple(assess_content_eligibility(i, context_summary="review-only artifact context") for i in intakes)
    report = build_artifact_backed_content_eligibility_report(assessments)
    seed = build_artifact_idea_seed_packet(report, intakes)
    packet = {"task_label": TASK_LABEL, "model_version": MODEL_VERSION, "source_baseline_commit": SOURCE_BASELINE_COMMIT, "intake_packets": [_asdict(i) for i in intakes], "eligibility_assessments": [_asdict(a) for a in assessments], "eligibility_report": _asdict(report), "artifact_idea_seed_packet": _asdict(seed), "safety_false_flags": list(SAFETY_FALSE_FLAGS), "artifact_scope": "docs/automation/0174U8_only", "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH}
    packet["contract_checksum"] = _digest(packet)
    return packet


def render_runbook(packet: dict[str, Any]) -> str:
    report = packet["eligibility_report"]
    return "\n".join(["# 0174U8 Internal Alpha Artifact Intake + Content Eligibility Contract", "", f"- task_label: `{packet['task_label']}`", f"- model_version: `{packet['model_version']}`", f"- source_baseline_commit: `{packet['source_baseline_commit']}`", f"- contract_checksum: `{packet['contract_checksum']}`", f"- eligible_content_idea_count: `{report['eligible_content_idea_count']}`", f"- eligible_editorial_brief_candidate_count: `{report['eligible_editorial_brief_candidate_count']}`", f"- blocked_artifact_count: `{report['blocked_artifact_count']}`", "", "## Boundaries", "", "- Review-only artifact intake.", "- Does not declare Internal Alpha ready.", "- Does not clear DQR/readiness or create current truth.", "- Never approves public claim, approval, or dispatch.", "- No provider/API/network/env/credential/scheduler/scraping/DM behavior.", "", f"## Next heavy batch", "", f"`{packet['next_heavy_batch_recommendation']}`"]) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve(); allowed = (root / DOC_REL_DIR).resolve(); out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed: raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U8")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet
