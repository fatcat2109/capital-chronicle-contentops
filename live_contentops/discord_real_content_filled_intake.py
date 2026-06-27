"""Discord real-content filled intake packet materializer.

Creates a deterministic, non-live filled-intake workflow surface. The module is
file-only: no environment reads, network calls, live posts, browser actions, or
automatic approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_PACKET_V0"
PLATFORM = "discord"
FILLED_INTAKE_DIR = Path("docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE")
DEFAULT_TEMPLATE = Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json")
DEFAULT_OUTPUT = FILLED_INTAKE_DIR / "filled_intake_packet.json"
DEFAULT_SCHEMA = FILLED_INTAKE_DIR / "filled_intake_schema.json"

TARGET_TO_CONTENT_TYPE = {
    "announcements": "announcement",
    "substack_drops": "substack_drop",
    "product_updates": "product_update",
}
CONTENT_TYPES = set(TARGET_TO_CONTENT_TYPE.values())
DISALLOWED_SOURCE_MARKERS = ("dryrun", "dry_run", "sample", "template", "test_message", "test-payload", "payload_fixture")
TRADING_SIGNAL_RE = re.compile(r"\b(buy|sell|hold|long|short|entry|exit|take profit|stop loss)\b", re.IGNORECASE)
POSITION_SIZING_RE = re.compile(r"\b(position size|size your position|allocate(?:\s+\w+){0,3}\s+\d+%|risk\s+\d+%|portfolio weight)", re.IGNORECASE)
GUARANTEED_PREDICTION_RE = re.compile(r"\b(guaranteed|will definitely|certain to|risk[- ]free|cannot lose|sure thing)\b", re.IGNORECASE)
SECRETISH_RE = re.compile(r"https://(?:discord(?:app)?\.com)/api/webhooks/|webhooks/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", re.IGNORECASE)


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


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validation_base() -> dict[str, Any]:
    return {
        "real_content_present": False,
        "source_artifact_present_or_pending": "PENDING",
        "content_nonempty": False,
        "target_allowed": False,
        "content_type_allowed": False,
        "payload_type_matches_target": False,
        "financial_advice_check_required": True,
        "no_trading_signal_required": True,
        "dryrun_payload_reuse_blocked": True,
    }


def blocked_packet(template_path: str | Path, source_artifact: str | Path | None = None, *, reason: str = "operator_content_missing") -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "filled_intake_status": "BLOCKED_AWAITING_OPERATOR_CONTENT",
        "platform": PLATFORM,
        "intake_id": None,
        "source_system": None,
        "source_artifact_path": path_text(source_artifact),
        "content_title": None,
        "content_body": None,
        "content_summary": None,
        "content_type": None,
        "target_name": None,
        "author_or_operator": None,
        "created_at_utc": None,
        "approval_required": True,
        "financial_advice_check_required": True,
        "no_trading_signal_required": True,
        "source_evidence_paths": [],
        "operator_notes": "Operator must provide real Capital Chronicle content before intake approval.",
        "publish_intent": None,
        "template_only": True,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "source_template_path": path_text(template_path),
        "block_reason": reason,
        "validation": validation_base(),
    }


def fail_packet(template_path: str | Path, source_artifact: str | Path | None, errors: list[str], *, target: str | None = None, content_type: str | None = None) -> dict[str, Any]:
    packet = blocked_packet(template_path, source_artifact, reason="validation_failed")
    packet["filled_intake_status"] = "FAIL_VALIDATION"
    packet["target_name"] = target
    packet["content_type"] = content_type
    packet["validation_errors"] = errors
    packet["validation"]["source_artifact_present_or_pending"] = "FAIL"
    packet["validation"]["target_allowed"] = target in TARGET_TO_CONTENT_TYPE
    packet["validation"]["content_type_allowed"] = content_type in CONTENT_TYPES
    packet["validation"]["payload_type_matches_target"] = bool(target in TARGET_TO_CONTENT_TYPE and TARGET_TO_CONTENT_TYPE[target] == content_type)
    return packet


def source_path_disallowed(path: str | Path) -> bool:
    lowered = path_text(path).lower()
    return any(marker in lowered for marker in DISALLOWED_SOURCE_MARKERS)


def text_has_blocked_language(text: str) -> list[str]:
    errors: list[str] = []
    if TRADING_SIGNAL_RE.search(text):
        errors.append("trading_signal_language_blocked")
    if POSITION_SIZING_RE.search(text):
        errors.append("position_sizing_language_blocked")
    if GUARANTEED_PREDICTION_RE.search(text):
        errors.append("guaranteed_prediction_language_blocked")
    if SECRETISH_RE.search(text):
        errors.append("webhook_or_secret_like_content_blocked")
    return errors


def derive_title_summary_body(text: str, fallback_title: str | None = None) -> tuple[str, str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", "", ""
    heading = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), "")
    title = fallback_title or heading or lines[0][:90]
    body_lines = [line for line in lines if line.lstrip("# ").strip() != title]
    body = "\n".join(body_lines).strip() or text.strip()
    summary_source = body_lines[0] if body_lines else lines[0]
    summary = summary_source[:240]
    return title.strip(), summary.strip(), body.strip()


def stable_intake_id(source_path: str | Path, target: str, content_type: str, text: str) -> str:
    material = json.dumps({"source": path_text(source_path), "target": target, "content_type": content_type, "text": text}, sort_keys=True)
    return f"discord_real_intake_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:12]}"


def materialize_filled_intake(template_path: str | Path, output_path: str | Path | None = None, source_artifact: str | Path | None = None, target: str | None = None, content_type: str | None = None, author_or_operator: str = "Jim", publish_intent: str = "operator-provided Capital Chronicle content") -> dict[str, Any]:
    try:
        load_json(template_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        return fail_packet(template_path, source_artifact, [f"template_unreadable:{exc.__class__.__name__}"], target=target, content_type=content_type)
    if source_artifact is None:
        return blocked_packet(template_path)
    if source_path_disallowed(source_artifact):
        return fail_packet(template_path, source_artifact, ["dryrun_sample_template_or_test_source_rejected"], target=target, content_type=content_type)
    source_path = Path(source_artifact)
    try:
        text = source_path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError) as exc:
        return fail_packet(template_path, source_artifact, [f"source_artifact_unreadable:{exc.__class__.__name__}"], target=target, content_type=content_type)
    if not text:
        return fail_packet(template_path, source_artifact, ["source_artifact_empty"], target=target, content_type=content_type)
    target = target or "announcements"
    content_type = content_type or TARGET_TO_CONTENT_TYPE.get(target)
    errors: list[str] = []
    if target not in TARGET_TO_CONTENT_TYPE:
        errors.append("unknown_target")
    if content_type not in CONTENT_TYPES:
        errors.append("unknown_content_type")
    if target in TARGET_TO_CONTENT_TYPE and TARGET_TO_CONTENT_TYPE[target] != content_type:
        errors.append("target_content_type_mismatch")
    errors.extend(text_has_blocked_language(text))
    if errors:
        packet = fail_packet(template_path, source_artifact, errors, target=target, content_type=content_type)
        packet["validation"]["content_nonempty"] = bool(text)
        packet["validation"]["real_content_present"] = False
        packet["validation"]["source_artifact_present_or_pending"] = "PASS"
        return packet
    title, summary, body = derive_title_summary_body(text)
    return {
        "task_label": TASK_LABEL,
        "filled_intake_status": "READY_FOR_INTAKE_APPROVAL",
        "platform": PLATFORM,
        "intake_id": stable_intake_id(source_path, target, content_type, text),
        "source_system": "operator_source_artifact",
        "source_artifact_path": path_text(source_artifact),
        "content_title": title,
        "content_body": body,
        "content_summary": summary,
        "content_type": content_type,
        "target_name": target,
        "author_or_operator": author_or_operator,
        "created_at_utc": utc_now(),
        "approval_required": True,
        "financial_advice_check_required": True,
        "no_trading_signal_required": True,
        "source_evidence_paths": [],
        "operator_notes": "Real content copied from operator-provided source artifact; still awaiting approval.",
        "publish_intent": publish_intent,
        "template_only": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "source_template_path": path_text(template_path),
        "validation": {
            "real_content_present": True,
            "source_artifact_present_or_pending": "PASS",
            "content_nonempty": True,
            "target_allowed": True,
            "content_type_allowed": True,
            "payload_type_matches_target": True,
            "financial_advice_check_required": True,
            "no_trading_signal_required": True,
            "dryrun_payload_reuse_blocked": True,
        },
    }


def filled_intake_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Discord Real Content Filled Intake Packet",
        "type": "object",
        "required": [
            "task_label",
            "filled_intake_status",
            "platform",
            "intake_id",
            "source_system",
            "source_artifact_path",
            "content_title",
            "content_body",
            "content_summary",
            "content_type",
            "target_name",
            "approval_required",
            "financial_advice_check_required",
            "no_trading_signal_required",
            "template_only",
            "not_approved",
            "not_dispatchable",
            "not_public_postable",
            "no_live_request_in_this_task",
            "no_env_read_in_this_task",
            "raw_secret_output",
            "validation",
        ],
        "properties": {
            "task_label": {"const": TASK_LABEL},
            "filled_intake_status": {"enum": ["READY_FOR_INTAKE_APPROVAL", "BLOCKED_AWAITING_OPERATOR_CONTENT", "FAIL_VALIDATION"]},
            "platform": {"const": PLATFORM},
            "approval_required": {"const": True},
            "financial_advice_check_required": {"const": True},
            "no_trading_signal_required": {"const": True},
            "not_approved": {"const": True},
            "not_dispatchable": {"const": True},
            "not_public_postable": {"const": True},
            "no_live_request_in_this_task": {"const": True},
            "no_env_read_in_this_task": {"const": True},
            "raw_secret_output": {"const": False},
        },
    }


def operator_fill_instructions() -> str:
    return """# Discord Real Content Filled Intake Instructions\n\nJim fills this workflow only with real Capital Chronicle content.\n\n## Required inputs\n\n- Use real Capital Chronicle content only.\n- Include `source_artifact_path` pointing to source content file.\n- Include `source_evidence_paths` when numeric claims are present.\n- Choose `target_name` and `content_type` correctly:\n  - `announcements` -> `announcement`\n  - `substack_drops` -> `substack_drop`\n  - `product_updates` -> `product_update`\n- Keep `not_approved=true`, `not_dispatchable=true`, and `not_public_postable=true` until later approval task.\n- Keep `template_only=false` only when real content is actually provided.\n\n## Safety rules\n\n- Do not paste webhook URLs or secrets.\n- Do not include buy/sell/hold recommendations.\n- Do not include position sizing guidance.\n- Do not include guaranteed predictions.\n- Do not reuse dry-run payloads, sample payloads, templates, or prior test messages as real content.\n\n## CLI examples\n\nBlocked framework packet, no real content yet:\n\n```powershell\npython -m live_contentops.discord_real_content_filled_intake --template docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json --output docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE/filled_intake_packet.json\n```\n\nFuture real source artifact intake:\n\n```powershell\npython -m live_contentops.discord_real_content_filled_intake --source-artifact <real_content_artifact_path> --target announcements --content-type announcement --output docs/automation/DISCORD_REAL_CONTENT_FILLED_INTAKE/filled_intake_packet.json\n```\n"""


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord Real Content Filled Intake Workflow\n\nStatus: `PASS`\n\nFilled intake status: `{packet.get('filled_intake_status')}`\n\n- No live request in this task: `true`\n- No env read in this task: `true`\n- Fake public-postable content created: `false`\n- Template/dry-run/sample content treated as real content: `false`\n- Not approved: `true`\n- Not dispatchable: `true`\n- Not public-postable: `true`\n\nIf no source artifact exists, framework remains blocked awaiting operator content.\n"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    if packet.get("filled_intake_status") == "READY_FOR_INTAKE_APPROVAL":
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_INTAKE_APPROVAL_FROM_FILLED_PACKET_V0"
        goal = "validate filled intake packet and produce operator approval candidate."
    else:
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_SOURCE_ARTIFACT_V0"
        goal = "Jim supplies real Capital Chronicle source content artifact for filled intake."
    return f"# Next Task Pointer\n\nRecommended next task:\n\n`{task}`\n\nGoal: {goal}\n"


def write_all_outputs(output: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, packet)
    write_json(out.parent / DEFAULT_SCHEMA.name, filled_intake_schema())
    (out.parent / "operator_fill_instructions.md").write_text(operator_fill_instructions(), encoding="utf-8")
    (out.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord real-content filled intake packet")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--source-artifact", default=None)
    parser.add_argument("--target", default=None)
    parser.add_argument("--content-type", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    packet = materialize_filled_intake(args.template, args.output, args.source_artifact, args.target, args.content_type)
    write_all_outputs(args.output, packet)
    print(json.dumps({
        "task_label": packet.get("task_label"),
        "filled_intake_status": packet.get("filled_intake_status"),
        "intake_id": packet.get("intake_id"),
        "target_name": packet.get("target_name"),
        "content_type": packet.get("content_type"),
        "no_live_request_in_this_task": packet.get("no_live_request_in_this_task"),
        "no_env_read_in_this_task": packet.get("no_env_read_in_this_task"),
        "template_only": packet.get("template_only"),
        "not_approved": packet.get("not_approved"),
        "not_dispatchable": packet.get("not_dispatchable"),
        "not_public_postable": packet.get("not_public_postable"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
