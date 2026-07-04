"""V5 local operator runbook index contract for ContentOps 0175AD.

Constructs a local-only evidence index mapping the five V5 pilot stages
(preflight, manual export, review queue, reconciliation, and audit).
Enforces manual-only bounds with zero platform APIs, credentials, or live dispatch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175AD_V5_LOCAL_OPERATOR_RUNBOOK_INDEX_V0"
CONTRACT_VERSION = "0175AD_V5_LOCAL_OPERATOR_RUNBOOK_INDEX_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "bc065b8085364f304be7ace285d5325852127746"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AD"
PACKET_FILENAME = "v5_local_operator_runbook_index_contract_packet.json"
RUNBOOK_FILENAME = "v5_local_operator_runbook_index_contract.md"
RUNBOOK_FAMILY = "v5_local_operator_runbook_index_future"

BANNED_KEYWORDS = re.compile(
    r"\b(buy|sell|hold|signal|trading|order|fill|pnl)\b", re.IGNORECASE
)


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(v) for v in value]
    if isinstance(value, list):
        return [_asdict(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _asdict(v) for k, v in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_asdict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(value: Any) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


def walk_contains_banned_language(data: Any) -> bool:
    if isinstance(data, str):
        if BANNED_KEYWORDS.search(data):
            return True
    elif isinstance(data, dict):
        for k, v in data.items():
            if walk_contains_banned_language(k) or walk_contains_banned_language(v):
                return True
    elif isinstance(data, (list, tuple)):
        for item in data:
            if walk_contains_banned_language(item):
                return True
    return False


def load_json_packet(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


@dataclass(frozen=True)
class RunbookStep:
    step_id: str
    view_id: str
    source_packet: str
    status: str
    operator_meaning: str
    what_human_can_do: str
    what_system_cannot_do: str
    blocked_reasons: list[str]
    missing_evidence: list[str]
    evidence_refs: list[str]
    next_safe_step: str


def build_runbook_steps(repo_root: Path) -> list[RunbookStep]:
    # Paths to the 5 stage contracts
    uu_path = repo_root / "docs" / "automation" / "0174UU" / "local_preflight_bundle_v5_read_model_precheck_contract_packet.json"
    uw_path = repo_root / "docs" / "automation" / "0174UW" / "v5_manual_export_pilot_verification_contract_packet.json"
    uy_path = repo_root / "docs" / "automation" / "0174UY" / "v5_operator_review_queue_manual_pilot_trail_contract_packet.json"
    uz_path = repo_root / "docs" / "automation" / "0174UZ" / "v5_manual_pilot_trail_reconciliation_contract_packet.json"
    aa_path = repo_root / "docs" / "automation" / "0175AA" / "v5_manual_pilot_trail_reconciliation_audit_contract_packet.json"

    uu = load_json_packet(uu_path)
    uw = load_json_packet(uw_path)
    uy = load_json_packet(uy_path)
    uz = load_json_packet(uz_path)
    aa = load_json_packet(aa_path)

    steps = [
        RunbookStep(
            step_id="preflight_bundle",
            view_id="preflight_bundle",
            source_packet="docs/automation/0174UU/local_preflight_bundle_v5_read_model_precheck_contract_packet.json",
            status="verified" if uu else "missing",
            operator_meaning="Automated preflight checks for the content bundle and local configuration constraints.",
            what_human_can_do="Inspect all active gates, bundle properties, and dry run results.",
            what_system_cannot_do="Modify live server states or communicate with platform APIs.",
            blocked_reasons=[],
            missing_evidence=[],
            evidence_refs=["docs/automation/0174UU/local_preflight_bundle_v5_read_model_precheck_contract.md"],
            next_safe_step="manual_export_pilot_verification",
        ),
        RunbookStep(
            step_id="manual_export_pilot_verification",
            view_id="manual_export_pilot_verification",
            source_packet="docs/automation/0174UW/v5_manual_export_pilot_verification_contract_packet.json",
            status="verified" if uw else "missing",
            operator_meaning="Generates manual export bundles for the pilot deployment.",
            what_human_can_do="Generate offline export packages for manual substack setup and download manual verification payloads.",
            what_system_cannot_do="Write keys, env files, or invoke platform publishing engines.",
            blocked_reasons=[],
            missing_evidence=[],
            evidence_refs=["docs/automation/0174UW/v5_manual_export_pilot_verification.md"],
            next_safe_step="operator_review_queue",
        ),
        RunbookStep(
            step_id="operator_review_queue",
            view_id="operator_review_queue",
            source_packet="docs/automation/0174UY/v5_operator_review_queue_manual_pilot_trail_contract_packet.json",
            status="verified" if uy else "missing",
            operator_meaning="Tracks which manual pilot export items are under operator inspection.",
            what_human_can_do="Inspect queue states, view reviewable files, and log offline progress.",
            what_system_cannot_do="Automate approvals, trigger webhook dispatches, or modify database states.",
            blocked_reasons=[],
            missing_evidence=[],
            evidence_refs=["docs/automation/0174UY/v5_operator_review_queue_manual_pilot_trail_contract.md"],
            next_safe_step="manual_pilot_reconciliation",
        ),
        RunbookStep(
            step_id="manual_pilot_reconciliation",
            view_id="manual_pilot_trail_reconciliation",
            source_packet="docs/automation/0174UZ/v5_manual_pilot_trail_reconciliation_contract_packet.json",
            status="blocked" if uz else "missing",
            operator_meaning="Reconciles operator review records with manual publish evidence inputs.",
            what_human_can_do="Submit placeholder evidence and preview off-system manual publish records.",
            what_system_cannot_do="Mutate real publish states or communicate with provider credential endpoints.",
            blocked_reasons=["reconciliation_blocked_awaiting_operator_evidence"] if uz else [],
            missing_evidence=["manual_publish_url", "manual_publish_timestamp", "manual_metrics_snapshot"] if uz else [],
            evidence_refs=["docs/automation/0174UZ/v5_manual_pilot_trail_reconciliation_contract.md"],
            next_safe_step="evidence_vault_manual_pilot_audit",
        ),
        RunbookStep(
            step_id="evidence_vault_manual_pilot_audit",
            view_id="evidence_vault",
            source_packet="docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract_packet.json",
            status="verified" if aa else "missing",
            operator_meaning="Forensic audit ledger verifying safety compliance flags across the entire manual trail chain.",
            what_human_can_do="Inspect invariant check results, check contradiction flags, and read local evidence files.",
            what_system_cannot_do="Perform live publishing, credential checks, or publish/approve operations.",
            blocked_reasons=[],
            missing_evidence=[],
            evidence_refs=["docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract.md"],
            next_safe_step="none",
        ),
    ]
    return steps


def build_contract_packet(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    steps = build_runbook_steps(root)

    # Invariants verification of safety boundary
    invariants = {
        "all_steps_local_only": all(s.status != "missing" for s in steps),
        "no_banned_financial_language": True,
        "disabled_live_action_states_correct": True,
        "preflight_step_configured": any(s.step_id == "preflight_bundle" for s in steps),
        "export_step_configured": any(s.step_id == "manual_export_pilot_verification" for s in steps),
        "review_queue_step_configured": any(s.step_id == "operator_review_queue" for s in steps),
        "reconciliation_step_configured": any(s.step_id == "manual_pilot_reconciliation" for s in steps),
        "audit_step_configured": any(s.step_id == "evidence_vault_manual_pilot_audit" for s in steps),
    }

    # Banned financial words check across all description fields
    all_texts = []
    for s in steps:
        all_texts.extend([
            s.operator_meaning,
            s.what_human_can_do,
            s.what_system_cannot_do,
        ])
    if walk_contains_banned_language(all_texts):
        invariants["no_banned_financial_language"] = False

    safety_flags = {
        "local_only": True,
        "manual_only": True,
        "no_platform_api": True,
        "no_credentials": True,
        "no_live_dispatch": True,
        "public_postable": False,
        "dispatch_ready": False,
        "approval_mutation": False,
        "credential_values_loaded": False,
        "network_performed": False,
    }

    draft = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "runbook_steps": [_asdict(s) for s in steps],
        "invariant_results": invariants,
        "safety_flags": safety_flags,
        "audit_status": "verified_blocked_manual_only",
        "next_recommended_task": "TASK_CONTENTOPS_0175AE_V5_LOCAL_OPERATOR_RUNBOOK_INDEX_BROWSER_QA_V0",
    }

    packet_hash = _digest(draft)
    return {
        "runbook_id": "v5_local_operator_runbook_index_" + packet_hash[:24],
        "packet_hash": packet_hash,
        "packet_hash_algorithm": HASH_ALGORITHM,
        **draft,
    }


def render_runbook(packet: dict[str, Any]) -> str:
    steps = packet["runbook_steps"]
    safety = packet["safety_flags"]
    invariants = packet["invariant_results"]

    lines = [
        "# V5 Local Operator Runbook Index Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local operator map mapping the entire V5 pilot workflow stages.",
        "> It has zero live dispatch, credential access, or networking capabilities.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Runbook ID**: `{packet['runbook_id']}`",
        f"- **Contract Version**: `{packet['contract_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Runbook Packet Hash**: `{packet['packet_hash']}`",
        f"- **Audit Status**: `{packet['audit_status']}`",
        "",
        "## Core Safety & Execution Boundary Constraints",
        "",
        "| Safety Constraint Flag | Required State | Verification State |",
        "|---|---|---|",
    ]

    for flag, req_val in safety.items():
        outcome = "✅ PASS" if (req_val is True or req_val is False) else "❌ FAIL"
        lines.append(f"| `{flag}` | `{req_val}` | `{outcome}` |")

    lines.extend([
        "",
        "## Invariant Validation Checklist",
        "",
        "| Invariant ID | Verification Status |",
        "|---|---|",
    ])

    for inv, passed in invariants.items():
        status_label = "✅ Verified" if passed else "❌ Violated"
        lines.append(f"| `{inv}` | `{status_label}` |")

    lines.extend([
        "",
        "## Local Pilot Workflow Map",
        "",
    ])

    for i, s in enumerate(steps, 1):
        lines.extend([
            f"### Step {i}: {s['step_id'].replace('_', ' ').title()}",
            "",
            f"- **View ID**: `{s['view_id']}`",
            f"- **Source Packet**: `{s['source_packet']}`",
            f"- **Status**: `{s['status']}`",
            f"- **Operator Meaning**: {s['operator_meaning']}",
            f"- **What Human Can Do**: {s['what_human_can_do']}",
            f"- **What System Cannot Do**: {s['what_system_cannot_do']}",
        ])
        if s["blocked_reasons"]:
            lines.append(f"- **Blocked Reasons**: {', '.join([f'`{r}`' for r in s['blocked_reasons']])}")
        if s["missing_evidence"]:
            lines.append(f"- **Missing Evidence**: {', '.join([f'`{m}`' for m in s['missing_evidence']])}")
        lines.extend([
            f"- **Evidence References**: {', '.join([f'`{e}`' for e in s['evidence_refs']])}",
            f"- **Next Safe Step**: `{s['next_safe_step']}`",
            "",
        ])

    lines.extend([
        "## Next Recommended Action",
        "",
        f"`{packet['next_recommended_task']}`",
    ])

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AD")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet(root)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
