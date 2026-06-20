"""Live read-only research credential slot inspection mock audit contract for ContentOps 0174UT.

Deterministic local-only validation contract. No live/API/provider/network/
env/credential/browser/scheduler/scraping/DM/reply automation or UI behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
from live_contentops import live_read_only_research_runbook_approval_gate_dry_run_contract as runbook
from live_contentops import live_read_only_research_local_preflight_simulation_contract as simulation
from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import read_only_credential_slot_check_validation_contract as slot_check

TASK_LABEL = "TASK_CONTENTOPS_0174UT_READ_ONLY_CREDENTIALS_SLOT_INSPECTION_MOCK_AUDIT_V0"
MATRIX_VERSION = "0174UT_READ_ONLY_CREDENTIALS_SLOT_INSPECTION_MOCK_AUDIT_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "dcd7cb7ef090ef7b44711c21aeac670ce06ad784"
DOC_REL_DIR = Path("docs") / "automation" / "0174UT"
PACKET_FILENAME = "read_only_credential_slot_inspection_mock_audit_contract_packet.json"
RUNBOOK_FILENAME = "read_only_credential_slot_inspection_mock_audit_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "read_only_credential_slot_inspection_mock_audit_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UU_READ_ONLY_CREDENTIALS_SLOT_DESTRUCTION_MOCK_AUDIT_V0"

PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class MockCredentialSlotInventory:
    inventory_id: str
    platform_id: str
    declared_slot_names: tuple[str, ...]
    missing_slot_names: tuple[str, ...]
    malformed_slot_names: tuple[str, ...]
    forbidden_slot_names: tuple[str, ...]
    attempted_value_fields: tuple[str, ...]
    attempted_hash_fields: tuple[str, ...]
    attempted_token_slice_fields: tuple[str, ...]
    inventory_mode: str = "mock_only"
    attempted_env_read: bool = False
    attempted_dotenv_read: bool = False
    credential_values_present: bool = False
    value_material_serialized: bool = False
    raw_secret_value: str = "absent"
    redacted_value: str = "[REDACTED]"


@dataclass(frozen=True)
class MockCredentialSlotInspectionFinding:
    finding_id: str
    platform_id: str
    inventory_id: str
    finding_kind: str
    severity: str
    classification: str
    audit_status: str
    redaction_status: str
    blocked_reason: str
    missing_proof: str
    secret_material_exposed: bool = False
    credential_value_read: bool = False
    env_read: bool = False
    dotenv_loaded: bool = False
    secret_hash_displayed: bool = False
    token_prefix_displayed: bool = False
    token_suffix_displayed: bool = False
    platform_api_called: bool = False
    provider_api_called: bool = False
    live_read_allowed: bool = False
    live_write_allowed: bool = False
    public_post_allowed: bool = False
    readiness_cleared: bool = False
    finding_hash: str = ""


@dataclass(frozen=True)
class MockCredentialSlotInspectionAuditDecision:
    decision_id: str
    platform_id: str
    inventory_id: str
    slot_schema_status: str
    inventory_status: str
    finding_count: int
    highest_severity: str
    audit_decision_status: str
    audit_strength: str
    failure_or_abort_classification: str
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    safety_flags: dict[str, bool]
    evidence_refs: tuple[str, ...]
    decision_hash: str


@dataclass(frozen=True)
class MockCredentialSlotInspectionAuditPacket:
    packet_id: str
    packet_hash: str
    packet_hash_algorithm: str
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_count: int
    inventory_count: int
    finding_count: int
    decision_count: int
    mock_inventories: tuple[MockCredentialSlotInventory, ...]
    inspection_findings: tuple[MockCredentialSlotInspectionFinding, ...]
    audit_decisions: tuple[MockCredentialSlotInspectionAuditDecision, ...]
    platform_audit_summary: dict[str, str]
    inventory_status_summary: dict[str, str]
    finding_kind_summary: dict[str, str]
    severity_summary: dict[str, str]
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    safety_flags: dict[str, bool]
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    next_required_gate: str


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


def build_mock_inventories() -> tuple[MockCredentialSlotInventory, ...]:
    inventories = []
    specs = slot_check.build_slot_specs()

    for spec in specs:
        p_id = spec.platform_id
        is_manual = spec.manual_only

        if is_manual:
            inventories.append(
                MockCredentialSlotInventory(
                    inventory_id=f"inventory_{p_id}_manual_only_substack_inventory",
                    platform_id=p_id,
                    declared_slot_names=(),
                    missing_slot_names=(),
                    malformed_slot_names=(),
                    forbidden_slot_names=(),
                    attempted_value_fields=(),
                    attempted_hash_fields=(),
                    attempted_token_slice_fields=(),
                )
            )
            continue

        # 1. all_slots_absent
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_all_slots_absent",
                platform_id=p_id,
                declared_slot_names=(),
                missing_slot_names=spec.required_slot_names,
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
            )
        )

        # 2. declared_slots_names_only
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_declared_slots_names_only",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
            )
        )

        # 3. missing_required_slot
        req_missing = (spec.required_slot_names[0],) if spec.required_slot_names else ()
        req_declared = spec.required_slot_names[1:] if spec.required_slot_names else ()
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_missing_required_slot",
                platform_id=p_id,
                declared_slot_names=req_declared,
                missing_slot_names=req_missing,
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
            )
        )

        # 4. forbidden_slot_name_present
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_forbidden_slot_name_present",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names + (f"{p_id.upper()}_PASSWORD",),
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(f"{p_id.upper()}_PASSWORD",),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
            )
        )

        # 5. credential_value_attempt_present
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_credential_value_attempt_present",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(spec.required_slot_names[0],) if spec.required_slot_names else (),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
                credential_values_present=True,
            )
        )

        # 6. secret_hash_attempt_present
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_secret_hash_attempt_present",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(f"{spec.required_slot_names[0]}_HASH",) if spec.required_slot_names else (),
                attempted_token_slice_fields=(),
            )
        )

        # 7. token_prefix_suffix_attempt_present
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_token_prefix_suffix_attempt_present",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(f"{spec.required_slot_names[0]}_PREFIX",) if spec.required_slot_names else (),
            )
        )

        # 8. dotenv_read_attempt
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_dotenv_read_attempt",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
                attempted_dotenv_read=True,
            )
        )

        # 9. env_read_attempt
        inventories.append(
            MockCredentialSlotInventory(
                inventory_id=f"inventory_{p_id}_env_read_attempt",
                platform_id=p_id,
                declared_slot_names=spec.required_slot_names,
                missing_slot_names=(),
                malformed_slot_names=(),
                forbidden_slot_names=(),
                attempted_value_fields=(),
                attempted_hash_fields=(),
                attempted_token_slice_fields=(),
                attempted_env_read=True,
            )
        )

    return tuple(inventories)


def compile_inspection_finding(
    inv: MockCredentialSlotInventory,
    kind: str,
) -> MockCredentialSlotInspectionFinding:
    finding_id = f"finding_{inv.platform_id}_{inv.inventory_id[:12]}_{kind}"
    draft = {
        "platform_id": inv.platform_id,
        "inventory_id": inv.inventory_id,
        "finding_kind": kind,
        "severity": "high" if kind in ("required_slot_missing", "forbidden_slot_name_present", "credential_value_attempt_present", "secret_hash_attempt_present", "token_prefix_suffix_attempt_present", "dotenv_read_attempt", "env_read_attempt") else "info",
        "classification": "manual_only" if inv.platform_id == "substack_newsletter" else "blocked",
        "audit_status": "failed_closed" if kind in ("required_slot_missing", "forbidden_slot_name_present", "credential_value_attempt_present", "secret_hash_attempt_present", "token_prefix_suffix_attempt_present", "dotenv_read_attempt", "env_read_attempt") else "not_applicable",
        "redaction_status": "redacted" if kind == "credential_value_attempt_present" else "none",
        "blocked_reason": f"{kind}_blocked",
        "missing_proof": f"{kind}_missing_proof",
    }
    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return MockCredentialSlotInspectionFinding(
        finding_id=finding_id,
        finding_hash=h,
        **draft
    )


def compile_findings_for_inventory(
    inv: MockCredentialSlotInventory
) -> tuple[MockCredentialSlotInspectionFinding, ...]:
    findings = []
    if inv.missing_slot_names:
        findings.append(compile_inspection_finding(inv, "required_slot_missing"))
    if inv.forbidden_slot_names:
        findings.append(compile_inspection_finding(inv, "forbidden_slot_name_present"))
    if inv.credential_values_present:
        findings.append(compile_inspection_finding(inv, "credential_value_attempt_present"))
    if inv.attempted_hash_fields:
        findings.append(compile_inspection_finding(inv, "secret_hash_attempt_present"))
    if inv.attempted_token_slice_fields:
        findings.append(compile_inspection_finding(inv, "token_prefix_suffix_attempt_present"))
    if inv.attempted_dotenv_read:
        findings.append(compile_inspection_finding(inv, "dotenv_read_attempt"))
    if inv.attempted_env_read:
        findings.append(compile_inspection_finding(inv, "env_read_attempt"))

    # Fallback info finding
    if not findings:
        findings.append(compile_inspection_finding(inv, "declared_slots_schema_only"))

    return tuple(findings)


def compile_audit_decision(
    platform_id: str,
    inv_id: str,
    specs: tuple[slot_check.ReadOnlyCredentialSlotSpec, ...],
    inventories: tuple[MockCredentialSlotInventory, ...],
    findings: tuple[MockCredentialSlotInspectionFinding, ...],
) -> MockCredentialSlotInspectionAuditDecision:
    spec = next(s for s in specs if s.platform_id == platform_id)
    inv = next(i for i in inventories if i.inventory_id == inv_id)
    inv_findings = [f for f in findings if f.inventory_id == inv_id]

    is_manual = platform_id == "substack_newsletter"

    blocked_reasons = []
    missing_proofs = []

    # Platform specific requirements & blockers
    if platform_id == "x":
        for r in ("x_app_access_gap", "spend_gate_unresolved", "rate_budget_gap", "read_only_endpoint_proof_gap"):
            blocked_reasons.append(r)
            missing_proofs.append(r)
    elif platform_id == "telegram_remote_operator":
        for r in ("no_arbitrary_dm_allowed", "operator_inbox_proof_required"):
            blocked_reasons.append(r)
            missing_proofs.append(r)
    elif platform_id == "telegram_channel_destination":
        for r in ("channel_admin_proof_required", "bot_permission_gap", "channel_state_symbolic_only"):
            blocked_reasons.append(r)
            missing_proofs.append(r)
    elif platform_id == "substack_newsletter":
        blocked_reasons.append("manual_export_only")
        missing_proofs.append("manual_export_only")
    elif platform_id == "linkedin":
        blocked_reasons.append("linkedin_organization_page_proof_missing")
        missing_proofs.append("linkedin_organization_page_proof_missing")
    elif platform_id in ("threads", "instagram", "facebook_page"):
        for r in ("meta_app_review_closed", "meta_app_account_proof_required"):
            blocked_reasons.append(r)
            missing_proofs.append(r)
    elif platform_id == "tiktok":
        for r in ("tiktok_app_audit_closed", "creator_account_proof_required", "video_publish_proof_required"):
            blocked_reasons.append(r)
            missing_proofs.append(r)
    elif platform_id == "youtube":
        for r in ("youtube_quota_unresolved", "youtube_oauth_flow_closed", "upload_proof_required"):
            blocked_reasons.append(r)
            missing_proofs.append(r)

    highest_sev = "none"
    for f in inv_findings:
        blocked_reasons.append(f.blocked_reason)
        missing_proofs.append(f.missing_proof)
        if f.severity == "high":
            highest_sev = "high"
        elif f.severity == "warning" and highest_sev != "high":
            highest_sev = "warning"
        elif f.severity == "info" and highest_sev not in ("high", "warning"):
            highest_sev = "info"

    if is_manual:
        audit_decision_status = "manual_only"
        audit_strength = "manual_policy_only"
    else:
        audit_decision_status = "blocked" if (highest_sev == "high" or "all_slots_absent" in inv_id or "missing_required_slot" in inv_id) else "not_ready"
        audit_strength = "strict_schema_validation"

    failure_or_abort = "none"
    if "required_slot_missing" in inv_id:
        failure_or_abort = "missing_required_slot_error"
    elif "forbidden_slot_name_present" in inv_id:
        failure_or_abort = "forbidden_slot_pattern_error"
    elif "credential_value_attempt_present" in inv_id:
        failure_or_abort = "credential_value_attempt_error"
    elif "dotenv_read_attempt" in inv_id:
        failure_or_abort = "dotenv_load_attempt_error"
    elif "env_read_attempt" in inv_id:
        failure_or_abort = "env_read_attempt_error"
    elif "secret_hash_attempt" in inv_id:
        failure_or_abort = "secret_hash_attempt_error"
    elif "token_prefix_suffix_attempt" in inv_id:
        failure_or_abort = "prefix_suffix_attempt_error"

    inventory_status = "missing_slots"
    if "declared_slots_names_only" in inv_id:
        inventory_status = "valid_names_only"
    elif "forbidden_slot_name" in inv_id:
        inventory_status = "forbidden_names"
    elif "credential_value_attempt" in inv_id:
        inventory_status = "exposed_secrets"
    elif "dotenv_read_attempt" in inv_id:
        inventory_status = "exposed_dotenv"
    elif "env_read_attempt" in inv_id:
        inventory_status = "exposed_env"

    draft = {
        "platform_id": platform_id,
        "inventory_id": inv_id,
        "slot_schema_status": "key_names_only" if not is_manual else "manual_no_credential",
        "inventory_status": inventory_status,
        "finding_count": len(inv_findings),
        "highest_severity": highest_sev,
        "audit_decision_status": audit_decision_status,
        "audit_strength": audit_strength,
        "failure_or_abort_classification": failure_or_abort,
        "blocked_reasons": tuple(dict.fromkeys(blocked_reasons)),
        "missing_proofs": tuple(dict.fromkeys(missing_proofs)),
        "safety_flags": {
            "live_read_allowed": False,
            "live_write_allowed": False,
            "env_read_allowed": False,
            "credential_hydrated": False,
            "platform_api_called": False,
            "provider_api_called": False,
            "public_post_allowed": False,
            "scheduler_enabled": False,
            "browser_session_used": False,
            "scraping_performed": False,
            "dm_or_reply_automation_allowed": False,
            "readiness_cleared": False,
        },
        "evidence_refs": ("proof:0174UT",),
    }

    h_basis = {str(k): _asdict(v) for k, v in draft.items()}
    h = sha256(json.dumps(h_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    return MockCredentialSlotInspectionAuditDecision(
        decision_id=f"audit_decision_{platform_id}_{inv_id[:12]}_" + h[:8],
        decision_hash=h,
        **draft
    )


def build_u9_audit_entries(
    decisions: tuple[MockCredentialSlotInspectionAuditDecision, ...]
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UT"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, dec in enumerate(decisions, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UT",
            source_model_version=MATRIX_VERSION,
            payload={
                "id": dec.decision_id,
                "platform_id": dec.platform_id,
                "inventory_id": dec.inventory_id,
                "status": dec.audit_decision_status,
                "source_payload_hash": dec.decision_hash,
                "blocked_reasons": dec.blocked_reasons,
                "missing_proofs": dec.missing_proofs,
                "safety_flags": dec.safety_flags,
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_supervised_credential_slot_inspection_audit_packet(
    slot_packet: slot_check.ReadOnlyCredentialSlotCheckPacket | None = None
) -> MockCredentialSlotInspectionAuditPacket:
    sim = simulation.build_supervised_live_read_only_research_local_preflight_simulation_packet()
    rq = runbook.build_supervised_live_read_only_research_runbook_approval_gate_dry_run_packet()
    sc_packet = slot_packet or slot_check.build_supervised_read_only_credential_slot_check_packet()
    bp = boundary.build_credential_boundary_packet()
    ab = binding.build_platform_account_binding_registry_packet()

    mock_inventories = build_mock_inventories()
    specs = slot_check.build_slot_specs()

    findings = []
    for inv in mock_inventories:
        for f in compile_findings_for_inventory(inv):
            findings.append(f)
    findings = tuple(findings)

    decisions = []
    for inv in mock_inventories:
        decisions.append(compile_audit_decision(inv.platform_id, inv.inventory_id, specs, mock_inventories, findings))
    decisions = tuple(decisions)

    platform_audit_summary = {pid: "blocked" if pid != "substack_newsletter" else "manual_only" for pid in PLATFORM_IDS}
    inventory_status_summary = {d.inventory_id: d.inventory_status for d in decisions}
    finding_kind_summary = {f.finding_id: f.finding_kind for f in findings}
    severity_summary = {f.finding_id: f.severity for f in findings}

    global_blocked_reasons = tuple(dict.fromkeys(r for d in decisions for r in d.blocked_reasons))
    global_missing_proofs = tuple(dict.fromkeys(p for d in decisions for p in d.missing_proofs))

    audit_entries = build_u9_audit_entries(decisions)

    safety_flags = {
        "live_read_allowed": False,
        "live_write_allowed": False,
        "public_post_allowed": False,
        "credential_hydrated": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "telegram_api_called": False,
        "network_performed": False,
        "env_read": False,
        "browser_session_used": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "dispatch_ready": False,
        "public_postable": False,
        "autonomous_posting_allowed": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "ingestion_repo_mutated": False,
        "ui_generated": False,
        "local_readiness_review_only": True,
        "review_only": True,
        "mock_only": True,
        "all_real_secret_reads_blocked": True,
        "all_env_reads_blocked": True,
        "all_dotenv_loads_blocked": True,
        "all_secret_outputs_blocked": True,
        "all_live_actions_blocked": True,
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "platform_count": len(PLATFORM_IDS),
        "inventory_count": len(mock_inventories),
        "finding_count": len(findings),
        "decision_count": len(decisions),
        "mock_inventories": mock_inventories,
        "inspection_findings": findings,
        "audit_decisions": decisions,
        "platform_audit_summary": platform_audit_summary,
        "inventory_status_summary": inventory_status_summary,
        "finding_kind_summary": finding_kind_summary,
        "severity_summary": severity_summary,
        "blocked_reasons": global_blocked_reasons,
        "missing_proofs": global_missing_proofs,
        "safety_flags": safety_flags,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "next_required_gate": NEXT_REQUIRED_GATE,
    }

    packet_hash = _digest(draft)
    return MockCredentialSlotInspectionAuditPacket(
        packet_id="read_only_credential_slot_inspection_mock_audit_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft
    )


def render_runbook(packet: MockCredentialSlotInspectionAuditPacket) -> str:
    lines = [
        "# Read-Only Credentials Slot Inspection Mock Audit Contract V0",
        "",
        "## Critical Security Warning",
        "> [!CAUTION]",
        "> **MOCK AUDIT ONLY. ZERO REAL SECRET VALUES OR PARAMETERS ARE ACCESSED.**",
        "> This contract validates synthetic mock inventories against key-name schemas to prove auditing capability.",
        "> No dotenv loads, env reads, raw credential lookups, or API integrations are run.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Source Baseline Commit**: `{packet.source_baseline_commit}`",
        f"- **Matrix/Packet ID**: `{packet.packet_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Next Required Gate**: `{packet.next_required_gate}`",
        "",
        "## 1. Mock Inventory Verification Matrix",
        "",
        "| Inventory ID | Platform ID | Mode | Declared Slots | Value Present | Malformed Slots |",
        "|---|---|---|---|---|---|",
    ]
    for inv in packet.mock_inventories:
        declared = ", ".join(f"`{name}`" for name in inv.declared_slot_names) if inv.declared_slot_names else "*None*"
        lines.append(
            f"| `{inv.inventory_id[:40]}` | `{inv.platform_id}` | `{inv.inventory_mode}` | {declared} | `{inv.credential_values_present}` | `{len(inv.malformed_slot_names)}` |"
        )

    lines.extend([
        "",
        "## 2. Inspection Findings Audit Matrix",
        "",
        "| Finding ID | Platform ID | Finding Kind | Severity | Audit Status | Redaction Status |",
        "|---|---|---|---|---|---|",
    ])
    for f in packet.inspection_findings:
        lines.append(
            f"| `{f.finding_id[:40]}` | `{f.platform_id}` | `{f.finding_kind}` | `{f.severity}` | `{f.audit_status}` | `{f.redaction_status}` |"
        )

    lines.extend([
        "",
        "## 3. Audit Decisions Output Matrix",
        "",
        "| Decision ID | Platform ID | Inventory Status | Audit Status | Severity | Failure / Abort |",
        "|---|---|---|---|---|---|",
    ])
    for d in packet.audit_decisions:
        lines.append(
            f"| `{d.decision_id[:40]}` | `{d.platform_id}` | `{d.inventory_status}` | `{d.audit_decision_status}` | `{d.highest_severity}` | `{d.failure_or_abort_classification}` |"
        )

    lines.extend([
        "",
        "## 4. Forbidden Secret-Output Checklist",
        "- [ ] Ensure zero credentials values are serialized, logged, or printed.",
        "- [ ] Confirm that raw API responses are not included in audit summaries.",
        "",
        "## 5. Redaction Proof Checklist",
        "- [ ] Redact all user operator credentials and replace with simulated values.",
        "- [ ] Enforce redaction required flag for all API mock inspections.",
        "",
        "## 6. Next Required Gate",
        f"- Next gate is: `{packet.next_required_gate}`",
    ])

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UT")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_supervised_credential_slot_inspection_audit_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "MockCredentialSlotInventory",
    "MockCredentialSlotInspectionFinding",
    "MockCredentialSlotInspectionAuditDecision",
    "MockCredentialSlotInspectionAuditPacket",
    "build_mock_inventories",
    "compile_findings_for_inventory",
    "compile_audit_decision",
    "build_supervised_credential_slot_inspection_audit_packet",
    "render_runbook",
    "write_artifacts",
]
