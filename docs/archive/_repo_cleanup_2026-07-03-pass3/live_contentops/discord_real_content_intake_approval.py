"""Discord real-content intake approval materializer.

Creates a deterministic, non-live operator approval candidate from a filled real
content intake packet. This module never reads environment variables, sends
network requests, approves automatically, or dispatches messages.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from live_contentops import discord_real_content_queue as queue

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_INTAKE_APPROVAL_V0"
PLATFORM = "discord"
APPROVAL_DIR = Path("docs/automation/DISCORD_REAL_CONTENT_INTAKE_APPROVAL")
DEFAULT_QUEUE_PACKET = Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_queue_packet.json")
DEFAULT_INTAKE = Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json")
DEFAULT_OUTPUT = APPROVAL_DIR / "real_content_intake_approval_packet.json"
DEFAULT_SCHEMA = APPROVAL_DIR / "real_content_intake_approval_schema.json"
DEFAULT_PANEL = APPROVAL_DIR / "operator_approval_panel.html"


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def empty_validation() -> dict[str, Any]:
    return {
        "filled_intake_present": False,
        "template_rejected": False,
        "target_allowed": False,
        "payload_type_matches_target": False,
        "payload_hash_generated": False,
        "content_nonempty": False,
        "financial_advice_check_passed": False,
        "no_trading_signal_passed": False,
        "position_sizing_check_passed": False,
        "guaranteed_prediction_check_passed": False,
        "source_evidence_present_or_pending": "PENDING",
        "invented_number_safety_passed_or_pending": "PENDING",
    }


def operator_decision_required(candidate_ready: bool) -> dict[str, bool]:
    return {
        "approve_payload_hash": candidate_ready,
        "approve_target": candidate_ready,
        "approve_content_preview": candidate_ready,
        "approve_no_financial_advice": candidate_ready,
        "approve_source_evidence": candidate_ready,
        "approve_future_one_request_dispatch": candidate_ready,
    }


def base_packet(queue_packet_path: str | Path, intake_path: str | Path | None) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "approval_materialization_status": "PASS",
        "intake_approval_status": "BLOCKED_AWAITING_FILLED_INTAKE",
        "platform": PLATFORM,
        "source_queue_packet": path_text(queue_packet_path),
        "source_intake_path": path_text(intake_path),
        "selected_intake_id": None,
        "target_name": None,
        "content_type": None,
        "payload_id": None,
        "payload_hash": None,
        "content_title": None,
        "content_preview_redacted_or_excerpt": None,
        "approval_state": "BLOCKED",
        "dispatch_state": "NOT_DISPATCHED",
        "ready_for_supervised_action": False,
        "operator_authorization_required": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "dryrun_payload_reuse_blocked": True,
        "validation": empty_validation(),
        "operator_decision_required": operator_decision_required(False),
    }


def queue_packet_valid(queue_packet_data: dict[str, Any]) -> bool:
    return (
        queue_packet_data.get("queue_materialization_status") == "PASS"
        and queue_packet_data.get("dryrun_payload_reuse_blocked") is True
        and queue_packet_data.get("no_live_request_in_this_task") is True
        and queue_packet_data.get("no_env_read_in_this_task") is True
    )


def load_actions_from_queue_packet(queue_packet_data: dict[str, Any]) -> dict[str, Any]:
    actions_path = queue_packet_data.get("source_actions_packet")
    if not actions_path:
        return {"supervised_dispatch_actions_ready": False, "actions": []}
    try:
        return load_json(actions_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {"supervised_dispatch_actions_ready": False, "actions": []}


def intake_is_template_or_unfilled(intake: dict[str, Any]) -> bool:
    return (
        intake.get("template_only") is True
        or intake.get("not_public_postable") is True
        or intake.get("not_approved") is True
        or intake.get("not_dispatchable") is True
    )


def content_nonempty(intake: dict[str, Any]) -> bool:
    return bool(
        str(intake.get("content_title", "")).strip()
        or str(intake.get("content_summary", "")).strip()
        or str(intake.get("content_body", "")).strip()
    )


def validation_from_queue(intake: dict[str, Any], actions_packet: dict[str, Any], queue_validation: dict[str, Any], payload_hash_generated: bool) -> dict[str, Any]:
    target = intake.get("target_name")
    content_type = intake.get("content_type")
    text = queue.content_text(intake)
    return {
        "filled_intake_present": True,
        "template_rejected": False,
        "target_allowed": bool(queue_validation.get("target_allowed")),
        "payload_type_matches_target": queue.TARGET_TO_PAYLOAD_TYPE.get(target) == content_type,
        "payload_hash_generated": payload_hash_generated,
        "content_nonempty": content_nonempty(intake),
        "financial_advice_check_passed": queue_validation.get("financial_advice_check_passed_or_pending") == "PASS",
        "no_trading_signal_passed": not bool(queue.TRADING_SIGNAL_RE.search(text)),
        "position_sizing_check_passed": not bool(queue.POSITION_SIZING_RE.search(text)),
        "guaranteed_prediction_check_passed": not bool(queue.GUARANTEED_PREDICTION_RE.search(text)),
        "source_evidence_present_or_pending": queue_validation.get("source_evidence_present_or_pending", "PENDING"),
        "invented_number_safety_passed_or_pending": queue_validation.get("invented_number_safety_passed_or_pending", "PENDING"),
    }


def blocked_for_missing_or_template(packet: dict[str, Any], reason: str, intake: dict[str, Any] | None = None) -> dict[str, Any]:
    packet["approval_materialization_status"] = "PASS"
    packet["intake_approval_status"] = "BLOCKED_AWAITING_FILLED_INTAKE"
    packet["approval_state"] = "BLOCKED"
    packet["block_reason"] = reason
    packet["validation"]["template_rejected"] = bool(intake and intake_is_template_or_unfilled(intake))
    packet["validation"]["filled_intake_present"] = False
    return packet


def materialize_approval(queue_packet_path: str | Path, intake_path: str | Path | None = None) -> dict[str, Any]:
    packet = base_packet(queue_packet_path, intake_path)
    try:
        queue_packet_data = load_json(queue_packet_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        packet["approval_materialization_status"] = "BLOCKED"
        packet["block_reason"] = f"queue_packet_unreadable:{exc.__class__.__name__}"
        return packet
    if not queue_packet_valid(queue_packet_data):
        packet["approval_materialization_status"] = "FAIL"
        packet["intake_approval_status"] = "FAIL_VALIDATION"
        packet["validation_errors"] = ["queue_packet_not_ready_or_missing_safety_flags"]
        return packet
    if intake_path is None:
        return blocked_for_missing_or_template(packet, "missing_intake")
    try:
        intake = load_json(intake_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return blocked_for_missing_or_template(packet, "missing_or_unreadable_intake")
    packet["selected_intake_id"] = intake.get("intake_id") or None
    packet["target_name"] = intake.get("target_name")
    packet["content_type"] = intake.get("content_type")
    packet["content_title"] = str(intake.get("content_title", "")).strip() or None
    packet["content_preview_redacted_or_excerpt"] = str(intake.get("content_body", "")).strip()[:240] or None
    if intake_is_template_or_unfilled(intake):
        return blocked_for_missing_or_template(packet, "template_or_unfilled_intake", intake)

    actions_packet = load_actions_from_queue_packet(queue_packet_data)
    record, rejection = queue.queue_record_from_intake(intake, actions_packet)
    if record is None:
        q_validation = rejection.get("validation", {})
        packet["approval_materialization_status"] = "FAIL"
        packet["intake_approval_status"] = "FAIL_VALIDATION"
        packet["approval_state"] = "BLOCKED"
        packet["validation"] = validation_from_queue(intake, actions_packet, q_validation, False)
        packet["validation_errors"] = rejection.get("errors", [])
        return packet

    packet["approval_materialization_status"] = "PASS"
    packet["intake_approval_status"] = "APPROVAL_CANDIDATE_READY"
    packet["payload_id"] = record.get("payload_id")
    packet["payload_hash"] = record.get("payload_hash")
    packet["content_title"] = record.get("content_title") or None
    packet["content_preview_redacted_or_excerpt"] = record.get("content_preview_redacted_or_excerpt") or None
    packet["approval_state"] = "PENDING_OPERATOR_APPROVAL"
    packet["dispatch_state"] = "NOT_DISPATCHED"
    packet["ready_for_supervised_action"] = False
    packet["operator_authorization_required"] = True
    packet["validation"] = validation_from_queue(intake, actions_packet, record.get("validation", {}), True)
    packet["operator_decision_required"] = operator_decision_required(True)
    return packet


def approval_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Discord Real Content Intake Approval Packet",
        "type": "object",
        "required": [
            "task_label",
            "approval_materialization_status",
            "intake_approval_status",
            "platform",
            "source_queue_packet",
            "approval_state",
            "dispatch_state",
            "ready_for_supervised_action",
            "operator_authorization_required",
            "no_live_request_in_this_task",
            "no_env_read_in_this_task",
            "dryrun_payload_reuse_blocked",
            "validation",
            "operator_decision_required",
        ],
        "properties": {
            "task_label": {"const": TASK_LABEL},
            "approval_materialization_status": {"enum": ["PASS", "BLOCKED", "FAIL"]},
            "intake_approval_status": {"enum": ["APPROVAL_CANDIDATE_READY", "BLOCKED_AWAITING_FILLED_INTAKE", "FAIL_VALIDATION"]},
            "platform": {"const": PLATFORM},
            "dispatch_state": {"const": "NOT_DISPATCHED"},
            "ready_for_supervised_action": {"const": False},
            "operator_authorization_required": {"const": True},
            "no_live_request_in_this_task": {"const": True},
            "no_env_read_in_this_task": {"const": True},
            "dryrun_payload_reuse_blocked": {"const": True},
        },
    }


def render_panel(packet: dict[str, Any]) -> str:
    status = html.escape(str(packet.get("intake_approval_status")))
    title = html.escape(str(packet.get("content_title") or "No filled intake provided"))
    target = html.escape(str(packet.get("target_name") or "pending"))
    payload_hash = html.escape(str(packet.get("payload_hash") or "pending"))
    preview = html.escape(str(packet.get("content_preview_redacted_or_excerpt") or "Operator must provide filled real content intake."))
    checks = "".join(
        f"<li><strong>{html.escape(str(key))}</strong>: {html.escape(str(value))}</li>"
        for key, value in packet.get("validation", {}).items()
    )
    decision = "".join(
        f"<li><strong>{html.escape(str(key))}</strong>: {html.escape(str(value))}</li>"
        for key, value in packet.get("operator_decision_required", {}).items()
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Discord Real Content Intake Approval</title>
  <meta name=\"description\" content=\"Static non-live Discord real content intake approval panel.\">
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: radial-gradient(circle at top left, #1e3a5f, #050816 55%, #02030a); color: #eef5ff; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 48px 24px; }}
    .card {{ border: 1px solid rgba(125, 211, 252, .28); background: rgba(8, 17, 34, .78); border-radius: 28px; padding: 28px; box-shadow: 0 28px 80px rgba(0, 0, 0, .35); }}
    .pill {{ display: inline-block; padding: 8px 14px; border-radius: 999px; background: rgba(45, 212, 191, .16); color: #7dd3fc; font-weight: 700; letter-spacing: .04em; }}
    h1 {{ font-size: clamp(2rem, 5vw, 4.4rem); line-height: .95; margin: 18px 0; }}
    h2 {{ color: #bae6fd; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 24px 0; }}
    .tile {{ background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .12); border-radius: 18px; padding: 18px; }}
    code {{ color: #67e8f9; word-break: break-all; }}
    ul {{ padding-left: 20px; }}
    .blocked {{ color: #fbbf24; }}
    .no-live {{ border-left: 4px solid #34d399; padding-left: 16px; color: #bbf7d0; }}
  </style>
</head>
<body>
  <main>
    <section class=\"card\" aria-labelledby=\"approval-title\">
      <span class=\"pill\">{status}</span>
      <h1 id=\"approval-title\">Discord Real Content Intake Approval</h1>
      <p class=\"no-live\">Static panel only. No live buttons. No hidden action. No webhook URL. No dispatch.</p>
      <div class=\"grid\">
        <div class=\"tile\"><h2>Content</h2><p>{title}</p></div>
        <div class=\"tile\"><h2>Target</h2><p><code>{target}</code></p></div>
        <div class=\"tile\"><h2>Payload Hash</h2><p><code>{payload_hash}</code></p></div>
      </div>
      <h2>Preview</h2>
      <p>{preview}</p>
      <h2>Validation Checks</h2>
      <ul>{checks}</ul>
      <h2>Operator Decision Required</h2>
      <ul>{decision}</ul>
      <p class=\"blocked\">If blocked, operator must provide filled real content intake before approval can continue.</p>
    </section>
  </main>
</body>
</html>
"""


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord Real Content Intake Approval\n\nStatus: `{packet.get('approval_materialization_status')}`\n\nIntake approval status: `{packet.get('intake_approval_status')}`\n\n- Approval state: `{packet.get('approval_state')}`\n- Dispatch state: `NOT_DISPATCHED`\n- Ready for supervised action: `false`\n- No live request in this task: `true`\n- No env read in this task: `true`\n- Fake public-postable content created: `false`\n\nOperator approval candidate is only created from filled, validating real content intake.\n"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    if packet.get("intake_approval_status") == "APPROVAL_CANDIDATE_READY":
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_DECISION_GATE_V0"
        goal = "operator reviews candidate payload hash, target, preview, evidence, and future one-request dispatch authorization."
    else:
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_PACKET_V0"
        goal = "operator supplies a real filled intake artifact without invented public-postable content."
    return f"# Next Task Pointer\n\nRecommended next task:\n\n`{task}`\n\nGoal: {goal}\n"


def write_all_outputs(output: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, packet)
    write_json(out.parent / DEFAULT_SCHEMA.name, approval_schema())
    (out.parent / DEFAULT_PANEL.name).write_text(render_panel(packet), encoding="utf-8")
    (out.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord real-content intake approval packet")
    parser.add_argument("--queue-packet", default=str(DEFAULT_QUEUE_PACKET))
    parser.add_argument("--intake", default=str(DEFAULT_INTAKE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    packet = materialize_approval(args.queue_packet, args.intake)
    write_all_outputs(args.output, packet)
    print(json.dumps({
        "task_label": packet.get("task_label"),
        "approval_materialization_status": packet.get("approval_materialization_status"),
        "intake_approval_status": packet.get("intake_approval_status"),
        "selected_intake_id": packet.get("selected_intake_id"),
        "approval_state": packet.get("approval_state"),
        "dispatch_state": packet.get("dispatch_state"),
        "no_live_request_in_this_task": packet.get("no_live_request_in_this_task"),
        "no_env_read_in_this_task": packet.get("no_env_read_in_this_task"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
