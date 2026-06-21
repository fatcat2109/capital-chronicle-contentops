"""Platform Preview Dry Render to Review Bundle contract, 0175AP.

Deterministic local-only contract combining dry renders into a review bundle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.platform_preview_dry_render_packet_contract import (
    build_contract_packet as build_dry_render_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AP_PLATFORM_PREVIEW_DRY_RENDER_TO_REVIEW_BUNDLE_V0"
MATRIX_VERSION = "0175AP_PLATFORM_PREVIEW_DRY_RENDER_TO_REVIEW_BUNDLE_V1"
SOURCE_BASELINE_COMMIT = "1a2d9bd78a254bee8790c3a8288168166a3f2fa8"
LEDGER_FAMILY = "platform_preview_dry_render_to_review_bundle_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AP"
PACKET_FILENAME = "platform_preview_dry_render_to_review_bundle_contract_packet.json"
RUNBOOK_FILENAME = "platform_preview_dry_render_to_review_bundle_contract.md"


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


@dataclass(frozen=True)
class PlatformReviewBundleDecisionStub:
    decision_stub_id: str
    decision_status: str = "disabled_pending_future_operator_gate"
    approve_button_enabled: bool = False
    reject_button_enabled: bool = False
    request_revision_enabled: bool = False
    publish_button_enabled: bool = False
    dispatch_button_enabled: bool = False
    operator_identity_bound: bool = False
    approval_signature_present: bool = False
    payload_hash_locked: bool = False


@dataclass(frozen=True)
class PlatformReviewBundleBlocker:
    blocker_id: str
    description: str
    active: bool = True


@dataclass(frozen=True)
class PlatformReviewBundleChecklistItem:
    item_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class PlatformReviewBundleItem:
    bundle_item_id: str
    source_render_id: str
    platform_target_id: str
    platform_family: str
    review_surface_type: str
    render_status: str
    bundle_status: str
    operator_review_required: bool
    manual_decision_required: bool
    publishability_status: str
    citation_slot_status: str
    limitation_slot_status: str
    dqr_status: str
    readiness_status: str
    current_truth_status: str
    account_binding_status: str
    credential_gate_status: str
    payload_hash_lock_status: str
    dispatch_gate_status: str
    blockers: list[str]
    missing_future_gates: list[str]
    review_notes_placeholder: str
    decision_stub: PlatformReviewBundleDecisionStub
    packet_hash: str
    # Safety & Status Flags
    public_postable: bool = False
    publishable_text: bool = False
    platform_ready: bool = False
    dispatch_ready: bool = False
    export_ready: bool = False
    platform_payload_created: bool = False
    publishable_payload_created: bool = False
    account_binding_active: bool = False
    credential_values_loaded: bool = False
    platform_api_called: bool = False
    scheduler_enabled: bool = False
    approved_for_publication: bool = False


@dataclass(frozen=True)
class PlatformPreviewDryRenderReviewBundlePacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    bundle_items: list[PlatformReviewBundleItem]
    global_blockers: list[PlatformReviewBundleBlocker]
    bundle_checklist: list[PlatformReviewBundleChecklistItem]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_bundle_blockers() -> list[PlatformReviewBundleBlocker]:
    blockers = {
        "blocked_no_operator_review": "Operator review gate is required but pending.",
        "blocked_no_manual_decision_gate": "Manual decision gate is required but pending.",
        "blocked_no_account_binding": "Account binding is required but inactive.",
        "blocked_no_credential_gate": "Credential gate authentication is required but pending.",
        "blocked_no_payload_hash_lock": "Payload hash lock verification is required but pending.",
        "blocked_dqr_readiness_unresolved": "DQR and publish readiness checks are unresolved.",
        "blocked_not_public_postable": "Candidate is not marked public postable.",
        "blocked_no_dispatch_gate": "Dispatch gate has not cleared the post.",
        "blocked_no_platform_api_authorization": "Platform API is not authorized (local contract dry run).",
        "blocked_no_export_gate": "Export gate has not been cleared."
    }
    return [
        PlatformReviewBundleBlocker(blocker_id=bid, description=desc, active=True)
        for bid, desc in blockers.items()
    ]


def build_bundle_checklist() -> list[PlatformReviewBundleChecklistItem]:
    return [
        PlatformReviewBundleChecklistItem(
            item_id="operator_review_checklist_pending",
            description="Verify operator manual visual inspection signature.",
            passed=False
        ),
        PlatformReviewBundleChecklistItem(
            item_id="manual_decision_checklist_pending",
            description="Verify manual Go/No-Go decision has been saved.",
            passed=False
        ),
        PlatformReviewBundleChecklistItem(
            item_id="preflight_bundle_cleared",
            description="Verify local preflight requirements have succeeded.",
            passed=False
        )
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "dry_render_only": True,
        "review_bundle_only": True,
        "network_performed": False,
        "env_read": False,
        "credential_values_loaded": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "account_binding_active": False,
        "scheduler_enabled": False,
        "autonomous_posting": False,
        "autonomous_reply_or_dm": False,
        "scraping": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_created": False,
        "publishable_payload_created": False,
        "export_ready": False,
        "approved_for_publication": False,
        "operator_approval_granted": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
    }


def build_contract_packet() -> dict[str, Any]:
    # Consume 0175AO dry render packet precedent
    dry_render_data = build_dry_render_packet()
    renders = dry_render_data.get("render_records", [])

    blockers = build_bundle_blockers()
    blocked_ids = [b.blocker_id for b in blockers]

    bundle_items: list[PlatformReviewBundleItem] = []

    for r in renders:
        tid = r["platform_target_id"]
        family = r["platform_family"]
        surface = r["preview_surface_type"]

        decision_stub = PlatformReviewBundleDecisionStub(
            decision_stub_id=f"decision_{tid}"
        )

        raw_item = {
            "bundle_item_id": f"bundle_item_{tid}",
            "source_render_id": r["render_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "review_surface_type": surface,
            "render_status": r["render_status"],
            "bundle_status": "review_bundle_blocked",
            "operator_review_required": True,
            "manual_decision_required": True,
            "publishability_status": "non_publishable_review_bundle",
            "citation_slot_status": r["citation_slot_status"],
            "limitation_slot_status": r["limitation_slot_status"],
            "dqr_status": "dqr_unresolved",
            "readiness_status": "readiness_unresolved",
            "current_truth_status": "current_truth_unpromoted",
            "account_binding_status": r["account_binding_status"],
            "credential_gate_status": r["credential_gate_status"],
            "payload_hash_lock_status": r["payload_hash_lock_status"],
            "dispatch_gate_status": r["dispatch_gate_status"],
            "blockers": blocked_ids,
            "missing_future_gates": ["lane_c_platform_review_bundle_operator_decision_gate"],
            "review_notes_placeholder": f"[REVIEW_NOTE_PLACEHOLDER: operator comments for {tid}]",
            "decision_stub": _asdict(decision_stub),
            "public_postable": False,
            "publishable_text": False,
            "platform_ready": False,
            "dispatch_ready": False,
            "export_ready": False,
            "platform_payload_created": False,
            "publishable_payload_created": False,
            "account_binding_active": False,
            "credential_values_loaded": False,
            "platform_api_called": False,
            "scheduler_enabled": False,
            "approved_for_publication": False,
        }

        item_hash = _digest(raw_item)
        bundle_items.append(
            PlatformReviewBundleItem(
                packet_hash=item_hash,
                **raw_item
            )
        )

    checklist = build_bundle_checklist()
    safety = build_safety_flags()

    summary_counts = {
        "registered_renders_count": len(renders),
        "bundle_items_count": len(bundle_items),
        "global_blockers_count": len(blockers),
        "checklist_items_count": len(checklist)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers",
        "manual_review_export"
    ]

    missing_gates = [
        "lane_c_platform_review_bundle_operator_decision_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = PlatformPreviewDryRenderReviewBundlePacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        bundle_items=bundle_items,
        global_blockers=blockers,
        bundle_checklist=checklist,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_review_bundle_operator_decision_gate"
    )

    raw_packet = _asdict(packet)
    raw_packet.pop("packet_hash")
    packet_hash = _digest(raw_packet)

    final_packet = {
        "packet_hash": packet_hash,
        **raw_packet
    }
    return final_packet


def render_runbook(packet: dict[str, Any]) -> str:
    items = packet["bundle_items"]
    blockers = packet["global_blockers"]
    checklist = packet["bundle_checklist"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Platform Preview Dry Render to Review Bundle Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a dry render review bundle contract report for human inspection only.",
        "> It combines dry renders into a single bundle with disabled decision stubs and blockers.",
        "> It does not authorize approvals, does not perform dispatch, does not export, and does not schedule.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Invariant Flag | Required State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | ✅ |")

    lines.extend([
        "",
        "## Review Bundle Summary Counts",
        "",
        f"- **Source Dry Renders**: `{counts['registered_renders_count']}`",
        f"- **Bundle Items Registered**: `{counts['bundle_items_count']}`",
        f"- **Bundle-level Blockers**: `{counts['global_blockers_count']}`",
        f"- **Checklist Verification Items**: `{counts['checklist_items_count']}`",
        "",
        "## Blocked Capabilities & Missing Gates",
        "",
        "### Blocked Capabilities",
    ])

    for bc in blocked_caps:
        lines.append(f"- `{bc}`")

    lines.extend([
        "",
        "### Missing Future Gates",
    ])

    for mg in missing_gates:
        lines.append(f"- `{mg}`")

    lines.extend([
        "",
        "## Global Bundle Blocker Status",
        "",
        "| Blocker ID | Description | Active Status |",
        "|---|---|---|",
    ])

    for b in blockers:
        lines.append(f"| `{b['blocker_id']}` | {b['description']} | ✅ Active |")

    lines.extend([
        "",
        "## Bundle Checklist Items",
        "",
        "| Item ID | Description | Verification Status |",
        "|---|---|---|",
    ])

    for c in checklist:
        status_str = "✅ Passed" if c["passed"] else "❌ Pending"
        lines.append(f"| `{c['item_id']}` | {c['description']} | {status_str} |")

    lines.extend([
        "",
        "## Platform Review Bundle Items",
        "",
    ])

    for item in items:
        lines.extend([
            f"### Bundle Item: `{item['bundle_item_id']}`",
            "",
            f"- **Source Render ID**: `{item['source_render_id']}`",
            f"- **Platform Target ID**: `{item['platform_target_id']}`",
            f"- **Platform Family**: `{item['platform_family']}`",
            f"- **Review Surface Type**: `{item['review_surface_type']}`",
            f"- **Render Status**: `{item['render_status']}`",
            f"- **Bundle Status**: `{item['bundle_status']}`",
            f"- **Operator Review Required**: `{item['operator_review_required']}`",
            f"- **Manual Decision Required**: `{item['manual_decision_required']}`",
            f"- **Publishability Status**: `{item['publishability_status']}`",
            f"- **Citation Status**: `{item['citation_slot_status']}`",
            f"- **Limitation Status**: `{item['limitation_slot_status']}`",
            f"- **DQR Status**: `{item['dqr_status']}`",
            f"- **Readiness Status**: `{item['readiness_status']}`",
            f"- **Current Truth Status**: `{item['current_truth_status']}`",
            f"- **Account Binding Status**: `{item['account_binding_status']}`",
            f"- **Credential Gate Status**: `{item['credential_gate_status']}`",
            f"- **Payload Hash Lock Status**: `{item['payload_hash_lock_status']}`",
            f"- **Dispatch Gate Status**: `{item['dispatch_gate_status']}`",
            f"- **Review Note Placeholder**: `{item['review_notes_placeholder']}`",
            "",
            "#### Decision Stub Details",
            "",
            f"- **Decision Stub ID**: `{item['decision_stub']['decision_stub_id']}`",
            f"- **Decision Status**: `{item['decision_stub']['decision_status']}`",
            f"- **Approve Button Enabled**: `{item['decision_stub']['approve_button_enabled']}`",
            f"- **Reject Button Enabled**: `{item['decision_stub']['reject_button_enabled']}`",
            f"- **Request Revision Enabled**: `{item['decision_stub']['request_revision_enabled']}`",
            f"- **Publish Button Enabled**: `{item['decision_stub']['publish_button_enabled']}`",
            f"- **Dispatch Button Enabled**: `{item['decision_stub']['dispatch_button_enabled']}`",
            f"- **Operator Identity Bound**: `{item['decision_stub']['operator_identity_bound']}`",
            f"- **Approval Signature Present**: `{item['decision_stub']['approval_signature_present']}`",
            f"- **Payload Hash Locked**: `{item['decision_stub']['payload_hash_locked']}`",
            "",
        ])

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AP")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
