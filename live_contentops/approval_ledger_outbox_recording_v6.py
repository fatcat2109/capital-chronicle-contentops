"""V6 Approval Ledger and Outbox Recording Lane.

Consolidates signature binding and supervised dispatch readiness to prepare inert
previews of the approval ledger entries and outbox records.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_APPROVAL_LEDGER_AND_OUTBOX_RECORDING_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_SIGN_PACKET = Path("docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_packet.json")
DEFAULT_READINESS_PACKET = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/supervised_dispatch_readiness_packet.json")
DEFAULT_HASH_RECORD = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json")
DEFAULT_PREVIEW_EXACT = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING")


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
        
    # 2. Token check
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
    return """# V6 Approval Ledger & Outbox Recording Runbook

This runbook guides Jim and automated validators to verify inert ledger and outbox previews before final commit.

## 1. Local Signature Binding Verification
- Confirm that the local operator signature matches the payload hash.
- Ensure supervised dispatch readiness has no blockers before commits are made.

## 2. Validation Scanning
- Confirm no credentials, secret cookies, webhooks, or local user paths exist.
"""


def generate_blocker_report_markdown(blockers: list[str], findings: list[str]) -> str:
    blockers_str = ", ".join(f"`{b}`" for b in blockers) if blockers else "None"
    findings_str = ", ".join(findings) if findings else "None"
    return f"""# Approval Ledger & Outbox Recording Blocker Report

- **Active Blockers**: {blockers_str}
- **Unsafe Material Detected**: {findings_str}
"""


def generate_implementation_report_markdown(status: str) -> str:
    return f"""# Approval Ledger & Outbox Recording Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: {status}
- **Schema Version**: {SCHEMA_VERSION}
"""


def generate_next_task_pointer_markdown(next_task: str) -> str:
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`
"""


def run_recording(
    sign_packet_path: Path,
    readiness_packet_path: Path,
    hash_record_path: Path,
    preview_exact_path: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    blockers = []
    validation_findings = []
    unexpected_claims = []
    
    # 1. Read files and check existence
    files_to_read = [
        (sign_packet_path, "sign_packet"),
        (readiness_packet_path, "readiness_packet"),
        (hash_record_path, "hash_record"),
        (preview_exact_path, "preview_exact")
    ]
    
    loaded_data: dict[str, dict[str, Any]] = {}
    
    for file_path, name in files_to_read:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                loaded_data[name] = json.loads(content)
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
        "outbox_dispatchable",
        "valid_for_dispatch"
    ]
    
    for name, p in loaded_data.items():
        for flag in safety_flags:
            if p.get(flag) is True:
                unexpected_claims.append(f"{name}:{flag}")
                
    sig_p = loaded_data.get("sign_packet", {})
    read_p = loaded_data.get("readiness_packet", {})
    hash_p = loaded_data.get("hash_record", {})
    
    operator_signature_valid = sig_p.get("operator_signature_valid", False)
    supervised_readiness_status = read_p.get("supervised_dispatch_readiness_status", "BLOCKED")
    payload_hash = hash_p.get("payload_hash", "")
    
    # Evaluate blockers
    if not operator_signature_valid:
        blockers.append("operator_signature_missing")
        
    if supervised_readiness_status == "BLOCKED":
        blockers.extend(read_p.get("blockers", []))
        
    if validation_findings:
        blockers.append("unsafe_artifact_material")
        
    if unexpected_claims:
        blockers.append("unexpected_dispatch_readiness_claim")
        
    blockers = sorted(list(set(blockers)))
    
    status = "BLOCKED_AWAITING_OPERATOR_SIGNATURE" if blockers else "DRAFT_READY_FOR_REVIEW"
    
    # 2. Build Previews
    ledger_preview = {
        "ledger_entry_preview_created": True,
        "ledger_entry_committed": False,
        "operator_signature_required": True,
        "operator_signature_valid": operator_signature_valid,
        "payload_hash": payload_hash,
        "payload_preview_ref": str(preview_exact_path),
        "approval_decision_source": "local_operator_signature_required",
        "valid_for_dispatch": False,
        "ledger_mutation_allowed": False,
        "immutable_audit_required_later": True
    }
    
    outbox_preview = {
        "outbox_record_preview_created": True,
        "outbox_record_created": False,
        "dispatchable": False,
        "platform_family": "telegram",
        "destination_class": "operator_review_only",
        "live_destination_bound": False,
        "destination_identifier_redacted_or_absent": True,
        "credential_hydrated": False,
        "dispatch_adapter_enabled": False,
        "manual_fallback_required": True,
        "public_url": None,
        "metrics": None
    }
    
    next_task = (
        "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"
        if not operator_signature_valid
        else "TASK_CONTENTOPS_V6_APPROVAL_LEDGER_AND_OUTBOX_RECORDING_LANE_HEAVY_BATCH_V0"
    )
    
    dst_p_dict = loaded_data.get("dest_packet", {})
    dst_complete = dst_p_dict.get("destination_binding_complete", False) if dst_p_dict else False

    packet = {
        "approval_ledger_outbox_status": status,
        "approval_ledger_entry_created": False,
        "outbox_record_created": False,
        "outbox_entry_created": False,
        "outbox_dispatchable": False,
        "operator_signature_valid": operator_signature_valid,
        "supervised_dispatch_readiness_status": supervised_readiness_status,
        "destination_binding_complete": dst_complete,
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
        "blockers": blockers
    }
    
    ledger_report = {
        "ledger_entry_preview_created": True,
        "ledger_entry_committed": False,
        "safety_checks_pass": len(blockers) == 0,
        "operator_signature_valid": operator_signature_valid,
        "unsafe_material_detected": len(validation_findings) > 0,
        "unsafe_material_findings": sorted(list(set(validation_findings))),
        "unexpected_claims_detected": len(unexpected_claims) > 0,
        "unexpected_claims_findings": sorted(unexpected_claims)
    }
    
    outbox_report = {
        "outbox_record_preview_created": True,
        "outbox_record_created": False,
        "dispatchable": False,
        "safety_checks_pass": len(blockers) == 0,
        "destination_class": "operator_review_only",
        "live_destination_bound": False,
        "credential_hydrated": False
    }
    
    return packet, ledger_preview, outbox_preview, ledger_report, outbox_report, blockers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Approval Ledger and Outbox Recording Lane")
    parser.add_argument("--sign-packet", default=str(DEFAULT_SIGN_PACKET))
    parser.add_argument("--readiness-packet", default=str(DEFAULT_READINESS_PACKET))
    parser.add_argument("--hash-record", default=str(DEFAULT_HASH_RECORD))
    parser.add_argument("--preview-exact", default=str(DEFAULT_PREVIEW_EXACT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    
    args = parser.parse_args(argv)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    packet, ledger_preview, outbox_preview, ledger_report, outbox_report, blockers = run_recording(
        Path(args.sign_packet),
        Path(args.readiness_packet),
        Path(args.hash_record),
        Path(args.preview_exact)
    )
    
    # Write json files
    write_json(out_dir / "approval_ledger_outbox_packet.json", packet)
    write_json(out_dir / "approval_ledger_entry_preview.json", ledger_preview)
    write_json(out_dir / "outbox_record_preview.json", outbox_preview)
    write_json(out_dir / "approval_ledger_validation_report.json", ledger_report)
    write_json(out_dir / "outbox_record_validation_report.json", outbox_report)
    
    # Write md files
    (out_dir / "approval_ledger_outbox_blocker_report.md").write_text(
        generate_blocker_report_markdown(blockers, ledger_report["unsafe_material_findings"]), encoding="utf-8"
    )
    (out_dir / "approval_ledger_outbox_runbook.md").write_text(generate_runbook_markdown(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report_markdown(packet["approval_ledger_outbox_status"]), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer_markdown(packet["next_recommended_task"]), encoding="utf-8")
    
    print(json.dumps({
        "approval_ledger_outbox_status": packet["approval_ledger_outbox_status"],
        "blockers": packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
