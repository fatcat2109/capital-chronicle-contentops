"""Non-live Discord operator approval gate.

Materializes final manual approval checkpoint for one supervised dispatch action.
No env reads. No network requests. Command preview is never executed here.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_DISPATCH_OPERATOR_APPROVAL_GATE_V0"
PLATFORM = "discord"
SELECTED_ACTION_ID = "discord_supervised_dispatch_action_announcements"
AUTHORIZATION_STATE = "NOT_AUTHORIZED_IN_THIS_TASK"
DEFAULT_OUTPUT_PACKET = Path("docs/automation/DISCORD_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
PANEL_FILENAME = "operator_approval_gate_panel.html"
IMPLEMENTATION_REPORT_FILENAME = "implementation_report.md"
NEXT_TASK_POINTER_FILENAME = "next_task_pointer.md"
USER_AGENT_REQUIRED = "CapitalChronicleContentOps/1.0"


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def _path_text(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def base_packet(status: str, actions_packet: str | Path, action_id: str) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "approval_gate_status": status,
        "platform": PLATFORM,
        "source_actions_packet": _path_text(actions_packet),
        "selected_action_id": action_id,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "live_controls_enabled": False,
        "operator_authorization_required": True,
        "operator_authorization_state": AUTHORIZATION_STATE,
        "future_live_dispatch_allowed": False,
    }


def _find_action(actions_packet: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    for action in actions_packet.get("actions", []):
        if isinstance(action, dict) and action.get("action_id") == action_id:
            return action
    return None


def _fail(packet: dict[str, Any], reason: str) -> dict[str, Any]:
    packet["approval_gate_status"] = "FAIL"
    packet["failure_reason"] = reason
    packet["future_live_dispatch_allowed"] = False
    packet["live_controls_enabled"] = False
    return packet


def _validate_action(action: dict[str, Any]) -> str | None:
    if action.get("action_status") != "READY":
        return "action_status_not_ready"
    if action.get("readiness_verified") is not True:
        return "readiness_verified_false"
    if action.get("payload_hash_verified") is not True:
        return "payload_hash_verified_false"
    if action.get("operator_authorization_required") is not True:
        return "operator_authorization_required_false"
    if action.get("request_budget_required") != 1:
        return "request_budget_required_not_1"
    if action.get("retry_budget_required") != 0:
        return "retry_budget_required_not_0"
    if action.get("wait_query_param") is not False:
        return "wait_query_param_not_false"
    if action.get("user_agent_required") != USER_AGENT_REQUIRED:
        return "user_agent_required_mismatch"
    if not action.get("live_command_preview_redacted"):
        return "command_preview_missing"
    return None


def build_approval_packet(actions_packet: dict[str, Any], source_actions_packet: str | Path, action_id: str) -> dict[str, Any]:
    packet = base_packet("PASS", source_actions_packet, action_id)
    if actions_packet.get("action_materialization_status") != "PASS":
        return _fail(packet, "actions_packet_status_not_pass")
    if actions_packet.get("supervised_dispatch_actions_ready") is not True:
        return _fail(packet, "supervised_dispatch_actions_ready_false")

    action = _find_action(actions_packet, action_id)
    if action is None:
        return _fail(packet, "selected_action_missing")

    conflict = _validate_action(action)
    if conflict is not None:
        return _fail(packet, conflict)

    packet.update({
        "selected_target_name": action.get("target_name"),
        "selected_payload_id": action.get("payload_id"),
        "selected_payload_hash": action.get("payload_hash"),
        "selected_payload_type": action.get("payload_type"),
        "destination_binding_id": action.get("destination_binding_id"),
        "credential_handle_id": action.get("credential_handle_id"),
        "env_key_name": action.get("env_key_name"),
        "action_status_from_source": action.get("action_status"),
        "readiness_verified": action.get("readiness_verified"),
        "payload_hash_verified": action.get("payload_hash_verified"),
        "command_preview_redacted": action.get("live_command_preview_redacted"),
        "approval_binding": {
            "action_id": action.get("action_id"),
            "target_name": action.get("target_name"),
            "payload_id": action.get("payload_id"),
            "payload_hash": action.get("payload_hash"),
            "destination_binding_id": action.get("destination_binding_id"),
            "credential_handle_id": action.get("credential_handle_id"),
            "request_budget_required": 1,
            "retry_budget_required": 0,
            "wait_query_param": False,
            "user_agent_required": USER_AGENT_REQUIRED,
        },
    })
    return packet


def panel_html(packet: dict[str, Any]) -> str:
    command = html.escape(packet.get("command_preview_redacted", "blocked"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discord Operator Approval Gate</title>
  <meta name="description" content="Static non-live Discord operator approval gate for selected supervised dispatch action.">
  <style>
    :root {{ color-scheme: dark; --bg:#11100f; --panel:#1b1a19; --line:#45413d; --text:#f4eee6; --muted:#aaa19a; --ok:#9ad7b4; --warn:#f1c66d; --danger:#ff9b9b; --ink:#0c0d0e; }}
    body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui,sans-serif; background:radial-gradient(circle at 10% 0,#302a22,var(--bg) 45%); color:var(--text); }}
    main {{ max-width:1060px; margin:0 auto; padding:36px; }}
    .gate {{ border:1px solid var(--line); background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025)); padding:28px; box-shadow:0 28px 90px rgba(0,0,0,.38); }}
    .eyebrow {{ color:var(--muted); text-transform:uppercase; letter-spacing:.13em; font-size:12px; margin:0 0 10px; }}
    h1 {{ margin:0 0 10px; font-size:31px; letter-spacing:-.04em; }}
    .state {{ color:var(--warn); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    dl {{ display:grid; grid-template-columns:190px 1fr; gap:10px; margin:22px 0; }}
    dt {{ color:var(--muted); }} dd {{ margin:0; overflow-wrap:anywhere; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; padding:14px; border:1px solid #33363a; background:var(--ink); color:#ddd5ca; }}
    .disabled {{ color:var(--danger); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    button {{ display:none; }}
  </style>
</head>
<body><main><section class="gate" aria-labelledby="page-title">
<p class="eyebrow">Capital Chronicle ContentOps</p>
<h1 id="page-title">Discord operator approval gate</h1>
<p class="state">{html.escape(packet.get('operator_authorization_state', AUTHORIZATION_STATE))} · future_live_dispatch_allowed=false · no live request</p>
<dl>
<dt>Selected action</dt><dd>{html.escape(packet.get('selected_action_id', 'missing'))}</dd>
<dt>Target</dt><dd>{html.escape(str(packet.get('selected_target_name', 'blocked')))}</dd>
<dt>Payload ID</dt><dd>{html.escape(str(packet.get('selected_payload_id', 'blocked')))}</dd>
<dt>Payload hash</dt><dd>{html.escape(str(packet.get('selected_payload_hash', 'blocked')))}</dd>
<dt>Env key</dt><dd>{html.escape(str(packet.get('env_key_name', 'blocked')))}</dd>
<dt>Authorization</dt><dd>{html.escape(packet.get('operator_authorization_state', AUTHORIZATION_STATE))}</dd>
<dt>Live allowed</dt><dd>false</dd>
</dl>
<pre>{command}</pre>
<p class="disabled">Live controls absent. This packet does not authorize dispatch.</p>
</section></main></body></html>
"""


def report_markdown(packet: dict[str, Any]) -> str:
    return f"""# Discord Operator Approval Gate Implementation Report

Status: `{packet.get('approval_gate_status')}`

## Selected Action

- Action: `{packet.get('selected_action_id')}`
- Target: `{packet.get('selected_target_name')}`
- Payload: `{packet.get('selected_payload_id')}`
- Authorization state: `{packet.get('operator_authorization_state')}`
- Future live dispatch allowed: `{str(packet.get('future_live_dispatch_allowed')).lower()}`

## Safety

- No live POST in this task.
- No env read in this task.
- Command preview preserved but not executed.
- Live controls disabled/absent.
- No raw webhook URL or env value stored.
"""


def next_task_markdown() -> str:
    return """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH_V0`

Goal: only after explicit user authorization, execute one selected operator-approved action with request budget `1` and retry budget `0`.
"""


def write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def generate_from_files(*, actions_packet: str | Path, action_id: str, output: str | Path = DEFAULT_OUTPUT_PACKET) -> dict[str, Any]:
    try:
        actions = load_json(actions_packet)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        packet = base_packet("BLOCKED", actions_packet, action_id)
        packet["blocker"] = f"actions_packet_missing_or_unreadable:{exc}"
    else:
        packet = build_approval_packet(actions, actions_packet, action_id)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_text(out.parent / PANEL_FILENAME, panel_html(packet))
    write_text(out.parent / IMPLEMENTATION_REPORT_FILENAME, report_markdown(packet))
    write_text(out.parent / NEXT_TASK_POINTER_FILENAME, next_task_markdown())
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord operator approval gate")
    parser.add_argument("--actions-packet", required=True)
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = generate_from_files(actions_packet=args.actions_packet, action_id=args.action_id, output=args.output)
    print(json.dumps({
        "task_label": packet["task_label"],
        "approval_gate_status": packet["approval_gate_status"],
        "platform": packet["platform"],
        "selected_action_id": packet["selected_action_id"],
        "operator_authorization_state": packet["operator_authorization_state"],
        "future_live_dispatch_allowed": packet["future_live_dispatch_allowed"],
        "no_live_request_in_this_task": packet["no_live_request_in_this_task"],
        "no_env_read_in_this_task": packet["no_env_read_in_this_task"],
        "raw_secret_output": packet["raw_secret_output"],
    }, indent=2, sort_keys=True))
    return 0 if packet["approval_gate_status"] in {"PASS", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
