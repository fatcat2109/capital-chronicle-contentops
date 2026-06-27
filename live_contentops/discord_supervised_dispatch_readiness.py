"""Non-live Discord supervised dispatch readiness materializer.

Consumes the tri-target closeout packet and emits operator-facing readiness
artifacts. This module does not read env and does not perform network requests.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_DISPATCH_RUNBOOK_AND_UI_READINESS_PANEL_V0"
PLATFORM = "discord"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
WRAPPER_MODULE = "live_contentops.discord_approved_outbox_live_dispatch"
DEFAULT_CLOSEOUT_PACKET = Path("docs/automation/DISCORD_TRI_TARGET_DISPATCH_CLOSEOUT/tri_target_dispatch_closeout_packet.json")
DEFAULT_OUTPUT_PACKET = Path("docs/automation/DISCORD_SUPERVISED_DISPATCH_RUNBOOK/supervised_dispatch_readiness_packet.json")
RUNBOOK_FILENAME = "supervised_dispatch_runbook.md"
PANEL_FILENAME = "supervised_dispatch_readiness_panel.html"


@dataclass(frozen=True)
class TargetReadinessSpec:
    target_name: str
    payload_id: str
    payload_hash: str
    allowed_payload_type: str
    env_key_name: str


TARGET_SPECS: dict[str, TargetReadinessSpec] = {
    "announcements": TargetReadinessSpec(
        target_name="announcements",
        payload_id="discord_dryrun_announcement_001",
        payload_hash="b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d",
        allowed_payload_type="announcement",
        env_key_name="DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
    ),
    "substack_drops": TargetReadinessSpec(
        target_name="substack_drops",
        payload_id="discord_dryrun_substack_drop_001",
        payload_hash="a084ced7249d9b764132e17888c15c5cfd6177329dbe5ce718311e07e849175d",
        allowed_payload_type="substack_drop",
        env_key_name="DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
    ),
    "product_updates": TargetReadinessSpec(
        target_name="product_updates",
        payload_id="discord_dryrun_product_update_001",
        payload_hash="81075439dcafcdc979482d51dd56ce7cb0a704827a9fbe702a2994b3f329efdd",
        allowed_payload_type="product_update",
        env_key_name="DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
    ),
}

OPERATOR_WORKFLOW = [
    "select approved payload",
    "verify target binding",
    "verify payload hash",
    "explicit operator authorization",
    "exactly one dispatch",
    "write redacted result packet",
    "closeout/update readiness",
]

HARD_RUNTIME_RULES = [
    "no autonomous dispatch",
    "no scheduler",
    "no retry by default",
    "request budget explicit",
    "raw webhook URL never printed/stored",
    "response body/header not recorded by default",
    "wait=false unless a future task explicitly changes it",
]


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def base_packet(status: str, source_closeout_packet: str | Path) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "readiness_status": status,
        "platform": PLATFORM,
        "supervised_discord_dispatch_ready": False,
        "source_closeout_packet": str(source_closeout_packet).replace("\\", "/"),
        "adapter_module": ADAPTER_MODULE,
        "wrapper_module": WRAPPER_MODULE,
        "verified_targets": {},
        "operator_workflow": OPERATOR_WORKFLOW,
        "hard_runtime_rules": HARD_RUNTIME_RULES,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
    }


def target_from_closeout(target_name: str, closeout_target: dict[str, Any]) -> dict[str, Any]:
    spec = TARGET_SPECS[target_name]
    return {
        "ready_for_supervised_dispatch": closeout_target.get("ready_for_supervised_dispatch") is True,
        "payload_id": closeout_target.get("payload_id"),
        "payload_hash": closeout_target.get("payload_hash"),
        "last_http_status_code": closeout_target.get("http_status_code"),
        "last_dispatch_result": closeout_target.get("result_status"),
        "allowed_payload_type": spec.allowed_payload_type,
        "env_key_name": spec.env_key_name,
    }


def validate_closeout(closeout: dict[str, Any]) -> str | None:
    summary = closeout.get("readiness_summary", {})
    if summary.get("supervised_discord_dispatch_ready") is not True:
        return "supervised_discord_dispatch_ready_false"
    if summary.get("verified_target_count") != 3:
        return "verified_target_count_not_3"
    targets = closeout.get("verified_targets", {})
    for target_name, spec in TARGET_SPECS.items():
        target = targets.get(target_name)
        if not isinstance(target, dict):
            return f"{target_name}_target_missing"
        if target.get("ready_for_supervised_dispatch") is not True:
            return f"{target_name}_not_ready_for_supervised_dispatch"
        if target.get("payload_id") != spec.payload_id:
            return f"{target_name}_payload_id_mismatch"
        if target.get("payload_hash") != spec.payload_hash:
            return f"{target_name}_payload_hash_mismatch"
        if target.get("http_status_code") != 204:
            return f"{target_name}_http_status_not_204"
        if target.get("result_status") != "PASS":
            return f"{target_name}_result_status_not_pass"
    return None


def build_readiness_packet(closeout: dict[str, Any], source_closeout_packet: str | Path) -> dict[str, Any]:
    failure = validate_closeout(closeout)
    if failure is not None:
        packet = base_packet("FAIL", source_closeout_packet)
        packet["failure_reason"] = failure
        return packet

    packet = base_packet("PASS", source_closeout_packet)
    packet["supervised_discord_dispatch_ready"] = True
    packet["verified_targets"] = {
        target_name: target_from_closeout(target_name, closeout["verified_targets"][target_name])
        for target_name in TARGET_SPECS
    }
    return packet


def build_blocked_packet(reason: str, source_closeout_packet: str | Path) -> dict[str, Any]:
    packet = base_packet("BLOCKED", source_closeout_packet)
    packet["blocker"] = reason
    return packet


def runbook_markdown(packet: dict[str, Any]) -> str:
    targets = packet.get("verified_targets", {})
    lines = [
        "# Discord Supervised Dispatch Runbook",
        "",
        "## Status",
        "",
        f"Readiness status: `{packet.get('readiness_status')}`",
        f"Supervised Discord dispatch ready: `{str(packet.get('supervised_discord_dispatch_ready')).lower()}`",
        "",
        "## What Is Verified",
        "",
        "The Discord approved-outbox adapter path is live verified for all three destinations.",
        "Each accepted pilot used one request, zero retries, `wait=false`, and redacted evidence only.",
        "",
        "## Ready Targets",
        "",
        "| Target | Payload ID | Payload type | Last HTTP | Last result | Env key name |",
        "|---|---|---|---:|---|---|",
    ]
    for target_name in TARGET_SPECS:
        target = targets.get(target_name, {})
        spec = TARGET_SPECS[target_name]
        lines.append(
            f"| `{target_name}` | `{target.get('payload_id', spec.payload_id)}` | "
            f"`{target.get('allowed_payload_type', spec.allowed_payload_type)}` | "
            f"`{target.get('last_http_status_code', 'n/a')}` | "
            f"`{target.get('last_dispatch_result', 'n/a')}` | `{spec.env_key_name}` |"
        )
    lines.extend([
        "",
        "## Required Approval Before Live Dispatch",
        "",
        "Before any future live dispatch, operator must confirm:",
        "",
        "1. Payload is in approved/outbox state.",
        "2. Target binding matches target-specific destination binding.",
        "3. Payload hash matches hash approval gate packet.",
        "4. Jim gives explicit authorization for exactly one dispatch.",
        "5. Request budget and retry budget are explicit.",
        "",
        "## Future Supervised Dispatch Command Pattern",
        "",
        "```powershell",
        "python -m live_contentops.discord_approved_outbox_live_dispatch --target <target_name> --payload-id <payload_id> --execute --output <redacted_result_packet.json>",
        "```",
        "",
        "Use only one of: `announcements`, `substack_drops`, `product_updates`.",
        "",
        "## Forbidden",
        "",
        "- No autonomous posting.",
        "- No hidden scheduler.",
        "- No unapproved target mutation.",
        "- No raw webhook URL printing or storage.",
        "- No response body/header recording by default.",
        "- No retry unless a future approved task changes policy.",
        "- No financial advice, trading signal, or market-direction language.",
        "",
        "## Result Packet Interpretation",
        "",
        "- `PASS` with HTTP `2xx`: dispatch succeeded.",
        "- `FAIL` with HTTP `403`: credential unauthorized or blocked.",
        "- `FAIL` with HTTP `404`: webhook not found or deleted.",
        "- `BLOCKED`: local precondition failed before dispatch.",
        "",
        "## Recovery From Non-2xx",
        "",
        "1. Stop. Do not retry automatically.",
        "2. Preserve redacted result packet only.",
        "3. Verify credential handle and target binding without printing secret values.",
        "4. Re-run dry-run/preflight only.",
        "5. Request explicit authorization before any new live attempt.",
    ])
    return "\n".join(lines) + "\n"


def panel_html(packet: dict[str, Any]) -> str:
    cards = []
    for target_name, target in packet.get("verified_targets", {}).items():
        cards.append(
            f"<article class='card'><p class='eyebrow'>{target_name}</p><h2>READY</h2><dl>"
            f"<dt>Payload</dt><dd>{target.get('payload_id')}</dd>"
            f"<dt>HTTP</dt><dd>{target.get('last_http_status_code')}</dd>"
            f"<dt>Result</dt><dd>{target.get('last_dispatch_result')}</dd>"
            f"<dt>Env key</dt><dd>{target.get('env_key_name')}</dd>"
            f"</dl></article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discord Supervised Dispatch Readiness</title>
  <meta name="description" content="Static non-live operator readiness panel for Discord supervised dispatch.">
  <style>
    :root {{ color-scheme: dark; --bg:#141313; --panel:#1b1b1b; --line:#45474a; --text:#f2eee8; --muted:#a9a29a; --ok:#9ad7b4; --warn:#f0c36a; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--text); }}
    main {{ max-width:1120px; margin:0 auto; padding:32px; }}
    .rail {{ border:1px solid var(--line); background:linear-gradient(135deg,#1f1e1e,#151515); padding:24px; }}
    h1 {{ margin:0 0 8px; font-size:28px; letter-spacing:-.03em; }}
    .status {{ color:var(--ok); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; margin-top:18px; }}
    .card {{ border:1px solid var(--line); background:var(--panel); padding:18px; }}
    .eyebrow {{ margin:0 0 10px; color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-size:12px; }}
    h2 {{ margin:0 0 14px; color:var(--ok); font-size:18px; }}
    dl {{ margin:0; display:grid; grid-template-columns:90px 1fr; gap:8px; }}
    dt {{ color:var(--muted); }} dd {{ margin:0; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap:anywhere; }}
    .rules {{ margin-top:18px; color:var(--warn); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
  </style>
</head>
<body>
<main>
  <section class="rail" aria-labelledby="page-title">
    <p class="eyebrow">Capital Chronicle ContentOps</p>
    <h1 id="page-title">Discord supervised dispatch readiness</h1>
    <p class="status">PASS · 3/3 targets adapter-dispatch verified · no live request in this view</p>
    <div class="grid">{''.join(cards)}</div>
    <p class="rules">Rules: explicit operator authorization only · one dispatch · no retry by default · no raw webhook URL display.</p>
  </section>
</main>
</body>
</html>
"""


def write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def generate_from_files(
    *,
    tri_target_closeout: str | Path = DEFAULT_CLOSEOUT_PACKET,
    output: str | Path = DEFAULT_OUTPUT_PACKET,
) -> dict[str, Any]:
    try:
        closeout = load_json(tri_target_closeout)
        packet = build_readiness_packet(closeout, tri_target_closeout)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        packet = build_blocked_packet(f"tri_target_closeout_missing_or_unreadable:{exc}", tri_target_closeout)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_text(out.parent / RUNBOOK_FILENAME, runbook_markdown(packet))
    write_text(out.parent / PANEL_FILENAME, panel_html(packet))
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord supervised dispatch readiness")
    parser.add_argument("--tri-target-closeout", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = generate_from_files(tri_target_closeout=args.tri_target_closeout, output=args.output)
    print(json.dumps({
        "task_label": packet["task_label"],
        "readiness_status": packet["readiness_status"],
        "platform": packet["platform"],
        "supervised_discord_dispatch_ready": packet["supervised_discord_dispatch_ready"],
        "no_live_request_in_this_task": packet["no_live_request_in_this_task"],
        "no_env_read_in_this_task": packet["no_env_read_in_this_task"],
        "raw_secret_output": packet["raw_secret_output"],
    }, indent=2, sort_keys=True))
    return 0 if packet["readiness_status"] in {"PASS", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
