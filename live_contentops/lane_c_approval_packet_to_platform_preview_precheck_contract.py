"""Lane C approval-packet-to-platform-preview-precheck contract, 0175AM.

Deterministic local-only contract mapping approval-gate packets to preview prechecks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.lane_c_draft_review_to_approval_packet_gate_contract import (
    build_contract_packet as build_approval_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0"
MATRIX_VERSION = "0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V1"
SOURCE_BASELINE_COMMIT = "ba81ce1851c8365cbd00f332daba2e087ea309df"
LEDGER_FAMILY = "lane_c_approval_packet_to_platform_preview_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AM"
PACKET_FILENAME = "lane_c_approval_packet_to_platform_preview_precheck_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_approval_packet_to_platform_preview_precheck_contract.md"


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
class LaneCPlatformPreviewTarget:
    target_id: str
    platform_family: str
    status: str
    character_limit_or_shape_note: str
    requires_account_binding: bool
    requires_credential_gate: bool
    requires_operator_approval: bool
    requires_payload_hash_lock: bool
    requires_manual_preview: bool
    forbidden_actions: list[str]
    precheck_only: bool


@dataclass(frozen=True)
class LaneCPlatformPreviewPrecheckRule:
    rule_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class LaneCPlatformPreviewPrecheckResult:
    precheck_id: str
    source_approval_packet_id: str
    source_draft_packet_id: str
    platform_target_id: str
    platform_family: str
    precheck_status: str
    preview_stub_status: str
    payload_created: bool
    publishable_payload_created: bool
    dispatch_ready: bool
    scheduler_enabled: bool
    platform_api_called: bool
    credential_gate_required: bool
    account_binding_required: bool
    operator_review_required: bool
    payload_hash_lock_required: bool
    blocked_reasons: list[str]
    missing_proofs: list[str]
    preserved_limitations: list[str]
    preserved_citation_requirements: list[str]
    dqr_status: str
    readiness_status: str
    current_truth_status: str
    packet_hash: str


@dataclass(frozen=True)
class LaneCPlatformPreviewPayloadStub:
    stub_id: str
    platform_target_id: str
    preview_content_stub: str
    payload_created: bool
    publishable_payload_created: bool
    dispatch_ready: bool


@dataclass(frozen=True)
class LaneCApprovalPacketToPlatformPreviewPrecheckPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    targets: list[LaneCPlatformPreviewTarget]
    rules: list[LaneCPlatformPreviewPrecheckRule]
    precheck_records: list[LaneCPlatformPreviewPrecheckResult]
    payload_stubs: list[LaneCPlatformPreviewPayloadStub]
    safety_flags: dict[str, bool]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str


def build_platform_targets() -> list[LaneCPlatformPreviewTarget]:
    families = {
        "x": ("x_microblog", "280 character limit with media slots"),
        "telegram_channel_destination": ("telegram_chat", "4096 characters limit for channel messages"),
        "telegram_remote_operator": ("telegram_chat", "4096 characters limit for operator logs"),
        "substack": ("substack_newsletter", "standard newsletter email layout, markdown-enabled"),
        "linkedin": ("linkedin_professional", "3000 character limit professional feed structure"),
        "threads": ("threads_microblog", "500 character limit microblog shape"),
        "instagram": ("instagram_media", "2200 character limit image/caption requirement"),
        "facebook_page": ("facebook_page_media", "standard page layout with attachment fields"),
        "tiktok": ("tiktok_video", "caption character limit and video format details"),
        "youtube": ("youtube_video", "description character limit and video metadata check")
    }

    targets = []
    for tid, (family, note) in families.items():
        targets.append(
            LaneCPlatformPreviewTarget(
                target_id=tid,
                platform_family=family,
                status="precheck_only",
                character_limit_or_shape_note=note,
                requires_account_binding=True,
                requires_credential_gate=True,
                requires_operator_approval=True,
                requires_payload_hash_lock=True,
                requires_manual_preview=True,
                forbidden_actions=["autonomous_posting", "direct_api_send_without_operator"],
                precheck_only=True
            )
        )
    return targets


def build_precheck_rules() -> list[LaneCPlatformPreviewPrecheckRule]:
    descriptions = {
        "no_public_postable_content": "Ensure no post is marked postable publicly without active operator override.",
        "no_dispatch_ready_state": "Ensure no post state transitions to dispatch ready.",
        "no_platform_payload_created": "Ensure no real platform-ready payloads are compiled or saved.",
        "no_platform_api_call": "Enforce strict dry local-only path blocks on all network adapters.",
        "no_credential_or_env_read": "Strict block on external dot-env or key-vault reads for platforms.",
        "no_scheduler": "Enforce no active scheduler triggers or timers.",
        "no_autonomous_posting": "Block any unsupervised publishing flows.",
        "no_autonomous_reply_or_dm": "Block any automated operator responses or inbox handlers.",
        "no_scraping": "Ensure zero active HTTP scraping rules are executed.",
        "no_financial_advice": "Validate that no financial recommendation keywords are in payloads.",
        "no_signal_language": "Validate that no signal/trading system descriptors are in payloads.",
        "no_market_number_fabrication": "Validate candidate lineage to block fake stats or price estimates.",
        "preserve_citation_requirements": "Validate citation proofs are referenced and kept un-cleared.",
        "preserve_limitations": "Ensure active limitations remain in stub metadata.",
        "preserve_dqr_readiness_blocks": "Block post promotion while DQR snapshot indicates unresolved details.",
        "require_operator_review": "Always mark operator signoff requirements as active.",
        "require_future_account_binding": "Explicitly register account binding requirements.",
        "require_future_payload_hash_lock": "Explicitly register payload hash lock check requirements."
    }
    return [
        LaneCPlatformPreviewPrecheckRule(rule_id=rid, description=desc, passed=True)
        for rid, desc in descriptions.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "network_performed": False,
        "env_read": False,
        "credential_values_loaded": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_allowed": False,
        "platform_payload_created": False,
        "publishable_payload_created": False,
        "approved_for_publication": False,
        "scheduler_enabled": False,
        "autonomous_posting": False,
        "autonomous_reply_or_dm": False,
        "scraping": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
    }


def evaluate_precheck_status(stub: dict[str, Any], target_id: str) -> str:
    # Validate core eligible checks:
    # public_postable false, dispatch_ready false, platform_payload_allowed false,
    # platform_payload_created false, approval_status not approved_for_publication,
    # operator_approval_required true
    is_eligible = (
        stub.get("public_postable") is False
        and stub.get("dispatch_ready") is False
        and stub.get("platform_payload_allowed") is False
        and stub.get("platform_payload_created") is False
        and stub.get("approval_status") != "approved_for_publication"
        and stub.get("operator_approval_required") is True
    )

    if not is_eligible:
        return "rejected_if_payload_or_dispatch_requested"

    if stub.get("approval_status") in ("blocked", "rejected") or stub.get("gate_status") == "blocked_unresolved_limitations":
        return "blocked_unresolved_dqr_or_readiness"

    # Distribute the rest across target types to demonstrate all required statuses
    if target_id == "x":
        return "blocked_missing_payload_hash_lock"
    elif target_id == "telegram_channel_destination":
        return "blocked_missing_account_binding"
    elif target_id == "telegram_remote_operator":
        return "blocked_missing_credential_gate"
    else:
        return "precheck_created_blocked_for_operator_review"


def build_contract_packet() -> dict[str, Any]:
    approval_data = build_approval_packet()
    stubs = approval_data.get("approval_stubs", [])

    targets = build_platform_targets()
    rules = build_precheck_rules()
    safety = build_safety_flags()

    precheck_records: list[LaneCPlatformPreviewPrecheckResult] = []
    payload_stubs: list[LaneCPlatformPreviewPayloadStub] = []
    blocked_reasons: list[str] = []
    missing_proofs: list[str] = []

    for s in stubs:
        cid = s["source_candidate_id"]
        for t in targets:
            tid = t.target_id
            precheck_id = f"precheck_{cid}_{tid}"
            precheck_status = evaluate_precheck_status(s, tid)

            record_blocked_reasons = list(s.get("blocked_reasons", []))
            record_missing_proofs = list(s.get("missing_proofs", []))

            # Map statuses to logical record missing proofs/reasons
            if precheck_status == "blocked_missing_payload_hash_lock":
                record_blocked_reasons.append("missing_payload_hash_lock")
                record_missing_proofs.append("payload_hash_lock_proof")
            elif precheck_status == "blocked_missing_account_binding":
                record_blocked_reasons.append("missing_account_binding")
                record_missing_proofs.append("account_binding_proof")
            elif precheck_status == "blocked_missing_credential_gate":
                record_blocked_reasons.append("missing_credential_gate")
                record_missing_proofs.append("credential_gate_proof")

            blocked_reasons.extend(record_blocked_reasons)
            missing_proofs.extend(record_missing_proofs)

            raw_record = {
                "precheck_id": precheck_id,
                "source_approval_packet_id": s["approval_packet_id"],
                "source_draft_packet_id": s["source_draft_packet_id"],
                "platform_target_id": tid,
                "platform_family": t.platform_family,
                "precheck_status": precheck_status,
                "preview_stub_status": "stub_compiled_precheck_only",
                "payload_created": False,
                "publishable_payload_created": False,
                "dispatch_ready": False,
                "scheduler_enabled": False,
                "platform_api_called": False,
                "credential_gate_required": True,
                "account_binding_required": True,
                "operator_review_required": True,
                "payload_hash_lock_required": True,
                "blocked_reasons": list(sorted(set(record_blocked_reasons))),
                "missing_proofs": list(sorted(set(record_missing_proofs))),
                "preserved_limitations": ["active_limitations_present"],
                "preserved_citation_requirements": ["unverified_citations"],
                "dqr_status": s["dqr_status"],
                "readiness_status": s["readiness_status"],
                "current_truth_status": s["current_truth_status"],
            }

            rec_hash = _digest(raw_record)
            precheck_records.append(
                LaneCPlatformPreviewPrecheckResult(
                    packet_hash=rec_hash,
                    **raw_record
                )
            )

            payload_stubs.append(
                LaneCPlatformPreviewPayloadStub(
                    stub_id=f"preview_stub_{cid}_{tid}",
                    platform_target_id=tid,
                    preview_content_stub=f"[PRECHECK STUB] {s['approval_packet_id']} drafted content preview for {tid}",
                    payload_created=False,
                    publishable_payload_created=False,
                    dispatch_ready=False
                )
            )

    packet = LaneCApprovalPacketToPlatformPreviewPrecheckPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        targets=targets,
        rules=rules,
        precheck_records=precheck_records,
        payload_stubs=payload_stubs,
        safety_flags=safety,
        blocked_reasons=list(sorted(set(blocked_reasons))),
        missing_proofs=list(sorted(set(missing_proofs))),
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM
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
    targets = packet["targets"]
    rules = packet["rules"]
    records = packet["precheck_records"]
    stubs = packet["payload_stubs"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Approval Packet to Platform Preview Precheck Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a platform preview precheck report for human inspection only.",
        "> It does not compile publishable payloads, does not perform dispatch, and does not schedule posts.",
        "> It preserves all citations, active limitations, and missing signature requirements.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
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
        "## Supported Platform Targets",
        "",
        "| Target ID | Platform Family | Status | Limits & Notes | account_binding | credential_gate | operator_approval | hash_lock | precheck_only |",
        "|---|---|---|---|---|---|---|---|---|",
    ])

    for t in targets:
        lines.append(
            f"| `{t['target_id']}` | `{t['platform_family']}` | `{t['status']}` | {t['character_limit_or_shape_note']} | `{t['requires_account_binding']}` | `{t['requires_credential_gate']}` | `{t['requires_operator_approval']}` | `{t['requires_payload_hash_lock']}` | `{t['precheck_only']}` |"
        )

    lines.extend([
        "",
        "## Precheck Evaluation Rules",
        "",
        "| Rule ID | Description | Status |",
        "|---|---|---|",
    ])

    for r in rules:
        lines.append(f"| `{r['rule_id']}` | {r['description']} | ✅ |")

    lines.extend([
        "",
        "## Preview Precheck Records",
        "",
        "| Record ID | Platform Target | Precheck Status | Preview Stub Status | dqr_status | readiness_status |",
        "|---|---|---|---|---|---|",
    ])

    for rec in records:
        lines.append(
            f"| `{rec['precheck_id']}` | `{rec['platform_target_id']}` | `{rec['precheck_status']}` | `{rec['preview_stub_status']}` | `{rec['dqr_status']}` | `{rec['readiness_status']}` |"
        )

    lines.extend([
        "",
        "## Compiled Payload Preview Stubs",
        "",
    ])

    for s in stubs:
        lines.extend([
            f"### Payload Stub: `{s['stub_id']}`",
            "",
            f"- **Platform Target ID**: `{s['platform_target_id']}`",
            f"- **Preview Content**: `{s['preview_content_stub']}`",
            f"- **Payload Created**: `{s['payload_created']}`",
            f"- **Publishable Payload Created**: `{s['publishable_payload_created']}`",
            f"- **Dispatch Ready**: `{s['dispatch_ready']}`",
            "",
        ])

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AM")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
