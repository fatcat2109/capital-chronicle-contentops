"""Discord source-artifact to filled-intake bridge.

Verifies exactly one operator-provided real source artifact, then bridges it into
Discord filled-intake workflow without approval, dispatch, env reads, or network.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import discord_real_content_filled_intake as filled_intake
from live_contentops import discord_real_content_source_artifact as source_artifact

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_FROM_SOURCE_ARTIFACT_V0"
PLATFORM = "discord"
BRIDGE_DIR = Path("docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE_FROM_SOURCE")
DEFAULT_OUTPUT = BRIDGE_DIR / "filled_intake_from_source_packet.json"
DEFAULT_SOURCE_ARTIFACT_PACKET = Path("docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/source_artifact_packet.json")
DEFAULT_SOURCE_INBOX = Path("docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/inbox")
DEFAULT_TEMPLATE = Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json")
DEFAULT_FILLED_OUTPUT = Path("docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE/filled_intake_packet.json")


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def base_validation() -> dict[str, Any]:
    return {
        "source_artifact_ready": False,
        "exactly_one_source_artifact": False,
        "source_path_allowed": False,
        "content_nonempty": False,
        "target_recommended_or_operator_required": False,
        "filled_intake_generated": False,
        "not_template": False,
        "not_dryrun": False,
        "not_sample": False,
        "not_test_message": False,
        "no_secret_like_text": False,
        "no_financial_advice_language": False,
        "no_trading_signal_language": False,
        "no_position_sizing_language": False,
        "no_guaranteed_prediction_language": False,
    }


def blocked_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "bridge_status": "BLOCKED_AWAITING_OPERATOR_ARTIFACT",
        "platform": PLATFORM,
        "source_artifact_packet_path": path_text(DEFAULT_SOURCE_ARTIFACT_PACKET),
        "filled_intake_packet_path": path_text(DEFAULT_FILLED_OUTPUT),
        "source_artifact_path": None,
        "source_artifact_sha256": None,
        "source_artifact_kind": None,
        "source_artifact_bytes": None,
        "recommended_target_name": None,
        "recommended_content_type": None,
        "filled_intake_status": "BLOCKED_AWAITING_OPERATOR_CONTENT",
        "intake_id": None,
        "content_title": None,
        "content_summary": None,
        "content_preview_redacted_or_excerpt": None,
        "source_evidence_required": False,
        "source_evidence_paths_detected": [],
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "validation": base_validation(),
        "block_reason": "operator_artifact_missing",
    }


def fail_packet(
    errors: list[str],
    *,
    source_packet: dict[str, Any] | None = None,
    filled_packet: dict[str, Any] | None = None,
    source_packet_path: str | Path | None = None,
) -> dict[str, Any]:
    packet = blocked_packet()
    packet["bridge_status"] = "FAIL_VALIDATION"
    packet["validation_errors"] = errors
    packet["block_reason"] = "validation_failed"
    if source_packet_path is not None:
        packet["source_artifact_packet_path"] = path_text(source_packet_path)
    if source_packet:
        packet.update({
            "source_artifact_path": source_packet.get("source_artifact_path"),
            "source_artifact_sha256": source_packet.get("source_artifact_sha256"),
            "source_artifact_kind": source_packet.get("source_artifact_kind"),
            "source_artifact_bytes": source_packet.get("source_artifact_bytes"),
            "recommended_target_name": source_packet.get("recommended_target_name"),
            "recommended_content_type": source_packet.get("recommended_content_type"),
            "content_title": source_packet.get("content_title_detected"),
            "content_preview_redacted_or_excerpt": source_packet.get("content_preview_redacted_or_excerpt"),
            "source_evidence_required": bool(source_packet.get("source_evidence_required")),
            "source_evidence_paths_detected": list(source_packet.get("source_evidence_paths_detected", [])),
        })
        validation = source_packet.get("validation", {})
        packet["validation"].update({
            "source_artifact_ready": source_packet.get("source_artifact_status") == "READY_FOR_FILLED_INTAKE",
            "source_path_allowed": bool(validation.get("source_path_allowed")),
            "content_nonempty": bool(validation.get("content_nonempty")),
            "not_template": bool(validation.get("not_template")),
            "not_dryrun": bool(validation.get("not_dryrun")),
            "not_sample": bool(validation.get("not_sample")),
            "not_test_message": bool(validation.get("not_test_message")),
            "no_secret_like_text": bool(validation.get("no_webhook_or_secret_like_text")),
            "no_financial_advice_language": bool(validation.get("no_financial_advice_language")),
            "no_trading_signal_language": bool(validation.get("no_trading_signal_language")),
            "no_position_sizing_language": bool(validation.get("no_position_sizing_language")),
            "no_guaranteed_prediction_language": bool(validation.get("no_guaranteed_prediction_language")),
        })
    if filled_packet:
        packet["filled_intake_status"] = filled_packet.get("filled_intake_status") or packet["filled_intake_status"]
        packet["intake_id"] = filled_packet.get("intake_id")
        packet["content_summary"] = filled_packet.get("content_summary")
        packet["validation"]["filled_intake_generated"] = filled_packet.get("filled_intake_status") == "READY_FOR_INTAKE_APPROVAL"
    return packet


def blocked_filled_packet(
    template: str | Path,
    filled_output: str | Path,
    source_artifact_path: str | Path | None,
    *,
    reason: str,
) -> dict[str, Any]:
    filled_packet = filled_intake.blocked_packet(template, source_artifact_path, reason=reason)
    filled_intake.write_all_outputs(filled_output, filled_packet)
    return filled_packet


def blocked_for_operator_target(source_packet: dict[str, Any], *, source_packet_path: str | Path, filled_packet: dict[str, Any] | None = None) -> dict[str, Any]:
    packet = blocked_packet()
    packet["source_artifact_packet_path"] = path_text(source_packet_path)
    packet["source_artifact_path"] = source_packet.get("source_artifact_path")
    packet["source_artifact_sha256"] = source_packet.get("source_artifact_sha256")
    packet["source_artifact_kind"] = source_packet.get("source_artifact_kind")
    packet["source_artifact_bytes"] = source_packet.get("source_artifact_bytes")
    packet["recommended_target_name"] = None
    packet["recommended_content_type"] = None
    packet["content_title"] = source_packet.get("content_title_detected")
    packet["content_preview_redacted_or_excerpt"] = source_packet.get("content_preview_redacted_or_excerpt")
    packet["source_evidence_required"] = bool(source_packet.get("source_evidence_required"))
    packet["source_evidence_paths_detected"] = list(source_packet.get("source_evidence_paths_detected", []))
    packet["block_reason"] = "operator_target_selection_required"
    validation = source_packet.get("validation", {})
    packet["validation"] = {
        "source_artifact_ready": source_packet.get("source_artifact_status") == "READY_FOR_FILLED_INTAKE",
        "exactly_one_source_artifact": True,
        "source_path_allowed": bool(validation.get("source_path_allowed")),
        "content_nonempty": bool(validation.get("content_nonempty")),
        "target_recommended_or_operator_required": False,
        "filled_intake_generated": False,
        "not_template": bool(validation.get("not_template")),
        "not_dryrun": bool(validation.get("not_dryrun")),
        "not_sample": bool(validation.get("not_sample")),
        "not_test_message": bool(validation.get("not_test_message")),
        "no_secret_like_text": bool(validation.get("no_webhook_or_secret_like_text")),
        "no_financial_advice_language": bool(validation.get("no_financial_advice_language")),
        "no_trading_signal_language": bool(validation.get("no_trading_signal_language")),
        "no_position_sizing_language": bool(validation.get("no_position_sizing_language")),
        "no_guaranteed_prediction_language": bool(validation.get("no_guaranteed_prediction_language")),
    }
    if filled_packet:
        packet["filled_intake_status"] = filled_packet.get("filled_intake_status")
        packet["content_summary"] = filled_packet.get("content_summary")
    return packet


def source_packet_current_or_refreshed(source_artifact_packet: str | Path, explicit_source_artifact: str | Path | None = None, *, inbox: str | Path = DEFAULT_SOURCE_INBOX) -> tuple[dict[str, Any], list[str]]:
    source_packet = source_artifact.materialize_source_artifact(explicit_source_artifact, inbox=inbox)
    candidates = source_packet.get("candidate_source_artifact_paths", [])
    write_json(source_artifact_packet, source_packet)
    return source_packet, candidates


def bridge_validation_from_source(source_packet: dict[str, Any], exactly_one: bool, filled_generated: bool, target_ready: bool) -> dict[str, Any]:
    validation = source_packet.get("validation", {})
    return {
        "source_artifact_ready": source_packet.get("source_artifact_status") == "READY_FOR_FILLED_INTAKE",
        "exactly_one_source_artifact": exactly_one,
        "source_path_allowed": bool(validation.get("source_path_allowed")),
        "content_nonempty": bool(validation.get("content_nonempty")),
        "target_recommended_or_operator_required": target_ready,
        "filled_intake_generated": filled_generated,
        "not_template": bool(validation.get("not_template")),
        "not_dryrun": bool(validation.get("not_dryrun")),
        "not_sample": bool(validation.get("not_sample")),
        "not_test_message": bool(validation.get("not_test_message")),
        "no_secret_like_text": bool(validation.get("no_webhook_or_secret_like_text")),
        "no_financial_advice_language": bool(validation.get("no_financial_advice_language")),
        "no_trading_signal_language": bool(validation.get("no_trading_signal_language")),
        "no_position_sizing_language": bool(validation.get("no_position_sizing_language")),
        "no_guaranteed_prediction_language": bool(validation.get("no_guaranteed_prediction_language")),
    }


def materialize_bridge(source_artifact_packet: str | Path = DEFAULT_SOURCE_ARTIFACT_PACKET, *, source_artifact_path: str | Path | None = None, target: str | None = None, content_type: str | None = None, inbox: str | Path = DEFAULT_SOURCE_INBOX, template: str | Path = DEFAULT_TEMPLATE, filled_output: str | Path = DEFAULT_FILLED_OUTPUT) -> dict[str, Any]:
    source_packet, candidates = source_packet_current_or_refreshed(source_artifact_packet, source_artifact_path, inbox=inbox)
    if len(candidates) > 1:
        filled_packet = blocked_filled_packet(template, filled_output, source_packet.get("source_artifact_path"), reason="validation_failed")
        return fail_packet(["multiple_source_artifacts_in_inbox"], source_packet=source_packet, filled_packet=filled_packet, source_packet_path=source_artifact_packet)
    if source_packet.get("source_artifact_status") == "BLOCKED_AWAITING_OPERATOR_ARTIFACT":
        filled_packet = blocked_filled_packet(template, filled_output, source_packet.get("source_artifact_path"), reason="operator_content_missing")
        packet = blocked_packet()
        packet["source_artifact_packet_path"] = path_text(source_artifact_packet)
        packet["filled_intake_packet_path"] = path_text(filled_output)
        packet["filled_intake_status"] = filled_packet.get("filled_intake_status")
        return packet
    if source_packet.get("source_artifact_status") != "READY_FOR_FILLED_INTAKE":
        filled_packet = blocked_filled_packet(template, filled_output, source_packet.get("source_artifact_path"), reason="validation_failed")
        return fail_packet(["source_artifact_not_ready"], source_packet=source_packet, filled_packet=filled_packet, source_packet_path=source_artifact_packet)
    target = target or source_packet.get("recommended_target_name")
    content_type = content_type or source_packet.get("recommended_content_type")
    if not target or not content_type:
        filled_packet = blocked_filled_packet(template, filled_output, source_packet.get("source_artifact_path"), reason="operator_content_missing")
        return blocked_for_operator_target(source_packet, source_packet_path=source_artifact_packet, filled_packet=filled_packet)
    filled_packet = filled_intake.materialize_filled_intake(template, filled_output, source_packet.get("source_artifact_path"), target, content_type)
    filled_intake.write_all_outputs(filled_output, filled_packet)
    if filled_packet.get("filled_intake_status") != "READY_FOR_INTAKE_APPROVAL":
        safe_filled_packet = blocked_filled_packet(template, filled_output, source_packet.get("source_artifact_path"), reason="validation_failed")
        return fail_packet(["filled_intake_generation_failed"], source_packet=source_packet, filled_packet=safe_filled_packet, source_packet_path=source_artifact_packet)
    return {
        "task_label": TASK_LABEL,
        "bridge_status": "READY_FOR_INTAKE_APPROVAL",
        "platform": PLATFORM,
        "source_artifact_packet_path": path_text(source_artifact_packet),
        "filled_intake_packet_path": path_text(filled_output),
        "source_artifact_path": source_packet.get("source_artifact_path"),
        "source_artifact_sha256": source_packet.get("source_artifact_sha256"),
        "source_artifact_kind": source_packet.get("source_artifact_kind"),
        "source_artifact_bytes": source_packet.get("source_artifact_bytes"),
        "recommended_target_name": target,
        "recommended_content_type": content_type,
        "filled_intake_status": filled_packet.get("filled_intake_status"),
        "intake_id": filled_packet.get("intake_id"),
        "content_title": filled_packet.get("content_title"),
        "content_summary": filled_packet.get("content_summary"),
        "content_preview_redacted_or_excerpt": filled_packet.get("content_body", "")[:240] or None,
        "source_evidence_required": bool(source_packet.get("source_evidence_required")),
        "source_evidence_paths_detected": list(source_packet.get("source_evidence_paths_detected", [])),
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "validation": bridge_validation_from_source(source_packet, True, True, True),
    }


def implementation_report(packet: dict[str, Any]) -> str:
    report_status = "PASS" if packet.get("bridge_status") == "READY_FOR_INTAKE_APPROVAL" else "BLOCKED_FAIL_SAFE"
    return f"""# Discord Filled Intake From Source Artifact Bridge\n\nStatus: `{report_status}`\n\nBridge status: `{packet.get('bridge_status')}`\n\n- No live request in this task: `true`\n- No env read in this task: `true`\n- Fake public-postable content created: `false`\n- Auto-approval performed: `false`\n- Auto-dispatch performed: `false`\n\nIf source artifact missing, invalid, or placeholder-filled, framework rewrites filled intake into blocked fail-safe state. If target/content type unclear, operator target selection remains required.\n"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    if packet.get("bridge_status") == "READY_FOR_INTAKE_APPROVAL":
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_INTAKE_APPROVAL_FROM_FILLED_PACKET_V0"
        goal = "validate filled intake packet and materialize operator approval candidate."
    elif packet.get("bridge_status") == "BLOCKED_AWAITING_OPERATOR_ARTIFACT":
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_SOURCE_ARTIFACT_V0"
        goal = "Jim places exactly one real source artifact into inbox."
    else:
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_FROM_SOURCE_ARTIFACT_V0"
        goal = "repair source artifact state or provide explicit target/content type selection."
    return f"# Next Task Pointer\n\nRecommended next task:\n\n`{task}`\n\nGoal: {goal}\n"


def write_all_outputs(output: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, packet)
    (out.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge Discord source artifact into filled intake")
    parser.add_argument("--source-artifact-packet", default=str(DEFAULT_SOURCE_ARTIFACT_PACKET))
    parser.add_argument("--source-artifact", default=None)
    parser.add_argument("--target", default=None)
    parser.add_argument("--content-type", default=None)
    parser.add_argument("--inbox", default=str(DEFAULT_SOURCE_INBOX))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--filled-output", default=str(DEFAULT_FILLED_OUTPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    packet = materialize_bridge(
        args.source_artifact_packet,
        source_artifact_path=args.source_artifact,
        target=args.target,
        content_type=args.content_type,
        inbox=args.inbox,
        template=args.template,
        filled_output=args.filled_output,
    )
    write_all_outputs(args.output, packet)
    print(json.dumps({
        "task_label": packet.get("task_label"),
        "bridge_status": packet.get("bridge_status"),
        "source_artifact_path": packet.get("source_artifact_path"),
        "filled_intake_status": packet.get("filled_intake_status"),
        "intake_id": packet.get("intake_id"),
        "recommended_target_name": packet.get("recommended_target_name"),
        "recommended_content_type": packet.get("recommended_content_type"),
        "no_live_request_in_this_task": packet.get("no_live_request_in_this_task"),
        "no_env_read_in_this_task": packet.get("no_env_read_in_this_task"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
