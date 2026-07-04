"""V5 manual pilot trail reconciliation audit contract for ContentOps 0175AA.

This contract implements a deterministic, local-only audit verifier for the
full manual pilot trail chain: 0174UW, 0174UY, and 0174UZ. It operates completely
locally and read-only, without credentials, network, or live action capability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175AA_MANUAL_PILOT_TRAIL_RECONCILIATION_AUDIT_V0"
CONTRACT_VERSION = "0175AA_V5_MANUAL_PILOT_TRAIL_RECONCILIATION_AUDIT_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "77c4dc546dcd0fba91879ccb7db66a64407ceae4"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AA"
PACKET_FILENAME = "v5_manual_pilot_trail_reconciliation_audit_contract_packet.json"
RUNBOOK_FILENAME = "v5_manual_pilot_trail_reconciliation_audit_contract.md"
AUDIT_FAMILY = "v5_manual_pilot_trail_reconciliation_audit_future"

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
    """Recursively walks a nested data structure checking for banned keywords."""
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


def run_audit(repo_root: Path) -> dict[str, Any]:
    """Reads packets and executes audit verification. Returns verification details."""
    uw_path = repo_root / "docs" / "automation" / "0174UW" / "v5_manual_export_pilot_verification_contract_packet.json"
    uy_path = repo_root / "docs" / "automation" / "0174UY" / "v5_operator_review_queue_manual_pilot_trail_contract_packet.json"
    uz_path = repo_root / "docs" / "automation" / "0174UZ" / "v5_manual_pilot_trail_reconciliation_contract_packet.json"

    uw = load_json_packet(uw_path)
    uy = load_json_packet(uy_path)
    uz = load_json_packet(uz_path)

    # Track missing files
    missing_packets = []
    if not uw:
        missing_packets.append("0174UW")
    if not uy:
        missing_packets.append("0174UY")
    if not uz:
        missing_packets.append("0174UZ")

    # Invariant checks dict
    invariants = {
        "uw_exists_and_manual_only": False,
        "uy_references_uw_correctly": False,
        "uz_references_uy_and_uw_correctly": False,
        "placeholders_remain_empty": False,
        "missing_evidence_fields_correct": False,
        "reconciliation_status_blocked_only": False,
        "public_postable_false": False,
        "dispatch_ready_false": False,
        "approval_mutation_false": False,
        "credential_values_loaded_false": False,
        "network_performed_false": False,
        "disabled_live_action_states_correct": False,
        "no_pretend_evidence": False,
        "no_banned_financial_language": False,
    }

    blocked_reasons = []
    contradictions = []

    # 1. 0174UW manual export exists and is manual-only
    if uw:
        local_only = uw.get("safety_flags", {}).get("local_only")
        manual_export = uw.get("safety_flags", {}).get("manual_export_only")
        pilot_only = uw.get("safety_flags", {}).get("pilot_verification_only")
        if local_only and manual_export and pilot_only:
            invariants["uw_exists_and_manual_only"] = True
        else:
            contradictions.append("0174UW safety_flags do not specify manual-only / pilot-only state")

    # 2. 0174UY operator review queue references 0174UW correctly
    if uy:
        # According to design spec, UY refers to 0174UW hash reference as "277fb7d44b247efc6021f038e362256f746cc039"
        ref_hash = uy.get("source_manual_export_packet_hash")
        if ref_hash == "277fb7d44b247efc6021f038e362256f746cc039":
            invariants["uy_references_uw_correctly"] = True
        else:
            contradictions.append(f"0174UY source_manual_export_packet_hash '{ref_hash}' is incorrect")

    # 3. 0174UZ reconciliation references 0174UY and 0174UW correctly
    if uz and uy:
        ref_uw = uz.get("source_manual_export_packet_hash")
        ref_uy_hash = uz.get("source_operator_review_packet_hash")
        ref_uy_qid = uz.get("source_operator_review_queue_id")

        match_uw = ref_uw == "277fb7d44b247efc6021f038e362256f746cc039"
        match_uy_hash = ref_uy_hash == uy.get("packet_hash")
        match_uy_qid = ref_uy_qid == uy.get("queue_id")

        if match_uw and match_uy_hash and match_uy_qid:
            invariants["uz_references_uy_and_uw_correctly"] = True
        else:
            if not match_uw:
                contradictions.append(f"0174UZ source_manual_export_packet_hash '{ref_uw}' is incorrect")
            if not match_uy_hash:
                contradictions.append(f"0174UZ source_operator_review_packet_hash '{ref_uy_hash}' does not match UY hash '{uy.get('packet_hash')}'")
            if not match_uy_qid:
                contradictions.append(f"0174UZ source_operator_review_queue_id '{ref_uy_qid}' does not match UY queue_id '{uy.get('queue_id')}'")

    # 4 & 13. Placeholders remain empty & no pretend evidence
    placeholders_empty = True
    no_pretend_evidence = True

    if uw:
        # Check empty placeholders in 0174UW
        url_placeholder = uw.get("manual_publish_url_placeholder", {})
        metrics_placeholder = uw.get("manual_metrics_placeholder", {})
        sig_placeholder = uw.get("review_signature_placeholder", {})

        if url_placeholder.get("value") != "":
            placeholders_empty = False
            no_pretend_evidence = False
            contradictions.append("0174UW manual_publish_url_placeholder has a value")
        if metrics_placeholder.get("value") != "":
            placeholders_empty = False
            no_pretend_evidence = False
            contradictions.append("0174UW manual_metrics_placeholder has a value")
        if sig_placeholder.get("signature_value") != "":
            placeholders_empty = False
            no_pretend_evidence = False
            contradictions.append("0174UW review_signature_placeholder has a signature_value")

    if uy:
        # Check empty placeholders in 0174UY
        placeholders = uy.get("manual_publish_placeholders", [])
        for i, pl in enumerate(placeholders):
            if pl.get("value") != "":
                placeholders_empty = False
                no_pretend_evidence = False
                contradictions.append(f"0174UY manual_publish_placeholder index {i} has a value")

    if uz:
        # Check empty placeholders in 0174UZ
        placeholder_fields = uz.get("placeholder_fields", [])
        for pl in placeholder_fields:
            field_id = pl.get("field_id")
            val = pl.get("value")
            if val != "":
                placeholders_empty = False
                # If these fields contain fake values that pretend to be evidence, it violates invariant 13
                # (e.g. if field is platform_post_id or platform_permalink or manual_publish_url)
                if field_id in ("manual_publish_url", "manual_publish_timestamp", "manual_metrics_snapshot", "platform_post_id", "platform_permalink"):
                    no_pretend_evidence = False
                contradictions.append(f"0174UZ placeholder field '{field_id}' has a value '{val}'")

    if uw or uy or uz:
        invariants["placeholders_remain_empty"] = placeholders_empty
        invariants["no_pretend_evidence"] = no_pretend_evidence

    # 5. Missing evidence includes manual_publish_url, manual_publish_timestamp, manual_metrics_snapshot
    if uz:
        missing = uz.get("missing_evidence", [])
        required_missing = {"manual_publish_url", "manual_publish_timestamp", "manual_metrics_snapshot"}
        if required_missing.issubset(set(missing)):
            invariants["missing_evidence_fields_correct"] = True
        else:
            contradictions.append(f"0174UZ missing_evidence is missing required fields. Found: {missing}")

    # 6. Reconciliation status is blocked/review-only, never ready
    if uz:
        recon_status = uz.get("reconciliation_status")
        if recon_status == "blocked_reconciliation_pending_evidence":
            invariants["reconciliation_status_blocked_only"] = True
        else:
            contradictions.append(f"0174UZ reconciliation_status '{recon_status}' is not blocked")

    # 7. No packet marks public_postable true
    public_postable_false = True
    for p_name, p in [("0174UW", uw), ("0174UY", uy), ("0174UZ", uz)]:
        if p:
            # Check safety flags
            if p.get("safety_flags", {}).get("public_postable") is not False:
                public_postable_false = False
                contradictions.append(f"{p_name} safety_flags public_postable is not False")
            # Check platform targets in UW
            if p_name == "0174UW":
                for target in p.get("platform_targets", []):
                    if target.get("public_postable") is not False:
                        public_postable_false = False
                        contradictions.append(f"0174UW platform target {target.get('target_id')} has public_postable True")

    if uw or uy or uz:
        invariants["public_postable_false"] = public_postable_false

    # 8. No packet marks dispatch_ready true
    dispatch_ready_false = True
    for p_name, p in [("0174UW", uw), ("0174UY", uy), ("0174UZ", uz)]:
        if p:
            if p.get("safety_flags", {}).get("dispatch_ready") is not False:
                dispatch_ready_false = False
                contradictions.append(f"{p_name} safety_flags dispatch_ready is not False")
            if p_name == "0174UW":
                for target in p.get("platform_targets", []):
                    if target.get("dispatch_ready") is not False:
                        dispatch_ready_false = False
                        contradictions.append(f"0174UW platform target {target.get('target_id')} has dispatch_ready True")

    if uw or uy or uz:
        invariants["dispatch_ready_false"] = dispatch_ready_false

    # 9. No packet marks approval_mutation true
    if uz:
        if uz.get("safety_flags", {}).get("approval_mutation") is False:
            invariants["approval_mutation_false"] = True
        else:
            contradictions.append("0174UZ safety_flags approval_mutation is not False")

    # 10. No packet marks credential_values_loaded true
    if uz:
        if uz.get("safety_flags", {}).get("credential_values_loaded") is False:
            invariants["credential_values_loaded_false"] = True
        else:
            contradictions.append("0174UZ safety_flags credential_values_loaded is not False")

    # 11. No packet marks network_performed true
    network_performed_false = True
    for p_name, p in [("0174UW", uw), ("0174UY", uy), ("0174UZ", uz)]:
        if p:
            if p.get("safety_flags", {}).get("network_performed") is not False:
                network_performed_false = False
                contradictions.append(f"{p_name} safety_flags network_performed is not False")

    if uw or uy or uz:
        invariants["network_performed_false"] = network_performed_false

    # 12. All disabled live action states keep publish/send/schedule/connect/verify/sync/live dispatch disabled
    disabled_live_states = True
    for p_name, p in [("0174UW", uw), ("0174UY", uy), ("0174UZ", uz)]:
        if p:
            state_key = "disabled_live_dispatch_state" if p_name == "0174UW" else "disabled_live_action_state"
            state = p.get(state_key, {})
            # Fields: live_dispatch_enabled, publish_enabled, send_enabled, schedule_enabled, connect_account_enabled, verify_credentials_enabled, sync_platform_enabled
            for f in ("live_dispatch_enabled", "publish_enabled", "send_enabled", "schedule_enabled", "connect_account_enabled", "verify_credentials_enabled", "sync_platform_enabled"):
                if state.get(f) is not False:
                    disabled_live_states = False
                    contradictions.append(f"{p_name} {state_key} field '{f}' is not False")

    if uw or uy or uz:
        invariants["disabled_live_action_states_correct"] = disabled_live_states

    # 14. No packet contains buy/sell/hold/signal/trading/order/fill/PnL language
    no_banned_words = True
    for p_name, p in [("0174UW", uw), ("0174UY", uy), ("0174UZ", uz)]:
        if p:
            if walk_contains_banned_language(p):
                no_banned_words = False
                contradictions.append(f"{p_name} contains banned financial/trading keywords")

    if uw or uy or uz:
        invariants["no_banned_financial_language"] = no_banned_words

    # Determine final audit status
    all_passed = (
        not missing_packets
        and all(invariants.values())
        and not contradictions
    )

    audit_status = "verified_blocked_manual_only" if all_passed else "failed_invariant_check"

    # Assemble blocked reasons
    if missing_packets:
        blocked_reasons.append(f"missing_source_packets: {', '.join(missing_packets)}")
    for inv_name, passed in invariants.items():
        if not passed:
            blocked_reasons.append(f"failed_invariant:{inv_name}")

    return {
        "source_packets_found": {
            "0174UW": uw is not None,
            "0174UY": uy is not None,
            "0174UZ": uz is not None,
        },
        "invariants": invariants,
        "blocked_reasons": blocked_reasons,
        "contradictions": contradictions,
        "audit_status": audit_status,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
    }


def build_audit_packet(repo_root: str | Path = ".") -> dict[str, Any]:
    """Generates the audit contract packet by reading and verifying source packages."""
    root = Path(repo_root).resolve()
    audit_results = run_audit(root)

    # Extract source packet hashes if they exist
    uw_path = root / "docs" / "automation" / "0174UW" / "v5_manual_export_pilot_verification_contract_packet.json"
    uy_path = root / "docs" / "automation" / "0174UY" / "v5_operator_review_queue_manual_pilot_trail_contract_packet.json"
    uz_path = root / "docs" / "automation" / "0174UZ" / "v5_manual_pilot_trail_reconciliation_contract_packet.json"

    uw = load_json_packet(uw_path)
    uy = load_json_packet(uy_path)
    uz = load_json_packet(uz_path)

    source_packets_metadata = {
        "0174UW_manual_export": {
            "packet_hash": uw.get("packet_hash") if uw else None,
            "contract_version": uw.get("contract_version") if uw else None,
        },
        "0174UY_operator_review": {
            "packet_hash": uy.get("packet_hash") if uy else None,
            "contract_version": uy.get("contract_version") if uy else None,
        },
        "0174UZ_reconciliation": {
            "packet_hash": uz.get("packet_hash") if uz else None,
            "contract_version": uz.get("contract_version") if uz else None,
        },
    }

    # Define safety flags for the audit contract itself
    safety_flags = {
        "local_only": True,
        "manual_only": True,
        "no_platform_api": True,
        "no_credentials": True,
        "no_scheduler": True,
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
        "source_packets": source_packets_metadata,
        "chain_links": {
            "uy_to_uw_link": "277fb7d44b247efc6021f038e362256f746cc039",
            "uz_to_uw_link": "277fb7d44b247efc6021f038e362256f746cc039",
            "uz_to_uy_packet_hash": uy.get("packet_hash") if uy else None,
            "uz_to_uy_queue_id": uy.get("queue_id") if uy else None,
        },
        "invariant_results": audit_results["invariants"],
        "blocked_reason_results": {
            "reasons": audit_results["blocked_reasons"],
        },
        "placeholder_integrity_results": {
            "passed": audit_results["invariants"]["placeholders_remain_empty"],
        },
        "disabled_live_action_results": {
            "passed": audit_results["invariants"]["disabled_live_action_states_correct"],
        },
        "safety_flag_results": {
            "public_postable": audit_results["invariants"]["public_postable_false"],
            "dispatch_ready": audit_results["invariants"]["dispatch_ready_false"],
            "approval_mutation": audit_results["invariants"]["approval_mutation_false"],
            "credential_values_loaded": audit_results["invariants"]["credential_values_loaded_false"],
            "network_performed": audit_results["invariants"]["network_performed_false"],
        },
        "missing_evidence_results": {
            "passed": audit_results["invariants"]["missing_evidence_fields_correct"],
            "required_missing": ["manual_publish_url", "manual_publish_timestamp", "manual_metrics_snapshot"],
        },
        "contradiction_results": {
            "contradictions_found": audit_results["contradictions"],
        },
        "audit_status": audit_results["audit_status"],
        "safety_flags": safety_flags,
        "next_recommended_task": "TASK_CONTENTOPS_0175AB_MANUAL_PILOT_TRAIL_RECONCILIATION_AUDIT_BROWSER_QA_V0",
    }

    packet_hash = _digest(draft)
    return {
        "audit_id": "v5_manual_pilot_trail_reconciliation_audit_" + packet_hash[:24],
        "packet_hash": packet_hash,
        "packet_hash_algorithm": HASH_ALGORITHM,
        **draft,
    }


def render_runbook(packet: dict[str, Any]) -> str:
    """Renders the forensic MD report runbook for the audit contract."""
    invariants = packet["invariant_results"]
    safety = packet["safety_flag_results"]
    contradictions = packet["contradiction_results"]["contradictions_found"]

    lines = [
        "# V5 Manual Pilot Trail Reconciliation Audit Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only audit verifier for compliance verification of the full manual pilot trail chain.",
        "> It has zero live dispatch, credential access, or networking capabilities.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Audit ID**: `{packet['audit_id']}`",
        f"- **Contract Version**: `{packet['contract_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Audit Packet Hash**: `{packet['packet_hash']}`",
        f"- **Audit Status**: `{packet['audit_status']}`",
        "",
        "## Audited Packets",
        "",
        "| Step | Target Packet | Hash | Version |",
        "|---|---|---|---|",
    ]

    for k, v in packet["source_packets"].items():
        lines.append(f"| {k} | `{k}` | `{v['packet_hash']}` | `{v['contract_version']}` |")

    lines.extend([
        "",
        "## Invariant Verification Status",
        "",
        "| Invariant Description | Verification Status |",
        "|---|---|",
    ])

    for inv, status in invariants.items():
        status_label = "✅ PASS" if status else "❌ FAIL"
        lines.append(f"| `{inv}` | `{status_label}` |")

    lines.extend([
        "",
        "## Safety and Core Constraints Verification",
        "",
        "| Constraint Flag | Expected | Verification Outcome |",
        "|---|---|---|",
        f"| `public_postable` | `False` | `{'✅ Verified' if safety['public_postable'] else '❌ Violated'}` |",
        f"| `dispatch_ready` | `False` | `{'✅ Verified' if safety['dispatch_ready'] else '❌ Violated'}` |",
        f"| `approval_mutation` | `False` | `{'✅ Verified' if safety['approval_mutation'] else '❌ Violated'}` |",
        f"| `credential_values_loaded` | `False` | `{'✅ Verified' if safety['credential_values_loaded'] else '❌ Violated'}` |",
        f"| `network_performed` | `False` | `{'✅ Verified' if safety['network_performed'] else '❌ Violated'}` |",
        "",
        "## Contradictions / Exceptions Found",
        "",
    ])

    if contradictions:
        for c in contradictions:
            lines.append(f"- ⚠️ {c}")
    else:
        lines.append("- ✅ Zero contradictions or exceptions found in the audit chain.")

    lines.extend([
        "",
        "## Disabled Live Dispatch Proof",
        "",
        f"- **Live action status checks pass**: `{packet['disabled_live_action_results']['passed']}`",
        "- **All platform integrations**: blocked and local-only review verified.",
        "",
        "## Next Recommended Action",
        "",
        f"`{packet['next_recommended_task']}`",
    ])

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    """Generates and writes compliance packet and runbook under docs/automation/0175AA/."""
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AA")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_audit_packet(root)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
