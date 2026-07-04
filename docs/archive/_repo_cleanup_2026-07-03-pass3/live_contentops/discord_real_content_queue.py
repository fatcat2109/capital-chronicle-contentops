"""Discord real-content approved queue materializer.

Builds a non-live queue contract for future supervised Discord dispatch from
operator-provided real content intake. This module does not read environment
variables, send network requests, call APIs, or create executable live controls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_APPROVED_PAYLOAD_QUEUE_V0"
PLATFORM = "discord"
QUEUE_DIR = Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE")
DEFAULT_OUTPUT = QUEUE_DIR / "real_content_queue_packet.json"
DEFAULT_TEMPLATE = QUEUE_DIR / "real_content_operator_intake_template.json"
DEFAULT_SCHEMA = QUEUE_DIR / "real_content_queue_schema.json"
DEFAULT_CLOSEOUT_PACKET = Path("docs/automation/DISCORD_ONE_ACTION_LIVE_DISPATCH_CLOSEOUT/one_action_live_dispatch_closeout_packet.json")
DEFAULT_ACTIONS_PACKET = Path("docs/automation/DISCORD_SUPERVISED_DISPATCH_ACTIONS/supervised_dispatch_actions_packet.json")

TARGET_TO_PAYLOAD_TYPE = {
    "announcements": "announcement",
    "substack_drops": "substack_drop",
    "product_updates": "product_update",
}
DISALLOWED_DRYRUN_PREFIXES = ("discord_dryrun_", "dryrun_")
TRADING_SIGNAL_RE = re.compile(r"\b(buy|sell|hold|long|short|entry|exit|take profit|stop loss)\b", re.IGNORECASE)
POSITION_SIZING_RE = re.compile(r"\b(position size|size your position|allocate\s+\d+%|risk\s+\d+%|portfolio weight)\b", re.IGNORECASE)
GUARANTEED_PREDICTION_RE = re.compile(r"\b(guaranteed|will definitely|certain to|risk[- ]free|cannot lose|sure thing)\b", re.IGNORECASE)
INVENTED_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|bps|x|million|billion|trillion|m|bn|usd|\$)(?=\W|$)", re.IGNORECASE)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path_text(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def intake_template() -> dict[str, Any]:
    return {
        "template_only": True,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "intake_id": "",
        "source_system": "",
        "source_artifact_path": "",
        "content_title": "",
        "content_body": "",
        "content_summary": "",
        "content_type": "announcement",
        "target_name": "announcements",
        "author_or_operator": "",
        "created_at_utc": "",
        "approval_required": True,
        "financial_advice_check_required": True,
        "no_trading_signal_required": True,
        "source_evidence_paths": [],
        "operator_notes": "",
        "publish_intent": "",
    }


def queue_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Discord Real Content Approved Queue Packet",
        "type": "object",
        "required": ["task_label", "queue_materialization_status", "real_content_queue_status", "platform", "dryrun_payload_reuse_blocked", "queue_records"],
        "properties": {
            "task_label": {"const": TASK_LABEL},
            "queue_materialization_status": {"enum": ["PASS", "BLOCKED", "FAIL"]},
            "real_content_queue_status": {"enum": ["READY_WITH_REAL_CONTENT", "BLOCKED_AWAITING_REAL_CONTENT_INPUT", "FAIL_EVIDENCE_CONFLICT"]},
            "platform": {"const": PLATFORM},
            "dryrun_payload_reuse_blocked": {"const": True},
            "queue_records": {"type": "array"},
        },
    }


def actions_by_target(actions_packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {action.get("target_name"): action for action in actions_packet.get("actions", [])}


def render_discord_payload(intake: dict[str, Any]) -> dict[str, Any]:
    title = str(intake.get("content_title", "")).strip()
    body = str(intake.get("content_body", "")).strip()
    summary = str(intake.get("content_summary", "")).strip()
    parts = [part for part in [f"**{title}**" if title else "", summary, body] if part]
    return {"content": "\n\n".join(parts), "allowed_mentions": {"parse": []}}


def stable_hash(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def payload_id_for(intake: dict[str, Any], payload_hash: str) -> str:
    return f"discord_real_{intake.get('content_type')}_{payload_hash[:12]}"


def content_text(intake: dict[str, Any]) -> str:
    return "\n".join(str(intake.get(key, "")) for key in ("content_title", "content_summary", "content_body"))


def validate_intake(intake: dict[str, Any], actions_packet: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    errors: list[str] = []
    target = intake.get("target_name")
    payload_type = intake.get("content_type")
    body = str(intake.get("content_body", "")).strip()
    summary = str(intake.get("content_summary", "")).strip()
    title = str(intake.get("content_title", "")).strip()
    evidence_paths = intake.get("source_evidence_paths") or []
    text = content_text(intake)
    if intake.get("template_only") is True or intake.get("not_public_postable") is True:
        errors.append("template_or_not_public_postable")
    if not intake.get("intake_id"):
        errors.append("intake_id_missing")
    if not (title or summary or body):
        errors.append("empty_content")
    if not body:
        errors.append("content_body_missing")
    if target not in TARGET_TO_PAYLOAD_TYPE:
        errors.append("unknown_target")
    elif TARGET_TO_PAYLOAD_TYPE[target] != payload_type:
        errors.append("target_payload_type_mismatch")
    if str(intake.get("payload_id", "")).startswith(DISALLOWED_DRYRUN_PREFIXES) or str(intake.get("intake_id", "")).startswith(DISALLOWED_DRYRUN_PREFIXES):
        errors.append("dryrun_payload_reuse_blocked")
    if TRADING_SIGNAL_RE.search(text):
        errors.append("trading_signal_language_blocked")
    if POSITION_SIZING_RE.search(text):
        errors.append("position_sizing_language_blocked")
    if GUARANTEED_PREDICTION_RE.search(text):
        errors.append("guaranteed_prediction_language_blocked")
    target_allowed = target in actions_by_target(actions_packet)
    if not target_allowed:
        errors.append("target_not_in_actions_packet")
    invented_numbers_present = bool(INVENTED_NUMBER_RE.search(text))
    source_evidence_present = bool(evidence_paths)
    validation = {
        "target_allowed": target_allowed,
        "payload_hash_generated": False,
        "financial_advice_check_passed_or_pending": "PASS" if not (TRADING_SIGNAL_RE.search(text) or POSITION_SIZING_RE.search(text) or GUARANTEED_PREDICTION_RE.search(text)) else "FAIL",
        "no_trading_signal_passed_or_pending": "PASS" if not TRADING_SIGNAL_RE.search(text) else "FAIL",
        "source_evidence_present_or_pending": "PASS" if source_evidence_present else "PENDING",
        "invented_number_safety_passed_or_pending": "PENDING" if invented_numbers_present and not source_evidence_present else "PASS",
        "dryrun_payload_reuse": False,
    }
    return not errors, validation, errors


def queue_record_from_intake(intake: dict[str, Any], actions_packet: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    valid, validation, errors = validate_intake(intake, actions_packet)
    if not valid:
        return None, {"intake_id": intake.get("intake_id"), "approval_state": "BLOCKED", "errors": errors, "validation": validation}
    payload = render_discord_payload(intake)
    payload_hash = stable_hash(payload)
    validation["payload_hash_generated"] = True
    action = actions_by_target(actions_packet)[intake["target_name"]]
    body = str(intake.get("content_body", "")).strip()
    return {
        "queue_record_id": f"discord_real_queue_{payload_hash[:12]}",
        "intake_id": intake["intake_id"],
        "source_artifact_path": intake.get("source_artifact_path", ""),
        "target_name": intake["target_name"],
        "payload_type": intake["content_type"],
        "payload_id": payload_id_for(intake, payload_hash),
        "payload_hash": payload_hash,
        "rendered_payload": payload,
        "content_title": str(intake.get("content_title", "")).strip(),
        "content_preview_redacted_or_excerpt": body[:240],
        "destination_binding_id": action.get("destination_binding_id"),
        "credential_handle_id": action.get("credential_handle_id"),
        "env_key_name": action.get("env_key_name"),
        "approval_state": "PENDING_OPERATOR_APPROVAL",
        "dispatch_state": "NOT_DISPATCHED",
        "operator_authorization_required": True,
        "ready_for_supervised_action": False,
        "validation": validation,
    }, {}


def base_packet(closeout_path: str | Path, actions_path: str | Path, closeout_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "queue_materialization_status": "PASS",
        "real_content_queue_status": "BLOCKED_AWAITING_REAL_CONTENT_INPUT",
        "platform": PLATFORM,
        "supervised_live_loop_verified": closeout_packet.get("readiness_update", {}).get("supervised_live_loop_verified") is True,
        "source_closeout_packet": path_text(closeout_path),
        "source_actions_packet": path_text(actions_path),
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "dryrun_payload_reuse_blocked": True,
        "approved_real_content_count": 0,
        "dispatchable_real_content_count": 0,
        "pending_real_content_count": 0,
        "rejected_or_blocked_count": 0,
        "queue_records": [],
    }


def materialize_queue(closeout_path: str | Path, actions_path: str | Path, intake_path: str | Path | None = None) -> dict[str, Any]:
    try:
        closeout = load_json(closeout_path)
        actions = load_json(actions_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        return {"task_label": TASK_LABEL, "queue_materialization_status": "BLOCKED", "real_content_queue_status": "BLOCKED_AWAITING_REAL_CONTENT_INPUT", "platform": PLATFORM, "blocker": exc.__class__.__name__, "source_closeout_packet": path_text(closeout_path), "source_actions_packet": path_text(actions_path), "no_live_request_in_this_task": True, "no_env_read_in_this_task": True, "raw_secret_output": False, "dryrun_payload_reuse_blocked": True, "approved_real_content_count": 0, "dispatchable_real_content_count": 0, "pending_real_content_count": 0, "rejected_or_blocked_count": 0, "queue_records": []}
    packet = base_packet(closeout_path, actions_path, closeout)
    if closeout.get("readiness_update", {}).get("supervised_live_loop_verified") is not True:
        packet["queue_materialization_status"] = "FAIL"
        packet["real_content_queue_status"] = "FAIL_EVIDENCE_CONFLICT"
        packet["evidence_conflict"] = "supervised_live_loop_not_verified"
        return packet
    if actions.get("supervised_dispatch_actions_ready") is not True:
        packet["queue_materialization_status"] = "FAIL"
        packet["real_content_queue_status"] = "FAIL_EVIDENCE_CONFLICT"
        packet["evidence_conflict"] = "supervised_dispatch_actions_not_ready"
        return packet
    if intake_path is None:
        return packet
    intake = load_json(intake_path)
    record, rejection = queue_record_from_intake(intake, actions)
    if record is None:
        packet["real_content_queue_status"] = "FAIL_EVIDENCE_CONFLICT"
        packet["queue_materialization_status"] = "FAIL"
        packet["rejected_or_blocked_count"] = 1
        packet["rejected_records"] = [rejection]
        return packet
    packet["real_content_queue_status"] = "READY_WITH_REAL_CONTENT"
    packet["pending_real_content_count"] = 1
    packet["queue_records"] = [record]
    return packet


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord Real Content Approved Queue\n\nStatus: `{packet.get('queue_materialization_status')}`\n\nReal content queue status: `{packet.get('real_content_queue_status')}`\n\n- No live request in this task: `true`\n- No env read in this task: `true`\n- Dry-run payload reuse blocked: `true`\n- Approved real content count: `{packet.get('approved_real_content_count')}`\n- Dispatchable real content count: `{packet.get('dispatchable_real_content_count')}`\n\nOperator must provide filled real content intake before future supervised dispatch.\n"""


def next_task_pointer() -> str:
    return """# Next Task Pointer\n\nRecommended next task:\n\n`TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_INTAKE_APPROVAL_V0`\n\nGoal: operator fills a real content intake packet, then queue materializer creates a pending, non-dispatched queue record for approval.\n"""


def write_all_outputs(output: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, packet)
    write_json(out.parent / DEFAULT_SCHEMA.name, queue_schema())
    write_json(out.parent / DEFAULT_TEMPLATE.name, intake_template())
    (out.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out.parent / "next_task_pointer.md").write_text(next_task_pointer(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord real-content approved queue packet")
    parser.add_argument("--closeout-packet", default=str(DEFAULT_CLOSEOUT_PACKET))
    parser.add_argument("--actions-packet", default=str(DEFAULT_ACTIONS_PACKET))
    parser.add_argument("--intake", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    packet = materialize_queue(args.closeout_packet, args.actions_packet, args.intake)
    write_all_outputs(args.output, packet)
    print(json.dumps({"task_label": packet.get("task_label"), "queue_materialization_status": packet.get("queue_materialization_status"), "real_content_queue_status": packet.get("real_content_queue_status"), "approved_real_content_count": packet.get("approved_real_content_count"), "dispatchable_real_content_count": packet.get("dispatchable_real_content_count"), "no_live_request_in_this_task": packet.get("no_live_request_in_this_task"), "no_env_read_in_this_task": packet.get("no_env_read_in_this_task")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
