"""Non-live Discord supervised dispatch action materializer.

Creates deterministic operator action records from verified readiness, payload,
and hash evidence. No env reads. No network requests. Does not execute previews.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVED_QUEUE_TO_SUPERVISED_DISPATCH_ACTIONS_V0"
PLATFORM = "discord"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
WRAPPER_MODULE = "live_contentops.discord_approved_outbox_live_dispatch"
USER_AGENT_REQUIRED = "CapitalChronicleContentOps/1.0"
DEFAULT_OUTPUT_PACKET = Path("docs/automation/DISCORD_SUPERVISED_DISPATCH_ACTIONS/supervised_dispatch_actions_packet.json")
PANEL_FILENAME = "supervised_dispatch_actions_panel.html"
IMPLEMENTATION_REPORT_FILENAME = "implementation_report.md"
NEXT_TASK_POINTER_FILENAME = "next_task_pointer.md"
FORBIDDEN = [
    "autonomous_dispatch",
    "scheduler",
    "retry_without_explicit_task",
    "raw_webhook_url_display",
    "response_body_capture_by_default",
]
TARGET_ORDER = ("announcements", "substack_drops", "product_updates")


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def _path_text(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def base_packet(status: str, readiness_packet: str | Path, payload_packet: str | Path, hash_packet: str | Path) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "action_materialization_status": status,
        "platform": PLATFORM,
        "source_readiness_packet": _path_text(readiness_packet),
        "source_payload_packet": _path_text(payload_packet),
        "source_hash_packet": _path_text(hash_packet),
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "supervised_dispatch_actions_ready": False,
        "action_count": 0,
        "actions": [],
    }


def _index_payloads(payload_packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p.get("payload_id"): p for p in payload_packet.get("payloads", []) if isinstance(p, dict)}


def _index_hashes(hash_packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p.get("payload_id"): p for p in hash_packet.get("approval_packets", []) if isinstance(p, dict)}


def _live_command(target_name: str, payload_id: str) -> str:
    return (
        "python -m live_contentops.discord_approved_outbox_live_dispatch "
        f"--target {target_name} --payload-id {payload_id} --execute "
        f"--output docs/automation/DISCORD_SUPERVISED_DISPATCH_ACTIONS/live_results/{target_name}_result_packet.json"
    )


def _fail(packet: dict[str, Any], reason: str) -> dict[str, Any]:
    packet["action_materialization_status"] = "FAIL"
    packet["failure_reason"] = reason
    packet["supervised_dispatch_actions_ready"] = False
    packet["action_count"] = len(packet.get("actions", []))
    return packet


def validate_and_build_actions(readiness: dict[str, Any], payloads: dict[str, Any], hashes: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    if readiness.get("readiness_status") != "PASS":
        return _fail(packet, "readiness_status_not_pass")
    if readiness.get("supervised_discord_dispatch_ready") is not True:
        return _fail(packet, "supervised_discord_dispatch_ready_false")

    payload_by_id = _index_payloads(payloads)
    hash_by_id = _index_hashes(hashes)
    ready_targets = readiness.get("verified_targets", {})
    actions: list[dict[str, Any]] = []

    for target_name in TARGET_ORDER:
        ready = ready_targets.get(target_name)
        if not isinstance(ready, dict):
            return _fail(packet, f"{target_name}_readiness_missing")
        if ready.get("ready_for_supervised_dispatch") is not True:
            return _fail(packet, f"{target_name}_not_ready")

        payload_id = ready.get("payload_id")
        payload = payload_by_id.get(payload_id)
        if not isinstance(payload, dict):
            return _fail(packet, f"{target_name}_payload_missing")
        if payload.get("target_name") != target_name:
            return _fail(packet, f"{target_name}_payload_target_mismatch")
        if payload.get("payload_type") != ready.get("allowed_payload_type"):
            return _fail(packet, f"{target_name}_payload_type_mismatch")

        approval = hash_by_id.get(payload_id)
        if not isinstance(approval, dict):
            return _fail(packet, f"{target_name}_payload_hash_missing")
        if approval.get("target_name") != target_name:
            return _fail(packet, f"{target_name}_hash_target_mismatch")
        if approval.get("payload_hash") != ready.get("payload_hash"):
            return _fail(packet, f"{target_name}_payload_hash_mismatch")
        if approval.get("payload_type") != payload.get("payload_type"):
            return _fail(packet, f"{target_name}_hash_payload_type_mismatch")
        if approval.get("destination_binding_id") != payload.get("destination_binding_id"):
            return _fail(packet, f"{target_name}_destination_binding_mismatch")
        if approval.get("credential_handle_id") != payload.get("credential_handle_id"):
            return _fail(packet, f"{target_name}_credential_handle_mismatch")

        actions.append({
            "action_id": f"discord_supervised_dispatch_action_{target_name}",
            "action_status": "READY",
            "target_name": target_name,
            "payload_id": payload_id,
            "payload_type": payload.get("payload_type"),
            "payload_hash": approval.get("payload_hash"),
            "env_key_name": ready.get("env_key_name"),
            "destination_binding_id": payload.get("destination_binding_id"),
            "credential_handle_id": payload.get("credential_handle_id"),
            "adapter_module": ADAPTER_MODULE,
            "wrapper_module": WRAPPER_MODULE,
            "readiness_verified": True,
            "payload_hash_verified": True,
            "operator_authorization_required": True,
            "live_command_preview_redacted": _live_command(target_name, payload_id),
            "request_budget_required": 1,
            "retry_budget_required": 0,
            "wait_query_param": False,
            "user_agent_required": USER_AGENT_REQUIRED,
            "response_body_recorded": False,
            "response_headers_recorded": False,
            "public_url_expected": None,
            "webhook_message_id_expected": None,
            "last_http_status_code_from_readiness": ready.get("last_http_status_code"),
            "forbidden": FORBIDDEN,
        })

    packet["actions"] = actions
    packet["action_count"] = len(actions)
    if len(actions) != 3:
        return _fail(packet, "action_count_not_3")
    packet["supervised_dispatch_actions_ready"] = True
    return packet


def panel_html(packet: dict[str, Any]) -> str:
    cards = []
    for action in packet.get("actions", []):
        command = html.escape(action["live_command_preview_redacted"])
        cards.append(
            "<article class='card'>"
            f"<p class='eyebrow'>{html.escape(action['target_name'])}</p>"
            "<h2>READY ACTION</h2>"
            "<dl>"
            f"<dt>Payload</dt><dd>{html.escape(action['payload_id'])}</dd>"
            f"<dt>Type</dt><dd>{html.escape(action['payload_type'])}</dd>"
            f"<dt>Last HTTP</dt><dd>{action.get('last_http_status_code_from_readiness')}</dd>"
            f"<dt>Env key</dt><dd>{html.escape(action['env_key_name'])}</dd>"
            "<dt>Auth</dt><dd>explicit operator authorization required</dd>"
            "</dl>"
            f"<pre>{command}</pre>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discord Supervised Dispatch Actions</title>
  <meta name="description" content="Static non-live operator panel for Discord supervised dispatch action records.">
  <style>
    :root {{ color-scheme: dark; --bg:#121111; --panel:#1b1b1c; --line:#43464a; --text:#f3efe8; --muted:#aaa49c; --ok:#9ad7b4; --warn:#f1c66d; --ink:#0f1113; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:radial-gradient(circle at top left,#2b2824,var(--bg) 42%); color:var(--text); }}
    main {{ max-width:1180px; margin:0 auto; padding:36px; }}
    .hero {{ border:1px solid var(--line); background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02)); padding:26px; box-shadow:0 24px 80px rgba(0,0,0,.35); }}
    .eyebrow {{ margin:0 0 10px; color:var(--muted); text-transform:uppercase; letter-spacing:.13em; font-size:12px; }}
    h1 {{ margin:0 0 10px; font-size:30px; letter-spacing:-.04em; }}
    .status {{ color:var(--ok); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:16px; margin-top:20px; }}
    .card {{ border:1px solid var(--line); background:var(--panel); padding:18px; }}
    h2 {{ margin:0 0 14px; color:var(--ok); font-size:18px; }}
    dl {{ margin:0 0 14px; display:grid; grid-template-columns:88px 1fr; gap:8px; }}
    dt {{ color:var(--muted); }} dd {{ margin:0; overflow-wrap:anywhere; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; background:var(--ink); border:1px solid #33363a; padding:12px; color:#d8d2ca; }}
    .disabled {{ margin-top:18px; color:var(--warn); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    button {{ display:none; }}
  </style>
</head>
<body><main><section class="hero" aria-labelledby="page-title">
<p class="eyebrow">Capital Chronicle ContentOps</p>
<h1 id="page-title">Discord supervised dispatch actions</h1>
<p class="status">PASS · 3 ready actions · non-live preview only · no raw webhook URL</p>
<div class="grid">{''.join(cards)}</div>
<p class="disabled">Live controls absent. Operator authorization required before future dispatch.</p>
</section></main></body></html>
"""


def report_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Discord Supervised Dispatch Actions Implementation Report",
        "",
        f"Status: `{packet.get('action_materialization_status')}`",
        f"Action count: `{packet.get('action_count')}`",
        "",
        "## Safety",
        "",
        "- No live POST in this task.",
        "- No env read in this task.",
        "- No raw webhook URL or env value stored.",
        "- Command previews are redacted strings only and were not executed.",
        "- Live controls are absent from the static panel.",
        "",
        "## Actions",
        "",
        "| Target | Payload | Type | Command preview |",
        "|---|---|---|---|",
    ]
    for action in packet.get("actions", []):
        lines.append(
            f"| `{action['target_name']}` | `{action['payload_id']}` | `{action['payload_type']}` | `{action['live_command_preview_redacted']}` |"
        )
    return "\n".join(lines) + "\n"


def next_task_markdown() -> str:
    return """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_DISPATCH_OPERATOR_APPROVAL_GATE_V0`

Goal: require explicit operator approval over one generated action record before any future live dispatch command may run.
"""


def write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def generate_from_files(*, readiness_packet: str | Path, payload_packet: str | Path, hash_packet: str | Path, output: str | Path = DEFAULT_OUTPUT_PACKET) -> dict[str, Any]:
    try:
        readiness = load_json(readiness_packet)
        payloads = load_json(payload_packet)
        hashes = load_json(hash_packet)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        packet = base_packet("BLOCKED", readiness_packet, payload_packet, hash_packet)
        packet["blocker"] = f"required_input_packet_missing_or_unreadable:{exc}"
    else:
        packet = base_packet("PASS", readiness_packet, payload_packet, hash_packet)
        packet = validate_and_build_actions(readiness, payloads, hashes, packet)

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_text(out.parent / PANEL_FILENAME, panel_html(packet))
    write_text(out.parent / IMPLEMENTATION_REPORT_FILENAME, report_markdown(packet))
    write_text(out.parent / NEXT_TASK_POINTER_FILENAME, next_task_markdown())
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord supervised dispatch actions")
    parser.add_argument("--readiness-packet", required=True)
    parser.add_argument("--payload-packet", required=True)
    parser.add_argument("--hash-packet", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = generate_from_files(
        readiness_packet=args.readiness_packet,
        payload_packet=args.payload_packet,
        hash_packet=args.hash_packet,
        output=args.output,
    )
    print(json.dumps({
        "task_label": packet["task_label"],
        "action_materialization_status": packet["action_materialization_status"],
        "platform": packet["platform"],
        "supervised_dispatch_actions_ready": packet["supervised_dispatch_actions_ready"],
        "action_count": packet["action_count"],
        "no_live_request_in_this_task": packet["no_live_request_in_this_task"],
        "no_env_read_in_this_task": packet["no_env_read_in_this_task"],
        "raw_secret_output": packet["raw_secret_output"],
    }, indent=2, sort_keys=True))
    return 0 if packet["action_materialization_status"] in {"PASS", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
