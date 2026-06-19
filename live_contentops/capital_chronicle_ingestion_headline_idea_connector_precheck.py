"""Capital Chronicle ingestion/headline idea connector precheck, 0174U7.

Read-only local precheck contract. Ingestion artifacts are context only, never
truth, readiness, DQR clearance, approval, dispatch, or public claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174U7_CAPITAL_CHRONICLE_INGESTION_HEADLINE_IDEA_CONNECTOR_PRECHECK_V0"
MODEL_VERSION = "0174U7_INGESTION_HEADLINE_IDEA_CONNECTOR_PRECHECK_V1"
PRIMARY_STARTING_HEAD = "a3a376ee73c67ce96bb0638960c2e93d01677ba1"
DOC_REL_DIR = Path("docs") / "automation" / "0174U7"
PACKET_FILENAME = "capital_chronicle_ingestion_headline_idea_connector_precheck_packet.json"
RUNBOOK_FILENAME = "capital_chronicle_ingestion_headline_idea_connector_precheck.md"
RECON_FILENAME = "ingestion_repo_recon_summary.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U8_INTERNAL_ALPHA_ARTIFACT_INTAKE_AND_CONTENT_ELIGIBILITY_CONTRACT_V0"
SAFE_EXTENSIONS = {".md", ".json", ".jsonl", ".csv", ".txt", ".yaml", ".yml"}
FORBIDDEN_PATH_TERMS = (".env", "credential", "credentials", "secret", "token", "cookie", "browser profile", "model call")
SAFETY_FALSE_FLAGS = ("env_or_credential_read", "ingestion_repo_mutated", "live_data_claim_created", "current_truth_promoted", "dqr_cleared", "readiness_cleared", "llm_provider_called", "provider_api_called", "platform_api_called", "telegram_api_called", "credential_hydrated", "env_read", "network_performed", "scheduler_enabled", "autonomous_posting_allowed", "scraping_performed", "dm_or_reply_automation_allowed", "live_dispatch_enabled", "dispatch_ready", "public_postable")
CLASS_HINTS = {
    "headline_surface": ("headline", "news_release", "release_calendar"),
    "official_source_catalog": ("official_source_catalog", "official sources", "official_sources", "source catalog"),
    "source_family_manifest": ("source_family", "family_manifest", "source spine", "source_spine"),
    "freshness_manifest": ("freshness", "sourcehealth", "source_health"),
    "coverage_gap_report": ("coverage", "gap_report", "gap report"),
    "dqr_summary": ("dqr", "data quality"),
    "data_sufficiency_summary": ("data_sufficiency", "data sufficiency"),
    "forecast_readiness_summary": ("forecast_readiness", "forecast readiness"),
    "internal_alpha_readiness_report": ("internal alpha", "internal_alpha", "not_ready", "ready"),
    "candidate_official_source_surface": ("candidate", "public_free", "no_key", "source surface"),
}
READINESS_CLASSES = {"freshness_manifest", "coverage_gap_report", "dqr_summary", "data_sufficiency_summary", "forecast_readiness_summary", "internal_alpha_readiness_report"}


@dataclass(frozen=True)
class IngestionRepoReadOnlySnapshot:
    snapshot_id: str; ingestion_repo_path: str; path_exists: bool; is_git_repo: bool; branch: str; head: str; inspected_at_epoch: int; inspected_paths: tuple[str, ...]; forbidden_paths_skipped: tuple[str, ...]; env_or_credential_read: bool; repo_mutated: bool; source_docs_found: tuple[str, ...]; artifact_surface_counts: dict[str, int]; evidence_refs: tuple[str, ...]; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class IngestionArtifactContextCandidate:
    candidate_id: str; candidate_class: str; source_repo_path: str; relative_path: str; file_ext: str; size_bytes: int; modified_time_epoch: int; contentops_use_class: str; may_generate_content_idea: bool; may_support_public_claim: bool; may_clear_dqr: bool; may_clear_readiness: bool; may_create_current_truth: bool; requires_human_review: bool; required_labels: tuple[str, ...]; evidence_refs: tuple[str, ...]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class HeadlineIdeaContextPacket:
    headline_context_packet_id: str; source_candidate_ids: tuple[str, ...]; topic_hint: str; content_lane: str; source_requirement_status: str; claim_risk_class: str; context_summary: str; citation_context_refs: tuple[str, ...]; limitation_notes: tuple[str, ...]; artifact_backed_claims_allowed: bool; public_postable: bool; human_review_required: bool; can_create_content_idea: bool; can_create_editorial_brief_candidate: bool; can_create_approval: bool; can_dispatch: bool; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]; evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class IngestionConnectorPrecheckReport:
    report_id: str; source_snapshot_id: str; candidate_count: int; usable_context_candidate_count: int; blocked_candidate_count: int; headline_context_packet_count: int; recommended_next_actions: tuple[str, ...]; current_truth_blocked: bool; dqr_clear_blocked: bool; readiness_clear_blocked: bool; provider_api_blocked: bool; network_blocked: bool; ingestion_repo_mutated: bool; validation_status: str; evidence_refs: tuple[str, ...]; blocked_reasons: tuple[str, ...]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _asdict(value: Any) -> Any:
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value


def safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def _forbidden(path: Path, root: Path | None = None) -> bool:
    target = path.relative_to(root).as_posix() if root is not None else str(path)
    s = target.lower()
    return any(term in s for term in FORBIDDEN_PATH_TERMS) or path.name.lower().startswith(".env")


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def classify_candidate(root: str | Path, path: str | Path, *, text_hint: str = "") -> IngestionArtifactContextCandidate:
    rootp, pathp = Path(root).resolve(), Path(path).resolve()
    rel = _rel(rootp, pathp)
    stat = pathp.stat()
    hay = f"{rel} {text_hint}".lower()
    found = "unknown_context_surface"
    for cls, hints in CLASS_HINTS.items():
        if any(h in hay for h in hints):
            found = cls; break
    use = "forbidden_or_unknown" if found == "unknown_context_surface" else ("readiness_context" if found in READINESS_CLASSES else "source_requirement_context" if "source" in found else "idea_context_only")
    blockers = ("unknown_context_surface_fail_closed",) if use == "forbidden_or_unknown" else ()
    labels = ("context_only", "human_review_required", "no_public_claims", "no_dqr_clearance", "no_readiness_clearance")
    h = _digest({"relative_path": rel, "class": found, "size": stat.st_size, "mtime": int(stat.st_mtime)})
    return IngestionArtifactContextCandidate("ingestion_candidate_" + h[:24], found, str(rootp), rel, pathp.suffix.lower(), stat.st_size, int(stat.st_mtime), use, use != "forbidden_or_unknown", False, False, False, False, True, labels, (rel,), blockers)


def build_read_only_snapshot(ingestion_repo_path: str | Path, *, inspected_at_epoch: int = 0, branch: str = "", head: str = "", max_files: int = 200) -> tuple[IngestionRepoReadOnlySnapshot, tuple[IngestionArtifactContextCandidate, ...]]:
    root = Path(ingestion_repo_path).resolve()
    if not root.exists():
        h = _digest({"path": str(root), "exists": False, "epoch": inspected_at_epoch})
        snap = IngestionRepoReadOnlySnapshot("ingestion_snapshot_" + h[:24], str(root), False, False, branch, head, inspected_at_epoch, (), (), False, False, (), {}, (str(root),), safety_flags(), ("ingestion_repo_path_missing",))
        return snap, ()
    inspected: list[str] = []; skipped: list[str] = []; docs: list[str] = []; candidates: list[IngestionArtifactContextCandidate] = []
    counts: dict[str, int] = {}
    is_git = (root / ".git").exists()
    for path in sorted(root.rglob("*")):
        if len(inspected) >= max_files: break
        rel = _rel(root, path)
        if _forbidden(path, root):
            skipped.append(rel); continue
        if path.is_dir() or any(part in {".git", ".venv", ".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() not in SAFE_EXTENSIONS:
            continue
        inspected.append(rel)
        if path.suffix.lower() == ".md": docs.append(rel)
        text_hint = ""
        if path.stat().st_size <= 65536 and path.suffix.lower() in {".md", ".json", ".txt", ".yaml", ".yml"}:
            text_hint = path.read_text(encoding="utf-8", errors="ignore")[:4096]
        cand = classify_candidate(root, path, text_hint=text_hint)
        counts[cand.candidate_class] = counts.get(cand.candidate_class, 0) + 1
        candidates.append(cand)
    blocked = () if candidates else ("no_candidate_surfaces_found",)
    h = _digest({"path": str(root), "branch": branch, "head": head, "inspected": inspected, "skipped": skipped, "counts": counts})
    snap = IngestionRepoReadOnlySnapshot("ingestion_snapshot_" + h[:24], str(root), True, is_git, branch, head, inspected_at_epoch, tuple(inspected), tuple(skipped), False, False, tuple(docs), counts, tuple(inspected[:20]), safety_flags(), blocked)
    return snap, tuple(candidates)


def build_headline_context_packets(candidates: tuple[IngestionArtifactContextCandidate, ...]) -> tuple[HeadlineIdeaContextPacket, ...]:
    usable = tuple(c for c in candidates if c.contentops_use_class != "forbidden_or_unknown")
    if not usable: return ()
    chosen = usable[:8]
    topic = "local ingestion context precheck"
    refs = tuple(c.relative_path for c in chosen)
    h = _digest({"candidate_ids": [c.candidate_id for c in chosen], "refs": refs})
    packet = HeadlineIdeaContextPacket("headline_context_" + h[:24], tuple(c.candidate_id for c in chosen), topic, "grounded_news_context", "source_provided_context_only", "source_context_claim", "Local ingestion artifacts may inform future ContentOps idea/context review only.", refs, ("Ingestion artifacts are not current truth.", "Human review required before any editorial use.", "DQR and readiness remain blocked."), False, False, True, True, True, False, False, safety_flags(), (), refs)
    return (packet,)


def build_precheck_report(snapshot: IngestionRepoReadOnlySnapshot, candidates: tuple[IngestionArtifactContextCandidate, ...], packets: tuple[HeadlineIdeaContextPacket, ...]) -> IngestionConnectorPrecheckReport:
    usable = sum(1 for c in candidates if c.contentops_use_class != "forbidden_or_unknown")
    blocked = len(candidates) - usable
    reasons = tuple(snapshot.blocked_reasons) + (() if usable else ("no_usable_context_candidates",))
    status = "precheck_valid_context_only" if snapshot.path_exists and usable else "blocked"
    h = _digest({"snapshot": snapshot.snapshot_id, "candidate_count": len(candidates), "usable": usable, "blocked": blocked, "packets": len(packets), "status": status})
    actions = ("preserve_context_only_boundary", "require_human_review_before_content_idea", NEXT_HEAVY_BATCH)
    return IngestionConnectorPrecheckReport("ingestion_precheck_report_" + h[:24], snapshot.snapshot_id, len(candidates), usable, blocked, len(packets), actions, True, True, True, True, True, False, status, snapshot.evidence_refs + tuple(p.evidence_refs[0] for p in packets), reasons)


def build_contract_packet(ingestion_repo_path: str | Path, *, branch: str = "", head: str = "", inspected_at_epoch: int = 0) -> dict[str, Any]:
    snapshot, candidates = build_read_only_snapshot(ingestion_repo_path, inspected_at_epoch=inspected_at_epoch, branch=branch, head=head)
    packets = build_headline_context_packets(candidates)
    report = build_precheck_report(snapshot, candidates, packets)
    data = {"task_label": TASK_LABEL, "model_version": MODEL_VERSION, "primary_starting_head": PRIMARY_STARTING_HEAD, "secondary_ingestion_repo_path": str(Path(ingestion_repo_path).resolve()), "snapshot": _asdict(snapshot), "candidates": [_asdict(c) for c in candidates[:25]], "headline_context_packets": [_asdict(p) for p in packets], "precheck_report": _asdict(report), "safety_false_flags": list(SAFETY_FALSE_FLAGS), "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH}
    data["contract_checksum"] = _digest(data)
    return data


def render_runbook(packet: dict[str, Any]) -> str:
    report = packet["precheck_report"]; snap = packet["snapshot"]
    return "\n".join(["# 0174U7 Ingestion Headline Idea Connector Precheck", "", f"- task_label: `{packet['task_label']}`", f"- model_version: `{packet['model_version']}`", f"- secondary_path: `{packet['secondary_ingestion_repo_path']}`", f"- secondary_branch: `{snap['branch']}`", f"- secondary_head: `{snap['head']}`", f"- validation_status: `{report['validation_status']}`", f"- candidate_count: `{report['candidate_count']}`", f"- usable_context_candidate_count: `{report['usable_context_candidate_count']}`", "", "## Boundaries", "", "- Context-only; not current truth.", "- DQR/readiness clearances remain blocked.", "- No provider/API/network/env/credential/scheduler/scraping/DM/dispatch behavior.", "- Ingestion repo mutation flag remains false."]) + "\n"


def render_recon_summary(packet: dict[str, Any]) -> str:
    snap = packet["snapshot"]
    skipped = "\n".join(f"- `{p}`" for p in snap["forbidden_paths_skipped"][:50]) or "- none"
    counts = "\n".join(f"- `{k}`: `{v}`" for k, v in sorted(snap["artifact_surface_counts"].items())) or "- none"
    return "\n".join(["# 0174U7 Ingestion Repo Recon Summary", "", f"- path_exists: `{snap['path_exists']}`", f"- is_git_repo: `{snap['is_git_repo']}`", f"- branch: `{snap['branch']}`", f"- head: `{snap['head']}`", f"- repo_mutated: `{snap['repo_mutated']}`", f"- env_or_credential_read: `{snap['env_or_credential_read']}`", "", "## Surface counts", "", counts, "", "## Forbidden paths skipped", "", skipped, "", "## Interpretation", "", "All observed ingestion surfaces are context-only candidates. They do not clear DQR, readiness, or current-truth gates."]) + "\n"


def write_artifacts(repo_root: str | Path, ingestion_repo_path: str | Path, *, branch: str = "", head: str = "", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve(); allowed = (root / DOC_REL_DIR).resolve(); out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed: raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U7")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet(ingestion_repo_path, branch=branch, head=head)
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    (out / RECON_FILENAME).write_text(render_recon_summary(packet), encoding="utf-8", newline="\n")
    return packet
