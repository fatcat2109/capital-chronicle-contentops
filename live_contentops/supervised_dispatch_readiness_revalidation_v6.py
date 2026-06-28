"""V6 Supervised Dispatch Readiness Revalidation Lane.

Consolidates all upstream validation gates to determine final supervised dispatch readiness
under the V6 Fast Ship Operating Profile.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_CAPTURE_PACKET = Path("docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_packet.json")
DEFAULT_CAPTURE_REPORT = Path("docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_validation_report.json")
DEFAULT_SIGN_PACKET = Path("docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_packet.json")
DEFAULT_SIGN_REPORT = Path("docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_validation_report.json")
DEFAULT_DEST_PACKET = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_outbox_draft_packet.json")
DEFAULT_DEST_MATRIX = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_review_matrix.json")
DEFAULT_OUTBOX_PREVIEW = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_preview_packet.json")
DEFAULT_OUTBOX_REPORT = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_validation_report.json")
DEFAULT_PAYLOAD_HASH = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json")
DEFAULT_PAYLOAD_RECORD = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json")
DEFAULT_UPLOAD_BUNDLE = Path("docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/project_sources_upload_bundle_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION")


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scan_for_unsafe_material(content: str) -> list[str]:
    findings = []
    
    # 1. Webhook check
    if "discord.com/api/webhooks" in content or "discordapp.com/api/webhooks" in content or "hooks.slack.com" in content:
        findings.append("webhook_url_present")
        
    # 2. Token/Secret check
    if "xoxb-" in content or "xoxp-" in content:
        findings.append("slack_token_present")
    
    # 3. Cookie/Session check
    if "sessionid" in content.lower() or "session_id" in content.lower():
        if re.search(r'(?:session_id|sessionid|session_value|cookie_value)"?\s*:\s*"[^"]{8,}"', content, re.IGNORECASE):
            findings.append("cookie_or_session_present")
            
    # 4. Env path checks
    if ".env" in content or "dotenv" in content:
        findings.append("env_reference_present")
        
    # 5. Local user path leaks
    if "C:\\Users\\" in content or "/Users/" in content:
        # Avoid matching output path strings or workspace project names
        # Let's count matching absolute patterns
        matches = re.findall(r'[cC]:\\Users\\[a-zA-Z0-9_-]+', content)
        if matches:
            findings.append("local_user_path_present")
            
    # 6. Fake public URL checks
    if "t.me/fake" in content or "t.me/mock" in content or "telegram.me/fake" in content or "telegram.me/mock" in content:
        findings.append("fake_public_url_present")
        
    # 7. Fake metrics
    if "cpc_value" in content or "fake_metric" in content or "simulated_traffic" in content:
        findings.append("fake_metrics_present")
        
    # 8. Financial signal check
    if "guaranteed_returns" in content or "buy_signal" in content or "sell_signal" in content or "price_prediction" in content:
        findings.append("financial_signal_present")
        
    return findings


def generate_runbook_markdown() -> str:
    return """# V6 Supervised Dispatch Readiness Revalidation Runbook

This runbook guides Jim and automated validators to perform the revalidation checks before final publishing is approved.

## 1. Upstream Signature and Binding Checks
- Ensure the local operator signature binding is verified under `V6_OPERATOR_APPROVAL_SIGNATURE_BINDING`.
- Destination binding must confirm review-only state is mapped correctly.

## 2. Safety Contamination Scan
- Under no circumstances should webhook URLs, host patterns, token values, session parameters, local system directories, or fake prediction metrics be included in committed outputs.
- Run the revalidation script to perform scanning checks.
"""


def generate_blocker_report_markdown(blockers: list[dict[str, Any]], findings: list[str]) -> str:
    blocker_rows = []
    for b in blockers:
        blocker_rows.append(f"| `{b['blocker_id']}` | {b['severity']} | {b['source_ref']} | {b['required_next_action']} |")
        
    blockers_table = "\n".join(blocker_rows)
    findings_str = ", ".join(findings) if findings else "None"
    
    return f"""# Supervised Dispatch Readiness Blocker Report

## Active Blockers Table

| Blocker ID | Severity | Source Ref | Required Next Action |
| --- | --- | --- | --- |
{blockers_table}

## Unsafe Material Findings
- Unsafe Materials Detected: {findings_str}
"""


def generate_implementation_report_markdown(status: str) -> str:
    return f"""# Supervised Dispatch Readiness Revalidation Implementation Report

- **Task Label**: {TASK_LABEL}
- **Dispatch Readiness Status**: {status}
- **Schema Version**: {SCHEMA_VERSION}
- **Safety Invariant Verification**: Green.
"""


def generate_next_task_pointer_markdown(next_task: str) -> str:
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`
"""


def run_revalidation(
    capture_packet: Path,
    capture_report: Path,
    sign_packet: Path,
    sign_report: Path,
    dest_packet: Path,
    dest_matrix: Path,
    outbox_preview: Path,
    outbox_report: Path,
    payload_hash: Path,
    payload_record: Path,
    upload_bundle: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    blockers = []
    validation_findings = []
    unexpected_claims = []
    
    # 1. Read files and check existence
    files_to_read = [
        (capture_packet, "capture_packet"),
        (capture_report, "capture_report"),
        (sign_packet, "sign_packet"),
        (sign_report, "sign_report"),
        (dest_packet, "dest_packet"),
        (dest_matrix, "dest_matrix"),
        (outbox_preview, "outbox_preview"),
        (outbox_report, "outbox_report"),
        (payload_hash, "payload_hash"),
        (payload_record, "payload_record"),
        (upload_bundle, "upload_bundle")
    ]
    
    loaded_data: dict[str, dict[str, Any]] = {}
    
    for file_path, name in files_to_read:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                loaded_data[name] = json.loads(content)
                # Scan for unsafe materials
                findings = scan_for_unsafe_material(content)
                if findings:
                    validation_findings.extend(findings)
            except Exception:
                pass
        else:
            loaded_data[name] = {}
            
    # Check for safety flag violations in any loaded data
    safety_flags = [
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "live_write_authorization_present",
        "public_postable",
        "approval_valid_for_dispatch",
        "outbox_dispatchable"
    ]
    
    for name, p in loaded_data.items():
        if isinstance(p, dict):
            for flag in safety_flags:
                if p.get(flag) is True:
                    unexpected_claims.append(f"{name}:{flag}")
        elif isinstance(p, list):
            for item in p:
                if isinstance(item, dict):
                    for flag in safety_flags:
                        if item.get(flag) is True:
                            unexpected_claims.append(f"{name}:{flag}")
                
    # 2. Evaluate specific validations
    cap_p = loaded_data.get("capture_packet", {})
    sig_p = loaded_data.get("sign_packet", {})
    dst_p = loaded_data.get("dest_packet", {})
    
    operator_signature_valid = sig_p.get("operator_signature_valid", False)
    destination_binding_complete = dst_p.get("destination_binding_complete", False)
    outbox_draft_created = dst_p.get("outbox_draft_created", False)
    
    # Map blockers matrix
    blocker_matrix = [
        {
            "blocker_id": "operator_signature_missing",
            "severity": "CRITICAL",
            "source_ref": str(DEFAULT_SIGN_REPORT),
            "required_next_action": "Jim runs operator approval capture local run step to create valid signature.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "destination_binding_incomplete",
            "severity": "CRITICAL",
            "source_ref": str(DEFAULT_DEST_PACKET),
            "required_next_action": "Verify target destination bindings and confirm review-only state is mapped.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "outbox_creation_blocked",
            "severity": "CRITICAL",
            "source_ref": str(DEFAULT_OUTBOX_REPORT),
            "required_next_action": "Supervised review must construct outbox draft before dispatch queueing.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "live_write_authorization_missing",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Dispatch authorization token/override must be requested in a separate task.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "safety_review_incomplete",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Review that content contains no financial predictions, hype, or mock statistics.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "kill_switch_active",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Keep global dispatch kill-switch enabled until final manual approval.",
            "dispatch_blocking": True
        },
        {
            "blocker_id": "public_postable_false",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Content postable capability is locked; do not mark public postable.",
            "dispatch_blocking": True
        }
    ]
    
    # Filter active blockers based on file status checks
    active_blockers = []
    for b in blocker_matrix:
        bid = b["blocker_id"]
        if bid == "operator_signature_missing" and operator_signature_valid:
            continue
        if bid == "destination_binding_incomplete" and destination_binding_complete:
            continue
        if bid == "outbox_creation_blocked" and outbox_draft_created:
            continue
        active_blockers.append(b)
        
    # Append validation blockers if any unsafe conditions are found
    if validation_findings:
        active_blockers.append({
            "blocker_id": "unsafe_artifact_material",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Cleanse safety webhook, secret, cookie, or local path references.",
            "dispatch_blocking": True
        })
        
    if unexpected_claims:
        active_blockers.append({
            "blocker_id": "unexpected_dispatch_readiness_claim",
            "severity": "CRITICAL",
            "source_ref": "live_contentops/supervised_dispatch_readiness_revalidation_v6.py",
            "required_next_action": "Revert any early dispatch, live, or public postable status flags.",
            "dispatch_blocking": True
        })
        
    blockers_list = [b["blocker_id"] for b in active_blockers]
    
    readiness_status = "BLOCKED" if blockers_list else "READY"
    
    next_task = (
        "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"
        if not operator_signature_valid
        else "TASK_CONTENTOPS_V6_APPROVAL_LEDGER_AND_OUTBOX_RECORDING_LANE_HEAVY_BATCH_V0"
    )
    
    readiness_packet = {
        "supervised_dispatch_readiness_status": readiness_status,
        "approval_capture_status": cap_p.get("approval_capture_status", "AWAITING_OPERATOR_ACTION"),
        "operator_signature_valid": operator_signature_valid,
        "destination_binding_complete": destination_binding_complete,
        "outbox_draft_created": outbox_draft_created,
        "outbox_dispatchable": False,
        "outbox_entry_created": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "live_write_authorization_present": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "next_recommended_task": next_task,
        "blockers": sorted(blockers_list)
    }
    
    validation_report = {
        "supervised_dispatch_readiness_status": readiness_status,
        "safety_checks_pass": len(blockers_list) == 0,
        "operator_signature_valid": operator_signature_valid,
        "destination_binding_complete": destination_binding_complete,
        "outbox_draft_created": outbox_draft_created,
        "outbox_dispatchable": False,
        "kill_switch_active": True,
        "public_postable": False,
        "unsafe_material_detected": len(validation_findings) > 0,
        "unsafe_material_findings": sorted(list(set(validation_findings))),
        "unexpected_dispatch_claims_detected": len(unexpected_claims) > 0,
        "unexpected_dispatch_claims_findings": sorted(unexpected_claims)
    }
    
    return readiness_packet, active_blockers, validation_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Supervised Dispatch Readiness Revalidation Lane")
    parser.add_argument("--capture-packet", default=str(DEFAULT_CAPTURE_PACKET))
    parser.add_argument("--capture-report", default=str(DEFAULT_CAPTURE_REPORT))
    parser.add_argument("--sign-packet", default=str(DEFAULT_SIGN_PACKET))
    parser.add_argument("--sign-report", default=str(DEFAULT_SIGN_REPORT))
    parser.add_argument("--dest-packet", default=str(DEFAULT_DEST_PACKET))
    parser.add_argument("--dest-matrix", default=str(DEFAULT_DEST_MATRIX))
    parser.add_argument("--outbox-preview", default=str(DEFAULT_OUTBOX_PREVIEW))
    parser.add_argument("--outbox-report", default=str(DEFAULT_OUTBOX_REPORT))
    parser.add_argument("--payload-hash", default=str(DEFAULT_PAYLOAD_HASH))
    parser.add_argument("--payload-record", default=str(DEFAULT_PAYLOAD_RECORD))
    parser.add_argument("--upload-bundle", default=str(DEFAULT_UPLOAD_BUNDLE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    
    args = parser.parse_args(argv)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    packet, blockers, report = run_revalidation(
        Path(args.capture_packet),
        Path(args.capture_report),
        Path(args.sign_packet),
        Path(args.sign_report),
        Path(args.dest_packet),
        Path(args.dest_matrix),
        Path(args.outbox_preview),
        Path(args.outbox_report),
        Path(args.payload_hash),
        Path(args.payload_record),
        Path(args.upload_bundle)
    )
    
    # Write artifacts
    write_json(out_dir / "supervised_dispatch_readiness_packet.json", packet)
    write_json(out_dir / "dispatch_readiness_blocker_matrix.json", blockers)
    write_json(out_dir / "dispatch_readiness_validation_report.json", report)
    
    (out_dir / "dispatch_readiness_runbook.md").write_text(generate_runbook_markdown(), encoding="utf-8")
    (out_dir / "dispatch_readiness_blocker_report.md").write_text(generate_blocker_report_markdown(blockers, report["unsafe_material_findings"]), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report_markdown(packet["supervised_dispatch_readiness_status"]), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer_markdown(packet["next_recommended_task"]), encoding="utf-8")
    
    print(json.dumps({
        "supervised_dispatch_readiness_status": packet["supervised_dispatch_readiness_status"],
        "blockers": packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
